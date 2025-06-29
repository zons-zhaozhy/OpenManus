"""
技术文档编写智能体

基于工作流引擎架构，专注于需求文档的专业编写：
- 需求规格说明
- 用例文档
- 接口设计
- 数据模型
"""

from typing import Any, Dict, List, Optional
from enum import Enum

from loguru import logger

from app.workflow.core.workflow_agent import WorkflowAgent
from app.workflow.core.workflow_context import WorkflowContext
from app.workflow.core.workflow_result import WorkflowResult
from app.workflow.engine.event_bus import EventBus
from app.llm import LLM


class DocumentType(Enum):
    """文档类型"""
    REQUIREMENT_SPEC = "需求规格说明书"
    USE_CASE = "用例文档"
    API_DESIGN = "接口设计文档"
    DATA_MODEL = "数据模型文档"


class TechnicalWriterAgent(WorkflowAgent):
    """技术文档编写智能体"""

    def __init__(
        self,
        workflow_context: WorkflowContext,
        event_bus: EventBus,
        name: str = "技术文档编写师",
        **kwargs
    ):
        description = "专注于需求文档的专业编写，包括规格说明、用例文档等"
        system_prompt = self._get_system_prompt()

        super().__init__(
            name=name,
            description=description,
            system_prompt=system_prompt,
            workflow_context=workflow_context,
            event_bus=event_bus,
            llm=LLM(config_name="technical_writer"),
            max_steps=4,
            **kwargs
        )

        self.current_doc_type = DocumentType.REQUIREMENT_SPEC
        self.doc_quality_scores = {doc_type: 0.0 for doc_type in DocumentType}
        self.generated_docs: Dict[DocumentType, str] = {}

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一位专业的技术文档编写专家，负责将需求分析结果转化为标准的技术文档。

# 工作原则
1. **专业规范**：遵循软件工程文档标准
2. **清晰完整**：确保文档结构清晰，内容完整
3. **一致性**：保持术语和格式的一致性
4. **可追溯**：建立需求项之间的关联关系
5. **可维护**：便于后续更新和维护

# 文档类型
## 1. 需求规格说明书（SRS）
- **文档结构**
  * 文档信息
  * 引言
  * 总体描述
  * 具体需求
  * 其他需求
  * 附录
- **编写要求**
  * IEEE 830标准
  * 结构化描述
  * 完整性检查
  * 一致性验证

## 2. 用例文档
- **基本信息**
  * 用例名称
  * 参与者
  * 前置条件
  * 后置条件
- **用例描述**
  * 基本流程
  * 替代流程
  * 异常流程
  * 业务规则

## 3. 接口设计文档
- **接口规范**
  * 接口描述
  * 请求参数
  * 响应格式
  * 错误码
- **设计原则**
  * RESTful规范
  * 版本控制
  * 安全机制
  * 性能考虑

## 4. 数据模型文档
- **模型定义**
  * 实体关系
  * 属性定义
  * 约束条件
  * 索引设计
- **设计规范**
  * 命名规范
  * 类型规范
  * 关系规范
  * 性能优化

请基于以上原则和规范，编写专业的技术文档。"""

    async def step(self, input_data: Any = None) -> Any:
        """执行文档编写步骤"""
        try:
            if self.current_step == 1:
                return await self._analyze_requirements()
            elif self.current_step == 2:
                return await self._generate_document_structure()
            elif self.current_step == 3:
                return await self._write_document_content()
            else:
                return await self._review_and_finalize()

        except Exception as e:
            logger.error(f"文档编写步骤执行失败: {e}")
            raise

    async def _analyze_requirements(self) -> str:
        """分析需求输入"""
        # 从上下文获取需求分析结果
        requirement_content = self.context.get("requirement_content", "")
        clarification_summary = self.context.get("clarification_summary", "")
        business_analysis = self.context.get("business_analysis_report", "")

        prompt = f"""请分析以下需求相关信息，为编写{self.current_doc_type.value}做准备：

需求内容：
{requirement_content}

需求澄清结果：
{clarification_summary}

业务分析报告：
{business_analysis}

分析要点：
1. 文档类型的适用性
2. 需要补充的信息
3. 文档的重点内容
4. 潜在的难点

请提供详细的分析结果。"""

        response = await self.llm.ask(
            messages=[{"role": "system", "content": prompt}],
            temperature=0.3
        )
        
        self.update_memory("assistant", response)
        
        # 发布需求分析完成事件
        await self.event_bus.publish(
            f"{self.name}_requirements_analyzed",
            {"agent": self.name, "analysis": response}
        )
        
        return response

    async def _generate_document_structure(self) -> str:
        """生成文档结构"""
        prompt = f"""请为{self.current_doc_type.value}生成详细的文档结构：

