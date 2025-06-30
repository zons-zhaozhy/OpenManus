"""需求评审工具测试"""

from datetime import datetime
from pathlib import Path

import pytest

from app.tool.requirements_reviewer import RequirementsReviewer, ReviewResult


@pytest.fixture
def reviewer():
    """创建评审工具实例"""
    return RequirementsReviewer()


@pytest.fixture
def sample_requirements():
    """创建示例需求数据"""
    return {
        "project_scope": [
            "开发一个在线教育平台，预计投资100万，预期年收入500万",
            "支持课程管理、学习管理和考试系统，目标在2025年底前完成",
            "目标用户为高校和培训机构，预计首年用户数10000+",
        ],
        "user_roles": [
            "管理员：必须具备系统配置和用户管理权限",
            "教师：需要课程内容管理和考试管理权限",
            "学生：可以参与课程学习和考试",
        ],
        "core_features": [
            "课程管理：优先级高，必须支持课程创建、编辑、发布，例如视频课程上传",
            "学习管理：优先级中，需要支持课程学习、进度跟踪，至少记录3个月的学习数据",
            "考试系统：优先级高，支持在线考试、自动评分，考试时间不超过2小时",
            "统计分析：优先级低，支持学习数据分析和报告生成，每周生成分析报告",
        ],
        "constraints": [
            "系统需要支持并发用户1000+，响应时间不超过2秒",
            "必须支持主流浏览器访问，兼容性测试覆盖率>95%",
            "系统可用性要求99.9%，每月维护时间不超过4小时",
        ],
        "success_criteria": [
            "验收标准：所有核心功能测试通过率100%",
            "性能指标：峰值并发1000用户时响应时间<2秒",
            "质量要求：代码测试覆盖率>80%，关键功能测试通过率100%",
        ],
    }


@pytest.mark.asyncio
async def test_review_requirements_success(reviewer, sample_requirements):
    """测试需求评审成功"""
    result = await reviewer.review_requirements(sample_requirements)

    assert isinstance(result, ReviewResult)
    assert result.business_value_score > 0
    assert result.smart_score > 0
    assert result.completeness_score > 0
    assert result.consistency_score > 0
    assert result.clarity_score > 0
    assert result.testability_score > 0
    assert isinstance(result.blocking_issues, list)
    assert isinstance(result.suggestions, list)
    assert isinstance(result.review_timestamp, datetime)


def test_calculate_business_value_score(reviewer, sample_requirements):
    """测试业务价值分数计算"""
    score = reviewer._calculate_business_value_score(sample_requirements)

    assert isinstance(score, float)
    assert 0 <= score <= 100
    # 示例需求包含了业务需求、明确价值、项目目标、可量化收益和投资回报
    assert score >= 80


def test_calculate_smart_score(reviewer, sample_requirements):
    """测试SMART原则分数计算"""
    score = reviewer._calculate_smart_score(sample_requirements)

    assert isinstance(score, float)
    assert 0 <= score <= 100
    # 示例需求包含了具体、可衡量、可达成、相关和时限要求
    assert score >= 80


def test_calculate_completion_rate(reviewer, sample_requirements):
    """测试完整度分数计算"""
    score = reviewer._calculate_completion_rate(sample_requirements)

    assert isinstance(score, float)
    assert 0 <= score <= 100
    # 示例需求包含了所有必需的部分
    assert score >= 90


def test_calculate_clarity_score(reviewer, sample_requirements):
    """测试清晰度分数计算"""
    score = reviewer._calculate_clarity_score(sample_requirements)

    assert isinstance(score, float)
    assert 0 <= score <= 100
    # 示例需求使用了明确的动词和度量标准
    assert score >= 80


def test_calculate_consistency_score(reviewer, sample_requirements):
    """测试一致性分数计算"""
    score = reviewer._calculate_consistency_score(sample_requirements)

    assert isinstance(score, float)
    assert 0 <= score <= 100
    # 示例需求使用了统一的术语和优先级表达
    assert score >= 80


def test_calculate_testability_score(reviewer, sample_requirements):
    """测试可测试性分数计算"""
    score = reviewer._calculate_testability_score(sample_requirements)

    assert isinstance(score, float)
    assert 0 <= score <= 100
    # 示例需求包含了验收标准和可测试的指标
    assert score >= 80


