# 🚀 猫头鹰工厂部署指南

## 📋 目录
- [系统要求](#系统要求)
- [环境准备](#环境准备)
- [后端部署](#后端部署)
- [前端部署](#前端部署)
- [数据库配置](#数据库配置)
- [GPU集群配置](#gpu集群配置)
- [生产环境部署](#生产环境部署)
- [监控和维护](#监控和维护)
- [故障排除](#故障排除)

## 🔧 系统要求

### 最低配置
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Windows 10+
- **CPU**: 4核心
- **内存**: 8GB RAM
- **存储**: 50GB 可用空间
- **网络**: 稳定的互联网连接

### 推荐配置
- **操作系统**: Ubuntu 22.04 LTS
- **CPU**: 8核心或更多
- **内存**: 16GB RAM 或更多
- **存储**: 100GB SSD
- **网络**: 千兆网络

### 软件依赖
- **Python**: 3.9+
- **Node.js**: 18+
- **Conda**: 最新版本
- **Git**: 2.0+
- **Docker**: 20.10+ (可选)

## 🌍 环境准备

### 1. 克隆项目
```bash
git clone https://github.com/ft54482/owl-workshop.git
cd owl-workshop
```

### 2. 安装Conda环境
```bash
# 创建Conda环境
conda env create -f environment.yml

# 激活环境
conda activate maotouying-factory
```

### 3. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

## 🔙 后端部署

### 1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置Supabase
1. 访问 [Supabase](https://supabase.com) 创建项目
2. 获取项目URL和API密钥
3. 在 `.env` 文件中配置:
```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
```

### 3. 初始化数据库
```bash
# 运行数据库初始化脚本
python scripts/setup_database.py

# 创建超级管理员账户
python scripts/init_super_admin.py
```

### 4. 启动后端服务
```bash
# 开发环境
python main.py

# 或使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. 验证后端服务
```bash
# 检查健康状态
curl http://localhost:8000/health

# 访问API文档
# http://localhost:8000/docs
```

## 🎨 前端部署

### 1. 安装依赖
```bash
cd frontend
npm install
```

### 2. 配置环境变量
```bash
# 创建前端环境配置
cp .env.example .env

# 编辑配置
nano .env
```

### 3. 启动开发服务器
```bash
# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

### 4. 验证前端服务
- 访问: http://localhost:3000
- 检查所有页面是否正常加载
- 测试登录功能

## 🗄️ 数据库配置

### Supabase表结构

#### 用户表 (users)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR UNIQUE NOT NULL,
    username VARCHAR UNIQUE NOT NULL,
    full_name VARCHAR,
    role VARCHAR DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    balance DECIMAL DEFAULT 0.0,
    total_tasks INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    last_login TIMESTAMP
);
```

#### 任务表 (tasks)
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    title VARCHAR NOT NULL,
    description TEXT,
    task_type VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'pending',
    priority INTEGER DEFAULT 1,
    progress DECIMAL DEFAULT 0.0,
    gpu_server_id UUID,
    config JSONB,
    result JSONB,
    error_message TEXT,
    cost DECIMAL DEFAULT 0.0,
    estimated_duration INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

#### GPU服务器表 (gpu_servers)
```sql
CREATE TABLE gpu_servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    host VARCHAR NOT NULL,
    port INTEGER DEFAULT 22,
    username VARCHAR NOT NULL,
    description TEXT,
    status VARCHAR DEFAULT 'offline',
    is_active BOOLEAN DEFAULT true,
    max_concurrent_tasks INTEGER DEFAULT 1,
    current_tasks INTEGER DEFAULT 0,
    total_memory DECIMAL,
    used_memory DECIMAL,
    gpu_count INTEGER,
    cpu_usage DECIMAL,
    memory_usage DECIMAL,
    last_heartbeat TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

## 🖥️ GPU集群配置

### 1. 配置GPU服务器
```bash
# 在每台GPU服务器上安装必要软件
sudo apt update
sudo apt install -y python3 python3-pip nvidia-driver-535

# 安装CUDA (如需要)
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.2.0/local_installers/cuda-repo-ubuntu2204-12-2-local_12.2.0-535.54.03-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2204-12-2-local_12.2.0-535.54.03-1_amd64.deb
sudo cp /var/cuda-repo-ubuntu2204-12-2-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda
```

### 2. 配置SSH密钥认证
```bash
# 生成SSH密钥对
ssh-keygen -t rsa -b 4096 -f ~/.ssh/gpu_server_key

# 将公钥复制到GPU服务器
ssh-copy-id -i ~/.ssh/gpu_server_key.pub user@gpu-server-ip

# 测试连接
ssh -i ~/.ssh/gpu_server_key user@gpu-server-ip
```

### 3. 在环境变量中配置GPU服务器
```env
# GPU集群配置
GPU_CLUSTER_ENABLED=true
GPU_MONITOR_INTERVAL=5
GPU_MAX_CONCURRENT_TASKS=10

# Worker节点配置
WORKER_02_HOST=192.168.1.100
WORKER_02_PORT=22
WORKER_02_USER=ubuntu
WORKER_02_KEY_PATH=/path/to/gpu_server_key

WORKER_03_HOST=192.168.1.101
WORKER_03_PORT=22
WORKER_03_USER=ubuntu
WORKER_03_KEY_PATH=/path/to/gpu_server_key
```

## 🏭 生产环境部署

### 使用Docker部署

#### 1. 创建Dockerfile (后端)
```dockerfile
# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. 创建Dockerfile (前端)
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### 3. 创建docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - DEBUG=false
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

#### 4. 部署命令
```bash
# 构建和启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 使用Nginx反向代理

```nginx
# /etc/nginx/sites-available/owl-workshop
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /var/www/owl-workshop/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket支持
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 📊 监控和维护

### 1. 日志监控
```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log

# 使用logrotate管理日志
sudo nano /etc/logrotate.d/owl-workshop
```

### 2. 系统监控
```bash
# 监控系统资源
htop

# 监控磁盘使用
df -h

# 监控网络连接
netstat -tulpn
```

### 3. 数据库维护
```sql
-- 清理过期任务
DELETE FROM tasks WHERE created_at < NOW() - INTERVAL '30 days' AND status = 'completed';

-- 更新统计信息
ANALYZE;

-- 检查数据库大小
SELECT pg_size_pretty(pg_database_size('postgres'));
```

## 🔧 故障排除

### 常见问题

#### 1. 后端启动失败
```bash
# 检查Python环境
python --version
pip list

# 检查端口占用
lsof -i :8000

# 检查Supabase连接
python -c "from config.supabase_config import supabase_manager; print(supabase_manager.test_connection())"
```

#### 2. 前端构建失败
```bash
# 清理node_modules
rm -rf node_modules package-lock.json
npm install

# 检查Node.js版本
node --version
npm --version
```

#### 3. 数据库连接问题
- 检查Supabase项目状态
- 验证API密钥是否正确
- 确认网络连接正常
- 检查防火墙设置

#### 4. GPU服务器连接问题
```bash
# 测试SSH连接
ssh -i /path/to/key user@gpu-server-ip

# 检查GPU状态
nvidia-smi

# 检查服务器资源
free -h
df -h
```

### 性能优化

#### 1. 后端优化
- 使用Gunicorn多进程部署
- 配置Redis缓存
- 优化数据库查询
- 启用gzip压缩

#### 2. 前端优化
- 启用代码分割
- 配置CDN
- 优化图片资源
- 启用浏览器缓存

#### 3. 数据库优化
- 创建适当的索引
- 定期清理过期数据
- 配置连接池
- 监控查询性能

## 📞 技术支持

如果在部署过程中遇到问题，请：

1. 查看日志文件获取详细错误信息
2. 检查环境配置是否正确
3. 确认所有依赖都已正确安装
4. 参考本文档的故障排除部分

---

**版本**: v0.10.0  
**更新时间**: 2024年12月  
**维护团队**: 猫头鹰工厂开发团队