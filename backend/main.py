# -*- coding: utf-8 -*-
"""
🦉 猫头鹰工厂 - 后台管理系统主应用
基于FastAPI + Supabase的完整后端解决方案
"""

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
from loguru import logger
import sys

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/app.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO",
    rotation="1 day",
    retention="30 days"
)

# 导入配置和服务
from config.supabase_config import settings, supabase_manager
from services.recharge_service import recharge_service
from services.gpu_monitor_service import gpu_monitor_service

# 导入API路由
from api.auth_routes import router as auth_router
from api.user_routes import router as user_router
from api.recharge_routes import router as recharge_router
from api.gpu_routes import router as gpu_router
from api.admin_routes import router as admin_router
from api.log_routes import router as log_router

# 导入Supabase认证中间件
from middleware.supabase_auth import get_current_user, get_admin_user

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 猫头鹰工厂后台管理系统启动中...")
    
    try:
        # 测试Supabase连接
        if supabase_manager.test_connection():
            logger.info("✅ Supabase连接测试成功")
        else:
            logger.warning("⚠️ Supabase连接测试失败")
        
        # 同步GPU服务器配置
        sync_result = await gpu_monitor_service.sync_gpu_servers_to_database()
        if sync_result["success"]:
            logger.info(f"✅ GPU服务器配置同步成功: {sync_result['message']}")
        else:
            logger.warning(f"⚠️ GPU服务器配置同步失败: {sync_result['message']}")
        
        logger.info("🎉 系统启动完成")
        
    except Exception as e:
        logger.error(f"❌ 系统启动失败: {e}")
    
    yield
    
    # 关闭时执行
    logger.info("👋 猫头鹰工厂后台管理系统关闭")

# 创建FastAPI应用
app = FastAPI(
    title="猫头鹰工厂后台管理系统",
    description="基于Supabase的完整后端管理解决方案",
    version="0.10.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://your-frontend-domain.com"  # 生产环境域名
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加可信主机中间件
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.your-domain.com"]
)

# 全局异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理"""
    logger.error(f"❌ 未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务器内部错误",
            "status_code": 500
        }
    )

# 根路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "🦉 猫头鹰工厂后台管理系统",
        "version": "0.10.0",
        "status": "running",
        "docs": "/docs"
    }

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 测试Supabase连接
        supabase_status = supabase_manager.test_connection()
        
        return {
            "status": "healthy",
            "timestamp": str(datetime.utcnow()),
            "services": {
                "supabase": "connected" if supabase_status else "disconnected",
                "api": "running"
            }
        }
    except Exception as e:
        logger.error(f"❌ 健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

# 系统信息
@app.get("/info")
async def system_info():
    """系统信息"""
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "debug": settings.debug,
        "environment": "development" if settings.debug else "production"
    }

# 注册API路由
app.include_router(auth_router, prefix="/api/auth", tags=["认证"])
app.include_router(user_router, prefix="/api/users", tags=["用户管理"])
app.include_router(recharge_router, prefix="/api/recharge", tags=["充值管理"])
app.include_router(gpu_router, prefix="/api/gpu", tags=["GPU监控"])
app.include_router(admin_router, prefix="/api/admin", tags=["系统管理"])
app.include_router(log_router, prefix="/api/logs", tags=["日志管理"])

# 导出依赖函数供路由使用
__all__ = ["app", "get_current_user", "get_admin_user"]

if __name__ == "__main__":
    # 开发环境运行
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )