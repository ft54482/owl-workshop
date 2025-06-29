# -*- coding: utf-8 -*-
"""
🦉 猫头鹰工厂 - Supabase认证中间件
处理用户认证和权限验证
"""

from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from loguru import logger

from config.supabase_config import settings, supabase_manager
from models.database_models import User, UserRole

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 验证JWT令牌
        token = credentials.credentials
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except JWTError as e:
        logger.error(f"JWT验证失败: {e}")
        raise credentials_exception
    
    # 从数据库获取用户信息
    try:
        response = supabase_manager.client.table('users').select('*').eq('id', user_id).single().execute()
        if not response.data:
            raise credentials_exception
            
        user_data = response.data
        user = User(**user_data)
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账户已被禁用"
            )
            
        return user
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        raise credentials_exception

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """获取管理员用户"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

async def get_super_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """获取超级管理员用户"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    return current_user

def create_access_token(user_id: str, expires_delta: Optional[int] = None) -> str:
    """创建访问令牌"""
    from datetime import datetime, timedelta
    
    if expires_delta:
        expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode = {"sub": user_id, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt