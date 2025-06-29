export interface User {
  id: string
  email: string
  username: string
  full_name?: string
  role: 'user' | 'admin' | 'super_admin'
  balance?: number
  total_tasks?: number
  is_active: boolean
  created_at: string
  last_login?: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
  full_name?: string
}