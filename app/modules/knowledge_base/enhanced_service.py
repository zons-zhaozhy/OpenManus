"""
增强版知识库服务 - 整合知识管理、文档处理、向量存储
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from .core.document_processor import DocumentProcessor
from .core.knowledge_manager import (
    DocumentType,
    KnowledgeBase,
    KnowledgeCategory,
    KnowledgeDocument,
    KnowledgeManager,
)
from .types import KnowledgeQuery, KnowledgeSearchResponse

# 尝试导入向量存储
try:
    from .core.vector_store import SearchResult, VectorSearchQuery, VectorStore

    VECTOR_STORE_AVAILABLE = True
except ImportError:
    VECTOR_STORE_AVAILABLE = False
    logger.warning("向量存储功能不可用")


class EnhancedKnowledgeService:
    """增强版知识库服务 - 高规格的知识管理系统"""

    def __init__(self, storage_path: str = "data/knowledge_bases"):
        """
        初始化增强版知识库服务

        Args:
            storage_path: 知识库存储路径
        """
        self.storage_path = storage_path

        # 初始化核心组件
        self.knowledge_manager = KnowledgeManager(storage_path)
        self.document_processor = DocumentProcessor(storage_path)

        # 初始化向量存储
        try:
            self.vector_store = VectorStore(
                storage_path=storage_path,
                embedding_model="paraphrase-multilingual-MiniLM-L12-v2",
            )
            logger.info("向量存储初始化成功")
        except Exception as e:
            logger.error(f"向量存储初始化失败: {e}")
            self.vector_store = None

        logger.info("增强版知识库服务初始化完成")

    # ==================== 知识库管理 ====================

    def create_knowledge_base(
        self,
        name: str,
        description: str,
        category: KnowledgeCategory,
        creator: str = "system",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        type: Optional[str] = None,
    ) -> Optional[KnowledgeBase]:
        """
        创建知识库

        Args:
            name: 知识库名称
            description: 描述
            category: 分类
            creator: 创建者
            tags: 标签
            metadata: 元数据
            type: 知识库类型（可选）

        Returns:
            Optional[KnowledgeBase]: 创建的知识库
        """
        try:
            # 创建知识库
            kb = self.knowledge_manager.create_knowledge_base(
                name=name,
                description=description,
                category=category,
                creator=creator,
                tags=tags,
                metadata=metadata,
            )

            if kb and self.vector_store:
                # 创建对应的向量集合
                success = self.vector_store.create_knowledge_base_collection(
                    kb.id, kb.name
                )
                if not success:
                    logger.warning(f"为知识库 {kb.id} 创建向量集合失败")
                else:
                    logger.info(f"为知识库 {kb.id} 创建向量集合成功")

            return kb

        except Exception as e:
            logger.error(f"创建知识库失败: {e}")
            return None

    def list_knowledge_bases(
        self,
        category: Optional[KnowledgeCategory] = None,
        tags: Optional[List[str]] = None,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        列出知识库（带统计信息）

        Args:
            category: 分类过滤
            tags: 标签过滤
            active_only: 仅显示活跃的

        Returns:
            List[Dict[str, Any]]: 知识库列表（带统计信息）
        """
        knowledge_bases = self.knowledge_manager.list_knowledge_bases(
            category=category, tags=tags, active_only=active_only
        )

        result = []
        for kb in knowledge_bases:
            # 获取基础统计信息
            stats = self.knowledge_manager.get_knowledge_base_stats(kb.id)

            # 获取向量存储统计信息
            if self.vector_store:
                vector_stats = self.vector_store.get_collection_stats(kb.id)
                stats.update(vector_stats)

            # 组合信息
            kb_info = {
                "id": kb.id,
                "name": kb.name,
                "description": kb.description,
                "category": kb.category.value,
                "creator": kb.creator,
                "version": kb.version,
                "tags": kb.tags,
                "is_active": kb.is_active,
                "created_at": kb.created_at.isoformat(),
                "updated_at": kb.updated_at.isoformat(),
                "stats": stats,
            }
            result.append(kb_info)

        return result

    async def search_knowledge(self, query: KnowledgeQuery) -> KnowledgeSearchResponse:
        """
        搜索知识

        Args:
            query: 搜索查询

        Returns:
            KnowledgeSearchResult: 搜索结果
        """
        if not self.vector_store:
            # 回退到传统搜索
            return await self._fallback_search(query)

        # 使用向量搜索
        vector_query = VectorSearchQuery(
            query_text=query.query_text,
            knowledge_base_ids=query.knowledge_base_ids or [],
            top_k=query.limit,
            min_score=query.min_confidence,
        )

        # 执行混合搜索
        search_results = self.vector_store.hybrid_search(vector_query)

        # 转换结果格式
        results = []
        for result in search_results:
            results.append(
                {
                    "id": result.id,
                    "content": result.content,
                    "score": result.score,
                    "knowledge_base_id": result.knowledge_base_id,
                    "document_id": result.document_id,
                    "metadata": result.metadata,
                }
            )

        return KnowledgeSearchResponse(
            query=query.query_text,
            results=results,
            total_results=len(results),
            search_time_ms=0,  # TODO: 添加实际搜索时间
        )

    async def _fallback_search(self, query: KnowledgeQuery) -> KnowledgeSearchResponse:
        """
        传统搜索（回退方案）

        Args:
            query: 搜索查询

        Returns:
            KnowledgeSearchResult: 搜索结果
        """
        # 简单的关键词匹配搜索
        results = []

        # 如果没有指定知识库，搜索所有活跃的知识库
        if not query.knowledge_base_ids:
            knowledge_bases = self.knowledge_manager.list_knowledge_bases(
                active_only=True
            )
            kb_ids = [kb.id for kb in knowledge_bases]
        else:
            kb_ids = query.knowledge_base_ids

        # 在每个知识库中搜索
        for kb_id in kb_ids:
            kb_results = await self._search_in_knowledge_base(kb_id, query.query_text)
            results.extend(kb_results)

        # 排序并限制结果数量
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        results = results[: query.limit]

        return KnowledgeSearchResponse(
            query=query.query_text,
            results=results,
            total_results=len(results),
            search_time_ms=0,
        )

    async def _search_in_knowledge_base(
        self, kb_id: str, query_text: str
    ) -> List[Dict[str, Any]]:
        """
        在指定知识库中搜索

        Args:
            kb_id: 知识库ID
            query_text: 查询文本

        Returns:
            List[Dict[str, Any]]: 搜索结果
        """
        results = []

        # 搜索文档
        documents_path = Path(self.storage_path) / "documents"
        for doc_file in documents_path.glob(f"{kb_id}_*.json"):
            try:
                with open(doc_file, "r", encoding="utf-8") as f:
                    doc_data = f.read()

                # 简单的关键词匹配
                if query_text.lower() in doc_data.lower():
                    import json

                    doc_info = json.loads(doc_data)

                    # 计算匹配分数（简单方法）
                    score = (
                        doc_data.lower().count(query_text.lower()) / len(doc_data) * 100
                    )

                    results.append(
                        {
                            "id": doc_info.get("id"),
                            "content": doc_info.get("content", "")[:200] + "...",
                            "score": score,
                            "knowledge_base_id": kb_id,
                            "document_id": doc_info.get("id"),
                            "metadata": doc_info.get("metadata", {}),
                        }
                    )
            except Exception as e:
                logger.warning(f"搜索文档失败: {doc_file}, 错误: {e}")

        return results

    def get_knowledge_base(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """
        获取知识库详情

        Args:
            kb_id: 知识库ID

        Returns:
            Optional[Dict[str, Any]]: 知识库详情
        """
        kb = self.knowledge_manager.get_knowledge_base(kb_id)
        if not kb:
            return None

        # 获取统计信息
        stats = self.knowledge_manager.get_knowledge_base_stats(kb_id)
        if self.vector_store:
            vector_stats = self.vector_store.get_collection_stats(kb_id)
            stats.update(vector_stats)

        return {
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "category": kb.category.value,
            "creator": kb.creator,
            "version": kb.version,
            "tags": kb.tags,
            "metadata": kb.metadata,
            "is_active": kb.is_active,
            "created_at": kb.created_at.isoformat(),
            "updated_at": kb.updated_at.isoformat(),
            "stats": stats,
        }

    def update_knowledge_base(
        self,
        kb_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        更新知识库信息

        Args:
            kb_id: 知识库ID
            name: 新名称
            description: 新描述
            tags: 新标签
            metadata: 新元数据

        Returns:
            bool: 更新是否成功
        """
        return self.knowledge_manager.update_knowledge_base(
            kb_id=kb_id,
            name=name,
            description=description,
            tags=tags,
            metadata=metadata,
        )

    def delete_knowledge_base(self, kb_id: str, hard_delete: bool = False) -> bool:
        """
        删除知识库

        Args:
            kb_id: 知识库ID
            hard_delete: 是否硬删除

        Returns:
            bool: 删除是否成功
        """
        success = self.knowledge_manager.delete_knowledge_base(kb_id, hard_delete)

        if success and hard_delete and self.vector_store:
            # 同时删除向量集合
            self.vector_store.delete_knowledge_base_collection(kb_id)

        return success

    async def upload_document(
        self,
        kb_id: str,
        file_path: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        上传文档到知识库

        Args:
            kb_id: 知识库ID
            file_path: 文件路径
            title: 文档标题
            metadata: 元数据

        Returns:
            Optional[Dict[str, Any]]: 上传结果
        """
        # 检查知识库是否存在
        kb = self.knowledge_manager.get_knowledge_base(kb_id)
        if not kb:
            logger.error(f"知识库不存在: {kb_id}")
            return None

        # 处理文档
        document = await self.document_processor.upload_document(
            file_path=file_path, knowledge_base_id=kb_id, title=title, metadata=metadata
        )

        if not document:
            return None

        # 添加到向量存储
        if self.vector_store:
            # 将文档分割成块进行向量化
            chunks = self._split_document_into_chunks(document.content)

            vector_docs = []
            for i, chunk in enumerate(chunks):
                vector_docs.append(
                    {
                        "id": f"{document.id}_chunk_{i}",
                        "content": chunk,
                        "metadata": {
                            "document_id": document.id,
                            "document_title": document.title,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "document_type": document.document_type.value,
                            **document.metadata,
                        },
                    }
                )

            if vector_docs:
                self.vector_store.add_documents(kb_id, vector_docs)

        # 返回结果
        return {
            "document_id": document.id,
            "title": document.title,
            "document_type": document.document_type.value,
            "file_size": document.file_size,
            "knowledge_points_count": len(document.knowledge_points),
            "keywords_count": len(document.keywords),
            "summary": document.summary,
            "created_at": document.created_at.isoformat(),
        }

    def _split_document_into_chunks(
        self, content: str, chunk_size: int = 500, overlap_size: int = 50
    ) -> List[str]:
        """
        将文档分割成块

        Args:
            content: 文档内容
            chunk_size: 块大小
            overlap_size: 重叠大小

        Returns:
            List[str]: 文档块列表
        """
        if len(content) <= chunk_size:
            return [content]

        chunks = []
        start = 0

        while start < len(content):
            end = start + chunk_size

            # 尝试在句号处分割
            if end < len(content):
                # 寻找最近的句号
                period_pos = content.rfind("。", start, end)
                if period_pos > start:
                    end = period_pos + 1

            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # 计算下一个起始位置
            start = end - overlap_size if end < len(content) else end

        return chunks

    def get_knowledge_recommendations(
        self, kb_id: str, context: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        获取知识推荐

        Args:
            kb_id: 知识库ID
            context: 上下文
            top_k: 推荐数量

        Returns:
            List[Dict[str, Any]]: 推荐结果
        """
        if not self.vector_store:
            return []

        # 使用向量搜索进行推荐
        query = VectorSearchQuery(
            query_text=context, knowledge_base_ids=[kb_id], top_k=top_k, min_score=0.5
        )

        results = self.vector_store.search(query)

        recommendations = []
        for result in results:
            recommendations.append(
                {
                    "id": result.id,
                    "content": result.content[:200] + "...",
                    "relevance_score": result.score,
                    "document_id": result.document_id,
                    "metadata": result.metadata,
                }
            )

        return recommendations

    def analyze_knowledge_gaps(self, kb_ids: List[str]) -> Dict[str, Any]:
        """
        分析知识库覆盖缺口

        Args:
            kb_ids: 知识库ID列表

        Returns:
            Dict[str, Any]: 分析结果
        """
        analysis = {
            "total_knowledge_bases": len(kb_ids),
            "coverage_analysis": {},
            "gap_areas": [],
            "recommendations": [],
        }

        # 分析每个知识库的覆盖范围
        categories_coverage = {}
        for kb_id in kb_ids:
            kb = self.knowledge_manager.get_knowledge_base(kb_id)
            if kb:
                category = kb.category.value
                if category not in categories_coverage:
                    categories_coverage[category] = []
                categories_coverage[category].append(kb_id)

        analysis["coverage_analysis"] = categories_coverage

        # 识别缺口领域
        all_categories = [cat.value for cat in KnowledgeCategory]
        missing_categories = [
            cat for cat in all_categories if cat not in categories_coverage
        ]
        analysis["gap_areas"] = missing_categories

        # 生成建议
        if missing_categories:
            analysis["recommendations"].append(
                f"建议创建以下领域的知识库: {', '.join(missing_categories)}"
            )

        # 分析知识库密度
        low_density_kbs = []
        for kb_id in kb_ids:
            stats = self.knowledge_manager.get_knowledge_base_stats(kb_id)
            if stats.get("document_count", 0) < 5:
                low_density_kbs.append(kb_id)

        if low_density_kbs:
            analysis["recommendations"].append(
                f"以下知识库需要补充更多内容: {', '.join(low_density_kbs)}"
            )

        return analysis

    def get_system_stats(self) -> Dict[str, Any]:
        """
        获取系统统计信息

        Returns:
            Dict[str, Any]: 系统统计
        """
        # 统计知识库
        all_kbs = self.knowledge_manager.list_knowledge_bases(active_only=False)
        active_kbs = self.knowledge_manager.list_knowledge_bases(active_only=True)

        # 统计文档
        documents_path = Path(self.storage_path) / "documents"
        total_documents = len(list(documents_path.glob("*.json")))

        # 统计存储大小
        total_size = sum(
            f.stat().st_size for f in Path(self.storage_path).rglob("*") if f.is_file()
        )

        stats = {
            "knowledge_bases": {
                "total": len(all_kbs),
                "active": len(active_kbs),
                "by_category": {},
            },
            "documents": {"total": total_documents},
            "storage": {
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
            },
            "vector_store": {"available": self.vector_store is not None},
        }

        # 按分类统计知识库
        for kb in active_kbs:
            category = kb.category.value
            stats["knowledge_bases"]["by_category"][category] = (
                stats["knowledge_bases"]["by_category"].get(category, 0) + 1
            )

        return stats

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息（别名方法）

        Returns:
            Dict[str, Any]: 统计信息
        """
        return self.get_system_stats()

    def add_document(
        self,
        kb_id: str,
        title: str,
        content: str,
        doc_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        添加文档到知识库

        Args:
            kb_id: 知识库ID
            title: 文档标题
            content: 文档内容
            doc_type: 文档类型
            metadata: 元数据

        Returns:
            bool: 添加是否成功
        """
        try:
            # 准备文档数据
            doc_id = str(uuid.uuid4())
            doc_metadata = {
                "title": title,
                "type": doc_type,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {}),
            }

            # 添加到向量存储
            success = self.vector_store.add_documents(
                kb_id,
                [
                    {
                        "content": content,
                        "metadata": doc_metadata,
                    }
                ],
            )

            if success:
                logger.info(f"文档添加成功: {title}")
                return True
            else:
                logger.warning(f"文档添加失败: {title}")
                return False

        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return False

    def get_vector_store_diagnostics(self) -> Dict[str, Any]:
        """
        获取向量存储诊断信息

        Returns:
            Dict[str, Any]: 诊断信息
        """
        if not self.vector_store:
            return {
                "status": "unavailable",
                "error": "向量存储未初始化",
            }

        return self.vector_store.get_diagnostic_info()
