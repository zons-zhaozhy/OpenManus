#!/usr/bin/env python3
"""
增强版知识库系统测试脚本
验证知识库管理、文档处理、向量存储等功能
"""

import asyncio
import json
import tempfile
from pathlib import Path

from loguru import logger

from app.modules.knowledge_base.core.knowledge_manager import KnowledgeCategory
from app.modules.knowledge_base.enhanced_service import EnhancedKnowledgeService
from app.modules.knowledge_base.types import KnowledgeQuery


async def test_knowledge_base_creation():
    """测试知识库创建功能"""
    logger.info("🧪 测试知识库创建功能")

    service = EnhancedKnowledgeService()

    # 创建测试知识库
    test_cases = [
        {
            "name": "需求分析指南",
            "description": "软件需求分析的方法论和最佳实践",
            "category": KnowledgeCategory.REQUIREMENTS_ANALYSIS,
            "tags": ["需求分析", "软件工程", "最佳实践"],
        },
        {
            "name": "系统架构设计",
            "description": "系统架构设计原则和模式",
            "category": KnowledgeCategory.SYSTEM_DESIGN,
            "tags": ["架构设计", "设计模式"],
        },
        {
            "name": "编码规范手册",
            "description": "代码质量和编程规范",
            "category": KnowledgeCategory.CODING_STANDARDS,
            "tags": ["编码规范", "代码质量"],
        },
    ]

    created_kbs = []
    for case in test_cases:
        kb = service.create_knowledge_base(**case)
        if kb:
            created_kbs.append(kb)
            logger.success(f"✅ 知识库创建成功: {kb.name} (ID: {kb.id})")
        else:
            logger.error(f"❌ 知识库创建失败: {case['name']}")

    return created_kbs


async def test_document_upload():
    """测试文档上传功能"""
    logger.info("📄 测试文档上传功能")

    service = EnhancedKnowledgeService()

    # 获取已有的知识库
    knowledge_bases = service.list_knowledge_bases()
    if not knowledge_bases:
        logger.error("❌ 没有可用的知识库")
        return []

    kb_id = knowledge_bases[0]["id"]
    logger.info(f"使用知识库: {knowledge_bases[0]['name']} (ID: {kb_id})")

    # 创建测试文档
    test_documents = [
        {
            "filename": "requirements_analysis_guide.md",
            "content": """# 需求分析指南

## 1. 需求收集阶段

### 1.1 干系人识别
- 识别所有利益相关者
- 明确各干系人的职责和权限
- 建立沟通渠道

### 1.2 需求收集技术
- 面谈法：深入了解用户需求
- 问卷调查：广泛收集意见
- 原型法：快速验证需求理解
- 头脑风暴：激发创新想法

## 2. 需求分析阶段

### 2.1 功能需求分析
- 明确系统必须提供的功能
- 定义输入输出规格
- 确定处理逻辑

### 2.2 非功能需求分析
- 性能需求：响应时间、吞吐量
- 安全需求：访问控制、数据保护
- 可用性需求：界面友好性、易用性
- 可靠性需求：故障处理、恢复能力

## 3. 需求验证

### 3.1 需求评审
- 完整性检查
- 一致性验证
- 可行性分析
- 可测试性评估

### 3.2 原型验证
- 界面原型
- 功能原型
- 用户体验测试
""",
        },
        {
            "filename": "system_design_principles.txt",
            "content": """系统设计基本原则

1. 单一职责原则 (SRP)
每个类应该只有一个引起它变化的原因。

2. 开闭原则 (OCP)
软件实体应该对扩展开放，对修改关闭。

3. 里氏替换原则 (LSP)
子类对象应该能够替换其父类对象。

4. 接口隔离原则 (ISP)
不应该强迫客户依赖它们不使用的接口。

5. 依赖倒置原则 (DIP)
高层模块不应该依赖低层模块，两者都应该依赖抽象。

架构模式：

1. 分层架构
- 表示层：用户界面
- 业务层：业务逻辑
- 数据层：数据访问

2. 微服务架构
- 服务拆分
- 独立部署
- 松耦合

3. 事件驱动架构
- 异步通信
- 事件发布订阅
- 解耦合
""",
        },
    ]

    uploaded_docs = []

    for doc_info in test_documents:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=f"_{doc_info['filename']}", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(doc_info["content"])
            temp_file_path = temp_file.name

        try:
            # 上传文档
            result = await service.upload_document(
                kb_id=kb_id,
                file_path=temp_file_path,
                title=doc_info["filename"].split(".")[0],
            )

            if result:
                uploaded_docs.append(result)
                logger.success(f"✅ 文档上传成功: {result['title']}")
                logger.info(f"   - 文档ID: {result['document_id']}")
                logger.info(f"   - 知识点数量: {result['knowledge_points_count']}")
                logger.info(f"   - 关键词数量: {result['keywords_count']}")
                logger.info(f"   - 摘要: {result['summary'][:100]}...")
            else:
                logger.error(f"❌ 文档上传失败: {doc_info['filename']}")

        finally:
            # 清理临时文件
            try:
                Path(temp_file_path).unlink()
            except OSError:
                pass

    return uploaded_docs


