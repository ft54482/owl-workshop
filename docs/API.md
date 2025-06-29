# 🔌 猫头鹰工厂 API 文档

## 📋 目录
- [API概述](#api概述)
- [认证机制](#认证机制)
- [用户管理API](#用户管理api)
- [任务管理API](#任务管理api)
- [GPU监控API](#gpu监控api)
- [充值管理API](#充值管理api)
- [系统管理API](#系统管理api)
- [日志管理API](#日志管理api)
- [错误处理](#错误处理)
- [API测试](#api测试)

## 🌐 API概述

### 基础信息
- **基础URL**: `http://localhost:8000/api`
- **版本**: v0.10.0
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **字符编码**: UTF-8

### 通用响应格式
```json
{
  "success": true,
  "message": "操作成功",
  "data": {},
  "error_code": null
}
```

### 分页响应格式
```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

## 🔐 认证机制

### JWT Token认证
所有需要认证的API都需要在请求头中包含JWT Token：

```http
Authorization: Bearer <your_jwt_token>
```

### 获取Token
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "username": "username",
      "role": "user"
    }
  }
}
```

## 👤 用户管理API

### 用户注册
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "newuser@example.com",
  "username": "newuser",
  "password": "password123",
  "full_name": "新用户"
}
```

### 获取当前用户信息
```http
GET /api/users/me
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "username",
    "full_name": "用户姓名",
    "role": "user",
    "balance": 100.50,
    "total_tasks": 25,
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-15T10:30:00Z"
  }
}
```

### 更新用户信息
```http
PUT /api/users/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "新的姓名",
  "username": "new_username"
}
```

### 修改密码
```http
POST /api/users/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "old_password",
  "new_password": "new_password"
}
```

### 获取用户统计信息
```http
GET /api/users/stats
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total_tasks": 25,
    "completed_tasks": 20,
    "failed_tasks": 2,
    "total_cost": 150.75,
    "current_balance": 100.50,
    "last_task_date": "2024-01-15T10:30:00Z"
  }
}
```

## 📋 任务管理API

### 创建任务
```http
POST /api/tasks
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "视频分析任务",
  "description": "分析视频内容",
  "task_type": "video_analysis",
  "priority": 2,
  "estimated_duration": 30,
  "config": {
    "video_url": "https://example.com/video.mp4",
    "analysis_type": "content"
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "task_uuid",
    "title": "视频分析任务",
    "status": "pending",
    "progress": 0.0,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### 获取任务列表
```http
GET /api/tasks?page=1&page_size=20&status=running
Authorization: Bearer <token>
```

**查询参数**:
- `page`: 页码 (默认: 1)
- `page_size`: 每页数量 (默认: 20)
- `status`: 任务状态过滤
- `task_type`: 任务类型过滤
- `sort_by`: 排序字段 (created_at, updated_at, priority)
- `sort_order`: 排序方向 (asc, desc)

### 获取任务详情
```http
GET /api/tasks/{task_id}
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "task_uuid",
    "title": "视频分析任务",
    "description": "分析视频内容",
    "task_type": "video_analysis",
    "status": "running",
    "progress": 45.5,
    "priority": 2,
    "gpu_server_id": "server_uuid",
    "config": {},
    "result": {},
    "error_message": null,
    "cost": 5.25,
    "estimated_duration": 30,
    "started_at": "2024-01-15T10:35:00Z",
    "completed_at": null,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:40:00Z"
  }
}
```

### 取消任务
```http
POST /api/tasks/{task_id}/cancel
Authorization: Bearer <token>
```

### 重新运行任务
```http
POST /api/tasks/{task_id}/retry
Authorization: Bearer <token>
```

### 删除任务
```http
DELETE /api/tasks/{task_id}
Authorization: Bearer <token>
```

## 🖥️ GPU监控API

### 获取GPU服务器列表
```http
GET /api/gpu/servers
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": "server_uuid",
      "name": "GPU-Server-01",
      "host": "192.168.1.100",
      "status": "online",
      "current_tasks": 2,
      "max_concurrent_tasks": 4,
      "total_memory": 24.0,
      "used_memory": 12.5,
      "gpu_count": 2,
      "cpu_usage": 45.2,
      "memory_usage": 68.3,
      "last_heartbeat": "2024-01-15T10:45:00Z"
    }
  ]
}
```

### 获取GPU服务器详情
```http
GET /api/gpu/servers/{server_id}
Authorization: Bearer <token>
```

### 获取GPU服务器实时状态
```http
GET /api/gpu/servers/{server_id}/status
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": {
    "server_id": "server_uuid",
    "status": "online",
    "cpu_usage": 45.2,
    "memory_usage": 68.3,
    "gpu_usage": [
      {"gpu_id": 0, "usage": 85.5, "memory_used": 10.2, "memory_total": 12.0},
      {"gpu_id": 1, "usage": 92.1, "memory_used": 11.8, "memory_total": 12.0}
    ],
    "running_tasks": [
      {"task_id": "task_uuid", "progress": 45.5}
    ],
    "timestamp": "2024-01-15T10:45:00Z"
  }
}
```

### 获取GPU集群概览
```http
GET /api/gpu/cluster/overview
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total_servers": 3,
    "online_servers": 2,
    "offline_servers": 1,
    "total_gpus": 6,
    "busy_gpus": 4,
    "idle_gpus": 2,
    "total_running_tasks": 5,
    "queue_length": 3,
    "average_gpu_usage": 78.5,
    "total_memory": 72.0,
    "used_memory": 45.2
  }
}
```

## 💰 充值管理API

### 生成充值码
```http
POST /api/recharge/codes
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "amount": 100.0,
  "description": "新用户充值码",
  "batch_size": 10,
  "expires_at": "2024-12-31T23:59:59Z",
  "max_uses": 1
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "codes": [
      {
        "id": "code_uuid",
        "code": "OWL-ABCD-1234-EFGH",
        "amount": 100.0,
        "expires_at": "2024-12-31T23:59:59Z"
      }
    ],
    "total_generated": 10,
    "total_amount": 1000.0
  }
}
```

### 使用充值码
```http
POST /api/recharge/redeem
Authorization: Bearer <token>
Content-Type: application/json

{
  "code": "OWL-ABCD-1234-EFGH"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "amount": 100.0,
    "new_balance": 250.0,
    "recharge_record_id": "record_uuid"
  }
}
```

### 获取充值记录
```http
GET /api/recharge/records?page=1&page_size=20
Authorization: Bearer <token>
```

### 获取充值码列表 (管理员)
```http
GET /api/recharge/codes?page=1&page_size=20&status=active
Authorization: Bearer <admin_token>
```

## ⚙️ 系统管理API

### 获取系统统计信息
```http
GET /api/admin/stats
Authorization: Bearer <admin_token>
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total_users": 1250,
    "active_users": 890,
    "total_tasks": 15420,
    "running_tasks": 25,
    "completed_tasks": 14800,
    "failed_tasks": 595,
    "total_gpu_servers": 3,
    "online_gpu_servers": 2,
    "total_revenue": 25680.50
  }
}
```

### 获取用户列表 (管理员)
```http
GET /api/admin/users?page=1&page_size=20&role=user&is_active=true
Authorization: Bearer <admin_token>
```

### 更新用户信息 (管理员)
```http
PUT /api/admin/users/{user_id}
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "role": "admin",
  "is_active": false,
  "balance": 200.0
}
```

### 获取系统配置
```http
GET /api/admin/config
Authorization: Bearer <admin_token>
```

### 更新系统配置
```http
PUT /api/admin/config
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "max_concurrent_tasks_per_user": 5,
  "default_task_timeout": 3600,
  "maintenance_mode": false
}
```

## 📊 日志管理API

### 获取系统日志
```http
GET /api/logs/system?page=1&page_size=50&level=ERROR&start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer <admin_token>
```

**查询参数**:
- `level`: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `start_date`: 开始日期
- `end_date`: 结束日期
- `search`: 搜索关键词

### 获取用户操作日志
```http
GET /api/logs/user-actions?user_id={user_id}&page=1&page_size=50
Authorization: Bearer <admin_token>
```

### 获取任务执行日志
```http
GET /api/logs/tasks/{task_id}
Authorization: Bearer <token>
```

### 下载日志文件
```http
GET /api/logs/download?log_type=system&date=2024-01-15
Authorization: Bearer <admin_token>
```

## ❌ 错误处理

### 错误响应格式
```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERROR_CODE",
  "details": {}
}
```

### 常见错误码

| 错误码 | HTTP状态码 | 描述 |
|--------|------------|------|
| `INVALID_CREDENTIALS` | 401 | 无效的认证凭据 |
| `ACCESS_DENIED` | 403 | 访问被拒绝 |
| `RESOURCE_NOT_FOUND` | 404 | 资源不存在 |
| `VALIDATION_ERROR` | 422 | 请求参数验证失败 |
| `INSUFFICIENT_BALANCE` | 400 | 余额不足 |
| `TASK_LIMIT_EXCEEDED` | 429 | 任务数量超限 |
| `SERVER_UNAVAILABLE` | 503 | 服务器不可用 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

### 参数验证错误示例
```json
{
  "success": false,
  "message": "请求参数验证失败",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field_errors": {
      "email": ["邮箱格式不正确"],
      "password": ["密码长度至少6位"]
    }
  }
}
```

## 🧪 API测试

### 使用curl测试

#### 登录获取Token
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123"
  }'
```

#### 获取用户信息
```bash
curl -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

#### 创建任务
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试任务",
    "task_type": "test",
    "description": "这是一个测试任务"
  }'
```

### 使用Python测试

```python
import requests
import json

# 基础URL
BASE_URL = "http://localhost:8000/api"

# 登录获取token
def login(email, password):
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        return response.json()["data"]["access_token"]
    else:
        raise Exception(f"登录失败: {response.text}")

# 创建认证头
def get_headers(token):
    return {"Authorization": f"Bearer {token}"}

# 获取用户信息
def get_user_info(token):
    response = requests.get(
        f"{BASE_URL}/users/me",
        headers=get_headers(token)
    )
    return response.json()

# 创建任务
def create_task(token, title, task_type, description=""):
    response = requests.post(
        f"{BASE_URL}/tasks",
        headers=get_headers(token),
        json={
            "title": title,
            "task_type": task_type,
            "description": description
        }
    )
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 登录
    token = login("admin@example.com", "admin123")
    print(f"Token: {token}")
    
    # 获取用户信息
    user_info = get_user_info(token)
    print(f"用户信息: {json.dumps(user_info, indent=2, ensure_ascii=False)}")
    
    # 创建任务
    task = create_task(token, "测试任务", "test", "API测试任务")
    print(f"创建任务: {json.dumps(task, indent=2, ensure_ascii=False)}")
```

### Postman集合

可以导入以下Postman集合来快速测试API：

```json
{
  "info": {
    "name": "猫头鹰工厂 API",
    "description": "猫头鹰工厂后台管理系统API测试集合",
    "version": "0.10.0"
  },
  "variable": [
    {
      "key": "baseUrl",
      "value": "http://localhost:8000/api"
    },
    {
      "key": "token",
      "value": ""
    }
  ],
  "item": [
    {
      "name": "认证",
      "item": [
        {
          "name": "登录",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"admin@example.com\",\n  \"password\": \"admin123\"\n}"
            },
            "url": {
              "raw": "{{baseUrl}}/auth/login",
              "host": ["{{baseUrl}}"],
              "path": ["auth", "login"]
            }
          }
        }
      ]
    }
  ]
}
```

---

**版本**: v0.10.0  
**更新时间**: 2024年12月  
**维护团队**: 猫头鹰工厂开发团队