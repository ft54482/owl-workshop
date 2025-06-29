import React from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  Users,
  Server,
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { dashboardService } from '../services/dashboardService'
import LoadingSpinner from '../components/LoadingSpinner'
import { cn } from '../lib/utils'

const DashboardPage: React.FC = () => {
  const { user } = useAuth()

  // 获取用户统计数据
  const { data: userStats, isLoading: userStatsLoading } = useQuery({
    queryKey: ['userStats'],
    queryFn: dashboardService.getUserStats,
  })

  // 获取系统统计数据（管理员）
  const { data: systemStats, isLoading: systemStatsLoading } = useQuery({
    queryKey: ['systemStats'],
    queryFn: dashboardService.getSystemStats,
    enabled: user?.role === 'admin' || user?.role === 'super_admin',
  })

  // 获取GPU集群概览
  const { data: gpuOverview, isLoading: gpuOverviewLoading } = useQuery({
    queryKey: ['gpuOverview'],
    queryFn: dashboardService.getGPUOverview,
    refetchInterval: 30000, // 30秒刷新一次
  })

  // 获取最近任务
  const { data: recentTasks, isLoading: recentTasksLoading } = useQuery({
    queryKey: ['recentTasks'],
    queryFn: () => dashboardService.getRecentTasks(5),
  })

  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin'

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">仪表板</h1>
        <p className="mt-1 text-sm text-gray-600">
          欢迎回来，{user?.full_name || user?.username}！
        </p>
      </div>

      {/* 用户统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="账户余额"
          value={`¥${user?.balance?.toFixed(2) || '0.00'}`}
          icon={TrendingUp}
          color="green"
          loading={false}
        />
        <StatCard
          title="总任务数"
          value={userStats?.total_tasks?.toString() || '0'}
          icon={Activity}
          color="blue"
          loading={userStatsLoading}
        />
        <StatCard
          title="已完成"
          value={userStats?.completed_tasks?.toString() || '0'}
          icon={CheckCircle}
          color="green"
          loading={userStatsLoading}
        />
        <StatCard
          title="总花费"
          value={`¥${userStats?.total_cost?.toFixed(2) || '0.00'}`}
          icon={TrendingUp}
          color="purple"
          loading={userStatsLoading}
        />
      </div>

      {/* 管理员统计卡片 */}
      {isAdmin && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">系统概览</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="总用户数"
              value={systemStats?.total_users?.toString() || '0'}
              icon={Users}
              color="blue"
              loading={systemStatsLoading}
            />
            <StatCard
              title="活跃用户"
              value={systemStats?.active_users?.toString() || '0'}
              icon={Activity}
              color="green"
              loading={systemStatsLoading}
            />
            <StatCard
              title="运行任务"
              value={systemStats?.running_tasks?.toString() || '0'}
              icon={Clock}
              color="orange"
              loading={systemStatsLoading}
            />
            <StatCard
              title="总收入"
              value={`¥${systemStats?.total_revenue?.toFixed(2) || '0.00'}`}
              icon={TrendingUp}
              color="purple"
              loading={systemStatsLoading}
            />
          </div>
        </div>
      )}

      {/* GPU集群状态 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">GPU集群状态</h2>
        {gpuOverviewLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        ) : gpuOverview ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <Server className="w-8 h-8 text-blue-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-blue-600">
                {gpuOverview.online_servers}/{gpuOverview.total_servers}
              </div>
              <div className="text-sm text-gray-600">在线服务器</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <Activity className="w-8 h-8 text-green-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-green-600">
                {gpuOverview.idle_gpus}/{gpuOverview.total_gpus}
              </div>
              <div className="text-sm text-gray-600">空闲GPU</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <Clock className="w-8 h-8 text-orange-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-orange-600">
                {gpuOverview.total_running_tasks}
              </div>
              <div className="text-sm text-gray-600">运行任务</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <TrendingUp className="w-8 h-8 text-purple-600 mx-auto mb-2" />
              <div className="text-2xl font-bold text-purple-600">
                {gpuOverview.average_gpu_usage?.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">平均使用率</div>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <AlertCircle className="w-12 h-12 mx-auto mb-2" />
            <p>无法获取GPU集群状态</p>
          </div>
        )}
      </div>

      {/* 最近任务 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">最近任务</h2>
        {recentTasksLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        ) : recentTasks && recentTasks.length > 0 ? (
          <div className="space-y-3">
            {recentTasks.map((task) => (
              <div
                key={task.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <TaskStatusIcon status={task.status} />
                  <div>
                    <p className="font-medium text-gray-900">{task.title}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(task.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">
                    {task.status === 'running' && `${task.progress?.toFixed(1)}%`}
                    {task.status === 'completed' && '已完成'}
                    {task.status === 'failed' && '失败'}
                    {task.status === 'pending' && '等待中'}
                  </p>
                  {task.cost && (
                    <p className="text-sm text-gray-500">¥{task.cost.toFixed(2)}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Activity className="w-12 h-12 mx-auto mb-2" />
            <p>暂无任务记录</p>
          </div>
        )}
      </div>
    </div>
  )
}

// 统计卡片组件
interface StatCardProps {
  title: string
  value: string
  icon: React.ComponentType<{ className?: string }>
  color: 'blue' | 'green' | 'orange' | 'purple'
  loading: boolean
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon: Icon, color, loading }) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    orange: 'bg-orange-50 text-orange-600',
    purple: 'bg-purple-50 text-purple-600',
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className={cn('p-2 rounded-lg', colorClasses[color])}>
          <Icon className="w-6 h-6" />
        </div>
        <div className="ml-4 flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          {loading ? (
            <LoadingSpinner size="sm" className="mt-1" />
          ) : (
            <p className="text-2xl font-bold text-gray-900">{value}</p>
          )}
        </div>
      </div>
    </div>
  )
}

// 任务状态图标组件
const TaskStatusIcon: React.FC<{ status: string }> = ({ status }) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-5 h-5 text-green-500" />
    case 'failed':
      return <XCircle className="w-5 h-5 text-red-500" />
    case 'running':
      return <Clock className="w-5 h-5 text-blue-500" />
    default:
      return <AlertCircle className="w-5 h-5 text-gray-400" />
  }
}

export default DashboardPage