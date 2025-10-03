#!/usr/bin/env python3
"""
健康检查API路由
提供系统健康状态监控

运行环境: Python 3.11+
依赖: fastapi, psutil, typing
"""

import time
import psutil
import platform
from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from backend.api.dependencies.services import (
    get_service_bundle, get_service_stats, ServiceBundle
)
from backend.infrastructure.config.settings import get_settings
from backend.shared.utils.response import create_success_response

# 创建路由器
router = APIRouter()


class HealthStatus(BaseModel):
    """健康状态模型"""
    status: str
    timestamp: float
    uptime: float
    version: str
    environment: str


class SystemInfo(BaseModel):
    """系统信息模型"""
    platform: str
    python_version: str
    cpu_count: int
    memory_total: int
    memory_available: int
    memory_percent: float
    cpu_percent: float
    disk_usage: Dict[str, Any]


class ServiceHealth(BaseModel):
    """服务健康状态模型"""
    service_name: str
    status: str
    last_check: float
    details: Dict[str, Any]


class DetailedHealthResponse(BaseModel):
    """详细健康检查响应模型"""
    overall_status: str
    timestamp: float
    uptime: float
    system_info: SystemInfo
    services: List[ServiceHealth]
    performance_metrics: Dict[str, Any]
    configuration: Dict[str, Any]


# 应用启动时间
start_time = time.time()


@router.get("/", response_model=HealthStatus)
async def basic_health_check():
    """基础健康检查
    
    返回应用的基本健康状态
    """
    settings = get_settings()
    current_time = time.time()
    
    return HealthStatus(
        status="healthy",
        timestamp=current_time,
        uptime=current_time - start_time,
        version=settings.version,
        environment=settings.environment
    )


@router.get("/detailed")
async def detailed_health_check(
    service_bundle: ServiceBundle = Depends(get_service_bundle),
    service_stats: Dict[str, Any] = Depends(get_service_stats)
):
    """详细健康检查
    
    返回系统的详细健康状态，包括服务状态、系统信息等
    """
    settings = get_settings()
    current_time = time.time()
    
    # 获取系统信息
    system_info = await get_system_info()
    
    # 检查服务健康状态
    service_health = await check_services_health(service_bundle)
    
    # 获取性能指标
    performance_metrics = await get_performance_metrics()
    
    # 获取配置信息（敏感信息已脱敏）
    config_info = get_safe_config_info(settings)
    
    # 确定整体状态
    overall_status = determine_overall_status(service_health, system_info)
    
    return create_success_response(
        data=DetailedHealthResponse(
            overall_status=overall_status,
            timestamp=current_time,
            uptime=current_time - start_time,
            system_info=system_info,
            services=service_health,
            performance_metrics=performance_metrics,
            configuration=config_info
        ).dict(),
        message="详细健康检查完成"
    )


@router.get("/services")
async def services_health_check(
    service_bundle: ServiceBundle = Depends(get_service_bundle)
):
    """服务健康检查
    
    检查各个服务组件的健康状态
    """
    service_health = await check_services_health(service_bundle)
    
    # 统计健康和不健康的服务
    healthy_count = sum(1 for service in service_health if service.status == "healthy")
    total_count = len(service_health)
    
    overall_status = "healthy" if healthy_count == total_count else "degraded" if healthy_count > 0 else "unhealthy"
    
    return create_success_response(
        data={
            "overall_status": overall_status,
            "healthy_services": healthy_count,
            "total_services": total_count,
            "services": [service.dict() for service in service_health],
            "timestamp": time.time()
        },
        message="服务健康检查完成"
    )


