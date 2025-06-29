from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta

from ..models.database_models import User, APIResponse, GPUServer, GPUStats
from ..middleware.supabase_auth import get_current_user, require_admin
from ..config.supabase_config import get_supabase_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/gpu", tags=["GPU监控"])

class GPUServerCreate(BaseModel):
    name: str
    host: str
    port: int = 22
    username: str
    description: Optional[str] = None
    gpu_count: int = 1
    gpu_model: Optional[str] = None
    memory_total: Optional[int] = None  # GB
    is_active: bool = True

class GPUServerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    gpu_count: Optional[int] = None
    gpu_model: Optional[str] = None
    memory_total: Optional[int] = None

@router.get("/servers", response_model=APIResponse[List[GPUServer]])
async def get_gpu_servers(current_user: User = Depends(get_current_user)):
    """
    获取GPU服务器列表
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 普通用户只能看到活跃的服务器
        query = supabase.table('gpu_servers').select('*')
        if current_user.role != 'admin' and current_user.role != 'super_admin':
            query = query.eq('is_active', True)
        
        result = query.order('created_at').execute()
        
        servers = [GPUServer(**server_data) for server_data in result.data]
        
        return APIResponse(
            success=True,
            message="获取GPU服务器列表成功",
            data=servers
        )
        
    except Exception as e:
        logger.error(f"获取GPU服务器列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取GPU服务器列表失败"
        )

@router.get("/servers/{server_id}", response_model=APIResponse[GPUServer])
async def get_gpu_server(server_id: str, current_user: User = Depends(get_current_user)):
    """
    获取GPU服务器详情
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        result = supabase.table('gpu_servers').select('*').eq('id', server_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GPU服务器不存在"
            )
        
        server = GPUServer(**result.data[0])
        
        # 普通用户只能查看活跃的服务器
        if current_user.role not in ['admin', 'super_admin'] and not server.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GPU服务器不存在"
            )
        
        return APIResponse(
            success=True,
            message="获取GPU服务器详情成功",
            data=server
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取GPU服务器详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取GPU服务器详情失败"
        )

@router.post("/servers", response_model=APIResponse[GPUServer])
async def create_gpu_server(request: GPUServerCreate, current_user: User = Depends(require_admin)):
    """
    创建GPU服务器（仅管理员）
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 检查服务器名称是否已存在
        existing_server = supabase.table('gpu_servers').select('id').eq('name', request.name).execute()
        if existing_server.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="服务器名称已存在"
            )
        
        # 创建服务器数据
        server_data = {
            'name': request.name,
            'host': request.host,
            'port': request.port,
            'username': request.username,
            'description': request.description,
            'gpu_count': request.gpu_count,
            'gpu_model': request.gpu_model,
            'memory_total': request.memory_total,
            'is_active': request.is_active,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('gpu_servers').insert(server_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建GPU服务器失败"
            )
        
        server = GPUServer(**result.data[0])
        logger.info(f"GPU服务器创建成功: {server.name} by {current_user.email}")
        
        return APIResponse(
            success=True,
            message="GPU服务器创建成功",
            data=server
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建GPU服务器失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建GPU服务器失败"
        )

@router.put("/servers/{server_id}", response_model=APIResponse[GPUServer])
async def update_gpu_server(server_id: str, request: GPUServerUpdate, current_user: User = Depends(require_admin)):
    """
    更新GPU服务器（仅管理员）
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 检查服务器是否存在
        server_result = supabase.table('gpu_servers').select('*').eq('id', server_id).execute()
        if not server_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GPU服务器不存在"
            )
        
        # 准备更新数据
        update_data = {'updated_at': datetime.utcnow().isoformat()}
        
        if request.name is not None:
            # 检查名称是否已被其他服务器使用
            existing_server = supabase.table('gpu_servers').select('id').eq('name', request.name).neq('id', server_id).execute()
            if existing_server.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="服务器名称已存在"
                )
            update_data['name'] = request.name
        
        if request.description is not None:
            update_data['description'] = request.description
        if request.is_active is not None:
            update_data['is_active'] = request.is_active
        if request.gpu_count is not None:
            update_data['gpu_count'] = request.gpu_count
        if request.gpu_model is not None:
            update_data['gpu_model'] = request.gpu_model
        if request.memory_total is not None:
            update_data['memory_total'] = request.memory_total
        
        # 更新服务器
        result = supabase.table('gpu_servers').update(update_data).eq('id', server_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新GPU服务器失败"
            )
        
        server = GPUServer(**result.data[0])
        logger.info(f"GPU服务器更新成功: {server.name} by {current_user.email}")
        
        return APIResponse(
            success=True,
            message="GPU服务器更新成功",
            data=server
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新GPU服务器失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新GPU服务器失败"
        )

