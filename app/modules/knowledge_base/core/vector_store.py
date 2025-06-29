"""
向量存储服务 - 基于Chroma的语义检索
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb import Collection
from chromadb.utils import embedding_functions
from loguru import logger

from .types import VectorSearchQuery, VectorSearchResult

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

    def __init__(
        self,
        storage_path: str = "data/vector_store",
        embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2",
    ):
        """
        初始化向量存储

        Args:
            storage_path: 存储路径
            embedding_model: embedding模型名称
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 初始化embedding函数
        self.embedding_model = None
        try:
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise ImportError("SentenceTransformers package is not installed")

            logger.info(f"正在加载SentenceTransformers模型: {embedding_model}")
            self.embedding_model = SentenceTransformer(embedding_model)
            self.embedding_function = (
                embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=embedding_model
                )
            )
            logger.info(f"SentenceTransformers模型加载成功: {embedding_model}")
        except Exception as e:
            logger.error(f"SentenceTransformers初始化失败: {e}")
            logger.warning("使用默认embedding函数作为回退方案")
            self.embedding_function = embedding_functions.DefaultEmbeddingFunction()

        # 初始化Chroma客户端
        try:
            self.client = chromadb.PersistentClient(path=str(self.storage_path))
            logger.info("Chroma客户端初始化成功")
        except Exception as e:
            logger.error(f"Chroma客户端初始化失败: {e}")
            raise

        # 存储集合映射
        self.collections: Dict[str, Collection] = {}

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

    def add_documents(
        self, kb_id: str, documents: List[Dict[str, Any]], batch_size: int = 100
    ) -> bool:
        """
        添加文档到知识库集合

        Args:
            kb_id: 知识库ID
            documents: 文档列表，每个文档包含content和metadata
            batch_size: 批处理大小

        Returns:
            bool: 添加是否成功
        """
        try:
            # 验证输入
            if not documents:
                logger.warning("没有文档需要添加")
                return True

            # 获取或创建集合
            collection = self._get_collection(kb_id)
            if not collection:
                logger.info(f"知识库集合不存在，尝试创建: {kb_id}")
                success = self.create_knowledge_base_collection(
                    kb_id, f"Knowledge Base {kb_id}"
                )
                if not success:
                    logger.error(f"创建知识库集合失败: {kb_id}")
                    return False
                collection = self._get_collection(kb_id)
                if not collection:
                    logger.error(f"无法获取新创建的知识库集合: {kb_id}")
                    return False

            # 准备数据
            ids = []
            contents = []
            metadatas = []

            for doc in documents:
                if not doc.get("content"):
                    logger.warning(f"跳过空内容文档: {doc.get('id', 'unknown')}")
                    continue

                doc_id = doc.get("id", str(uuid.uuid4()))
                ids.append(doc_id)
                contents.append(doc["content"])
                metadata = {
                    "kb_id": kb_id,
                    "doc_id": doc_id,
                    "timestamp": datetime.now().isoformat(),
                    **doc.get("metadata", {}),
                }
                metadatas.append(metadata)

            if not ids:
                logger.warning("没有有效的文档需要添加")
                return True

            # 批量添加
            total_added = 0
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i : i + batch_size]
                batch_contents = contents[i : i + batch_size]
                batch_metadatas = metadatas[i : i + batch_size]

                try:
                    collection.add(
                        ids=batch_ids,
                        documents=batch_contents,
                        metadatas=batch_metadatas,
                    )
                    total_added += len(batch_ids)
                    logger.info(f"成功添加 {len(batch_ids)} 个文档到知识库: {kb_id}")
                except Exception as e:
                    logger.error(f"批量添加文档失败: {e}")
                    return False

            logger.info(
                f"文档添加完成，总共添加: {total_added} 个文档到知识库: {kb_id}"
            )
            return True

        except Exception as e:
            logger.error(f"添加文档失败: {kb_id}, 错误: {e}")
            return False

    def search(self, query: VectorSearchQuery) -> List[VectorSearchResult]:
        """
        执行语义搜索

        Args:
            query: 搜索查询对象

        Returns:
            List[VectorSearchResult]: 搜索结果列表
        """
        try:
            all_results = []

            # 验证查询
            if not query.query_text.strip():
                logger.warning("搜索查询文本为空")
                return []

            # 如果没有指定知识库ID，使用所有可用的知识库
            kb_ids = query.knowledge_base_ids or list(self.collections.keys())
            if not kb_ids:
                logger.warning("没有可用的知识库集合")
                return []

            logger.info(f"开始搜索，查询文本: {query.query_text}, 知识库: {kb_ids}")

            for kb_id in kb_ids:
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
                try:
                    results = collection.query(**search_kwargs)
                    logger.debug(f"知识库 {kb_id} 搜索结果: {results}")
                except Exception as e:
                    logger.warning(f"搜索知识库 {kb_id} 失败: {e}")
                    continue

                # 处理结果
                if results and results.get("documents") and results["documents"][0]:
                    for i, (doc_id, document, metadata, distance) in enumerate(
                        zip(
                            results["ids"][0],
                            results["documents"][0],
                            results["metadatas"][0],
                            results["distances"][0],
                        )
                    ):
                        # 转换距离为相似度分数 (1 - distance)
                        score = max(0.0, min(1.0, 1.0 - float(distance)))

                        if score >= query.min_score:
                            result = VectorSearchResult(
                                id=doc_id,
                                content=document,
                                score=score,
                                metadata=metadata or {},
                                knowledge_base_id=kb_id,
                            )
                            all_results.append(result)
                            logger.debug(f"添加搜索结果: {doc_id}, 分数: {score}")

            # 按分数排序
            all_results.sort(key=lambda x: x.score, reverse=True)
            final_results = all_results[: query.top_k]

            logger.info(f"搜索完成，找到 {len(final_results)} 个结果")
            return final_results

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
        获取知识库集合统计信息

        Args:
            kb_id: 知识库ID

        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            collection = self._get_collection(kb_id)
            if not collection:
                return {
                    "vector_count": 0,
                    "total_chunks": 0,
                    "last_updated": None,
                }

            # 获取集合信息
            count = collection.count()
            metadata = collection.metadata or {}

            return {
                "vector_count": count,
                "total_chunks": count,
                "last_updated": metadata.get("last_updated"),
            }

        except Exception as e:
            logger.error(f"获取知识库集合统计信息失败: {kb_id}, 错误: {e}")
            return {
                "vector_count": 0,
                "total_chunks": 0,
                "last_updated": None,
            }

    def _get_collection(self, kb_id: str) -> Optional[Collection]:
        """
        获取知识库集合

        Args:
            kb_id: 知识库ID

        Returns:
            Optional[Collection]: 知识库集合
        """
        try:
            collection_name = f"kb_{kb_id}"

            # 检查缓存
            if kb_id in self.collections:
                return self.collections[kb_id]

            # 尝试获取已存在的集合
            try:
                collection = self.client.get_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function,
                )
                self.collections[kb_id] = collection
                return collection
            except Exception:
                logger.warning(f"知识库集合不存在: {kb_id}")
                return None

        except Exception as e:
            logger.error(f"获取知识库集合失败: {kb_id}, 错误: {e}")
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

    def get_diagnostic_info(self) -> Dict[str, Any]:
        """
        获取向量存储的诊断信息

        Returns:
            Dict[str, Any]: 诊断信息
        """
        try:
            info = {
                "status": "healthy",
                "embedding_function": {
                    "type": self.embedding_function.__class__.__name__,
                    "is_default": isinstance(
                        self.embedding_function,
                        embedding_functions.DefaultEmbeddingFunction,
                    ),
                },
                "collections": {},
                "total_documents": 0,
                "errors": [],
            }

            # 检查所有集合
            for kb_id in self.collections.keys():
                collection = self._get_collection(kb_id)
                if not collection:
                    info["errors"].append(f"无法访问知识库集合: {kb_id}")
                    continue

                try:
                    count = collection.count()
                    peek = collection.peek()
                    info["collections"][kb_id] = {
                        "document_count": count,
                        "has_documents": count > 0,
                        "sample_document_ids": peek["ids"] if peek else [],
                    }
                    info["total_documents"] += count
                except Exception as e:
                    info["errors"].append(f"获取知识库 {kb_id} 统计信息失败: {e}")

            # 检查存储路径
            storage_info = {
                "path": str(self.storage_path),
                "exists": self.storage_path.exists(),
                "is_dir": self.storage_path.is_dir(),
                "size_bytes": sum(
                    f.stat().st_size
                    for f in self.storage_path.rglob("*")
                    if f.is_file()
                ),
            }
            info["storage"] = storage_info

            # 设置状态
            if info["errors"]:
                info["status"] = "warning" if info["total_documents"] > 0 else "error"

            return info

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "embedding_function": {
                    "type": "unknown",
                    "is_default": True,
                },
                "collections": {},
                "total_documents": 0,
                "errors": [str(e)],
            }