@router.get("/system")
async def system_health_check():
    """系统健康检查
    
    检查系统资源使用情况
    """
    system_info = await get_system_info()
    performance_metrics = await get_performance_metrics()
    
    # 评估系统健康状态
    status = "healthy"
    warnings = []
    
    if system_info.memory_percent > 90:
        status = "warning"
        warnings.append("内存使用率过高")
    
    if system_info.cpu_percent > 90:
        status = "warning"
        warnings.append("CPU使用率过高")
    
    disk_usage = system_info.disk_usage
    if disk_usage.get("percent", 0) > 90:
        status = "warning"
        warnings.append("磁盘使用率过高")
    
    return create_success_response(
        data={
            "status": status,
            "warnings": warnings,
            "system_info": system_info.dict(),
            "performance_metrics": performance_metrics,
            "timestamp": time.time()
        },
        message="系统健康检查完成"
    )


@router.get("/readiness")
async def readiness_check(
    service_bundle: ServiceBundle = Depends(get_service_bundle)
):
    """就绪检查
    
    检查应用是否准备好接收请求
    """
    # 检查关键服务是否可用
    critical_services = []
    
    if service_bundle.has_rag_engine():
        try:
            rag_health = await service_bundle.rag_engine.health_check()
            if not all(rag_health.values()):
                critical_services.append("RAG引擎")
        except Exception:
            critical_services.append("RAG引擎")
    
    if service_bundle.has_llm_manager():
        try:
            llm_health = await service_bundle.llm_manager.health_check()
            if not any(llm_health.values()):
                critical_services.append("LLM管理器")
        except Exception:
            critical_services.append("LLM管理器")
    
    is_ready = len(critical_services) == 0
    status_code = 200 if is_ready else 503
    
    return create_success_response(
        data={
            "ready": is_ready,
            "status": "ready" if is_ready else "not_ready",
            "failed_services": critical_services,
            "timestamp": time.time()
        },
        message="就绪检查完成",
        status_code=status_code
    )


@router.get("/liveness")
async def liveness_check():
    """存活检查
    
    检查应用是否仍在运行
    """
    try:
        # 简单的存活检查
        current_time = time.time()
        uptime = current_time - start_time
        
        # 检查基本系统资源
        memory_info = psutil.virtual_memory()
        
        return create_success_response(
            data={
                "alive": True,
                "uptime": uptime,
                "memory_available": memory_info.available,
                "timestamp": current_time
            },
            message="存活检查通过"
        )
    except Exception as e:
        return create_success_response(
            data={
                "alive": False,
                "error": str(e),
                "timestamp": time.time()
            },
            message="存活检查失败",
            status_code=503
        )


@router.get("/metrics")
async def get_metrics(
    service_stats: Dict[str, Any] = Depends(get_service_stats)
):
    """获取应用指标
    
    返回应用的性能和使用指标
    """
    system_metrics = await get_performance_metrics()
    
    return create_success_response(
        data={
            "system_metrics": system_metrics,
            "service_stats": service_stats,
            "uptime": time.time() - start_time,
            "timestamp": time.time()
        },
        message="指标获取成功"
    )


# 辅助函数

async def get_system_info() -> SystemInfo:
    """获取系统信息"""
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return SystemInfo(
        platform=platform.platform(),
        python_version=platform.python_version(),
        cpu_count=psutil.cpu_count(),
        memory_total=memory.total,
        memory_available=memory.available,
        memory_percent=memory.percent,
        cpu_percent=psutil.cpu_percent(interval=1),
        disk_usage={
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100
        }
    )