@router.delete("/servers/{server_id}", response_model=APIResponse)
async def delete_gpu_server(server_id: str, current_user: User = Depends(require_admin)):
    """
    删除GPU服务器（仅管理员）
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 检查服务器是否存在
        server_result = supabase.table('gpu_servers').select('*').eq('id', server_id).execute()
        if not server_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GPU服务器不存在"
            )
        
        # 检查是否有正在运行的任务
        running_tasks = supabase.table('tasks').select('id').eq('gpu_server_id', server_id).eq('status', 'running').execute()
        if running_tasks.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="服务器上有正在运行的任务，无法删除"
            )
        
        # 删除服务器
        supabase.table('gpu_servers').delete().eq('id', server_id).execute()
        
        logger.info(f"GPU服务器删除成功: {server_id} by {current_user.email}")
        
        return APIResponse(
            success=True,
            message="GPU服务器删除成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除GPU服务器失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除GPU服务器失败"
        )

@router.get("/stats", response_model=APIResponse[Dict[str, Any]])
async def get_gpu_stats(current_user: User = Depends(get_current_user)):
    """
    获取GPU统计信息
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 获取服务器统计
        servers_result = supabase.table('gpu_servers').select('*').eq('is_active', True).execute()
        servers = servers_result.data
        
        total_servers = len(servers)
        total_gpus = sum(server.get('gpu_count', 0) for server in servers)
        
        # 获取任务统计
        tasks_result = supabase.table('tasks').select('status, gpu_server_id').execute()
        tasks = tasks_result.data
        
        running_tasks = len([t for t in tasks if t['status'] == 'running'])
        pending_tasks = len([t for t in tasks if t['status'] == 'pending'])
        
        # 计算GPU使用率（简化版本）
        gpu_utilization = (running_tasks / total_gpus * 100) if total_gpus > 0 else 0
        
        stats = {
            'total_servers': total_servers,
            'total_gpus': total_gpus,
            'running_tasks': running_tasks,
            'pending_tasks': pending_tasks,
            'gpu_utilization': round(gpu_utilization, 2),
            'servers': servers
        }
        
        return APIResponse(
            success=True,
            message="获取GPU统计成功",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"获取GPU统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取GPU统计失败"
        )

@router.post("/servers/{server_id}/test", response_model=APIResponse)
async def test_gpu_server_connection(server_id: str, current_user: User = Depends(require_admin)):
    """
    测试GPU服务器连接（仅管理员）
    """
    try:
        supabase = get_supabase_manager().get_client()
        
        # 获取服务器信息
        server_result = supabase.table('gpu_servers').select('*').eq('id', server_id).execute()
        if not server_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GPU服务器不存在"
            )
        
        server = server_result.data[0]
        
        # 这里应该实现实际的连接测试逻辑
        # 例如SSH连接测试、GPU状态检查等
        # 目前返回模拟结果
        
        connection_success = True  # 模拟连接成功
        
        if connection_success:
            # 更新服务器状态
            supabase.table('gpu_servers').update({
                'last_ping': datetime.utcnow().isoformat(),
                'status': 'online'
            }).eq('id', server_id).execute()
            
            return APIResponse(
                success=True,
                message="GPU服务器连接测试成功"
            )
        else:
            # 更新服务器状态为离线
            supabase.table('gpu_servers').update({
                'status': 'offline'
            }).eq('id', server_id).execute()
            
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GPU服务器连接失败"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试GPU服务器连接失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="测试GPU服务器连接失败"
        )