"""
架构设计助手API路由
"""

import asyncio
import json
import os
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.requirements_modular.storage import session_storage
from app.assistants.architecture.flow import ArchitectureFlow
from app.core.adaptive_learning_system import AnalysisCase
from app.logger import logger

architecture_router = APIRouter(prefix="/api/architecture", tags=["Architecture"])


# 数据模型
class ArchitectureRequest(BaseModel):
    requirements_doc: str
    session_id: Optional[str] = None
    # 新增：支持从第一期会话直接启动
    source_requirements_session_id: Optional[str] = None
    # 新增：项目约束信息
    project_constraints: Optional[Dict] = None


class ArchitectureResponse(BaseModel):
    session_id: str
    status: str
    result: Optional[str] = None
    progress: Optional[Dict] = None
    error: Optional[str] = None


class RequirementsImportRequest(BaseModel):
    """从第一期导入需求的请求模型"""

    requirements_session_id: str
    project_constraints: Optional[Dict] = None


# 会话管理
architecture_sessions = {}


@architecture_router.get("/")
async def get_architecture_info():
    """获取架构设计助手信息"""
    return {
        "name": "架构设计助手",
        "status": "ready",
        "description": "智能化系统架构设计助手",
        "version": "2.0.0",
        "capabilities": [
            "技术选型分析",
            "系统架构设计",
            "数据库设计",
            "架构质量评审",
            "与需求分析无缝集成",
        ],
        "integration": {
            "requirements_analysis": "支持从第一期需求分析直接导入",
            "supported_input_formats": ["requirements_document", "session_import"],
        },
    }


@architecture_router.post(
    "/import-from-requirements", response_model=ArchitectureResponse
)
async def import_from_requirements(request: RequirementsImportRequest):
    """
    从第一期需求分析会话导入需求并启动架构设计
    这是第一期与第二期集成的关键接口
    """
    try:
        logger.info(f"开始从需求分析会话导入: {request.requirements_session_id}")

        # 1. 从第一期会话获取需求文档
        requirements_data = await _load_requirements_from_session(
            request.requirements_session_id
        )

        if not requirements_data:
            raise HTTPException(
                status_code=404,
                detail=f"未找到需求分析会话: {request.requirements_session_id}",
            )

        # 2. 验证需求文档质量
        if not await _validate_requirements_quality(requirements_data):
            raise HTTPException(
                status_code=400, detail="需求文档质量不达标，无法进行架构设计"
            )

        # 3. 生成架构设计会话ID
        architecture_session_id = str(uuid.uuid4())

        # 4. 准备架构设计输入
        architecture_input = await _prepare_architecture_input(
            requirements_data, request.project_constraints
        )

        # 5. 创建架构设计流程
        flow = ArchitectureFlow(session_id=architecture_session_id)

        # 6. 执行架构设计
        result = await flow.execute(architecture_input["formatted_requirements"])

        # 7. 保存会话信息
        architecture_sessions[architecture_session_id] = {
            "flow": flow,
            "source_requirements_session": request.requirements_session_id,
            "requirements_data": requirements_data,
            "project_constraints": request.project_constraints,
            "created_at": datetime.now(),
            "last_updated": datetime.now(),
            "status": "completed",
        }

        return ArchitectureResponse(
            session_id=architecture_session_id,
            status="completed",
            result=result,
            progress=flow.get_progress(),
        )

    except Exception as e:
        logger.error(f"从需求分析导入失败: {e}")
        return ArchitectureResponse(session_id="", status="error", error=str(e))


async def _load_requirements_from_session(
    requirements_session_id: str,
) -> Optional[Dict]:
    """
    从第一期需求分析会话加载需求文档
    支持多种加载方式：文件系统、内存会话、数据库等
    """
    try:
        # 方式1: 从需求分析API的session_storage加载
        session_data = session_storage.get_session(requirements_session_id)
        if session_data:
            return {
                "session_id": requirements_session_id,
                "requirement_text": session_data.get("requirement_text", ""),
                "quality_score": session_data.get("quality_score", 0.0),
                "clarification_history": session_data.get("clarification_history", []),
                "analysis_result": session_data.get("analysis_result", {}),
                "source": "active_session",
            }

        # 方式2: 从文件系统加载已保存的需求文档
        requirements_dir = "data/requirements"
        if os.path.exists(requirements_dir):
            for filename in os.listdir(requirements_dir):
                if requirements_session_id[:8] in filename and filename.endswith(".md"):
                    filepath = os.path.join(requirements_dir, filename)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()

                    # 解析文档内容
                    requirements_text = _extract_requirements_from_document(content)
                    quality_score = _extract_quality_score_from_document(content)

                    return {
                        "session_id": requirements_session_id,
                        "requirement_text": requirements_text,
                        "quality_score": quality_score,
                        "source": "saved_document",
                        "file_path": filepath,
                    }

        # 方式3: 尝试通过API调用获取（如果第一期服务正在运行）
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://localhost:8000/api/requirements/sessions/{requirements_session_id}"
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "session_id": requirements_session_id,
                        "requirement_text": data.get("requirement_text", ""),
                        "quality_score": data.get("quality_score", 0.0),
                        "source": "api_call",
                    }
        except Exception as e:
            logger.warning(f"无法通过API获取需求数据: {e}")

        return None

    except Exception as e:
        logger.error(f"加载需求文档失败: {e}")
        return None


