#!/usr/bin/env python3
"""
OpenManus Web服务器

启动集成的前后端服务，包括：
1. FastAPI后端API服务
2. 静态文件服务（前端）
3. WebSocket服务（实时通信）
"""

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.ai_company import ai_company_router
from app.api.codebase import router as codebase_router
from app.api.knowledge_base import router as knowledge_router
from app.api.orchestrated_requirements import router as orchestrated_router
from app.api.project_management import project_router
from app.api.requirements import requirements_router

# 创建FastAPI应用
app = FastAPI(
    title="OpenManus AI助手", description="智能化软件需求分析助手", version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite默认开发服务器端口
        "http://127.0.0.1:5173",
        "http://localhost:5174",  # 备用端口
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(requirements_router)
app.include_router(orchestrated_router)  # 协调式需求分析
app.include_router(ai_company_router)
app.include_router(project_router)
app.include_router(knowledge_router)
app.include_router(codebase_router)

# 如果前端构建文件存在，提供静态文件服务
web_build_path = "app/web/dist"
if os.path.exists(web_build_path):
    app.mount("/static", StaticFiles(directory=web_build_path), name="static")


@app.get("/")
async def root():
    """根路径"""
    return {"message": "OpenManus AI助手后端服务", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "OpenManus"}


if __name__ == "__main__":
    print("🚀 启动 OpenManus Web 服务器...")
    print("📖 API文档: http://localhost:8000/docs")
    print("🔧 健康检查: http://localhost:8000/health")
    print("💻 前端页面: http://localhost:3000")

    uvicorn.run(
        "run_web_server:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
