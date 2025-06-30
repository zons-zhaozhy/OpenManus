import pytest

from app.agent.dialogue_context import DialogueContext
from app.agent.manus import Manus
from app.agent.message import Message


@pytest.mark.asyncio
async def test_analyze_requirements_with_export_format(
    manus, dialogue_context, sample_requirements
):
    """测试带导出格式的需求分析"""
    # 设置对话上下文
    dialogue_context.accumulated_requirements = sample_requirements
    dialogue_context.history = [
        Message(role="user", content="我需要一个在线教育平台"),
        Message(role="assistant", content="好的，让我们开始需求分析"),
    ]
    manus.dialogue_context = dialogue_context

    # 测试Markdown格式
    markdown_report = await manus.analyze_requirements(
        "我需要一个在线教育平台", export_format="markdown"
    )
    assert isinstance(markdown_report, str)
    assert "# 需求评审报告" in markdown_report
    assert "## 基本信息" in markdown_report
    assert "## 质量评估" in markdown_report
    assert "### 总体评分" in markdown_report
    assert "### 详细指标" in markdown_report
    assert "### 质量可视化" in markdown_report
    assert "### 趋势分析" in markdown_report
    assert "### 问题分布" in markdown_report
    assert "## 问题分析" in markdown_report
    assert "### 阻塞问题" in markdown_report
    assert "### 改进建议" in markdown_report
    assert "## 历史记录" in markdown_report

    # 测试HTML格式
    try:
        import markdown

        html_report = await manus.analyze_requirements(
            "我需要一个在线教育平台", export_format="html"
        )
        assert isinstance(html_report, str)
        assert "<!DOCTYPE html>" in html_report
        assert "<html>" in html_report
        assert "<head>" in html_report
        assert "<body>" in html_report
        assert "</html>" in html_report
        assert "<style>" in html_report
        assert "mermaid.initialize" in html_report
    except ImportError:
        html_report = await manus.analyze_requirements(
            "我需要一个在线教育平台", export_format="html"
        )
        assert "注意：未安装markdown包" in html_report


@pytest.mark.asyncio
async def test_analyze_requirements_error_handling(manus, dialogue_context):
    """测试需求分析错误处理"""
    # 设置无效的对话上下文
    dialogue_context.accumulated_requirements = {}
    manus.dialogue_context = dialogue_context

    # 测试无效的导出格式
    report = await manus.analyze_requirements("我需要一个系统", export_format="invalid")
    assert isinstance(report, str)
    assert "需求分析失败" in report