def _extract_requirements_from_document(document_content: str) -> str:
    """从保存的需求文档中提取需求内容"""
    try:
        # 查找"最终需求描述"部分
        import re

        match = re.search(
            r"## 🎯 最终需求描述\s*\n\n(.*?)\n\n## ", document_content, re.DOTALL
        )
        if match:
            return match.group(1).strip()

        # 如果没有找到标准格式，返回整个文档
        return document_content
    except Exception:
        return document_content


def _extract_quality_score_from_document(document_content: str) -> float:
    """从保存的需求文档中提取质量评分"""
    try:
        import re

        match = re.search(r"质量评分\*\*:\s*(\d+\.?\d*)", document_content)
        if match:
            return float(match.group(1))
        return 0.8  # 默认质量分
    except Exception:
        return 0.8


async def _validate_requirements_quality(requirements_data: Dict) -> bool:
    """验证需求文档质量是否达到架构设计标准"""
    try:
        quality_score = requirements_data.get("quality_score", 0.0)
        requirement_text = requirements_data.get("requirement_text", "")

        # 质量检查标准
        checks = {
            "quality_score_threshold": quality_score >= 0.7,  # 最低质量要求
            "content_length": len(requirement_text) >= 100,  # 最小内容长度
            "has_functional_requirements": "功能" in requirement_text
            or "需求" in requirement_text,
            "has_basic_structure": any(
                keyword in requirement_text
                for keyword in ["系统", "用户", "功能", "管理"]
            ),
        }

        passed_checks = sum(checks.values())
        total_checks = len(checks)

        logger.info(f"需求质量验证: {passed_checks}/{total_checks} 项通过")

        # 至少通过75%的检查才能继续
        return passed_checks >= (total_checks * 0.75)

    except Exception as e:
        logger.error(f"需求质量验证失败: {e}")
        return False


async def _prepare_architecture_input(
    requirements_data: Dict, project_constraints: Optional[Dict]
) -> Dict:
    """
    准备架构设计的输入数据
    将第一期的需求数据转换为第二期能够处理的格式
    """
    try:
        requirement_text = requirements_data.get("requirement_text", "")

        # 构建完整的架构设计输入
        formatted_input = f"""# 系统架构设计输入文档

## 📋 项目基础信息
- **需求来源会话**: {requirements_data.get('session_id', 'unknown')}
- **需求质量评分**: {requirements_data.get('quality_score', 0.0):.2f}
- **文档生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 核心需求描述

{requirement_text}

## 📊 澄清历史信息
"""

        # 添加澄清历史（如果有）
        clarification_history = requirements_data.get("clarification_history", [])
        if clarification_history:
            formatted_input += "\n### 需求澄清过程\n"
            for i, qa in enumerate(clarification_history, 1):
                question = qa.get("question", "")
                answer = qa.get("answer", "")
                formatted_input += f"\n**Q{i}**: {question}\n**A{i}**: {answer}\n"

        # 添加项目约束（如果有）
        if project_constraints:
            formatted_input += "\n## 🔒 项目约束条件\n"

            if "budget" in project_constraints:
                formatted_input += f"- **预算限制**: {project_constraints['budget']}\n"

            if "timeline" in project_constraints:
                formatted_input += (
                    f"- **时间限制**: {project_constraints['timeline']}\n"
                )

            if "team_size" in project_constraints:
                formatted_input += (
                    f"- **团队规模**: {project_constraints['team_size']}\n"
                )

            if "technology_constraints" in project_constraints:
                formatted_input += (
                    f"- **技术约束**: {project_constraints['technology_constraints']}\n"
                )

            if "deployment_environment" in project_constraints:
                formatted_input += (
                    f"- **部署环境**: {project_constraints['deployment_environment']}\n"
                )

        formatted_input += f"""

## 📝 架构设计要求

请基于以上需求信息进行专业的系统架构设计，包括：

1. **技术选型分析** - 选择最适合的技术栈
2. **系统架构设计** - 设计完整的系统架构
3. **数据库设计** - 设计数据模型和数据库结构
4. **架构质量评审** - 进行专业的质量评估

请确保架构设计方案：
- 完全满足上述需求
- 考虑项目约束条件
- 具备良好的可扩展性和可维护性
- 符合软件工程最佳实践
"""

        return {
            "formatted_requirements": formatted_input,
            "raw_requirements": requirement_text,
            "quality_metadata": {
                "source_session": requirements_data.get("session_id"),
                "quality_score": requirements_data.get("quality_score", 0.0),
                "clarification_rounds": len(clarification_history),
            },
            "constraints": project_constraints or {},
        }

    except Exception as e:
        logger.error(f"准备架构设计输入失败: {e}")
        raise


