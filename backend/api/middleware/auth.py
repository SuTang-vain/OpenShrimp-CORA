#!/usr/bin/env python3
"""
认证中间件
处理请求认证和权限验证

运行环境: Python 3.11+
依赖: fastapi, starlette
"""

import time
from typing import Dict, Any, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.api.dependencies.auth import get_current_user, verify_api_key
from backend.shared.utils.response import create_error_response, create_unauthorized_response
from backend.infrastructure.config.settings import get_settings


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件
    
    处理请求认证、权限验证和速率限制
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        """
        初始化认证中间件
        
        Args:
            app: FastAPI应用实例
            exclude_paths: 排除认证的路径列表
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/refresh",
            "/static"
        ]
        self.settings = get_settings()
        
        # 简单的内存速率限制器
        self.rate_limit_storage = {}
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求
        
        Args:
            request: 请求对象
            call_next: 下一个处理器
            
        Returns:
            响应对象
        """
        # 检查是否需要认证
        if self._should_skip_auth(request):
            return await call_next(request)
        
        # 速率限制检查
        if self.settings.security.rate_limit_enabled:
            rate_limit_result = await self._check_rate_limit(request)
            if rate_limit_result:
                return rate_limit_result
        
        # 认证检查
        auth_result = await self._authenticate_request(request)
        if isinstance(auth_result, JSONResponse):
            return auth_result
        
        # 将用户信息添加到请求状态
        if auth_result:
            request.state.user = auth_result
        
        # 继续处理请求
        response = await call_next(request)
        
        # 添加安全头
        self._add_security_headers(response)
        
        return response
    
    def _should_skip_auth(self, request: Request) -> bool:
        """
        检查是否应该跳过认证
        
        Args:
            request: 请求对象
            
        Returns:
            是否跳过认证
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
    
    async def _authenticate_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        认证请求
        
        Args:
            request: 请求对象
            
        Returns:
            用户信息或错误响应
        """
        try:
            # 尝试获取用户信息
            user = await get_current_user(request)
            
            if not user:
                # 检查是否需要强制认证（安全访问，默认不要求）
                require_auth = getattr(self.settings.security, "require_authentication", False)
                if require_auth:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content=create_unauthorized_response("需要认证")
                    )
                return None
            
            # 检查用户是否激活
            if not user.get("is_active", True):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content=create_error_response(
                        message="用户账户已禁用",
                        code=status.HTTP_403_FORBIDDEN
                    )
                )
            
            return user
            
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=create_error_response(
                    message=f"认证失败: {str(e)}",
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            )
    
    async def _check_rate_limit(self, request: Request) -> Optional[JSONResponse]:
        """
        检查速率限制
        
        Args:
            request: 请求对象
            
        Returns:
            错误响应或None
        """
        try:
            # 获取客户端标识
            client_ip = self._get_client_ip(request)
            identifier = f"ip_{client_ip}"
            
            # 检查用户认证状态
            auth_header = request.headers.get("Authorization")
            if auth_header:
                # 如果有认证信息，尝试获取用户ID作为标识
                try:
                    user = await get_current_user(request)
                    if user:
                        identifier = f"user_{user['id']}"
                except:
                    pass
            
            # 检查速率限制
            if not self._is_rate_limit_allowed(identifier):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content=create_error_response(
                        message="请求过于频繁，请稍后再试",
                        code=status.HTTP_429_TOO_MANY_REQUESTS,
                        error_code="RATE_LIMIT_EXCEEDED"
                    ),
                    headers={
                        "Retry-After": str(self.settings.security.rate_limit_window)
                    }
                )
            
            return None
            
        except Exception:
            # 速率限制检查失败时，允许请求继续
            return None
    
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
    
    def _is_rate_limit_allowed(self, identifier: str) -> bool:
        """
        检查是否允许请求（速率限制）
        
        Args:
            identifier: 请求标识符
            
        Returns:
            是否允许请求
        """
        now = time.time()
        window_start = now - self.settings.security.rate_limit_window
        
        # 清理过期记录
        if identifier in self.rate_limit_storage:
            self.rate_limit_storage[identifier] = [
                req_time for req_time in self.rate_limit_storage[identifier]
                if req_time > window_start
            ]
        else:
            self.rate_limit_storage[identifier] = []
        
        # 检查请求数量
        if len(self.rate_limit_storage[identifier]) >= self.settings.security.rate_limit_requests:
            return False
        
        # 记录当前请求
        self.rate_limit_storage[identifier].append(now)
        return True
    
    def _add_security_headers(self, response: Response):
        """
        添加安全头
        
        Args:
            response: 响应对象
        """
        # 添加安全相关的HTTP头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # CORS头（如果需要）
        cors_enabled = getattr(self.settings.security, "cors_enabled", False)
        if cors_enabled:
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-API-Key"


class APIKeyMiddleware(BaseHTTPMiddleware):
    """API密钥中间件
    
    专门处理API密钥认证
    """
    
    def __init__(self, app, require_api_key: bool = False):
        """
        初始化API密钥中间件
        
        Args:
            app: FastAPI应用实例
            require_api_key: 是否强制要求API密钥
        """
        super().__init__(app)
        self.require_api_key = require_api_key
        self.settings = get_settings()
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求
        
        Args:
            request: 请求对象
            call_next: 下一个处理器
            
        Returns:
            响应对象
        """
        # 检查API密钥
        if self.require_api_key or self.settings.security.require_api_key:
            api_key = request.headers.get("X-API-Key")
            
            if not api_key:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content=create_unauthorized_response("缺少API密钥")
                )
            
            if not verify_api_key(api_key):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content=create_unauthorized_response("无效的API密钥")
                )
        
        return await call_next(request)


class CORSMiddleware(BaseHTTPMiddleware):
    """CORS中间件
    
    处理跨域请求
    """
    
    def __init__(self, app, allow_origins: list = None, allow_methods: list = None, allow_headers: list = None):
        """
        初始化CORS中间件
        
        Args:
            app: FastAPI应用实例
            allow_origins: 允许的源列表
            allow_methods: 允许的方法列表
            allow_headers: 允许的头列表
        """
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["Content-Type", "Authorization", "X-API-Key"]
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求
        
        Args:
            request: 请求对象
            call_next: 下一个处理器
            
        Returns:
            响应对象
        """
        # 处理预检请求
        if request.method == "OPTIONS":
            response = Response()
            self._add_cors_headers(response, request)
            return response
        
        # 处理正常请求
        response = await call_next(request)
        self._add_cors_headers(response, request)
        
        return response
    
    def _add_cors_headers(self, response: Response, request: Request):
        """
        添加CORS头
        
        Args:
            response: 响应对象
            request: 请求对象
        """
        origin = request.headers.get("Origin")
        
        if "*" in self.allow_origins or (origin and origin in self.allow_origins):
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
        
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "86400"  # 24小时