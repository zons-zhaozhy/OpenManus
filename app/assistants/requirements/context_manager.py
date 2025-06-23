"""
需求分析多智能体上下文管理器

优化智能体间的上下文信息共享机制：
1. 统一的上下文存储和检索
2. 智能体间的信息传递
3. 知识库集成
4. 代码库分析结果共享
5. 多轮对话历史管理
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.logger import logger
from app.schema import Message


@dataclass
class ContextItem:
    """上下文信息项"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str = ""
    stage: str = ""  # 需求澄清、业务分析、文档编写、质量评审
    content: str = ""
    content_type: str = "text"  # text, analysis, document, review
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SharedKnowledge:
    """共享知识库"""

    requirements_patterns: Dict[str, Any] = field(default_factory=dict)
    business_domains: Dict[str, Any] = field(default_factory=dict)
    technical_constraints: Dict[str, Any] = field(default_factory=dict)
    user_feedback_history: List[str] = field(default_factory=list)


class RequirementsContextManager:
    """需求分析上下文管理器"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.context_items: List[ContextItem] = []
        self.shared_knowledge = SharedKnowledge()
        self.agent_conversations: Dict[str, List[Message]] = {}
        self.global_state: Dict[str, Any] = {
            "current_stage": "初始化",
            "user_input": "",
            "clarity_score": 0.0,
            "business_complexity": "未知",
            "technical_feasibility": "未评估",
            "document_completeness": 0.0,
            "quality_score": 0.0,
        }

    def add_context_item(
        self,
        agent_name: str,
        stage: str,
        content: str,
        content_type: str = "text",
        confidence: float = 1.0,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """添加上下文信息项"""
        item = ContextItem(
            agent_name=agent_name,
            stage=stage,
            content=content,
            content_type=content_type,
            confidence=confidence,
            metadata=metadata or {},
        )
        self.context_items.append(item)
        logger.info(f"添加上下文: {agent_name} - {stage} - {content_type}")
        return item.id

    def get_context_for_agent(
        self, agent_name: str, include_stages: List[str] = None
    ) -> List[ContextItem]:
        """获取特定智能体的相关上下文"""
        items = []
        for item in self.context_items:
            # 包含自己的所有信息
            if item.agent_name == agent_name:
                items.append(item)
            # 包含指定阶段的信息
            elif include_stages and item.stage in include_stages:
                items.append(item)
        return sorted(items, key=lambda x: x.timestamp)

    def get_stage_results(self, stage: str) -> List[ContextItem]:
        """获取特定阶段的所有结果"""
        return [item for item in self.context_items if item.stage == stage]

    def build_context_prompt(self, agent_name: str, current_stage: str) -> str:
        """为智能体构建包含上下文的提示词"""
        # 获取前序阶段的结果
        previous_stages = self._get_previous_stages(current_stage)
        context_items = []

        for stage in previous_stages:
            stage_items = self.get_stage_results(stage)
            context_items.extend(stage_items)

        if not context_items:
            return f"当前阶段：{current_stage}\n没有前序上下文信息。"

        # 构建上下文提示词
        context_prompt = f"""# 项目上下文信息

## 当前阶段
{current_stage}

## 项目状态
- 用户输入：{self.global_state.get('user_input', '未提供')}
- 当前阶段：{self.global_state.get('current_stage', '未知')}
- 需求清晰度：{self.global_state.get('clarity_score', 0.0)}/1.0

## 前序阶段成果
"""

        for item in context_items[-5:]:  # 只显示最近5个重要结果
            context_prompt += f"""
### {item.stage} - {item.agent_name}
**类型**: {item.content_type}
**置信度**: {item.confidence}
**内容**:
{item.content[:500]}...

"""

        return context_prompt

    def _get_previous_stages(self, current_stage: str) -> List[str]:
        """获取当前阶段的前序阶段"""
        stage_order = ["需求澄清", "业务分析", "文档编写", "质量评审"]
        try:
            current_index = stage_order.index(current_stage)
            return stage_order[:current_index]
        except ValueError:
            return []

    def update_global_state(self, key: str, value: Any):
        """更新全局状态"""
        self.global_state[key] = value
        logger.info(f"更新全局状态: {key} = {value}")

    def get_conversation_for_agent(self, agent_name: str) -> List[Message]:
        """获取智能体的对话历史"""
        return self.agent_conversations.get(agent_name, [])

    def add_message_for_agent(self, agent_name: str, message: Message):
        """为智能体添加消息"""
        if agent_name not in self.agent_conversations:
            self.agent_conversations[agent_name] = []
        self.agent_conversations[agent_name].append(message)

    def share_knowledge_between_agents(
        self, from_agent: str, to_agent: str, knowledge_type: str, knowledge_data: Any
    ):
        """智能体间共享知识"""
        knowledge_id = str(uuid.uuid4())

        # 记录知识共享
        self.add_context_item(
            agent_name=f"{from_agent}→{to_agent}",
            stage="知识共享",
            content=f"共享{knowledge_type}数据",
            content_type="knowledge_transfer",
            metadata={
                "from_agent": from_agent,
                "to_agent": to_agent,
                "knowledge_type": knowledge_type,
                "knowledge_id": knowledge_id,
                "data": knowledge_data,
            },
        )

        logger.info(f"知识共享: {from_agent} → {to_agent} ({knowledge_type})")
        return knowledge_id

    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话摘要"""
        stage_counts = {}
        for item in self.context_items:
            stage_counts[item.stage] = stage_counts.get(item.stage, 0) + 1

        return {
            "session_id": self.session_id,
            "total_context_items": len(self.context_items),
            "stage_distribution": stage_counts,
            "global_state": self.global_state,
            "active_agents": list(self.agent_conversations.keys()),
            "session_duration": datetime.now()
            - min(
                [item.timestamp for item in self.context_items], default=datetime.now()
            ),
        }
