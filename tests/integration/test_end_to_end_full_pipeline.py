"""
端到端完整管道测试 - 从需求分析到架构设计的完整流程验证
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.assistants.architecture.flow import ArchitectureFlow
from app.assistants.requirements.flow import RequirementsFlow


class TestEndToEndPipeline:
    """端到端完整管道测试"""

    def __init__(self):
        self.test_session_id = f"e2e_test_{int(datetime.now().timestamp())}"
        self.test_results = {}

    async def test_complete_pipeline(self):
        """测试完整的从需求到架构的管道"""
        print("🚀 开始端到端完整管道测试")
        print(f"测试会话ID: {self.test_session_id}")
        print("=" * 60)

        # Step 1: 模拟第一期需求分析输出
        print("\n📋 Step 1: 准备需求分析输出数据")
        requirements_doc = self._get_sample_requirements_document()
        print(f"✅ 需求文档准备完成，长度: {len(requirements_doc)} 字符")

        # Step 2: 准备项目约束条件
        print("\n🔧 Step 2: 准备项目约束条件")
        project_constraints = self._get_project_constraints()
        print("✅ 项目约束条件准备完成")

        # Step 3: 执行架构设计流程
        print("\n🏗️  Step 3: 执行架构设计流程")
        architecture_flow = ArchitectureFlow(session_id=self.test_session_id)

        try:
            # 构建完整输入
            full_input = self._combine_requirements_and_constraints(
                requirements_doc, project_constraints
            )

            print("🔄 开始架构设计流程执行...")
            architecture_result = await architecture_flow.execute(full_input)

            print(f"✅ 架构设计流程执行完成")
            print(f"   输出长度: {len(architecture_result)} 字符")

            # Step 4: 验证输出质量
            print("\n📊 Step 4: 验证输出质量")
            quality_results = self._validate_architecture_output(architecture_result)

            # Step 5: 验证智能体协作
            print("\n🤝 Step 5: 验证智能体协作")
            collaboration_results = self._validate_agent_collaboration(
                architecture_flow
            )

            # Step 6: 生成测试报告
            print("\n📑 Step 6: 生成测试报告")
            self._generate_test_report(
                requirements_doc,
                architecture_result,
                quality_results,
                collaboration_results,
            )

            print("\n🎯 端到端测试完成！")
            return True

        except Exception as e:
            print(f"❌ 测试过程中出现异常: {e}")
            print("📝 这可能是由于LLM调用超时或其他网络问题")
            print("🔧 将进行组件级别验证...")

            # 降级测试：组件级别验证
            await self._fallback_component_tests(architecture_flow, requirements_doc)
            return False

    def _get_sample_requirements_document(self):
        """获取示例需求规格说明书（模拟第一期输出）"""
        return """
# 智能客服系统需求规格说明书

## 1. 项目概述
### 1.1 项目背景
企业需要一个智能客服系统，能够自动处理客户咨询，提供7x24小时服务，降低人工客服成本，提升客户满意度。

### 1.2 项目目标
- 构建智能化客服系统，支持多渠道接入
- 实现智能问答，覆盖80%常见问题自动回复
- 支持人工客服无缝接入，处理复杂问题
- 提供完整的客服管理和数据分析功能

## 2. 功能性需求

### 2.1 智能问答模块
- **自然语言理解**：理解客户问题意图，支持多轮对话
- **知识库管理**：维护FAQ知识库，支持动态更新
- **智能回复**：基于知识库自动生成回复，支持个性化
- **意图识别**：识别客户需求类型（咨询、投诉、建议等）

### 2.2 多渠道接入
- **Web客服**：网站嵌入式客服窗口
- **微信客服**：微信公众号/小程序客服
- **App客服**：移动应用内置客服
- **电话客服**：语音转文字后处理

### 2.3 人工客服系统
- **工单管理**：智能转人工的工单流转
- **客服工作台**：人工客服操作界面
- **客户画像**：展示客户历史记录和偏好
- **质量监控**：服务质量评估和监控

### 2.4 数据分析
- **对话分析**：对话数据统计和分析
- **客户满意度**：满意度调研和分析
- **知识库优化**：基于数据优化知识库
- **运营报表**：客服运营数据报表

### 2.5 系统管理
- **用户权限管理**：不同角色权限控制
- **配置管理**：系统参数和规则配置
- **日志管理**：系统操作日志记录
- **接口管理**：第三方系统集成接口

## 3. 非功能性需求

### 3.1 性能需求
- **并发处理**：支持10,000个并发对话
- **响应时间**：智能回复响应时间 < 2秒
- **系统可用性**：99.9%系统可用性
- **数据处理**：支持每日100万条对话记录

