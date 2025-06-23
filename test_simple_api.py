#!/usr/bin/env python3
"""
简化测试API服务器 - 用于快速测试前后端连通性
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="OpenManus 测试API", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequirementInput(BaseModel):
    content: str
    project_context: str = None


@app.get("/")
async def root():
    return {"message": "OpenManus 测试API运行正常", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "OpenManus-Test"}


@app.get("/api/requirements/health")
async def requirements_health():
    return {
        "status": "healthy",
        "service": "requirements_test",
        "version": "1.0.0",
        "agents_available": ["clarifier", "analyst", "writer", "reviewer"],
        "active_sessions_count": 0,
    }


@app.post("/api/requirements/analyze")
async def test_analyze(request: RequirementInput):
    """测试需求分析接口"""
    return {
        "session_id": "test-session-123",
        "status": "completed",
        "result": {
            "final_result": f"已收到您的需求：{request.content}。这是一个测试响应，说明API连通正常！",
            "session_summary": "测试会话摘要",
            "parallel_enabled": True,
        },
        "progress": {
            "current_stage": "测试完成",
            "clarification_complete": True,
            "analysis_complete": True,
        },
    }


@app.post("/api/requirements/clarify")
async def test_clarify(request: dict):
    """测试需求澄清接口"""
    return {
        "session_id": request.get("session_id", "test-session-123"),
        "response": f"收到您的回答：{request.get('answer', '')}。这是测试澄清响应！",
        "progress": {
            "current_stage": "澄清测试",
            "clarification_complete": False,
            "analysis_complete": False,
        },
    }


if __name__ == "__main__":
    print("🚀 启动OpenManus简化测试API服务器...")
    print("📍 URL: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    print("🔍 健康检查: curl http://localhost:8000/health")
    print(
        "⚡ 需求分析测试: curl -X POST http://localhost:8000/api/requirements/analyze -H 'Content-Type: application/json' -d '{\"content\":\"测试需求\"}'"
    )

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
