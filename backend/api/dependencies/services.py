#!/usr/bin/env python3
"""
API服务依赖项
提供服务实例的依赖注入

运行环境: Python 3.11+
依赖: fastapi, typing
"""

from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, Request

from backend.services.agent.manager import AgentServiceManager
from backend.services.search.engine import SearchEngineService
from backend.services.document.service import DocumentService
from backend.services.user_service import UserService, user_service
from backend.core.rag import RAGEngine
from backend.core.llm import LLMManager
from backend.services.agent.camel_service import CamelAgentService


def get_services_from_request(request: Request) -> Dict[str, Any]:
    """从请求中获取服务字典
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        服务字典
        
    Raises:
        HTTPException: 服务不可用时
    """
    if not hasattr(request.state, 'services'):
        raise HTTPException(
            status_code=503,
            detail="服务不可用"
        )
    
    return request.state.services


def get_agent_manager(request: Request) -> AgentServiceManager:
    """获取智能体管理器
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        智能体管理器实例
        
    Raises:
        HTTPException: 服务不可用时
    """
    services = get_services_from_request(request)
    
    agent_manager = services.get('agent_manager')
    if not agent_manager:
        raise HTTPException(
            status_code=503,
            detail="智能体管理器服务不可用"
        )
    
    return agent_manager


# 别名函数
def get_agent_service(request: Request) -> AgentServiceManager:
    """获取智能体服务（get_agent_manager的别名）
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        智能体管理器实例
    """
    return get_agent_manager(request)


def get_camel_service(request: Request) -> CamelAgentService:
    """获取CAMEL智能体服务
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        CAMEL智能体服务实例
        
    Raises:
        HTTPException: 服务不可用时
    """
    services = get_services_from_request(request)
    camel_service = services.get('camel_service')
    if not camel_service:
        raise HTTPException(
            status_code=503,
            detail="CAMEL智能体服务不可用"
        )
    return camel_service


def get_search_service(request: Request) -> SearchEngineService:
    """获取搜索引擎服务
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        搜索引擎服务实例
        
    Raises:
        HTTPException: 服务不可用时
    """
    services = get_services_from_request(request)
    
    search_service = services.get('search_service')
    if not search_service:
        raise HTTPException(
            status_code=503,
            detail="搜索引擎服务不可用"
        )
    
    return search_service


def get_document_service(request: Request) -> DocumentService:
    """获取文档服务
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        文档服务实例
        
    Raises:
        HTTPException: 服务不可用时
    """
    services = get_services_from_request(request)
    
    document_service = services.get('document_service')
    if not document_service:
        raise HTTPException(
            status_code=503,
            detail="文档服务不可用"
        )
    
    return document_service


def get_rag_engine(request: Request) -> RAGEngine:
    """获取RAG引擎
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        RAG引擎实例
        
    Raises:
        HTTPException: 服务不可用时
    """
    services = get_services_from_request(request)
    
    rag_engine = services.get('rag_engine')
    if not rag_engine:
        raise HTTPException(
            status_code=503,
            detail="RAG引擎服务不可用"
        )
    
    return rag_engine


def get_llm_manager(request: Request) -> LLMManager:
    """获取LLM管理器
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        LLM管理器实例
        
    Raises:
        HTTPException: 服务不可用时
    """
    services = get_services_from_request(request)
    
    llm_manager = services.get('llm_manager')
    if not llm_manager:
        raise HTTPException(
            status_code=503,
            detail="LLM管理器服务不可用"
        )
    
    return llm_manager


def get_optional_agent_manager(request: Request) -> Optional[AgentServiceManager]:
    """获取可选的智能体管理器
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        智能体管理器实例或None
    """
    try:
        return get_agent_manager(request)
    except HTTPException:
        return None


def get_optional_search_service(request: Request) -> Optional[SearchEngineService]:
    """获取可选的搜索引擎服务
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        搜索引擎服务实例或None
    """
    try:
        return get_search_service(request)
    except HTTPException:
        return None


def get_optional_document_service(request: Request) -> Optional[DocumentService]:
    """获取可选的文档服务
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        文档服务实例或None
    """
    try:
        return get_document_service(request)
    except HTTPException:
        return None


def get_optional_rag_engine(request: Request) -> Optional[RAGEngine]:
    """获取可选的RAG引擎
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        RAG引擎实例或None
    """
    try:
        return get_rag_engine(request)
    except HTTPException:
        return None


def get_optional_llm_manager(request: Request) -> Optional[LLMManager]:
    """获取可选的LLM管理器
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        LLM管理器实例或None
    """
    try:
        return get_llm_manager(request)
    except HTTPException:
        return None


def get_optional_camel_service(request: Request) -> Optional[CamelAgentService]:
    """获取可选的CAMEL智能体服务
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        CAMEL智能体服务实例或None
    """
    try:
        return get_camel_service(request)
    except HTTPException:
        return None


# 服务健康检查依赖
async def check_agent_service_health(agent_manager: AgentServiceManager = Depends(get_agent_manager)) -> bool:
    """检查智能体服务健康状态
    
    Args:
        agent_manager: 智能体管理器
        
    Returns:
        健康状态
    """
    try:
        # 这里可以添加具体的健康检查逻辑
        return hasattr(agent_manager, 'health_check')
    except Exception:
        return False