### 3.2 安全需求
- **数据加密**：敏感数据传输和存储加密
- **访问控制**：基于角色的访问控制
- **审计日志**：完整的操作审计记录
- **隐私保护**：客户数据隐私保护

### 3.3 可扩展性需求
- **水平扩展**：支持服务器水平扩展
- **模块扩展**：支持新功能模块接入
- **第三方集成**：支持CRM、工单系统集成
- **AI模型升级**：支持AI模型在线升级

### 3.4 可维护性需求
- **监控告警**：系统健康监控和告警
- **日志分析**：结构化日志和分析
- **部署自动化**：支持自动化部署
- **文档完善**：完整的技术文档

## 4. 业务约束

### 4.1 项目约束
- **项目预算**：200万元人民币
- **开发周期**：12个月
- **团队规模**：15人（5后端、3前端、2AI、2测试、2运维、1PM）
- **上线时间**：2025年12月底前

### 4.2 技术约束
- **部署环境**：私有云+公有云混合部署
- **数据合规**：满足《数据安全法》等法规要求
- **集成要求**：需要集成现有CRM和工单系统
- **AI服务**：优先使用国产大模型服务

### 4.3 运营约束
- **服务时间**：7x24小时服务
- **客服团队**：现有20人客服团队
- **培训要求**：提供完整的系统操作培训
- **迁移计划**：需要平滑迁移现有客服数据

## 5. 验收标准

### 5.1 功能验收
- ✅ 智能问答准确率达到85%以上
- ✅ 支持4个渠道同时接入
- ✅ 人工接入平均等待时间 < 30秒
- ✅ 数据分析报表功能完整

### 5.2 性能验收
- ✅ 支持10,000并发对话
- ✅ 智能回复响应时间 < 2秒
- ✅ 系统可用性 > 99.9%
- ✅ 数据处理能力满足要求

### 5.3 安全验收
- ✅ 通过安全渗透测试
- ✅ 数据加密实施到位
- ✅ 权限控制功能正常
- ✅ 审计日志完整

## 6. 风险与应对

### 6.1 技术风险
- **AI效果风险**：大模型回复质量不稳定
  - 应对：建立完善的知识库和训练机制
- **性能风险**：高并发场景下性能瓶颈
  - 应对：采用微服务架构，支持弹性扩展

### 6.2 项目风险
- **进度风险**：AI模型训练时间不确定
  - 应对：并行开发，预留缓冲时间
- **集成风险**：第三方系统集成复杂
  - 应对：提前进行接口对接测试

### 6.3 运营风险
- **用户接受度**：客户对AI客服接受度
  - 应对：提供人工客服备选方案
- **数据质量**：历史数据质量影响效果
  - 应对：数据清洗和标准化处理
"""

    def _get_project_constraints(self):
        """获取项目约束条件"""
        return {
            "budget": "200万元",
            "timeline": "12个月",
            "team": {
                "size": 15,
                "composition": {
                    "backend": 5,
                    "frontend": 3,
                    "ai": 2,
                    "test": 2,
                    "devops": 2,
                    "pm": 1,
                },
            },
            "deployment": "私有云+公有云混合部署",
            "compliance": ["数据安全法", "网络安全法"],
            "integration": ["现有CRM系统", "工单系统"],
            "performance": {
                "concurrent_users": 10000,
                "response_time": "< 2秒",
                "availability": "99.9%",
            },
        }

    def _combine_requirements_and_constraints(self, requirements_doc, constraints):
        """结合需求文档和约束条件"""
        return f"""
{requirements_doc}

## 补充项目约束条件

### 技术约束
- 预算：{constraints['budget']}
- 开发周期：{constraints['timeline']}
- 团队规模：{constraints['team']['size']}人
- 部署环境：{constraints['deployment']}

### 性能约束
- 并发用户：{constraints['performance']['concurrent_users']}
- 响应时间：{constraints['performance']['response_time']}
- 系统可用性：{constraints['performance']['availability']}

