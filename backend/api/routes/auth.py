#!/usr/bin/env python3
"""
认证API路由
提供用户注册、登录、登出等认证功能

运行环境: Python 3.11+
依赖: fastapi, pydantic, typing
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import logging

from backend.core.models.user import UserCreate, UserLogin, UserResponse, AuthResponse, ChangePasswordRequest
from backend.services.user_service import UserService, user_service
from backend.api.dependencies.services import get_user_service
from backend.api.dependencies.auth import get_current_user
from backend.shared.utils.response import create_success_response, create_error_response

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()

# HTTP Bearer 认证
security = HTTPBearer(auto_error=False)


@router.post("/register", response_model=AuthResponse)
async def register(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """用户注册"""
    try:
        logger.info(f"开始注册用户: {user_data.username}, email: {user_data.email}")
        
        # 创建用户
        user = user_service.create_user(user_data)
        if not user:
            logger.warning(f"用户注册失败: {user_data.username}")
            raise HTTPException(status_code=400, detail="注册失败，请稍后重试")
        
        logger.info(f"用户创建成功: {user.username}")
        
        # 生成访问令牌
        access_token = user_service.create_access_token(data={"sub": user.username})
        refresh_token = user_service.create_refresh_token(data={"sub": user.username})
        
        logger.info(f"用户注册成功: {user.username}")
        return AuthResponse(
            success=True,
            message="注册成功",
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=user_service.access_token_expire_minutes * 60,
            user=user.to_response()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注册过程中发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/login", response_model=AuthResponse, summary="用户登录")
async def login(login_data: UserLogin) -> AuthResponse:
    """
    用户登录
    
    Args:
        login_data: 登录数据
        
    Returns:
        认证响应，包含用户信息和访问令牌
        
    Raises:
        HTTPException: 登录失败时抛出异常
    """
    try:
        logger.info(f"用户登录请求: {login_data.username}")
        
        # 调用用户服务进行登录
        result = user_service.login_user(login_data)
        
        if not result.success:
            logger.warning(f"用户登录失败: {result.message}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.message
            )
        
        logger.info(f"用户登录成功: {login_data.username}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户登录异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )


@router.post("/logout", summary="用户登出")
async def logout(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    用户登出
    
    Args:
        credentials: HTTP认证凭据
        
    Returns:
        登出响应
        
    Note:
        由于使用JWT无状态认证，登出主要由前端处理（删除本地token）
        后端可以在此处记录登出日志或进行其他清理操作
    """
    try:
        if credentials:
            # 可以在此处添加token黑名单逻辑
            logger.info("用户登出")
        
        return create_success_response(
            message="登出成功",
            data={"logged_out": True}
        )
        
    except Exception as e:
        logger.error(f"用户登出异常: {e}", exc_info=True)
        return create_error_response(
            message="登出失败",
            code=500
        )


@router.post("/refresh", response_model=AuthResponse, summary="刷新访问令牌")
async def refresh_token(request: Request) -> AuthResponse:
    """
    刷新访问令牌
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        认证响应，包含新的访问令牌
        
    Raises:
        HTTPException: 刷新失败时抛出异常
    """
    try:
        # 从请求体获取刷新令牌
        body = await request.json()
        refresh_token = body.get("refresh_token")
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少刷新令牌"
            )
        
        # 调用用户服务刷新令牌
        result = user_service.refresh_access_token(refresh_token)
        
        if not result.success:
            logger.warning(f"令牌刷新失败: {result.message}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.message
            )
        
        logger.info("令牌刷新成功")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"令牌刷新异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新失败"
        )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserResponse:
    """
    获取当前用户信息
    
    Args:
        current_user: 当前用户（通过依赖注入获取）
        
    Returns:
        用户信息
        
    Raises:
        HTTPException: 获取失败时抛出异常
    """
    try:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未认证用户"
            )
        
        # 从用户服务获取完整用户信息
        user = user_service.get_user_by_id(current_user.get("id"))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return user.to_response()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户信息异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )


@router.post("/change-password", response_model=AuthResponse, summary="修改密码")
async def change_password(
    change_data: ChangePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> AuthResponse:
    """
    修改密码
    
    Args:
        change_data: 修改密码数据
        current_user: 当前用户（通过依赖注入获取）
        
    Returns:
        认证响应
        
    Raises:
        HTTPException: 修改失败时抛出异常
    """
    try:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未认证用户"
            )
        
        # 调用用户服务修改密码
        result = user_service.change_password(current_user.get("id"), change_data)
        
        if not result.success:
            logger.warning(f"密码修改失败: {result.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        logger.info(f"用户密码修改成功: {current_user.get('username')}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"密码修改异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码修改失败"
        )


@router.get("/status", summary="认证状态检查")
async def auth_status(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    检查认证状态
    
    Args:
        credentials: HTTP认证凭据
        
    Returns:
        认证状态信息
    """
    try:
        if not credentials:
            return create_success_response(
                message="未认证",
                data={
                    "authenticated": False,
                    "user": None
                }
            )
        
        # 验证令牌
        user = user_service.get_current_user_from_token(credentials.credentials)
        if not user:
            return create_success_response(
                message="令牌无效",
                data={
                    "authenticated": False,
                    "user": None
                }
            )
        
        return create_success_response(
            message="已认证",
            data={
                "authenticated": True,
                "user": user.to_response()
            }
        )
        
    except Exception as e:
        logger.error(f"认证状态检查异常: {e}", exc_info=True)
        return create_error_response(
            message="状态检查失败",
            code=500
        )