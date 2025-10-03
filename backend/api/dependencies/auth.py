#!/usr/bin/env python3
"""
API认证依赖项
提供用户认证和API密钥验证

运行环境: Python 3.11+
依赖: fastapi, jose, passlib, typing
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.infrastructure.config.settings import get_settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer认证
security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
        
    Returns:
        密码是否正确
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希
    
    Args:
        password: 明文密码
        
    Returns:
        哈希密码
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌
    
    Args:
        data: 令牌数据
        expires_delta: 过期时间增量
        
    Returns:
        JWT令牌
    """
    settings = get_settings()
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.security.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.security.secret_key, 
        algorithm=settings.security.algorithm
    )
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """创建刷新令牌
    
    Args:
        data: 令牌数据
        
    Returns:
        JWT刷新令牌
    """
    settings = get_settings()
    to_encode = data.copy()
    
    expire = datetime.utcnow() + timedelta(days=settings.security.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.security.secret_key,
        algorithm=settings.security.algorithm
    )
    
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """验证令牌
    
    Args:
        token: JWT令牌
        
    Returns:
        令牌载荷或None
    """
    try:
        settings = get_settings()
        payload = jwt.decode(
            token,
            settings.security.secret_key,
            algorithms=[settings.security.algorithm]
        )
        
        # 检查令牌是否过期
        exp = payload.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            return None
        
        return payload
        
    except JWTError:
        return None


def verify_api_key(api_key: str) -> bool:
    """验证API密钥
    
    Args:
        api_key: API密钥
        
    Returns:
        API密钥是否有效
    """
    settings = get_settings()
    
    if not settings.security.require_api_key:
        return True
    
    return api_key in settings.security.api_keys


async def get_current_user_from_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """从令牌获取当前用户
    
    Args:
        credentials: HTTP认证凭据
        
    Returns:
        用户信息或None
    """
    if not credentials:
        return None
    
    payload = verify_token(credentials.credentials)
    if not payload:
        return None
    
    # 检查令牌类型
    if payload.get("type") == "refresh":
        return None
    
    username = payload.get("sub")
    if not username:
        return None
    
    # 从用户服务获取真实用户信息
    from backend.services.user_service import user_service
    user = user_service.get_user_by_username(username)
    if not user or not user.is_active:
        return None
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
        "roles": ["admin"] if user.is_admin else ["user"],
        "permissions": ["read", "write"],
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None
    }


