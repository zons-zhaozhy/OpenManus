"""
需求澄清师智能体 - 基于BaseAgent

充分利用OpenManus现有能力：
- 继承BaseAgent，自动获得状态管理、内存管理、LLM客户端
- 使用现有的提示词系统和配置管理
- 专注于需求澄清的核心逻辑
"""

from typing import Dict, List, Optional

from app.agent.base import BaseAgent
from app.llm import LLM
from app.logger import logger


class RequirementClarifierAgent(BaseAgent):
    """需求澄清师智能体"""

    def __init__(self, name: str = "需求澄清师", **kwargs):
        # 使用专门的系统提示词
        system_prompt = self._get_system_prompt()

        super().__init__(
            name=name,
            system_prompt=system_prompt,
            next_step_prompt="请分析用户需求，识别模糊点和缺失信息，生成有针对性的澄清问题。",
            llm=LLM(config_name="requirements_clarifier"),  # 使用专门的LLM配置
            max_steps=5,  # 限制澄清轮数
            **kwargs,
        )

        self.clarification_questions: List[str] = []
        self.clarification_answers: Dict[str, str] = {}
        self.clarity_score = 0.0

    def _get_system_prompt(self) -> str:
        """获取系统提示词，复用现有的提示词管理"""
        return """你是一位资深的需求澄清师，专门负责通过专业的提问来澄清模糊的用户需求。

# 核心原则（重要！）
1. **严谨性**：绝不瞎猜、不假设、不自作主张
2. **科学性**：运用软件工程需求分析的方法和手段
3. **用户友好**：提供快捷、便利的澄清途径
4. **语义理解**：深入理解用户真实意图
5. **结构化**：系统性多轮交互引导
6. **专业性**：避免过度发散，聚焦核心需求

# 职责
- 分析用户的初始需求描述，识别语义模糊点
- 基于软件工程理论设计专业澄清问题
- 提供多种便利的作答方式（选择题、填空题等）
- 引导用户逐步完善需求信息，避免发散

# 工作方法（科学严谨）
1. **需求解构**：将复杂需求分解为可验证的组件
2. **5W1H分析**：Who（用户）、What（功能）、When（时机）、Where（场景）、Why（价值）、How（约束）
3. **优先级排序**：区分核心需求与辅助需求
4. **边界明确**：明确包含什么、不包含什么
5. **验收标准**：如何验证需求是否被满足

# 澄清问题设计原则
- **封闭式问题**：提供选择项，便于快速回答
- **层次化提问**：从宏观到微观，逐步深入
- **场景化描述**：用具体场景帮助用户理解
- **对比式选择**：通过对比帮助用户明确偏好

# 澄清维度（系统化）
1. **功能边界**：核心功能 vs 扩展功能
2. **用户角色**：主要用眷 vs 次要用户
3. **使用场景**：典型场景 vs 边缘场景
4. **性能要求**：响应时间、并发量等具体指标
5. **约束条件**：技术栈、预算、时间等限制
6. **集成需求**：与现有系统的对接要求

# 回复格式要求
请按以下结构化格式回复：

## 需求理解总结
[简洁总结对用户需求的理解]

## 关键澄清问题
[3-5个结构化问题，提供选择项或填空]

## 优先澄清建议
[建议用户优先回答哪些问题，为什么]

严格按照软件工程需求分析规范工作，确保澄清过程科学、高效、用户友好。"""

    async def step(self) -> str:
        """执行单步澄清任务"""
        try:
            # 获取最新的用户消息
            if not self.messages:
                return "没有收到用户需求，请先提供需求描述。"

            last_message = self.messages[-1]

            # 根据当前状态决定下一步行动
            if last_message.role == "user":
                # 分析用户需求，生成澄清问题
                return await self._analyze_and_clarify()
            else:
                # 继续分析或总结
                return await self._continue_clarification()

        except Exception as e:
            logger.error(f"需求澄清步骤执行失败: {e}")
            return f"澄清过程中发生错误: {str(e)}"

    async def _analyze_and_clarify(self) -> str:
        """分析需求并生成澄清问题"""
        try:
            # 构建分析提示词
            analysis_prompt = """请分析以下用户需求，识别需要澄清的关键点：

分析框架：
1. 需求清晰度评估（1-10分）
2. 缺失的关键信息
3. 模糊或矛盾的表述
4. 建议的澄清问题（3-5个）

请以结构化格式输出分析结果。"""

            # 调用LLM进行分析
            messages = self.memory.get_messages() + [
                {"role": "system", "content": analysis_prompt}
            ]

            response = await self.llm.ask(messages, temperature=0.3)

            # 更新智能体状态
            self.update_memory("assistant", response)

            # 解析并存储澄清问题
            self._extract_clarification_questions(response)

            logger.info(f"生成了 {len(self.clarification_questions)} 个澄清问题")
            return response

        except Exception as e:
            logger.error(f"需求分析失败: {e}")
            return "需求分析过程中发生错误，请重新提供需求描述。"

    async def _continue_clarification(self) -> str:
        """继续澄清过程"""
        # 评估当前澄清程度
        clarity_score = await self._evaluate_clarity()

        if clarity_score >= 8.0:
            # 澄清度足够，结束澄清
            self.state = self.state.__class__.FINISHED
            return await self._generate_clarification_summary()
        else:
            # 需要进一步澄清
            return await self._generate_follow_up_questions()

    async def _evaluate_clarity(self) -> float:
        """评估当前需求澄清度"""
        try:
            evaluation_prompt = """请评估当前需求的澄清度（1-10分）：

评估标准：
- 功能需求是否明确？
- 非功能需求是否充分？
- 用户角色和场景是否清晰？
- 技术约束是否明确？
- 验收标准是否可定义？

请给出分数（1-10）和简要说明。"""

            messages = self.memory.get_messages() + [
                {"role": "system", "content": evaluation_prompt}
            ]

            response = await self.llm.ask(messages, temperature=0.2)

            # 简单的分数解析（实际项目中可以更复杂）
            import re

            score_match = re.search(r"(\d+(?:\.\d+)?)", response)
            if score_match:
                self.clarity_score = float(score_match.group(1))
            else:
                self.clarity_score = 5.0  # 默认中等分数

            return self.clarity_score

        except Exception as e:
            logger.error(f"澄清度评估失败: {e}")
            return 5.0

    async def _generate_follow_up_questions(self) -> str:
        """生成后续澄清问题"""
        prompt = """基于当前对话，生成2-3个最重要的后续澄清问题，优先关注：
1. 尚未明确的核心功能
2. 重要的非功能需求
3. 关键的业务规则或约束

请直接列出问题，简洁明了。"""

        messages = self.memory.get_messages() + [{"role": "system", "content": prompt}]

        response = await self.llm.ask(messages, temperature=0.4)
        self.update_memory("assistant", response)

        return response

    async def _generate_clarification_summary(self) -> str:
        """生成澄清总结"""
        summary_prompt = """请总结整个需求澄清过程的结果：

总结结构：
1. **澄清后的核心需求**
2. **关键功能点**
3. **重要约束条件**
4. **后续建议**

请以结构化、易理解的方式输出。"""

        messages = self.memory.get_messages() + [
            {"role": "system", "content": summary_prompt}
        ]

        response = await self.llm.ask(messages, temperature=0.3)
        self.update_memory("assistant", response)

        logger.info("需求澄清流程完成")
        return response

    def _extract_clarification_questions(self, response: str):
        """从回复中提取澄清问题"""
        # 简单的问题提取逻辑（实际项目中可以更复杂）
        import re

        questions = re.findall(r"\d+\.\s*(.+\?)", response)
        self.clarification_questions.extend(questions)

    def get_clarification_status(self) -> Dict:
        """获取澄清状态"""
        return {
            "clarity_score": self.clarity_score,
            "questions_asked": len(self.clarification_questions),
            "current_step": self.current_step,
            "state": (
                self.state.value if hasattr(self.state, "value") else str(self.state)
            ),
            "questions": self.clarification_questions[-3:],  # 最近3个问题
        }
