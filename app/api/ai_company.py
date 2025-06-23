"""
AI软件公司完整流程API - 支持五个阶段的协调管理
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.ai_company_orchestrator import AICompanyOrchestrator
from app.logger import logger


class ProjectInput(BaseModel):
    content: str
    project_name: Optional[str] = "新项目"
    project_type: Optional[str] = "Web应用"


class StageRequest(BaseModel):
    stage: str
    input_data: Optional[str] = None


# 创建路由器
ai_company_router = APIRouter(prefix="/api/ai-company", tags=["AI Company"])

# 全局项目管理器（简化实现，生产环境建议使用持久化存储）
active_projects: Dict[str, AICompanyOrchestrator] = {}


@ai_company_router.get("/")
async def get_ai_company_info():
    """获取AI软件公司信息"""
    return {
        "name": "OpenManus AI软件公司",
        "description": "通过多智能体协作实现完整的软件开发生命周期",
        "version": "1.0.0",
        "stages": [
            {
                "stage": "需求分析",
                "description": "智能化需求澄清和分析",
                "agents": ["需求澄清师", "业务分析师", "技术文档编写师", "质量评审师"],
                "status": "已完成",
            },
            {
                "stage": "架构设计",
                "description": "系统架构和技术选型设计",
                "agents": ["技术选型师", "系统架构师", "数据库设计师", "架构评审师"],
                "status": "已完成",
            },
            {
                "stage": "编码实现",
                "description": "基于架构设计实现代码",
                "agents": ["前端开发师", "后端开发师", "API开发师", "代码评审师"],
                "status": "开发中",
            },
            {
                "stage": "测试部署",
                "description": "系统测试和部署上线",
                "agents": ["测试工程师", "DevOps工程师", "QA评审师"],
                "status": "规划中",
            },
            {
                "stage": "智能体群协作",
                "description": "跨阶段协作和项目管理",
                "agents": ["项目管理智能体", "决策智能体", "协调智能体"],
                "status": "规划中",
            },
        ],
        "capabilities": [
            "端到端软件项目开发",
            "多智能体协作",
            "质量保证体系",
            "自动化工作流",
        ],
    }


@ai_company_router.post("/projects/create")
async def create_project(request: ProjectInput) -> Dict:
    """创建新的软件项目"""
    try:
        # 创建项目ID
        import uuid

        project_id = str(uuid.uuid4())

        # 创建AI软件公司协调器
        orchestrator = AICompanyOrchestrator()
        active_projects[project_id] = orchestrator

        logger.info(f"创建新项目: {project_id} - {request.project_name}")

        return {
            "project_id": project_id,
            "project_name": request.project_name,
            "project_type": request.project_type,
            "status": "已创建",
            "current_stage": "需求分析",
            "next_steps": [
                "调用 /projects/{project_id}/execute 开始项目执行",
                "调用 /projects/{project_id}/status 查看项目状态",
            ],
        }

    except Exception as e:
        logger.error(f"项目创建失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@ai_company_router.post("/projects/{project_id}/execute")
async def execute_project(project_id: str, request: ProjectInput) -> Dict:
    """执行完整的软件项目开发流程"""
    try:
        if project_id not in active_projects:
            raise HTTPException(status_code=404, detail="项目不存在")

        orchestrator = active_projects[project_id]

        logger.info(f"开始执行项目: {project_id}")

        # 执行完整项目流程
        result = await orchestrator.execute_full_project(request.content)

        return {
            "project_id": project_id,
            "execution_result": result,
            "timestamp": "2025-01-23T17:00:00Z",
        }

    except Exception as e:
        logger.error(f"项目执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@ai_company_router.get("/projects/{project_id}/status")
async def get_project_status(project_id: str) -> Dict:
    """获取项目状态"""
    try:
        if project_id not in active_projects:
            raise HTTPException(status_code=404, detail="项目不存在")

        orchestrator = active_projects[project_id]
        status = orchestrator.get_project_status()

        return {
            "project_id": project_id,
            "status": status,
            "timestamp": "2025-01-23T17:00:00Z",
        }

    except Exception as e:
        logger.error(f"状态查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@ai_company_router.get("/projects/{project_id}/stages/{stage}")
async def get_stage_details(project_id: str, stage: str) -> Dict:
    """获取指定阶段的详细信息"""
    try:
        if project_id not in active_projects:
            raise HTTPException(status_code=404, detail="项目不存在")

        orchestrator = active_projects[project_id]
        details = orchestrator.get_stage_details(stage)

        return {
            "project_id": project_id,
            "stage_details": details,
            "timestamp": "2025-01-23T17:00:00Z",
        }

    except Exception as e:
        logger.error(f"阶段详情查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@ai_company_router.get("/projects")
async def list_active_projects() -> Dict:
    """列出所有活跃项目"""
    try:
        projects = []
        for project_id, orchestrator in active_projects.items():
            status = orchestrator.get_project_status()
            projects.append(
                {
                    "project_id": project_id,
                    "current_stage": status["current_stage"],
                    "completion_percentage": status["completion_percentage"],
                    "completed_stages": status["completed_stages"],
                }
            )

        return {"active_projects": projects, "total_count": len(projects)}

    except Exception as e:
        logger.error(f"项目列表获取失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@ai_company_router.delete("/projects/{project_id}")
async def cleanup_project(project_id: str) -> Dict:
    """清理项目"""
    try:
        if project_id in active_projects:
            del active_projects[project_id]
            logger.info(f"清理项目: {project_id}")

        return {"project_id": project_id, "status": "已清理"}

    except Exception as e:
        logger.error(f"项目清理失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")


@ai_company_router.get("/health")
async def health_check() -> Dict:
    """健康检查"""
    try:
        return {
            "status": "healthy",
            "service": "ai_company",
            "version": "1.0.0",
            "available_stages": 5,
            "implemented_stages": 2,  # 需求分析 + 架构设计
            "active_projects_count": len(active_projects),
            "capabilities": [
                "需求分析智能体团队 ✅",
                "架构设计智能体团队 ✅",
                "编码实现智能体团队 🔄",
                "测试部署智能体团队 📋",
                "智能体群协作 📋",
            ],
        }

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {"status": "unhealthy", "error": str(e)}
