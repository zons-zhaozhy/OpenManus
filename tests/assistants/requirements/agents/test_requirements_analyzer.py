"""
需求分析器测试用例
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from app.assistants.requirements.agents.requirement_clarifier import (
    RequirementClarifier,
)
from app.core.cache import get_cache_manager


@pytest.fixture
async def cache_manager():
    """缓存管理器fixture"""
    return get_cache_manager()


@pytest.fixture
async def requirement_clarifier():
    """需求澄清智能体fixture"""
    return RequirementClarifier()


@pytest.mark.asyncio
async def test_initial_analysis(requirement_clarifier):
    """测试初步分析功能"""
    # 准备测试数据
    requirement_text = "开发一个在线商城系统"

    # 执行分析
    result = await requirement_clarifier._initial_analysis(requirement_text)

    # 验证结果
    assert isinstance(result, dict)
    assert "main_goal" in result
    assert "key_features" in result
    assert "constraints" in result
    assert "user_value" in result
    assert "technical_feasibility" in result
    assert "summary" in result


@pytest.mark.asyncio
async def test_generate_questions(requirement_clarifier):
    """测试生成澄清问题功能"""
    # 准备测试数据
    requirement_text = "开发一个在线商城系统"
    initial_analysis = {
        "main_goal": "构建在线商城平台",
        "key_features": ["用户管理", "商品管理", "订单管理"],
        "constraints": ["性能要求高", "安全性要求高"],
        "user_value": "提供便捷的在线购物体验",
        "technical_feasibility": "技术可行",
        "summary": "标准的电商系统",
    }

    # 执行分析
    result = await requirement_clarifier._generate_questions(
        requirement_text, initial_analysis
    )

    # 验证结果
    assert isinstance(result, list)
    for question in result:
        assert "question" in question
        assert "purpose" in question
        assert "category" in question
        assert "priority" in question
        assert 1 <= question["priority"] <= 5


@pytest.mark.asyncio
async def test_assess_completeness(requirement_clarifier):
    """测试评估完整性功能"""
    # 准备测试数据
    requirement_text = "开发一个在线商城系统"
    initial_analysis = {
        "main_goal": "构建在线商城平台",
        "key_features": ["用户管理", "商品管理", "订单管理"],
        "constraints": ["性能要求高", "安全性要求高"],
        "user_value": "提供便捷的在线购物体验",
        "technical_feasibility": "技术可行",
        "summary": "标准的电商系统",
    }

    # 执行分析
    result = await requirement_clarifier._assess_completeness(
        requirement_text, initial_analysis
    )

    # 验证结果
    assert isinstance(result, dict)
    assert "scores" in result
    assert "reasons" in result
    assert "overall_score" in result
    assert "summary" in result

    # 验证评分
    scores = result["scores"]
    for key in [
        "goal_clarity",
        "functional_completeness",
        "constraint_clarity",
        "verifiability",
        "feasibility",
    ]:
        assert key in scores
        assert 0 <= scores[key] <= 100


@pytest.mark.asyncio
async def test_identify_risks(requirement_clarifier):
    """测试识别风险功能"""
    # 准备测试数据
    requirement_text = "开发一个在线商城系统"
    initial_analysis = {
        "main_goal": "构建在线商城平台",
        "key_features": ["用户管理", "商品管理", "订单管理"],
        "constraints": ["性能要求高", "安全性要求高"],
        "user_value": "提供便捷的在线购物体验",
        "technical_feasibility": "技术可行",
        "summary": "标准的电商系统",
    }

    # 执行分析
    result = await requirement_clarifier._identify_risks(
        requirement_text, initial_analysis
    )

    # 验证结果
    assert isinstance(result, list)
    for risk in result:
        assert "risk_type" in risk
        assert "description" in risk
        assert "impact" in risk
        assert "probability" in risk
        assert "mitigation" in risk
        assert 1 <= risk["impact"] <= 5
        assert 1 <= risk["probability"] <= 5


@pytest.mark.asyncio
async def test_cache_analysis(requirement_clarifier, cache_manager):
    """测试缓存分析结果功能"""
    # 准备测试数据
    requirement_text = "开发一个在线商城系统"
    test_result = {"summary": "测试结果", "timestamp": datetime.now().isoformat()}

    # 缓存结果
    await requirement_clarifier._cache_analysis(requirement_text, test_result)

    # 获取缓存
    cached_result = await requirement_clarifier._get_cached_analysis(requirement_text)

    # 验证结果
    assert cached_result is not None
    assert cached_result["summary"] == test_result["summary"]
    assert cached_result["timestamp"] == test_result["timestamp"]


@pytest.mark.asyncio
async def test_shared_context(requirement_clarifier):
    """测试共享上下文功能"""
    # 准备测试数据
    test_context = {"test_key": "test_value", "timestamp": datetime.now().isoformat()}

    # 更新上下文
    await requirement_clarifier._update_shared_context(test_context)

    # 获取上下文
    shared_context = await requirement_clarifier._get_shared_context()

    # 验证结果
    assert shared_context is not None
    assert shared_context["test_key"] == test_context["test_key"]
    assert shared_context["timestamp"] == test_context["timestamp"]


@pytest.mark.asyncio
async def test_full_analysis_flow(requirement_clarifier):
    """测试完整分析流程"""
    # 准备测试数据
    requirement_text = "开发一个在线商城系统"

    # 执行分析
    result = await requirement_clarifier.analyze(requirement_text)

    # 验证结果结构
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "requirement_text" in result
    assert "initial_analysis" in result
    assert "clarification_questions" in result
    assert "completeness_score" in result
    assert "risks" in result
    assert "summary" in result
    assert "status" in result

    # 验证结果内容
    assert result["requirement_text"] == requirement_text
    assert isinstance(result["initial_analysis"], dict)
    assert isinstance(result["clarification_questions"], list)
    assert isinstance(result["completeness_score"], dict)
    assert isinstance(result["risks"], list)
    assert isinstance(result["summary"], str)
    assert result["status"] in ["需要澄清", "完整"]