def test_empty_requirements(reviewer):
    """测试空需求的处理"""
    empty_requirements = {}

    business_value_score = reviewer._calculate_business_value_score(empty_requirements)
    smart_score = reviewer._calculate_smart_score(empty_requirements)
    completion_rate = reviewer._calculate_completion_rate(empty_requirements)
    clarity_score = reviewer._calculate_clarity_score(empty_requirements)
    consistency_score = reviewer._calculate_consistency_score(empty_requirements)
    testability_score = reviewer._calculate_testability_score(empty_requirements)

    assert business_value_score == 0
    assert smart_score == 0
    assert completion_rate == 0
    assert clarity_score == 0
    assert consistency_score == 0
    assert testability_score == 0


def test_partial_requirements(reviewer):
    """测试部分需求的处理"""
    partial_requirements = {
        "project_scope": [
            "开发一个在线教育平台",
        ],
        "core_features": [
            "课程管理：支持课程创建、编辑、发布",
        ],
    }

    business_value_score = reviewer._calculate_business_value_score(
        partial_requirements
    )
    smart_score = reviewer._calculate_smart_score(partial_requirements)
    completion_rate = reviewer._calculate_completion_rate(partial_requirements)
    clarity_score = reviewer._calculate_clarity_score(partial_requirements)
    consistency_score = reviewer._calculate_consistency_score(partial_requirements)
    testability_score = reviewer._calculate_testability_score(partial_requirements)

    assert 0 < business_value_score < 50  # 业务价值信息不完整
    assert 0 < smart_score < 50  # SMART原则信息不完整
    assert 0 < completion_rate < 50  # 只有2个部分
    assert 0 < clarity_score < 50  # 缺少具体的度量标准
    assert 0 < consistency_score < 50  # 样本太少，难以评估一致性
    assert 0 < testability_score < 50  # 缺少验收标准和测试场景


def test_invalid_requirements(reviewer):
    """测试无效需求的处理"""
    invalid_requirements = {
        "invalid_section": ["无效的需求部分"],
    }

    business_value_score = reviewer._calculate_business_value_score(
        invalid_requirements
    )
    smart_score = reviewer._calculate_smart_score(invalid_requirements)
    completion_rate = reviewer._calculate_completion_rate(invalid_requirements)
    clarity_score = reviewer._calculate_clarity_score(invalid_requirements)
    consistency_score = reviewer._calculate_consistency_score(invalid_requirements)
    testability_score = reviewer._calculate_testability_score(invalid_requirements)

    assert business_value_score == 0  # 无效的需求部分
    assert smart_score == 0  # 无效的需求部分
    assert completion_rate == 0  # 缺少所有必需部分
    assert clarity_score == 0  # 无效的需求部分
    assert consistency_score == 0  # 无效的需求部分
    assert testability_score == 0  # 无效的需求部分


def test_generate_review_summary(reviewer, sample_requirements):
    """测试评审总结生成"""
    result = ReviewResult(
        business_value_score=85.0,
        smart_score=75.0,
        completeness_score=95.0,
        consistency_score=80.0,
        clarity_score=82.0,
        testability_score=78.0,
        blocking_issues=["需求完整性问题：缺少用户权限矩阵"],
        suggestions=["添加用户权限详细说明"],
        review_timestamp=datetime.now(),
        review_history=[],
    )

    summary = reviewer._generate_review_summary(result)

    assert isinstance(summary, str)
    assert "总体评价" in summary
    assert "主要指标" in summary
    assert "主要优势" in summary
    assert "主要问题" in summary
    assert "阻塞问题" in summary
    assert "改进建议" in summary

    # 检查总体得分计算
    overall_score = (85.0 + 75.0 + 95.0 + 80.0 + 82.0 + 78.0) / 6
    assert f"{overall_score:.1f}分" in summary

    # 检查状态评估
    assert "良好" in summary  # 82.5分应该是"良好"状态

    # 检查优势识别
    assert "业务价值明确" in summary  # 85分 >= 80
    assert "需求完整度高" in summary  # 95分 >= 80
    assert "需求一致性好" in summary  # 80分 >= 80
    assert "需求描述清晰" in summary  # 82分 >= 80

    # 检查问题识别
    assert "SMART原则" in summary  # 75分 < 80
    assert "可测试性" in summary  # 78分 < 80