@pytest.mark.asyncio
async def test_analyze_requirements_with_file_saving(
    manus, dialogue_context, sample_requirements, tmp_path
):
    """测试带文件保存的需求分析"""
    # 设置对话上下文
    dialogue_context.accumulated_requirements = sample_requirements
    dialogue_context.history = [
        Message(role="user", content="我需要一个在线教育平台"),
        Message(role="assistant", content="好的，让我们开始需求分析"),
    ]
    manus.dialogue_context = dialogue_context

    # 测试保存Markdown格式
    output_dir = tmp_path / "reports"
    markdown_report = await manus.analyze_requirements(
        "我需要一个在线教育平台",
        export_format="markdown",
        save_to_file=True,
        output_dir=str(output_dir),
    )
    assert isinstance(markdown_report, str)
    assert "报告已保存至" in markdown_report
    assert output_dir.exists()
    assert len(list(output_dir.glob("*.md"))) == 1

    # 测试保存HTML格式
    try:
        import markdown

        html_report = await manus.analyze_requirements(
            "我需要一个在线教育平台",
            export_format="html",
            save_to_file=True,
            output_dir=str(output_dir),
        )
        assert isinstance(html_report, str)
        assert "报告已保存至" in html_report
        assert output_dir.exists()
        assert len(list(output_dir.glob("*.html"))) == 1

        # 检查生成的HTML文件
        html_file = next(output_dir.glob("*.html"))
        with open(html_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "<!DOCTYPE html>" in content
            assert "<html>" in content
            assert "<head>" in content
            assert "<body>" in content
            assert "</html>" in content
    except ImportError:
        html_report = await manus.analyze_requirements(
            "我需要一个在线教育平台",
            export_format="html",
            save_to_file=True,
            output_dir=str(output_dir),
        )
        assert "未安装markdown包" in html_report


@pytest.mark.asyncio
async def test_analyze_requirements_without_file_saving(
    manus, dialogue_context, sample_requirements
):
    """测试不保存文件的需求分析"""
    # 设置对话上下文
    dialogue_context.accumulated_requirements = sample_requirements
    dialogue_context.history = [
        Message(role="user", content="我需要一个在线教育平台"),
        Message(role="assistant", content="好的，让我们开始需求分析"),
    ]
    manus.dialogue_context = dialogue_context

    # 测试不保存文件
    report = await manus.analyze_requirements(
        "我需要一个在线教育平台", save_to_file=False
    )
    assert isinstance(report, str)
    assert "报告已保存至" not in report


@pytest.mark.asyncio
async def test_analyze_requirements_invalid_directory(
    manus, dialogue_context, sample_requirements
):
    """测试保存到无效目录时的错误处理"""
    # 设置对话上下文
    dialogue_context.accumulated_requirements = sample_requirements
    dialogue_context.history = [
        Message(role="user", content="我需要一个在线教育平台"),
        Message(role="assistant", content="好的，让我们开始需求分析"),
    ]
    manus.dialogue_context = dialogue_context

    # 测试保存到无效目录
    report = await manus.analyze_requirements(
        "我需要一个在线教育平台",
        save_to_file=True,
        output_dir="/invalid/directory/path",
    )
    assert isinstance(report, str)
    assert "保存报告失败" in report


@pytest.mark.asyncio
async def test_analyze_requirements_with_batch_export(
    manus, dialogue_context, sample_requirements, tmp_path
):
    """测试带批量导出的需求分析"""
    # 设置对话上下文
    dialogue_context.accumulated_requirements = sample_requirements
    dialogue_context.history = [
        Message(role="user", content="我需要一个在线教育平台"),
        Message(role="assistant", content="好的，让我们开始需求分析"),
    ]
    manus.dialogue_context = dialogue_context

    # 测试批量导出
    output_dir = tmp_path / "reports"
    report = await manus.analyze_requirements(
        "我需要一个在线教育平台",
        export_format="markdown",
        save_to_file=True,
        output_dir=str(output_dir),
        batch_export=True,
        include_history=True,
    )

    assert isinstance(report, str)
    assert "需求分析报告" in report
    assert "本次评审结果" in report
    assert "批量导出结果" in report
    assert "已导出以下文件" in report
    assert output_dir.exists()
    assert len(list(output_dir.glob("*.md"))) >= 2  # 至少有当前报告和汇总报告


@pytest.mark.asyncio
async def test_analyze_requirements_with_batch_export_no_history(
    manus, dialogue_context, sample_requirements, tmp_path
):
    """测试不包含历史记录的批量导出"""
    # 设置对话上下文
    dialogue_context.accumulated_requirements = sample_requirements
    dialogue_context.history = [
        Message(role="user", content="我需要一个在线教育平台"),
        Message(role="assistant", content="好的，让我们开始需求分析"),
    ]
    manus.dialogue_context = dialogue_context

    # 测试不包含历史记录的批量导出
    output_dir = tmp_path / "reports"
    report = await manus.analyze_requirements(
        "我需要一个在线教育平台",
        export_format="markdown",
        save_to_file=True,
        output_dir=str(output_dir),
        batch_export=True,
        include_history=False,
    )

    assert isinstance(report, str)
    assert "需求分析报告" in report
    assert "本次评审结果" in report
    assert "批量导出结果" in report
    assert output_dir.exists()
    assert len(list(output_dir.glob("*.md"))) == 2  # 只有当前报告和汇总报告


@pytest.mark.asyncio
async def test_analyze_requirements_with_batch_export_html(
    manus, dialogue_context, sample_requirements, tmp_path
):
    """测试HTML格式的批量导出"""
    # 设置对话上下文
    dialogue_context.accumulated_requirements = sample_requirements
    dialogue_context.history = [
        Message(role="user", content="我需要一个在线教育平台"),
        Message(role="assistant", content="好的，让我们开始需求分析"),
    ]
    manus.dialogue_context = dialogue_context

    # 测试HTML格式的批量导出
    output_dir = tmp_path / "reports"
    report = await manus.analyze_requirements(
        "我需要一个在线教育平台",
        export_format="html",
        save_to_file=True,
        output_dir=str(output_dir),
        batch_export=True,
        include_history=True,
    )

    assert isinstance(report, str)
    assert "需求分析报告" in report
    assert "本次评审结果" in report
    assert "批量导出结果" in report
    assert output_dir.exists()
    assert len(list(output_dir.glob("*.html"))) >= 2  # 至少有当前报告和汇总报告

    # 检查HTML文件内容
    for html_file in output_dir.glob("*.html"):
        with open(html_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "<!DOCTYPE html>" in content
            assert "<html>" in content
            assert "<head>" in content
            assert "<body>" in content
            assert "</html>" in content
            if "summary" in str(html_file):
                assert "需求评审汇总报告" in content
                assert "评审概况" in content
                assert "平均得分" in content


@pytest.mark.asyncio
async def test_analyze_requirements_with_batch_export_invalid_directory(
    manus, dialogue_context, sample_requirements
):
    """测试无效目录的批量导出"""
    # 设置对话上下文
    dialogue_context.accumulated_requirements = sample_requirements
    dialogue_context.history = [
        Message(role="user", content="我需要一个在线教育平台"),
        Message(role="assistant", content="好的，让我们开始需求分析"),
    ]
    manus.dialogue_context = dialogue_context

    # 测试无效目录的批量导出
    report = await manus.analyze_requirements(
        "我需要一个在线教育平台",
        save_to_file=True,
        output_dir="/invalid/directory/path",
        batch_export=True,
    )

    assert isinstance(report, str)
    assert "批量导出失败" in report
