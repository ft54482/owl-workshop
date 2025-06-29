# -*- coding: utf-8 -*-
"""
🦉 猫头鹰工厂 - 数据库模型定义
定义所有数据库表的Pydantic模型
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from enum import Enum

class UserRole(str, Enum):
    """用户角色枚举"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"

class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class GPUStatus(str, Enum):
    """GPU状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    MAINTENANCE = "maintenance"

# 用户相关模型
class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True

class UserCreate(UserBase):
    """创建用户模型"""
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    """更新用户模型"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class User(UserBase):
    """用户完整模型"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    balance: float = 0.0
    total_tasks: int = 0
    
    class Config:
        from_attributes = True

# 任务相关模型
class TaskBase(BaseModel):
    """任务基础模型"""
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    task_type: str = Field(..., max_length=50)
    priority: int = Field(default=1, ge=1, le=5)
    estimated_duration: Optional[int] = None  # 预估时长(分钟)
    
class TaskCreate(TaskBase):
    """创建任务模型"""
    config: Optional[Dict[str, Any]] = None

class TaskUpdate(BaseModel):
    """更新任务模型"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    progress: Optional[float] = Field(None, ge=0, le=100)
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class Task(TaskBase):
    """任务完整模型"""
    id: str
    user_id: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    gpu_server_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    cost: float = 0.0
    
    class Config:
        from_attributes = True

# GPU服务器相关模型
class GPUServerBase(BaseModel):
    """GPU服务器基础模型"""
    name: str = Field(..., max_length=100)
    host: str
    port: int = Field(default=22, ge=1, le=65535)
    username: str
    description: Optional[str] = None
    max_concurrent_tasks: int = Field(default=1, ge=1)
    
class GPUServerCreate(GPUServerBase):
    """创建GPU服务器模型"""
    ssh_key_path: Optional[str] = None
    password: Optional[str] = None

class GPUServerUpdate(BaseModel):
    """更新GPU服务器模型"""
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    description: Optional[str] = None
    status: Optional[GPUStatus] = None
    max_concurrent_tasks: Optional[int] = None
    is_active: Optional[bool] = None

class GPUServer(GPUServerBase):
    """GPU服务器完整模型"""
    id: str
    status: GPUStatus = GPUStatus.OFFLINE
    is_active: bool = True
    current_tasks: int = 0
    total_memory: Optional[float] = None  # GB
    used_memory: Optional[float] = None   # GB
    gpu_count: Optional[int] = None
    cpu_usage: Optional[float] = None     # %
    memory_usage: Optional[float] = None  # %
    last_heartbeat: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# 充值码相关模型
class RechargeCodeBase(BaseModel):
    """充值码基础模型"""
    amount: float = Field(..., gt=0)
    description: Optional[str] = None
    expires_at: Optional[datetime] = None
    max_uses: int = Field(default=1, ge=1)
    
class RechargeCodeCreate(RechargeCodeBase):
    """创建充值码模型"""
    batch_size: int = Field(default=1, ge=1, le=1000)

class RechargeCode(RechargeCodeBase):
    """充值码完整模型"""
    id: str
    code: str
    created_by: str
    used_count: int = 0
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# 充值记录模型
class RechargeRecord(BaseModel):
    """充值记录模型"""
    id: str
    user_id: str
    recharge_code_id: str
    amount: float
    created_at: datetime
    
    class Config:
        from_attributes = True

# API响应模型
class APIResponse(BaseModel):
    """API统一响应模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None
    error_code: Optional[str] = None

class PaginatedResponse(BaseModel):
    """分页响应模型"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

# 认证相关模型
class Token(BaseModel):
    """令牌模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User

class LoginRequest(BaseModel):
    """登录请求模型"""
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    """注册请求模型"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None

# 统计数据模型
class SystemStats(BaseModel):
    """系统统计模型"""
    total_users: int
    active_users: int
    total_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_gpu_servers: int
    online_gpu_servers: int
    total_revenue: float
    
class UserStats(BaseModel):
    """用户统计模型"""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_cost: float
    current_balance: float
    last_task_date: Optional[datetime] = None