def test_analyze_trends_with_history(reviewer):
    """测试有历史记录时的趋势分析"""
    history = [
        {
            "scores": {
                "business_value": 80.0,
                "smart": 70.0,
                "completeness": 85.0,
                "consistency": 75.0,
                "clarity": 78.0,
                "testability": 72.0,
            },
            "blocking_issues": ["问题1", "问题2"],
            "suggestions": ["建议1", "建议2", "建议3"],
            "timestamp": "2025-06-01T10:00:00",
        },
        {
            "scores": {
                "business_value": 85.0,
                "smart": 75.0,
                "completeness": 90.0,
                "consistency": 80.0,
                "clarity": 82.0,
                "testability": 78.0,
            },
            "blocking_issues": ["问题2", "问题3"],
            "suggestions": ["建议2", "建议3", "建议4"],
            "timestamp": "2025-06-02T10:00:00",
        },
    ]

    result = ReviewResult(
        business_value_score=85.0,
        smart_score=75.0,
        completeness_score=90.0,
        consistency_score=80.0,
        clarity_score=82.0,
        testability_score=78.0,
        blocking_issues=["问题2", "问题3"],
        suggestions=["建议2", "建议3", "建议4"],
        review_timestamp=datetime.now(),
        review_history=history,
    )

    trends = reviewer._analyze_trends(result)

    assert isinstance(trends, dict)
    assert "trend_analysis" in trends
    assert "score_trends" in trends
    assert "issue_trends" in trends
    assert "improvement_trends" in trends

    # 检查分数趋势
    score_trends = trends["score_trends"]
    assert len(score_trends) == 6  # 6个指标
    assert score_trends["business_value"]["change"] == 5.0  # 85 - 80
    assert score_trends["smart"]["change"] == 5.0  # 75 - 70
    assert score_trends["completeness"]["change"] == 5.0  # 90 - 85

    # 检查问题趋势
    issue_trends = trends["issue_trends"]
    assert len(issue_trends["new_issues"]) == 1  # 问题3是新增的
    assert len(issue_trends["resolved_issues"]) == 1  # 问题1被解决了
    assert len(issue_trends["persistent_issues"]) == 1  # 问题2持续存在

    # 检查改进趋势
    improvement_trends = trends["improvement_trends"]
    assert len(improvement_trends["new_suggestions"]) == 1  # 建议4是新增的
    assert len(improvement_trends["implemented_suggestions"]) == 1  # 建议1被实施了
    assert len(improvement_trends["pending_suggestions"]) == 2  # 建议2和3待处理


def test_analyze_trends_without_history(reviewer):
    """测试无历史记录时的趋势分析"""
    result = ReviewResult(
        business_value_score=85.0,
        smart_score=75.0,
        completeness_score=90.0,
        consistency_score=80.0,
        clarity_score=82.0,
        testability_score=78.0,
        blocking_issues=["问题1"],
        suggestions=["建议1"],
        review_timestamp=datetime.now(),
        review_history=[],
    )

    trends = reviewer._analyze_trends(result)

    assert isinstance(trends, dict)
    assert trends["trend_analysis"] == "历史数据不足，无法分析趋势"
    assert trends["score_trends"] == {}
    assert trends["issue_trends"] == []
    assert trends["improvement_trends"] == []


def test_analyze_trends_with_single_history(reviewer):
    """测试只有一条历史记录时的趋势分析"""
    history = [
        {
            "scores": {
                "business_value": 80.0,
                "smart": 70.0,
                "completeness": 85.0,
                "consistency": 75.0,
                "clarity": 78.0,
                "testability": 72.0,
            },
            "blocking_issues": ["问题1"],
            "suggestions": ["建议1"],
            "timestamp": "2025-06-01T10:00:00",
        }
    ]

    result = ReviewResult(
        business_value_score=85.0,
        smart_score=75.0,
        completeness_score=90.0,
        consistency_score=80.0,
        clarity_score=82.0,
        testability_score=78.0,
        blocking_issues=["问题2"],
        suggestions=["建议2"],
        review_timestamp=datetime.now(),
        review_history=history,
    )

    trends = reviewer._analyze_trends(result)

    assert isinstance(trends, dict)
    assert trends["trend_analysis"] == "历史数据不足，无法分析趋势"
    assert trends["score_trends"] == {}
    assert trends["issue_trends"] == []
    assert trends["improvement_trends"] == []


