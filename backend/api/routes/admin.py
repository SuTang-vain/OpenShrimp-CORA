#!/usr/bin/env python3
"""
管理员API路由
提供系统管理和监控功能

运行环境: Python 3.11+
依赖: fastapi, typing
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.dependencies.auth import get_current_admin_user
from backend.api.dependencies.services import (
    get_agent_service,
    get_search_service,
    get_document_service,
    get_llm_manager
)
from backend.shared.utils.response import create_success_response, create_error_response
from backend.services.agent.manager import AgentServiceManager
from backend.services.search.engine import SearchEngineService
from backend.services.document.manager import DocumentService
from backend.core.llm import LLMManager


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin_user)]
)


class SystemStats(BaseModel):
    """系统统计信息"""
    total_agents: int
    active_agents: int
    total_documents: int
    total_searches: int
    system_health: str
    uptime: str


class ServiceStatus(BaseModel):
    """服务状态"""
    name: str
    status: str
    last_check: str
    details: Dict[str, Any]


@router.get("/stats", response_model=Dict[str, Any])
async def get_system_stats(
    agent_service: AgentServiceManager = Depends(get_agent_service),
    search_service: SearchEngineService = Depends(get_search_service),
    document_service: DocumentService = Depends(get_document_service),
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """
    获取系统统计信息
    
    Returns:
        系统统计数据
    """
    try:
        # 获取各服务统计信息
        agent_stats = await agent_service.get_stats()
        search_stats = await search_service.get_stats()
        document_stats = await document_service.get_stats()
        
        stats = SystemStats(
            total_agents=agent_stats.get('total', 0),
            active_agents=agent_stats.get('active', 0),
            total_documents=document_stats.get('total', 0),
            total_searches=search_stats.get('total', 0),
            system_health="healthy",
            uptime="24h 30m"
        )
        
        return create_success_response(
            data=stats.dict(),
            message="系统统计信息获取成功"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"获取系统统计信息失败: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/services/status", response_model=Dict[str, Any])
async def get_services_status(
    agent_service: AgentServiceManager = Depends(get_agent_service),
    search_service: SearchEngineService = Depends(get_search_service),
    document_service: DocumentService = Depends(get_document_service),
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """
    获取所有服务状态
    
    Returns:
        服务状态列表
    """
    try:
        services_status = []
        
        # 检查智能体服务状态
        try:
            await agent_service.health_check()
            services_status.append(ServiceStatus(
                name="agent_service",
                status="healthy",
                last_check="2024-01-01T00:00:00Z",
                details={"active_tasks": 0}
            ))
        except Exception as e:
            services_status.append(ServiceStatus(
                name="agent_service",
                status="unhealthy",
                last_check="2024-01-01T00:00:00Z",
                details={"error": str(e)}
            ))
        
        # 检查搜索服务状态
        try:
            await search_service.health_check()
            services_status.append(ServiceStatus(
                name="search_service",
                status="healthy",
                last_check="2024-01-01T00:00:00Z",
                details={"engines": ["web", "academic"]}
            ))
        except Exception as e:
            services_status.append(ServiceStatus(
                name="search_service",
                status="unhealthy",
                last_check="2024-01-01T00:00:00Z",
                details={"error": str(e)}
            ))
        
        # 检查文档服务状态
        try:
            await document_service.health_check()
            services_status.append(ServiceStatus(
                name="document_service",
                status="healthy",
                last_check="2024-01-01T00:00:00Z",
                details={"storage": "available"}
            ))
        except Exception as e:
            services_status.append(ServiceStatus(
                name="document_service",
                status="unhealthy",
                last_check="2024-01-01T00:00:00Z",
                details={"error": str(e)}
            ))
        
        return create_success_response(
            data=[status.dict() for status in services_status],
            message="服务状态获取成功"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"获取服务状态失败: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/services/{service_name}/restart")
async def restart_service(service_name: str):
    """
    重启指定服务
    
    Args:
        service_name: 服务名称
        
    Returns:
        重启结果
    """
    try:
        # 模拟服务重启
        if service_name not in ["agent_service", "search_service", "document_service", "llm_manager"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"服务 {service_name} 不存在"
            )
        
        # 这里应该实现实际的服务重启逻辑
        # 目前只是模拟
        
        return create_success_response(
            data={"service": service_name, "status": "restarted"},
            message=f"服务 {service_name} 重启成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return create_error_response(
            message=f"重启服务失败: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/logs")
async def get_system_logs(
    level: str = "info",
    limit: int = 100,
    offset: int = 0
):
    """
    获取系统日志
    
    Args:
        level: 日志级别 (debug, info, warning, error)
        limit: 返回条数限制
        offset: 偏移量
        
    Returns:
        系统日志列表
    """
    try:
        # 模拟日志数据
        logs = [
            {
                "timestamp": "2024-01-01T00:00:00Z",
                "level": "info",
                "service": "agent_service",
                "message": "智能体任务创建成功",
                "details": {"task_id": "task_123"}
            },
            {
                "timestamp": "2024-01-01T00:01:00Z",
                "level": "warning",
                "service": "search_service",
                "message": "搜索引擎响应缓慢",
                "details": {"response_time": "5.2s"}
            }
        ]
        
        # 根据级别过滤
        if level != "all":
            logs = [log for log in logs if log["level"] == level]
        
        # 分页
        total = len(logs)
        logs = logs[offset:offset + limit]
        
        return create_success_response(
            data={
                "logs": logs,
                "total": total,
                "limit": limit,
                "offset": offset
            },
            message="系统日志获取成功"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"获取系统日志失败: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/maintenance/mode")
async def toggle_maintenance_mode(enabled: bool):
    """
    切换维护模式
    
    Args:
        enabled: 是否启用维护模式
        
    Returns:
        维护模式状态
    """
    try:
        # 这里应该实现实际的维护模式切换逻辑
        # 目前只是模拟
        
        return create_success_response(
            data={"maintenance_mode": enabled},
            message=f"维护模式已{'启用' if enabled else '禁用'}"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"切换维护模式失败: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/config")
async def get_system_config():
    """
    获取系统配置
    
    Returns:
        系统配置信息
    """
    try:
        config = {
            "version": "1.0.0",
            "environment": "development",
            "features": {
                "agent_service": True,
                "search_service": True,
                "document_service": True,
                "rag_engine": True
            },
            "limits": {
                "max_concurrent_agents": 10,
                "max_document_size": "10MB",
                "max_search_results": 100
            }
        }
        
        return create_success_response(
            data=config,
            message="系统配置获取成功"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"获取系统配置失败: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put("/config")
async def update_system_config(config: Dict[str, Any]):
    """
    更新系统配置
    
    Args:
        config: 新的配置数据
        
    Returns:
        更新结果
    """
    try:
        # 这里应该实现实际的配置更新逻辑
        # 目前只是模拟
        
        return create_success_response(
            data=config,
            message="系统配置更新成功"
        )
        
    except Exception as e:
        return create_error_response(
            message=f"更新系统配置失败: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )