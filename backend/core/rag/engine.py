#!/usr/bin/env python3
"""
RAG引擎实现
完整的检索增强生成引擎

运行环境: Python 3.11+
依赖: asyncio, typing, time
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base import (
    BaseRetriever, BaseRAGEngine, Document, DocumentChunk, 
    RetrievalQuery, RetrievalResult, RAGResponse, RetrievalStrategy,
    BaseDocumentProcessor, BaseEmbeddingProvider, BaseVectorStore,
    RAGError, RetrievalError
)


class StandardRetriever(BaseRetriever):
    """标准检索器
    
    实现多种检索策略的统一检索器
    """
    
    def __init__(self, vector_store: BaseVectorStore, 
                 embedding_provider: BaseEmbeddingProvider,
                 config: Dict[str, Any]):
        super().__init__(vector_store, embedding_provider, config)
        self.default_top_k = config.get('default_top_k', 5)
        self.default_threshold = config.get('default_threshold', 0.7)
        self.enable_rerank = config.get('enable_rerank', False)
        self.query_expansion = config.get('query_expansion', False)
    
    def validate_config(self) -> bool:
        """验证配置"""
        return self.default_top_k > 0 and 0 <= self.default_threshold <= 1
    
    async def retrieve(self, query: RetrievalQuery) -> List[RetrievalResult]:
        """执行检索"""
        try:
            # 查询扩展
            if query.expand_query or self.query_expansion:
                expanded_query = await self._expand_query(query.query)
            else:
                expanded_query = query.query
            
            # 生成查询嵌入
            if query.query_embedding:
                query_embedding = query.query_embedding
            else:
                # 嵌入生成失败时回退到关键词检索
                query_embedding = None
                try:
                    query_embedding = await self.embedding_provider.embed_text(expanded_query)
                except Exception:
                    # 回退：后续走关键词检索路径
                    query_embedding = None
            
            # 根据策略执行检索
            if query.strategy == RetrievalStrategy.SIMILARITY:
                if query_embedding is not None:
                    results = await self._similarity_search(query_embedding, query)
                else:
                    # 无法生成嵌入时回退到关键词检索
                    results = await self._keyword_search(expanded_query, query)
            elif query.strategy == RetrievalStrategy.MMR:
                if query_embedding is not None:
                    results = await self._mmr_search(query_embedding, query)
                else:
                    results = await self._keyword_search(expanded_query, query)
            elif query.strategy == RetrievalStrategy.HYBRID:
                if query_embedding is not None:
                    results = await self._hybrid_search(expanded_query, query_embedding, query)
                else:
                    # 混合检索在嵌入不可用时退化为关键词检索
                    results = await self._keyword_search(expanded_query, query)
            elif query.strategy == RetrievalStrategy.KEYWORD:
                results = await self._keyword_search(expanded_query, query)
            elif query.strategy == RetrievalStrategy.SEMANTIC_HYBRID:
                if query_embedding is not None:
                    results = await self._semantic_hybrid_search(expanded_query, query_embedding, query)
                else:
                    results = await self._keyword_search(expanded_query, query)
            else:
                if query_embedding is not None:
                    results = await self._similarity_search(query_embedding, query)
                else:
                    results = await self._keyword_search(expanded_query, query)
            
            # 重排序
            if query.rerank or self.enable_rerank:
                results = await self._rerank_results(results, query.query)
            
            # 过滤低分结果
            results = [r for r in results if r.score >= query.threshold]
            
            return results[:query.top_k]
            
        except Exception as e:
            raise RetrievalError(f"检索失败: {str(e)}") from e
    
    async def _similarity_search(self, query_embedding: List[float], 
                               query: RetrievalQuery) -> List[RetrievalResult]:
        """相似度搜索"""
        results = await self.vector_store.search(
            query_embedding=query_embedding,
            top_k=query.top_k * 2,  # 获取更多结果用于后续处理
            filters=query.filters
        )
        
        # 更新检索方法
        for result in results:
            result.retrieval_method = 'similarity_search'
        
        return results
    
    async def _mmr_search(self, query_embedding: List[float], 
                         query: RetrievalQuery) -> List[RetrievalResult]:
        """最大边际相关性搜索"""
        # 首先获取相似度搜索结果
        initial_results = await self.vector_store.search(
            query_embedding=query_embedding,
            top_k=query.top_k * 3,  # 获取更多候选
            filters=query.filters
        )
        
        if not initial_results:
            return []
        
        # MMR算法参数
        lambda_param = self.config.get('mmr_lambda', 0.5)  # 多样性权重
        
        # 执行MMR选择
        selected_results = []
        remaining_results = initial_results.copy()
        
        # 选择第一个最相似的结果
        if remaining_results:
            best_result = max(remaining_results, key=lambda x: x.score)
            selected_results.append(best_result)
            remaining_results.remove(best_result)
        
        # 迭代选择剩余结果
        while len(selected_results) < query.top_k and remaining_results:
            best_score = -1
            best_result = None
            
            for candidate in remaining_results:
                # 计算与查询的相似度
                query_sim = candidate.score
                
                # 计算与已选择结果的最大相似度
                max_selected_sim = 0
                if selected_results and candidate.chunk.embedding:
                    for selected in selected_results:
                        if selected.chunk.embedding:
                            sim = self._cosine_similarity(
                                candidate.chunk.embedding, 
                                selected.chunk.embedding
                            )
                            max_selected_sim = max(max_selected_sim, sim)
                
                # MMR分数
                mmr_score = lambda_param * query_sim - (1 - lambda_param) * max_selected_sim
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_result = candidate
            
            if best_result:
                best_result.retrieval_method = 'mmr_search'
                best_result.metadata['mmr_score'] = best_score
                selected_results.append(best_result)
                remaining_results.remove(best_result)
            else:
                break
        
        return selected_results
    
    async def _hybrid_search(self, query: str, query_embedding: List[float], 
                           query_obj: RetrievalQuery) -> List[RetrievalResult]:
        """混合搜索（向量+关键词）"""
        # 向量搜索
        vector_results = await self._similarity_search(query_embedding, query_obj)
        
        # 关键词搜索
        keyword_results = await self._keyword_search(query, query_obj)
        
        # 合并和重新排序结果
        combined_results = self._merge_search_results(
            vector_results, keyword_results, 
            vector_weight=0.7, keyword_weight=0.3
        )
        
        # 更新检索方法
        for result in combined_results:
            result.retrieval_method = 'hybrid_search'
        
        return combined_results[:query_obj.top_k]
    
    async def _keyword_search(self, query: str, query_obj: RetrievalQuery) -> List[RetrievalResult]:
        """关键词搜索（简化实现）"""
        # 获取所有文档块
        all_chunks = await self.vector_store.list_chunks(limit=1000)
        
        # 简单的关键词匹配
        query_terms = query.lower().split()
        results = []
        
        for chunk in all_chunks:
            content_lower = chunk.content.lower()
            
            # 计算关键词匹配分数
            matches = sum(1 for term in query_terms if term in content_lower)
            if matches > 0:
                score = matches / len(query_terms)
                
                result = RetrievalResult(
                    chunk=chunk,
                    score=score,
                    rank=0,  # 稍后重新排序
                    retrieval_method='keyword_search',
                    metadata={'keyword_matches': matches}
                )
                results.append(result)
        
        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        # 更新排名
        for i, result in enumerate(results):
            result.rank = i
        
        return results[:query_obj.top_k]
    
    async def _semantic_hybrid_search(self, query: str, query_embedding: List[float], 
                                    query_obj: RetrievalQuery) -> List[RetrievalResult]:
        """语义混合搜索"""
        # 这里可以实现更复杂的语义搜索策略
        # 当前使用混合搜索作为基础
        return await self._hybrid_search(query, query_embedding, query_obj)
    
    async def _expand_query(self, query: str) -> str:
        """查询扩展"""
        # 简化的查询扩展实现
        # 实际应用中可能使用同义词词典、词嵌入等
        
        # 添加一些常见的同义词和相关词
        expansion_map = {
            '搜索': ['查找', '检索', '寻找'],
            '文档': ['文件', '资料', '材料'],
            '信息': ['数据', '内容', '资讯'],
            '分析': ['解析', '研究', '评估']
        }
        
        expanded_terms = [query]
        
        for term, synonyms in expansion_map.items():
            if term in query:
                expanded_terms.extend(synonyms)
        
        return ' '.join(expanded_terms)
    
    async def _rerank_results(self, results: List[RetrievalResult], 
                            query: str) -> List[RetrievalResult]:
        """重排序结果"""
        # 简化的重排序实现
        # 实际应用中可能使用专门的重排序模型
        
        for result in results:
            # 基于内容长度和查询匹配度调整分数
            content_length_factor = min(len(result.chunk.content) / 1000, 1.0)
            query_match_factor = self._calculate_query_match(result.chunk.content, query)
            
            # 重新计算分数
            rerank_score = (
                result.score * 0.6 + 
                content_length_factor * 0.2 + 
                query_match_factor * 0.2
            )
            
            result.score = rerank_score
            result.metadata['reranked'] = True
        
        # 重新排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        # 更新排名
        for i, result in enumerate(results):
            result.rank = i
        
        return results
    
    def _merge_search_results(self, vector_results: List[RetrievalResult], 
                            keyword_results: List[RetrievalResult],
                            vector_weight: float = 0.7, 
                            keyword_weight: float = 0.3) -> List[RetrievalResult]:
        """合并搜索结果"""
        # 创建结果字典
        result_dict = {}
        
        # 添加向量搜索结果
        for result in vector_results:
            chunk_id = result.chunk.chunk_id
            result_dict[chunk_id] = result
            result.score *= vector_weight
        
        # 添加关键词搜索结果
        for result in keyword_results:
            chunk_id = result.chunk.chunk_id
            if chunk_id in result_dict:
                # 合并分数
                result_dict[chunk_id].score += result.score * keyword_weight
                result_dict[chunk_id].metadata['hybrid_score'] = True
            else:
                result.score *= keyword_weight
                result_dict[chunk_id] = result
        
        # 转换为列表并排序
        merged_results = list(result_dict.values())
        merged_results.sort(key=lambda x: x.score, reverse=True)
        
        # 更新排名
        for i, result in enumerate(merged_results):
            result.rank = i
        
        return merged_results
    
    def _calculate_query_match(self, content: str, query: str) -> float:
        """计算查询匹配度"""
        content_lower = content.lower()
        query_lower = query.lower()
        query_terms = query_lower.split()
        
        matches = sum(1 for term in query_terms if term in content_lower)
        return matches / len(query_terms) if query_terms else 0
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class RAGEngine(BaseRAGEngine):
    """RAG引擎实现
    
    完整的检索增强生成引擎
    """
    
    def __init__(self, 
                 document_processor: BaseDocumentProcessor,
                 embedding_provider: BaseEmbeddingProvider,
                 vector_store: BaseVectorStore,
                 retriever: BaseRetriever,
                 config: Dict[str, Any]):
        super().__init__(document_processor, embedding_provider, vector_store, retriever, config)
        self.llm_manager = config.get('llm_manager')  # LLM管理器
        self.max_context_length = config.get('max_context_length', 4000)
        self.answer_language = config.get('answer_language', 'zh-CN')
        self.include_sources = config.get('include_sources', True)
        
        # 统计信息
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_documents': 0,
            'total_chunks': 0
        }
        # 查询延迟记录（毫秒）
        self._latency_records: List[float] = []

    async def add_document(self, document: Document, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """添加文档并返回处理结果
        
        支持传入可选配置（如分块策略、大小与重叠）。
        返回包含处理后的 chunks 与嵌入信息的结果字典。
        """
        original_attrs: Dict[str, Any] = {}
        try:
            # 1. 按需覆盖文档处理器的配置
            if config:
                strategy = config.get('chunking_strategy')
                chunk_size = config.get('chunk_size')
                chunk_overlap = config.get('chunk_overlap')
                
                if strategy is not None and hasattr(self.document_processor, 'strategy'):
                    original_attrs['strategy'] = getattr(self.document_processor, 'strategy', None)
                    setattr(self.document_processor, 'strategy', strategy)
                if chunk_size is not None and hasattr(self.document_processor, 'chunk_size'):
                    original_attrs['chunk_size'] = getattr(self.document_processor, 'chunk_size', None)
                    setattr(self.document_processor, 'chunk_size', chunk_size)
                if chunk_overlap is not None and hasattr(self.document_processor, 'chunk_overlap'):
                    original_attrs['chunk_overlap'] = getattr(self.document_processor, 'chunk_overlap', None)
                    setattr(self.document_processor, 'chunk_overlap', chunk_overlap)

            # 1.5 支持预计算的块直接入库（跳过文档处理器）
            precomputed = None
            if config and 'precomputed_chunks' in config:
                precomputed = config.get('precomputed_chunks')
            if precomputed:
                # 规范化为 DocumentChunk 列表
                normalized_chunks: List[DocumentChunk] = []
                for idx, item in enumerate(precomputed):
                    if isinstance(item, DocumentChunk):
                        # 确保 doc_id 一致
                        chunk = item
                        chunk.doc_id = document.doc_id
                        normalized_chunks.append(chunk)
                    elif isinstance(item, dict):
                        content = item.get('content', '')
                        chunk_id = item.get('chunk_id') or f"{document.doc_id}_chunk_{idx}"
                        meta = item.get('metadata', {})
                        # 填充必要字段
                        normalized_chunks.append(DocumentChunk(
                            content=content,
                            chunk_id=chunk_id,
                            doc_id=document.doc_id,
                            chunk_index=idx,
                            start_char=0,
                            end_char=len(content),
                            metadata=meta,
                        ))
                    else:
                        # 非法项，跳过
                        continue

                if not normalized_chunks:
                    # 没有有效块则走常规处理
                    pass
                else:
                    # 生成嵌入
                    texts = [chunk.content for chunk in normalized_chunks]
                    embeddings = await self.embedding_provider.embed_batch(texts)
                    for chunk, embedding in zip(normalized_chunks, embeddings):
                        chunk.embedding = embedding

                    # 存储到向量数据库
                    success = await self.vector_store.add_chunks(normalized_chunks)
                    if success:
                        self.stats['total_documents'] += 1
                        self.stats['total_chunks'] += len(normalized_chunks)

                    return {'success': success, 'chunks': normalized_chunks, 'embeddings': embeddings, 'precomputed': True}
            
            # 2. 处理文档，生成文档块
            chunks = await self.document_processor.process_document(document)
            if not chunks:
                # 恢复原配置后返回
                if original_attrs:
                    for k, v in original_attrs.items():
                        try:
                            setattr(self.document_processor, k, v)
                        except Exception:
                            pass
                return {'success': False, 'chunks': [], 'embeddings': []}
            
            # 3. 生成嵌入
            texts = [chunk.content for chunk in chunks]
            embeddings = await self.embedding_provider.embed_batch(texts)
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
            
            # 4. 存储到向量数据库
            success = await self.vector_store.add_chunks(chunks)
            if success:
                self.stats['total_documents'] += 1
                self.stats['total_chunks'] += len(chunks)
            
            return {'success': success, 'chunks': chunks, 'embeddings': embeddings}
        except Exception as e:
            raise RAGError(f"添加文档失败: {str(e)}") from e
        finally:
            # 恢复文档处理器原始配置
            if original_attrs:
                for k, v in original_attrs.items():
                    try:
                        setattr(self.document_processor, k, v)
                    except Exception:
                        pass
    
    def validate_config(self) -> bool:
        """验证配置"""
        required_components = [
            self.document_processor,
            self.embedding_provider,
            self.vector_store,
            self.retriever
        ]
        
        return all(component is not None for component in required_components)
    
    # 注意：add_document 已更新为接受可选配置并返回结果字典
    # 旧的 boolean 版本已移除，避免方法重复覆盖
    
    async def query(self, query: str, **kwargs) -> RAGResponse:
        """执行RAG查询"""
        start_time = time.time()
        self.stats['total_queries'] += 1
        
        try:
            # 构建检索查询
            retrieval_query = RetrievalQuery(
                query=query,
                top_k=kwargs.get('top_k', 5),
                strategy=RetrievalStrategy(kwargs.get('strategy', 'similarity')),
                filters=kwargs.get('filters', {}),
                threshold=kwargs.get('threshold', 0.7),
                include_metadata=kwargs.get('include_metadata', True),
                rerank=kwargs.get('rerank', False),
                expand_query=kwargs.get('expand_query', False)
            )
            
            # 执行检索
            retrieved_chunks = await self.retriever.retrieve(retrieval_query)
            
            if not retrieved_chunks:
                return RAGResponse(
                    query=query,
                    answer="抱歉，没有找到相关信息。",
                    retrieved_chunks=[],
                    sources=[],
                    confidence=0.0,
                    execution_time=time.time() - start_time,
                    metadata={'no_results': True}
                )
            
            # 生成答案
            answer = await self._generate_answer(query, retrieved_chunks, **kwargs)
            
            # 提取来源
            sources = self._extract_sources(retrieved_chunks) if self.include_sources else []
            
            # 计算置信度
            confidence = self._calculate_confidence(retrieved_chunks, answer)
            
            execution_time = time.time() - start_time
            try:
                self._latency_records.append(execution_time * 1000.0)
            except Exception:
                pass
            
            self.stats['successful_queries'] += 1
            
            return RAGResponse(
                query=query,
                answer=answer,
                retrieved_chunks=retrieved_chunks,
                sources=sources,
                confidence=confidence,
                execution_time=execution_time,
                metadata={
                    'retrieval_strategy': retrieval_query.strategy.value,
                    'chunks_retrieved': len(retrieved_chunks),
                    'max_score': max(r.score for r in retrieved_chunks) if retrieved_chunks else 0
                }
            )
            
        except Exception as e:
            self.stats['failed_queries'] += 1
            execution_time = time.time() - start_time
            try:
                self._latency_records.append(execution_time * 1000.0)
            except Exception:
                pass
            
            return RAGResponse(
                query=query,
                answer=f"查询处理失败: {str(e)}",
                retrieved_chunks=[],
                sources=[],
                confidence=0.0,
                execution_time=execution_time,
                metadata={'error': str(e)}
            )
    
    async def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        try:
            # 获取文档的所有块
            chunks = await self.vector_store.list_chunks(doc_id=doc_id)
            
            if not chunks:
                return True  # 文档不存在，视为删除成功
            
            # 删除所有块
            chunk_ids = [chunk.chunk_id for chunk in chunks]
            success = await self.vector_store.delete_chunks(chunk_ids)
            
            if success:
                self.stats['total_documents'] -= 1
                self.stats['total_chunks'] -= len(chunks)
            
            return success
            
        except Exception as e:
            raise RAGError(f"删除文档失败: {str(e)}") from e
    
    async def update_document(self, document: Document) -> bool:
        """更新文档"""
        try:
            # 先删除旧文档
            await self.delete_document(document.doc_id)
            
            # 再添加新文档，兼容新的返回结构
            result = await self.add_document(document)
            if isinstance(result, dict):
                return bool(result.get('success', False))
            return bool(result)
            
        except Exception as e:
            raise RAGError(f"更新文档失败: {str(e)}") from e
    
    async def health_check(self) -> Dict[str, bool]:
        """健康检查"""
        health_status = {}
        
        # 检查各组件
        try:
            health_status['embedding_provider'] = await self.embedding_provider.health_check()
        except Exception:
            health_status['embedding_provider'] = False
        
        try:
            health_status['vector_store'] = await self.vector_store.health_check()
        except Exception:
            health_status['vector_store'] = False
        
        try:
            health_status['document_processor'] = self.document_processor.validate_config()
        except Exception:
            health_status['document_processor'] = False
        
        try:
            health_status['retriever'] = self.retriever.validate_config()
        except Exception:
            health_status['retriever'] = False
        
        return health_status
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        # 获取向量存储统计
        vector_stats = await self.vector_store.get_stats()
        # 嵌入缓存统计（如果可用）
        embedding_cache_stats = None
        try:
            if hasattr(self.embedding_provider, 'get_cache_stats'):
                embedding_cache_stats = self.embedding_provider.get_cache_stats()
        except Exception as _:
            embedding_cache_stats = {'error': 'cache_stats_unavailable'}
        # 延迟分位统计
        latencies = sorted(self._latency_records)
        def _percentile(arr: List[float], p: float) -> float:
            if not arr:
                return 0.0
            k = max(0, min(len(arr) - 1, int(round(p * (len(arr) - 1)))))
            return arr[k]
        latency_stats = {
            'count': len(latencies),
            'avg_ms': (sum(latencies) / len(latencies)) if latencies else 0.0,
            'p50_ms': _percentile(latencies, 0.50),
            'p95_ms': _percentile(latencies, 0.95),
        }
        index_scale = {
            'total_documents': vector_stats.get('total_documents'),
            'total_chunks': vector_stats.get('total_chunks'),
            'vector_dimension': vector_stats.get('vector_dimension')
        }
        
        return {
            **self.stats,
            'vector_store_stats': vector_stats,
            'embedding_cache_stats': embedding_cache_stats,
            'latency': latency_stats,
            'index': index_scale,
            'config': {
                'max_context_length': self.max_context_length,
                'answer_language': self.answer_language,
                'include_sources': self.include_sources
            }
        }

    def get_retrieval_query_cls(self):
        """用于路由层解耦，返回检索查询类"""
        return RetrievalQuery

    def get_retrieval_strategy_enum(self):
        """用于路由层解耦，返回检索策略枚举"""
        return RetrievalStrategy
    
    async def _generate_answer(self, query: str, 
                             retrieved_chunks: List[RetrievalResult], 
                             **kwargs) -> str:
        """生成答案"""
        if not self.llm_manager:
            # 如果没有LLM管理器，返回简单的拼接结果
            context_parts = []
            for result in retrieved_chunks[:3]:  # 只使用前3个结果
                context_parts.append(f"来源: {result.chunk.content[:200]}...")
            
            return f"基于检索到的信息：\n\n" + "\n\n".join(context_parts)
        
        # 构建上下文
        context = self._build_context(retrieved_chunks)
        
        # 构建提示
        prompt = self._build_prompt(query, context, **kwargs)
        
        # 调用LLM生成答案（这里需要集成LLM管理器）
        # 由于当前没有实际的LLM调用，返回模拟答案
        return f"基于检索到的{len(retrieved_chunks)}个相关文档片段，针对您的问题'{query}'的回答：\n\n" + \
               f"根据文档内容分析，{context[:200]}..."
    
    def _build_context(self, retrieved_chunks: List[RetrievalResult]) -> str:
        """构建上下文"""
        context_parts = []
        current_length = 0
        
        for result in retrieved_chunks:
            chunk_text = result.chunk.content
            
            # 检查是否超过最大上下文长度
            if current_length + len(chunk_text) > self.max_context_length:
                # 截断文本
                remaining_length = self.max_context_length - current_length
                if remaining_length > 100:  # 至少保留100字符
                    chunk_text = chunk_text[:remaining_length] + "..."
                    context_parts.append(chunk_text)
                break
            
            context_parts.append(chunk_text)
            current_length += len(chunk_text)
        
        return "\n\n".join(context_parts)
    
    def _build_prompt(self, query: str, context: str, **kwargs) -> str:
        """构建提示"""
        language = kwargs.get('language', self.answer_language)
        
        if language == 'zh-CN':
            prompt = f"""