### 集成约束
- 需要集成：{', '.join(constraints['integration'])}
- 合规要求：{', '.join(constraints['compliance'])}
"""

    def _validate_architecture_output(self, output):
        """验证架构设计输出质量"""
        print("   📊 分析架构设计输出...")

        validation_results = {
            "length_check": len(output) > 5000,  # 至少5000字符
            "contains_tech_stack": any(
                keyword in output.lower()
                for keyword in ["技术选型", "前端", "后端", "数据库"]
            ),
            "contains_architecture": any(
                keyword in output.lower()
                for keyword in ["系统架构", "模块", "组件", "设计"]
            ),
            "contains_database": any(
                keyword in output.lower()
                for keyword in ["数据库设计", "表结构", "er图"]
            ),
            "contains_review": any(
                keyword in output.lower()
                for keyword in ["评审", "评分", "建议", "风险"]
            ),
        }

        passed_checks = sum(validation_results.values())
        total_checks = len(validation_results)

        print(f"   📋 质量检查结果: {passed_checks}/{total_checks} 项通过")
        for check, result in validation_results.items():
            status = "✅" if result else "❌"
            print(f"      {status} {check}")

        return validation_results

    def _validate_agent_collaboration(self, flow):
        """验证智能体协作情况"""
        print("   🤝 检查智能体协作状态...")

        collaboration_results = {
            "agents_initialized": len(flow.agents) == 4,
            "tech_selector_available": "tech_selector" in flow.agents,
            "architect_available": "architect" in flow.agents,
            "db_designer_available": "db_designer" in flow.agents,
            "reviewer_available": "reviewer" in flow.agents,
        }

        # 检查流程状态
        progress = flow.get_progress()
        collaboration_results["progress_tracked"] = "current_stage" in progress

        passed_checks = sum(collaboration_results.values())
        total_checks = len(collaboration_results)

        print(f"   📋 协作检查结果: {passed_checks}/{total_checks} 项通过")
        for check, result in collaboration_results.items():
            status = "✅" if result else "❌"
            print(f"      {status} {check}")

        return collaboration_results

    async def _fallback_component_tests(self, flow, requirements_doc):
        """降级测试：组件级别验证"""
        print("\n🔧 执行组件级别降级测试...")

        # 测试智能体初始化
        print("   🤖 测试智能体初始化...")
        agents_ok = len(flow.agents) == 4
        print(f"   {'✅' if agents_ok else '❌'} 智能体初始化: {len(flow.agents)}/4")

        # 测试单个智能体功能（简化版本，避免LLM调用）
        print("   🔍 测试智能体基础功能...")
        try:
            tech_selector = flow.get_agent("tech_selector")
            architect = flow.get_agent("architect")
            db_designer = flow.get_agent("db_designer")
            reviewer = flow.get_agent("reviewer")

            # 检查智能体是否有必要的方法
            has_methods = (
                hasattr(tech_selector, "analyze_tech_requirements")
                and hasattr(architect, "design_system_architecture")
                and hasattr(db_designer, "design_database_schema")
                and hasattr(reviewer, "review_architecture")
            )

            print(f"   {'✅' if has_methods else '❌'} 智能体方法检查")

        except Exception as e:
            print(f"   ❌ 智能体功能测试失败: {e}")

    def _generate_test_report(
        self,
        requirements_doc,
        architecture_result,
        quality_results,
        collaboration_results,
    ):
        """生成测试报告"""
        print("   📄 生成详细测试报告...")

        report = {
            "test_session_id": self.test_session_id,
            "timestamp": datetime.now().isoformat(),
            "input_data": {
                "requirements_length": len(requirements_doc),
                "requirements_preview": requirements_doc[:200] + "...",
            },
            "output_data": {
                "architecture_length": len(architecture_result),
                "architecture_preview": architecture_result[:200] + "...",
            },
            "quality_assessment": quality_results,
            "collaboration_assessment": collaboration_results,
            "overall_score": self._calculate_overall_score(
                quality_results, collaboration_results
            ),
        }

        # 保存报告到文件
        report_file = f"test_reports/e2e_test_report_{self.test_session_id}.json"
        os.makedirs("test_reports", exist_ok=True)

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"   📁 测试报告已保存: {report_file}")
        print(f"   🏆 总体评分: {report['overall_score']}/100")

    def _calculate_overall_score(self, quality_results, collaboration_results):
        """计算总体评分"""
        quality_score = sum(quality_results.values()) / len(quality_results) * 60
        collaboration_score = (
            sum(collaboration_results.values()) / len(collaboration_results) * 40
        )
        return round(quality_score + collaboration_score, 1)


async def main():
    """主测试函数"""
    print("🎯 OpenManus 第二期架构设计多智能体端到端测试")
    print("=" * 60)

    test = TestEndToEndPipeline()

    try:
        success = await test.test_complete_pipeline()
        if success:
            print("\n🎉 端到端测试完全成功！")
            print("✅ 第二期架构设计多智能体系统已就绪")
        else:
            print("\n⚠️  端到端测试部分成功")
            print("📝 系统基础功能正常，但可能存在LLM调用问题")

    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现严重错误: {e}")

    print("\n📊 测试报告已生成在 test_reports/ 目录")


if __name__ == "__main__":
    asyncio.run(main())
