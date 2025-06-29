"""
全面测试需求分析助手的核心功能
"""

import asyncio

import pytest

from app.assistants.requirements.flow import RequirementsFlow
from app.core.types import AgentResponse
from app.flow.state import FlowState
from app.logger import logger

# 测试数据
TEST_REQUIREMENTS = [
    {
        "name": "简单需求",
        "input": "我需要一个待办事项管理系统",
        "expected_stages": ["初始化", "需求澄清", "业务分析", "文档生成", "质量评审"],
    },
    {
        "name": "复杂需求",
        "input": """
        我需要一个企业级的项目管理系统，具有以下功能：
        1. 用户管理和权限控制
        2. 项目创建和任务分配
        3. 进度跟踪和报告生成
        4. 团队协作和文件共享
        5. 集成第三方工具
        """,
        "expected_stages": ["初始化", "需求澄清", "业务分析", "文档生成", "质量评审"],
    },
    {
        "name": "模糊需求",
        "input": "我想要一个类似淘宝的系统",
        "expected_stages": ["初始化", "需求澄清", "业务分析", "文档生成", "质量评审"],
    },
]


@pytest.mark.asyncio
async def test_requirements_flow_initialization():
    """测试需求分析流程初始化"""
    flow = RequirementsFlow()
    assert flow is not None
    assert flow.agents is not None
    assert "clarifier" in flow.agents
    assert "analyst" in flow.agents
    assert "writer" in flow.agents
    assert "reviewer" in flow.agents

    # 验证上下文管理器初始化
    assert flow.context_manager is not None
    assert flow.knowledge_base is not None
    assert flow.code_analyzer is not None


@pytest.mark.asyncio
async def test_requirements_flow_simple():
    """测试简单需求分析流程"""
    flow = RequirementsFlow()
    requirement = TEST_REQUIREMENTS[0]

    # 记录进度
    stages = []

    async def progress_callback(step, total, stage):
        stages.append(stage)
        logger.info(f"当前阶段: {stage} ({step}/{total})")

    result = await flow.execute(requirement["input"], progress_callback)

    # 验证结果
    assert result is not None
    assert len(result) > 0
    assert all(stage in stages for stage in requirement["expected_stages"])

    # 验证上下文
    context = flow.context_manager.get_session_summary()
    assert context is not None
    assert "user_input" in context
    assert "current_stage" in context


@pytest.mark.asyncio
async def test_requirements_flow_complex():
    """测试复杂需求分析流程"""
    flow = RequirementsFlow()
    requirement = TEST_REQUIREMENTS[1]

    stages = []

    async def progress_callback(step, total, stage):
        stages.append(stage)
        logger.info(f"当前阶段: {stage} ({step}/{total})")

    result = await flow.execute(requirement["input"], progress_callback)

    # 验证结果
    assert result is not None
    assert len(result) > 0
    assert all(stage in stages for stage in requirement["expected_stages"])

    # 验证质量评审
    context = flow.context_manager.get_session_summary()
    assert "quality_review" in context
    quality_metrics = flow._get_quality_metrics()
    assert quality_metrics["total_score"] >= 70


@pytest.mark.asyncio
async def test_requirements_flow_unclear():
    """测试模糊需求分析流程"""
    flow = RequirementsFlow()
    requirement = TEST_REQUIREMENTS[2]

    stages = []

    async def progress_callback(step, total, stage):
        stages.append(stage)
        logger.info(f"当前阶段: {stage} ({step}/{total})")

    result = await flow.execute(requirement["input"], progress_callback)

    # 验证结果
    assert result is not None
    assert len(result) > 0
    assert all(stage in stages for stage in requirement["expected_stages"])

    # 验证澄清问题生成
    context = flow.context_manager.get_session_summary()
    assert "clarification_questions" in context
    assert len(context["clarification_questions"]) > 0


@pytest.mark.asyncio
async def test_parallel_processing():
    """测试并行处理功能"""
    flow = RequirementsFlow(enable_parallel=True)
    requirement = TEST_REQUIREMENTS[1]

    start_time = asyncio.get_event_loop().time()
    result = await flow.execute(requirement["input"])
    end_time = asyncio.get_event_loop().time()
    parallel_time = end_time - start_time

    # 测试串行处理
    flow = RequirementsFlow(enable_parallel=False)
    start_time = asyncio.get_event_loop().time()
    result = await flow.execute(requirement["input"])
    end_time = asyncio.get_event_loop().time()
    sequential_time = end_time - start_time

    # 验证并行处理更快
    assert parallel_time < sequential_time


@pytest.mark.asyncio
async def test_knowledge_base_integration():
    """测试知识库集成"""
    flow = RequirementsFlow()

    # 准备测试数据
    test_input = "我需要一个类似GitHub的代码托管平台"

    # 执行预处理
    await flow._preprocess_with_knowledge_base(test_input)

    # 验证知识库结果
    context = flow.context_manager.get_session_summary()
    assert "knowledge_base_results" in context
    assert len(context["knowledge_base_results"]) > 0


@pytest.mark.asyncio
async def test_code_analysis_integration():
    """测试代码分析集成"""
    flow = RequirementsFlow()

    # 准备测试数据
    test_input = "需要一个RESTful API服务"

    # 执行预处理
    await flow._preprocess_with_code_analysis(test_input)

    # 验证代码分析结果
    context = flow.context_manager.get_session_summary()
    assert "code_analysis_results" in context
    assert len(context["code_analysis_results"]) > 0


@pytest.mark.asyncio
async def test_quality_metrics():
    """测试质量指标计算"""
    flow = RequirementsFlow()
    requirement = TEST_REQUIREMENTS[1]

    await flow.execute(requirement["input"])
    metrics = flow._get_quality_metrics()

    # 验证质量指标
    assert "total_score" in metrics
    assert "quality_level" in metrics
    assert "improvement_suggestions" in metrics
    assert metrics["total_score"] >= 0
    assert metrics["total_score"] <= 100


@pytest.mark.asyncio
async def test_error_handling():
    """测试错误处理"""
    flow = RequirementsFlow()

    # 测试空输入
    with pytest.raises(ValueError):
        await flow.execute("")

    # 测试无效输入
    with pytest.raises(ValueError):
        await flow.execute("   ")

    # 测试超长输入
    long_input = "test" * 1000
    with pytest.raises(ValueError):
        await flow.execute(long_input)


@pytest.mark.asyncio
async def test_requirements_flow_state_transitions():
    """测试需求分析流程的状态转换"""
    # 创建流程实例
    flow = RequirementsFlow()

    # 检查初始状态
    assert flow.state_manager.current_state == FlowState.INITIALIZED.value

    # 执行流程
    result = await flow.execute("测试需求：开发一个简单的待办事项应用")

    # 验证最终状态
    assert flow.state_manager.current_state == FlowState.COMPLETED.value

    # 验证结果
    assert isinstance(result, dict)
    assert "status" in result
    assert result["status"] == "success"
    assert "result" in result
    assert "analysis" in result["result"]
    assert "report" in result["result"]
    assert "metrics" in result["result"]


if __name__ == "__main__":
    pytest.main(["-v", __file__])
