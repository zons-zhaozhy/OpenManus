"""需求评审工具"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import markdown
from pydantic import BaseModel, Field

from app.llm import get_llm
from app.prompt.requirements_review import format_requirements_review_prompt
from app.schema import Message
from app.tool.base import BaseTool


@dataclass
class ReviewResult:
    """评审结果"""

    business_value_score: float
    smart_score: float
    completeness_score: float
    consistency_score: float
    clarity_score: float
    testability_score: float
    blocking_issues: List[str]
    suggestions: List[str]
    review_timestamp: datetime = Field(default_factory=datetime.now)
    review_history: List[Dict[str, Any]] = Field(default_factory=list)


class RequirementsReviewer(BaseTool):
    """需求评审工具"""

    name: str = "requirements_reviewer"
    description: str = "使用LLM评估需求质量"

    def __init__(self):
        super().__init__()
        self.requirements: Dict[str, List[str]] = {}

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具"""
        if "requirements" not in kwargs:
            return {"error": "Missing requirements parameter"}

        try:
            self.requirements = kwargs["requirements"]
            result = await self.review_requirements(self.requirements)

            # 生成可视化图表
            visualizations = self._generate_visualizations(result)

            # 构建详细的评审报告
            report = {
                "scores": {
                    "business_value": result.business_value_score,
                    "smart": result.smart_score,
                    "completeness": result.completeness_score,
                    "consistency": result.consistency_score,
                    "clarity": result.clarity_score,
                    "testability": result.testability_score,
                },
                "blocking_issues": result.blocking_issues,
                "suggestions": result.suggestions,
                "timestamp": result.review_timestamp.isoformat(),
                "summary": self._generate_review_summary(result),
                "trends": self._analyze_trends(result),
                "visualizations": visualizations,
            }

            # 保存评审历史
            result.review_history.append(report)

            return report
        except Exception as e:
            return {
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat(),
            }

    async def review_requirements(
        self, requirements: Dict[str, List[str]]
    ) -> ReviewResult:
        """评审需求"""
        try:
            # 计算各项评分
            completeness_score = self._calculate_completion_rate(requirements)
            clarity_score = self._calculate_clarity_score(requirements)
            consistency_score = self._calculate_consistency_score(requirements)
            testability_score = self._calculate_testability_score(requirements)
            business_value_score = self._calculate_business_value_score(requirements)
            smart_score = self._calculate_smart_score(requirements)

            # 识别阻塞问题
            blocking_issues = []

            # 检查完整性问题
            required_details = {
                "project_scope": [
                    "项目名称",
                    "项目目标",
                    "主要功能范围",
                    "预期用户群体",
                ],
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
                    blocking_issues.append(
                        f"完整性问题: {category}: 缺少 {', '.join(missing_details)}"
                    )

            # 生成改进建议
            suggestions = [
                "完善未完成的需求点，确保每个关键点都有充分描述",
                "添加遗漏的细节信息",
                "考虑增加对话轮次以提高完整性",
            ]

            if business_value_score < 80:
                suggestions.extend(
                    [
                        "明确需求的业务价值和收益",
                        "添加可量化的业务指标",
                        "说明与项目目标的关联性",
                    ]
                )

            if smart_score < 80:
                suggestions.extend(
                    [
                        "使需求描述更具体和明确",
                        "添加可衡量的指标",
                        "确保需求在现有条件下可实现",
                        "明确时间要求和里程碑",
                    ]
                )

            if clarity_score < 80:
                suggestions.extend(
                    [
                        "为需求添加具体的度量标准",
                        "使用更明确的动词（必须、应该、需要等）",
                        "添加具体的例子来说明需求",
                    ]
                )

            if consistency_score < 80:
                suggestions.extend(
                    ["统一使用相同的术语", "建立术语表", "统一优先级的表达方式"]
                )

            if testability_score < 80:
                suggestions.extend(
                    ["添加具体的验收标准", "包含可度量的指标", "描述具体的测试场景"]
                )

            # 创建评审结果
            review_result = ReviewResult(
                business_value_score=business_value_score,
                smart_score=smart_score,
                completeness_score=completeness_score,
                consistency_score=consistency_score,
                clarity_score=clarity_score,
                testability_score=testability_score,
                blocking_issues=blocking_issues,
                suggestions=suggestions,
            )

            return review_result

        except Exception as e:
            raise Exception(f"需求评审失败: {str(e)}")

    def _parse_review_response(self, response: str) -> ReviewResult:
        """解析LLM的评审响应"""
        lines = response.split("\n")

        scores = {
            "business_value": 0.0,
            "smart": 0.0,
            "completeness": 0.0,
            "consistency": 0.0,
            "testability": 0.0,
        }

        blocking_issues = []
        suggestions = []

        current_section = ""

        try:
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 解析分数
                if "分" in line:
                    for key in scores.keys():
                        if key.replace("_", " ") in line.lower():
                            try:
                                # 提取分数（假设格式为 "XX分" 或 "XX/100"）
                                score_text = (
                                    line.split("：")[-1]
                                    .split("/")[0]
                                    .replace("分", "")
                                    .strip()
                                )
                                scores[key] = float(score_text) / 100
                            except (ValueError, IndexError):
                                continue

                # 识别阻塞项
                elif "阻塞项" in line:
                    current_section = "blocking"
                    issue = line.split("：")[-1].strip()
                    if issue:
                        blocking_issues.append(issue)

                # 收集建议
                elif "建议" in line:
                    current_section = "suggestions"
                    suggestion = line.split("：")[-1].strip()
                    if suggestion:
                        suggestions.append(suggestion)

                # 根据当前section继续收集内容
                elif current_section == "blocking" and line.startswith("- "):
                    blocking_issues.append(line[2:].strip())
                elif current_section == "suggestions" and line.startswith("- "):
                    suggestions.append(line[2:].strip())

        except Exception as e:
            # 如果解析出错，添加一个错误说明到建议中
            suggestions.append(f"解析评审结果时出现错误: {str(e)}")

        return ReviewResult(
            business_value_score=scores["business_value"],
            smart_score=scores["smart"],
            completeness_score=self._calculate_completion_rate(self.requirements),
            consistency_score=scores["consistency"],
            clarity_score=scores["clarity"],
            testability_score=scores["testability"],
            blocking_issues=blocking_issues,
            suggestions=suggestions,
        )

    def _calculate_completion_rate(self, requirements: Dict[str, List[str]]) -> float:
        """计算需求完成度"""
        total_sections = (
            5  # project_scope, user_roles, core_features, constraints, success_criteria
        )
        completed_sections = 0

        # 检查每个部分是否有内容
        if requirements.get("project_scope"):
            completed_sections += 1
        if requirements.get("user_roles"):
            completed_sections += 1
        if requirements.get("core_features"):
            completed_sections += 1
        if requirements.get("constraints"):
            completed_sections += 1
        if requirements.get("success_criteria"):
            completed_sections += 1

        # 基础完成度
        base_completion = (completed_sections / total_sections) * 100

        # 根据内容丰富度调整
        content_richness = 0
        for section_content in requirements.values():
            if section_content:
                content_richness += len(section_content)

        # 内容丰富度权重
        richness_factor = min(1.0, content_richness / 10)  # 每个部分平均2个需求点为基准

        # 最终完成度
        final_completion = base_completion * (0.7 + 0.3 * richness_factor)

        return round(final_completion, 1)

    def _calculate_clarity_score(self, requirements: Dict[str, List[str]]) -> float:
        """计算需求的清晰度分数"""
        total_score = 0
        total_items = 0

        for section_content in requirements.values():
            for requirement in section_content:
                # 检查是否包含具体的度量标准
                has_metrics = any(
                    keyword in requirement.lower()
                    for keyword in [
                        "数量",
                        "时间",
                        "百分比",
                        "程度",
                        "大于",
                        "小于",
                        "等于",
                        "至少",
                        "最多",
                    ]
                )

                # 检查是否使用了明确的动词
                has_clear_verbs = any(
                    verb in requirement.lower()
                    for verb in ["必须", "应该", "需要", "可以", "不能"]
                )

                # 检查是否有具体的例子
                has_examples = "例如" in requirement or "比如" in requirement

                # 计算得分
                score = sum(
                    [
                        0.4 if has_metrics else 0,  # 度量标准权重
                        0.4 if has_clear_verbs else 0,  # 明确动词权重
                        0.2 if has_examples else 0,  # 具体例子权重
                    ]
                )

                total_score += score
                total_items += 1

        # 避免除零错误
        if total_items == 0:
            return 0.0

        # 转换为百分制分数
        clarity_score = (total_score / total_items) * 100
        return round(clarity_score, 1)

    def _calculate_consistency_score(self, requirements: Dict[str, List[str]]) -> float:
        """计算需求一致性分数"""
        total_score = 0
        total_items = 0

        for section_content in requirements.values():
            for requirement in section_content:
                # 检查是否使用了相同的术语
                has_same_terms = all(
                    term in requirement.lower() for term in section_content
                )

                # 检查是否使用了相同的优先级表达方式
                has_same_priority_expression = all(
                    expression in requirement.lower() for expression in section_content
                )

                # 计算得分
                score = sum(
                    [
                        0.5 if has_same_terms else 0,  # 相同术语权重
                        (
                            0.5 if has_same_priority_expression else 0
                        ),  # 相同优先级表达权重
                    ]
                )

                total_score += score
                total_items += 1

        # 避免除零错误
        if total_items == 0:
            return 0.0

        # 转换为百分制分数
        consistency_score = (total_score / total_items) * 100
        return round(consistency_score, 1)

    def _calculate_testability_score(self, requirements: Dict[str, List[str]]) -> float:
        """计算需求的可测试性分数"""
        total_score = 0
        total_items = 0

        for section_content in requirements.values():
            for requirement in section_content:
                # 检查是否包含可度量的指标
                has_metrics = any(
                    keyword in requirement.lower()
                    for keyword in [
                        "大于",
                        "小于",
                        "等于",
                        "至少",
                        "最多",
                        "不超过",
                        "不少于",
                    ]
                )

                # 检查是否有明确的验收条件
                has_acceptance = any(
                    keyword in requirement.lower()
                    for keyword in ["验收", "测试", "检验", "评估", "验证", "确认"]
                )

                # 检查是否有具体的场景
                has_scenarios = any(
                    keyword in requirement.lower()
                    for keyword in ["场景", "情况", "当", "如果", "假设", "条件"]
                )

                # 检查是否有边界条件
                has_boundaries = any(
                    keyword in requirement.lower()
                    for keyword in ["边界", "极限", "最大", "最小", "异常", "错误"]
                )

                # 计算得分
                score = sum(
                    [
                        0.3 if has_metrics else 0,  # 可度量指标权重
                        0.3 if has_acceptance else 0,  # 验收条件权重
                        0.2 if has_scenarios else 0,  # 测试场景权重
                        0.2 if has_boundaries else 0,  # 边界条件权重
                    ]
                )

                total_score += score
                total_items += 1

        # 避免除零错误
        if total_items == 0:
            return 0.0

        # 转换为百分制分数
        testability_score = (total_score / total_items) * 100
        return round(testability_score, 1)

    def _calculate_business_value_score(
        self, requirements: Dict[str, List[str]]
    ) -> float:
        """计算需求的业务价值分数"""
        total_score = 0
        total_items = 0

        # 检查项目范围部分
        if "project_scope" in requirements:
            for requirement in requirements["project_scope"]:
                # 检查是否源自实际业务需要
                has_business_need = any(
                    keyword in requirement.lower()
                    for keyword in ["需求", "问题", "痛点", "改进", "优化", "提升"]
                )

                # 检查是否有明确的价值
                has_clear_value = any(
                    keyword in requirement.lower()
                    for keyword in ["价值", "收益", "效益", "节省", "提高", "增加"]
                )

                # 检查是否符合项目目标
                has_project_alignment = any(
                    keyword in requirement.lower()
                    for keyword in ["目标", "战略", "规划", "方向"]
                )

                # 检查是否有可量化的收益
                has_quantifiable_benefits = any(
                    keyword in requirement.lower()
                    for keyword in ["百分比", "数量", "金额", "比例", "程度"]
                )

                # 检查是否考虑了投资回报
                has_roi_consideration = any(
                    keyword in requirement.lower()
                    for keyword in ["投资", "成本", "回报", "roi", "收入"]
                )

                # 计算得分
                score = sum(
                    [
                        0.25 if has_business_need else 0,  # 业务需求权重
                        0.25 if has_clear_value else 0,  # 明确价值权重
                        0.2 if has_project_alignment else 0,  # 目标一致性权重
                        0.15 if has_quantifiable_benefits else 0,  # 可量化收益权重
                        0.15 if has_roi_consideration else 0,  # 投资回报权重
                    ]
                )

                total_score += score
                total_items += 1

        # 检查核心功能部分
        if "core_features" in requirements:
            for requirement in requirements["core_features"]:
                # 检查功能是否与业务价值相关
                has_value_alignment = any(
                    keyword in requirement.lower()
                    for keyword in ["价值", "收益", "效益", "业务", "重要", "关键"]
                )

                # 检查是否有优先级说明
                has_priority = any(
                    keyword in requirement.lower()
                    for keyword in ["优先级", "重要性", "必须", "应该", "可以"]
                )

                # 计算得分
                score = sum(
                    [
                        0.6 if has_value_alignment else 0,  # 业务价值关联权重
                        0.4 if has_priority else 0,  # 优先级说明权重
                    ]
                )

                total_score += score
                total_items += 1

        # 避免除零错误
        if total_items == 0:
            return 0.0

        # 转换为百分制分数
        business_value_score = (total_score / total_items) * 100
        return round(business_value_score, 1)

    def _calculate_smart_score(self, requirements: Dict[str, List[str]]) -> float:
        """计算需求的SMART原则分数"""
        total_score = 0
        total_items = 0

        for section_content in requirements.values():
            for requirement in section_content:
                # Specific（具体）
                is_specific = any(
                    keyword in requirement.lower()
                    for keyword in [
                        "具体",
                        "明确",
                        "详细",
                        "精确",
                        "准确",
                        "清晰",
                        "定义",
                        "规定",
                    ]
                ) and not any(
                    keyword in requirement.lower()
                    for keyword in ["模糊", "不确定", "可能", "也许"]
                )

                # Measurable（可衡量）
                is_measurable = any(
                    keyword in requirement.lower()
                    for keyword in [
                        "数量",
                        "时间",
                        "百分比",
                        "大于",
                        "小于",
                        "等于",
                        "至少",
                        "最多",
                        "不超过",
                    ]
                )

                # Achievable（可达成）
                is_achievable = not any(
                    keyword in requirement.lower()
                    for keyword in ["不可能", "难以实现", "无法", "不能"]
                ) and any(
                    keyword in requirement.lower()
                    for keyword in ["可以", "能够", "实现", "完成", "达到"]
                )

                # Relevant（相关）
                is_relevant = any(
                    keyword in requirement.lower()
                    for keyword in [
                        "目标",
                        "业务",
                        "价值",
                        "需求",
                        "用户",
                        "客户",
                        "相关",
                    ]
                )

                # Time-bound（时限）
                is_time_bound = any(
                    keyword in requirement.lower()
                    for keyword in [
                        "时间",
                        "期限",
                        "截止",
                        "完成时间",
                        "天内",
                        "周内",
                        "月内",
                        "年内",
                    ]
                )

                # 计算得分
                score = sum(
                    [
                        0.25 if is_specific else 0,  # 具体性权重
                        0.25 if is_measurable else 0,  # 可衡量性权重
                        0.2 if is_achievable else 0,  # 可达成性权重
                        0.15 if is_relevant else 0,  # 相关性权重
                        0.15 if is_time_bound else 0,  # 时限性权重
                    ]
                )

                total_score += score
                total_items += 1

        # 避免除零错误
        if total_items == 0:
            return 0.0

        # 转换为百分制分数
        smart_score = (total_score / total_items) * 100
        return round(smart_score, 1)

    def _generate_review_summary(self, result: ReviewResult) -> str:
        """生成评审总结"""
        # 计算总体得分
        overall_score = (
            result.business_value_score
            + result.smart_score
            + result.completeness_score
            + result.consistency_score
            + result.clarity_score
            + result.testability_score
        ) / 6

        # 确定总体状态
        if overall_score >= 90:
            status = "卓越"
        elif overall_score >= 80:
            status = "优秀"
        elif overall_score >= 70:
            status = "良好"
        elif overall_score >= 60:
            status = "及格"
        else:
            status = "需要改进"

        # 识别主要优势
        strengths = []
        if result.business_value_score >= 80:
            strengths.append("业务价值明确")
        if result.smart_score >= 80:
            strengths.append("符合SMART原则")
        if result.completeness_score >= 80:
            strengths.append("需求完整度高")
        if result.consistency_score >= 80:
            strengths.append("需求一致性好")
        if result.clarity_score >= 80:
            strengths.append("需求描述清晰")
        if result.testability_score >= 80:
            strengths.append("可测试性强")

        # 识别主要问题
        weaknesses = []
        if result.business_value_score < 60:
            weaknesses.append("业务价值不明确")
        if result.smart_score < 60:
            weaknesses.append("不符合SMART原则")
        if result.completeness_score < 60:
            weaknesses.append("需求不完整")
        if result.consistency_score < 60:
            weaknesses.append("需求不一致")
        if result.clarity_score < 60:
            weaknesses.append("需求描述不清晰")
        if result.testability_score < 60:
            weaknesses.append("可测试性差")

        # 生成总结文本
        summary = f"""# 需求评审总结

## 总体评价
- 总体得分：{overall_score:.1f}分
- 评估状态：{status}

## 主要指标
- 业务价值：{result.business_value_score}分
- SMART原则：{result.smart_score}分
- 完整性：{result.completeness_score}分
- 一致性：{result.consistency_score}分
- 清晰度：{result.clarity_score}分
- 可测试性：{result.testability_score}分

## 主要优势
{chr(10).join([f"- {strength}" for strength in strengths]) if strengths else "- 无明显优势"}

## 主要问题
{chr(10).join([f"- {weakness}" for weakness in weaknesses]) if weaknesses else "- 无明显问题"}

## 阻塞问题
{chr(10).join([f"- {issue}" for issue in result.blocking_issues]) if result.blocking_issues else "- 无阻塞问题"}

## 改进建议
{chr(10).join([f"- {suggestion}" for suggestion in result.suggestions])}"""

        return summary

    def _analyze_trends(self, result: ReviewResult) -> Dict[str, Any]:
        """分析评审趋势"""
        # 获取历史记录
        history = result.review_history

        # 如果历史记录少于2条，无法分析趋势
        if len(history) < 2:
            return {
                "trend_analysis": "历史数据不足，无法分析趋势",
                "score_trends": {},
                "issue_trends": [],
                "improvement_trends": [],
            }

        # 分析分数趋势
        score_trends = {}
        metrics = [
            "business_value",
            "smart",
            "completeness",
            "consistency",
            "clarity",
            "testability",
        ]

        for metric in metrics:
            scores = [h["scores"][metric] for h in history]
            current = scores[-1]
            previous = scores[-2]
            change = current - previous
            trend = "上升" if change > 0 else "下降" if change < 0 else "持平"
            score_trends[metric] = {
                "current": current,
                "previous": previous,
                "change": change,
                "trend": trend,
            }

        # 分析问题趋势
        current_issues = set(result.blocking_issues)
        previous_issues = set(history[-2]["blocking_issues"])
        new_issues = current_issues - previous_issues
        resolved_issues = previous_issues - current_issues
        persistent_issues = current_issues & previous_issues

        issue_trends = {
            "new_issues": list(new_issues),
            "resolved_issues": list(resolved_issues),
            "persistent_issues": list(persistent_issues),
        }

        # 分析改进趋势
        current_suggestions = set(result.suggestions)
        previous_suggestions = set(history[-2]["suggestions"])
        new_suggestions = current_suggestions - previous_suggestions
        implemented_suggestions = previous_suggestions - current_suggestions
        pending_suggestions = current_suggestions & previous_suggestions

        improvement_trends = {
            "new_suggestions": list(new_suggestions),
            "implemented_suggestions": list(implemented_suggestions),
            "pending_suggestions": list(pending_suggestions),
        }

        # 生成趋势分析总结
        trend_analysis = f"""# 趋势分析

## 分数趋势
{chr(10).join([f"- {metric}：{data['trend']} ({data['change']:+.1f}分)" for metric, data in score_trends.items()])}

## 问题趋势
- 新增问题：{len(new_issues)}个
- 已解决问题：{len(resolved_issues)}个
- 持续存在问题：{len(persistent_issues)}个

## 改进趋势
- 新增建议：{len(new_suggestions)}个
- 已实施建议：{len(implemented_suggestions)}个
- 待处理建议：{len(pending_suggestions)}个"""

        return {
            "trend_analysis": trend_analysis,
            "score_trends": score_trends,
            "issue_trends": issue_trends,
            "improvement_trends": improvement_trends,
        }

    def _generate_visualizations(self, result: ReviewResult) -> Dict[str, str]:
        """生成可视化图表"""
        try:
            # 生成雷达图数据
            radar_data = {
                "业务价值": result.business_value_score,
                "SMART原则": result.smart_score,
                "完整性": result.completeness_score,
                "一致性": result.consistency_score,
                "清晰度": result.clarity_score,
                "可测试性": result.testability_score,
            }

            # 生成雷达图
            radar_chart = f"""```mermaid
graph TD
    subgraph 需求质量雷达图
    A[业务价值 {radar_data['业务价值']}%] --- B[SMART原则 {radar_data['SMART原则']}%]
    B --- C[完整性 {radar_data['完整性']}%]
    C --- D[一致性 {radar_data['一致性']}%]
    D --- E[清晰度 {radar_data['清晰度']}%]
    E --- F[可测试性 {radar_data['可测试性']}%]
    F --- A
    end
```"""

            # 生成趋势图数据
            if len(result.review_history) >= 2:
                history = result.review_history[-2:]  # 只取最近两次记录
                trend_data = {
                    "业务价值": [h["scores"]["business_value"] for h in history],
                    "SMART原则": [h["scores"]["smart"] for h in history],
                    "完整性": [h["scores"]["completeness"] for h in history],
                    "一致性": [h["scores"]["consistency"] for h in history],
                    "清晰度": [h["scores"]["clarity"] for h in history],
                    "可测试性": [h["scores"]["testability"] for h in history],
                }

                # 生成趋势图
                trend_chart = f"""```mermaid
graph LR
    subgraph 需求质量趋势
    A[上次评审] --> B[本次评审]
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    end
```"""
            else:
                trend_chart = "历史数据不足，无法生成趋势图"

            # 生成问题分布图
            issue_types = {
                "业务价值问题": len(
                    [i for i in result.blocking_issues if "业务价值" in i]
                ),
                "SMART原则问题": len(
                    [i for i in result.blocking_issues if "SMART" in i]
                ),
                "完整性问题": len([i for i in result.blocking_issues if "完整性" in i]),
                "一致性问题": len([i for i in result.blocking_issues if "一致性" in i]),
                "清晰度问题": len([i for i in result.blocking_issues if "清晰度" in i]),
                "可测试性问题": len(
                    [i for i in result.blocking_issues if "可测试性" in i]
                ),
            }

            # 生成问题分布图
            issue_chart = f"""```mermaid
pie title 问题分布
    "业务价值问题" : {issue_types['业务价值问题']}
    "SMART原则问题" : {issue_types['SMART原则问题']}
    "完整性问题" : {issue_types['完整性问题']}
    "一致性问题" : {issue_types['一致性问题']}
    "清晰度问题" : {issue_types['清晰度问题']}
    "可测试性问题" : {issue_types['可测试性问题']}
```"""

            return {
                "radar_chart": radar_chart,
                "trend_chart": trend_chart,
                "issue_chart": issue_chart,
            }
        except Exception as e:
            return {
                "error": f"生成可视化图表时出错: {str(e)}",
                "radar_chart": "",
                "trend_chart": "",
                "issue_chart": "",
            }

    def export_report(self, result: ReviewResult, format: str = "markdown") -> str:
        """导出评审报告

        Args:
            result: 评审结果
            format: 导出格式，支持 "markdown" 或 "html"

        Returns:
            str: 格式化的报告内容
        """
        try:
            # 生成可视化图表
            visualizations = self._generate_visualizations(result)

            # 生成报告内容
            report_content = f"""# 需求评审报告

## 基本信息
- 评审时间：{result.review_timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- 评审轮次：第{len(result.review_history) + 1}轮

## 质量评估

### 总体评分
- 总体得分：{(result.business_value_score + result.smart_score + result.completeness_score + result.consistency_score + result.clarity_score + result.testability_score) / 6:.1f}分

### 详细指标
- 业务价值：{result.business_value_score}分
- SMART原则：{result.smart_score}分
- 完整性：{result.completeness_score}分
- 一致性：{result.consistency_score}分
- 清晰度：{result.clarity_score}分
- 可测试性：{result.testability_score}分

### 质量可视化
{visualizations["radar_chart"]}

### 趋势分析
{visualizations["trend_chart"]}

### 问题分布
{visualizations["issue_chart"]}

## 问题分析

### 阻塞问题
{chr(10).join([f"- {issue}" for issue in result.blocking_issues]) if result.blocking_issues else "- 无阻塞问题"}

### 改进建议
{chr(10).join([f"- {suggestion}" for suggestion in result.suggestions])}

## 历史记录
"""
            # 添加历史记录
            if result.review_history:
                for i, history in enumerate(result.review_history, 1):
                    report_content += f"\n### 第{i}轮评审 ({history['timestamp']})\n"
                    report_content += "#### 评分\n"
                    for metric, score in history["scores"].items():
                        report_content += f"- {metric}: {score}分\n"
                    if history.get("blocking_issues"):
                        report_content += "\n#### 阻塞问题\n"
                        report_content += "\n".join(
                            [f"- {issue}" for issue in history["blocking_issues"]]
                        )
                    if history.get("suggestions"):
                        report_content += "\n#### 改进建议\n"
                        report_content += "\n".join(
                            [f"- {suggestion}" for suggestion in history["suggestions"]]
                        )

            # 如果需要HTML格式，转换markdown为HTML
            if format.lower() == "html":
                try:
                    # 添加基本样式
                    report_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>需求评审报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            padding: 2em;
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1, h2, h3 {{ color: #333; }}
        .mermaid {{ background: #f8f9fa; padding: 1em; border-radius: 4px; }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{startOnLoad:true}});</script>
</head>
<body>
{report_content}
</body>
</html>
"""
                except ImportError:
                    report_content += "\n\n> 注意：未安装markdown包，无法转换为HTML格式。请先安装：pip install markdown"

            return report_content

        except Exception as e:
            return f"生成报告时出错: {str(e)}"

    def save_report(
        self,
        result: ReviewResult,
        format: str = "markdown",
        output_dir: str = "reports",
    ) -> str:
        """保存评审报告到文件系统

        Args:
            result: 评审结果
            format: 导出格式，支持 "markdown" 或 "html"
            output_dir: 输出目录，默认为 "reports"

        Returns:
            str: 保存的文件路径
        """
        try:
            # 生成报告内容
            report_content = self.export_report(result, format=format)

            # 确保输出目录存在
            from pathlib import Path

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            timestamp = result.review_timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"requirements_review_{timestamp}.{'html' if format.lower() == 'html' else 'md'}"
            filepath = output_path / filename

            # 保存文件
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(report_content)

            return str(filepath)

        except Exception as e:
            raise Exception(f"保存报告失败: {str(e)}")

    def batch_export(
        self,
        results: List[ReviewResult],
        formats: List[str] = ["markdown"],
        output_dir: str = "reports",
        include_summary: bool = True,
    ) -> Dict[str, List[str]]:
        """批量导出评审报告

        Args:
            results: 评审结果列表
            formats: 导出格式列表，支持 "markdown" 或 "html"
            output_dir: 输出目录，默认为 "reports"
            include_summary: 是否生成汇总报告，默认为 True

        Returns:
            Dict[str, List[str]]: 按格式分类的文件路径列表
        """
        try:
            # 确保输出目录存在
            from pathlib import Path

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # 按格式导出报告
            exported_files = {fmt: [] for fmt in formats}
            for result in results:
                for fmt in formats:
                    filepath = self.save_report(
                        result, format=fmt, output_dir=str(output_path)
                    )
                    exported_files[fmt].append(filepath)

            # 如果需要生成汇总报告
            if include_summary and results:
                summary = self._generate_batch_summary(results)
                for fmt in formats:
                    # 生成汇总报告文件名
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"requirements_review_summary_{timestamp}.{'html' if fmt.lower() == 'html' else 'md'}"
                    filepath = output_path / filename

                    # 保存汇总报告
                    with open(filepath, "w", encoding="utf-8") as f:
                        if fmt.lower() == "html":
                            try:
                                import markdown

                                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>需求评审汇总报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
        .chart {{ margin: 20px 0; }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{startOnLoad:true}});</script>
</head>
<body>
{markdown.markdown(summary)}
</body>
</html>"""
                                f.write(html_content)
                            except ImportError:
                                f.write(
                                    f"注意：未安装markdown包，无法生成HTML格式的汇总报告。\n\n{summary}"
                                )
                        else:
                            f.write(summary)

                    exported_files[fmt].append(str(filepath))

            return exported_files

        except Exception as e:
            raise Exception(f"批量导出报告失败: {str(e)}")

    def _generate_batch_summary(self, results: List[ReviewResult]) -> str:
        """生成批量评审汇总报告

        Args:
            results: 评审结果列表

        Returns:
            str: 汇总报告内容
        """
        if not results:
            return "无评审结果可供汇总"

        # 计算平均分数
        avg_scores = {
            "business_value": sum(r.business_value_score for r in results)
            / len(results),
            "smart": sum(r.smart_score for r in results) / len(results),
            "completeness": sum(r.completeness_score for r in results) / len(results),
            "consistency": sum(r.consistency_score for r in results) / len(results),
            "clarity": sum(r.clarity_score for r in results) / len(results),
            "testability": sum(r.testability_score for r in results) / len(results),
        }

        # 收集所有问题和建议
        all_issues = []
        all_suggestions = []
        for result in results:
            all_issues.extend(result.blocking_issues)
            all_suggestions.extend(result.suggestions)

        # 统计问题和建议的频率
        from collections import Counter

        issue_counts = Counter(all_issues)
        suggestion_counts = Counter(all_suggestions)

        # 生成汇总报告
        summary = f"""# 需求评审汇总报告

## 评审概况
- 总评审次数：{len(results)}
- 评审时间范围：{min(r.review_timestamp for r in results).strftime('%Y-%m-%d')} 至 {max(r.review_timestamp for r in results).strftime('%Y-%m-%d')}

## 平均得分
- 业务价值：{avg_scores['business_value']:.1f}分
- SMART原则：{avg_scores['smart']:.1f}分
- 完整性：{avg_scores['completeness']:.1f}分
- 一致性：{avg_scores['consistency']:.1f}分
- 清晰度：{avg_scores['clarity']:.1f}分
- 可测试性：{avg_scores['testability']:.1f}分

## 问题分布
{chr(10).join([f"- {issue} (出现{count}次)" for issue, count in issue_counts.most_common()])}

## 常见建议
{chr(10).join([f"- {suggestion} (提出{count}次)" for suggestion, count in suggestion_counts.most_common()])}

## 趋势分析
```mermaid
graph TD
    subgraph 评分趋势
    A[首次评审] --> B[最新评审]
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    end
```

## 改进建议
1. 重点关注高频问题的解决
2. 持续跟进常见建议的实施
3. 定期回顾评审结果，确保持续改进
"""

        return summary
