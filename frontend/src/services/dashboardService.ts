import axios from 'axios'
import { UserStats, SystemStats, GPUOverview, Task } from '../types/dashboard'

class DashboardService {
  async getUserStats(): Promise<UserStats> {
    const response = await axios.get('/api/users/stats')
    return response.data.data
  }

  async getSystemStats(): Promise<SystemStats> {
    const response = await axios.get('/api/admin/stats')
    return response.data.data
  }

  async getGPUOverview(): Promise<GPUOverview> {
    const response = await axios.get('/api/gpu/cluster/overview')
    return response.data.data
  }

  async getRecentTasks(limit: number = 10): Promise<Task[]> {
    const response = await axios.get(`/api/tasks?page=1&page_size=${limit}&sort_by=created_at&sort_order=desc`)
    return response.data.items
  }
}

export const dashboardService = new DashboardService()