async def check_search_service_health(search_service: SearchEngineService = Depends(get_search_service)) -> bool:
    """检查搜索服务健康状态
    
    Args:
        search_service: 搜索引擎服务
        
    Returns:
        健康状态
    """
    try:
        # 这里可以添加具体的健康检查逻辑
        return hasattr(search_service, 'health_check')
    except Exception:
        return False


async def check_document_service_health(document_service: DocumentService = Depends(get_document_service)) -> bool:
    """检查文档服务健康状态
    
    Args:
        document_service: 文档服务
        
    Returns:
        健康状态
    """
    try:
        # 这里可以添加具体的健康检查逻辑
        return hasattr(document_service, 'health_check')
    except Exception:
        return False


async def check_rag_engine_health(rag_engine: RAGEngine = Depends(get_rag_engine)) -> bool:
    """检查RAG引擎健康状态
    
    Args:
        rag_engine: RAG引擎
        
    Returns:
        健康状态
    """
    try:
        health_status = await rag_engine.health_check()
        return all(health_status.values())
    except Exception:
        return False


async def check_llm_manager_health(llm_manager: LLMManager = Depends(get_llm_manager)) -> bool:
    """检查LLM管理器健康状态
    
    Args:
        llm_manager: LLM管理器
        
    Returns:
        健康状态
    """
    try:
        health_status = await llm_manager.health_check()
        return any(health_status.values())  # 至少有一个LLM提供商可用
    except Exception:
        return False


# 服务统计信息依赖
async def get_service_stats(request: Request) -> Dict[str, Any]:
    """获取所有服务的统计信息
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        服务统计信息
    """
    services = get_services_from_request(request)
    stats = {}
    
    # RAG引擎统计
    rag_engine = services.get('rag_engine')
    if rag_engine:
        try:
            stats['rag_engine'] = await rag_engine.get_stats()
        except Exception as e:
            stats['rag_engine'] = {'error': str(e)}
    
    # LLM管理器统计
    llm_manager = services.get('llm_manager')
    if llm_manager:
        try:
            stats['llm_manager'] = llm_manager.get_provider_stats()
        except Exception as e:
            stats['llm_manager'] = {'error': str(e)}
    
    # 搜索服务统计
    search_service = services.get('search_service')
    if search_service and hasattr(search_service, 'get_stats'):
        try:
            stats['search_service'] = await search_service.get_stats()
        except Exception as e:
            stats['search_service'] = {'error': str(e)}
    
    # 文档服务统计
    document_service = services.get('document_service')
    if document_service and hasattr(document_service, 'get_stats'):
        try:
            stats['document_service'] = await document_service.get_stats()
        except Exception as e:
            stats['document_service'] = {'error': str(e)}
    
    # 智能体管理器统计
    agent_manager = services.get('agent_manager')
    if agent_manager and hasattr(agent_manager, 'get_stats'):
        try:
            stats['agent_manager'] = await agent_manager.get_stats()
        except Exception as e:
            stats['agent_manager'] = {'error': str(e)}
    
    return stats


# 服务配置依赖
def get_service_config(request: Request) -> Dict[str, Any]:
    """获取服务配置信息
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        服务配置信息
    """
    services = get_services_from_request(request)
    config = {}
    
    # LLM管理器配置
    llm_manager = services.get('llm_manager')
    if llm_manager and hasattr(llm_manager, 'get_config'):
        config['llm_manager'] = llm_manager.get_config()
    
    # 其他服务配置可以在这里添加
    
    return config


# 批量服务依赖
class ServiceBundle:
    """服务包装类
    
    将多个服务打包在一起，方便批量注入
    """
    
    def __init__(self, request: Request):
        self.services = get_services_from_request(request)
        self.agent_manager = self.services.get('agent_manager')
        self.search_service = self.services.get('search_service')
        self.document_service = self.services.get('document_service')
        self.rag_engine = self.services.get('rag_engine')
        self.llm_manager = self.services.get('llm_manager')
        self.camel_service = self.services.get('camel_service')
    
    def has_agent_manager(self) -> bool:
        """是否有智能体管理器"""
        return self.agent_manager is not None
    
    def has_search_service(self) -> bool:
        """是否有搜索服务"""
        return self.search_service is not None
    
    def has_document_service(self) -> bool:
        """是否有文档服务"""
        return self.document_service is not None
    
    def has_rag_engine(self) -> bool:
        """是否有RAG引擎"""
        return self.rag_engine is not None
    
    def has_llm_manager(self) -> bool:
        """是否有LLM管理器"""
        return self.llm_manager is not None

    def has_camel_service(self) -> bool:
        """是否有CAMEL智能体服务"""
        return self.camel_service is not None
    
    async def health_check(self) -> Dict[str, bool]:
        """批量健康检查"""
        health_status = {}
        
        if self.rag_engine:
            try:
                rag_health = await self.rag_engine.health_check()
                health_status['rag_engine'] = all(rag_health.values())
            except Exception:
                health_status['rag_engine'] = False
        
        if self.llm_manager:
            try:
                llm_health = await self.llm_manager.health_check()
                health_status['llm_manager'] = any(llm_health.values())
            except Exception:
                health_status['llm_manager'] = False
        
        # 其他服务的健康检查可以在这里添加
        
        return health_status


def get_user_service() -> UserService:
    """获取用户服务
    
    Returns:
        用户服务实例
    """
    return user_service


def get_service_bundle(request: Request) -> ServiceBundle:
    """获取服务包
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        服务包实例
    """
    return ServiceBundle(request)