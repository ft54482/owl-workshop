from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
import uuid

from ..models.database_models import (
    User, Task, TaskCreate, TaskUpdate, APIResponse, PaginatedResponse
)
from ..middleware.supabase_auth import get_current_user
from ..config.supabase_config import get_supabase_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["任务管理"])

class CreateTaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    task_type: str
    priority: int = 1
    estimated_duration: Optional[int] = None
    config: Dict[str, Any] = {}

class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    config: Optional[Dict[str, Any]] = None

@router.post("", response_model=APIResponse[Task])
async def create_task(request: CreateTaskRequest, current_user: User = Depends(get_current_user)):
    """
    创建新任务
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 检查用户余额（如果需要）
        if current_user.balance is not None and current_user.balance <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="余额不足，请先充值"
            )
        
        # 检查用户当前运行的任务数量
        running_tasks = supabase.table('tasks').select('id').eq('user_id', current_user.id).eq('status', 'running').execute()
        if len(running_tasks.data) >= 5:  # 限制每个用户最多5个并发任务
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="并发任务数量已达上限，请等待现有任务完成"
            )
        
        # 创建任务数据
        task_id = str(uuid.uuid4())
        task_data = {
            'id': task_id,
            'user_id': current_user.id,
            'title': request.title,
            'description': request.description,
            'task_type': request.task_type,
            'status': 'pending',
            'progress': 0.0,
            'priority': request.priority,
            'estimated_duration': request.estimated_duration,
            'config': request.config,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # 插入任务
        result = supabase.table('tasks').insert(task_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建任务失败"
            )
        
        task = Task(**result.data[0])
        logger.info(f"任务创建成功: {task.id} by {current_user.email}")
        
        # 这里可以添加任务调度逻辑
        # await schedule_task(task)
        
        return APIResponse(
            success=True,
            message="任务创建成功",
            data=task
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建任务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建任务失败"
        )

@router.get("", response_model=PaginatedResponse[Task])
async def get_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(get_current_user)
):
    """
    获取任务列表
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 构建查询
        query = supabase.table('tasks').select('*').eq('user_id', current_user.id)
        
        # 添加过滤条件
        if status:
            query = query.eq('status', status)
        if task_type:
            query = query.eq('task_type', task_type)
        
        # 添加排序
        desc = sort_order.lower() == 'desc'
        query = query.order(sort_by, desc=desc)
        
        # 获取总数
        count_query = supabase.table('tasks').select('id', count='exact').eq('user_id', current_user.id)
        if status:
            count_query = count_query.eq('status', status)
        if task_type:
            count_query = count_query.eq('task_type', task_type)
        
        count_result = count_query.execute()
        total = count_result.count
        
        # 分页查询
        offset = (page - 1) * page_size
        result = query.range(offset, offset + page_size - 1).execute()
        
        tasks = [Task(**task_data) for task_data in result.data]
        total_pages = (total + page_size - 1) // page_size
        
        return PaginatedResponse(
            items=tasks,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取任务列表失败"
        )

@router.get("/{task_id}", response_model=APIResponse[Task])
async def get_task(task_id: str, current_user: User = Depends(get_current_user)):
    """
    获取任务详情
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 查询任务
        result = supabase.table('tasks').select('*').eq('id', task_id).eq('user_id', current_user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        task = Task(**result.data[0])
        
        return APIResponse(
            success=True,
            message="获取任务详情成功",
            data=task
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取任务详情失败"
        )

@router.put("/{task_id}", response_model=APIResponse[Task])
async def update_task(task_id: str, request: UpdateTaskRequest, current_user: User = Depends(get_current_user)):
    """
    更新任务信息
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 检查任务是否存在且属于当前用户
        task_result = supabase.table('tasks').select('*').eq('id', task_id).eq('user_id', current_user.id).execute()
        
        if not task_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        current_task = task_result.data[0]
        
        # 检查任务状态是否允许修改
        if current_task['status'] in ['running', 'completed']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="任务正在运行或已完成，无法修改"
            )
        
        # 准备更新数据
        update_data = {'updated_at': datetime.utcnow().isoformat()}
        
        if request.title is not None:
            update_data['title'] = request.title
        if request.description is not None:
            update_data['description'] = request.description
        if request.priority is not None:
            update_data['priority'] = request.priority
        if request.config is not None:
            update_data['config'] = request.config
        
        # 更新任务
        result = supabase.table('tasks').update(update_data).eq('id', task_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新任务失败"
            )
        
        task = Task(**result.data[0])
        logger.info(f"任务更新成功: {task_id} by {current_user.email}")
        
        return APIResponse(
            success=True,
            message="任务更新成功",
            data=task
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新任务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新任务失败"
        )

@router.post("/{task_id}/cancel", response_model=APIResponse)
async def cancel_task(task_id: str, current_user: User = Depends(get_current_user)):
    """
    取消任务
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 检查任务是否存在且属于当前用户
        task_result = supabase.table('tasks').select('*').eq('id', task_id).eq('user_id', current_user.id).execute()
        
        if not task_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        current_task = task_result.data[0]
        
        # 检查任务状态是否允许取消
        if current_task['status'] in ['completed', 'failed', 'cancelled']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="任务已完成或已取消，无法再次取消"
            )
        
        # 更新任务状态为已取消
        supabase.table('tasks').update({
            'status': 'cancelled',
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', task_id).execute()
        
        logger.info(f"任务取消成功: {task_id} by {current_user.email}")
        
        # 这里可以添加通知GPU服务器停止任务的逻辑
        # await notify_gpu_server_cancel_task(task_id)
        
        return APIResponse(
            success=True,
            message="任务取消成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取消任务失败"
        )

@router.post("/{task_id}/retry", response_model=APIResponse[Task])
async def retry_task(task_id: str, current_user: User = Depends(get_current_user)):
    """
    重新运行任务
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 检查任务是否存在且属于当前用户
        task_result = supabase.table('tasks').select('*').eq('id', task_id).eq('user_id', current_user.id).execute()
        
        if not task_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        current_task = task_result.data[0]
        
        # 检查任务状态是否允许重试
        if current_task['status'] not in ['failed', 'cancelled']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只有失败或已取消的任务才能重新运行"
            )
        
        # 重置任务状态
        update_data = {
            'status': 'pending',
            'progress': 0.0,
            'error_message': None,
            'result': None,
            'started_at': None,
            'completed_at': None,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('tasks').update(update_data).eq('id', task_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="重新运行任务失败"
            )
        
        task = Task(**result.data[0])
        logger.info(f"任务重新运行: {task_id} by {current_user.email}")
        
        # 这里可以添加重新调度任务的逻辑
        # await schedule_task(task)
        
        return APIResponse(
            success=True,
            message="任务重新运行成功",
            data=task
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新运行任务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重新运行任务失败"
        )

@router.delete("/{task_id}", response_model=APIResponse)
async def delete_task(task_id: str, current_user: User = Depends(get_current_user)):
    """
    删除任务
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 检查任务是否存在且属于当前用户
        task_result = supabase.table('tasks').select('*').eq('id', task_id).eq('user_id', current_user.id).execute()
        
        if not task_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        current_task = task_result.data[0]
        
        # 检查任务状态是否允许删除
        if current_task['status'] == 'running':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="正在运行的任务无法删除，请先取消任务"
            )
        
        # 删除任务
        supabase.table('tasks').delete().eq('id', task_id).execute()
        
        logger.info(f"任务删除成功: {task_id} by {current_user.email}")
        
        return APIResponse(
            success=True,
            message="任务删除成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除任务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除任务失败"
        )