def test_generate_visualizations(reviewer, sample_requirements):
    """测试可视化图表生成"""
    result = ReviewResult(
        business_value_score=85.0,
        smart_score=75.0,
        completeness_score=95.0,
        consistency_score=80.0,
        clarity_score=82.0,
        testability_score=78.0,
        blocking_issues=[
            "业务价值问题：缺少ROI分析",
            "SMART原则问题：时间要求不明确",
            "完整性问题：缺少用户权限矩阵",
            "一致性问题：术语使用不统一",
            "清晰度问题：部分需求描述模糊",
            "可测试性问题：验收标准不完整",
        ],
        suggestions=["添加用户权限详细说明"],
        review_timestamp=datetime.now(),
        review_history=[],
    )

    visualizations = reviewer._generate_visualizations(result)

    # 检查返回的图表
    assert isinstance(visualizations, dict)
    assert "radar_chart" in visualizations
    assert "trend_chart" in visualizations
    assert "issue_chart" in visualizations

    # 检查雷达图
    assert "```mermaid" in visualizations["radar_chart"]
    assert "需求质量雷达图" in visualizations["radar_chart"]
    assert "业务价值 85.0%" in visualizations["radar_chart"]
    assert "SMART原则 75.0%" in visualizations["radar_chart"]
    assert "完整性 95.0%" in visualizations["radar_chart"]
    assert "一致性 80.0%" in visualizations["radar_chart"]
    assert "清晰度 82.0%" in visualizations["radar_chart"]
    assert "可测试性 78.0%" in visualizations["radar_chart"]

    # 检查趋势图
    assert "历史数据不足，无法生成趋势图" == visualizations["trend_chart"]

    # 检查问题分布图
    assert "```mermaid" in visualizations["issue_chart"]
    assert "问题分布" in visualizations["issue_chart"]
    assert '"业务价值问题" : 1' in visualizations["issue_chart"]
    assert '"SMART原则问题" : 1' in visualizations["issue_chart"]
    assert '"完整性问题" : 1' in visualizations["issue_chart"]
    assert '"一致性问题" : 1' in visualizations["issue_chart"]
    assert '"清晰度问题" : 1' in visualizations["issue_chart"]
    assert '"可测试性问题" : 1' in visualizations["issue_chart"]


def test_generate_visualizations_with_history(reviewer):
    """测试带历史记录的可视化图表生成"""
    history = [
        {
            "scores": {
                "business_value": 80.0,
                "smart": 70.0,
                "completeness": 85.0,
                "consistency": 75.0,
                "clarity": 78.0,
                "testability": 72.0,
            },
            "blocking_issues": ["问题1", "问题2"],
            "suggestions": ["建议1", "建议2", "建议3"],
            "timestamp": "2025-06-01T10:00:00",
        },
        {
            "scores": {
                "business_value": 85.0,
                "smart": 75.0,
                "completeness": 90.0,
                "consistency": 80.0,
                "clarity": 82.0,
                "testability": 78.0,
            },
            "blocking_issues": ["问题2", "问题3"],
            "suggestions": ["建议2", "建议3", "建议4"],
            "timestamp": "2025-06-02T10:00:00",
        },
    ]

    result = ReviewResult(
        business_value_score=85.0,
        smart_score=75.0,
        completeness_score=90.0,
        consistency_score=80.0,
        clarity_score=82.0,
        testability_score=78.0,
        blocking_issues=["问题2", "问题3"],
        suggestions=["建议2", "建议3", "建议4"],
        review_timestamp=datetime.now(),
        review_history=history,
    )

    visualizations = reviewer._generate_visualizations(result)

    # 检查返回的图表
    assert isinstance(visualizations, dict)
    assert "radar_chart" in visualizations
    assert "trend_chart" in visualizations
    assert "issue_chart" in visualizations

    # 检查雷达图
    assert "```mermaid" in visualizations["radar_chart"]
    assert "需求质量雷达图" in visualizations["radar_chart"]
    assert "业务价值 85.0%" in visualizations["radar_chart"]
    assert "SMART原则 75.0%" in visualizations["radar_chart"]
    assert "完整性 90.0%" in visualizations["radar_chart"]
    assert "一致性 80.0%" in visualizations["radar_chart"]
    assert "清晰度 82.0%" in visualizations["radar_chart"]
    assert "可测试性 78.0%" in visualizations["radar_chart"]

    # 检查趋势图
    assert "```mermaid" in visualizations["trend_chart"]
    assert "需求质量趋势" in visualizations["trend_chart"]
    assert "上次评审" in visualizations["trend_chart"]
    assert "本次评审" in visualizations["trend_chart"]

    # 检查问题分布图
    assert "```mermaid" in visualizations["issue_chart"]
    assert "问题分布" in visualizations["issue_chart"]
    assert '"业务价值问题" : 0' in visualizations["issue_chart"]
    assert '"SMART原则问题" : 0' in visualizations["issue_chart"]
    assert '"完整性问题" : 0' in visualizations["issue_chart"]
    assert '"一致性问题" : 0' in visualizations["issue_chart"]
    assert '"清晰度问题" : 0' in visualizations["issue_chart"]
    assert '"可测试性问题" : 0' in visualizations["issue_chart"]


