from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
from datetime import datetime

from ..models.database_models import User, APIResponse, UserStats
from ..middleware.supabase_auth import get_current_user, hash_password, verify_password
from ..config.supabase_config import get_supabase_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["用户管理"])

class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.get("/me", response_model=APIResponse[User])
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    获取当前用户详细信息
    """
    try:
        # 获取最新的用户信息，包括余额等
        supabase = get_supabase_manager().get_client()
        user_data = supabase.table('users').select('*').eq('id', current_user.id).execute()
        
        if not user_data.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        user_info = user_data.data[0]
        user = User(**user_info)
        
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

@router.put("/me", response_model=APIResponse[User])
async def update_user_profile(request: UpdateUserRequest, current_user: User = Depends(get_current_user)):
    """
    更新用户信息
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 准备更新数据
        update_data = {}
        if request.username is not None:
            # 检查用户名是否已被使用
            existing_user = supabase.table('users').select('id').eq('username', request.username).neq('id', current_user.id).execute()
            if existing_user.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已被使用"
                )
            update_data['username'] = request.username
        
        if request.full_name is not None:
            update_data['full_name'] = request.full_name
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有提供要更新的数据"
            )
        
        # 添加更新时间
        update_data['updated_at'] = datetime.utcnow().isoformat()
        
        # 更新用户信息
        result = supabase.table('users').update(update_data).eq('id', current_user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        updated_user = User(**result.data[0])
        logger.info(f"用户信息更新成功: {current_user.email}")
        
        return APIResponse(
            success=True,
            message="用户信息更新成功",
            data=updated_user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户信息失败"
        )

@router.post("/change-password", response_model=APIResponse)
async def change_password(request: ChangePasswordRequest, current_user: User = Depends(get_current_user)):
    """
    修改密码
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 获取当前用户的密码哈希
        user_data = supabase.table('users').select('password_hash').eq('id', current_user.id).execute()
        if not user_data.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 验证当前密码
        current_password_hash = user_data.data[0]['password_hash']
        if not verify_password(request.current_password, current_password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前密码错误"
            )
        
        # 验证新密码强度
        if len(request.new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="新密码长度至少6位"
            )
        
        # 生成新密码哈希
        new_password_hash = hash_password(request.new_password)
        
        # 更新密码
        supabase.table('users').update({
            'password_hash': new_password_hash,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', current_user.id).execute()
        
        logger.info(f"用户密码修改成功: {current_user.email}")
        
        return APIResponse(
            success=True,
            message="密码修改成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改密码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改密码失败"
        )

@router.get("/stats", response_model=APIResponse[UserStats])
async def get_user_stats(current_user: User = Depends(get_current_user)):
    """
    获取用户统计信息
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 获取任务统计
        tasks_result = supabase.table('tasks').select('status, cost').eq('user_id', current_user.id).execute()
        tasks = tasks_result.data
        
        # 计算统计数据
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t['status'] == 'completed'])
        failed_tasks = len([t for t in tasks if t['status'] == 'failed'])
        total_cost = sum(float(t['cost'] or 0) for t in tasks)
        
        # 获取最后任务时间
        last_task_result = supabase.table('tasks').select('created_at').eq('user_id', current_user.id).order('created_at', desc=True).limit(1).execute()
        last_task_date = last_task_result.data[0]['created_at'] if last_task_result.data else None
        
        stats = UserStats(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            total_cost=total_cost,
            current_balance=current_user.balance or 0.0,
            last_task_date=last_task_date
        )
        
        return APIResponse(
            success=True,
            message="获取用户统计成功",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"获取用户统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户统计失败"
        )