@architecture_router.post("/design", response_model=ArchitectureResponse)
async def design_architecture(request: ArchitectureRequest):
    """开始架构设计"""
    try:
        # 生成或使用现有会话ID
        session_id = request.session_id or str(uuid.uuid4())

        logger.info(f"开始架构设计 - 会话ID: {session_id}")

        # 如果指定了源需求会话，先导入需求
        if request.source_requirements_session_id:
            import_request = RequirementsImportRequest(
                requirements_session_id=request.source_requirements_session_id,
                project_constraints=request.project_constraints,
            )
            return await import_from_requirements(import_request)

        # 否则直接使用提供的需求文档
        # 创建架构设计流程
        flow = ArchitectureFlow(session_id=session_id)

        # 执行架构设计
        result = await flow.execute(request.requirements_doc)

        # 保存会话信息
        architecture_sessions[session_id] = {
            "flow": flow,
            "created_at": datetime.now(),
            "last_updated": datetime.now(),
            "status": "completed",
        }

        return ArchitectureResponse(
            session_id=session_id,
            status="completed",
            result=result,
            progress=flow.get_progress(),
        )

    except Exception as e:
        logger.error(f"架构设计失败: {e}")
        return ArchitectureResponse(session_id=session_id, status="error", error=str(e))


@architecture_router.get("/session/{session_id}/progress")
async def get_design_progress(session_id: str):
    """获取架构设计进度"""
    if session_id not in architecture_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    session = architecture_sessions[session_id]
    flow = session["flow"]

    return {
        "session_id": session_id,
        "progress": flow.get_progress(),
        "created_at": session["created_at"],
        "last_updated": session["last_updated"],
    }


@architecture_router.get("/session/{session_id}/result")
async def get_design_result(session_id: str):
    """获取架构设计结果"""
    if session_id not in architecture_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    session = architecture_sessions[session_id]
    flow = session["flow"]

    return {
        "session_id": session_id,
        "status": session["status"],
        "result": flow.current_context,
        "progress": flow.get_progress(),
    }


@architecture_router.post("/validate")
async def validate_architecture(request: dict):
    """验证架构设计质量"""
    try:
        tech_stack = request.get("tech_stack", "")
        architecture_doc = request.get("architecture_doc", "")
        database_doc = request.get("database_doc", "")

        # 创建临时流程用于验证
        flow = ArchitectureFlow()
        reviewer = flow.get_agent("reviewer")

        # 执行架构评审
        review_result = await reviewer.review_architecture(
            tech_stack, architecture_doc, database_doc
        )

        review_summary = reviewer.get_review_summary()

        return {
            "validation_result": review_result,
            "score": review_summary["total_score"],
            "quality_level": review_summary["quality_level"],
            "recommendations": review_summary.get("recommendations", []),
        }

    except Exception as e:
        logger.error(f"架构验证失败: {e}")
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


@architecture_router.get("/sessions")
async def list_sessions():
    """获取所有会话列表"""
    sessions = []
    for session_id, session_info in architecture_sessions.items():
        sessions.append(
            {
                "session_id": session_id,
                "created_at": session_info["created_at"],
                "last_updated": session_info["last_updated"],
                "status": session_info["status"],
                "source_requirements_session": session_info.get(
                    "source_requirements_session"
                ),
            }
        )

    return {"sessions": sessions}


@architecture_router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """删除指定会话"""
    if session_id not in architecture_sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    del architecture_sessions[session_id]
    return {"message": f"会话 {session_id} 已删除"}


@architecture_router.post("/analyze")
async def analyze_architecture(content: Dict) -> Dict:
    """分析系统架构"""
    try:
        # 创建会话ID
        session_id = str(uuid.uuid4())

        # 创建会话数据
        session_data = {
            "id": session_id,
            "content": content,
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # 存储会话数据
        session_storage.set_session(session_id, session_data)

        # 创建Flow实例
        flow = ArchitectureFlow()

        # 执行分析
        result = await flow.execute(content)

        # 更新会话状态
        session_data["status"] = "completed"
        session_data["result"] = result
        session_data["updated_at"] = datetime.now().isoformat()
        session_storage.set_session(session_id, session_data)

        return {
            "session_id": session_id,
            "status": "success",
            "result": result,
        }

    except Exception as e:
        logger.error(f"分析架构失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@architecture_router.get("/session/{session_id}")
async def get_session(session_id: str) -> Dict:
    """获取会话状态"""
    try:
        session_data = session_storage.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
        return session_data
    except Exception as e:
        logger.error(f"获取会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@architecture_router.post("/session/{session_id}/cancel")
async def cancel_session(session_id: str) -> Dict:
    """取消会话"""
    try:
        session_data = session_storage.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")

        session_data["status"] = "cancelled"
        session_data["updated_at"] = datetime.now().isoformat()
        session_storage.set_session(session_id, session_data)

        return {"status": "success", "message": "会话已取消"}
    except Exception as e:
        logger.error(f"取消会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
