"""
知识库管理API接口 - API层

职责：
1. 定义知识库管理的REST API接口
2. 处理HTTP请求和响应
3. 参数验证和错误处理
4. 调用modules/knowledge_base中的服务实现业务逻辑

架构关系：
- 本文件属于API层，负责接口定义和请求处理
- 核心业务逻辑在modules/knowledge_base/中实现
- 通过EnhancedKnowledgeService类调用底层功能

这种分层设计使得：
- API接口与业务逻辑分离
- 业务逻辑可以独立测试和维护
- 接口变更不影响核心功能实现
"""

import asyncio
import os
import tempfile
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from loguru import logger
from pydantic import BaseModel, Field

from app.modules.knowledge_base.core.knowledge_manager import KnowledgeCategory
from app.modules.knowledge_base.enhanced_service import EnhancedKnowledgeService
from app.modules.knowledge_base.types import KnowledgeQuery

# 初始化知识库服务
knowledge_service = EnhancedKnowledgeService()

# 创建路由
router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


# ==================== 请求/响应模型 ====================


class CreateKnowledgeBaseRequest(BaseModel):
    """创建知识库请求"""

    name: str = Field(..., description="知识库名称")
    description: str = Field(..., description="知识库描述")
    category: str = Field(..., description="知识库分类")
    creator: str = Field(default="user", description="创建者")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")


class UpdateKnowledgeBaseRequest(BaseModel):
    """更新知识库请求"""

    name: Optional[str] = Field(default=None, description="新名称")
    description: Optional[str] = Field(default=None, description="新描述")
    tags: Optional[List[str]] = Field(default=None, description="新标签")


class KnowledgeSearchRequest(BaseModel):
    """知识搜索请求"""

    query_text: str = Field(..., description="搜索文本")
    knowledge_base_ids: Optional[List[str]] = Field(
        default=None, description="指定知识库ID列表"
    )
    limit: int = Field(default=10, description="返回结果数量")
    min_confidence: float = Field(default=0.0, description="最小置信度")


