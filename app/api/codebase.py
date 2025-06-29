"""
代码库管理API - API层

职责：
1. 定义代码库管理和分析的REST API接口
2. 处理HTTP请求和响应
3. 参数验证和错误处理
4. 调用modules/codebase中的服务实现业务逻辑

架构关系：
- 本文件属于API层，负责接口定义和请求处理
- 核心业务逻辑在modules/codebase/中实现
- 通过CodebaseManager类调用底层功能

这种分层设计使得：
- API接口与业务逻辑分离
- 业务逻辑可以独立测试和维护
- 接口变更不影响核心功能实现
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

from app.modules.codebase.manager import CodebaseManager
from app.modules.codebase.types import CodeSearchQuery, ComponentType


# 请求模型
class CreateCodebaseRequest(BaseModel):
    """创建代码库请求"""

    name: str = Field(..., description="代码库名称")
    description: str = Field(..., description="代码库描述")
    root_path: str = Field(..., description="代码库根路径")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")
    language_primary: Optional[str] = Field(default=None, description="主要编程语言")
    metadata: Optional[Dict] = Field(default=None, description="元数据")
    auto_analyze: bool = Field(default=True, description="是否自动分析")


class UpdateCodebaseRequest(BaseModel):
    """更新代码库请求"""

    name: Optional[str] = Field(default=None, description="代码库名称")
    description: Optional[str] = Field(default=None, description="代码库描述")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")
    language_primary: Optional[str] = Field(default=None, description="主要编程语言")
    metadata: Optional[Dict] = Field(default=None, description="元数据")


class CodeSearchRequest(BaseModel):
    """代码搜索请求"""

    query_text: str = Field(..., description="搜索文本")
    codebase_ids: List[str] = Field(..., description="代码库ID列表")
    component_types: Optional[List[str]] = Field(
        default=None, description="组件类型列表"
    )
    file_patterns: Optional[List[str]] = Field(default=None, description="文件模式列表")
    exclude_patterns: Optional[List[str]] = Field(
        default=None, description="排除模式列表"
    )
    languages: Optional[List[str]] = Field(default=None, description="编程语言列表")
    max_results: int = Field(default=50, description="最大结果数")
    include_content: bool = Field(default=True, description="是否包含内容")


class WorkloadEstimationRequest(BaseModel):
    """工作量估算请求"""

    codebase_id: str = Field(..., description="代码库ID")
    task_description: str = Field(default="", description="任务描述")


# 响应模型
class CodebaseInfoResponse(BaseModel):
    """代码库信息响应"""

    id: str
    name: str
    description: str
    root_path: str
    created_at: str
    updated_at: str
    tags: List[str]
    language_primary: Optional[str]
    size_mb: float
    metadata: Dict


class AnalysisResultResponse(BaseModel):
    """分析结果响应"""

    codebase_id: str
    analysis_time: str
    tech_stacks: List[Dict]
    components_count: int
    similarities_count: int
    metrics: Dict
    file_count: int
    total_lines: int
    languages: Dict[str, int]
    estimated_effort_days: float
    reusability_score: float
    suggestions: List[str]


# 创建路由
router = APIRouter(prefix="/api/codebase", tags=["代码库管理"])

# 初始化管理器
codebase_manager = CodebaseManager()


@router.post("/create", response_model=Dict)
async def create_codebase(request: CreateCodebaseRequest):
    """创建新的代码库"""
    try:
        codebase = codebase_manager.create_codebase(
            name=request.name,
            description=request.description,
            root_path=request.root_path,
            tags=request.tags,
            language_primary=request.language_primary,
            metadata=request.metadata,
            auto_analyze=request.auto_analyze,
        )

        if not codebase:
            raise HTTPException(status_code=400, detail="代码库创建失败")

        return {
            "success": True,
            "message": "代码库创建成功",
            "codebase_id": codebase.id,
            "codebase": {
                "id": codebase.id,
                "name": codebase.name,
                "description": codebase.description,
                "root_path": codebase.root_path,
                "created_at": codebase.created_at.isoformat(),
                "updated_at": codebase.updated_at.isoformat(),
                "tags": codebase.tags,
                "language_primary": codebase.language_primary,
                "size_mb": codebase.size_mb,
                "metadata": codebase.metadata,
            },
        }

    except Exception as e:
        logger.error(f"创建代码库失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建代码库失败: {str(e)}")


@router.get("/list", response_model=Dict)
async def list_codebases(
    tags: Optional[str] = Query(
        default=None, description="筛选标签，多个标签用逗号分隔"
    )
):
    """获取代码库列表"""
    try:
        tag_list = tags.split(",") if tags else None
        codebases = codebase_manager.list_codebases(tags=tag_list)

        return {
            "success": True,
            "total": len(codebases),
            "codebases": [
                {
                    "id": cb.id,
                    "name": cb.name,
                    "description": cb.description,
                    "root_path": cb.root_path,
                    "created_at": cb.created_at.isoformat(),
                    "updated_at": cb.updated_at.isoformat(),
                    "tags": cb.tags,
                    "language_primary": cb.language_primary,
                    "size_mb": cb.size_mb,
                    "metadata": cb.metadata,
                }
                for cb in codebases
            ],
        }

    except Exception as e:
        logger.error(f"获取代码库列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取代码库列表失败: {str(e)}")


@router.get("/{codebase_id}", response_model=Dict)
async def get_codebase(codebase_id: str):
    """获取代码库详情"""
    try:
        codebase = codebase_manager.get_codebase(codebase_id)
        if not codebase:
            raise HTTPException(status_code=404, detail="代码库不存在")

        return {
            "success": True,
            "codebase": {
                "id": codebase.id,
                "name": codebase.name,
                "description": codebase.description,
                "root_path": codebase.root_path,
                "created_at": codebase.created_at.isoformat(),
                "updated_at": codebase.updated_at.isoformat(),
                "tags": codebase.tags,
                "language_primary": codebase.language_primary,
                "size_mb": codebase.size_mb,
                "metadata": codebase.metadata,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取代码库详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取代码库详情失败: {str(e)}")


@router.put("/{codebase_id}", response_model=Dict)
async def update_codebase(codebase_id: str, request: UpdateCodebaseRequest):
    """更新代码库信息"""
    try:
        updates = {k: v for k, v in request.dict().items() if v is not None}
        codebase = codebase_manager.update_codebase(codebase_id, **updates)

        if not codebase:
            raise HTTPException(status_code=404, detail="代码库不存在")

        return {
            "success": True,
            "message": "代码库更新成功",
            "codebase": {
                "id": codebase.id,
                "name": codebase.name,
                "description": codebase.description,
                "root_path": codebase.root_path,
                "created_at": codebase.created_at.isoformat(),
                "updated_at": codebase.updated_at.isoformat(),
                "tags": codebase.tags,
                "language_primary": codebase.language_primary,
                "size_mb": codebase.size_mb,
                "metadata": codebase.metadata,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新代码库失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新代码库失败: {str(e)}")


@router.delete("/{codebase_id}", response_model=Dict)
async def delete_codebase(codebase_id: str):
    """删除代码库"""
    try:
        success = codebase_manager.delete_codebase(codebase_id)
        if not success:
            raise HTTPException(status_code=404, detail="代码库不存在")

        return {"success": True, "message": "代码库删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除代码库失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除代码库失败: {str(e)}")


@router.post("/{codebase_id}/analyze", response_model=Dict)
async def analyze_codebase(codebase_id: str):
    """分析代码库"""
    try:
        result = codebase_manager.analyze_codebase(codebase_id)
        if not result:
            raise HTTPException(status_code=400, detail="代码库分析失败")

        return {
            "success": True,
            "message": "代码库分析完成",
            "analysis": {
                "codebase_id": result.codebase_id,
                "analysis_time": result.analysis_time.isoformat(),
                "tech_stacks": [
                    {
                        "name": ts.name,
                        "version": ts.version,
                        "type": ts.type.value,
                        "confidence": ts.confidence,
                        "description": ts.description,
                        "used_files": ts.used_files,
                    }
                    for ts in result.tech_stacks
                ],
                "components_count": len(result.components),
                "similarities_count": len(result.similarities),
                "metrics": {
                    "lines_of_code": result.metrics.lines_of_code,
                    "lines_of_comments": result.metrics.lines_of_comments,
                    "cyclomatic_complexity": result.metrics.cyclomatic_complexity,
                    "maintainability_index": result.metrics.maintainability_index,
                    "code_duplication_ratio": result.metrics.code_duplication_ratio,
                    "test_coverage": result.metrics.test_coverage,
                    "technical_debt_ratio": result.metrics.technical_debt_ratio,
                },
                "file_count": result.file_count,
                "total_lines": result.total_lines,
                "languages": result.languages,
                "estimated_effort_days": result.estimated_effort_days,
                "reusability_score": result.reusability_score,
                "suggestions": result.suggestions,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"代码库分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"代码库分析失败: {str(e)}")


@router.get("/{codebase_id}/analysis", response_model=Dict)
async def get_analysis_result(codebase_id: str):
    """获取分析结果"""
    try:
        result = codebase_manager.get_analysis_result(codebase_id)
        if not result:
            raise HTTPException(status_code=404, detail="分析结果不存在")

        return {
            "success": True,
            "analysis": {
                "codebase_id": result.codebase_id,
                "analysis_time": result.analysis_time.isoformat(),
                "tech_stacks": [
                    {
                        "name": ts.name,
                        "version": ts.version,
                        "type": ts.type.value,
                        "confidence": ts.confidence,
                        "description": ts.description,
                        "used_files": ts.used_files,
                    }
                    for ts in result.tech_stacks
                ],
                "components": [
                    {
                        "name": comp.name,
                        "type": comp.type.value,
                        "file_path": comp.file_path,
                        "start_line": comp.start_line,
                        "end_line": comp.end_line,
                        "complexity": comp.complexity.value,
                        "dependencies": comp.dependencies,
                        "description": comp.description,
                        "parameters": comp.parameters,
                        "return_type": comp.return_type,
                    }
                    for comp in result.components
                ],
                "similarities": [
                    {
                        "file1": sim.file1,
                        "file2": sim.file2,
                        "similarity_score": sim.similarity_score,
                        "similar_components": sim.similar_components,
                        "similarity_type": sim.similarity_type,
                        "details": sim.details,
                    }
                    for sim in result.similarities
                ],
                "metrics": {
                    "lines_of_code": result.metrics.lines_of_code,
                    "lines_of_comments": result.metrics.lines_of_comments,
                    "cyclomatic_complexity": result.metrics.cyclomatic_complexity,
                    "maintainability_index": result.metrics.maintainability_index,
                    "code_duplication_ratio": result.metrics.code_duplication_ratio,
                    "test_coverage": result.metrics.test_coverage,
                    "technical_debt_ratio": result.metrics.technical_debt_ratio,
                },
                "file_count": result.file_count,
                "total_lines": result.total_lines,
                "languages": result.languages,
                "estimated_effort_days": result.estimated_effort_days,
                "reusability_score": result.reusability_score,
                "suggestions": result.suggestions,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分析结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分析结果失败: {str(e)}")


@router.get("/{codebase_id}/structure", response_model=Dict)
async def analyze_structure(codebase_id: str):
    """分析代码结构"""
    try:
        structure = codebase_manager.analyze_structure(codebase_id)
        if not structure:
            raise HTTPException(status_code=404, detail="代码库不存在或结构分析失败")

        return {"success": True, "structure": structure}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"结构分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"结构分析失败: {str(e)}")


@router.get("/{codebase_id}/similarity", response_model=Dict)
async def analyze_similarity(codebase_id: str):
    """分析代码相似度"""
    try:
        similarities = codebase_manager.analyze_similarity(codebase_id)

        return {
            "success": True,
            "total": len(similarities),
            "similarities": [
                {
                    "file1": sim.file1,
                    "file2": sim.file2,
                    "similarity_score": sim.similarity_score,
                    "similar_components": sim.similar_components,
                    "similarity_type": sim.similarity_type,
                    "details": sim.details,
                }
                for sim in similarities
            ],
        }

    except Exception as e:
        logger.error(f"相似度分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"相似度分析失败: {str(e)}")


@router.post("/search", response_model=Dict)
async def search_components(request: CodeSearchRequest):
    """搜索代码组件"""
    try:
        # 转换组件类型
        component_types = None
        if request.component_types:
            component_types = [ComponentType(ct) for ct in request.component_types]

        query = CodeSearchQuery(
            query_text=request.query_text,
            codebase_ids=request.codebase_ids,
            component_types=component_types,
            file_patterns=request.file_patterns or [],
            exclude_patterns=request.exclude_patterns or [],
            languages=request.languages or [],
            max_results=request.max_results,
            include_content=request.include_content,
        )

        results = codebase_manager.search_components(query)

        return {
            "success": True,
            "total": len(results),
            "results": [
                {
                    "component": {
                        "name": result.component.name,
                        "type": result.component.type.value,
                        "file_path": result.component.file_path,
                        "start_line": result.component.start_line,
                        "end_line": result.component.end_line,
                        "complexity": result.component.complexity.value,
                        "description": result.component.description,
                        "parameters": result.component.parameters,
                        "return_type": result.component.return_type,
                    },
                    "codebase_id": result.codebase_id,
                    "relevance_score": result.relevance_score,
                    "content_snippet": result.content_snippet,
                    "highlights": result.highlights,
                }
                for result in results
            ],
        }

    except Exception as e:
        logger.error(f"代码搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"代码搜索失败: {str(e)}")


@router.post("/estimate-workload", response_model=Dict)
async def estimate_workload(request: WorkloadEstimationRequest):
    """估算工作量"""
    try:
        estimation = codebase_manager.estimate_workload(
            codebase_id=request.codebase_id,
            task_description=request.task_description,
        )

        if not estimation:
            raise HTTPException(status_code=404, detail="代码库不存在或分析结果不存在")

        return {
            "success": True,
            "estimation": {
                "total_days": estimation.total_days,
                "breakdown": estimation.breakdown,
                "confidence": estimation.confidence,
                "assumptions": estimation.assumptions,
                "risks": estimation.risks,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"工作量估算失败: {e}")
        raise HTTPException(status_code=500, detail=f"工作量估算失败: {str(e)}")


@router.get("/statistics", response_model=Dict)
async def get_statistics():
    """获取统计信息"""
    try:
        stats = codebase_manager.get_statistics()
        tech_stack_distribution = codebase_manager.get_tech_stack_distribution()
        complexity_distribution = codebase_manager.get_complexity_distribution()

        return {
            "success": True,
            "statistics": {
                **stats,
                "tech_stack_distribution": tech_stack_distribution,
                "complexity_distribution": complexity_distribution,
            },
        }

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.post("/create-sample", response_model=Dict)
async def create_sample_codebase():
    """创建示例代码库（用于测试）"""
    try:
        # 使用当前项目作为示例
        import os

        current_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        codebase = codebase_manager.create_codebase(
            name="OpenManus示例代码库",
            description="OpenManus项目的示例代码库，用于测试代码分析功能",
            root_path=current_path,
            tags=["python", "fastapi", "ai", "需求分析"],
            language_primary="python",
            metadata={"source": "sample", "project_type": "web_application"},
            auto_analyze=True,
        )

        if not codebase:
            raise HTTPException(status_code=400, detail="示例代码库创建失败")

        return {
            "success": True,
            "message": "示例代码库创建成功",
            "codebase_id": codebase.id,
            "note": "分析可能需要一些时间，请稍后查看分析结果",
        }

    except Exception as e:
        logger.error(f"创建示例代码库失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建示例代码库失败: {str(e)}")
