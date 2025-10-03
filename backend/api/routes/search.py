#!/usr/bin/env python3
"""
搜索API路由
提供智能搜索和RAG查询功能

运行环境: Python 3.11+
依赖: fastapi, pydantic, typing
"""

import time
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Query, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator

from backend.api.schemas.search import (
    SearchRequest, SearchResponse, RAGQueryRequest, RAGQueryResponse,
    SearchFilters, SearchStrategy, StreamSearchResponse
)
from backend.api.dependencies.auth import get_current_user, require_api_key
from backend.api.dependencies.services import get_search_service, get_rag_engine
from backend.services.search.engine import SearchEngineService
from backend.core.rag import RAGEngine, RetrievalStrategy, EmbeddingModel, create_embedding_provider
from backend.shared.utils.response import create_success_response, create_error_response

# 创建路由器
router = APIRouter()


@router.post("/", response_model=SearchResponse)
async def search_root(
    request: SearchRequest,
    search_service: SearchEngineService = Depends(get_search_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """根路径搜索端点
    
    为了兼容前端请求，提供根路径的搜索功能
    """
    return await search_query(request, search_service, current_user)


@router.post("/query", response_model=SearchResponse)
async def search_query(
    request: SearchRequest,
    search_service: SearchEngineService = Depends(get_search_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """执行搜索查询
    
    支持多种搜索策略：
    - similarity: 语义相似度搜索
    - keyword: 关键词搜索
    - hybrid: 混合搜索
    - mmr: 最大边际相关性搜索
    """
    try:
        start_time = time.time()
        
        # 执行搜索
        results = await search_service.search(
            query=request.query,
            strategy=request.strategy,
            top_k=request.top_k,
            filters=request.filters.dict() if request.filters else {},
            threshold=request.threshold,
            include_metadata=request.include_metadata,
            user_id=current_user.get('id') if current_user else None
        )
        
        execution_time = time.time() - start_time
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            execution_time=execution_time,
            strategy=request.strategy,
            metadata={
                'user_id': current_user.get('id') if current_user else None,
                'timestamp': time.time(),
                'filters_applied': bool(request.filters)
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"搜索查询失败: {str(e)}"
        )


@router.post("/rag", response_model=RAGQueryResponse)
async def rag_query(
    request: RAGQueryRequest,
    rag_engine: RAGEngine = Depends(get_rag_engine),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """执行RAG查询
    
    检索增强生成查询，返回基于文档的智能回答
    """
    try:
        start_time = time.time()
        
        # 执行RAG查询
        rag_response = await rag_engine.query(
            query=request.query,
            top_k=request.top_k,
            strategy=request.strategy,
            filters=request.filters.dict() if request.filters else {},
            threshold=request.threshold,
            rerank=request.rerank,
            expand_query=request.expand_query,
            language=request.language,
            max_context_length=request.max_context_length
        )
        
        execution_time = time.time() - start_time
        
        return RAGQueryResponse(
            query=request.query,
            answer=rag_response.answer,
            sources=rag_response.sources,
            retrieved_chunks=[
                {
                    'content': result.chunk.content,
                    'score': result.score,
                    'source': result.chunk.metadata.get('source', ''),
                    'doc_id': result.chunk.doc_id,
                    'chunk_id': result.chunk.chunk_id
                }
                for result in rag_response.retrieved_chunks
            ],
            confidence=rag_response.confidence,
            execution_time=execution_time,
            metadata={
                **rag_response.metadata,
                'user_id': current_user.get('id') if current_user else None,
                'timestamp': time.time()
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"RAG查询失败: {str(e)}"
        )


@router.post("/rag/stream")
async def rag_query_stream(
    request: RAGQueryRequest,
    rag_engine: RAGEngine = Depends(get_rag_engine),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """流式RAG查询
    
    返回流式响应，适用于长文本生成
    """
    try:
        async def generate_stream():
            """生成流式响应"""
            import json
            
            # 首先执行检索
            start_time = time.time()
            
            # 构建检索查询
            from backend.core.rag.base import RetrievalQuery
            retrieval_query = RetrievalQuery(
                query=request.query,
                top_k=request.top_k,
                strategy=RetrievalStrategy(request.strategy),
                filters=request.filters.dict() if request.filters else {},
                threshold=request.threshold,
                rerank=request.rerank,
                expand_query=request.expand_query
            )
            
            # 执行检索
            retrieved_chunks = await rag_engine.retriever.retrieve(retrieval_query)
            
            # 发送检索结果
            retrieval_data = {
                'type': 'retrieval',
                'chunks': [
                    {
                        'content': result.chunk.content[:200] + '...',
                        'score': result.score,
                        'source': result.chunk.metadata.get('source', ''),
                        'doc_id': result.chunk.doc_id
                    }
                    for result in retrieved_chunks
                ],
                'total_chunks': len(retrieved_chunks)
            }
            yield f"data: {json.dumps(retrieval_data, ensure_ascii=False)}\n\n"
            
            # 模拟流式生成答案
            answer_parts = [
                "基于检索到的文档内容，",
                "我可以为您提供以下信息：\n\n",
                "根据相关文档的分析，",
                "主要观点包括：\n",
                "1. 核心概念和定义\n",
                "2. 关键特征和属性\n",
                "3. 实际应用场景\n\n",
                "综合以上信息，",
                "可以得出结论..."
            ]
            
            full_answer = ""
            for i, part in enumerate(answer_parts):
                full_answer += part
                
                chunk_data = {
                    'type': 'answer_chunk',
                    'content': part,
                    'full_content': full_answer,
                    'chunk_index': i,
                    'is_final': i == len(answer_parts) - 1
                }
                yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                
                # 模拟生成延迟
                import asyncio
                await asyncio.sleep(0.1)
            
            # 发送最终结果
            execution_time = time.time() - start_time
            final_data = {
                'type': 'final',
                'query': request.query,
                'answer': full_answer,
                'sources': list(set(
                    result.chunk.metadata.get('source', f'文档 {result.chunk.doc_id}')
                    for result in retrieved_chunks
                )),
                'confidence': 0.85,
                'execution_time': execution_time,
                'metadata': {
                    'chunks_retrieved': len(retrieved_chunks),
                    'user_id': current_user.get('id') if current_user else None,
                    'timestamp': time.time()
                }
            }
            yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"流式RAG查询失败: {str(e)}"
        )


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., description="查询文本"),
    limit: int = Query(default=5, ge=1, le=20, description="建议数量"),
    search_service: SearchEngineService = Depends(get_search_service)
):
    """获取搜索建议
    
    基于查询历史和文档内容提供搜索建议
    """
    try:
        suggestions = await search_service.get_suggestions(
            query=query,
            limit=limit
        )
        
        return create_success_response(
            data={
                'query': query,
                'suggestions': suggestions,
                'total': len(suggestions)
            },
            message="搜索建议获取成功"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"获取搜索建议失败: {str(e)}",
            status_code=500
        )


@router.get("/history")
async def get_search_history(
    limit: int = Query(default=20, ge=1, le=100, description="历史记录数量"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    search_service: SearchEngineService = Depends(get_search_service)
):
    """获取搜索历史
    
    返回用户的搜索历史记录
    """
    try:
        history = await search_service.get_search_history(
            user_id=current_user['id'],
            limit=limit,
            offset=offset
        )
        
        return create_success_response(
            data={
                'history': history,
                'total': len(history),
                'limit': limit,
                'offset': offset
            },
            message="搜索历史获取成功"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"获取搜索历史失败: {str(e)}",
            status_code=500
        )


@router.delete("/history")
async def clear_search_history(
    current_user: Dict[str, Any] = Depends(get_current_user),
    search_service: SearchEngineService = Depends(get_search_service)
):
    """清空搜索历史
    
    删除用户的所有搜索历史记录
    """
    try:
        await search_service.clear_search_history(
            user_id=current_user['id']
        )
        
        return create_success_response(
            message="搜索历史已清空"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"清空搜索历史失败: {str(e)}",
            status_code=500
        )


@router.get("/stats")
async def get_search_stats(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    search_service: SearchEngineService = Depends(get_search_service)
):
    """获取搜索统计信息
    
    返回搜索相关的统计数据
    """
    try:
        stats = await search_service.get_search_stats(
            user_id=current_user.get('id') if current_user else None
        )
        
        return create_success_response(
            data=stats,
            message="搜索统计信息获取成功"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"获取搜索统计信息失败: {str(e)}",
            status_code=500
        )


@router.get("/rag/stats")
async def get_rag_stats(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    rag_engine: RAGEngine = Depends(get_rag_engine)
):
    """获取RAG统计信息（含嵌入缓存指标）"""
    try:
        stats = await rag_engine.get_stats()
        return create_success_response(
            data=stats,
            message="RAG统计信息获取成功"
        )
    except Exception as e:
        return create_error_response(
            message=f"获取RAG统计信息失败: {str(e)}",
            status_code=500
        )


@router.get("/rag/processor")
async def get_rag_processor_config(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    rag_engine: RAGEngine = Depends(get_rag_engine)
):
    """查看当前文档处理器的分块策略与配置"""
    try:
        processor = rag_engine.document_processor

        def safe_attr(obj, name, default=None):
            try:
                return getattr(obj, name)
            except Exception:
                return default

        # 判断是否为增强型处理器，优先读取 text 子处理器配置
        is_enhanced = hasattr(processor, 'text')
        base = processor.text if is_enhanced else processor

        strategy = safe_attr(base, 'strategy')
        strategy_value = strategy.value if hasattr(strategy, 'value') else str(strategy)

        data = {
            'processor_type': processor.__class__.__name__,
            'is_enhanced': bool(is_enhanced),
            'effective_strategy': strategy_value,
            'chunk_size': safe_attr(base, 'chunk_size'),
            'chunk_overlap': safe_attr(base, 'chunk_overlap'),
            'min_chunk_size': safe_attr(base, 'min_chunk_size'),
            'max_chunk_size': safe_attr(base, 'max_chunk_size'),
            'dynamic_chunking': bool(safe_attr(base, 'dynamic_chunking', False)),
            'supported_types': [t.value for t in safe_attr(processor, 'get_supported_types')()]
        }

        return create_success_response(
            data=data,
            message="当前文档处理器配置获取成功"
        )
    except Exception as e:
        return create_error_response(
            message=f"获取文档处理器配置失败: {str(e)}",
            status_code=500
        )


@router.post("/feedback")
async def submit_search_feedback(
    feedback_data: Dict[str, Any] = Body(...),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    search_service: SearchEngineService = Depends(get_search_service)
):
    """提交搜索反馈
    
    用户可以对搜索结果进行评价和反馈
    """
    try:
        # 验证反馈数据
        required_fields = ['query', 'rating', 'feedback_type']
        for field in required_fields:
            if field not in feedback_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"缺少必需字段: {field}"
                )
        
        # 提交反馈
        feedback_id = await search_service.submit_feedback(
            user_id=current_user.get('id') if current_user else None,
            query=feedback_data['query'],
            rating=feedback_data['rating'],
            feedback_type=feedback_data['feedback_type'],
            comments=feedback_data.get('comments', ''),
            metadata=feedback_data.get('metadata', {})
        )
        
        return create_success_response(
            data={'feedback_id': feedback_id},
            message="反馈提交成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return create_error_response(
            message=f"提交反馈失败: {str(e)}",
            status_code=500
        )


@router.get("/popular")
async def get_popular_queries(
    limit: int = Query(default=10, ge=1, le=50, description="热门查询数量"),
    time_range: str = Query(default="7d", description="时间范围 (1d, 7d, 30d)"),
    search_service: SearchEngineService = Depends(get_search_service)
):
    """获取热门查询
    
    返回指定时间范围内的热门搜索查询
    """
    try:
        popular_queries = await search_service.get_popular_queries(
            limit=limit,
            time_range=time_range
        )
        
        return create_success_response(
            data={
                'queries': popular_queries,
                'total': len(popular_queries),
                'time_range': time_range
            },
            message="热门查询获取成功"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"获取热门查询失败: {str(e)}",
            status_code=500
        )


@router.post("/analyze")
async def analyze_query(
    query: str = Body(..., embed=True),
    search_service: SearchEngineService = Depends(get_search_service)
):
    """分析查询
    
    分析查询的意图、关键词和复杂度
    """
    try:
        analysis = await search_service.analyze_query(query)
        
        return create_success_response(
            data=analysis,
            message="查询分析完成"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"查询分析失败: {str(e)}",
            status_code=500
        )