async def get_current_user_from_api_key(x_api_key: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """从API密钥获取当前用户
    
    Args:
        x_api_key: API密钥头
        
    Returns:
        用户信息或None
    """
    if not x_api_key:
        return None
    
    if not verify_api_key(x_api_key):
        return None
    
    # API密钥用户（系统用户）
    return {
        "id": "api_user",
        "username": "api_user",
        "email": "api@system.com",
        "roles": ["api_user"],
        "permissions": ["read", "write"],
        "is_active": True,
        "auth_type": "api_key"
    }


async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """获取当前用户（支持多种认证方式）
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        用户信息或None
    """
    # 首先尝试从JWT令牌获取用户
    credentials = await security(request)
    if credentials:
        user = await get_current_user_from_token(credentials)
        if user:
            return user
    
    # 然后尝试从API密钥获取用户
    api_key = request.headers.get("X-API-Key")
    if api_key:
        user = await get_current_user_from_api_key(api_key)
        if user:
            return user
    
    return None


async def require_authentication(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    """要求用户认证
    
    Args:
        current_user: 当前用户
        
    Returns:
        用户信息
        
    Raises:
        HTTPException: 未认证时
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已禁用"
        )
    
    return current_user


async def require_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """要求API密钥认证
    
    Args:
        x_api_key: API密钥头
        
    Returns:
        API密钥
        
    Raises:
        HTTPException: API密钥无效时
    """
    settings = get_settings()
    
    if not settings.security.require_api_key:
        return "not_required"
    
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少API密钥",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if not verify_api_key(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API密钥",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    return x_api_key


def require_roles(required_roles: list[str]):
    """要求特定角色
    
    Args:
        required_roles: 必需的角色列表
        
    Returns:
        依赖函数
    """
    async def check_roles(current_user: Dict[str, Any] = Depends(require_authentication)) -> Dict[str, Any]:
        user_roles = current_user.get("roles", [])
        
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return check_roles


def require_permissions(required_permissions: list[str]):
    """要求特定权限
    
    Args:
        required_permissions: 必需的权限列表
        
    Returns:
        依赖函数
    """
    async def check_permissions(current_user: Dict[str, Any] = Depends(require_authentication)) -> Dict[str, Any]:
        user_permissions = current_user.get("permissions", [])
        
        if not all(perm in user_permissions for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下权限: {', '.join(required_permissions)}"
            )
        
        return current_user
    
    return check_permissions


async def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """获取可选用户（不抛出异常）
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        用户信息或None
    """
    try:
        return await get_current_user(request)
    except Exception:
        return None


class RateLimitChecker:
    """速率限制检查器"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # 简单的内存存储，生产环境应使用Redis
    
    def is_allowed(self, identifier: str) -> bool:
        """检查是否允许请求
        
        Args:
            identifier: 请求标识符（用户ID、IP等）
            
        Returns:
            是否允许请求
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        # 清理过期记录
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > window_start
            ]
        else:
            self.requests[identifier] = []
        
        # 检查请求数量
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # 记录当前请求
        self.requests[identifier].append(now)
        return True


# 全局速率限制检查器
rate_limiter = RateLimitChecker()


async def check_rate_limit(request: Request, current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)):
    """检查速率限制
    
    Args:
        request: FastAPI请求对象
        current_user: 当前用户
        
    Raises:
        HTTPException: 超过速率限制时
    """
    settings = get_settings()
    
    if not settings.security.rate_limit_enabled:
        return
    
    # 确定标识符
    if current_user:
        identifier = f"user_{current_user['id']}"
    else:
        # 使用IP地址
        client_ip = request.client.host if request.client else "unknown"
        identifier = f"ip_{client_ip}"
    
    # 检查速率限制
    if not rate_limiter.is_allowed(identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后再试",
            headers={
                "Retry-After": str(settings.security.rate_limit_window)
            }
        )


# 管理员权限检查
require_admin = require_roles(["admin", "superuser"])

# 获取当前管理员用户
async def get_current_admin_user(current_user: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    """获取当前管理员用户
    
    Args:
        current_user: 当前用户（必须是管理员）
        
    Returns:
        管理员用户信息
    """
    return current_user

# 读权限检查
require_read_permission = require_permissions(["read"])

# 写权限检查
require_write_permission = require_permissions(["write"])

# 删除权限检查
require_delete_permission = require_permissions(["delete"])


# 用户信息验证函数
def validate_user_data(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """验证用户数据
    
    Args:
        user_data: 用户数据
        
    Returns:
        验证后的用户数据
        
    Raises:
        ValueError: 数据无效时
    """
    required_fields = ["username", "email"]
    
    for field in required_fields:
        if field not in user_data or not user_data[field]:
            raise ValueError(f"缺少必需字段: {field}")
    
    # 验证邮箱格式
    email = user_data["email"]
    if "@" not in email or "." not in email:
        raise ValueError("无效的邮箱格式")
    
    # 验证用户名
    username = user_data["username"]
    if len(username) < 3 or len(username) > 50:
        raise ValueError("用户名长度必须在3-50个字符之间")
    
    return user_data


# 令牌刷新函数
async def refresh_access_token(refresh_token: str) -> Optional[str]:
    """刷新访问令牌
    
    Args:
        refresh_token: 刷新令牌
        
    Returns:
        新的访问令牌或None
    """
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return None
    
    # 创建新的访问令牌
    new_token_data = {
        "sub": payload.get("sub"),
        "username": payload.get("username"),
        "email": payload.get("email"),
        "roles": payload.get("roles", []),
        "permissions": payload.get("permissions", []),
        "is_active": payload.get("is_active", True)
    }
    
    return create_access_token(new_token_data)