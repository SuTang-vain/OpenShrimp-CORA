#!/usr/bin/env python3
"""
用户服务
提供用户管理、认证和授权功能

运行环境: Python 3.11+
依赖: bcrypt, jose, passlib, typing
"""

import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
import logging

from backend.core.models.user import User, UserCreate, UserLogin, UserResponse, AuthResponse, ChangePasswordRequest
from backend.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)

# 密码加密上下文 (临时注释掉)
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# 内存用户存储（生产环境应使用数据库）
users_db: Dict[str, User] = {}
users_by_email: Dict[str, str] = {}  # email -> user_id 映射
users_by_username: Dict[str, str] = {}  # username -> user_id 映射


class UserService:
    """用户服务类"""
    
    def __init__(self):
        """初始化用户服务"""
        self.settings = get_settings()
        self.secret_key = self.settings.security.secret_key
        self.algorithm = self.settings.security.algorithm
        self.access_token_expire_minutes = self.settings.security.access_token_expire_minutes
        self.refresh_token_expire_days = self.settings.security.refresh_token_expire_days
        
        # 创建默认管理员用户
        self._create_default_admin()
    
    def _create_default_admin(self):
        """创建默认管理员用户"""
        admin_username = "admin"
        admin_email = "admin@shrimpagent.com"
        
        # 检查是否已存在管理员
        if admin_username not in users_by_username:
            admin_user = User(
                id=str(uuid.uuid4()),
                username=admin_username,
                email=admin_email,
                full_name="系统管理员",
                password_hash="admin123",  # 临时使用明文密码
                is_admin=True,
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            users_db[admin_user.id] = admin_user
            users_by_email[admin_email] = admin_user.id
            users_by_username[admin_username] = admin_user.id
            
            logger.info(f"创建默认管理员用户: {admin_username}")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
            
        Returns:
            密码是否正确
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """生成密码哈希
        
        Args:
            password: 明文密码
            
        Returns:
            哈希密码
        """
        return pwd_context.hash(password)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            用户对象或None
        """
        user_id = users_by_username.get(username)
        if user_id:
            return users_db.get(user_id)
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户
        
        Args:
            email: 邮箱地址
            
        Returns:
            用户对象或None
        """
        user_id = users_by_email.get(email)
        if user_id:
            return users_db.get(user_id)
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户对象或None
        """
        return users_db.get(user_id)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """认证用户
        
        Args:
            username: 用户名或邮箱
            password: 密码
            
        Returns:
            认证成功的用户对象或None
        """
        # 尝试用户名登录
        user = self.get_user_by_username(username)
        if not user:
            # 尝试邮箱登录
            user = self.get_user_by_email(username)
        
        if not user:
            return None
        
        # 临时使用明文密码比较
        if password != user.password_hash:
            return None
        
        if not user.is_active:
            return None
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        users_db[user.id] = user
        
        return user
    
    def create_user(self, user_data: UserCreate) -> Optional[User]:
        """创建新用户
        
        Args:
            user_data: 用户创建数据
            
        Returns:
            创建的用户对象或None
        """
        try:
            logger.info(f"开始创建用户: {user_data.username}, email: {user_data.email}")
            
            # 检查用户名是否已存在
            if user_data.username in users_by_username:
                logger.warning(f"用户名已存在: {user_data.username}")
                return None
            
            # 检查邮箱是否已存在
            if user_data.email in users_by_email:
                logger.warning(f"邮箱已被注册: {user_data.email}")
                return None
            
            # 创建新用户
            user_id = str(uuid.uuid4())
            new_user = User(
                id=user_id,
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                password_hash=user_data.password,  # 临时使用明文密码
                is_active=True,
                is_admin=False,
                created_at=datetime.utcnow()
            )
            
            # 保存用户
            users_db[user_id] = new_user
            users_by_email[user_data.email] = user_id
            users_by_username[user_data.username] = user_id
            
            logger.info(f"用户创建成功: {user_data.username}, ID: {user_id}")
            return new_user
            
        except Exception as e:
            logger.error(f"用户创建失败: {e}", exc_info=True)
            return None
    
    def login_user(self, login_data: UserLogin) -> AuthResponse:
        """用户登录
        
        Args:
            login_data: 登录数据
            
        Returns:
            认证响应
        """
        try:
            # 认证用户
            user = self.authenticate_user(login_data.username, login_data.password)
            if not user:
                return AuthResponse(
                    success=False,
                    message="用户名或密码错误"
                )
            
            # 生成访问令牌
            access_token = self.create_access_token(data={"sub": user.username})
            refresh_token = self.create_refresh_token(data={"sub": user.username})
            
            logger.info(f"用户登录成功: {user.username}")
            
            return AuthResponse(
                success=True,
                message="登录成功",
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=self.access_token_expire_minutes * 60,
                user=user.to_response()
            )
            
        except Exception as e:
            logger.error(f"用户登录失败: {e}")
            return AuthResponse(
                success=False,
                message="登录失败，请稍后重试"
            )
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌
        
        Args:
            data: 令牌数据
            expires_delta: 过期时间增量
            
        Returns:
            JWT令牌
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """创建刷新令牌
        
        Args:
            data: 令牌数据
            
        Returns:
            JWT刷新令牌
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            令牌数据或None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                return None
            return payload
        except JWTError:
            return None
    
    def get_current_user_from_token(self, token: str) -> Optional[User]:
        """从令牌获取当前用户
        
        Args:
            token: JWT令牌
            
        Returns:
            用户对象或None
        """
        payload = self.verify_token(token)
        if not payload:
            return None
        
        username = payload.get("sub")
        if not username:
            return None
        
        user = self.get_user_by_username(username)
        return user
    
    def refresh_access_token(self, refresh_token: str) -> AuthResponse:
        """刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            认证响应
        """
        try:
            payload = self.verify_token(refresh_token)
            if not payload or payload.get("type") != "refresh":
                return AuthResponse(
                    success=False,
                    message="无效的刷新令牌"
                )
            
            username = payload.get("sub")
            user = self.get_user_by_username(username)
            if not user or not user.is_active:
                return AuthResponse(
                    success=False,
                    message="用户不存在或已被禁用"
                )
            
            # 生成新的访问令牌
            access_token = self.create_access_token(data={"sub": username})
            
            return AuthResponse(
                success=True,
                message="令牌刷新成功",
                access_token=access_token,
                token_type="bearer",
                expires_in=self.access_token_expire_minutes * 60,
                user=user.to_response()
            )
            
        except Exception as e:
            logger.error(f"令牌刷新失败: {e}")
            return AuthResponse(
                success=False,
                message="令牌刷新失败"
            )
    
    def change_password(self, user_id: str, change_data: ChangePasswordRequest) -> AuthResponse:
        """修改密码
        
        Args:
            user_id: 用户ID
            change_data: 修改密码数据
            
        Returns:
            认证响应
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return AuthResponse(
                    success=False,
                    message="用户不存在"
                )
            
            # 验证当前密码
            if not self.verify_password(change_data.current_password, user.password_hash):
                return AuthResponse(
                    success=False,
                    message="当前密码错误"
                )
            
            # 更新密码
            user.password_hash = self.get_password_hash(change_data.new_password)
            user.updated_at = datetime.utcnow()
            users_db[user_id] = user
            
            logger.info(f"用户修改密码成功: {user.username}")
            
            return AuthResponse(
                success=True,
                message="密码修改成功"
            )
            
        except Exception as e:
            logger.error(f"密码修改失败: {e}")
            return AuthResponse(
                success=False,
                message="密码修改失败，请稍后重试"
            )


# 全局用户服务实例
user_service = UserService()