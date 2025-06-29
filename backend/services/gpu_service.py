import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import paramiko
import psutil

from ..models.database_models import GPUServer
from ..config.supabase_config import get_supabase_manager

logger = logging.getLogger(__name__)

class GPUService:
    """
    GPU服务管理类
    """
    
    def __init__(self):
        self.supabase = get_supabase_manager().get_client()
    
    async def find_available_server(self) -> Optional[GPUServer]:
        """
        查找可用的GPU服务器
        """
        try:
            # 获取所有活跃的GPU服务器
            result = self.supabase.table('gpu_servers').select('*').eq('is_active', True).execute()
            
            if not result.data:
                logger.warning("没有可用的GPU服务器")
                return None
            
            servers = [GPUServer(**server_data) for server_data in result.data]
            
            # 检查每个服务器的可用性
            for server in servers:
                if await self._check_server_availability(server):
                    logger.info(f"找到可用服务器: {server.name}")
                    return server
            
            logger.warning("所有GPU服务器都不可用")
            return None
            
        except Exception as e:
            logger.error(f"查找可用服务器失败: {str(e)}")
            return None
    
    async def _check_server_availability(self, server: GPUServer) -> bool:
        """
        检查服务器可用性
        """
        try:
            # 检查服务器上正在运行的任务数量
            running_tasks = self.supabase.table('tasks').select('id').eq('gpu_server_id', server.id).eq('status', 'running').execute()
            
            # 简单的负载均衡：如果正在运行的任务数量小于GPU数量，则认为可用
            if len(running_tasks.data) < server.gpu_count:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"检查服务器可用性失败: {server.name}, 错误: {str(e)}")
            return False
    
    async def get_server_stats(self, server_id: str) -> Optional[Dict[str, Any]]:
        """
        获取服务器统计信息
        """
        try:
            # 获取服务器信息
            server_result = self.supabase.table('gpu_servers').select('*').eq('id', server_id).execute()
            
            if not server_result.data:
                return None
            
            server = GPUServer(**server_result.data[0])
            
            # 获取服务器上的任务统计
            tasks_result = self.supabase.table('tasks').select('status').eq('gpu_server_id', server_id).execute()
            tasks = tasks_result.data
            
            running_tasks = len([t for t in tasks if t['status'] == 'running'])
            completed_tasks = len([t for t in tasks if t['status'] == 'completed'])
            failed_tasks = len([t for t in tasks if t['status'] == 'failed'])
            
            # 计算GPU使用率
            gpu_utilization = (running_tasks / server.gpu_count * 100) if server.gpu_count > 0 else 0
            
            stats = {
                'server_id': server_id,
                'server_name': server.name,
                'gpu_count': server.gpu_count,
                'gpu_model': server.gpu_model,
                'memory_total': server.memory_total,
                'running_tasks': running_tasks,
                'completed_tasks': completed_tasks,
                'failed_tasks': failed_tasks,
                'gpu_utilization': round(gpu_utilization, 2),
                'status': server.status,
                'last_ping': server.last_ping
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取服务器统计失败: {server_id}, 错误: {str(e)}")
            return None
    
    async def ping_server(self, server_id: str) -> bool:
        """
        Ping服务器检查连接状态
        """
        try:
            # 获取服务器信息
            server_result = self.supabase.table('gpu_servers').select('*').eq('id', server_id).execute()
            
            if not server_result.data:
                return False
            
            server = GPUServer(**server_result.data[0])
            
            # 尝试SSH连接
            connection_success = await self._test_ssh_connection(server)
            
            # 更新服务器状态
            status = 'online' if connection_success else 'offline'
            update_data = {
                'status': status,
                'last_ping': datetime.utcnow().isoformat()
            }
            
            self.supabase.table('gpu_servers').update(update_data).eq('id', server_id).execute()
            
            return connection_success
            
        except Exception as e:
            logger.error(f"Ping服务器失败: {server_id}, 错误: {str(e)}")
            return False
    
    async def _test_ssh_connection(self, server: GPUServer) -> bool:
        """
        测试SSH连接
        """
        try:
            # 创建SSH客户端
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 尝试连接（这里需要配置SSH密钥或密码）
            # 注意：在生产环境中应该使用密钥认证
            ssh.connect(
                hostname=server.host,
                port=server.port,
                username=server.username,
                timeout=10
            )
            
            # 执行简单命令测试
            stdin, stdout, stderr = ssh.exec_command('echo "test"')
            output = stdout.read().decode().strip()
            
            ssh.close()
            
            return output == 'test'
            
        except Exception as e:
            logger.debug(f"SSH连接测试失败: {server.host}:{server.port}, 错误: {str(e)}")
            return False
    
    async def get_gpu_info(self, server_id: str) -> Optional[Dict[str, Any]]:
        """
        获取GPU信息
        """
        try:
            # 获取服务器信息
            server_result = self.supabase.table('gpu_servers').select('*').eq('id', server_id).execute()
            
            if not server_result.data:
                return None
            
            server = GPUServer(**server_result.data[0])
            
            # 这里应该通过SSH连接到服务器获取实际的GPU信息
            # 目前返回模拟数据
            gpu_info = {
                'server_id': server_id,
                'gpus': []
            }
            
            for i in range(server.gpu_count):
                gpu_info['gpus'].append({
                    'id': i,
                    'name': server.gpu_model or f'GPU {i}',
                    'memory_total': server.memory_total or 8192,  # MB
                    'memory_used': 2048,  # 模拟使用的内存
                    'memory_free': (server.memory_total or 8192) - 2048,
                    'utilization': 45.5,  # 模拟GPU使用率
                    'temperature': 65,  # 模拟温度
                    'power_usage': 150,  # 模拟功耗
                    'processes': []  # 运行的进程
                })
            
            return gpu_info
            
        except Exception as e:
            logger.error(f"获取GPU信息失败: {server_id}, 错误: {str(e)}")
            return None
    
    async def monitor_all_servers(self):
        """
        监控所有服务器
        """
        try:
            # 获取所有活跃的服务器
            result = self.supabase.table('gpu_servers').select('*').eq('is_active', True).execute()
            
            if not result.data:
                logger.info("没有需要监控的服务器")
                return
            
            servers = [GPUServer(**server_data) for server_data in result.data]
            
            # 并发监控所有服务器
            tasks = [self.ping_server(server.id) for server in servers]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计结果
            online_count = sum(1 for result in results if result is True)
            total_count = len(servers)
            
            logger.info(f"服务器监控完成: {online_count}/{total_count} 在线")
            
        except Exception as e:
            logger.error(f"监控服务器失败: {str(e)}")
    
    async def get_cluster_stats(self) -> Dict[str, Any]:
        """
        获取集群统计信息
        """
        try:
            # 获取所有服务器
            servers_result = self.supabase.table('gpu_servers').select('*').execute()
            servers = servers_result.data
            
            # 获取所有任务
            tasks_result = self.supabase.table('tasks').select('status, gpu_server_id').execute()
            tasks = tasks_result.data
            
            # 计算统计信息
            total_servers = len(servers)
            active_servers = len([s for s in servers if s['is_active']])
            online_servers = len([s for s in servers if s['status'] == 'online'])
            
            total_gpus = sum(s['gpu_count'] for s in servers if s['is_active'])
            
            running_tasks = len([t for t in tasks if t['status'] == 'running'])
            pending_tasks = len([t for t in tasks if t['status'] == 'pending'])
            completed_tasks = len([t for t in tasks if t['status'] == 'completed'])
            failed_tasks = len([t for t in tasks if t['status'] == 'failed'])
            
            # 计算集群使用率
            cluster_utilization = (running_tasks / total_gpus * 100) if total_gpus > 0 else 0
            
            stats = {
                'total_servers': total_servers,
                'active_servers': active_servers,
                'online_servers': online_servers,
                'total_gpus': total_gpus,
                'running_tasks': running_tasks,
                'pending_tasks': pending_tasks,
                'completed_tasks': completed_tasks,
                'failed_tasks': failed_tasks,
                'cluster_utilization': round(cluster_utilization, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取集群统计失败: {str(e)}")
            return {}
    
    async def schedule_maintenance(self, server_id: str, maintenance_window: int = 3600):
        """
        调度服务器维护
        """
        try:
            logger.info(f"开始服务器维护: {server_id}")
            
            # 标记服务器为维护状态
            self.supabase.table('gpu_servers').update({
                'status': 'maintenance',
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', server_id).execute()
            
            # 等待维护窗口
            await asyncio.sleep(maintenance_window)
            
            # 恢复服务器状态
            self.supabase.table('gpu_servers').update({
                'status': 'online',
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', server_id).execute()
            
            logger.info(f"服务器维护完成: {server_id}")
            
        except Exception as e:
            logger.error(f"服务器维护失败: {server_id}, 错误: {str(e)}")