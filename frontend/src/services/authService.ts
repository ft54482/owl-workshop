import axios from 'axios'
import { User, LoginResponse, RegisterRequest } from '../types/auth'

class AuthService {
  private baseURL = '/api/auth'
  private token: string | null = null

  constructor() {
    // 从localStorage获取token
    this.token = localStorage.getItem('token')
    if (this.token) {
      this.setAuthHeader()
    }
  }

  setToken(token: string | null) {
    this.token = token
    if (token) {
      localStorage.setItem('token', token)
      this.setAuthHeader()
    } else {
      localStorage.removeItem('token')
      delete axios.defaults.headers.common['Authorization']
    }
  }

  private setAuthHeader() {
    if (this.token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
    }
  }

  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await axios.post(`${this.baseURL}/login`, {
      email,
      password,
    })
    return response.data.data
  }

  async register(email: string, username: string, password: string, fullName?: string): Promise<void> {
    const registerData: RegisterRequest = {
      email,
      username,
      password,
    }
    
    if (fullName) {
      registerData.full_name = fullName
    }

    await axios.post(`${this.baseURL}/register`, registerData)
  }

  async getCurrentUser(): Promise<User> {
    const response = await axios.get('/api/users/me')
    return response.data.data
  }

  async updateProfile(userData: Partial<User>): Promise<User> {
    const response = await axios.put('/api/users/me', userData)
    return response.data.data
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await axios.post('/api/users/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
  }

  logout() {
    this.setToken(null)
  }
}

export const authService = new AuthService()