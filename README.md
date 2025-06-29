# 猫头鹰工厂 (Owl Workshop) v0.10

🦉 **智能数据分析与内容营销平台** - 基于 Supabase 的现代化智能GPU分析平台

## 📋 项目概述

猫头鹰工厂是一个完整的GPU计算资源管理平台，提供企业级的AI视频内容分析与处理服务。支持：

- 🔐 用户注册登录和权限管理
- 💰 充值码系统和余额管理
- 🖥️ GPU服务器资源调度
- 📊 智能分析任务管理
- 📈 实时数据统计和监控
- 🎥 AI视频内容分析
- 🗣️ Whisper语音识别服务
- 🤖 DeepSeek AI集成

## 🏗️ 技术架构

### 后端技术栈
- **数据库**: Supabase (PostgreSQL)
- **API框架**: FastAPI
- **语言**: Python 3.9+ (通过Conda管理)
- **ORM**: Supabase Python Client
- **认证**: Supabase Auth
- **AI服务**: Whisper, DeepSeek

### 前端技术栈
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI库**: Tailwind CSS + Framer Motion
- **状态管理**: React Context
- **路由**: React Router

### GPU集群管理
- **集群监控**: 实时GPU资源监控
- **任务调度**: 智能负载均衡
- **分布式计算**: 多节点协同处理

## 📁 项目结构

```
猫头鹰工场/
├── 前端页面/                # React前端应用 (端口3000)
│   ├── src/
│   │   ├── components/      # React组件
│   │   ├── pages/          # 页面组件
│   │   ├── contexts/       # React Context
│   │   └── utils/          # 工具函数
│   ├── package.json
│   └── vite.config.ts
├── 后端程序/                # FastAPI后端服务 (端口8000)
│   ├── api/                # API路由
│   ├── models/             # 数据模型
│   ├── services/           # 业务逻辑
│   ├── main.py             # FastAPI主应用
│   └── requirements.txt
├── GPU服务器配置/           # GPU集群管理
│   ├── gpu_dashboard.py    # GPU监控面板
│   ├── cluster_manager.py  # 集群管理器
│   └── deployment_scripts/ # 部署脚本
├── 核心代码/                # 核心AI服务
│   ├── whisper_server.py   # Whisper语音识别
│   ├── moreapi_client.py   # MoreAPI集成
│   └── ai_workflow.py      # AI工作流
├── 核心服务/                # 企业级服务
│   ├── 猫头鹰工厂_主服务API.py
│   ├── GPU集群任务分发服务.py
│   └── MoreAPI集成服务.py
├── PromptX/                # PromptX集成
├── 配置文件/                # 系统配置
├── 部署脚本/                # 生产部署
└── 项目文档/                # 技术文档
```

## 🌐 系统访问地址

### 🖥️ 后台管理系统
- **后台API服务**: http://localhost:8000
- **API文档 (Swagger)**: http://localhost:8000/docs
- **API文档 (ReDoc)**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health
- **系统状态**: http://localhost:8000/status

### 🎨 前端用户界面
- **前端应用**: http://localhost:3000
- **管理后台**: http://localhost:3000/admin
- **用户仪表板**: http://localhost:3000/dashboard
- **GPU监控**: http://localhost:3000/gpu-management

### 📊 数据库管理
- **Supabase控制台**: https://supabase.com/dashboard
- **数据库直连**: 配置在环境变量中

## 🚀 快速开始

### 1. 环境准备

确保已安装：
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 或 Anaconda
- Node.js 18+
- Git
- Python 3.9+

### 2. 克隆项目

```bash
git clone https://github.com/ft54482/owl-workshop.git
cd owl-workshop
```

### 3. 配置环境变量

复制 `.env.example` 到 `.env` 并配置：

```env
# Supabase配置
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# AI服务配置
MOREAPI_KEY=your_moreapi_key
DEEPSEEK_API_KEY=your_deepseek_key

# 应用配置
APP_ENV=development
DEBUG=true
```

### 4. 创建并激活Conda环境

```bash
# 从environment.yml文件创建Conda环境
conda env create -f environment.yml

# 激活新创建的环境
conda activate maotouying-factory
```

### 5. 启动服务