def test_generate_visualizations_error_handling(reviewer):
    """测试可视化图表生成的错误处理"""
    # 创建一个无效的ReviewResult对象
    result = ReviewResult(
        business_value_score=None,  # type: ignore
        smart_score=None,  # type: ignore
        completeness_score=None,  # type: ignore
        consistency_score=None,  # type: ignore
        clarity_score=None,  # type: ignore
        testability_score=None,  # type: ignore
        blocking_issues=[],
        suggestions=[],
        review_timestamp=datetime.now(),
        review_history=[],
    )

    visualizations = reviewer._generate_visualizations(result)

    # 检查错误处理
    assert isinstance(visualizations, dict)
    assert "error" in visualizations
    assert "生成可视化图表时出错" in visualizations["error"]
    assert visualizations["radar_chart"] == ""
    assert visualizations["trend_chart"] == ""
    assert visualizations["issue_chart"] == ""


def test_export_report_markdown(reviewer, sample_requirements):
    """测试导出Markdown格式的评审报告"""
    result = ReviewResult(
        business_value_score=85.0,
        smart_score=75.0,
        completeness_score=95.0,
        consistency_score=80.0,
        clarity_score=82.0,
        testability_score=78.0,
        blocking_issues=[
            "业务价值问题：缺少ROI分析",
            "SMART原则问题：时间要求不明确",
        ],
        suggestions=["添加用户权限详细说明"],
        review_timestamp=datetime.now(),
        review_history=[
            {
                "scores": {
                    "business_value": 80.0,
                    "smart": 70.0,
                    "completeness": 85.0,
                    "consistency": 75.0,
                    "clarity": 78.0,
                    "testability": 72.0,
                },
                "blocking_issues": ["问题1", "问题2"],
                "suggestions": ["建议1", "建议2"],
                "timestamp": "2025-06-01T10:00:00",
            }
        ],
    )

    report = reviewer.export_report(result, format="markdown")

    # 检查报告内容
    assert isinstance(report, str)
    assert "# 需求评审报告" in report
    assert "## 基本信息" in report
    assert "## 质量评估" in report
    assert "### 总体评分" in report
    assert "### 详细指标" in report
    assert "### 质量可视化" in report
    assert "### 趋势分析" in report
    assert "### 问题分布" in report
    assert "## 问题分析" in report
    assert "### 阻塞问题" in report
    assert "### 改进建议" in report
    assert "## 历史记录" in report

    # 检查评分内容
    assert "业务价值：85.0分" in report
    assert "SMART原则：75.0分" in report
    assert "完整性：95.0分" in report
    assert "一致性：80.0分" in report
    assert "清晰度：82.0分" in report
    assert "可测试性：78.0分" in report

    # 检查问题和建议
    assert "业务价值问题：缺少ROI分析" in report
    assert "SMART原则问题：时间要求不明确" in report
    assert "添加用户权限详细说明" in report

    # 检查历史记录
    assert "第1轮评审" in report
    assert "问题1" in report
    assert "问题2" in report
    assert "建议1" in report
    assert "建议2" in report


def test_export_report_html(reviewer, sample_requirements):
    """测试导出HTML格式的评审报告"""
    result = ReviewResult(
        business_value_score=85.0,
        smart_score=75.0,
        completeness_score=95.0,
        consistency_score=80.0,
        clarity_score=82.0,
        testability_score=78.0,
        blocking_issues=["问题1", "问题2"],
        suggestions=["建议1", "建议2"],
        review_timestamp=datetime.now(),
        review_history=[],
    )

    try:
        import markdown

        report = reviewer.export_report(result, format="html")

        # 检查HTML基本结构
        assert "<!DOCTYPE html>" in report
        assert "<html>" in report
        assert "<head>" in report
        assert "<body>" in report
        assert "</html>" in report

        # 检查样式和脚本
        assert "<style>" in report
        assert "font-family" in report
        assert "mermaid.initialize" in report

        # 检查内容转换
        assert "<h1" in report
        assert "<h2" in report
        assert "<h3" in report
        assert "<ul" in report or "<ol" in report
        assert "<li" in report

    except ImportError:
        report = reviewer.export_report(result, format="html")
        assert "注意：未安装markdown包" in report