class StandardResponse(BaseModel):
    """标准响应格式"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[dict] = Field(default=None, description="响应数据")


# ==================== 知识库管理接口 ====================


@router.post("/knowledge-bases", response_model=StandardResponse)
async def create_knowledge_base(request: CreateKnowledgeBaseRequest):
    """创建知识库"""
    try:
        # 验证分类
        try:
            category = KnowledgeCategory(request.category)
        except ValueError:
            available_categories = [cat.value for cat in KnowledgeCategory]
            raise HTTPException(
                status_code=400,
                detail=f"无效的知识库分类。可用分类: {available_categories}",
            )

        # 创建知识库
        kb = knowledge_service.create_knowledge_base(
            name=request.name,
            description=request.description,
            category=category,
            creator=request.creator,
            tags=request.tags,
        )

        if not kb:
            raise HTTPException(status_code=500, detail="知识库创建失败")

        return StandardResponse(
            success=True,
            message="知识库创建成功",
            data={
                "id": kb.id,
                "name": kb.name,
                "category": kb.category.value,
                "created_at": kb.created_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建知识库失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建知识库失败: {str(e)}")


@router.get("/knowledge-bases", response_model=StandardResponse)
async def list_knowledge_bases(
    category: Optional[str] = None, active_only: bool = True
):
    """列出知识库"""
    try:
        # 处理分类过滤
        category_filter = None
        if category:
            try:
                category_filter = KnowledgeCategory(category)
            except ValueError:
                available_categories = [cat.value for cat in KnowledgeCategory]
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的知识库分类。可用分类: {available_categories}",
                )

        # 获取知识库列表
        knowledge_bases = knowledge_service.list_knowledge_bases(
            category=category_filter, active_only=active_only
        )

        return StandardResponse(
            success=True,
            message="获取知识库列表成功",
            data={"knowledge_bases": knowledge_bases, "total": len(knowledge_bases)},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识库列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识库列表失败: {str(e)}")


@router.get("/knowledge-bases/{kb_id}", response_model=StandardResponse)
async def get_knowledge_base(kb_id: str):
    """获取知识库详情"""
    try:
        kb_info = knowledge_service.get_knowledge_base(kb_id)

        if not kb_info:
            raise HTTPException(status_code=404, detail="知识库不存在")

        return StandardResponse(
            success=True, message="获取知识库详情成功", data=kb_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识库详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识库详情失败: {str(e)}")


@router.put("/knowledge-bases/{kb_id}", response_model=StandardResponse)
async def update_knowledge_base(kb_id: str, request: UpdateKnowledgeBaseRequest):
    """更新知识库"""
    try:
        success = knowledge_service.update_knowledge_base(
            kb_id=kb_id,
            name=request.name,
            description=request.description,
            tags=request.tags,
        )

        if not success:
            raise HTTPException(status_code=404, detail="知识库不存在或更新失败")

        return StandardResponse(
            success=True, message="知识库更新成功", data={"kb_id": kb_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新知识库失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新知识库失败: {str(e)}")


@router.delete("/knowledge-bases/{kb_id}", response_model=StandardResponse)
async def delete_knowledge_base(kb_id: str, hard_delete: bool = False):
    """删除知识库"""
    try:
        success = knowledge_service.delete_knowledge_base(kb_id, hard_delete)

        if not success:
            raise HTTPException(status_code=404, detail="知识库不存在或删除失败")

        delete_type = "硬删除" if hard_delete else "软删除"
        return StandardResponse(
            success=True,
            message=f"知识库{delete_type}成功",
            data={"kb_id": kb_id, "delete_type": delete_type},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除知识库失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除知识库失败: {str(e)}")


# ==================== 文档管理接口 ====================


@router.post("/knowledge-bases/{kb_id}/documents", response_model=StandardResponse)
async def upload_document(
    kb_id: str, file: UploadFile = File(...), title: Optional[str] = Form(None)
):
    """上传文档到知识库"""
    try:
        # 验证知识库存在
        kb_info = knowledge_service.get_knowledge_base(kb_id)
        if not kb_info:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f"_{file.filename}"
        ) as temp_file:
            # 保存上传的文件
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # 处理文档
            result = await knowledge_service.upload_document(
                kb_id=kb_id, file_path=temp_file_path, title=title or file.filename
            )

            if not result:
                raise HTTPException(status_code=500, detail="文档处理失败")

            return StandardResponse(success=True, message="文档上传成功", data=result)

        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传文档失败: {str(e)}")


# ==================== 知识检索接口 ====================


@router.post("/search", response_model=StandardResponse)
async def search_knowledge(request: KnowledgeSearchRequest):
    """搜索知识"""
    try:
        # 构建查询对象
        query = KnowledgeQuery(
            query_text=request.query_text,
            knowledge_base_ids=request.knowledge_base_ids,
            limit=request.limit,
            min_confidence=request.min_confidence,
        )

        # 执行搜索
        search_result = await knowledge_service.search_knowledge(query)

        return StandardResponse(
            success=True,
            message="知识搜索成功",
            data={
                "query": search_result.query,
                "results": search_result.results,
                "total_results": search_result.total_results,
                "search_time_ms": search_result.search_time_ms,
            },
        )

    except Exception as e:
        logger.error(f"知识搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"知识搜索失败: {str(e)}")


# ==================== 系统管理接口 ====================


@router.get("/categories", response_model=StandardResponse)
async def get_knowledge_categories():
    """获取可用的知识库分类"""
    try:
        categories = [
            {"value": cat.value, "label": cat.value.replace("_", " ").title()}
            for cat in KnowledgeCategory
        ]

        return StandardResponse(
            success=True, message="获取知识库分类成功", data={"categories": categories}
        )

    except Exception as e:
        logger.error(f"获取知识库分类失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识库分类失败: {str(e)}")


@router.get("/stats", response_model=StandardResponse)
async def get_system_stats():
    """获取系统统计信息"""
    try:
        stats = knowledge_service.get_system_stats()

        return StandardResponse(
            success=True, message="获取系统统计信息成功", data=stats
        )

    except Exception as e:
        logger.error(f"获取系统统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统统计信息失败: {str(e)}")


# ==================== 高级功能接口 ====================


@router.get("/knowledge-bases/{kb_id}/recommendations", response_model=StandardResponse)
async def get_knowledge_recommendations(kb_id: str, context: str, top_k: int = 5):
    """获取知识推荐"""
    try:
        # 验证知识库存在
        kb_info = knowledge_service.get_knowledge_base(kb_id)
        if not kb_info:
            raise HTTPException(status_code=404, detail="知识库不存在")

        # 获取推荐
        recommendations = knowledge_service.get_knowledge_recommendations(
            kb_id=kb_id, context=context, top_k=top_k
        )

        return StandardResponse(
            success=True,
            message="获取知识推荐成功",
            data={
                "recommendations": recommendations,
                "context": context,
                "kb_id": kb_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识推荐失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识推荐失败: {str(e)}")


@router.post("/analysis/gaps", response_model=StandardResponse)
async def analyze_knowledge_gaps(kb_ids: List[str]):
    """分析知识库覆盖缺口"""
    try:
        if not kb_ids:
            raise HTTPException(status_code=400, detail="必须提供至少一个知识库ID")

        # 执行分析
        analysis = knowledge_service.analyze_knowledge_gaps(kb_ids)

        return StandardResponse(
            success=True, message="知识库缺口分析完成", data=analysis
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"知识库缺口分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"知识库缺口分析失败: {str(e)}")


# ==================== 测试接口 ====================


@router.post("/test/sample-data", response_model=StandardResponse)
async def create_sample_data():
    """创建示例数据（用于测试）"""
    try:
        sample_kbs = []

        # 创建示例知识库
        categories_data = [
            (
                "需求分析最佳实践",
                "包含需求分析的方法论、模板和最佳实践",
                KnowledgeCategory.REQUIREMENTS_ANALYSIS,
            ),
            ("系统设计指南", "系统架构设计原则和模式", KnowledgeCategory.SYSTEM_DESIGN),
            ("编码规范", "代码质量和编程规范", KnowledgeCategory.CODING_STANDARDS),
        ]

        for name, desc, category in categories_data:
            kb = knowledge_service.create_knowledge_base(
                name=name,
                description=desc,
                category=category,
                creator="system",
                tags=["sample", "test"],
            )
            if kb:
                sample_kbs.append(
                    {"id": kb.id, "name": kb.name, "category": kb.category.value}
                )

        return StandardResponse(
            success=True,
            message=f"成功创建 {len(sample_kbs)} 个示例知识库",
            data={"sample_knowledge_bases": sample_kbs},
        )

    except Exception as e:
        logger.error(f"创建示例数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建示例数据失败: {str(e)}")
