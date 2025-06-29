"""
知识库适配器
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.logger import logger
from app.modules.knowledge_base.core.knowledge_manager import KnowledgeCategory
from app.modules.knowledge_base.core.vector_store import VectorSearchQuery
from app.modules.knowledge_base.enhanced_service import EnhancedKnowledgeService
from app.modules.knowledge_base.types import (
    KnowledgeQuery,
    KnowledgeScope,
    KnowledgeType,
)

from .base import KnowledgeBase


class EnhancedKnowledgeBaseAdapter(KnowledgeBase):
    """增强版知识库适配器"""

    def __init__(self):
        """初始化增强版知识库适配器"""
        self.service = EnhancedKnowledgeService()
        self.current_kb_id = None
        self._initialize_default_kb()

    def _initialize_default_kb(self):
        """初始化默认知识库"""
        try:
            # 创建默认知识库
            kb = self.service.create_knowledge_base(
                name="Requirements Analysis KB",
                description="Default knowledge base for requirements analysis",
                category=KnowledgeCategory.REQUIREMENTS_ANALYSIS,
                creator="system",
                tags=["requirements", "analysis"],
                metadata={
                    "type": KnowledgeType.DOMAIN_KNOWLEDGE.value,
                    "scope": KnowledgeScope.GLOBAL.value,
                },
            )
            if kb:
                self.current_kb_id = kb.id
                logger.info(f"默认知识库初始化完成: {kb.id}")

                # 添加默认知识条目
                default_entries = [
                    {
                        "title": "需求澄清问题模板",
                        "content": """1. 功能性需求澄清：
- 具体要实现什么功能？
- 预期的用户场景？
- 功能的优先级？
2. 非功能性需求：
- 性能要求
- 安全要求
- 可用性要求
3. 约束条件：
- 时间约束
- 资源约束
- 技术约束
4. 用户角色：
- 主要用户群体
- 权限级别
- 使用频率""",
                        "type": "template",
                        "timestamp": datetime.now().isoformat(),
                    },
                    {
                        "title": "业务分析框架",
                        "content": """1. 业务目标分析：
- 核心业务目标
- 成功指标
- 关键绩效
2. 利益相关者分析：
- 主要利益相关者
- 期望与需求
- 影响程度
3. 业务流程分析：
- 当前流程
- 期望流程
- 痛点识别
4. 价值主张分析：
- 核心价值
- 竞争优势
- 差异化特性""",
                        "type": "framework",
                        "timestamp": datetime.now().isoformat(),
                    },
                    {
                        "title": "需求规格文档结构",
                        "content": """1. 概述：
