#!/usr/bin/env python3
"""
调试与诊断 API 路由
提供向量库统计与指定文档块的嵌入存在性/维度检查
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends

from backend.api.dependencies.auth import get_current_user
from backend.api.dependencies.services import get_rag_engine
from backend.shared.utils.response import create_success_response, create_error_response
from backend.core.rag import RAGEngine


router = APIRouter()


@router.get("/debug/vector-store/stats")
async def debug_vector_store_stats(
    rag_engine: RAGEngine = Depends(get_rag_engine),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """查看向量库统计与当前嵌入提供商信息"""
    try:
        vs = rag_engine.vector_store
        provider = rag_engine.embedding_provider

        vector_stats = await vs.get_stats()
        provider_info = {
            'provider_class': provider.__class__.__name__,
            'model': getattr(getattr(provider, 'model', None), 'value', None) or str(getattr(provider, 'model', None)),
            'dimension': getattr(provider, 'dimension', None),
        }

        retriever_cfg = getattr(rag_engine, 'retriever', None)
        retriever_info = None
        try:
            if retriever_cfg:
                retriever_info = {
                    'default_top_k': getattr(retriever_cfg, 'default_top_k', None),
                    'default_threshold': getattr(retriever_cfg, 'default_threshold', None),
                    'enable_rerank': getattr(retriever_cfg, 'enable_rerank', None),
                }
        except Exception:
            retriever_info = None

        return create_success_response(
            data={
                'vector_store': vector_stats,
                'embedding_provider': provider_info,
                'retriever': retriever_info,
            },
            message="向量库与嵌入提供商统计"
        )
    except Exception as e:
        return create_error_response(
            message=f"获取调试统计失败: {str(e)}",
            status_code=500
        )

@router.get("/debug/vector-store/docs")
async def debug_vector_store_docs(
    rag_engine: RAGEngine = Depends(get_rag_engine),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """列出向量库中已索引的文档ID及统计"""
    try:
        chunks = await rag_engine.vector_store.list_chunks(doc_id=None, limit=5000)
        doc_map: Dict[str, Dict[str, Any]] = {}
        for ch in chunks:
            d = doc_map.setdefault(ch.doc_id, {"doc_id": ch.doc_id, "chunk_count": 0, "has_null_embeddings": 0})
            d["chunk_count"] += 1
            if getattr(ch, 'embedding', None) is None:
                d["has_null_embeddings"] += 1
        return create_success_response(
            data={
                'documents': list(doc_map.values()),
                'total_distinct_docs': len(doc_map),
                'total_chunks_scanned': len(chunks)
            },
            message="向量库文档ID列表"
        )
    except Exception as e:
        return create_error_response(
            message=f"列出向量库文档失败: {str(e)}",
            status_code=500
        )


@router.get("/debug/vector-store/chunks/{doc_id}")
async def debug_vector_store_doc_chunks(
    doc_id: str,
    rag_engine: RAGEngine = Depends(get_rag_engine),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """列出指定文档的块，显示嵌入存在性与维度"""
    try:
        chunks = await rag_engine.vector_store.list_chunks(doc_id=doc_id, limit=1000)

        items = []
        for ch in chunks:
            emb = getattr(ch, 'embedding', None)
            items.append({
                'chunk_id': ch.chunk_id,
                'doc_id': ch.doc_id,
                'chunk_index': ch.chunk_index,
                'content_len': len(ch.content or ''),
                'has_embedding': emb is not None,
                'embedding_len': len(emb) if isinstance(emb, list) else 0,
            })

        return create_success_response(
            data={
                'doc_id': doc_id,
                'total_chunks': len(chunks),
                'items': items,
            },
            message="文档块嵌入检查"
        )
    except Exception as e:
        return create_error_response(
            message=f"获取文档块嵌入信息失败: {str(e)}",
            status_code=500
        )

@router.get("/debug/vector-store/chunks")
async def debug_vector_store_all_chunks(
    rag_engine: RAGEngine = Depends(get_rag_engine),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """列出向量库所有块（最多5000），显示嵌入存在性与维度"""
    try:
        chunks = await rag_engine.vector_store.list_chunks(doc_id=None, limit=5000)
        items = []
        for ch in chunks:
            emb = getattr(ch, 'embedding', None)
            items.append({
                'chunk_id': ch.chunk_id,
                'doc_id': ch.doc_id,
                'chunk_index': ch.chunk_index,
                'content_len': len(ch.content or ''),
                'has_embedding': emb is not None,
                'embedding_len': len(emb) if isinstance(emb, list) else 0,
            })
        return create_success_response(
            data={
                'total_chunks': len(chunks),
                'items': items,
            },
            message="所有块嵌入检查"
        )
    except Exception as e:
        return create_error_response(
            message=f"获取所有块嵌入信息失败: {str(e)}",
            status_code=500
        )

@router.post("/debug/vector-store/rebuild-embeddings")
async def debug_vector_store_rebuild_embeddings(
    rag_engine: RAGEngine = Depends(get_rag_engine),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """为向量库中缺失嵌入的块重建嵌入（不修改元数据，仅填充向量）"""
    try:
        vs = rag_engine.vector_store
        provider = rag_engine.embedding_provider

        # 读取所有块
        chunks = await vs.list_chunks(doc_id=None, limit=10000)
        missing = [ch for ch in chunks if getattr(ch, 'embedding', None) is None]
        if not missing:
            return create_success_response(
                data={
                    'total_chunks': len(chunks),
                    'repaired': 0,
                    'message': '没有缺失嵌入的块'
                },
                message="嵌入无需重建"
            )

        texts = [ch.content for ch in missing]
        # 生成嵌入
        embeddings = await provider.embed_batch(texts)
        if not embeddings or len(embeddings) != len(missing):
            raise RuntimeError("嵌入生成失败或数量不匹配")

        # 更新块向量
        repaired = 0
        for ch, emb in zip(missing, embeddings):
            ch.embedding = emb
            ok = await vs.update_chunk(ch)
            if ok:
                repaired += 1

        return create_success_response(
            data={
                'total_chunks': len(chunks),
                'missing_before': len(missing),
                'repaired': repaired
            },
            message="已重建缺失嵌入"
        )
    except Exception as e:
        return create_error_response(
            message=f"重建嵌入失败: {str(e)}",
            status_code=500
        )