#### 启动后端服务
```bash
cd 后端程序
python start_server.py
```

#### 启动前端服务
```bash
cd 前端页面
npm install
npm run dev
```

#### 启动GPU集群服务
```bash
cd GPU服务器配置
python gpu_dashboard.py
```

### 6. 验证服务

```bash
# 检查后端API健康状态
curl http://localhost:8000/health

# 检查前端应用
open http://localhost:3000

# 检查GPU监控
open http://localhost:3000/gpu-management
```

## 🔧 核心功能

### 用户管理系统
- 用户注册/登录
- 角色权限管理
- 账户余额管理
- 充值码系统

### GPU集群管理
- 实时GPU资源监控
- 智能任务调度
- 负载均衡
- 性能统计

### AI服务集成
- **Whisper语音识别**: 高精度语音转文字
- **DeepSeek AI**: 智能内容分析
- **MoreAPI**: 企业级API服务
- **视频分析**: AI驱动的视频内容分析

### 数据分析平台
- 实时数据统计
- 用户行为分析
- 任务执行报告
- 系统性能监控

## 📊 数据库设计

### 核心表结构

#### 用户表 (users)
- `id`: 用户唯一标识
- `username`: 用户名
- `email`: 邮箱
- `role`: 用户角色 (admin/user)
- `balance`: 账户余额
- `created_at`: 创建时间

#### 任务表 (analysis_tasks)
- `id`: 任务唯一标识
- `user_id`: 用户ID
- `task_type`: 任务类型
- `status`: 任务状态
- `cost`: 任务费用
- `server_id`: 分配的服务器ID
- `output_data`: 输出数据

#### GPU服务器表 (gpu_servers)
- `id`: 服务器唯一标识
- `name`: 服务器名称
- `gpu_model`: GPU型号
- `status`: 服务器状态
- `current_load`: 当前负载

## 🔧 API接口

### 用户管理
- `POST /api/users` - 创建用户
- `GET /api/users/{user_id}` - 获取用户信息
- `PUT /api/users/{user_id}/balance` - 更新用户余额

### 任务管理
- `POST /api/tasks` - 创建任务
- `GET /api/tasks/{task_id}` - 获取任务详情
- `PUT /api/tasks/{task_id}/status` - 更新任务状态

### GPU管理
- `GET /api/gpu/servers` - 获取GPU服务器列表
- `GET /api/gpu/stats` - 获取GPU统计信息
- `POST /api/gpu/tasks` - 分配GPU任务

## 🛠️ 开发指南

### 代码规范
- Python: 遵循 PEP 8 编码规范
- TypeScript: 使用严格模式
- React: 使用函数组件和Hooks
- 添加适当的类型注解

### 测试
```bash
# 运行后端测试
pytest tests/

# 运行前端测试
npm test
```

## 🔒 安全考虑

- 使用 Supabase RLS (Row Level Security)
- API 密钥安全存储
- 用户密码安全哈希
- 输入验证和错误处理
- CORS 和 CSRF 保护

## 🚀 部署

### 生产环境部署

1. **环境配置**: 设置生产环境变量
2. **数据库迁移**: 运行生产数据库迁移
3. **应用部署**: 使用 Docker 或云平台部署
4. **监控设置**: 配置日志和监控系统

### Docker 部署

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📝 版本历史

### v0.10 (当前版本)
- ✨ 完整的React前端重构
- 🔧 GPU集群管理优化
- 🤖 AI服务集成增强
- 📊 实时监控面板
- 🔐 安全性提升
- 📱 响应式设计优化

### v0.9
- 🎥 视频分析功能
- 🗣️ Whisper集成
- 💰 充值系统

### v0.8
- 👥 用户管理系统
- 🖥️ GPU资源调度

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如果您遇到问题或有疑问，请：

1. 查看项目文档
2. 搜索 [Issues](../../issues)
3. 创建新的 [Issue](../../issues/new)

## 🔗 相关链接

- [Supabase 文档](https://supabase.com/docs)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [React 文档](https://react.dev/)
- [Vite 文档](https://vitejs.dev/)

---

**猫头鹰工厂** - 让GPU计算更智能，让AI服务更便捷 🦉✨

*Built with ❤️ by 猫头鹰工场团队*