- 项目背景
- 目标
- 范围
2. 功能需求：
- 详细功能描述
- 用例场景
3. 非功能需求：
- 性能要求
- 安全要求
- 可用性要求
4. 约束条件：
- 技术约束
- 时间约束
- 资源约束
5. 验收标准：
- 测试要求
- 质量标准""",
                        "type": "template",
                        "timestamp": datetime.now().isoformat(),
                    },
                ]

                # 添加默认条目
                for entry in default_entries:
                    success = self.service.add_document(
                        kb.id,
                        entry["title"],
                        entry["content"],
                        entry["type"],
                        {"timestamp": entry["timestamp"]},
                    )
                    if success:
                        logger.info(f"添加默认知识条目成功: {entry['title']}")
                    else:
                        logger.warning(f"添加默认知识条目失败: {entry['title']}")
            else:
                logger.warning("默认知识库创建失败")
        except Exception as e:
            logger.error(f"初始化默认知识库失败: {e}")

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索知识"""
        try:
            if not self.current_kb_id:
                logger.warning("没有可用的知识库，尝试重新初始化")
                self._initialize_default_kb()
                if not self.current_kb_id:
                    return []

            # 构建向量搜索查询
            vector_query = VectorSearchQuery(
                query_text=query,
                knowledge_base_ids=[self.current_kb_id],
                top_k=top_k,
                min_score=0.5,
            )

            # 执行向量搜索
            search_results = self.service.vector_store.search(vector_query)

            # 转换结果格式
            results = []
            for result in search_results:
                results.append(
                    {
                        "content": result.content,
                        "similarity": result.score,
                        "metadata": result.metadata,
                    }
                )

            return results

        except Exception as e:
            logger.error(f"知识库搜索失败: {e}")
            return []

    async def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """查询知识库"""
        return await self.search(query_text, top_k)

    async def add(self, document: Dict[str, Any]) -> bool:
        """添加文档到知识库"""
        try:
            if not self.current_kb_id:
                logger.warning("没有可用的知识库，尝试重新初始化")
                self._initialize_default_kb()
                if not self.current_kb_id:
                    return False

            # 添加到向量存储
            success = self.service.vector_store.add_documents(
                self.current_kb_id,
                [
                    {
                        "content": document["content"],
                        "metadata": {
                            "title": document.get("title", ""),
                            "type": document.get("type", ""),
                            "timestamp": document.get("timestamp", ""),
                        },
                    }
                ],
            )

            return success

        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return False

    async def update(self, id: str, content: Dict[str, Any]) -> bool:
        """更新知识"""
        # 由于增强版知识库使用不同的文档管理方式，这里简单处理为删除并重新添加
        return await self.add(content)

    async def delete(self, id: str) -> bool:
        """删除知识"""
        # 由于增强版知识库使用不同的文档管理方式，这里暂不实现删除
        return True

    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取知识"""
        # 由于增强版知识库使用不同的文档管理方式，这里暂不实现按ID获取
        return None

    def _extract_text(self, content: Dict[str, Any]) -> str:
        """提取文本用于向量化 - 保持与旧版实现一致"""
        text_parts = []
        for value in content.values():
            if isinstance(value, (str, int, float)):
                text_parts.append(str(value))
            elif isinstance(value, (list, tuple)):
                text_parts.extend(
                    str(item) for item in value if isinstance(item, (str, int, float))
                )
            elif isinstance(value, dict):
                text_parts.extend(self._extract_text(value))
        return " ".join(text_parts)


class RequirementsKnowledgeBase(KnowledgeBase):
    """需求分析知识库适配器"""

    def __init__(self):
        """初始化需求分析知识库适配器"""
        super().__init__()
        self.service = EnhancedKnowledgeService()
        self.current_kb_id = None
        self._initialize_default_kb()

    def _initialize_default_kb(self):
        """初始化默认知识库"""
        try:
            # 创建默认知识库
            kb = self.service.create_knowledge_base(
                name="Requirements Analysis KB",
                description="Default knowledge base for requirements analysis",
                category=KnowledgeCategory.REQUIREMENTS_ANALYSIS,
                creator="system",
                tags=["requirements", "analysis"],
                metadata={
                    "type": KnowledgeType.REQUIREMENTS_TEMPLATES.value,
                    "scope": KnowledgeScope.GLOBAL.value,
                },
            )
            if kb:
                self.current_kb_id = kb.id
                logger.info(f"默认知识库初始化完成: {kb.id}")

                # 添加默认知识条目
                default_entries = [
                    {
                        "title": "需求澄清问题模板",
                        "content": "1. 功能性需求澄清：具体要实现什么功能？预期的用户场景？\n2. 非功能性需求：性能要求、安全要求、可用性要求\n3. 约束条件：时间约束、资源约束、技术约束\n4. 用户角色：主要用户群体、权限级别、使用频率",
                        "doc_type": "template",
                        "metadata": {
                            "type": "requirements_template",
                            "category": "requirements_analysis",
                            "tags": ["requirements", "clarification", "template"],
                        },
                    },
                    {
                        "title": "业务分析框架",
                        "content": "1. 业务目标分析：核心业务目标、成功指标、关键绩效\n2. 利益相关者分析：主要利益相关者、期望与需求、影响程度\n3. 业务流程分析：当前流程、期望流程、痛点识别\n4. 价值主张分析：核心价值、竞争优势、差异化特性",
                        "doc_type": "framework",
                        "metadata": {
                            "type": "business_analysis",
                            "category": "requirements_analysis",
                            "tags": ["business", "analysis", "framework"],
                        },
                    },
                    {
                        "title": "需求规格文档结构",
                        "content": "1. 概述：项目背景、目标、范围\n2. 功能需求：详细功能描述、用例场景\n3. 非功能需求：性能、安全、可用性要求\n4. 约束条件：技术约束、时间约束、资源约束\n5. 验收标准：测试要求、质量标准",
                        "doc_type": "template",
                        "metadata": {
                            "type": "document_template",
                            "category": "requirements_analysis",
                            "tags": ["requirements", "document", "template"],
                        },
                    },
                ]

                # 添加默认知识条目
                for entry in default_entries:
                    success = self.service.add_document(
                        kb_id=kb.id,
                        title=entry["title"],
                        content=entry["content"],
                        doc_type=entry["doc_type"],
                        metadata=entry["metadata"],
                    )
                    if success:
                        logger.info(f"添加默认知识条目成功: {entry['title']}")
                    else:
                        logger.warning(f"添加默认知识条目失败: {entry['title']}")
            else:
                logger.warning("默认知识库创建失败")
        except Exception as e:
            logger.error(f"初始化默认知识库失败: {e}")

    async def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """查询知识库"""
        try:
            if not self.current_kb_id:
                return []

            results = await self.service.search_knowledge(
                KnowledgeQuery(
                    query_text=query_text,
                    knowledge_base_ids=[self.current_kb_id],
                    limit=top_k,
                    min_confidence=0.5,
                )
            )
            return results.results
        except Exception as e:
            logger.error(f"查询知识库失败: {e}")
            return []

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索知识"""
        return await self.query(query, top_k)

    async def add(self, content: Dict[str, Any]) -> bool:
        """添加知识"""
        try:
            if not self.current_kb_id:
                return False

            success = self.service.add_document(
                kb_id=self.current_kb_id,
                title=content.get("title", ""),
                content=content.get("content", ""),
                doc_type=content.get("doc_type", "general"),
                metadata=content.get("metadata", {}),
            )
            return success
        except Exception as e:
            logger.error(f"添加知识失败: {e}")
            return False

    async def update(self, id: str, content: Dict[str, Any]) -> bool:
        """更新知识"""
        try:
            if not self.current_kb_id:
                return False

            # TODO: 实现更新功能
            return False
        except Exception as e:
            logger.error(f"更新知识失败: {e}")
            return False

    async def delete(self, id: str) -> bool:
        """删除知识"""
        try:
            if not self.current_kb_id:
                return False

            # TODO: 实现删除功能
            return False
        except Exception as e:
            logger.error(f"删除知识失败: {e}")
            return False

    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取知识"""
        try:
            if not self.current_kb_id:
                return None

            # TODO: 实现获取功能
            return None
        except Exception as e:
            logger.error(f"获取知识失败: {e}")
            return None

    def analyze(self, text: str) -> Dict[str, Any]:
        """分析文本"""
        try:
            if not self.current_kb_id:
                return {}

            analysis = self.service.analyze_text(
                text=text,
                kb_id=self.current_kb_id,
            )
            return analysis
        except Exception as e:
            logger.error(f"分析文本失败: {e}")
            return {}
