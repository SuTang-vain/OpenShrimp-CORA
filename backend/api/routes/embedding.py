#!/usr/bin/env python3
"""
嵌入模型管理API路由
支持热切换当前RAG嵌入提供商并查询状态
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field

from backend.api.dependencies.auth import get_current_user
from backend.api.dependencies.services import get_rag_engine
from backend.shared.utils.response import create_success_response, create_error_response
from backend.core.rag import RAGEngine, EmbeddingModel, create_embedding_provider


router = APIRouter()


class EmbeddingSwitchRequest(BaseModel):
    model: str = Field(..., description="目标嵌入模型标识，如 'text-embedding-ada-002'、'openai-3-small'、'sentence-transformers'")
    config: Optional[Dict[str, Any]] = Field(None, description="可选配置覆盖，例如 api_key、cache 设置等")


@router.post("/rag/embedding/switch")
async def switch_embedding_model(
    request: EmbeddingSwitchRequest = Body(...),
    rag_engine: RAGEngine = Depends(get_rag_engine),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """热切换RAG嵌入模型，并保持检索器同步更新"""
    try:
        # 解析目标模型
        try:
            target_model = EmbeddingModel(request.model)
        except Exception:
            raise HTTPException(status_code=400, detail=f"不支持的嵌入模型: {request.model}")

        # 合并配置：在现有提供商配置上进行浅覆盖
        base_cfg = dict(getattr(rag_engine.embedding_provider, 'config', {}) or {})
        override_cfg = request.config or {}
        new_cfg = {**base_cfg, **override_cfg}

        # 创建新的提供商（自动应用缓存包装）
        new_provider = create_embedding_provider(target_model, new_cfg)

        # 更新引擎与检索器的提供商引用
        rag_engine.embedding_provider = new_provider
        if hasattr(rag_engine, 'retriever') and rag_engine.retriever:
            rag_engine.retriever.embedding_provider = new_provider

        # 返回当前状态
        info = {
            'provider_class': new_provider.__class__.__name__,
            'model': new_provider.model.value if hasattr(new_provider.model, 'value') else str(new_provider.model),
            'dimension': getattr(new_provider, 'dimension', None),
        }
        if hasattr(new_provider, 'get_cache_stats'):
            try:
                info['cache'] = new_provider.get_cache_stats()
            except Exception:
                info['cache'] = {'error': 'cache stats unavailable'}

        return create_success_response(data=info, message="嵌入模型切换成功")
    except HTTPException:
        raise
    except Exception as e:
        return create_error_response(message=f"切换失败: {str(e)}", status_code=500)


@router.get("/rag/embedding/current")
async def get_current_embedding_model(
    rag_engine: RAGEngine = Depends(get_rag_engine),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """查看当前RAG嵌入模型与缓存状态"""
    provider = rag_engine.embedding_provider
    info = {
        'provider_class': provider.__class__.__name__,
        'model': provider.model.value if hasattr(provider.model, 'value') else str(provider.model),
        'dimension': getattr(provider, 'dimension', None),
    }
    if hasattr(provider, 'get_cache_stats'):
        try:
            info['cache'] = provider.get_cache_stats()
        except Exception:
            info['cache'] = {'error': 'cache stats unavailable'}
    return create_success_response(data=info, message="当前嵌入模型信息")