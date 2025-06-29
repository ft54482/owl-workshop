import React, { createContext, useContext, useEffect, useState } from 'react'
import { User } from '../types/auth'
import { authService } from '../services/authService'
import toast from 'react-hot-toast'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string, fullName?: string) => Promise<void>
  logout: () => void
  updateUser: (userData: Partial<User>) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: React.ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = localStorage.getItem('token')
        if (token) {
          authService.setToken(token)
          const userData = await authService.getCurrentUser()
          setUser(userData)
        }
      } catch (error) {
        console.error('Auth initialization failed:', error)
        localStorage.removeItem('token')
        authService.setToken(null)
      } finally {
        setLoading(false)
      }
    }

    initAuth()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      const response = await authService.login(email, password)
      const { access_token, user: userData } = response
      
      localStorage.setItem('token', access_token)
      authService.setToken(access_token)
      setUser(userData)
      
      toast.success('登录成功！')
    } catch (error: any) {
      const message = error.response?.data?.message || '登录失败，请检查邮箱和密码'
      toast.error(message)
      throw error
    }
  }

  const register = async (email: string, username: string, password: string, fullName?: string) => {
    try {
      await authService.register(email, username, password, fullName)
      toast.success('注册成功！请登录')
    } catch (error: any) {
      const message = error.response?.data?.message || '注册失败，请重试'
      toast.error(message)
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    authService.setToken(null)
    setUser(null)
    toast.success('已退出登录')
  }

  const updateUser = (userData: Partial<User>) => {
    if (user) {
      setUser({ ...user, ...userData })
    }
  }

  const value: AuthContextType = {
    user,
    loading,
    login,
    register,
    logout,
    updateUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}