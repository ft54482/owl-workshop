from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from datetime import datetime

# 导入路由
from .api import auth_routes, user_routes, task_routes, gpu_routes, recharge_routes, admin_routes
from .config.supabase_config import get_supabase_manager
from .models.database_models import APIResponse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('owl_workshop.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    logger.info("猫头鹰工厂后端服务启动中...")
    
    try:
        # 初始化Supabase连接
        supabase_manager = get_supabase_manager()
        supabase = supabase_manager.get_client()
        
        # 测试数据库连接
        test_result = supabase.table('users').select('id').limit(1).execute()
        logger.info("数据库连接测试成功")
        
        # 这里可以添加其他初始化逻辑
        # 例如：启动任务调度器、初始化缓存等
        
        logger.info("猫头鹰工厂后端服务启动完成")
        
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}")
        raise
    
    yield
    
    # 关闭时执行
    logger.info("猫头鹰工厂后端服务关闭中...")
    # 这里可以添加清理逻辑
    logger.info("猫头鹰工厂后端服务已关闭")

# 创建FastAPI应用
app = FastAPI(
    title="猫头鹰工厂 API",
    description="猫头鹰工厂GPU集群管理系统后端API",
    version="0.10.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        # 生产环境域名
        "https://owl-workshop.example.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置受信任主机
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "*.example.com",  # 生产环境域名
    ]
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # 记录请求信息
    logger.info(f"请求开始: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.time() - start_time
    
    # 记录响应信息
    logger.info(f"请求完成: {request.method} {request.url} - 状态码: {response.status_code} - 耗时: {process_time:.3f}s")
    
    # 添加响应头
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            message="服务器内部错误",
            error="INTERNAL_SERVER_ERROR"
        ).dict()
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse(
            success=False,
            message=exc.detail,
            error=f"HTTP_{exc.status_code}"
        ).dict()
    )

# 注册路由
app.include_router(auth_routes.router, prefix="/api")
app.include_router(user_routes.router, prefix="/api")
app.include_router(task_routes.router, prefix="/api")
app.include_router(gpu_routes.router, prefix="/api")
app.include_router(recharge_routes.router, prefix="/api")
app.include_router(admin_routes.router, prefix="/api")

# 根路径
@app.get("/", response_model=APIResponse)
async def root():
    return APIResponse(
        success=True,
        message="欢迎使用猫头鹰工厂API",
        data={
            "name": "猫头鹰工厂",
            "version": "0.10.0",
            "description": "GPU集群管理系统",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    )

# 健康检查
@app.get("/health", response_model=APIResponse)
async def health_check():
    try:
        # 检查数据库连接
        supabase_manager = get_supabase_manager()
        supabase = supabase_manager.get_client()
        
        # 简单的数据库查询测试
        test_result = supabase.table('users').select('id').limit(1).execute()
        
        return APIResponse(
            success=True,
            message="服务健康",
            data={
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "connected"
            }
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return JSONResponse(
            status_code=503,
            content=APIResponse(
                success=False,
                message="服务不健康",
                data={
                    "status": "unhealthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e)
                }
            ).dict()
        )

# API信息
@app.get("/api/info", response_model=APIResponse)
async def api_info():
    return APIResponse(
        success=True,
        message="API信息",
        data={
            "name": "猫头鹰工厂 API",
            "version": "0.10.0",
            "description": "GPU集群管理系统后端API",
            "endpoints": {
                "auth": "/api/auth",
                "users": "/api/users",
                "tasks": "/api/tasks",
                "gpu": "/api/gpu",
                "recharge": "/api/recharge",
                "admin": "/api/admin"
            },
            "documentation": {
                "swagger": "/docs",
                "redoc": "/redoc"
            }
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )