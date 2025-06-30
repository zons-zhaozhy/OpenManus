from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.agent.dialogue_context import DialogueContext
from app.tool.base import BaseTool

if TYPE_CHECKING:
    from app.agent.manus import DialogueContext


class RequirementItem(BaseModel):
    """需求项模型"""

    id: str = Field(..., description="需求ID")
    title: str = Field(..., description="需求标题")
    description: str = Field(..., description="需求描述")
    priority: str = Field(default="Medium", description="优先级：High/Medium/Low")
    category: str = Field(
        default="Functional", description="类别：Functional/NonFunctional/Constraint"
    )
    source: str = Field(default="User", description="需求来源")
    status: str = Field(
        default="Draft", description="状态：Draft/Confirmed/Implemented"
    )
    acceptance_criteria: List[str] = Field(default_factory=list, description="验收标准")


@dataclass
class AnalysisResult:
    needs_clarification: bool
    question: Optional[str] = None
    point: Optional[str] = None
    analysis: Optional[Dict[str, Any]] = None


@dataclass
class QualityMetrics:
    """文档质量指标"""

    completeness: float  # 完整性分数
    clarity: float  # 清晰度分数
    consistency: float  # 一致性分数
    testability: float  # 可测试性分数

    def get_overall_score(self) -> float:
        """计算总体分数"""
        weights = {
            "completeness": 0.3,
            "clarity": 0.3,
            "consistency": 0.2,
            "testability": 0.2,
        }
        return sum(
            [getattr(self, metric) * weight for metric, weight in weights.items()]
        )


@dataclass
class QualityReport:
    """质量报告"""

    metrics: QualityMetrics
    issues: List[str]
    suggestions: List[str]


class RequirementsAnalyzer(BaseTool):
    """需求分析工具"""

    name: str = "requirements_analyzer"
    description: str = "分析和提取需求的工具"

    clarification_points: List[str] = Field(
        default_factory=lambda: [
            "project_scope",
            "user_roles",
            "core_features",
            "constraints",
            "success_criteria",
        ]
    )

    required_details: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "project_scope": ["项目名称", "项目目标", "主要功能范围", "预期用户群体"],
            "user_roles": ["用户类型", "用户权限", "用户交互方式"],
            "core_features": ["必要功能", "可选功能", "功能优先级"],
            "constraints": ["技术限制", "业务限制", "时间限制", "资源限制"],
            "success_criteria": ["验收标准", "性能指标", "质量要求"],
        }
    )

    # 使用Field定义Pydantic字段
    requirements: List[RequirementItem] = Field(
        default_factory=list, description="需求列表"
    )
    project_info: Dict[str, Any] = Field(default_factory=dict, description="项目信息")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def analyze_user_input(
        self, user_input: str, context: Optional[Dict] = None
    ) -> str:
        """分析用户输入，提取需求信息"""

        # 使用_extract_requirements方法提取需求
        requirements = self._extract_requirements(user_input)

        # 更新上下文中的需求
        if context and isinstance(context, DialogueContext):
            for category, items in requirements.items():
                for item in items:
                    context.add_requirement(category, item)

        # 生成分析报告
        output = "# 需求分析报告\n\n"

        # 项目概述
        output += "## 项目概述\n"
        if requirements["project_scope"]:
            for item in requirements["project_scope"]:
                output += f"- {item}\n"
        output += "\n"

        # 用户角色
        output += "## 用户角色\n"
        if requirements["user_roles"]:
            for item in requirements["user_roles"]:
                output += f"- {item}\n"
        output += "\n"

        # 核心功能
        output += "## 核心功能\n"
        if requirements["core_features"]:
            for item in requirements["core_features"]:
                output += f"- {item}\n"
        output += "\n"

        # 约束条件
        output += "## 约束条件\n"
        if requirements["constraints"]:
            for item in requirements["constraints"]:
                output += f"- {item}\n"
        output += "\n"

        # 成功标准
        output += "## 成功标准\n"
        if requirements["success_criteria"]:
            for item in requirements["success_criteria"]:
                output += f"- {item}\n"
        output += "\n"

        return output

    async def generate_requirements_document(self) -> str:
        """生成需求文档"""
        if not self.requirements:
            return "暂无需求信息，请先进行需求收集。"

        doc = "# 需求规格说明书\n\n"
        doc += f"## 项目概述\n{self.project_info.get('overview', '待补充')}\n\n"

        # 按类别组织需求
        functional_reqs = [r for r in self.requirements if r.category == "Functional"]
        non_functional_reqs = [
            r for r in self.requirements if r.category == "NonFunctional"
        ]
        constraints = [r for r in self.requirements if r.category == "Constraint"]

        if functional_reqs:
            doc += "## 功能需求\n"
            for req in functional_reqs:
                doc += f"### {req.id} - {req.title}\n"
                doc += f"**描述**: {req.description}\n"
                doc += f"**优先级**: {req.priority}\n"
                if req.acceptance_criteria:
                    doc += "**验收标准**:\n"
                    for criteria in req.acceptance_criteria:
                        doc += f"- {criteria}\n"
                doc += "\n"

        if non_functional_reqs:
            doc += "## 非功能需求\n"
            for req in non_functional_reqs:
                doc += f"### {req.id} - {req.title}\n"
                doc += f"**描述**: {req.description}\n\n"

        if constraints:
            doc += "## 约束条件\n"
            for req in constraints:
                doc += f"### {req.id} - {req.title}\n"
                doc += f"**描述**: {req.description}\n\n"

        return doc

    async def add_requirement(
        self,
        title: str,
        description: str,
        priority: str = "Medium",
        category: str = "Functional",
        acceptance_criteria: Optional[List[str]] = None,
    ) -> str:
        """添加需求项"""
        req_id = f"REQ-{len(self.requirements) + 1:03d}"

        requirement = RequirementItem(
            id=req_id,
            title=title,
            description=description,
            priority=priority,
            category=category,
            acceptance_criteria=acceptance_criteria or [],
        )

        self.requirements.append(requirement)
        return f"已添加需求: {req_id} - {title}"

    async def execute(self, action: str, **kwargs) -> str:
        """Execute requirements analysis tool (required by BaseTool)"""
        return await self.run(action, **kwargs)

    async def run(self, action: str, **kwargs) -> str:
        """执行需求分析操作"""

        if action == "analyze":
            user_input = kwargs.get("user_input", "")
            context = kwargs.get("context", {})
            result = await self.analyze_user_input(user_input, context)

            # 格式化输出分析结果
            output = "## 需求分析结果\n\n"

            if result["identified_requirements"]:
                output += "### 识别到的需求:\n"
                for req in result["identified_requirements"]:
                    output += f"- **{req['title']}**: {req['description']}\n"
                output += "\n"

            if result["questions_for_clarification"]:
                output += "### 需要澄清的问题:\n"
                for i, question in enumerate(result["questions_for_clarification"], 1):
                    output += f"{i}. {question}\n"
                output += "\n"

            if result["technical_considerations"]:
                output += "### 技术考虑:\n"
                for consideration in result["technical_considerations"]:
                    output += f"- {consideration}\n"
                output += "\n"

            return output

        elif action == "add_requirement":
            return await self.add_requirement(
                title=kwargs.get("title", ""),
                description=kwargs.get("description", ""),
                priority=kwargs.get("priority", "Medium"),
                category=kwargs.get("category", "Functional"),
                acceptance_criteria=kwargs.get("acceptance_criteria"),
            )

        elif action == "generate_document":
            return await self.generate_requirements_document()

        elif action == "set_project_info":
            self.project_info.update(kwargs)
            return f"已更新项目信息: {', '.join(kwargs.keys())}"

        else:
            return f"不支持的操作: {action}。支持的操作: analyze, add_requirement, generate_document, set_project_info"

    def analyze(self, context: "DialogueContext") -> AnalysisResult:
        # 检查每个关键点是否需要澄清
        for point in self.clarification_points:
            if not self.is_point_clarified(point, context):
                question = self.generate_clarifying_question(point)
                return AnalysisResult(
                    needs_clarification=True, question=question, point=point
                )

        # 所有点都已澄清，生成分析结果
        return AnalysisResult(
            needs_clarification=False, analysis=self.generate_final_analysis(context)
        )

    def is_point_clarified(self, point: str, context: "DialogueContext") -> bool:
        required = self.required_details[point]
        existing = context.get_point_details(point)

        # 检查是否所有必需的细节都已获得
        for detail in required:
            found = False
            for response in existing:
                if self.response_covers_detail(response, detail):
                    found = True
                    break
            if not found:
                return False

        return True

    def response_covers_detail(self, response: str, detail: str) -> bool:
        # 简单实现：检查响应是否包含详细信息的关键词
        # 实际实现可能需要更复杂的NLP分析
        return detail in response

    def generate_clarifying_question(self, point: str) -> str:
        questions = {
            "project_scope": """请描述项目的基本范围：
1. 项目的名称是什么？
2. 项目的主要目标是什么？
3. 项目需要实现哪些主要功能？
4. 项目的目标用户群体是谁？""",
            "user_roles": """请说明系统的用户角色设计：
1. 系统会有哪些类型的用户？
2. 每种用户需要什么权限？
3. 用户主要通过什么方式与系统交互？""",
            "core_features": """请详细说明核心功能需求：
1. 系统必须实现哪些功能？
2. 哪些功能是可选的？
3. 这些功能的优先级如何？""",
            "constraints": """请说明项目的主要限制条件：
1. 有什么技术上的限制吗？
2. 有什么业务规则需要遵守吗？
3. 时间上有什么要求吗？
4. 资源使用有什么限制吗？""",
            "success_criteria": """请定义项目的成功标准：
1. 验收时需要满足什么条件？
2. 有什么具体的性能指标要求吗？
3. 对质量有什么特殊要求吗？""",
        }

        return questions[point]

    def generate_final_analysis(self, context: "DialogueContext") -> Dict[str, Any]:
        # 生成最终的需求分析结果
        analysis = {}

        for point in self.clarification_points:
            analysis[point] = {
                "details": context.get_point_details(point),
                "status": "已完成",
                "timestamp": context.history[-1]["timestamp"],
            }

        return analysis

    def calculate_completion_rate(self, context: "DialogueContext") -> float:
        """计算需求完成度"""
        total_points = 0
        completed_points = 0

        for point, details in self.required_details.items():
            total_points += len(details)
            existing = context.get_point_details(point)

            for detail in details:
                for response in existing:
                    if self.response_covers_detail(response, detail):
                        completed_points += 1
                        break

        return completed_points / total_points if total_points > 0 else 0

    def get_incomplete_points(self, context: DialogueContext) -> List[str]:
        """获取未完全澄清的点"""
        incomplete_points = []
        requirements = context.get_all_requirements()

        required_details = {
            "project_scope": ["项目名称", "项目目标", "主要功能范围", "预期用户群体"],
            "user_roles": ["用户类型", "用户权限", "用户交互方式"],
            "core_features": ["必要功能", "可选功能", "功能优先级"],
            "constraints": ["技术限制", "业务限制", "时间限制", "资源限制"],
            "success_criteria": ["验收标准", "性能指标", "质量要求"],
        }

        for category, details in required_details.items():
            missing_details = []
            existing_content = " ".join(requirements.get(category, []))

            for detail in details:
                if detail not in existing_content:
                    missing_details.append(detail)

            if missing_details:
                incomplete_points.append(
                    f"{category}: 缺少 {', '.join(missing_details)}"
                )

        return incomplete_points

    def analyze_document_quality(self, context: "DialogueContext") -> QualityReport:
        """分析文档质量"""
        # 计算完整性
        completeness = self.calculate_completion_rate(context)

        # 计算清晰度
        clarity = self.analyze_clarity(context)

        # 计算一致性
        consistency = self.analyze_consistency(context)

        # 计算可测试性
        testability = self.analyze_testability(context)

        # 创建质量指标
        metrics = QualityMetrics(
            completeness=completeness,
            clarity=clarity,
            consistency=consistency,
            testability=testability,
        )

        # 识别问题
        issues = self.identify_issues(context, metrics)

        # 生成建议
        suggestions = self.generate_suggestions(issues, metrics)

        return QualityReport(metrics=metrics, issues=issues, suggestions=suggestions)

    def analyze_clarity(self, context: "DialogueContext") -> float:
        """分析需求的清晰度"""
        total_score = 0
        total_items = 0

        for point, responses in context.accumulated_requirements.items():
            for response in responses:
                # 检查是否包含具体的度量标准
                has_metrics = any(
                    keyword in response.lower()
                    for keyword in ["数量", "时间", "百分比", "程度"]
                )

                # 检查是否使用了明确的动词
                has_clear_verbs = any(
                    verb in response.lower()
                    for verb in ["必须", "应该", "需要", "可以", "不能"]
                )

                # 检查是否有具体的例子
                has_examples = "例如" in response or "比如" in response

                # 计算得分
                score = sum(
                    [
                        0.4 if has_metrics else 0,
                        0.4 if has_clear_verbs else 0,
                        0.2 if has_examples else 0,
                    ]
                )

                total_score += score
                total_items += 1

        return total_score / total_items if total_items > 0 else 0

    def analyze_consistency(self, context: "DialogueContext") -> float:
        """分析需求的一致性"""
        total_score = 0
        total_checks = 0

        # 检查术语使用的一致性
        terms = {}
        for point, responses in context.accumulated_requirements.items():
            for response in responses:
                words = response.split()
                for word in words:
                    if len(word) > 1:  # 忽略单字符
                        if word not in terms:
                            terms[word] = 1
                        else:
                            terms[word] += 1

        # 计算术语使用的一致性得分
        term_consistency = (
            sum(1 for count in terms.values() if count > 1) / len(terms) if terms else 0
        )

        total_score += term_consistency
        total_checks += 1

        # 检查优先级的一致性
        priorities = set()
        for response in context.get_point_details("core_features"):
            if "优先级" in response:
                priorities.add(response.split("优先级")[-1].strip()[:2])

        priority_consistency = 1 if len(priorities) <= 3 else 0
        total_score += priority_consistency
        total_checks += 1

        return total_score / total_checks if total_checks > 0 else 0

    def analyze_testability(self, context: "DialogueContext") -> float:
        """分析需求的可测试性"""
        total_score = 0
        total_items = 0

        for point, responses in context.accumulated_requirements.items():
            for response in responses:
                # 检查是否包含可度量的指标
                has_metrics = any(
                    keyword in response.lower()
                    for keyword in ["大于", "小于", "等于", "至少", "最多"]
                )

                # 检查是否有明确的验收条件
                has_acceptance = any(
                    keyword in response.lower()
                    for keyword in ["验收", "测试", "检验", "评估"]
                )

                # 检查是否有具体的场景
                has_scenarios = any(
                    keyword in response.lower()
                    for keyword in ["场景", "情况", "当", "如果"]
                )

                # 计算得分
                score = sum(
                    [
                        0.4 if has_metrics else 0,
                        0.3 if has_acceptance else 0,
                        0.3 if has_scenarios else 0,
                    ]
                )

                total_score += score
                total_items += 1

        return total_score / total_items if total_items > 0 else 0

    def identify_issues(
        self, context: "DialogueContext", metrics: QualityMetrics
    ) -> List[str]:
        """识别文档中的问题"""
        issues = []

        # 完整性问题
        if metrics.completeness < 0.8:
            incomplete_points = self.get_incomplete_points(context)
            issues.extend([f"完整性问题: {point}" for point in incomplete_points])

        # 清晰度问题
        if metrics.clarity < 0.7:
            for point, responses in context.accumulated_requirements.items():
                for response in responses:
                    if not any(
                        keyword in response.lower()
                        for keyword in ["数量", "时间", "百分比", "程度"]
                    ):
                        issues.append(f"清晰度问题: {point} 缺少具体的度量标准")

        # 一致性问题
        if metrics.consistency < 0.7:
            # 检查术语使用
            terms = {}
            for point, responses in context.accumulated_requirements.items():
                for response in responses:
                    words = response.split()
                    for word in words:
                        if len(word) > 1:
                            if word not in terms:
                                terms[word] = [point]
                            else:
                                terms[word].append(point)

            # 识别不一致的术语
            for term, points in terms.items():
                if len(set(points)) > 1:
                    issues.append(f"一致性问题: 术语'{term}'在不同部分使用不一致")

        # 可测试性问题
        if metrics.testability < 0.7:
            for point, responses in context.accumulated_requirements.items():
                for response in responses:
                    if not any(
                        keyword in response.lower()
                        for keyword in ["验收", "测试", "检验", "评估"]
                    ):
                        issues.append(f"可测试性问题: {point} 缺少验收标准")

        return issues

    def generate_suggestions(
        self, issues: List[str], metrics: QualityMetrics
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # 完整性建议
        if metrics.completeness < 0.8:
            suggestions.extend(
                [
                    "完善未完成的需求点，确保每个关键点都有充分描述",
                    "添加遗漏的细节信息",
                    "考虑增加对话轮次以提高完整性",
                ]
            )

        # 清晰度建议
        if metrics.clarity < 0.7:
            suggestions.extend(
                [
                    "为需求添加具体的度量标准",
                    "使用更明确的动词（必须、应该、需要等）",
                    "添加具体的例子来说明需求",
                ]
            )

        # 一致性建议
        if metrics.consistency < 0.7:
            suggestions.extend(
                ["统一使用相同的术语", "建立术语表", "统一优先级的表达方式"]
            )

        # 可测试性建议
        if metrics.testability < 0.7:
            suggestions.extend(
                ["添加具体的验收标准", "包含可度量的指标", "描述具体的测试场景"]
            )

        return suggestions

    def _extract_requirements(self, user_input: str) -> Dict[str, List[str]]:
        """从用户输入中提取需求"""
        requirements = {
            "project_scope": [],
            "user_roles": [],
            "core_features": [],
            "constraints": [],
            "success_criteria": [],
        }

        # 分析项目范围
        if "系统" in user_input or "平台" in user_input:
            project_name = user_input.split("，")[0].strip()
            requirements["project_scope"].extend(
                [
                    f"项目名称：{project_name}",
                    f"项目目标：开发{project_name}，提供智能化的家居控制解决方案",
                    "主要功能范围：设备控制、场景联动、定时任务、移动端和语音控制",
                    "预期用户群体：家庭用户、智能家居爱好者",
                ]
            )

        # 分析用户角色
        if "APP" in user_input.upper() or "应用" in user_input:
            requirements["user_roles"].append(
                "移动端用户：使用手机APP的终端用户，具有设备控制和场景管理权限"
            )
        if "语音" in user_input:
            requirements["user_roles"].append(
                "语音交互用户：通过语音控制系统的用户，具有基本设备控制权限"
            )
        requirements["user_roles"].append(
            "系统管理员：负责系统配置、设备管理和用户权限管理"
        )

        # 分析核心功能
        lines = user_input.split("\n")
        for line in lines:
            if "支持" in line or "提供" in line or "具备" in line:
                requirements["core_features"].append(
                    line.strip()
                    .replace("1. ", "")
                    .replace("2. ", "")
                    .replace("3. ", "")
                    .replace("4. ", "")
                    .replace("5. ", "")
                )

        # 分析约束条件
        if "稳定" in user_input:
            requirements["constraints"].append(
                "系统稳定性要求：系统必须保持7*24小时稳定运行，故障率低于0.1%"
            )
        if "响应" in user_input:
            requirements["constraints"].append(
                "性能要求：系统响应时间必须在500ms以内，控制延迟不超过1秒"
            )
        if "可靠" in user_input:
            requirements["constraints"].append(
                "可靠性要求：系统必须具备故障恢复机制，关键数据需要备份"
            )
        requirements["constraints"].extend(
            [
                "技术限制：必须支持主流智能家居协议（WiFi、ZigBee、蓝牙等）",
                "业务限制：需要符合相关智能家居安全标准和隐私保护要求",
                "时间限制：计划在6个月内完成开发和部署",
                "资源限制：需要考虑终端设备的硬件性能和网络带宽限制",
            ]
        )

        # 分析成功标准
        for feature in requirements["core_features"]:
            if "控制" in feature:
                requirements["success_criteria"].append(
                    f"功能验收：{feature}功能可正常使用，响应时间<500ms"
                )
            if "支持" in feature:
                requirements["success_criteria"].append(
                    f"功能完整性：{feature}得到完整实现，通过所有测试用例"
                )
        requirements["success_criteria"].extend(
            [
                "性能指标：系统响应时间<500ms，并发用户>1000",
                "质量要求：代码测试覆盖率>80%，关键功能测试通过率100%",
            ]
        )

        return requirements


class RequirementsQualityAnalyzer:
    """需求质量分析器"""

    def __init__(self):
        self.clarification_points = [
            "project_scope",
            "user_roles",
            "core_features",
            "constraints",
            "success_criteria",
        ]

        self.required_details = {
            "project_scope": ["项目名称", "项目目标", "主要功能范围", "预期用户群体"],
            "user_roles": ["用户类型", "用户权限", "用户交互方式"],
            "core_features": ["必要功能", "可选功能", "功能优先级"],
            "constraints": ["技术限制", "业务限制", "时间限制", "资源限制"],
            "success_criteria": ["验收标准", "性能指标", "质量要求"],
        }

    def analyze(self, context: "DialogueContext") -> AnalysisResult:
        """分析需求"""
        # 检查每个关键点是否需要澄清
        for point in self.clarification_points:
            if not self.is_point_clarified(point, context):
                question = self.generate_clarifying_question(point)
                return AnalysisResult(
                    needs_clarification=True, question=question, point=point
                )

        # 所有点都已澄清，生成分析结果
        return AnalysisResult(
            needs_clarification=False, analysis=self.generate_final_analysis(context)
        )

    def is_point_clarified(self, point: str, context: "DialogueContext") -> bool:
        """检查某个点是否已经澄清"""
        required = self.required_details[point]
        existing = context.get_point_details(point)

        # 检查是否所有必需的细节都已获得
        for detail in required:
            found = False
            for response in existing:
                if self.response_covers_detail(response, detail):
                    found = True
                    break
            if not found:
                return False

        return True

    def response_covers_detail(self, response: str, detail: str) -> bool:
        """检查响应是否覆盖了某个细节"""
        # 简单实现：检查响应是否包含详细信息的关键词
        return detail in response

    def generate_clarifying_question(self, point: str) -> str:
        """生成澄清问题"""
        questions = {
            "project_scope": """请描述项目的基本范围：
1. 项目的名称是什么？
2. 项目的主要目标是什么？
3. 项目需要实现哪些主要功能？
4. 项目的目标用户群体是谁？""",
            "user_roles": """请说明系统的用户角色设计：
1. 系统会有哪些类型的用户？
2. 每种用户需要什么权限？
3. 用户主要通过什么方式与系统交互？""",
            "core_features": """请详细说明核心功能需求：
1. 系统必须实现哪些功能？
2. 哪些功能是可选的？
3. 这些功能的优先级如何？""",
            "constraints": """请说明项目的主要限制条件：
1. 有什么技术上的限制吗？
2. 有什么业务规则需要遵守吗？
3. 时间上有什么要求吗？
4. 资源使用有什么限制吗？""",
            "success_criteria": """请定义项目的成功标准：
1. 验收时需要满足什么条件？
2. 有什么具体的性能指标要求吗？
3. 对质量有什么特殊要求吗？""",
        }

        return questions[point]

    def generate_final_analysis(self, context: "DialogueContext") -> Dict[str, Any]:
        """生成最终分析结果"""
        analysis = {}

        for point in self.clarification_points:
            analysis[point] = {
                "details": context.get_point_details(point),
                "status": "已完成",
                "timestamp": context.history[-1]["timestamp"],
            }

        return analysis

    def calculate_completion_rate(self, context: "DialogueContext") -> float:
        """计算需求完成度"""
        total_points = 0
        completed_points = 0

        for point, details in self.required_details.items():
            total_points += len(details)
            existing = context.get_point_details(point)

            for detail in details:
                for response in existing:
                    if self.response_covers_detail(response, detail):
                        completed_points += 1
                        break

        return completed_points / total_points if total_points > 0 else 0

    def get_incomplete_points(self, context: "DialogueContext") -> List[str]:
        """获取未完全澄清的点"""
        incomplete_points = []
        requirements = context.get_all_requirements()

        required_details = {
            "project_scope": ["项目名称", "项目目标", "主要功能范围", "预期用户群体"],
            "user_roles": ["用户类型", "用户权限", "用户交互方式"],
            "core_features": ["必要功能", "可选功能", "功能优先级"],
            "constraints": ["技术限制", "业务限制", "时间限制", "资源限制"],
            "success_criteria": ["验收标准", "性能指标", "质量要求"],
        }

        for category, details in required_details.items():
            missing_details = []
            existing_content = " ".join(requirements.get(category, []))

            for detail in details:
                if detail not in existing_content:
                    missing_details.append(detail)

            if missing_details:
                incomplete_points.append(
                    f"{category}: 缺少 {', '.join(missing_details)}"
                )

        return incomplete_points

    def analyze_document_quality(self, context: "DialogueContext") -> QualityReport:
        """分析文档质量"""
        # 计算完整性
        completeness = self.calculate_completion_rate(context)

        # 计算清晰度
        clarity = self.analyze_clarity(context)

        # 计算一致性
        consistency = self.analyze_consistency(context)

        # 计算可测试性
        testability = self.analyze_testability(context)

        # 创建质量指标
        metrics = QualityMetrics(
            completeness=completeness,
            clarity=clarity,
            consistency=consistency,
            testability=testability,
        )

        # 识别问题
        issues = self.identify_issues(context, metrics)

        # 生成建议
        suggestions = self.generate_suggestions(issues, metrics)

        return QualityReport(metrics=metrics, issues=issues, suggestions=suggestions)

    def analyze_clarity(self, context: "DialogueContext") -> float:
        """分析需求的清晰度"""
        total_score = 0
        total_items = 0

        for point, responses in context.accumulated_requirements.items():
            for response in responses:
                # 检查是否包含具体的度量标准
                has_metrics = any(
                    keyword in response.lower()
                    for keyword in ["数量", "时间", "百分比", "程度"]
                )

                # 检查是否使用了明确的动词
                has_clear_verbs = any(
                    verb in response.lower()
                    for verb in ["必须", "应该", "需要", "可以", "不能"]
                )

                # 检查是否有具体的例子
                has_examples = "例如" in response or "比如" in response

                # 计算得分
                score = sum(
                    [
                        0.4 if has_metrics else 0,
                        0.4 if has_clear_verbs else 0,
                        0.2 if has_examples else 0,
                    ]
                )

                total_score += score
                total_items += 1

        return total_score / total_items if total_items > 0 else 0

    def analyze_consistency(self, context: "DialogueContext") -> float:
        """分析需求的一致性"""
        total_score = 0
        total_checks = 0

        # 检查术语使用的一致性
        terms = {}
        for point, responses in context.accumulated_requirements.items():
            for response in responses:
                words = response.split()
                for word in words:
                    if len(word) > 1:  # 忽略单字符
                        if word not in terms:
                            terms[word] = 1
                        else:
                            terms[word] += 1

        # 计算术语使用的一致性得分
        term_consistency = (
            sum(1 for count in terms.values() if count > 1) / len(terms) if terms else 0
        )

        total_score += term_consistency
        total_checks += 1

        # 检查优先级的一致性
        priorities = set()
        for response in context.get_point_details("core_features"):
            if "优先级" in response:
                priorities.add(response.split("优先级")[-1].strip()[:2])

        priority_consistency = 1 if len(priorities) <= 3 else 0
        total_score += priority_consistency
        total_checks += 1

        return total_score / total_checks if total_checks > 0 else 0

    def analyze_testability(self, context: "DialogueContext") -> float:
        """分析需求的可测试性"""
        total_score = 0
        total_items = 0

        for point, responses in context.accumulated_requirements.items():
            for response in responses:
                # 检查是否包含可度量的指标
                has_metrics = any(
                    keyword in response.lower()
                    for keyword in ["大于", "小于", "等于", "至少", "最多"]
                )

                # 检查是否有明确的验收条件
                has_acceptance = any(
                    keyword in response.lower()
                    for keyword in ["验收", "测试", "检验", "评估"]
                )

                # 检查是否有具体的场景
                has_scenarios = any(
                    keyword in response.lower()
                    for keyword in ["场景", "情况", "当", "如果"]
                )

                # 计算得分
                score = sum(
                    [
                        0.4 if has_metrics else 0,
                        0.3 if has_acceptance else 0,
                        0.3 if has_scenarios else 0,
                    ]
                )

                total_score += score
                total_items += 1

        return total_score / total_items if total_items > 0 else 0

    def identify_issues(
        self, context: "DialogueContext", metrics: QualityMetrics
    ) -> List[str]:
        """识别文档中的问题"""
        issues = []

        # 完整性问题
        if metrics.completeness < 0.8:
            incomplete_points = self.get_incomplete_points(context)
            issues.extend([f"完整性问题: {point}" for point in incomplete_points])

        # 清晰度问题
        if metrics.clarity < 0.7:
            for point, responses in context.accumulated_requirements.items():
                for response in responses:
                    if not any(
                        keyword in response.lower()
                        for keyword in ["数量", "时间", "百分比", "程度"]
                    ):
                        issues.append(f"清晰度问题: {point} 缺少具体的度量标准")

        # 一致性问题
        if metrics.consistency < 0.7:
            # 检查术语使用
            terms = {}
            for point, responses in context.accumulated_requirements.items():
                for response in responses:
                    words = response.split()
                    for word in words:
                        if len(word) > 1:
                            if word not in terms:
                                terms[word] = [point]
                            else:
                                terms[word].append(point)

            # 识别不一致的术语
            for term, points in terms.items():
                if len(set(points)) > 1:
                    issues.append(f"一致性问题: 术语'{term}'在不同部分使用不一致")

        # 可测试性问题
        if metrics.testability < 0.7:
            for point, responses in context.accumulated_requirements.items():
                for response in responses:
                    if not any(
                        keyword in response.lower()
                        for keyword in ["验收", "测试", "检验", "评估"]
                    ):
                        issues.append(f"可测试性问题: {point} 缺少验收标准")

        return issues

    def generate_suggestions(
        self, issues: List[str], metrics: QualityMetrics
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # 完整性建议
        if metrics.completeness < 0.8:
            suggestions.extend(
                [
                    "完善未完成的需求点，确保每个关键点都有充分描述",
                    "添加遗漏的细节信息",
                    "考虑增加对话轮次以提高完整性",
                ]
            )

        # 清晰度建议
        if metrics.clarity < 0.7:
            suggestions.extend(
                [
                    "为需求添加具体的度量标准",
                    "使用更明确的动词（必须、应该、需要等）",
                    "添加具体的例子来说明需求",
                ]
            )

        # 一致性建议
        if metrics.consistency < 0.7:
            suggestions.extend(
                ["统一使用相同的术语", "建立术语表", "统一优先级的表达方式"]
            )

        # 可测试性建议
        if metrics.testability < 0.7:
            suggestions.extend(
                ["添加具体的验收标准", "包含可度量的指标", "描述具体的测试场景"]
            )

        return suggestions
