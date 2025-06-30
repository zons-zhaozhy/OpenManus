"""
OpenManus Web界面
高仿OpenHands的Web交互界面
"""

import asyncio
import uuid
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agent.manus import Manus
from app.logger import logger


class ChatMessage(BaseModel):
    """聊天消息模型"""

    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: Optional[str] = None


class SessionRequest(BaseModel):
    """会话请求模型"""

    message: str
    session_id: Optional[str] = None


class SessionResponse(BaseModel):
    """会话响应模型"""

    session_id: str
    response: str
    status: str  # "thinking" | "ready" | "error"
    suggestions: Optional[List[str]] = None
    analysis_progress: Optional[float] = None  # 需求分析进度 0-100
    analysis_metrics: Optional[Dict] = None  # 需求分析指标


class AgentStatus(BaseModel):
    """Agent状态模型"""

    status: str  # "disconnected" | "connecting" | "initializing" | "ready" | "thinking" | "error"
    message: str
    progress: Optional[float] = None  # 进度百分比 0-100
    metrics: Optional[Dict] = None  # 分析指标


class WebInterface:
    """Web界面管理器"""

    def __init__(self):
        self.app = FastAPI(title="OpenManus", description="AI需求分析助手")
        self.sessions: Dict[str, Dict] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.setup_middleware()
        self.setup_routes()

    def setup_middleware(self):
        """设置中间件"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def setup_routes(self):
        """设置路由"""

        @self.app.get("/")
        async def serve_frontend():
            """服务前端页面"""
            return FileResponse("frontend/index.html")

        # 静态文件服务
        self.app.mount(
            "/static", StaticFiles(directory="frontend/static"), name="static"
        )

        @self.app.post("/api/chat", response_model=SessionResponse)
        async def chat_endpoint(request: SessionRequest):
            """聊天API端点"""
            try:
                # 获取或创建会话
                session_id = request.session_id or str(uuid.uuid4())

                if session_id not in self.sessions:
                    # 创建新会话
                    agent = await Manus.create()
                    self.sessions[session_id] = {
                        "agent": agent,
                        "history": [],
                        "status": "ready",
                        "analysis_progress": 0,
                        "analysis_metrics": {},
                    }

                session = self.sessions[session_id]
                agent = session["agent"]

                # 更新状态为思考中
                session["status"] = "thinking"
                await self.broadcast_status(
                    session_id, "thinking", "正在分析您的需求...", 0
                )

                # 添加用户消息到历史
                session["history"].append({"role": "user", "content": request.message})

                # 处理消息
                response = await agent.analyze_requirements(request.message)

                # 计算分析进度和指标
                progress = agent.get_analysis_progress()
                metrics = agent.get_analysis_metrics()

                # 更新会话状态
                session["analysis_progress"] = progress
                session["analysis_metrics"] = metrics

                # 添加助手回复到历史
                session["history"].append({"role": "assistant", "content": response})

                # 分析回复，提取建议
                suggestions = self.extract_suggestions(response)

                # 更新状态
                session["status"] = "ready"
                await self.broadcast_status(
                    session_id,
                    "ready",
                    "就绪，等待您的输入",
                    progress,
                    metrics,
                )

                return SessionResponse(
                    session_id=session_id,
                    response=response,
                    status="ready",
                    suggestions=suggestions,
                    analysis_progress=progress,
                    analysis_metrics=metrics,
                )

            except Exception as e:
                logger.error(f"Chat API error: {e}")
                await self.broadcast_status(session_id, "error", f"处理错误: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/sessions/{session_id}/history")
        async def get_session_history(session_id: str):
            """获取会话历史"""
            if session_id not in self.sessions:
                raise HTTPException(status_code=404, detail="Session not found")

            session = self.sessions[session_id]
            return {
                "history": session["history"],
                "analysis_progress": session["analysis_progress"],
                "analysis_metrics": session["analysis_metrics"],
            }

        @self.app.delete("/api/sessions/{session_id}")
        async def delete_session(session_id: str):
            """删除会话"""
            if session_id in self.sessions:
                # 清理Agent资源
                agent = self.sessions[session_id]["agent"]
                await agent.cleanup()
                del self.sessions[session_id]
                return {"message": "Session deleted"}
            else:
                raise HTTPException(status_code=404, detail="Session not found")

        @self.app.websocket("/ws/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, session_id: str):
            """WebSocket连接"""
            await websocket.accept()
            self.websocket_connections[session_id] = websocket

            try:
                # 发送初始状态
                session = self.sessions.get(session_id, {})
                progress = session.get("analysis_progress", 0)
                metrics = session.get("analysis_metrics", {})
                await self.send_status(
                    websocket, "ready", "连接成功，准备开始对话", progress, metrics
                )

                while True:
                    # 保持连接活跃
                    await asyncio.sleep(1)

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session {session_id}")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                if session_id in self.websocket_connections:
                    del self.websocket_connections[session_id]

    def extract_suggestions(self, response: str) -> List[str]:
        """从回复中提取建议问题"""
        suggestions = []
        lines = response.split("\n")

        for line in lines:
            line = line.strip()
            # 查找编号列表格式的问题
            if line and any(line.startswith(f"{i}.") for i in range(1, 10)):
                question = line[2:].strip()  # 移除编号
                if question and len(question) > 10:  # 过滤太短的内容
                    suggestions.append(question)
            # 查找以问号结尾的句子
            elif line.endswith("？") and len(line) > 15:
                suggestions.append(line)

        return suggestions[:5]  # 最多返回5个建议

    async def send_status(
        self,
        websocket: WebSocket,
        status: str,
        message: str,
        progress: Optional[float] = None,
        metrics: Optional[Dict] = None,
    ):
        """发送状态到WebSocket"""
        try:
            await websocket.send_json(
                {
                    "type": "status",
                    "status": status,
                    "message": message,
                    "progress": progress,
                    "metrics": metrics,
                }
            )
        except Exception as e:
            logger.error(f"Failed to send status: {e}")

    async def broadcast_status(
        self,
        session_id: str,
        status: str,
        message: str,
        progress: Optional[float] = None,
        metrics: Optional[Dict] = None,
    ):
        """广播状态到指定会话"""
        if session_id in self.websocket_connections:
            websocket = self.websocket_connections[session_id]
            await self.send_status(websocket, status, message, progress, metrics)

    async def run(self, host: str = "0.0.0.0", port: int = 3000):
        """运行Web服务器"""
        config = uvicorn.Config(self.app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
