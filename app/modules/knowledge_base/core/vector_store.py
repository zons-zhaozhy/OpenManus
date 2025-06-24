"""
向量存储服务 - 基于Chroma的高性能语义检索
"""

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

# 导入Chroma向量数据库
try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions

    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("Chroma向量数据库未安装，将跳过向量存储功能")

# 导入embedding模型
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("SentenceTransformers未安装，将使用默认embedding")


@dataclass
class SearchResult:
    """搜索结果"""

    id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    knowledge_base_id: str
    document_id: str


@dataclass
class VectorSearchQuery:
    """向量搜索查询"""

    query_text: str
    knowledge_base_ids: List[str]
    top_k: int = 10
    min_score: float = 0.0
    filters: Optional[Dict[str, Any]] = None


class VectorStore:
    """向量存储服务 - 基于Chroma的语义检索"""

    def __init__(self, storage_path: str = "data/knowledge_bases"):
        """
        初始化向量存储服务

        Args:
            storage_path: 存储路径
        """
        if not CHROMA_AVAILABLE:
            raise RuntimeError("Chroma向量数据库未安装，请运行: pip install chromadb")

        self.storage_path = Path(storage_path)
        self.vector_path = self.storage_path / "vectors"
        self.vector_path.mkdir(parents=True, exist_ok=True)

        # 初始化Chroma客户端 - 使用新的配置方式
        self.client = chromadb.PersistentClient(path=str(self.vector_path))

        # 初始化embedding函数
        self._init_embedding_function()

        # 集合缓存
        self.collections = {}

        logger.info(f"向量存储服务初始化完成，存储路径: {self.vector_path}")

    def _init_embedding_function(self):
        """初始化embedding函数"""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            # 使用多语言模型
            try:
                self.embedding_model = SentenceTransformer(
                    "paraphrase-multilingual-MiniLM-L12-v2"
                )
                self.embedding_function = None  # 使用自定义embedding
                logger.info("使用SentenceTransformers多语言模型")
            except Exception as e:
                logger.warning(
                    f"SentenceTransformers初始化失败: {e}，使用默认embedding"
                )
                self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
                self.embedding_model = None
        else:
            # 使用Chroma默认embedding
            self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
            self.embedding_model = None
            logger.info("使用Chroma默认embedding函数")

    def create_knowledge_base_collection(self, kb_id: str, kb_name: str) -> bool:
        """
        为知识库创建向量集合

        Args:
            kb_id: 知识库ID
            kb_name: 知识库名称

        Returns:
            bool: 创建是否成功
        """
        try:
            collection_name = f"kb_{kb_id}"

            # 检查集合是否已存在（静默检查，不产生错误日志）
            try:
                collection = self.client.get_collection(
                    name=collection_name, embedding_function=self.embedding_function
                )
                logger.info(f"知识库集合已存在: {collection_name}")
                self.collections[kb_id] = collection
                return True
            except Exception:
                # 集合不存在，继续创建新集合
                pass

            # 创建新集合
            collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"kb_name": kb_name, "kb_id": kb_id},
            )

            self.collections[kb_id] = collection
            logger.info(f"知识库向量集合创建成功: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"创建知识库向量集合失败: {e}")
            return False

    def add_documents(self, kb_id: str, documents: List[Dict[str, Any]]) -> bool:
        """
        添加文档到向量存储

        Args:
            kb_id: 知识库ID
            documents: 文档列表，每个文档包含id、content、metadata

        Returns:
            bool: 添加是否成功
        """
        try:
            collection = self._get_collection(kb_id)
            if not collection:
                logger.error(f"知识库集合不存在: {kb_id}")
                return False

            # 准备数据
            ids = []
            contents = []
            metadatas = []
            embeddings = []

            for doc in documents:
                doc_id = doc.get("id")
                content = doc.get("content", "")
                metadata = doc.get("metadata", {})

                if not doc_id or not content:
                    logger.warning(f"文档缺少必要字段: {doc}")
                    continue

                ids.append(doc_id)
                contents.append(content)
                metadatas.append(
                    {**metadata, "kb_id": kb_id, "content_length": len(content)}
                )

                # 生成embedding
                if self.embedding_model:
                    embedding = self.embedding_model.encode(content).tolist()
                    embeddings.append(embedding)

            if not ids:
                logger.warning("没有有效的文档可添加")
                return False

            # 添加到集合
            if self.embedding_model:
                collection.add(
                    ids=ids,
                    documents=contents,
                    metadatas=metadatas,
                    embeddings=embeddings,
                )
            else:
                collection.add(ids=ids, documents=contents, metadatas=metadatas)

            logger.info(f"成功添加 {len(ids)} 个文档到知识库 {kb_id}")
            return True

        except Exception as e:
            logger.error(f"添加文档到向量存储失败: {e}")
            return False

    def search(self, query: VectorSearchQuery) -> List[SearchResult]:
        """
        执行语义搜索

        Args:
            query: 搜索查询对象

        Returns:
            List[SearchResult]: 搜索结果列表
        """
        try:
            all_results = []

            for kb_id in query.knowledge_base_ids:
                collection = self._get_collection(kb_id)
                if not collection:
                    logger.warning(f"知识库集合不存在: {kb_id}")
                    continue

                # 构建查询参数
                search_kwargs = {
                    "query_texts": [query.query_text],
                    "n_results": query.top_k,
                }

                # 添加过滤条件
                if query.filters:
                    search_kwargs["where"] = query.filters

                # 执行搜索
                results = collection.query(**search_kwargs)

                # 处理结果
                if results and results.get("documents"):
                    for i, (doc_id, document, metadata, distance) in enumerate(
                        zip(
                            results["ids"][0],
                            results["documents"][0],
                            results["metadatas"][0],
                            results["distances"][0],
                        )
                    ):
                        # 转换距离为相似度分数 (1 - distance)
                        score = max(0.0, 1.0 - distance)

                        if score >= query.min_score:
                            result = SearchResult(
                                id=doc_id,
                                content=document,
                                score=score,
                                metadata=metadata,
                                knowledge_base_id=kb_id,
                                document_id=metadata.get("document_id", ""),
                            )
                            all_results.append(result)

            # 按分数排序并返回top_k结果
            all_results.sort(key=lambda x: x.score, reverse=True)
            return all_results[: query.top_k]

        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []

    def update_document(
        self,
        kb_id: str,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        更新文档

        Args:
            kb_id: 知识库ID
            doc_id: 文档ID
            content: 新内容
            metadata: 新元数据

        Returns:
            bool: 更新是否成功
        """
        try:
            collection = self._get_collection(kb_id)
            if not collection:
                logger.error(f"知识库集合不存在: {kb_id}")
                return False

            # 生成新的embedding
            if self.embedding_model:
                embedding = self.embedding_model.encode(content).tolist()

                collection.update(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[
                        {
                            **(metadata or {}),
                            "kb_id": kb_id,
                            "content_length": len(content),
                        }
                    ],
                    embeddings=[embedding],
                )
            else:
                collection.update(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[
                        {
                            **(metadata or {}),
                            "kb_id": kb_id,
                            "content_length": len(content),
                        }
                    ],
                )

            logger.info(f"文档更新成功: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"更新文档失败: {e}")
            return False

    def delete_document(self, kb_id: str, doc_id: str) -> bool:
        """
        删除文档

        Args:
            kb_id: 知识库ID
            doc_id: 文档ID

        Returns:
            bool: 删除是否成功
        """
        try:
            collection = self._get_collection(kb_id)
            if not collection:
                logger.error(f"知识库集合不存在: {kb_id}")
                return False

            collection.delete(ids=[doc_id])
            logger.info(f"文档删除成功: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False

    def delete_knowledge_base_collection(self, kb_id: str) -> bool:
        """
        删除知识库的向量集合

        Args:
            kb_id: 知识库ID

        Returns:
            bool: 删除是否成功
        """
        try:
            collection_name = f"kb_{kb_id}"
            self.client.delete_collection(name=collection_name)

            # 从缓存中移除
            if kb_id in self.collections:
                del self.collections[kb_id]

            logger.info(f"知识库向量集合删除成功: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"删除知识库向量集合失败: {e}")
            return False

    def get_collection_stats(self, kb_id: str) -> Dict[str, Any]:
        """
        获取集合统计信息

        Args:
            kb_id: 知识库ID

        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            collection = self._get_collection(kb_id)
            if not collection:
                return {}

            count = collection.count()

            return {
                "kb_id": kb_id,
                "document_count": count,
                "collection_name": f"kb_{kb_id}",
            }

        except Exception as e:
            logger.error(f"获取集合统计信息失败: {e}")
            return {}

    def _get_collection(self, kb_id: str):
        """获取知识库对应的向量集合"""
        if kb_id in self.collections:
            return self.collections[kb_id]

        try:
            collection_name = f"kb_{kb_id}"
            collection = self.client.get_collection(
                name=collection_name, embedding_function=self.embedding_function
            )
            self.collections[kb_id] = collection
            return collection
        except Exception as e:
            logger.error(f"获取向量集合失败: {e}")
            return None

    def hybrid_search(
        self, query: VectorSearchQuery, keyword_boost: float = 0.3
    ) -> List[SearchResult]:
        """
        混合搜索：结合语义搜索和关键词搜索

        Args:
            query: 搜索查询
            keyword_boost: 关键词匹配的权重提升

        Returns:
            List[SearchResult]: 搜索结果
        """
        # 先执行语义搜索
        semantic_results = self.search(query)

        # 提取查询关键词
        query_keywords = self._extract_keywords(query.query_text)

        # 对结果进行关键词匹配增强
        for result in semantic_results:
            keyword_matches = 0
            for keyword in query_keywords:
                if keyword.lower() in result.content.lower():
                    keyword_matches += 1

            # 根据关键词匹配情况调整分数
            if keyword_matches > 0:
                keyword_ratio = keyword_matches / len(query_keywords)
                result.score = min(1.0, result.score + keyword_boost * keyword_ratio)

        # 重新排序
        semantic_results.sort(key=lambda x: x.score, reverse=True)
        return semantic_results

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        import re

        # 简单的关键词提取
        words = re.findall(r"\b[\u4e00-\u9fff]+\b|\b[a-zA-Z]+\b", text)

        # 过滤停用词
        stop_words = {
            "的",
            "了",
            "在",
            "是",
            "我",
            "有",
            "和",
            "就",
            "不",
            "人",
            "都",
            "一",
            "也",
            "很",
            "到",
            "说",
            "要",
            "去",
            "你",
            "会",
            "着",
            "没有",
            "看",
            "好",
            "自己",
            "这",
        }

        keywords = [word for word in words if len(word) > 1 and word not in stop_words]
        return list(set(keywords))  # 去重

    def get_similar_documents(
        self, kb_id: str, doc_id: str, top_k: int = 5
    ) -> List[SearchResult]:
        """
        查找相似文档

        Args:
            kb_id: 知识库ID
            doc_id: 参考文档ID
            top_k: 返回结果数量

        Returns:
            List[SearchResult]: 相似文档列表
        """
        try:
            collection = self._get_collection(kb_id)
            if not collection:
                return []

            # 获取参考文档
            doc_results = collection.get(
                ids=[doc_id], include=["documents", "metadatas"]
            )

            if not doc_results or not doc_results.get("documents"):
                logger.warning(f"参考文档不存在: {doc_id}")
                return []

            reference_content = doc_results["documents"][0]

            # 使用参考文档内容进行搜索
            query = VectorSearchQuery(
                query_text=reference_content,
                knowledge_base_ids=[kb_id],
                top_k=top_k + 1,  # +1 because the reference doc will be included
            )

            results = self.search(query)

            # 排除参考文档自身
            similar_docs = [r for r in results if r.id != doc_id]

            return similar_docs[:top_k]

        except Exception as e:
            logger.error(f"查找相似文档失败: {e}")
            return []