要求：
1. 符合文档标准规范
2. 结构层次清晰
3. 覆盖所有关键内容
4. 便于后续填充

请提供完整的文档结构设计。"""

        response = await self.llm.ask(
            messages=self.get_memory() + [{"role": "system", "content": prompt}],
            temperature=0.3
        )
        
        self.update_memory("assistant", response)
        
        # 发布文档结构生成完成事件
        await self.event_bus.publish(
            f"{self.name}_document_structure_generated",
            {"agent": self.name, "structure": response}
        )
        
        return response

    async def _write_document_content(self) -> str:
        """编写文档内容"""
        prompt = f"""请基于前面的分析和结构，编写{self.current_doc_type.value}的具体内容：

编写要求：
1. 专业性：使用规范的技术语言
2. 完整性：覆盖所有必要信息
3. 准确性：描述准确无歧义
4. 可读性：条理清晰易于理解

请提供完整的文档内容。"""

        response = await self.llm.ask(
            messages=self.get_memory() + [{"role": "system", "content": prompt}],
            temperature=0.4
        )
        
        self.update_memory("assistant", response)
        
        # 保存生成的文档
        self.generated_docs[self.current_doc_type] = response
        
        # 发布文档内容编写完成事件
        await self.event_bus.publish(
            f"{self.name}_document_content_written",
            {
                "agent": self.name,
                "doc_type": self.current_doc_type.value,
                "content": response
            }
        )
        
        return response

    async def _review_and_finalize(self) -> str:
        """审查和完善文档"""
        prompt = f"""请审查{self.current_doc_type.value}的内容质量：

审查维度：
1. 完整性检查
2. 一致性验证
3. 规范性评估
4. 可读性评估
5. 改进建议

请提供详细的审查报告和改进建议。"""

        response = await self.llm.ask(
            messages=self.get_memory() + [{"role": "system", "content": prompt}],
            temperature=0.3
        )
        
        self.update_memory("assistant", response)
        
        # 更新文档质量分数
        self.doc_quality_scores[self.current_doc_type] = self._calculate_quality_score(response)
        
        # 更新上下文
        self.context.update({
            f"{self.current_doc_type.value}_content": self.generated_docs[self.current_doc_type],
            f"{self.current_doc_type.value}_quality_score": self.doc_quality_scores[self.current_doc_type]
        })
        
        # 发布文档审查完成事件
        await self.event_bus.publish(
            f"{self.name}_document_reviewed",
            {
                "agent": self.name,
                "doc_type": self.current_doc_type.value,
                "review": response,
                "quality_score": self.doc_quality_scores[self.current_doc_type]
            }
        )
        
        return response

    def _calculate_quality_score(self, review_content: str) -> float:
        """计算文档质量分数"""
        # 简单的质量评分逻辑，可以根据需要优化
        score = 0.0
        positive_indicators = [
            "完整", "清晰", "准确", "规范", "专业",
            "结构良好", "易于理解", "逻辑性强"
        ]
        negative_indicators = [
            "缺失", "混乱", "模糊", "歧义", "不规范",
            "难以理解", "逻辑混乱", "需要改进"
        ]
        
        for indicator in positive_indicators:
            if indicator in review_content:
                score += 1.0
                
        for indicator in negative_indicators:
            if indicator in review_content:
                score -= 1.0
        
        # 归一化到0-10分
        total_indicators = len(positive_indicators) + len(negative_indicators)
        normalized_score = (score + total_indicators) / (2 * total_indicators) * 10
        
        return round(normalized_score, 2)

    async def switch_document_type(self) -> None:
        """切换文档类型"""
        doc_types = list(DocumentType)
        current_index = doc_types.index(self.current_doc_type)
        next_index = (current_index + 1) % len(doc_types)
        self.current_doc_type = doc_types[next_index]
        
        # 重置步骤
        self.current_step = 1
        
        # 发布文档类型切换事件
        await self.event_bus.publish(
            f"{self.name}_document_type_switched",
            {
                "agent": self.name,
                "old_type": doc_types[current_index].value,
                "new_type": doc_types[next_index].value
            }
        )

    def get_document_summary(self) -> Dict[str, Any]:
        """获取文档生成摘要"""
        return {
            "current_doc_type": self.current_doc_type.value,
            "quality_scores": {
                doc_type.value: score 
                for doc_type, score in self.doc_quality_scores.items()
            },
            "generated_docs_count": len(self.generated_docs),
            "current_step": self.current_step,
            "state": self.state.value
        }
