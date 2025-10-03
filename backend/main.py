#!/usr/bin/env python3
"""
Shrimp Agent v2 FastAPI主应用
现代化的智能搜索和RAG系统后端

运行环境: Python 3.11+
依赖: fastapi, uvicorn, pydantic, asyncio
"""

import asyncio
import inspect
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

# 导入路由
from backend.api.routes.search import router as search_router
from backend.api.routes.documents import router as documents_router
from backend.api.routes.agents import router as agents_router
from backend.api.routes.health import router as health_router
from backend.api.routes.admin import router as admin_router
from backend.api.routes.auth import router as auth_router
from backend.api.routes.embedding import router as embedding_router
from backend.api.routes.mcp import router as mcp_router
from backend.api.routes.graph import router as graph_router
from backend.api.routes.services import router as services_router
from backend.infrastructure.graph.neo4j_client import Neo4jClient

# 导入中间件
from backend.api.middleware.auth import AuthMiddleware
from backend.api.middleware.rate_limit import RateLimitMiddleware
from backend.api.middleware.logging import LoggingMiddleware

# 导入配置和服务
from backend.infrastructure.config.settings import get_settings
from backend.services.agent.manager import AgentServiceManager
from backend.services.search.engine import SearchEngineService
from backend.services.document.service import DocumentService
from backend.core.rag import create_rag_engine
from backend.core.llm import create_llm_manager
from backend.services.agent.camel_service import CamelAgentService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局服务实例
services: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("正在启动 Shrimp Agent v2...")
    
    try:
        # 加载配置
        settings = get_settings()
        
        # 初始化LLM管理器
        if settings.llm_config:
            llm_manager = create_llm_manager(settings.llm_config)
            services['llm_manager'] = llm_manager
            logger.info("LLM管理器初始化完成")
        
        # 初始化RAG引擎
        if settings.rag_config:
            rag_config = settings.rag_config.copy()
            rag_config['llm_manager'] = services.get('llm_manager')
            rag_engine = create_rag_engine(rag_config)
            services['rag_engine'] = rag_engine
            logger.info("RAG引擎初始化完成")

        # 初始化 Neo4j 图数据库客户端（若已配置凭据，则加载）
        try:
            graph_db = Neo4jClient.from_store()
            if graph_db:
                services['graph_db'] = graph_db
                logger.info("Neo4j 图数据库客户端已加载")
            else:
                logger.info("Neo4j 凭据未配置或连接失败，跳过图数据库客户端初始化")
        except Exception as e:
            logger.warning(f"Neo4j 客户端初始化异常: {e}")
        
        # 初始化服务管理器
        agent_manager = AgentServiceManager()
        services['agent_manager'] = agent_manager
        
        # 初始化搜索引擎服务
        search_service = SearchEngineService({
            'rag_engine': services.get('rag_engine'),
            'max_results': 20,
            'default_timeout': 30.0,
            'enable_web_search': True,
            'enable_document_search': True
        })
        services['search_service'] = search_service
        
        # 初始化文档服务（统一使用 service.py 实现）
        document_service = DocumentService({
            'rag_engine': services.get('rag_engine'),
            'storage_path': "./data/documents",
            'max_file_size': 50 * 1024 * 1024,
            'supported_formats': [
                '.txt', '.md', '.pdf', '.docx', '.html', '.json', '.csv'
            ],
            'enable_ocr': False,
            'enable_auto_processing': True
        })
        services['document_service'] = document_service

        # 初始化 CAMEL 多Agent 服务（按开关）
        if getattr(settings.agent, 'enable_camel_framework', False):
            camel_service = CamelAgentService({
                'llm_manager': services.get('llm_manager'),
                'rag_engine': services.get('rag_engine'),
                'available_agents': settings.agent.available_agents,
                'search_engines': ['google', 'bing'],
                'max_results': 10
            })
            services['camel_service'] = camel_service
            logger.info("CAMEL智能体服务初始化完成")
        
        # 健康检查
        health_checks = await perform_health_checks()
        if not all(health_checks.values()):
            logger.warning(f"部分服务健康检查失败: {health_checks}")
        
        logger.info("Shrimp Agent v2 启动完成")
        
        yield
        
    except Exception as e:
        logger.error(f"启动失败: {e}")
        raise
    
    finally:
        # 关闭时清理
        logger.info("正在关闭 Shrimp Agent v2...")
        
        # 清理服务（兼容同步/异步 close 方法）
        for service_name, service in services.items():
            try:
                if hasattr(service, 'close'):
                    close_fn = getattr(service, 'close')
                    if inspect.iscoroutinefunction(close_fn):
                        await close_fn()
                    else:
                        close_fn()
                logger.info(f"服务 {service_name} 已关闭")
            except Exception as e:
                logger.error(f"关闭服务 {service_name} 失败: {e}")
        
        services.clear()
        logger.info("Shrimp Agent v2 已关闭")