async def test_knowledge_search():
    """测试知识搜索功能"""
    logger.info("🔍 测试知识搜索功能")

    service = EnhancedKnowledgeService()

    # 测试搜索查询
    test_queries = [
        "需求分析",
        "系统设计原则",
        "微服务架构",
        "用户界面设计",
        "数据库设计",
    ]

    search_results = []

    for query_text in test_queries:
        logger.info(f"搜索: {query_text}")

        query = KnowledgeQuery(query_text=query_text, limit=5, min_confidence=0.0)

        result = await service.search_knowledge(query)

        logger.info(f"   找到 {result.total_results} 个结果")
        for i, item in enumerate(result.results[:3]):  # 显示前3个结果
            logger.info(f"   {i+1}. 分数: {item.get('score', 0):.2f}")
            logger.info(f"      内容: {item.get('content', '')[:100]}...")

        search_results.append(
            {
                "query": query_text,
                "total_results": result.total_results,
                "results": result.results,
            }
        )

    return search_results


async def test_system_stats():
    """测试系统统计功能"""
    logger.info("📊 测试系统统计功能")

    service = EnhancedKnowledgeService()

    # 获取系统统计信息
    stats = service.get_system_stats()

    logger.info("系统统计信息:")
    logger.info(f"  知识库总数: {stats['knowledge_bases']['total']}")
    logger.info(f"  活跃知识库: {stats['knowledge_bases']['active']}")
    logger.info(f"  文档总数: {stats['documents']['total']}")
    logger.info(f"  存储大小: {stats['storage']['total_size_mb']} MB")
    logger.info(f"  向量存储可用: {stats['vector_store']['available']}")

    # 按分类统计
    if stats["knowledge_bases"]["by_category"]:
        logger.info("  按分类统计:")
        for category, count in stats["knowledge_bases"]["by_category"].items():
            logger.info(f"    {category}: {count}")

    return stats


async def test_knowledge_gaps_analysis():
    """测试知识库缺口分析"""
    logger.info("🔍 测试知识库缺口分析")

    service = EnhancedKnowledgeService()

    # 获取所有知识库ID
    knowledge_bases = service.list_knowledge_bases()
    kb_ids = [kb["id"] for kb in knowledge_bases]

    if not kb_ids:
        logger.warning("⚠️ 没有知识库可供分析")
        return {}

    # 执行缺口分析
    analysis = service.analyze_knowledge_gaps(kb_ids)

    logger.info("知识库缺口分析结果:")
    logger.info(f"  分析的知识库数量: {analysis['total_knowledge_bases']}")

    # 覆盖范围分析
    if analysis["coverage_analysis"]:
        logger.info("  覆盖的领域:")
        for category, kb_list in analysis["coverage_analysis"].items():
            logger.info(f"    {category}: {len(kb_list)} 个知识库")

    # 缺口领域
    if analysis["gap_areas"]:
        logger.info("  缺失的领域:")
        for area in analysis["gap_areas"]:
            logger.info(f"    - {area}")

    # 改进建议
    if analysis["recommendations"]:
        logger.info("  改进建议:")
        for recommendation in analysis["recommendations"]:
            logger.info(f"    - {recommendation}")

    return analysis


async def main():
    """主测试函数"""
    logger.info("🚀 开始增强版知识库系统测试")

    test_results = {}

    try:
        # 1. 测试知识库创建
        created_kbs = await test_knowledge_base_creation()
        test_results["knowledge_base_creation"] = {
            "success": len(created_kbs) > 0,
            "created_count": len(created_kbs),
        }

        # 2. 测试文档上传
        uploaded_docs = await test_document_upload()
        test_results["document_upload"] = {
            "success": len(uploaded_docs) > 0,
            "uploaded_count": len(uploaded_docs),
        }

        # 3. 测试知识搜索
        search_results = await test_knowledge_search()
        test_results["knowledge_search"] = {
            "success": len(search_results) > 0,
            "queries_tested": len(search_results),
        }

        # 4. 测试系统统计
        stats = await test_system_stats()
        test_results["system_stats"] = {"success": bool(stats), "stats": stats}

        # 5. 测试缺口分析
        gaps_analysis = await test_knowledge_gaps_analysis()
        test_results["gaps_analysis"] = {
            "success": bool(gaps_analysis),
            "analysis": gaps_analysis,
        }

    except Exception as e:
        logger.error(f"❌ 测试过程中发生异常: {e}")
        test_results["error"] = str(e)

    # 输出测试摘要
    logger.info("\n📋 测试摘要:")
    for test_name, result in test_results.items():
        if test_name == "error":
            logger.error(f"  ❌ 测试异常: {result}")
        else:
            status = "✅ 成功" if result.get("success") else "❌ 失败"
            logger.info(f"  {status} {test_name}")

    # 保存详细结果
    with open(
        "enhanced_knowledge_system_test_results.json", "w", encoding="utf-8"
    ) as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2, default=str)

    logger.info(
        f"\n📄 详细测试结果已保存到: enhanced_knowledge_system_test_results.json"
    )

    return test_results


if __name__ == "__main__":
    asyncio.run(main())
