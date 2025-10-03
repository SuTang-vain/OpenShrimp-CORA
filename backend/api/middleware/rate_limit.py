#!/usr/bin/env python3
"""
速率限制中间件
提供API请求速率限制功能

运行环境: Python 3.11+
依赖: fastapi, starlette, redis(可选)
"""

import time
import asyncio
from typing import Dict, Any, Optional, Callable
from collections import defaultdict
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.shared.utils.response import create_error_response
from backend.infrastructure.config.settings import get_settings


class RateLimitStorage:
    """速率限制存储接口"""
    
    async def get_request_count(self, key: str, window: int) -> int:
        """获取指定时间窗口内的请求数量"""
        raise NotImplementedError
    
    async def increment_request_count(self, key: str, window: int) -> int:
        """增加请求计数并返回当前计数"""
        raise NotImplementedError
    
    async def reset_request_count(self, key: str):
        """重置请求计数"""
        raise NotImplementedError


class MemoryRateLimitStorage(RateLimitStorage):
    """基于内存的速率限制存储"""
    
    def __init__(self):
        self.storage = defaultdict(list)
        self.lock = asyncio.Lock()
    
    async def get_request_count(self, key: str, window: int) -> int:
        """获取指定时间窗口内的请求数量"""
        async with self.lock:
            now = time.time()
            window_start = now - window
            
            # 清理过期记录
            self.storage[key] = [
                timestamp for timestamp in self.storage[key]
                if timestamp > window_start
            ]
            
            return len(self.storage[key])
    
    async def increment_request_count(self, key: str, window: int) -> int:
        """增加请求计数并返回当前计数"""
        async with self.lock:
            now = time.time()
            window_start = now - window
            
            # 清理过期记录
            self.storage[key] = [
                timestamp for timestamp in self.storage[key]
                if timestamp > window_start
            ]
            
            # 添加当前请求
            self.storage[key].append(now)
            
            return len(self.storage[key])
    
    async def reset_request_count(self, key: str):
        """重置请求计数"""
        async with self.lock:
            if key in self.storage:
                del self.storage[key]


