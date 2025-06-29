#!/usr/bin/env python3
"""
OpenManus Web服务器

启动集成的前后端服务，包括：
1. FastAPI后端API服务
2. 静态文件服务（前端）
3. WebSocket服务（实时通信）
"""

import asyncio
import os
import signal
import sys
from pathlib import Path
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router
from app.core.performance_controller import (
    PerformanceConfig,
    init_performance_controller,
)
from app.logger import logger

# 配置更合理的超时参数
performance_config = PerformanceConfig(
    llm_timeout_seconds=30.0,
    llm_concurrent_limit=5,
    monitor_interval=60.0,
)

# 创建FastAPI应用
app = FastAPI(
    title="OpenManus AI助手", description="智能化软件需求分析助手", version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router)


# 初始化性能控制器
@app.on_event("startup")
async def startup_event():
    """启动事件"""
    # 初始化性能控制器
    await init_performance_controller(performance_config)
    logger.info("性能控制器初始化完成")


# 挂载静态文件
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """根路径"""
    return {"message": "OpenManus AI助手后端服务", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """健康检查"""
    from app.core.performance_controller import get_performance_controller

    controller = get_performance_controller()
    status = controller.get_status()

    return {"status": "healthy", "service": "OpenManus", "performance": status}


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    print("🧹 开始清理应用资源...")

    # 清理性能控制器
    from app.core.performance_controller import get_performance_controller

    controller = get_performance_controller()
    await controller.cleanup()

    # 清理沙盒管理器（如果有的话）
    try:
        from app.sandbox.core.manager import get_sandbox_manager

        sandbox_manager = get_sandbox_manager()
        await sandbox_manager.cleanup()
        print("✅ 沙盒管理器清理完成")
    except Exception as e:
        print(f"⚠️ 沙盒管理器清理异常: {e}")

    print("✅ 应用资源清理完成")


async def cleanup_handler():
    """处理程序退出时的清理工作"""
    print("🛑 接收到退出信号，开始清理...")
    await shutdown_event()


def signal_handler(signum, frame):
    """信号处理器"""
    print(f"🛑 接收到信号 {signum}，开始优雅关闭...")

    # 在事件循环中运行清理函数
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(cleanup_handler())
        else:
            asyncio.run(cleanup_handler())
    except Exception as e:
        print(f"⚠️ 清理过程中出现异常: {e}")
    finally:
        sys.exit(0)


if __name__ == "__main__":
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # 终止信号

    print("🚀 启动 OpenManus Web 服务器...")
    print("📖 API文档: http://localhost:8000/docs")
    print("🔧 健康检查: http://localhost:8000/health")
    print("💻 前端页面: http://localhost:3000")

    try:
        port = int(os.getenv("PORT", 8000))
        uvicorn.run(app, host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        print("🛑 用户中断，正在关闭...")
    except Exception as e:
        print(f"💥 服务器启动失败: {e}")
    finally:
        # 确保清理工作完成
        asyncio.run(cleanup_handler())
