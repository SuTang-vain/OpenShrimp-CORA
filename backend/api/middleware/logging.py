#!/usr/bin/env python3
"""
日志中间件
提供请求日志记录和监控功能

运行环境: Python 3.11+
依赖: fastapi, starlette, logging
"""

import time
import uuid
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.infrastructure.config.settings import get_settings


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件
    
    记录请求和响应信息，用于监控和调试
    """
    
    def __init__(
        self,
        app,
        logger: Optional[logging.Logger] = None,
        log_requests: bool = True,
        log_responses: bool = True,
        log_request_body: bool = False,
        log_response_body: bool = False,
        exclude_paths: Optional[list] = None
    ):
        """
        初始化日志中间件
        
        Args:
            app: FastAPI应用实例
            logger: 日志记录器
            log_requests: 是否记录请求
            log_responses: 是否记录响应
            log_request_body: 是否记录请求体
            log_response_body: 是否记录响应体
            exclude_paths: 排除的路径列表
        """
        super().__init__(app)
        self.logger = logger or self._setup_logger()
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static"
        ]
        self.settings = get_settings()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("api_middleware")
        
        if not logger.handlers:
            # 创建处理器
            handler = logging.StreamHandler()
            
            # 创建格式器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            
            # 添加处理器
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求
        
        Args:
            request: 请求对象
            call_next: 下一个处理器
            
        Returns:
            响应对象
        """
        # 检查是否应该跳过日志记录
        if self._should_skip_logging(request):
            return await call_next(request)
        
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 记录请求信息
        if self.log_requests:
            await self._log_request(request, request_id)
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            # 记录响应信息
            if self.log_responses:
                await self._log_response(request, response, request_id, process_time)
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录异常
            await self._log_exception(request, e, request_id, process_time)
            
            # 重新抛出异常
            raise
    
    def _should_skip_logging(self, request: Request) -> bool:
        """
        检查是否应该跳过日志记录
        
        Args:
            request: 请求对象
            
        Returns:
            是否跳过日志记录
        """
        path = request.url.path
        
        # 检查排除路径
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        
        # 检查静态文件
        if path.startswith("/static/") or path.endswith((".css", ".js", ".ico", ".png", ".jpg", ".jpeg", ".gif")):
            return True
        
        return False
    
    async def _log_request(self, request: Request, request_id: str):
        """
        记录请求信息
        
        Args:
            request: 请求对象
            request_id: 请求ID
        """
        try:
            # 基本请求信息
            log_data = {
                "type": "request",
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": self._sanitize_headers(dict(request.headers)),
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("User-Agent", "")
            }
            
            # 添加用户信息（如果有）
            if hasattr(request.state, 'user') and request.state.user:
                log_data["user"] = {
                    "id": request.state.user.get("id"),
                    "username": request.state.user.get("username"),
                    "roles": request.state.user.get("roles", [])
                }
            
            # 记录请求体（如果启用）
            if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    if body:
                        # 尝试解析JSON
                        try:
                            log_data["body"] = json.loads(body.decode())
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            log_data["body"] = f"<binary data: {len(body)} bytes>"
                except Exception:
                    log_data["body"] = "<failed to read body>"
            
            # 记录日志
            self.logger.info(f"Request: {json.dumps(log_data, ensure_ascii=False)}")
            
        except Exception as e:
            self.logger.error(f"Failed to log request: {e}")
    
    async def _log_response(self, request: Request, response: Response, request_id: str, process_time: float):
        """
        记录响应信息
        
        Args:
            request: 请求对象
            response: 响应对象
            request_id: 请求ID
            process_time: 处理时间
        """
        try:
            # 基本响应信息
            log_data = {
                "type": "response",
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": round(process_time, 4),
                "response_headers": self._sanitize_headers(dict(response.headers))
            }
            
            # 记录响应体（如果启用且不是大文件）
            if self.log_response_body and hasattr(response, 'body'):
                try:
                    # 检查内容类型
                    content_type = response.headers.get("content-type", "")
                    if content_type.startswith(("application/json", "text/")):
                        # 只记录文本类型的响应
                        if hasattr(response, 'body') and response.body:
                            try:
                                body_text = response.body.decode() if isinstance(response.body, bytes) else str(response.body)
                                if len(body_text) < 10000:  # 限制大小
                                    log_data["body"] = body_text
                                else:
                                    log_data["body"] = f"<large response: {len(body_text)} chars>"
                            except Exception:
                                log_data["body"] = "<failed to decode response body>"
                except Exception:
                    pass
            
            # 根据状态码选择日志级别
            if response.status_code >= 500:
                self.logger.error(f"Response: {json.dumps(log_data, ensure_ascii=False)}")
            elif response.status_code >= 400:
                self.logger.warning(f"Response: {json.dumps(log_data, ensure_ascii=False)}")
            else:
                self.logger.info(f"Response: {json.dumps(log_data, ensure_ascii=False)}")
            
        except Exception as e:
            self.logger.error(f"Failed to log response: {e}")
    
    async def _log_exception(self, request: Request, exception: Exception, request_id: str, process_time: float):
        """
        记录异常信息
        
        Args:
            request: 请求对象
            exception: 异常对象
            request_id: 请求ID
            process_time: 处理时间
        """
        try:
            log_data = {
                "type": "exception",
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "method": request.method,
                "path": request.url.path,
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "process_time": round(process_time, 4)
            }
            
            # 添加用户信息（如果有）
            if hasattr(request.state, 'user') and request.state.user:
                log_data["user_id"] = request.state.user.get("id")
            
            self.logger.error(f"Exception: {json.dumps(log_data, ensure_ascii=False)}")
            
        except Exception as e:
            self.logger.error(f"Failed to log exception: {e}")
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        清理敏感的请求头信息
        
        Args:
            headers: 原始请求头
            
        Returns:
            清理后的请求头
        """
        sensitive_headers = {
            "authorization",
            "x-api-key",
            "cookie",
            "set-cookie",
            "x-auth-token",
            "x-access-token"
        }
        
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = "<redacted>"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端IP地址
        
        Args:
            request: 请求对象
            
        Returns:
            客户端IP地址
        """
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 使用客户端IP
        if request.client:
            return request.client.host
        
        return "unknown"


class AccessLogMiddleware(BaseHTTPMiddleware):
    """访问日志中间件
    
    简化版的访问日志记录
    """
    
    def __init__(self, app, logger: Optional[logging.Logger] = None):
        super().__init__(app)
        self.logger = logger or logging.getLogger("access")
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # 记录访问日志
        client_ip = request.client.host if request.client else "unknown"
        log_message = (
            f"{client_ip} - "
            f"{request.method} {request.url.path} "
            f"HTTP/{request.scope.get('http_version', '1.1')} "
            f"{response.status_code} "
            f"{process_time:.4f}s"
        )
        
        self.logger.info(log_message)
        
        return response


class PerformanceLogMiddleware(BaseHTTPMiddleware):
    """性能日志中间件
    
    专门记录性能相关的指标
    """
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
        self.logger = logging.getLogger("performance")
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # 记录慢请求
        if process_time > self.slow_request_threshold:
            self.logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {process_time:.4f}s (threshold: {self.slow_request_threshold}s)"
            )
        
        # 添加性能头
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        
        return response