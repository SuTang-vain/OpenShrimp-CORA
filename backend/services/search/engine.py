#!/usr/bin/env python3
"""
搜索引擎服务
提供统一的搜索功能和管理

运行环境: Python 3.11+
依赖: asyncio, typing, time
"""

import asyncio
import time
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from collections import defaultdict

from backend.core.rag import RAGEngine, RetrievalStrategy
from backend.core.rag.base import RetrievalQuery, Document
from backend.api.schemas.search import SearchResultItem, SearchSuggestion, SearchHistoryItem


class SearchEngineService:
    """搜索引擎服务
    
    统一管理各种搜索功能，包括RAG搜索、关键词搜索等
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rag_engine = config.get('rag_engine')
        self.max_results = config.get('max_results', 20)
        self.default_timeout = config.get('default_timeout', 30.0)
        self.enable_web_search = config.get('enable_web_search', True)
        self.enable_document_search = config.get('enable_document_search', True)
        
        # 搜索历史和统计（简化实现，生产环境应使用数据库）
        self.search_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.search_stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_execution_time': 0.0,
            'strategy_usage': defaultdict(int),
            'popular_queries': defaultdict(int)
        }
        
        # 搜索建议缓存
        self.suggestion_cache: Dict[str, List[SearchSuggestion]] = {}
        
        # 反馈数据
        self.feedback_data: List[Dict[str, Any]] = []
    
    async def search(
        self,
        query: str,
        strategy: str = "similarity",
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        threshold: float = 0.7,
        include_metadata: bool = True,
        user_id: Optional[str] = None
    ) -> List[SearchResultItem]:
        """执行搜索
        
        Args:
            query: 搜索查询
            strategy: 搜索策略
            top_k: 返回结果数量
            filters: 搜索过滤器
            threshold: 相似度阈值
            include_metadata: 是否包含元数据
            user_id: 用户ID
            
        Returns:
            搜索结果列表
        """
        start_time = time.time()
        
        try:
            self.search_stats['total_queries'] += 1
            self.search_stats['strategy_usage'][strategy] += 1
            self.search_stats['popular_queries'][query.lower()] += 1
            
            # 记录搜索历史
            if user_id:
                await self._record_search_history(
                    user_id=user_id,
                    query=query,
                    strategy=strategy,
                    timestamp=datetime.now()
                )
            
            # 根据策略执行搜索
            if strategy in ["similarity", "hybrid", "mmr", "semantic_hybrid"]:
                results = await self._rag_search(
                    query=query,
                    strategy=strategy,
                    top_k=top_k,
                    filters=filters,
                    threshold=threshold
                )
            elif strategy == "keyword":
                results = await self._keyword_search(
                    query=query,
                    top_k=top_k,
                    filters=filters
                )
            else:
                # 默认使用相似度搜索
                results = await self._rag_search(
                    query=query,
                    strategy="similarity",
                    top_k=top_k,
                    filters=filters,
                    threshold=threshold
                )
            
            # 后处理结果
            processed_results = await self._post_process_results(
                results=results,
                query=query,
                include_metadata=include_metadata
            )
            
            execution_time = time.time() - start_time
            self.search_stats['successful_queries'] += 1
            self.search_stats['total_execution_time'] += execution_time
            
            # 更新搜索历史的结果数量
            if user_id:
                await self._update_search_history(
                    user_id=user_id,
                    query=query,
                    results_count=len(processed_results),
                    execution_time=execution_time
                )
            
            return processed_results
            
        except Exception as e:
            self.search_stats['failed_queries'] += 1
            raise Exception(f"搜索执行失败: {str(e)}")
    
    async def _rag_search(
        self,
        query: str,
        strategy: str,
        top_k: int,
        filters: Optional[Dict[str, Any]],
        threshold: float
    ) -> List[Dict[str, Any]]:
        """RAG搜索"""
        if not self.rag_engine:
            raise Exception("RAG引擎不可用")
        
        # 构建检索查询
        retrieval_query = RetrievalQuery(
            query=query,
            top_k=top_k,
            strategy=RetrievalStrategy(strategy),
            filters=filters or {},
            threshold=threshold,
            include_metadata=True
        )
        
        # 执行检索
        retrieval_results = await self.rag_engine.retriever.retrieve(retrieval_query)
        
        # 转换为搜索结果格式
        results = []
        for i, result in enumerate(retrieval_results):
            search_result = {
                'content': result.chunk.content,
                'score': result.score,
                'rank': i + 1,
                'doc_id': result.chunk.doc_id,
                'chunk_id': result.chunk.chunk_id,
                'source': result.chunk.metadata.get('source', ''),
                'title': result.chunk.metadata.get('title', ''),
                'url': result.chunk.metadata.get('url', ''),
                'metadata': result.chunk.metadata,
                'retrieval_method': result.retrieval_method
            }
            results.append(search_result)
        
        return results
    
    async def _keyword_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """关键词搜索"""
        if not self.rag_engine:
            raise Exception("RAG引擎不可用")
        
        # 获取所有文档块
        all_chunks = await self.rag_engine.vector_store.list_chunks(limit=1000)
        
        # 简单的关键词匹配
        query_terms = query.lower().split()
        results = []
        
        for chunk in all_chunks:
            content_lower = chunk.content.lower()
            
            # 应用过滤器
            if filters:
                if not self._apply_filters(chunk, filters):
                    continue
            
            # 计算关键词匹配分数
            matches = sum(1 for term in query_terms if term in content_lower)
            if matches > 0:
                score = matches / len(query_terms)
                
                result = {
                    'content': chunk.content,
                    'score': score,
                    'rank': 0,  # 稍后重新排序
                    'doc_id': chunk.doc_id,
                    'chunk_id': chunk.chunk_id,
                    'source': chunk.metadata.get('source', ''),
                    'title': chunk.metadata.get('title', ''),
                    'url': chunk.metadata.get('url', ''),
                    'metadata': chunk.metadata,
                    'keyword_matches': matches
                }
                results.append(result)
        
        # 按分数排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 更新排名
        for i, result in enumerate(results[:top_k]):
            result['rank'] = i + 1
        
        return results[:top_k]
    
    def _apply_filters(self, chunk, filters: Dict[str, Any]) -> bool:
        """应用过滤器"""
        for key, value in filters.items():
            if key == 'doc_type':
                if chunk.metadata.get('doc_type') != value:
                    return False
            elif key == 'source':
                if chunk.metadata.get('source') != value:
                    return False
            elif key == 'tags':
                chunk_tags = chunk.metadata.get('tags', [])
                if not any(tag in chunk_tags for tag in value):
                    return False
            elif key == 'language':
                if chunk.metadata.get('language') != value:
                    return False
            elif key == 'author':
                if chunk.metadata.get('author') != value:
                    return False
            elif key in chunk.metadata:
                if chunk.metadata[key] != value:
                    return False
        return True
    
    async def _post_process_results(
        self,
        results: List[Dict[str, Any]],
        query: str,
        include_metadata: bool
    ) -> List[SearchResultItem]:
        """后处理搜索结果"""
        processed_results = []
        
        for result in results:
            # 生成高亮片段
            highlight = self._generate_highlight(result['content'], query)
            
            # 创建搜索结果项
            search_item = SearchResultItem(
                content=result['content'],
                score=result['score'],
                rank=result['rank'],
                doc_id=result['doc_id'],
                chunk_id=result['chunk_id'],
                source=result.get('source'),
                title=result.get('title'),
                url=result.get('url'),
                metadata=result.get('metadata') if include_metadata else None,
                highlight=highlight
            )
            
            processed_results.append(search_item)
        
        return processed_results
    
    def _generate_highlight(self, content: str, query: str) -> str:
        """生成高亮片段"""
        query_terms = query.lower().split()
        content_lower = content.lower()
        
        # 简单的高亮实现
        highlighted = content
        for term in query_terms:
            if term in content_lower:
                # 找到第一个匹配位置
                start_idx = content_lower.find(term)
                if start_idx != -1:
                    # 提取上下文
                    context_start = max(0, start_idx - 50)
                    context_end = min(len(content), start_idx + len(term) + 50)
                    
                    context = content[context_start:context_end]
                    
                    # 添加高亮标记
                    highlighted = context.replace(
                        content[start_idx:start_idx + len(term)],
                        f"<mark>{content[start_idx:start_idx + len(term)]}</mark>"
                    )
                    break
        
        return highlighted
    
    async def get_suggestions(
        self,
        query: str,
        limit: int = 5
    ) -> List[SearchSuggestion]:
        """获取搜索建议"""
        # 检查缓存
        cache_key = f"{query.lower()}_{limit}"
        if cache_key in self.suggestion_cache:
            return self.suggestion_cache[cache_key]
        
        suggestions = []
        
        # 基于热门查询生成建议
        popular_queries = sorted(
            self.search_stats['popular_queries'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        query_lower = query.lower()
        for popular_query, frequency in popular_queries:
            if query_lower in popular_query or popular_query.startswith(query_lower):
                suggestion = SearchSuggestion(
                    text=popular_query,
                    score=frequency / max(self.search_stats['popular_queries'].values()),
                    type="query_completion",
                    metadata={
                        "frequency": frequency,
                        "last_used": datetime.now().isoformat()
                    }
                )
                suggestions.append(suggestion)
                
                if len(suggestions) >= limit:
                    break
        
        # 如果建议不足，添加一些通用建议
        if len(suggestions) < limit:
            generic_suggestions = [
                f"{query} 教程",
                f"{query} 应用",
                f"{query} 原理",
                f"{query} 案例",
                f"{query} 发展"
            ]
            
            for generic in generic_suggestions:
                if len(suggestions) >= limit:
                    break
                
                suggestion = SearchSuggestion(
                    text=generic,
                    score=0.5,
                    type="generic_expansion",
                    metadata={"generated": True}
                )
                suggestions.append(suggestion)
        
        # 缓存结果
        self.suggestion_cache[cache_key] = suggestions
        
        return suggestions
    
    async def get_search_history(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[SearchHistoryItem]:
        """获取搜索历史"""
        user_history = self.search_history.get(user_id, [])
        
        # 按时间倒序排序
        sorted_history = sorted(
            user_history,
            key=lambda x: x['timestamp'],
            reverse=True
        )
        
        # 分页
        paginated_history = sorted_history[offset:offset + limit]
        
        # 转换为SearchHistoryItem
        history_items = []
        for item in paginated_history:
            history_item = SearchHistoryItem(
                query=item['query'],
                timestamp=item['timestamp'],
                strategy=item['strategy'],
                results_count=item.get('results_count', 0),
                execution_time=item.get('execution_time', 0.0),
                user_rating=item.get('user_rating')
            )
            history_items.append(history_item)
        
        return history_items
    
    async def clear_search_history(self, user_id: str) -> None:
        """清空搜索历史"""
        if user_id in self.search_history:
            del self.search_history[user_id]
    
    async def get_search_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取搜索统计信息"""
        stats = self.search_stats.copy()
        
        # 计算平均执行时间
        if stats['successful_queries'] > 0:
            stats['avg_execution_time'] = stats['total_execution_time'] / stats['successful_queries']
        else:
            stats['avg_execution_time'] = 0.0
        
        # 获取热门查询
        popular_queries = sorted(
            stats['popular_queries'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        stats['popular_queries'] = dict(popular_queries)
        
        # 如果指定了用户ID，添加用户特定统计
        if user_id and user_id in self.search_history:
            user_history = self.search_history[user_id]
            stats['user_stats'] = {
                'total_searches': len(user_history),
                'recent_searches': [item['query'] for item in user_history[-5:]],
                'favorite_strategy': self._get_user_favorite_strategy(user_history)
            }
        
        return stats
    
    def _get_user_favorite_strategy(self, user_history: List[Dict[str, Any]]) -> str:
        """获取用户最喜欢的搜索策略"""
        strategy_count = defaultdict(int)
        for item in user_history:
            strategy_count[item['strategy']] += 1
        
        if strategy_count:
            return max(strategy_count.items(), key=lambda x: x[1])[0]
        return "similarity"
    
    async def submit_feedback(
        self,
        user_id: Optional[str],
        query: str,
        rating: int,
        feedback_type: str,
        comments: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """提交搜索反馈"""
        feedback_id = f"feedback_{int(time.time() * 1000)}"
        
        feedback = {
            'feedback_id': feedback_id,
            'user_id': user_id,
            'query': query,
            'rating': rating,
            'feedback_type': feedback_type,
            'comments': comments,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.feedback_data.append(feedback)
        
        return feedback_id
    
    async def get_popular_queries(
        self,
        limit: int = 10,
        time_range: str = "7d"
    ) -> List[Dict[str, Any]]:
        """获取热门查询"""
        # 简化实现，返回所有时间的热门查询
        popular_queries = sorted(
            self.search_stats['popular_queries'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        result = []
        for query, count in popular_queries:
            result.append({
                'query': query,
                'count': count,
                'percentage': (count / self.search_stats['total_queries']) * 100 if self.search_stats['total_queries'] > 0 else 0
            })
        
        return result
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """分析查询"""
        # 简化的查询分析实现
        words = query.split()
        
        # 判断查询意图
        intent = self._determine_intent(query)
        
        # 提取关键词
        keywords = [word.lower() for word in words if len(word) > 2]
        
        # 实体识别（简化）
        entities = self._extract_entities(query)
        
        # 复杂度评估
        complexity = self._assess_complexity(query)
        
        # 语言检测
        language = self._detect_language(query)
        
        # 建议策略
        suggested_strategy = self._suggest_strategy(query, complexity)
        
        return {
            'query': query,
            'intent': intent,
            'keywords': keywords,
            'entities': entities,
            'complexity': complexity,
            'language': language,
            'suggested_strategy': suggested_strategy,
            'confidence': 0.8  # 简化的置信度
        }
    
    def _determine_intent(self, query: str) -> str:
        """确定查询意图"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['什么是', '定义', '含义']):
            return 'definition'
        elif any(word in query_lower for word in ['如何', '怎么', '方法']):
            return 'how_to'
        elif any(word in query_lower for word in ['比较', '区别', '差异']):
            return 'comparison'
        elif any(word in query_lower for word in ['列出', '有哪些', '包括']):
            return 'list'
        elif '?' in query or '？' in query:
            return 'factual'
        else:
            return 'explanation'
    
    def _extract_entities(self, query: str) -> List[Dict[str, Any]]:
        """提取实体（简化实现）"""
        entities = []
        
        # 简单的实体识别
        tech_terms = ['AI', '人工智能', '机器学习', '深度学习', '神经网络', '算法']
        domain_terms = ['医疗', '金融', '教育', '交通', '制造业']
        
        for term in tech_terms:
            if term in query:
                entities.append({'text': term, 'type': 'TECHNOLOGY'})
        
        for term in domain_terms:
            if term in query:
                entities.append({'text': term, 'type': 'DOMAIN'})
        
        return entities
    
    def _assess_complexity(self, query: str) -> str:
        """评估查询复杂度"""
        words = query.split()
        
        if len(words) <= 3:
            return 'simple'
        elif len(words) <= 8:
            return 'medium'
        else:
            return 'complex'
    
    def _detect_language(self, query: str) -> str:
        """检测语言（简化实现）"""
        # 简单的中英文检测
        chinese_chars = sum(1 for char in query if '\u4e00' <= char <= '\u9fff')
        total_chars = len(query.replace(' ', ''))
        
        if chinese_chars / total_chars > 0.5:
            return 'zh-CN'
        else:
            return 'en-US'
    
    def _suggest_strategy(self, query: str, complexity: str) -> str:
        """建议搜索策略"""
        if complexity == 'simple':
            return 'similarity'
        elif complexity == 'medium':
            return 'hybrid'
        else:
            return 'semantic_hybrid'
    
    async def _record_search_history(
        self,
        user_id: str,
        query: str,
        strategy: str,
        timestamp: datetime
    ) -> None:
        """记录搜索历史"""
        history_item = {
            'query': query,
            'strategy': strategy,
            'timestamp': timestamp,
            'results_count': 0,  # 稍后更新
            'execution_time': 0.0  # 稍后更新
        }
        
        self.search_history[user_id].append(history_item)
        
        # 限制历史记录数量
        max_history = 1000
        if len(self.search_history[user_id]) > max_history:
            self.search_history[user_id] = self.search_history[user_id][-max_history:]
    
    async def _update_search_history(
        self,
        user_id: str,
        query: str,
        results_count: int,
        execution_time: float
    ) -> None:
        """更新搜索历史"""
        if user_id in self.search_history:
            user_history = self.search_history[user_id]
            # 更新最后一条记录
            if user_history and user_history[-1]['query'] == query:
                user_history[-1]['results_count'] = results_count
                user_history[-1]['execution_time'] = execution_time
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查RAG引擎
            if self.rag_engine:
                rag_health = await self.rag_engine.health_check()
                return all(rag_health.values())
            return True
        except Exception:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return {
            'search_stats': self.search_stats,
            'total_users': len(self.search_history),
            'total_feedback': len(self.feedback_data),
            'cache_size': len(self.suggestion_cache),
            'config': {
                'max_results': self.max_results,
                'default_timeout': self.default_timeout,
                'enable_web_search': self.enable_web_search,
                'enable_document_search': self.enable_document_search
            }
        }