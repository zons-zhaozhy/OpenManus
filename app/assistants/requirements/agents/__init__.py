"""
需求分析智能体模块

所有智能体都基于BaseAgent实现，充分利用OpenManus现有架构：
- 自动的状态管理和内存管理
- 统一的LLM客户端注入
- 标准的执行循环和错误处理
"""

from .business_analyst import BusinessAnalystAgent
from .quality_reviewer import QualityReviewerAgent
from .requirement_clarifier import RequirementClarifierAgent
from .technical_writer import TechnicalWriterAgent

__all__ = [
    "RequirementClarifierAgent",
    "BusinessAnalystAgent",
    "TechnicalWriterAgent",
    "QualityReviewerAgent",
]
