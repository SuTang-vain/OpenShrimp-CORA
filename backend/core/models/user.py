#!/usr/bin/env python3
"""
用户数据模型
定义用户相关的数据结构和验证规则

运行环境: Python 3.11+
依赖: pydantic, typing, datetime
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
import re


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    
    @validator('username')
    def validate_username(cls, v):
        """验证用户名格式"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v


class UserCreate(UserBase):
    """用户注册请求模型"""
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    confirm_password: str = Field(..., alias="confirmPassword", description="确认密码")
    
    class Config:
        populate_by_name = True
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """验证密码确认"""
        if 'password' in values and v != values['password']:
            raise ValueError('密码和确认密码不匹配')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('密码必须包含字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含数字')
        return v


class UserLogin(BaseModel):
    """用户登录请求模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserResponse(UserBase):
    """用户响应模型"""
    id: str = Field(..., description="用户ID")
    is_active: bool = Field(True, description="是否激活")
    is_admin: bool = Field(False, description="是否管理员")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    
    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """认证响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    access_token: Optional[str] = Field(None, description="访问令牌")
    refresh_token: Optional[str] = Field(None, description="刷新令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: Optional[int] = Field(None, description="令牌过期时间(秒)")
    user: Optional[UserResponse] = Field(None, description="用户信息")


class User(UserBase):
    """用户完整模型"""
    id: str = Field(..., description="用户ID")
    password_hash: str = Field(..., description="密码哈希")
    is_active: bool = Field(True, description="是否激活")
    is_admin: bool = Field(False, description="是否管理员")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    
    class Config:
        from_attributes = True
    
    def to_response(self) -> UserResponse:
        """转换为响应模型"""
        return UserResponse(
            id=self.id,
            username=self.username,
            email=self.email,
            full_name=self.full_name,
            is_active=self.is_active,
            is_admin=self.is_admin,
            created_at=self.created_at,
            updated_at=self.updated_at,
            last_login=self.last_login
        )


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """验证密码确认"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('新密码和确认密码不匹配')
        return v
    
    @validator('new_password')
    def validate_password(cls, v):
        """验证密码强度"""
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('密码必须包含字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含数字')
        return v


class TokenData(BaseModel):
    """JWT令牌数据模型"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    is_admin: bool = False
    exp: Optional[datetime] = None