async def perform_health_checks() -> Dict[str, bool]:
    """执行健康检查"""
    health_status = {}
    
    # 检查LLM管理器
    if 'llm_manager' in services:
        try:
            llm_health = await services['llm_manager'].health_check()
            health_status['llm_manager'] = all(llm_health.values())
        except Exception as e:
            logger.error(f"LLM管理器健康检查失败: {e}")
            health_status['llm_manager'] = False
    
    # 检查RAG引擎
    if 'rag_engine' in services:
        try:
            rag_health = await services['rag_engine'].health_check()
            health_status['rag_engine'] = all(rag_health.values())
        except Exception as e:
            logger.error(f"RAG引擎健康检查失败: {e}")
            health_status['rag_engine'] = False
    
    return health_status


# 创建FastAPI应用
app = FastAPI(
    title="Shrimp Agent v2 API",
    description="现代化的智能搜索和RAG系统",
    version="2.0.0",
    docs_url=None,  # 禁用默认文档
    redoc_url=None,  # 禁用默认ReDoc
    lifespan=lifespan
)

# 添加中间件

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://10.157.57.195:3000"
    ],  # 允许的前端域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Gzip压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 自定义中间件
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)


# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": time.time(),
                "path": str(request.url)
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "内部服务器错误",
                "timestamp": time.time(),
                "path": str(request.url)
            }
        }
    )


# 请求处理中间件
@app.middleware("http")
async def process_time_middleware(request: Request, call_next):
    """请求处理时间中间件"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# 根路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Shrimp Agent v2 API",
        "version": "2.0.0",
        "description": "现代化的智能搜索和RAG系统",
        "status": "running",
        "timestamp": time.time(),
        "docs": "/docs",
        "health": "/health"
    }


# 自定义文档路由
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """自定义Swagger UI"""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Shrimp Agent v2 API - 文档",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )


# 自定义OpenAPI
@app.get("/openapi.json", include_in_schema=False)
async def custom_openapi():
    """自定义OpenAPI规范"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Shrimp Agent v2 API",
        version="2.0.0",
        description="现代化的智能搜索和RAG系统API文档",
        routes=app.routes,
    )
    
    # 添加自定义信息
    openapi_schema["info"]["contact"] = {
        "name": "Shrimp Agent Team",
        "email": "support@shrimpagent.com"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# 服务访问器
@app.middleware("http")
async def add_services_to_request(request: Request, call_next):
    """将服务添加到请求上下文"""
    request.state.services = services
    response = await call_next(request)
    return response


# 注册路由
app.include_router(
    health_router,
    prefix="/health",
    tags=["健康检查"]
)

app.include_router(
    auth_router,
    prefix="/api/auth",
    tags=["认证"]
)

app.include_router(
    search_router,
    prefix="/api",
    tags=["搜索"]
)

app.include_router(
    embedding_router,
    prefix="/api",
    tags=["嵌入"]
)

app.include_router(
    mcp_router,
    prefix="/api",
    tags=["MCP"]
)

app.include_router(
    graph_router,
    prefix="/api",
    tags=["图谱"]
)

app.include_router(
    services_router,
    prefix="/api",
    tags=["服务适配"]
)

app.include_router(
    documents_router,
    prefix="/api",
    tags=["文档管理"]
)

app.include_router(
    agents_router,
    prefix="/api/v1/agents",
    tags=["智能体"]
)

app.include_router(
    admin_router,
    prefix="/api/v1/admin",
    tags=["管理"]
)


# 开发模式启动
if __name__ == "__main__":
    import uvicorn
    
    # 获取配置
    settings = get_settings()
    
    # 启动服务器
    uvicorn.run(
            "backend.main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug,
            log_level="info" if not settings.debug else "debug",
            access_log=True
        )