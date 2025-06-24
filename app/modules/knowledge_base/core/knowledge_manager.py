"""
高规格知识库管理器
支持用户自定义知识库编目、知识材料上传、自动解析识别知识点
"""

import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from loguru import logger


class DocumentType(Enum):
    """文档类型枚举"""

    PDF = "pdf"
    WORD = "word"
    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"


class KnowledgeCategory(Enum):
    """知识分类枚举"""

    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    SYSTEM_DESIGN = "system_design"
    CODING_STANDARDS = "coding_standards"
    TESTING_GUIDELINES = "testing_guidelines"
    PROJECT_MANAGEMENT = "project_management"
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    TECHNICAL_DOCS = "technical_docs"
    BEST_PRACTICES = "best_practices"


@dataclass
class KnowledgeBase:
    """知识库实体"""

    id: str
    name: str
    description: str
    category: KnowledgeCategory
    version: str
    creator: str
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    metadata: Dict[str, Any]
    is_active: bool = True


@dataclass
class KnowledgeDocument:
    """知识文档实体"""

    id: str
    knowledge_base_id: str
    title: str
    content: str
    document_type: DocumentType
    file_path: Optional[str]
    file_size: int
    checksum: str
    knowledge_points: List[str]
    keywords: List[str]
    summary: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


@dataclass
class KnowledgePoint:
    """知识点实体"""

    id: str
    document_id: str
    content: str
    category: str
    importance_score: float
    context: str
    related_points: List[str]
    created_at: datetime


class KnowledgeManager:
    """高规格知识库管理器"""

    def __init__(self, storage_path: str = "data/knowledge_bases"):
        """
        初始化知识库管理器

        Args:
            storage_path: 知识库存储路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 初始化存储结构
        self.databases_path = self.storage_path / "databases"
        self.documents_path = self.storage_path / "documents"
        self.indexes_path = self.storage_path / "indexes"
        self.uploads_path = self.storage_path / "uploads"

        for path in [
            self.databases_path,
            self.documents_path,
            self.indexes_path,
            self.uploads_path,
        ]:
            path.mkdir(exist_ok=True)

        logger.info(f"知识库管理器初始化完成，存储路径: {self.storage_path}")

    def create_knowledge_base(
        self,
        name: str,
        description: str,
        category: KnowledgeCategory,
        creator: str = "system",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeBase:
        """
        创建新的知识库

        Args:
            name: 知识库名称
            description: 知识库描述
            category: 知识库分类
            creator: 创建者
            tags: 标签列表
            metadata: 元数据

        Returns:
            KnowledgeBase: 创建的知识库对象
        """
        knowledge_base = KnowledgeBase(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            category=category,
            version="1.0.0",
            creator=creator,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=tags or [],
            metadata=metadata or {},
        )

        # 保存到文件
        self._save_knowledge_base(knowledge_base)

        logger.info(f"知识库创建成功: {name} (ID: {knowledge_base.id})")
        return knowledge_base

    def list_knowledge_bases(
        self,
        category: Optional[KnowledgeCategory] = None,
        tags: Optional[List[str]] = None,
        active_only: bool = True,
    ) -> List[KnowledgeBase]:
        """
        列出知识库

        Args:
            category: 过滤分类
            tags: 过滤标签
            active_only: 仅显示活跃的知识库

        Returns:
            List[KnowledgeBase]: 知识库列表
        """
        knowledge_bases = []

        for db_file in self.databases_path.glob("*.json"):
            try:
                with open(db_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                kb = KnowledgeBase(
                    **{
                        **data,
                        "category": KnowledgeCategory(data["category"]),
                        "created_at": datetime.fromisoformat(data["created_at"]),
                        "updated_at": datetime.fromisoformat(data["updated_at"]),
                    }
                )

                # 应用过滤条件
                if active_only and not kb.is_active:
                    continue

                if category and kb.category != category:
                    continue

                if tags and not any(tag in kb.tags for tag in tags):
                    continue

                knowledge_bases.append(kb)

            except Exception as e:
                logger.warning(f"加载知识库失败: {db_file}, 错误: {e}")

        return knowledge_bases

    def get_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBase]:
        """
        获取指定知识库

        Args:
            kb_id: 知识库ID

        Returns:
            Optional[KnowledgeBase]: 知识库对象或None
        """
        db_file = self.databases_path / f"{kb_id}.json"

        if not db_file.exists():
            return None

        try:
            with open(db_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            return KnowledgeBase(
                **{
                    **data,
                    "category": KnowledgeCategory(data["category"]),
                    "created_at": datetime.fromisoformat(data["created_at"]),
                    "updated_at": datetime.fromisoformat(data["updated_at"]),
                }
            )
        except Exception as e:
            logger.error(f"加载知识库失败: {kb_id}, 错误: {e}")
            return None

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
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            return False

        # 更新字段
        if name is not None:
            kb.name = name
        if description is not None:
            kb.description = description
        if tags is not None:
            kb.tags = tags
        if metadata is not None:
            kb.metadata.update(metadata)

        kb.updated_at = datetime.now()

        # 保存更改
        self._save_knowledge_base(kb)

        logger.info(f"知识库更新成功: {kb_id}")
        return True

    def delete_knowledge_base(self, kb_id: str, hard_delete: bool = False) -> bool:
        """
        删除知识库

        Args:
            kb_id: 知识库ID
            hard_delete: 是否硬删除（否则软删除）

        Returns:
            bool: 删除是否成功
        """
        if hard_delete:
            # 硬删除：删除文件
            db_file = self.databases_path / f"{kb_id}.json"
            if db_file.exists():
                db_file.unlink()
                logger.info(f"知识库硬删除成功: {kb_id}")
                return True
        else:
            # 软删除：标记为非活跃
            kb = self.get_knowledge_base(kb_id)
            if kb:
                kb.is_active = False
                kb.updated_at = datetime.now()
                self._save_knowledge_base(kb)
                logger.info(f"知识库软删除成功: {kb_id}")
                return True

        return False

    def _save_knowledge_base(self, kb: KnowledgeBase) -> None:
        """保存知识库到文件"""
        db_file = self.databases_path / f"{kb.id}.json"

        # 转换为可序列化的字典
        data = asdict(kb)
        data["category"] = kb.category.value
        data["created_at"] = kb.created_at.isoformat()
        data["updated_at"] = kb.updated_at.isoformat()

        with open(db_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_knowledge_base_stats(self, kb_id: str) -> Dict[str, Any]:
        """
        获取知识库统计信息

        Args:
            kb_id: 知识库ID

        Returns:
            Dict[str, Any]: 统计信息
        """
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            return {}

        # 统计文档数量
        document_count = len(list(self.documents_path.glob(f"{kb_id}_*.json")))

        # 计算总大小
        total_size = sum(
            doc_file.stat().st_size
            for doc_file in self.documents_path.glob(f"{kb_id}_*.json")
        )

        return {
            "knowledge_base_id": kb_id,
            "name": kb.name,
            "category": kb.category.value,
            "document_count": document_count,
            "total_size_bytes": total_size,
            "created_at": kb.created_at.isoformat(),
            "updated_at": kb.updated_at.isoformat(),
            "tags": kb.tags,
            "is_active": kb.is_active,
        }