async def check_services_health(service_bundle: ServiceBundle) -> List[ServiceHealth]:
    """检查服务健康状态"""
    services = []
    current_time = time.time()
    
    # 检查RAG引擎
    if service_bundle.has_rag_engine():
        try:
            rag_health = await service_bundle.rag_engine.health_check()
            # 增加配置验证结果
            try:
                config_valid = bool(service_bundle.rag_engine.validate_config())
            except Exception:
                config_valid = False
            status = "healthy" if all(rag_health.values()) and config_valid else "unhealthy"
            services.append(ServiceHealth(
                service_name="RAG引擎",
                status=status,
                last_check=current_time,
                details={
                    **rag_health,
                    "config_valid": config_valid
                }
            ))
        except Exception as e:
            services.append(ServiceHealth(
                service_name="RAG引擎",
                status="error",
                last_check=current_time,
                details={"error": str(e)}
            ))
    
    # 检查LLM管理器
    if service_bundle.has_llm_manager():
        try:
            llm_health = await service_bundle.llm_manager.health_check()
            status = "healthy" if any(llm_health.values()) else "unhealthy"
            services.append(ServiceHealth(
                service_name="LLM管理器",
                status=status,
                last_check=current_time,
                details=llm_health
            ))
        except Exception as e:
            services.append(ServiceHealth(
                service_name="LLM管理器",
                status="error",
                last_check=current_time,
                details={"error": str(e)}
            ))
    
    # 检查搜索服务
    if service_bundle.has_search_service():
        try:
            # 假设搜索服务有健康检查方法
            status = "healthy"  # 简化实现
            services.append(ServiceHealth(
                service_name="搜索服务",
                status=status,
                last_check=current_time,
                details={"status": "operational"}
            ))
        except Exception as e:
            services.append(ServiceHealth(
                service_name="搜索服务",
                status="error",
                last_check=current_time,
                details={"error": str(e)}
            ))
    
    # 检查文档服务
    if service_bundle.has_document_service():
        try:
            status = "healthy"  # 简化实现
            services.append(ServiceHealth(
                service_name="文档服务",
                status=status,
                last_check=current_time,
                details={"status": "operational"}
            ))
        except Exception as e:
            services.append(ServiceHealth(
                service_name="文档服务",
                status="error",
                last_check=current_time,
                details={"error": str(e)}
            ))
    
    # 检查智能体管理器
    if service_bundle.has_agent_manager():
        try:
            status = "healthy"  # 简化实现
            services.append(ServiceHealth(
                service_name="智能体管理器",
                status=status,
                last_check=current_time,
                details={"status": "operational"}
            ))
        except Exception as e:
            services.append(ServiceHealth(
                service_name="智能体管理器",
                status="error",
                last_check=current_time,
                details={"error": str(e)}
            ))
    
    return services


async def get_performance_metrics() -> Dict[str, Any]:
    """获取性能指标"""
    # 获取进程信息
    process = psutil.Process()
    
    return {
        "process_memory": {
            "rss": process.memory_info().rss,
            "vms": process.memory_info().vms,
            "percent": process.memory_percent()
        },
        "process_cpu": {
            "percent": process.cpu_percent(),
            "times": process.cpu_times()._asdict()
        },
        "process_threads": process.num_threads(),
        "process_fds": process.num_fds() if hasattr(process, 'num_fds') else None,
        "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
        "boot_time": psutil.boot_time(),
        "uptime": time.time() - start_time
    }


def get_safe_config_info(settings) -> Dict[str, Any]:
    """获取安全的配置信息（脱敏）"""
    return {
        "app_name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "debug": settings.debug,
        "host": settings.host,
        "port": settings.port,
        "data_dir": settings.data_dir,
        "llm_providers_enabled": [
            name for name, config in settings.llm.providers.items()
            if config.get('enabled', False)
        ],
        "security": {
            "rate_limit_enabled": settings.security.rate_limit_enabled,
            "require_api_key": settings.security.require_api_key,
            "cors_origins": settings.security.cors_origins
        },
        "monitoring": {
            "enabled": settings.monitoring.enabled,
            "prometheus_enabled": settings.monitoring.prometheus_enabled
        }
    }


def determine_overall_status(services: List[ServiceHealth], system_info: SystemInfo) -> str:
    """确定整体健康状态"""
    # 检查服务状态
    service_statuses = [service.status for service in services]
    
    if "error" in service_statuses:
        return "unhealthy"
    
    if "unhealthy" in service_statuses:
        return "degraded"
    
    # 检查系统资源
    if system_info.memory_percent > 95 or system_info.cpu_percent > 95:
        return "degraded"
    
    if system_info.disk_usage.get("percent", 0) > 95:
        return "degraded"
    
    return "healthy"