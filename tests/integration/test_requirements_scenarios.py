#!/usr/bin/env python3
"""
需求分析场景测试
模拟真实的需求分析场景，验证知识库和代码库功能的协作效果
"""

import asyncio
import tempfile
from pathlib import Path
from loguru import logger
from app.modules.knowledge_base.enhanced_service import EnhancedKnowledgeService
from app.modules.knowledge_base.core.knowledge_manager import KnowledgeCategory
from app.modules.knowledge_base.types import KnowledgeQuery
from app.modules.codebase.manager import CodebaseManager
from app.modules.codebase.types import CodeSearchQuery


class RequirementAnalysisScenarios:
    """需求分析场景测试器"""
    
    def __init__(self):
        self.knowledge_service = EnhancedKnowledgeService()
        self.codebase_manager = CodebaseManager()
    
    async def run_all_scenarios(self):
        """运行所有测试场景"""
        logger.info("🚀 开始需求分析场景测试")
        
        # 准备测试数据
        await self._setup_test_data()
        
        # 运行测试场景
        scenarios = [
            self._scenario_new_feature_request(),
            self._scenario_system_integration(),
            self._scenario_performance_optimization(),
            self._scenario_security_enhancement()
        ]
        
        results = []
        for i, scenario in enumerate(scenarios, 1):
            logger.info(f"📋 执行场景 {i}: {scenario['name']}")
            result = await self._execute_scenario(scenario)
            results.append(result)
        
        # 汇总报告
        self._generate_summary_report(results)
        
        logger.success("🎯 所有需求分析场景测试完成")
    
    async def _setup_test_data(self):
        """设置测试数据"""
        logger.info("📋 设置测试数据")
        
        # 创建或使用现有知识库
        kb_list = self.knowledge_service.list_knowledge_bases()
        if kb_list:
            self.test_kb_id = kb_list[0]["id"]
            logger.info(f"使用现有知识库: {self.test_kb_id}")
        else:
            logger.info("没有可用的知识库，跳过知识库测试")
            self.test_kb_id = None
    
    def _scenario_new_feature_request(self):
        """场景1：新功能需求"""
        return {
            "name": "智能推荐系统需求分析",
            "description": "电商平台新增个性化推荐功能",
            "initial_requirement": """
            我们希望在电商平台上增加一个智能推荐系统，能够：
            - 根据用户购买历史推荐相关商品
            - 基于用户浏览行为进行个性化推荐
            - 支持实时推荐和批量推荐
            """,
            "knowledge_queries": [
                "推荐系统算法",
                "个性化推荐最佳实践",
                "用户行为分析"
            ],
            "code_searches": [
                "数据分析",
                "算法实现", 
                "用户管理"
            ],
            "expected_clarifications": [
                "推荐算法的具体类型选择",
                "数据隐私和安全要求", 
                "系统性能和响应时间要求",
                "推荐结果的准确性评估标准"
            ]
        }
    
    def _scenario_system_integration(self):
        """场景2：系统集成需求"""
        return {
            "name": "第三方支付集成",
            "description": "集成微信支付和支付宝支付",
            "initial_requirement": """
            需要在现有电商系统中集成第三方支付功能：
            - 支持微信支付和支付宝支付
            - 支持订单支付、退款、查询
            - 需要处理支付回调和异常情况
            """,
            "knowledge_queries": [
                "第三方API集成",
                "支付系统安全",
                "错误处理最佳实践"
            ],
            "code_searches": [
                "API接口",
                "HTTP客户端",
                "配置管理"
            ],
            "expected_clarifications": [
                "支付安全认证机制",
                "异常处理和重试策略",
                "支付数据的存储和备份",
                "合规性和监管要求"
            ]
        }
    
    def _scenario_performance_optimization(self):
        """场景3：性能优化需求"""
        return {
            "name": "系统性能优化", 
            "description": "解决高并发访问下的性能问题",
            "initial_requirement": """
            当前系统在高并发访问时响应较慢，需要优化：
            - 页面加载时间超过3秒
            - 数据库查询耗时过长
            - 服务器资源使用率过高
            """,
            "knowledge_queries": [
                "性能优化策略",
                "数据库优化",
                "缓存设计"
            ],
            "code_searches": [
                "缓存",
                "数据库查询",
                "异步处理"
            ],
            "expected_clarifications": [
                "具体的性能指标要求",
                "优化的优先级排序",
                "可接受的架构调整范围",
                "性能监控和测试方案"
            ]
        }
    
    def _scenario_security_enhancement(self):
        """场景4：安全增强需求"""
        return {
            "name": "系统安全增强",
            "description": "提升系统安全防护能力", 
            "initial_requirement": """
            为提升系统安全性，需要加强以下方面：
            - 用户身份认证和授权
            - 数据传输加密
            - 防止SQL注入和XSS攻击
            """,
            "knowledge_queries": [
                "web安全最佳实践",
                "身份认证机制",
                "数据加密"
            ],
            "code_searches": [
                "身份认证",
                "安全验证",
                "加密算法"
            ],
            "expected_clarifications": [
                "安全等级和合规要求",
                "现有安全漏洞的评估",
                "安全升级的时间计划",
                "用户体验与安全的平衡"
            ]
        }
    
    async def _execute_scenario(self, scenario):
        """执行测试场景"""
        result = {
            "scenario": scenario["name"],
            "knowledge_search_results": [],
            "code_search_results": [],
            "clarification_analysis": [],
            "effectiveness_score": 0
        }
        
        # 1. 知识库搜索测试
        if self.test_kb_id:
            for query_text in scenario["knowledge_queries"]:
                try:
                    query = KnowledgeQuery(
                        query_text=query_text,
                        knowledge_base_ids=[self.test_kb_id],
                        limit=3
                    )
                    search_result = await self.knowledge_service.search_knowledge(query)
                    result["knowledge_search_results"].append({
                        "query": query_text,
                        "results_count": len(search_result.results),
                        "has_results": len(search_result.results) > 0
                    })
                except Exception as e:
                    result["knowledge_search_results"].append({
                        "query": query_text,
                        "error": str(e),
                        "has_results": False
                    })
        
        # 2. 代码库搜索测试
        codebases = self.codebase_manager.list_codebases()
        if codebases:
            codebase_ids = [cb.id for cb in codebases[:3]]
            
            for search_term in scenario["code_searches"]:
                try:
                    search_query = CodeSearchQuery(
                        query_text=search_term,
                        codebase_ids=codebase_ids
                    )
                    search_results = self.codebase_manager.search_components(search_query)
                    result["code_search_results"].append({
                        "query": search_term,
                        "results_count": len(search_results),
                        "has_results": len(search_results) > 0
                    })
                except Exception as e:
                    result["code_search_results"].append({
                        "query": search_term,
                        "error": str(e),
                        "has_results": False
                    })
        
        # 3. 需求澄清分析
        for clarification in scenario["expected_clarifications"]:
            # 模拟澄清分析过程
            analysis = self._analyze_clarification_need(
                clarification, 
                result["knowledge_search_results"],
                result["code_search_results"]
            )
            result["clarification_analysis"].append(analysis)
        
        # 4. 计算效果评分
        result["effectiveness_score"] = self._calculate_effectiveness_score(result)
        
        return result
    
    def _analyze_clarification_need(self, clarification, knowledge_results, code_results):
        """分析澄清需求"""
        # 基于搜索结果分析澄清的必要性和可行性
        knowledge_support = any(kr.get("has_results", False) for kr in knowledge_results)
        code_support = any(cr.get("has_results", False) for cr in code_results)
        
        return {
            "clarification": clarification,
            "knowledge_support": knowledge_support,
            "code_support": code_support,
            "priority": "high" if knowledge_support and code_support else "medium",
            "guidance_available": knowledge_support or code_support
        }
    
    def _calculate_effectiveness_score(self, result):
        """计算效果评分"""
        score = 0
        
        # 知识库搜索效果 (30%)
        knowledge_hits = sum(1 for kr in result["knowledge_search_results"] if kr.get("has_results", False))
        knowledge_total = len(result["knowledge_search_results"])
        if knowledge_total > 0:
            score += (knowledge_hits / knowledge_total) * 0.3
        
        # 代码库搜索效果 (30%)
        code_hits = sum(1 for cr in result["code_search_results"] if cr.get("has_results", False))
        code_total = len(result["code_search_results"])
        if code_total > 0:
            score += (code_hits / code_total) * 0.3
        
        # 澄清分析质量 (40%)
        clarification_quality = sum(1 for ca in result["clarification_analysis"] if ca.get("guidance_available", False))
        clarification_total = len(result["clarification_analysis"])
        if clarification_total > 0:
            score += (clarification_quality / clarification_total) * 0.4
        
        return round(score * 100, 1)
    
    def _generate_summary_report(self, results):
        """生成汇总报告"""
        print("\n" + "="*80)
        print("🎯 需求分析场景测试报告")
        print("="*80)
        
        total_score = sum(r["effectiveness_score"] for r in results)
        avg_score = total_score / len(results) if results else 0
        
        print(f"总体平均分: {avg_score:.1f}%")
        print(f"测试场景数: {len(results)}")
        
        print("\n📊 各场景详细结果:")
        for result in results:
            print(f"\n🔸 {result['scenario']}")
            print(f"   效果评分: {result['effectiveness_score']}%")
            print(f"   知识库搜索: {len([kr for kr in result['knowledge_search_results'] if kr.get('has_results', False)])}/{len(result['knowledge_search_results'])} 命中")
            print(f"   代码库搜索: {len([cr for cr in result['code_search_results'] if cr.get('has_results', False)])}/{len(result['code_search_results'])} 命中")
            print(f"   澄清指导: {len([ca for ca in result['clarification_analysis'] if ca.get('guidance_available', False)])}/{len(result['clarification_analysis'])} 可用")
        
        print(f"\n🎯 总体评估:")
        if avg_score >= 80:
            print("   ✅ 优秀 - 系统在需求分析中表现优异，能有效支持各种场景")
        elif avg_score >= 60:
            print("   ✅ 良好 - 系统基本能够支持需求分析，部分场景需要改进")
        elif avg_score >= 40:
            print("   ⚠️ 中等 - 系统提供部分支持，需要大幅改进")
        else:
            print("   ❌ 待改进 - 系统在需求分析中支持有限，需要重点优化")
        
        print("\n💡 改进建议:")
        print("   • 丰富知识库内容，增加更多最佳实践和案例")
        print("   • 提升代码搜索的准确性和相关性")
        print("   • 加强不同模块间的数据整合")
        print("   • 优化需求澄清的智能引导")
        
        print("="*80)


async def main():
    """主函数"""
    tester = RequirementAnalysisScenarios()
    await tester.run_all_scenarios()


if __name__ == "__main__":
    asyncio.run(main())
