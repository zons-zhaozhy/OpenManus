"""
需求分析知识库

包含需求分析的专业知识、最佳实践、常见模式等
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.logger import logger


@dataclass
class RequirementPattern:
    """需求模式"""

    name: str
    pattern: str
    description: str
    examples: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    difficulty_level: str = "中等"  # 简单、中等、复杂
    domain: str = "通用"


@dataclass
class BusinessDomain:
    """业务领域"""

    name: str
    description: str
    common_requirements: List[str] = field(default_factory=list)
    technical_constraints: List[str] = field(default_factory=list)
    stakeholders: List[str] = field(default_factory=list)
    typical_features: List[str] = field(default_factory=list)


@dataclass
class ClarificationTemplate:
    """澄清问题模板"""

    category: str
    questions: List[str] = field(default_factory=list)
    trigger_keywords: List[str] = field(default_factory=list)
    priority: int = 1  # 1-高优先级, 2-中优先级, 3-低优先级


class RequirementsKnowledgeBase:
    """需求分析知识库"""

    def __init__(self):
        self._init_requirement_patterns()
        self._init_business_domains()
        self._init_clarification_templates()
        self._init_quality_checklist()

    def _init_requirement_patterns(self):
        """初始化需求模式"""
        self.requirement_patterns = [
            RequirementPattern(
                name="功能性需求",
                pattern=r"(需要|要求|希望|想要).*(功能|特性|能力)",
                description="用户明确表达的功能需求",
                examples=[
                    "我需要一个用户登录功能",
                    "希望系统能够自动备份数据",
                    "要求支持多语言切换",
                ],
                keywords=["功能", "特性", "能力", "支持", "实现"],
                difficulty_level="简单",
            ),
            RequirementPattern(
                name="性能需求",
                pattern=r"(性能|速度|响应|处理|并发|吞吐)",
                description="系统性能相关要求",
                examples=[
                    "系统响应时间要在2秒内",
                    "支持1000个并发用户",
                    "数据处理速度要快",
                ],
                keywords=["性能", "速度", "响应时间", "并发", "吞吐量"],
                difficulty_level="中等",
            ),
            RequirementPattern(
                name="用户体验需求",
                pattern=r"(用户体验|界面|交互|操作|便捷|友好)",
                description="用户体验和界面相关需求",
                examples=["界面要简洁美观", "操作要便捷友好", "用户体验要好"],
                keywords=["界面", "交互", "体验", "操作", "友好"],
                difficulty_level="中等",
            ),
            RequirementPattern(
                name="集成需求",
                pattern=r"(集成|对接|连接|API|接口|第三方)",
                description="系统集成和对接需求",
                examples=["需要对接微信支付", "要集成邮件系统", "连接第三方API"],
                keywords=["集成", "对接", "API", "接口", "第三方"],
                difficulty_level="复杂",
            ),
            RequirementPattern(
                name="安全需求",
                pattern=r"(安全|权限|认证|授权|加密|防护)",
                description="系统安全相关需求",
                examples=["需要用户权限管理", "数据要加密存储", "防止SQL注入攻击"],
                keywords=["安全", "权限", "认证", "加密", "防护"],
                difficulty_level="复杂",
            ),
        ]

    def _init_business_domains(self):
        """初始化业务领域"""
        self.business_domains = [
            BusinessDomain(
                name="电子商务",
                description="在线购物、支付、订单管理等商务平台",
                common_requirements=[
                    "用户注册登录",
                    "商品展示",
                    "购物车",
                    "订单管理",
                    "支付集成",
                    "库存管理",
                    "用户评价",
                    "推荐系统",
                ],
                technical_constraints=[
                    "高并发处理",
                    "支付安全",
                    "数据一致性",
                    "库存实时性",
                ],
                stakeholders=["用户", "商家", "平台管理员", "支付服务商"],
                typical_features=["商品搜索", "订单跟踪", "优惠券", "会员系统"],
            ),
            BusinessDomain(
                name="内容管理",
                description="文章、新闻、博客等内容发布平台",
                common_requirements=[
                    "内容发布",
                    "分类管理",
                    "用户评论",
                    "内容搜索",
                    "权限管理",
                    "SEO优化",
                    "多媒体支持",
                ],
                technical_constraints=["内容安全", "搜索性能", "存储优化", "CDN加速"],
                stakeholders=["内容创作者", "读者", "编辑", "管理员"],
                typical_features=["富文本编辑", "标签系统", "访问统计", "社交分享"],
            ),
            BusinessDomain(
                name="企业管理",
                description="ERP、CRM、OA等企业内部管理系统",
                common_requirements=[
                    "组织架构管理",
                    "工作流引擎",
                    "报表统计",
                    "权限控制",
                    "数据导入导出",
                    "系统集成",
                    "移动端支持",
                ],
                technical_constraints=[
                    "数据安全",
                    "系统稳定性",
                    "集成复杂性",
                    "权限细粒度",
                ],
                stakeholders=["员工", "管理者", "HR", "IT管理员"],
                typical_features=["审批流程", "考勤管理", "绩效评估", "文档管理"],
            ),
            BusinessDomain(
                name="教育培训",
                description="在线教育、培训管理、知识分享平台",
                common_requirements=[
                    "课程管理",
                    "学员管理",
                    "在线学习",
                    "考试系统",
                    "进度跟踪",
                    "证书管理",
                    "互动交流",
                ],
                technical_constraints=[
                    "视频处理",
                    "大并发学习",
                    "防作弊",
                    "学习数据分析",
                ],
                stakeholders=["学员", "教师", "管理员", "家长"],
                typical_features=["视频播放", "作业提交", "讨论区", "学习计划"],
            ),
        ]

    def _init_clarification_templates(self):
        """初始化澄清问题模板"""
        self.clarification_templates = [
            ClarificationTemplate(
                category="用户角色",
                questions=[
                    "谁是这个系统的主要用户？",
                    "不同用户角色有什么不同的权限和功能需求？",
                    "预期有多少用户同时使用系统？",
                ],
                trigger_keywords=["用户", "角色", "权限", "登录"],
                priority=1,
            ),
            ClarificationTemplate(
                category="核心功能",
                questions=[
                    "系统最核心、最重要的功能是什么？",
                    "用户使用系统的主要工作流程是怎样的？",
                    "哪些功能是必需的，哪些是可选的？",
                ],
                trigger_keywords=["功能", "特性", "流程", "操作"],
                priority=1,
            ),
            ClarificationTemplate(
                category="数据管理",
                questions=[
                    "系统需要管理哪些类型的数据？",
                    "数据从哪里来，要如何导入？",
                    "需要与其他系统交换数据吗？",
                    "数据的安全性和备份有什么要求？",
                ],
                trigger_keywords=["数据", "信息", "存储", "导入", "导出"],
                priority=1,
            ),
            ClarificationTemplate(
                category="技术环境",
                questions=[
                    "系统部署在什么环境？（云端/本地/混合）",
                    "有没有特定的技术栈偏好？",
                    "需要支持哪些设备和浏览器？",
                    "与现有系统的集成要求是什么？",
                ],
                trigger_keywords=["部署", "技术", "平台", "集成", "兼容"],
                priority=2,
            ),
            ClarificationTemplate(
                category="性能要求",
                questions=[
                    "系统的响应时间要求是什么？",
                    "预期的并发用户数量是多少？",
                    "系统的可用性要求是多少？（如99.9%）",
                    "数据处理量级是多大？",
                ],
                trigger_keywords=["性能", "速度", "并发", "响应", "处理"],
                priority=2,
            ),
            ClarificationTemplate(
                category="界面体验",
                questions=[
                    "用户界面有什么特殊要求？",
                    "需要支持移动端吗？",
                    "有没有品牌色彩或设计风格要求？",
                    "用户的技术水平如何？需要什么程度的易用性？",
                ],
                trigger_keywords=["界面", "UI", "移动", "设计", "体验"],
                priority=2,
            ),
            ClarificationTemplate(
                category="业务规则",
                questions=[
                    "系统有哪些重要的业务规则？",
                    "什么情况下需要发送通知或提醒？",
                    "有没有审批流程或工作流要求？",
                    "数据的生命周期管理规则是什么？",
                ],
                trigger_keywords=["规则", "流程", "审批", "通知", "工作流"],
                priority=2,
            ),
            ClarificationTemplate(
                category="项目约束",
                questions=[
                    "项目的时间要求是什么？",
                    "预算范围大概是多少？",
                    "团队规模和技术能力如何？",
                    "有没有法规遵循要求？",
                ],
                trigger_keywords=["时间", "预算", "团队", "法规", "约束"],
                priority=3,
            ),
        ]

    def _init_quality_checklist(self):
        """初始化质量检查清单"""
        self.quality_checklist = {
            "完整性检查": [
                "是否包含了所有主要功能需求？",
                "非功能性需求是否明确？",
                "用户角色和权限是否定义清楚？",
                "数据模型是否完整？",
                "系统边界是否清晰？",
            ],
            "正确性检查": [
                "需求描述是否准确无歧义？",
                "业务规则是否正确？",
                "技术约束是否合理？",
                "用户流程是否符合实际业务？",
                "数据关系是否正确？",
            ],
            "一致性检查": [
                "不同章节的需求是否一致？",
                "术语使用是否统一？",
                "功能间是否存在冲突？",
                "数据定义是否一致？",
                "界面描述是否统一？",
            ],
            "可行性检查": [
                "技术实现是否可行？",
                "时间计划是否合理？",
                "资源需求是否现实？",
                "风险识别是否充分？",
                "成本估算是否合理？",
            ],
            "可测试性检查": [
                "需求是否可以验证和测试？",
                "验收标准是否明确？",
                "测试场景是否覆盖全面？",
                "性能指标是否可量化？",
                "异常情况处理是否完善？",
            ],
        }

    def identify_requirement_patterns(self, text: str) -> List[RequirementPattern]:
        """识别文本中的需求模式"""
        identified_patterns = []
        text_lower = text.lower()

        for pattern in self.requirement_patterns:
            # 使用正则表达式匹配
            if re.search(pattern.pattern, text_lower):
                identified_patterns.append(pattern)
                continue

            # 使用关键词匹配
            for keyword in pattern.keywords:
                if keyword in text_lower:
                    identified_patterns.append(pattern)
                    break

        return identified_patterns

    def suggest_business_domain(self, text: str) -> Optional[BusinessDomain]:
        """根据需求文本建议业务领域"""
        text_lower = text.lower()

        domain_scores = {}
        for domain in self.business_domains:
            score = 0

            # 检查常见需求匹配
            for req in domain.common_requirements:
                if req.lower() in text_lower:
                    score += 2

            # 检查典型特性匹配
            for feature in domain.typical_features:
                if feature.lower() in text_lower:
                    score += 1

            if score > 0:
                domain_scores[domain] = score

        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        return None

    def generate_clarification_questions(
        self, text: str, max_questions: int = 10
    ) -> List[str]:
        """生成澄清问题"""
        text_lower = text.lower()
        relevant_templates = []

        # 根据触发关键词找到相关模板
        for template in self.clarification_templates:
            for keyword in template.trigger_keywords:
                if keyword in text_lower:
                    relevant_templates.append(template)
                    break

        # 如果没有匹配的模板，使用高优先级模板
        if not relevant_templates:
            relevant_templates = [
                t for t in self.clarification_templates if t.priority == 1
            ]

        # 按优先级排序并选择问题
        relevant_templates.sort(key=lambda x: x.priority)
        questions = []

        for template in relevant_templates:
            questions.extend(template.questions)
            if len(questions) >= max_questions:
                break

        return questions[:max_questions]

    def get_quality_checklist_for_stage(self, stage: str) -> List[str]:
        """获取特定阶段的质量检查清单"""
        stage_mapping = {
            "需求澄清": ["完整性检查", "正确性检查"],
            "业务分析": ["完整性检查", "正确性检查", "一致性检查"],
            "文档编写": ["完整性检查", "正确性检查", "一致性检查", "可测试性检查"],
            "质量评审": list(self.quality_checklist.keys()),
        }

        relevant_categories = stage_mapping.get(stage, ["完整性检查"])
        checklist = []

        for category in relevant_categories:
            if category in self.quality_checklist:
                checklist.extend(self.quality_checklist[category])

        return checklist

    def search_knowledge(self, query: str) -> Dict[str, Any]:
        """搜索知识库"""
        query_lower = query.lower()
        results = {"patterns": [], "domains": [], "templates": [], "quality_items": []}

        # 搜索需求模式
        for pattern in self.requirement_patterns:
            if (
                query_lower in pattern.name.lower()
                or query_lower in pattern.description.lower()
                or any(query_lower in kw for kw in pattern.keywords)
            ):
                results["patterns"].append(pattern)

        # 搜索业务领域
        for domain in self.business_domains:
            if (
                query_lower in domain.name.lower()
                or query_lower in domain.description.lower()
            ):
                results["domains"].append(domain)

        # 搜索澄清模板
        for template in self.clarification_templates:
            if query_lower in template.category.lower() or any(
                query_lower in q.lower() for q in template.questions
            ):
                results["templates"].append(template)

        return results