def test_export_report_error_handling(reviewer):
    """测试导出报告的错误处理"""
    # 创建一个无效的ReviewResult对象
    result = ReviewResult(
        business_value_score=None,  # type: ignore
        smart_score=None,  # type: ignore
        completeness_score=None,  # type: ignore
        consistency_score=None,  # type: ignore
        clarity_score=None,  # type: ignore
        testability_score=None,  # type: ignore
        blocking_issues=[],
        suggestions=[],
        review_timestamp=datetime.now(),
        review_history=[],
    )

    report = reviewer.export_report(result)
    assert "生成报告时出错" in report


def test_save_report_markdown(reviewer, sample_requirements, tmp_path):
    """测试保存Markdown格式的评审报告"""
    result = ReviewResult(
        business_value_score=85.0,
        smart_score=75.0,
        completeness_score=95.0,
        consistency_score=80.0,
        clarity_score=82.0,
        testability_score=78.0,
        blocking_issues=["问题1", "问题2"],
        suggestions=["建议1", "建议2"],
        review_timestamp=datetime.now(),
        review_history=[],
    )

    # 使用临时目录作为输出目录
    output_dir = tmp_path / "reports"
    filepath = reviewer.save_report(
        result, format="markdown", output_dir=str(output_dir)
    )

    # 检查文件是否存在
    assert Path(filepath).exists()
    assert Path(filepath).suffix == ".md"

    # 检查文件内容
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        assert "# 需求评审报告" in content
        assert "## 基本信息" in content
        assert "## 质量评估" in content
        assert "问题1" in content
        assert "问题2" in content
        assert "建议1" in content
        assert "建议2" in content


def test_save_report_html(reviewer, sample_requirements, tmp_path):
    """测试保存HTML格式的评审报告"""
    result = ReviewResult(
        business_value_score=85.0,
        smart_score=75.0,
        completeness_score=95.0,
        consistency_score=80.0,
        clarity_score=82.0,
        testability_score=78.0,
        blocking_issues=["问题1", "问题2"],
        suggestions=["建议1", "建议2"],
        review_timestamp=datetime.now(),
        review_history=[],
    )

    try:
        import markdown

        # 使用临时目录作为输出目录
        output_dir = tmp_path / "reports"
        filepath = reviewer.save_report(
            result, format="html", output_dir=str(output_dir)
        )

        # 检查文件是否存在
        assert Path(filepath).exists()
        assert Path(filepath).suffix == ".html"

        # 检查文件内容
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            assert "<!DOCTYPE html>" in content
            assert "<html>" in content
            assert "<head>" in content
            assert "<body>" in content
            assert "</html>" in content
            assert "<style>" in content
            assert "mermaid.initialize" in content
            assert "问题1" in content
            assert "问题2" in content
            assert "建议1" in content
            assert "建议2" in content

    except ImportError:
        # 如果没有安装markdown包，应该抛出异常
        with pytest.raises(Exception) as excinfo:
            reviewer.save_report(result, format="html", output_dir=str(output_dir))
        assert "未安装markdown包" in str(excinfo.value)


def test_save_report_invalid_directory(reviewer, sample_requirements):
    """测试保存到无效目录时的错误处理"""
    result = ReviewResult(
        business_value_score=85.0,
        smart_score=75.0,
        completeness_score=95.0,
        consistency_score=80.0,
        clarity_score=82.0,
        testability_score=78.0,
        blocking_issues=[],
        suggestions=[],
        review_timestamp=datetime.now(),
        review_history=[],
    )

    # 尝试保存到一个无效的目录
    with pytest.raises(Exception) as excinfo:
        reviewer.save_report(result, output_dir="/invalid/directory/path")
    assert "保存报告失败" in str(excinfo.value)


