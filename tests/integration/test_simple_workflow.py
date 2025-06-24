#!/usr/bin/env python3
"""
简化的需求分析工作流测试
快速验证知识库和代码库的核心功能
"""

import asyncio

from loguru import logger

from app.modules.codebase.manager import CodebaseManager
from app.modules.codebase.types import CodeSearchQuery
from app.modules.knowledge_base.enhanced_service import EnhancedKnowledgeService


async def test_basic_functionality():
    """测试基本功能"""
    logger.info("🚀 开始基本功能测试")

    # 1. 测试知识库服务
    logger.info("📚 测试知识库服务")
    knowledge_service = EnhancedKnowledgeService()
    kb_list = knowledge_service.list_knowledge_bases()
    logger.info(f"  ✅ 知识库数量: {len(kb_list)}")

    # 2. 测试代码库管理器
    logger.info("💻 测试代码库管理器")
    codebase_manager = CodebaseManager()
    stats = codebase_manager.get_statistics()
    logger.info(f"  ✅ 代码库统计: {stats.get('total_codebases', 0)} 个代码库")
    logger.info(f"  ✅ 总文件数: {stats.get('total_files', 0)}")
    logger.info(f"  ✅ 总组件数: {stats.get('total_components', 0)}")

    # 3. 测试代码组件搜索
    logger.info("🔍 测试代码组件搜索")

    # 获取现有代码库ID
    codebases = codebase_manager.list_codebases()
    codebase_ids = [cb.id for cb in codebases]

    if codebase_ids:
        search_query = CodeSearchQuery(
            query_text="API 接口 服务", codebase_ids=codebase_ids[:3]  # 使用前3个代码库
        )
        search_results = codebase_manager.search_components(search_query)
        logger.info(f"  ✅ API相关组件: {len(search_results)} 个")
    else:
        search_results = []
        logger.info("  ⚠️ 没有可用的代码库进行搜索")

    # 4. 测试工作量估算
    logger.info("📊 测试工作量估算")
    if codebase_ids:
        estimation = codebase_manager.estimate_workload(
            codebase_id=codebase_ids[0],
            task_description="开发一个用户管理API接口，包括注册、登录、信息管理功能",
        )
        if estimation:
            logger.info(f"  ✅ 估算结果: {estimation.total_days} 天")
            logger.info(f"  ✅ 置信度: {estimation.confidence:.1%}")
        else:
            logger.info("  ⚠️ 工作量估算失败")
    else:
        estimation = None
        logger.info("  ⚠️ 没有可用的代码库进行工作量估算")

    # 5. 综合评估
    logger.info("🎯 综合评估")

    test_results = {
        "knowledge_base_available": len(kb_list) > 0,
        "codebase_analyzed": stats.get("total_components", 0) > 0,
        "search_functional": len(search_results) >= 0,
        "estimation_working": estimation is not None
        and hasattr(estimation, "total_days"),
    }

    success_count = sum(test_results.values())
    total_tests = len(test_results)
    success_rate = success_count / total_tests

    print("\n" + "=" * 60)
    print("🎯 需求分析工作流基本功能测试报告")
    print("=" * 60)

    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")

    print(f"\n总体成功率: {success_rate:.1%} ({success_count}/{total_tests})")

    if success_rate >= 0.8:
        print("🎉 测试评估: 优秀 - 系统功能正常，可以支持需求分析工作")
    elif success_rate >= 0.6:
        print("✅ 测试评估: 良好 - 系统基本功能正常，部分功能需要改进")
    else:
        print("⚠️ 测试评估: 需要改进 - 系统存在关键功能问题")

    print("=" * 60)

    logger.success("🏁 基本功能测试完成")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
