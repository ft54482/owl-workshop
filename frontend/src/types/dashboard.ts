export interface UserStats {
  total_tasks: number
  completed_tasks: number
  failed_tasks: number
  total_cost: number
  current_balance: number
  last_task_date?: string
}

export interface SystemStats {
  total_users: number
  active_users: number
  total_tasks: number
  running_tasks: number
  completed_tasks: number
  failed_tasks: number
  total_gpu_servers: number
  online_gpu_servers: number
  total_revenue: number
}

export interface GPUOverview {
  total_servers: number
  online_servers: number
  offline_servers: number
  total_gpus: number
  busy_gpus: number
  idle_gpus: number
  total_running_tasks: number
  queue_length: number
  average_gpu_usage: number
  total_memory: number
  used_memory: number
}

export interface Task {
  id: string
  title: string
  description?: string
  task_type: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress?: number
  priority: number
  gpu_server_id?: string
  config: Record<string, any>
  result?: Record<string, any>
  error_message?: string
  cost?: number
  estimated_duration?: number
  started_at?: string
  completed_at?: string
  created_at: string
  updated_at: string
}