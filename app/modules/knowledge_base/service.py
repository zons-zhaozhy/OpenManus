"""
知识库服务 - 简化实现版本，快速让系统活起来
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.logger import logger

from .types import (
    KnowledgeBase,
    KnowledgeEntry,
    KnowledgeQuery,
    KnowledgeRecommendation,
    KnowledgeSearchResult,
    KnowledgeType,
)


class KnowledgeService:
    """知识库服务 - 核心功能实现"""

    def __init__(self):
        self.knowledge_bases: Dict[str, KnowledgeBase] = {}
        self.knowledge_entries: Dict[str, List[KnowledgeEntry]] = {}
        self.data_dir = Path("data/knowledge_base")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 初始化默认知识库
        self._init_default_knowledge_bases()

    def _init_default_knowledge_bases(self):
        """初始化默认知识库"""
        # 需求分析知识库
        requirements_kb = KnowledgeBase(
            id="requirements_analysis",
            name="需求分析知识库",
            description="软件需求分析相关的知识和模板",
            type=KnowledgeType.REQUIREMENTS_TEMPLATES,
            storage_path=str(self.data_dir / "requirements"),
        )

        # 最佳实践知识库
        best_practices_kb = KnowledgeBase(
            id="best_practices",
            name="最佳实践知识库",
            description="软件工程最佳实践和经验总结",
            type=KnowledgeType.BEST_PRACTICES,
            storage_path=str(self.data_dir / "best_practices"),
        )

        self.knowledge_bases["requirements_analysis"] = requirements_kb
        self.knowledge_bases["best_practices"] = best_practices_kb

        # 初始化默认知识条目
        self._load_default_knowledge_entries()

    def _load_default_knowledge_entries(self):
        """加载默认知识条目"""
        # 需求分析相关知识
        requirements_entries = [
            KnowledgeEntry(
                id=str(uuid.uuid4()),
                title="需求澄清问题模板",
                content="1. 功能性需求澄清：具体要实现什么功能？预期的用户场景？\n2. 非功能性需求：性能要求、安全要求、可用性要求\n3. 约束条件：时间约束、资源约束、技术约束\n4. 用户角色：主要用户群体、权限级别、使用频率",
                summary="标准的需求澄清问题模板，帮助全面了解用户需求",
                type=KnowledgeType.REQUIREMENTS_TEMPLATES,
                category="需求澄清",
                tags=["需求分析", "澄清问题", "模板"],
                source="系统默认",
                confidence=0.9,
            ),
            KnowledgeEntry(
                id=str(uuid.uuid4()),
                title="业务分析框架",
                content="1. 业务目标分析：核心业务目标、成功指标、关键绩效\n2. 利益相关者分析：主要利益相关者、期望与需求、影响程度\n3. 业务流程分析：当前流程、期望流程、痛点识别\n4. 价值主张分析：核心价值、竞争优势、差异化特性",
                summary="系统化的业务分析框架，确保全面理解业务需求",
                type=KnowledgeType.BEST_PRACTICES,
                category="业务分析",
                tags=["业务分析", "框架", "方法论"],
                source="系统默认",
                confidence=0.9,
            ),
            KnowledgeEntry(
                id=str(uuid.uuid4()),
                title="需求规格文档结构",
                content="1. 概述：项目背景、目标、范围\n2. 功能需求：详细功能描述、用例场景\n3. 非功能需求：性能、安全、可用性要求\n4. 约束条件：技术约束、时间约束、资源约束\n5. 验收标准：测试要求、质量标准",
                summary="标准的需求规格文档结构模板",
                type=KnowledgeType.REQUIREMENTS_TEMPLATES,
                category="文档模板",
                tags=["需求文档", "结构", "模板"],
                source="系统默认",
                confidence=0.9,
            ),
        ]

        self.knowledge_entries["requirements_analysis"] = requirements_entries
        self.knowledge_entries["best_practices"] = []

        logger.info(f"已加载 {len(requirements_entries)} 个默认知识条目")

    def search_knowledge(self, query: KnowledgeQuery) -> KnowledgeRecommendation:
        """搜索知识库"""
        start_time = datetime.now()

        all_results = []
        query_text_lower = query.query_text.lower()

        # 在所有知识库中搜索
        for kb_id, entries in self.knowledge_entries.items():
            for entry in entries:
                relevance_score = self._calculate_relevance(entry, query)

                if relevance_score >= query.min_confidence:
                    result = KnowledgeSearchResult(
                        entry=entry,
                        relevance_score=relevance_score,
                        match_type="semantic" if relevance_score > 0.7 else "keyword",
                        matched_keywords=self._extract_matched_keywords(
                            entry, query_text_lower
                        ),
                        explanation=f"基于{entry.category}匹配，相关度: {relevance_score:.2f}",
                    )
                    all_results.append(result)

        # 按相关性排序并限制结果数量
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        final_results = all_results[: query.limit]

        # 计算平均相关性
        avg_relevance = (
            sum(r.relevance_score for r in final_results) / len(final_results)
            if final_results
            else 0.0
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        return KnowledgeRecommendation(
            query=query.query_text,
            results=final_results,
            patterns=[],  # 简化实现
            suggestions=self._generate_suggestions(query, final_results),
            total_results=len(final_results),
            avg_relevance=avg_relevance,
            processing_time=processing_time,
        )

    def _calculate_relevance(
        self, entry: KnowledgeEntry, query: KnowledgeQuery
    ) -> float:
        """计算知识条目与查询的相关性"""
        query_text_lower = query.query_text.lower()
        relevance_score = 0.0

        # 标题匹配（权重：0.4）
        title_matches = sum(
            1 for word in query_text_lower.split() if word in entry.title.lower()
        )
        title_score = min(title_matches / len(query_text_lower.split()), 1.0) * 0.4

        # 内容匹配（权重：0.3）
        content_matches = sum(
            1 for word in query_text_lower.split() if word in entry.content.lower()
        )
        content_score = min(content_matches / len(query_text_lower.split()), 1.0) * 0.3

        # 标签匹配（权重：0.2）
        tag_matches = sum(
            1
            for word in query_text_lower.split()
            for tag in entry.tags
            if word in tag.lower()
        )
        tag_score = min(tag_matches / len(query_text_lower.split()), 1.0) * 0.2

        # 类型匹配（权重：0.1）
        type_score = 0.0
        if query.knowledge_types and entry.type in query.knowledge_types:
            type_score = 0.1

        relevance_score = title_score + content_score + tag_score + type_score

        # 考虑知识条目的可信度
        relevance_score *= entry.confidence

        return min(relevance_score, 1.0)

    def _extract_matched_keywords(
        self, entry: KnowledgeEntry, query_lower: str
    ) -> List[str]:
        """提取匹配的关键词"""
        query_words = query_lower.split()
        matched = []

        for word in query_words:
            if (
                word in entry.title.lower()
                or word in entry.content.lower()
                or any(word in tag.lower() for tag in entry.tags)
            ):
                matched.append(word)

        return matched

    def _generate_suggestions(
        self, query: KnowledgeQuery, results: List[KnowledgeSearchResult]
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []

        if not results:
            suggestions.append(
                "未找到相关知识，建议：1) 检查关键词拼写 2) 使用更通用的术语 3) 尝试不同的表达方式"
            )
        elif len(results) < 3:
            suggestions.append(
                "结果较少，建议：1) 使用更宽泛的关键词 2) 检查同义词 3) 考虑相关概念"
            )
        else:
            # 基于结果类型给出建议
            types = set(r.entry.type for r in results)
            if KnowledgeType.REQUIREMENTS_TEMPLATES in types:
                suggestions.append("找到了需求模板，建议结合项目具体情况进行调整")
            if KnowledgeType.BEST_PRACTICES in types:
                suggestions.append("找到了最佳实践，建议根据团队现状进行适配")

        return suggestions

    def add_knowledge_entry(self, kb_id: str, entry: KnowledgeEntry) -> bool:
        """添加知识条目"""
        try:
            if kb_id not in self.knowledge_entries:
                self.knowledge_entries[kb_id] = []

            self.knowledge_entries[kb_id].append(entry)

            # 更新使用统计
            if kb_id in self.knowledge_bases:
                self.knowledge_bases[kb_id].total_entries += 1
                self.knowledge_bases[kb_id].last_updated = datetime.now()

            logger.info(f"成功添加知识条目: {entry.title} 到知识库: {kb_id}")
            return True

        except Exception as e:
            logger.error(f"添加知识条目失败: {e}")
            return False

    def get_knowledge_bases(self) -> List[KnowledgeBase]:
        """获取所有知识库"""
        # 更新统计信息
        for kb_id, kb in self.knowledge_bases.items():
            kb.total_entries = len(self.knowledge_entries.get(kb_id, []))

        return list(self.knowledge_bases.values())

    def get_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBase]:
        """获取指定知识库"""
        kb = self.knowledge_bases.get(kb_id)
        if kb:
            kb.total_entries = len(self.knowledge_entries.get(kb_id, []))
        return kb

    def upload_document(
        self, kb_id: str, file_path: str, file_content: str, file_type: str
    ) -> bool:
        """上传文档到知识库"""
        try:
            # 简化的文档处理：直接将内容作为知识条目
            entry = KnowledgeEntry(
                id=str(uuid.uuid4()),
                title=f"上传文档: {Path(file_path).name}",
                content=file_content[:5000],  # 限制长度
                summary=(
                    file_content[:200] + "..."
                    if len(file_content) > 200
                    else file_content
                ),
                type=KnowledgeType.DOMAIN_KNOWLEDGE,
                category="上传文档",
                tags=["上传", file_type],
                source=f"用户上传: {file_path}",
                confidence=0.8,
            )

            return self.add_knowledge_entry(kb_id, entry)

        except Exception as e:
            logger.error(f"文档上传失败: {e}")
            return False

    def analyze_code_directory(self, kb_id: str, directory_path: str) -> Dict[str, Any]:
        """分析代码目录"""
        try:
            analysis_result = {
                "directory": directory_path,
                "total_files": 0,
                "languages": {},
                "components": [],
                "patterns": [],
            }

            directory = Path(directory_path)
            if not directory.exists():
                return analysis_result

            # 简化的代码分析
            for file_path in directory.rglob("*"):
                if file_path.is_file() and file_path.suffix in [
                    ".py",
                    ".js",
                    ".ts",
                    ".java",
                    ".go",
                ]:
                    analysis_result["total_files"] += 1

                    lang = file_path.suffix[1:]  # 去掉点号
                    analysis_result["languages"][lang] = (
                        analysis_result["languages"].get(lang, 0) + 1
                    )

                    # 创建代码知识条目
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()[:2000]  # 限制长度

                        entry = KnowledgeEntry(
                            id=str(uuid.uuid4()),
                            title=f"代码文件: {file_path.name}",
                            content=content,
                            summary=f"{lang}代码文件，路径: {file_path}",
                            type=KnowledgeType.TECHNICAL_PATTERNS,
                            category="代码分析",
                            tags=["代码", lang, file_path.parent.name],
                            source=f"代码分析: {file_path}",
                            confidence=0.7,
                        )

                        self.add_knowledge_entry(kb_id, entry)
                        analysis_result["components"].append(
                            {
                                "name": file_path.name,
                                "path": str(file_path),
                                "language": lang,
                                "size": len(content),
                            }
                        )

                    except Exception:
                        continue  # 忽略无法读取的文件

            logger.info(
                f"代码目录分析完成: {directory_path}, 找到 {analysis_result['total_files']} 个文件"
            )
            return analysis_result

        except Exception as e:
            logger.error(f"代码目录分析失败: {e}")
            return {"error": str(e)}


# 全局实例
knowledge_service = KnowledgeService()
