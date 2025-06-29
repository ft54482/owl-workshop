import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from ..models.database_models import Task, TaskCreate, TaskUpdate
from ..config.supabase_config import get_supabase_manager
from .gpu_service import GPUService

logger = logging.getLogger(__name__)

class TaskService:
    """
    任务服务类
    """
    
    def __init__(self):
        self.supabase = get_supabase_manager().get_client()
        self.gpu_service = GPUService()
        self._running_tasks: Dict[str, asyncio.Task] = {}
    
    async def create_task(self, user_id: str, task_data: TaskCreate) -> Task:
        """
        创建新任务
        """
        try:
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 准备任务数据
            task_dict = {
                'id': task_id,
                'user_id': user_id,
                'title': task_data.title,
                'description': task_data.description,
                'task_type': task_data.task_type,
                'status': 'pending',
                'progress': 0.0,
                'priority': task_data.priority,
                'estimated_duration': task_data.estimated_duration,
                'config': task_data.config,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # 插入数据库
            result = self.supabase.table('tasks').insert(task_dict).execute()
            
            if not result.data:
                raise Exception("创建任务失败")
            
            task = Task(**result.data[0])
            logger.info(f"任务创建成功: {task_id}")
            
            # 异步调度任务
            asyncio.create_task(self._schedule_task(task))
            
            return task
            
        except Exception as e:
            logger.error(f"创建任务失败: {str(e)}")
            raise
    
    async def get_task(self, task_id: str, user_id: Optional[str] = None) -> Optional[Task]:
        """
        获取任务详情
        """
        try:
            query = self.supabase.table('tasks').select('*').eq('id', task_id)
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.execute()
            
            if not result.data:
                return None
            
            return Task(**result.data[0])
            
        except Exception as e:
            logger.error(f"获取任务失败: {str(e)}")
            return None
    
    async def update_task(self, task_id: str, update_data: TaskUpdate, user_id: Optional[str] = None) -> Optional[Task]:
        """
        更新任务
        """
        try:
            # 检查任务是否存在
            task = await self.get_task(task_id, user_id)
            if not task:
                return None
            
            # 检查任务状态是否允许更新
            if task.status in ['running', 'completed']:
                raise Exception("任务正在运行或已完成，无法更新")
            
            # 准备更新数据
            update_dict = {'updated_at': datetime.utcnow().isoformat()}
            
            if update_data.title is not None:
                update_dict['title'] = update_data.title
            if update_data.description is not None:
                update_dict['description'] = update_data.description
            if update_data.priority is not None:
                update_dict['priority'] = update_data.priority
            if update_data.config is not None:
                update_dict['config'] = update_data.config
            
            # 更新数据库
            query = self.supabase.table('tasks').update(update_dict).eq('id', task_id)
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.execute()
            
            if not result.data:
                return None
            
            return Task(**result.data[0])
            
        except Exception as e:
            logger.error(f"更新任务失败: {str(e)}")
            raise
    
    async def cancel_task(self, task_id: str, user_id: Optional[str] = None) -> bool:
        """
        取消任务
        """
        try:
            # 检查任务是否存在
            task = await self.get_task(task_id, user_id)
            if not task:
                return False
            
            # 检查任务状态
            if task.status in ['completed', 'failed', 'cancelled']:
                return False
            
            # 如果任务正在运行，停止执行
            if task_id in self._running_tasks:
                self._running_tasks[task_id].cancel()
                del self._running_tasks[task_id]
            
            # 更新任务状态
            query = self.supabase.table('tasks').update({
                'status': 'cancelled',
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', task_id)
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.execute()
            
            logger.info(f"任务取消成功: {task_id}")
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"取消任务失败: {str(e)}")
            return False
    
    async def delete_task(self, task_id: str, user_id: Optional[str] = None) -> bool:
        """
        删除任务
        """
        try:
            # 检查任务是否存在
            task = await self.get_task(task_id, user_id)
            if not task:
                return False
            
            # 检查任务状态
            if task.status == 'running':
                raise Exception("正在运行的任务无法删除")
            
            # 删除任务
            query = self.supabase.table('tasks').delete().eq('id', task_id)
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.execute()
            
            logger.info(f"任务删除成功: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除任务失败: {str(e)}")
            raise
    
    async def _schedule_task(self, task: Task):
        """
        调度任务执行
        """
        try:
            logger.info(f"开始调度任务: {task.id}")
            
            # 查找可用的GPU服务器
            available_server = await self.gpu_service.find_available_server()
            
            if not available_server:
                # 没有可用服务器，任务保持pending状态
                logger.warning(f"没有可用的GPU服务器，任务 {task.id} 保持等待状态")
                return
            
            # 更新任务状态为运行中
            await self._update_task_status(task.id, 'running', {
                'gpu_server_id': available_server.id,
                'started_at': datetime.utcnow().isoformat()
            })
            
            # 创建任务执行协程
            execution_task = asyncio.create_task(
                self._execute_task(task, available_server)
            )
            
            self._running_tasks[task.id] = execution_task
            
            # 等待任务完成
            await execution_task
            
        except asyncio.CancelledError:
            logger.info(f"任务被取消: {task.id}")
        except Exception as e:
            logger.error(f"调度任务失败: {task.id}, 错误: {str(e)}")
            await self._update_task_status(task.id, 'failed', {
                'error_message': str(e),
                'completed_at': datetime.utcnow().isoformat()
            })
        finally:
            # 清理运行中的任务记录
            if task.id in self._running_tasks:
                del self._running_tasks[task.id]
    
    async def _execute_task(self, task: Task, server):
        """
        执行任务
        """
        try:
            logger.info(f"开始执行任务: {task.id} 在服务器: {server.name}")
            
            # 根据任务类型执行不同的逻辑
            if task.task_type == 'training':
                await self._execute_training_task(task, server)
            elif task.task_type == 'inference':
                await self._execute_inference_task(task, server)
            elif task.task_type == 'data_processing':
                await self._execute_data_processing_task(task, server)
            else:
                raise Exception(f"不支持的任务类型: {task.task_type}")
            
            # 任务完成
            await self._update_task_status(task.id, 'completed', {
                'progress': 100.0,
                'completed_at': datetime.utcnow().isoformat()
            })
            
            logger.info(f"任务执行完成: {task.id}")
            
        except Exception as e:
            logger.error(f"执行任务失败: {task.id}, 错误: {str(e)}")
            await self._update_task_status(task.id, 'failed', {
                'error_message': str(e),
                'completed_at': datetime.utcnow().isoformat()
            })
            raise
    
    async def _execute_training_task(self, task: Task, server):
        """
        执行训练任务
        """
        # 模拟训练过程
        total_steps = 100
        
        for step in range(total_steps):
            # 检查任务是否被取消
            if task.id not in self._running_tasks:
                raise asyncio.CancelledError()
            
            # 模拟训练步骤
            await asyncio.sleep(0.1)  # 模拟处理时间
            
            # 更新进度
            progress = (step + 1) / total_steps * 100
            await self._update_task_progress(task.id, progress)
            
            logger.debug(f"任务 {task.id} 训练进度: {progress:.1f}%")
    
    async def _execute_inference_task(self, task: Task, server):
        """
        执行推理任务
        """
        # 模拟推理过程
        total_batches = 50
        
        for batch in range(total_batches):
            # 检查任务是否被取消
            if task.id not in self._running_tasks:
                raise asyncio.CancelledError()
            
            # 模拟推理步骤
            await asyncio.sleep(0.05)  # 模拟处理时间
            
            # 更新进度
            progress = (batch + 1) / total_batches * 100
            await self._update_task_progress(task.id, progress)
            
            logger.debug(f"任务 {task.id} 推理进度: {progress:.1f}%")
    
    async def _execute_data_processing_task(self, task: Task, server):
        """
        执行数据处理任务
        """
        # 模拟数据处理过程
        total_files = 20
        
        for file_idx in range(total_files):
            # 检查任务是否被取消
            if task.id not in self._running_tasks:
                raise asyncio.CancelledError()
            
            # 模拟文件处理
            await asyncio.sleep(0.2)  # 模拟处理时间
            
            # 更新进度
            progress = (file_idx + 1) / total_files * 100
            await self._update_task_progress(task.id, progress)
            
            logger.debug(f"任务 {task.id} 数据处理进度: {progress:.1f}%")
    
    async def _update_task_status(self, task_id: str, status: str, extra_data: Dict[str, Any] = None):
        """
        更新任务状态
        """
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if extra_data:
                update_data.update(extra_data)
            
            self.supabase.table('tasks').update(update_data).eq('id', task_id).execute()
            
        except Exception as e:
            logger.error(f"更新任务状态失败: {task_id}, 错误: {str(e)}")
    
    async def _update_task_progress(self, task_id: str, progress: float):
        """
        更新任务进度
        """
        try:
            self.supabase.table('tasks').update({
                'progress': progress,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', task_id).execute()
            
        except Exception as e:
            logger.error(f"更新任务进度失败: {task_id}, 错误: {str(e)}")
    
    async def get_running_tasks(self) -> List[str]:
        """
        获取正在运行的任务ID列表
        """
        return list(self._running_tasks.keys())
    
    async def stop_all_tasks(self):
        """
        停止所有正在运行的任务
        """
        logger.info("停止所有正在运行的任务")
        
        for task_id, task_coroutine in self._running_tasks.items():
            task_coroutine.cancel()
            logger.info(f"任务已停止: {task_id}")
        
        self._running_tasks.clear()