class RedisRateLimitStorage(RateLimitStorage):
    """基于Redis的速率限制存储"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def get_request_count(self, key: str, window: int) -> int:
        """获取指定时间窗口内的请求数量"""
        try:
            now = time.time()
            window_start = now - window
            
            # 使用Redis的ZCOUNT命令计算时间窗口内的请求数
            count = await self.redis.zcount(key, window_start, now)
            return count
        except Exception:
            # Redis连接失败时返回0，允许请求通过
            return 0
    
    async def increment_request_count(self, key: str, window: int) -> int:
        """增加请求计数并返回当前计数"""
        try:
            now = time.time()
            window_start = now - window
            
            # 使用Redis管道执行原子操作
            pipe = self.redis.pipeline()
            
            # 清理过期记录
            pipe.zremrangebyscore(key, 0, window_start)
            
            # 添加当前请求
            pipe.zadd(key, {str(now): now})
            
            # 设置过期时间
            pipe.expire(key, window + 60)  # 额外60秒缓冲
            
            # 获取当前计数
            pipe.zcard(key)
            
            results = await pipe.execute()
            return results[-1]  # 返回最后一个结果（计数）
            
        except Exception:
            # Redis连接失败时返回0，允许请求通过
            return 0
    
    async def reset_request_count(self, key: str):
        """重置请求计数"""
        try:
            await self.redis.delete(key)
        except Exception:
            pass


class RateLimitRule:
    """速率限制规则"""
    
    def __init__(
        self,
        max_requests: int,
        window_seconds: int,
        key_func: Optional[Callable[[Request], str]] = None,
        skip_func: Optional[Callable[[Request], bool]] = None,
        error_message: str = "请求过于频繁，请稍后再试"
    ):
        """
        初始化速率限制规则
        
        Args:
            max_requests: 最大请求数
            window_seconds: 时间窗口（秒）
            key_func: 生成限制键的函数
            skip_func: 跳过限制的函数
            error_message: 错误消息
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_func = key_func or self._default_key_func
        self.skip_func = skip_func or (lambda req: False)
        self.error_message = error_message
    
    def _default_key_func(self, request: Request) -> str:
        """默认的键生成函数"""
        # 优先使用用户ID，其次使用IP地址
        if hasattr(request.state, 'user') and request.state.user:
            return f"user_{request.state.user['id']}"
        
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        return f"ip_{client_ip}"
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
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
    
    def get_key(self, request: Request) -> str:
        """获取限制键"""
        return self.key_func(request)
    
    def should_skip(self, request: Request) -> bool:
        """是否应该跳过限制"""
        return self.skip_func(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""
    
    def __init__(
        self,
        app,
        storage: Optional[RateLimitStorage] = None,
        default_rule: Optional[RateLimitRule] = None,
        rules: Optional[Dict[str, RateLimitRule]] = None
    ):
        """
        初始化速率限制中间件
        
        Args:
            app: FastAPI应用实例
            storage: 存储后端
            default_rule: 默认限制规则
            rules: 路径特定的限制规则
        """
        super().__init__(app)
        self.storage = storage or MemoryRateLimitStorage()
        self.settings = get_settings()
        
        # 默认规则
        self.default_rule = default_rule or RateLimitRule(
            max_requests=self.settings.security.rate_limit_requests,
            window_seconds=self.settings.security.rate_limit_window
        )
        
        # 路径特定规则
        self.rules = rules or {}
        
        # 排除路径
        self.exclude_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求
        
        Args:
            request: 请求对象
            call_next: 下一个处理器
            
        Returns:
            响应对象
        """
        # 检查是否启用速率限制
        if not self.settings.security.rate_limit_enabled:
            return await call_next(request)
        
        # 检查是否应该跳过
        if self._should_skip_rate_limit(request):
            return await call_next(request)
        
        # 获取适用的规则
        rule = self._get_applicable_rule(request)
        
        # 检查规则是否要求跳过
        if rule.should_skip(request):
            return await call_next(request)
        
        # 执行速率限制检查
        rate_limit_result = await self._check_rate_limit(request, rule)
        if rate_limit_result:
            return rate_limit_result
        
        # 继续处理请求
        return await call_next(request)
    
    def _should_skip_rate_limit(self, request: Request) -> bool:
        """
        检查是否应该跳过速率限制
        
        Args:
            request: 请求对象
            
        Returns:
            是否跳过速率限制
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
    
    def _get_applicable_rule(self, request: Request) -> RateLimitRule:
        """
        获取适用的限制规则
        
        Args:
            request: 请求对象
            
        Returns:
            适用的限制规则
        """
        path = request.url.path
        
        # 检查路径特定规则
        for pattern, rule in self.rules.items():
            if path.startswith(pattern):
                return rule
        
        # 返回默认规则
        return self.default_rule
    
    async def _check_rate_limit(self, request: Request, rule: RateLimitRule) -> Optional[JSONResponse]:
        """
        检查速率限制
        
        Args:
            request: 请求对象
            rule: 限制规则
            
        Returns:
            错误响应或None
        """
        try:
            # 生成限制键
            key = rule.get_key(request)
            
            # 增加请求计数
            current_count = await self.storage.increment_request_count(
                key, rule.window_seconds
            )
            
            # 检查是否超过限制
            if current_count > rule.max_requests:
                # 计算重试时间
                retry_after = rule.window_seconds
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content=create_error_response(
                        message=rule.error_message,
                        code=status.HTTP_429_TOO_MANY_REQUESTS,
                        error_code="RATE_LIMIT_EXCEEDED",
                        details={
                            "max_requests": rule.max_requests,
                            "window_seconds": rule.window_seconds,
                            "current_count": current_count,
                            "retry_after": retry_after
                        }
                    ),
                    headers={
                        "X-RateLimit-Limit": str(rule.max_requests),
                        "X-RateLimit-Remaining": str(max(0, rule.max_requests - current_count)),
                        "X-RateLimit-Reset": str(int(time.time() + retry_after)),
                        "Retry-After": str(retry_after)
                    }
                )
            
            return None
            
        except Exception as e:
            # 速率限制检查失败时，记录错误但允许请求继续
            print(f"Rate limit check failed: {e}")
            return None


def create_rate_limit_rules() -> Dict[str, RateLimitRule]:
    """创建默认的速率限制规则"""
    return {
        "/api/v1/auth/": RateLimitRule(
            max_requests=10,
            window_seconds=60,
            error_message="认证请求过于频繁，请稍后再试"
        ),
        "/api/v1/search/": RateLimitRule(
            max_requests=50,
            window_seconds=60,
            error_message="搜索请求过于频繁，请稍后再试"
        ),
        "/api/v1/agents/": RateLimitRule(
            max_requests=20,
            window_seconds=60,
            error_message="智能体请求过于频繁，请稍后再试"
        ),
        "/api/v1/documents/upload": RateLimitRule(
            max_requests=5,
            window_seconds=60,
            error_message="文档上传过于频繁，请稍后再试"
        )
    }


def create_user_based_key_func(request: Request) -> str:
    """基于用户的键生成函数"""
    if hasattr(request.state, 'user') and request.state.user:
        return f"user_{request.state.user['id']}"
    
    # 如果没有用户信息，使用IP地址
    client_ip = request.client.host if request.client else "unknown"
    return f"ip_{client_ip}"


def create_ip_based_key_func(request: Request) -> str:
    """基于IP的键生成函数"""
    # 获取真实IP地址
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return f"ip_{forwarded_for.split(',')[0].strip()}"
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return f"ip_{real_ip}"
    
    client_ip = request.client.host if request.client else "unknown"
    return f"ip_{client_ip}"


def create_api_key_based_key_func(request: Request) -> str:
    """基于API密钥的键生成函数"""
    api_key = request.headers.get("X-API-Key")
    if api_key:
        # 使用API密钥的哈希值作为键
        import hashlib
        key_hash = hashlib.md5(api_key.encode()).hexdigest()[:8]
        return f"api_{key_hash}"
    
    # 如果没有API密钥，回退到IP地址
    return create_ip_based_key_func(request)