from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta

from ..models.database_models import (
    User, APIResponse, PaginatedResponse, SystemStats
)
from ..middleware.supabase_auth import get_current_user, require_admin, require_super_admin
from ..config.supabase_config import get_supabase_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["系统管理"])

class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    balance: Optional[float] = None

class SystemConfigUpdate(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None

@router.get("/users", response_model=PaginatedResponse[User])
async def get_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(require_admin)
):
    """
    获取所有用户列表（仅管理员）
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 构建查询
        query = supabase.table('users').select('*')
        
        # 添加搜索条件
        if search:
            # 这里简化处理，实际应该使用全文搜索
            query = query.or_(f'username.ilike.%{search}%,email.ilike.%{search}%,full_name.ilike.%{search}%')
        
        if role:
            query = query.eq('role', role)
        
        if is_active is not None:
            query = query.eq('is_active', is_active)
        
        # 获取总数
        count_query = supabase.table('users').select('id', count='exact')
        if search:
            count_query = count_query.or_(f'username.ilike.%{search}%,email.ilike.%{search}%,full_name.ilike.%{search}%')
        if role:
            count_query = count_query.eq('role', role)
        if is_active is not None:
            count_query = count_query.eq('is_active', is_active)
        
        count_result = count_query.execute()
        total = count_result.count
        
        # 分页查询
        offset = (page - 1) * page_size
        result = query.order('created_at', desc=True).range(offset, offset + page_size - 1).execute()
        
        users = [User(**user_data) for user_data in result.data]
        total_pages = (total + page_size - 1) // page_size
        
        return PaginatedResponse(
            items=users,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表失败"
        )

@router.get("/users/{user_id}", response_model=APIResponse[User])
async def get_user_by_id(user_id: str, current_user: User = Depends(require_admin)):
    """
    获取指定用户详情（仅管理员）
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        result = supabase.table('users').select('*').eq('id', user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        user = User(**result.data[0])
        
        return APIResponse(
            success=True,
            message="获取用户详情成功",
            data=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户详情失败"
        )

@router.put("/users/{user_id}", response_model=APIResponse[User])
async def update_user(user_id: str, request: UpdateUserRequest, current_user: User = Depends(require_admin)):
    """
    更新用户信息（仅管理员）
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 检查用户是否存在
        user_result = supabase.table('users').select('*').eq('id', user_id).execute()
        if not user_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        target_user = user_result.data[0]
        
        # 权限检查：只有超级管理员可以修改管理员
        if target_user['role'] in ['admin', 'super_admin'] and current_user.role != 'super_admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，无法修改管理员用户"
            )
        
        # 准备更新数据
        update_data = {'updated_at': datetime.utcnow().isoformat()}
        
        if request.username is not None:
            # 检查用户名是否已被使用
            existing_user = supabase.table('users').select('id').eq('username', request.username).neq('id', user_id).execute()
            if existing_user.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已被使用"
                )
            update_data['username'] = request.username
        
        if request.full_name is not None:
            update_data['full_name'] = request.full_name
        
        if request.role is not None:
            # 只有超级管理员可以修改角色
            if current_user.role != 'super_admin':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足，无法修改用户角色"
                )
            
            valid_roles = ['user', 'admin', 'super_admin']
            if request.role not in valid_roles:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的角色，有效角色: {', '.join(valid_roles)}"
                )
            
            update_data['role'] = request.role
        
        if request.is_active is not None:
            update_data['is_active'] = request.is_active
        
        if request.balance is not None:
            if request.balance < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="余额不能为负数"
                )
            update_data['balance'] = request.balance
        
        # 更新用户
        result = supabase.table('users').update(update_data).eq('id', user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新用户失败"
            )
        
        user = User(**result.data[0])
        logger.info(f"用户更新成功: {user_id} by {current_user.email}")
        
        return APIResponse(
            success=True,
            message="用户更新成功",
            data=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户失败"
        )

@router.delete("/users/{user_id}", response_model=APIResponse)
async def delete_user(user_id: str, current_user: User = Depends(require_super_admin)):
    """
    删除用户（仅超级管理员）
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 检查用户是否存在
        user_result = supabase.table('users').select('*').eq('id', user_id).execute()
        if not user_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        target_user = user_result.data[0]
        
        # 不能删除自己
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除自己"
            )
        
        # 检查用户是否有正在运行的任务
        running_tasks = supabase.table('tasks').select('id').eq('user_id', user_id).eq('status', 'running').execute()
        if running_tasks.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户有正在运行的任务，无法删除"
            )
        
        # 删除用户（这里应该考虑软删除）
        supabase.table('users').update({
            'is_active': False,
            'deleted_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', user_id).execute()
        
        logger.info(f"用户删除成功: {user_id} by {current_user.email}")
        
        return APIResponse(
            success=True,
            message="用户删除成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户失败"
        )

@router.get("/stats", response_model=APIResponse[SystemStats])
async def get_system_stats(current_user: User = Depends(require_admin)):
    """
    获取系统统计信息（仅管理员）
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 获取用户统计
        users_result = supabase.table('users').select('role, is_active, created_at').execute()
        users = users_result.data
        
        total_users = len(users)
        active_users = len([u for u in users if u['is_active']])
        admin_users = len([u for u in users if u['role'] in ['admin', 'super_admin']])
        
        # 计算新用户（最近7天）
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_users = len([u for u in users if datetime.fromisoformat(u['created_at'].replace('Z', '+00:00')) > week_ago])
        
        # 获取任务统计
        tasks_result = supabase.table('tasks').select('status, created_at, cost').execute()
        tasks = tasks_result.data
        
        total_tasks = len(tasks)
        running_tasks = len([t for t in tasks if t['status'] == 'running'])
        completed_tasks = len([t for t in tasks if t['status'] == 'completed'])
        failed_tasks = len([t for t in tasks if t['status'] == 'failed'])
        
        # 计算今日任务
        today = datetime.utcnow().date()
        today_tasks = len([t for t in tasks if datetime.fromisoformat(t['created_at'].replace('Z', '+00:00')).date() == today])
        
        # 计算总收入
        total_revenue = sum(float(t['cost'] or 0) for t in tasks if t['status'] == 'completed')
        
        # 获取GPU服务器统计
        servers_result = supabase.table('gpu_servers').select('is_active, gpu_count').execute()
        servers = servers_result.data
        
        total_servers = len(servers)
        active_servers = len([s for s in servers if s['is_active']])
        total_gpus = sum(s['gpu_count'] for s in servers if s['is_active'])
        
        # 获取充值统计
        recharge_result = supabase.table('recharge_records').select('amount, created_at').execute()
        recharges = recharge_result.data
        
        total_recharge = sum(float(r['amount']) for r in recharges)
        
        # 计算今日充值
        today_recharge = sum(float(r['amount']) for r in recharges 
                           if datetime.fromisoformat(r['created_at'].replace('Z', '+00:00')).date() == today)
        
        stats = SystemStats(
            total_users=total_users,
            active_users=active_users,
            new_users=new_users,
            admin_users=admin_users,
            total_tasks=total_tasks,
            running_tasks=running_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            today_tasks=today_tasks,
            total_servers=total_servers,
            active_servers=active_servers,
            total_gpus=total_gpus,
            total_revenue=total_revenue,
            total_recharge=total_recharge,
            today_recharge=today_recharge
        )
        
        return APIResponse(
            success=True,
            message="获取系统统计成功",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"获取系统统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取系统统计失败"
        )

@router.get("/logs", response_model=APIResponse[List[Dict[str, Any]]])
async def get_system_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    level: Optional[str] = Query(None),
    current_user: User = Depends(require_admin)
):
    """
    获取系统日志（仅管理员）
    """
    try:
        # 这里应该实现实际的日志查询逻辑
        # 目前返回模拟数据
        
        logs = [
            {
                'id': '1',
                'timestamp': datetime.utcnow().isoformat(),
                'level': 'INFO',
                'message': '用户登录成功',
                'user_id': current_user.id,
                'ip_address': '192.168.1.1'
            },
            {
                'id': '2',
                'timestamp': (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                'level': 'WARNING',
                'message': 'GPU服务器连接超时',
                'server_id': 'server-1'
            }
        ]
        
        return APIResponse(
            success=True,
            message="获取系统日志成功",
            data=logs
        )
        
    except Exception as e:
        logger.error(f"获取系统日志失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取系统日志失败"
        )

@router.post("/maintenance", response_model=APIResponse)
async def toggle_maintenance_mode(enabled: bool, current_user: User = Depends(require_super_admin)):
    """
    切换维护模式（仅超级管理员）
    """
    try:
        # 这里应该实现维护模式的逻辑
        # 例如设置全局配置、停止任务调度等
        
        logger.info(f"维护模式{'开启' if enabled else '关闭'}: by {current_user.email}")
        
        return APIResponse(
            success=True,
            message=f"维护模式已{'开启' if enabled else '关闭'}"
        )
        
    except Exception as e:
        logger.error(f"切换维护模式失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="切换维护模式失败"
        )