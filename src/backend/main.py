"""
应用程序入口点
初始化FastAPI应用并注册所有路由
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Import routers
from backend.routers import (
    domains,
    odd,
    pipeline,
    config,
    simulation,
    agent,
    feedback,
    monitor,
    user,
)

# Import from onesim
from onesim.utils.common import setup_logging

# Create FastAPI application
app = FastAPI(
    title="Agent Simulation API",
    description="OneSim系统API",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(domains.router)
app.include_router(odd.router)
app.include_router(pipeline.router)
app.include_router(config.router)
app.include_router(simulation.router)
app.include_router(agent.router)
app.include_router(feedback.router)
app.include_router(monitor.router)
app.include_router(user.router)

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Agent Simulation API"}

# Global variables will be imported from appropriate modules

# 在这里定义需要在应用启动时执行的代码
@app.on_event("startup")
async def startup_event():
    
    # 日志配置
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    logger.add(os.path.join(log_dir, "app.log"), rotation="500 MB", compression="zip")
    
    logger.info("应用程序启动")

# 在这里定义需要在应用关闭时执行的代码
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("应用程序关闭") 