请基于以下上下文信息回答用户的问题。

上下文信息：
{context}

用户问题：{query}

请提供准确、有用的回答，如果上下文信息不足以回答问题，请说明。

回答：
"""
        else:
            prompt = f"""
Please answer the user's question based on the following context information.

Context:
{context}

User Question: {query}

Please provide an accurate and helpful answer. If the context information is insufficient to answer the question, please indicate so.

Answer:
"""
        
        return prompt
    
    def _extract_sources(self, retrieved_chunks: List[RetrievalResult]) -> List[str]:
        """提取来源"""
        sources = set()
        
        for result in retrieved_chunks:
            chunk = result.chunk
            
            # 尝试从元数据中获取来源
            if 'source' in chunk.metadata:
                sources.add(chunk.metadata['source'])
            elif 'title' in chunk.metadata:
                sources.add(chunk.metadata['title'])
            else:
                sources.add(f"文档 {chunk.doc_id}")
        
        return list(sources)
    
    def _calculate_confidence(self, retrieved_chunks: List[RetrievalResult], 
                            answer: str) -> float:
        """计算置信度"""
        if not retrieved_chunks:
            return 0.0
        
        # 基于检索结果的平均分数
        avg_score = sum(r.score for r in retrieved_chunks) / len(retrieved_chunks)
        
        # 基于答案长度的调整
        answer_length_factor = min(len(answer) / 200, 1.0)
        
        # 基于检索结果数量的调整
        result_count_factor = min(len(retrieved_chunks) / 5, 1.0)
        
        # 综合置信度
        confidence = (avg_score * 0.6 + answer_length_factor * 0.2 + result_count_factor * 0.2)
        
        return min(confidence, 1.0)