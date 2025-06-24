"""
协调式需求分析API
提供整合知识库、代码库和需求分析助手的统一接口
"""

from typing import Dict

from fastapi import APIRouter, HTTPException
from loguru import logger

from ..core.requirements_orchestrator import RequirementsOrchestrator
from ..schema import RequirementAnalysisRequest, RequirementAnalysisResponse

router = APIRouter(prefix="/api/v1/orchestrated", tags=["协调式需求分析"])

# 全局协调器实例
orchestrator = RequirementsOrchestrator()


@router.post("/analyze", response_model=RequirementAnalysisResponse)
async def analyze_requirement_comprehensive(
    request: RequirementAnalysisRequest,
) -> RequirementAnalysisResponse:
    """
    综合需求分析
    整合知识库、代码库和需求分析助手的能力，提供全方位的需求分析服务

    Args:
        request: 需求分析请求

    Returns:
        RequirementAnalysisResponse: 综合分析结果
    """
    try:
        logger.info(f"接收到协调式需求分析请求: {request.content[:50]}...")

        # 调用协调器进行综合分析
        response = await orchestrator.analyze_requirement_comprehensive(request)

        logger.success(f"协调式需求分析完成，置信度: {response.confidence_score}")
        return response

    except Exception as e:
        logger.error(f"协调式需求分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"需求分析失败: {str(e)}")


@router.get("/collaboration/status")
async def get_collaboration_status() -> Dict:
    """
    获取三模块协作状态

    Returns:
        Dict: 协作状态信息
    """
    try:
        status = await orchestrator.get_collaboration_status()
        return {"success": True, "data": status, "message": "协作状态获取成功"}
    except Exception as e:
        logger.error(f"获取协作状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取协作状态失败: {str(e)}")


@router.get("/capabilities")
async def get_orchestrator_capabilities() -> Dict:
    """
    获取协调器能力清单

    Returns:
        Dict: 能力清单
    """
    return {
        "success": True,
        "data": {
            "core_capabilities": [
                "智能知识检索与匹配",
                "代码组件分析与复用评估",
                "技术可行性评估",
                "工作量智能估算",
                "需求澄清与优化建议",
                "多模块协作协调",
            ],
            "analysis_stages": [
                {
                    "stage": "上下文收集",
                    "description": "并行收集知识库和代码库相关信息",
                    "outputs": ["相关知识", "相关组件", "技术栈信息"],
                },
                {
                    "stage": "智能澄清",
                    "description": "结合收集的上下文进行需求澄清",
                    "outputs": ["澄清后需求", "澄清问题", "改进建议"],
                },
                {
                    "stage": "可行性评估",
                    "description": "评估技术可行性和工作量",
                    "outputs": ["可行性评分", "工作量估算", "技术风险"],
                },
                {
                    "stage": "智能建议",
                    "description": "基于分析结果生成智能建议",
                    "outputs": ["实施建议", "技术建议", "风险缓解建议"],
                },
            ],
            "integration_features": [
                "知识库语义搜索",
                "代码库智能匹配",
                "模板推荐",
                "组件复用分析",
                "技术栈兼容性评估",
                "多维度置信度计算",
            ],
        },
        "message": "协调器能力清单获取成功",
    }


@router.get("/health")
async def health_check() -> Dict:
    """
    健康检查

    Returns:
        Dict: 健康状态
    """
    try:
        collaboration_status = await orchestrator.get_collaboration_status()

        health_score = 1.0
        issues = []

        # 检查知识库
        if collaboration_status["knowledge_base"]["available"] == 0:
            health_score -= 0.3
            issues.append("知识库为空")

        # 检查代码库
        if collaboration_status["codebase"]["components"] == 0:
            health_score -= 0.3
            issues.append("代码库组件为空")

        # 检查协作健康度
        if collaboration_status["collaboration_health"] == "需要改进":
            health_score -= 0.2
            issues.append("协作模块存在问题")

        status = "healthy"
        if health_score < 0.7:
            status = "degraded"
        if health_score < 0.4:
            status = "unhealthy"

        return {
            "status": status,
            "health_score": round(health_score, 2),
            "collaboration_health": collaboration_status["collaboration_health"],
            "issues": issues,
            "timestamp": collaboration_status.get("analysis_time"),
            "modules": {
                "knowledge_base": collaboration_status["knowledge_base"],
                "codebase": collaboration_status["codebase"],
                "orchestrator": "运行中",
            },
        }

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "health_score": 0.0,
            "error": str(e),
            "timestamp": None,
        }