def test_batch_export(reviewer, sample_requirements, tmp_path):
    """测试批量导出评审报告"""
    # 创建多个评审结果
    results = [
        ReviewResult(
            business_value_score=85.0,
            smart_score=75.0,
            completeness_score=95.0,
            consistency_score=80.0,
            clarity_score=82.0,
            testability_score=78.0,
            blocking_issues=["问题1", "问题2"],
            suggestions=["建议1", "建议2"],
            review_timestamp=datetime.now(),
            review_history=[],
        ),
        ReviewResult(
            business_value_score=88.0,
            smart_score=82.0,
            completeness_score=90.0,
            consistency_score=85.0,
            clarity_score=87.0,
            testability_score=83.0,
            blocking_issues=["问题2", "问题3"],
            suggestions=["建议2", "建议3"],
            review_timestamp=datetime.now(),
            review_history=[],
        ),
    ]

    # 使用临时目录作为输出目录
    output_dir = tmp_path / "reports"
    exported_files = reviewer.batch_export(
        results,
        formats=["markdown", "html"],
        output_dir=str(output_dir),
        include_summary=True,
    )

    # 检查导出的文件
    assert "markdown" in exported_files
    assert "html" in exported_files
    assert len(exported_files["markdown"]) == 3  # 2个报告 + 1个汇总
    assert len(exported_files["html"]) == 3  # 2个报告 + 1个汇总

    # 检查所有文件是否存在
    for fmt, files in exported_files.items():
        for filepath in files:
            assert Path(filepath).exists()
            if "summary" in filepath:
                # 检查汇总报告内容
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    assert "需求评审汇总报告" in content
                    assert "评审概况" in content
                    assert "平均得分" in content
                    assert "问题分布" in content
                    assert "常见建议" in content
                    assert "趋势分析" in content
                    assert "改进建议" in content
                    if fmt == "html":
                        assert "<!DOCTYPE html>" in content
                        assert "<html>" in content
                        assert "<head>" in content
                        assert "<body>" in content
                        assert "</html>" in content
                        assert "mermaid.initialize" in content


def test_batch_export_empty_results(reviewer, tmp_path):
    """测试空结果集的批量导出"""
    output_dir = tmp_path / "reports"
    exported_files = reviewer.batch_export(
        results=[],
        formats=["markdown"],
        output_dir=str(output_dir),
        include_summary=True,
    )

    assert "markdown" in exported_files
    assert len(exported_files["markdown"]) == 0


def test_batch_export_invalid_format(reviewer, sample_requirements, tmp_path):
    """测试无效格式的批量导出"""
    result = ReviewResult(
        business_value_score=85.0,
        smart_score=75.0,
        completeness_score=95.0,
        consistency_score=80.0,
        clarity_score=82.0,
        testability_score=78.0,
        blocking_issues=[],
        suggestions=[],
        review_timestamp=datetime.now(),
        review_history=[],
    )

    output_dir = tmp_path / "reports"
    with pytest.raises(Exception) as excinfo:
        reviewer.batch_export(
            results=[result],
            formats=["invalid"],
            output_dir=str(output_dir),
        )
    assert "不支持的导出格式" in str(excinfo.value)


def test_batch_export_invalid_directory(reviewer, sample_requirements):
    """测试无效目录的批量导出"""
    result = ReviewResult(
        business_value_score=85.0,
        smart_score=75.0,
        completeness_score=95.0,
        consistency_score=80.0,
        clarity_score=82.0,
        testability_score=78.0,
        blocking_issues=[],
        suggestions=[],
        review_timestamp=datetime.now(),
        review_history=[],
    )

    with pytest.raises(Exception) as excinfo:
        reviewer.batch_export(
            results=[result],
            formats=["markdown"],
            output_dir="/invalid/directory/path",
        )
    assert "批量导出报告失败" in str(excinfo.value)


def test_batch_export_without_summary(reviewer, sample_requirements, tmp_path):
    """测试不生成汇总报告的批量导出"""
    results = [
        ReviewResult(
            business_value_score=85.0,
            smart_score=75.0,
            completeness_score=95.0,
            consistency_score=80.0,
            clarity_score=82.0,
            testability_score=78.0,
            blocking_issues=["问题1"],
            suggestions=["建议1"],
            review_timestamp=datetime.now(),
            review_history=[],
        ),
    ]

    output_dir = tmp_path / "reports"
    exported_files = reviewer.batch_export(
        results=results,
        formats=["markdown"],
        output_dir=str(output_dir),
        include_summary=False,
    )

    assert "markdown" in exported_files
    assert len(exported_files["markdown"]) == 1  # 只有1个报告，没有汇总
    assert all("summary" not in f for f in exported_files["markdown"])
