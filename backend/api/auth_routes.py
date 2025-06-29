from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
from datetime import datetime, timedelta

from ..models.database_models import User, UserCreate, UserLogin, APIResponse
from ..middleware.supabase_auth import (
    create_user, 
    authenticate_user, 
    create_access_token, 
    get_current_user,
    get_user_by_id
)
from ..config.supabase_config import get_supabase_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["认证"])
security = HTTPBearer()

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: User

@router.post("/register", response_model=APIResponse)
async def register(request: RegisterRequest):
    """
    用户注册
    """
    try:
        logger.info(f"用户注册请求: {request.email}")
        
        # 检查用户是否已存在
        supabase = get_supabase_manager().get_client()
        existing_user = supabase.table('users').select('*').eq('email', request.email).execute()
        
        if existing_user.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
        
        # 检查用户名是否已存在
        existing_username = supabase.table('users').select('*').eq('username', request.username).execute()
        if existing_username.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被使用"
            )
        
        # 创建用户
        user_data = UserCreate(
            email=request.email,
            username=request.username,
            password=request.password,
            full_name=request.full_name
        )
        
        user = await create_user(user_data)
        logger.info(f"用户注册成功: {user.email}")
        
        return APIResponse(
            success=True,
            message="注册成功",
            data={"user_id": user.id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )

@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(request: LoginRequest):
    """
    用户登录
    """
    try:
        logger.info(f"用户登录请求: {request.email}")
        
        # 验证用户凭据
        user = await authenticate_user(request.email, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账户已被禁用"
            )
        
        # 创建访问令牌
        access_token_expires = timedelta(minutes=30)  # 30分钟过期
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email},
            expires_delta=access_token_expires
        )
        
        # 更新最后登录时间
        supabase = get_supabase_manager().get_client()
        supabase.table('users').update({
            'last_login': datetime.utcnow().isoformat()
        }).eq('id', user.id).execute()
        
        logger.info(f"用户登录成功: {user.email}")
        
        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800,  # 30分钟
            user=user
        )
        
        return APIResponse(
            success=True,
            message="登录成功",
            data=token_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户登录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )

@router.post("/logout", response_model=APIResponse)
async def logout(current_user: User = Depends(get_current_user)):
    """
    用户登出
    """
    try:
        logger.info(f"用户登出: {current_user.email}")
        
        # 这里可以添加令牌黑名单逻辑
        # 目前只是记录日志
        
        return APIResponse(
            success=True,
            message="登出成功"
        )
        
    except Exception as e:
        logger.error(f"用户登出失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出失败"
        )

@router.get("/me", response_model=APIResponse[User])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息
    """
    try:
        # 获取最新的用户信息
        user = await get_user_by_id(current_user.id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return APIResponse(
            success=True,
            message="获取用户信息成功",
            data=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )

@router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    刷新访问令牌
    """
    try:
        # 验证当前令牌
        current_user = await get_current_user(credentials)
        
        # 创建新的访问令牌
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": current_user.id, "email": current_user.email},
            expires_delta=access_token_expires
        )
        
        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800,
            user=current_user
        )
        
        return APIResponse(
            success=True,
            message="令牌刷新成功",
            data=token_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"令牌刷新失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新失败"
        )