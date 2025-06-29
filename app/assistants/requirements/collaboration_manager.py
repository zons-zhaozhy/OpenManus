"""
协作管理器模块
"""

import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from app.logger import logger


class CollaborationManager:
    """协作管理器"""

    def __init__(self) -> None:
        """初始化协作管理器"""
        self.agents: Dict[str, Any] = {}
        self.agent_states: Dict[str, str] = {}
        self.agent_results: Dict[str, Any] = {}
        self.agent_errors: Dict[str, str] = {}
        self.active_agents: Set[str] = set()

    def register_agent(self, agent_id: str, agent: Any) -> None:
        """
        注册智能体

        Args:
            agent_id: 智能体ID
            agent: 智能体实例
        """
        logger.info(f"注册智能体: {agent_id}")
        self.agents[agent_id] = agent
        self.agent_states[agent_id] = "IDLE"
        self.agent_results[agent_id] = None
        self.agent_errors[agent_id] = None

    def get_agent(self, agent_id: str) -> Any:
        """
        获取智能体

        Args:
            agent_id: 智能体ID

        Returns:
            Any: 智能体实例
        """
        if agent_id not in self.agents:
            logger.error(f"智能体 {agent_id} 不存在")
            raise ValueError(f"智能体 {agent_id} 不存在")
        return self.agents[agent_id]

    async def update_state(
        self,
        agent_id: str,
        state: str,
        task: Optional[str] = None,
        progress: Optional[float] = None,
    ) -> None:
        """
        更新智能体状态

        Args:
            agent_id: 智能体ID
            state: 新状态
            task: 当前任务描述 (可选)
            progress: 进度百分比 (0.0-1.0) (可选)
        """
        if agent_id not in self.agents:
            logger.error(f"无法更新状态: 智能体 {agent_id} 不存在")
            raise ValueError(f"智能体 {agent_id} 不存在")

        self.agent_states[agent_id] = state
        logger.info(f"更新智能体 {agent_id} 状态: {state}")

        if state == "ACTIVE":
            self.active_agents.add(agent_id)
        elif state in ["IDLE", "COMPLETED", "ERROR"]:
            if agent_id in self.active_agents:
                self.active_agents.remove(agent_id)

        if task is not None:
            logger.info(f"智能体 {agent_id} 当前任务: {task}")

        if progress is not None:
            logger.info(f"智能体 {agent_id} 进度: {progress*100:.1f}%")

    async def update_state_async(self, agent_id: str, state: str) -> None:
        """
        异步更新智能体状态 (兼容旧代码)

        Args:
            agent_id: 智能体ID
            state: 新状态
        """
        await self.update_state(agent_id, state)

    def get_all_agents(self) -> Dict[str, Any]:
        """
        获取所有智能体

        Returns:
            Dict[str, Any]: 所有智能体
        """
        return self.agents

    def update_result(self, agent_id: str, result: Any) -> None:
        """
        更新智能体结果

        Args:
            agent_id: 智能体ID
            result: 结果
        """
        logger.info(f"更新智能体 {agent_id} 结果")
        if agent_id not in self.agents:
            logger.error(f"智能体 {agent_id} 不存在")
            raise ValueError(f"智能体 {agent_id} 不存在")
        self.agent_results[agent_id] = result

    def update_error(self, agent_id: str, error: str) -> None:
        """
        更新智能体错误

        Args:
            agent_id: 智能体ID
            error: 错误
        """
        logger.error(f"智能体 {agent_id} 发生错误: {error}")
        if agent_id not in self.agents:
            logger.error(f"智能体 {agent_id} 不存在")
            raise ValueError(f"智能体 {agent_id} 不存在")
        self.agent_errors[agent_id] = error
        self.agent_states[agent_id] = "ERROR"
        if agent_id in self.active_agents:
            self.active_agents.remove(agent_id)

    def get_state(self, agent_id: str) -> str:
        """
        获取智能体状态

        Args:
            agent_id: 智能体ID

        Returns:
            str: 状态
        """
        if agent_id not in self.agents:
            logger.error(f"智能体 {agent_id} 不存在")
            raise ValueError(f"智能体 {agent_id} 不存在")
        return self.agent_states[agent_id]

    def get_result(self, agent_id: str) -> Any:
        """
        获取智能体结果

        Args:
            agent_id: 智能体ID

        Returns:
            Any: 结果
        """
        if agent_id not in self.agents:
            logger.error(f"智能体 {agent_id} 不存在")
            raise ValueError(f"智能体 {agent_id} 不存在")
        return self.agent_results[agent_id]

    def get_error(self, agent_id: str) -> Optional[str]:
        """
        获取智能体错误

        Args:
            agent_id: 智能体ID

        Returns:
            Optional[str]: 错误
        """
        if agent_id not in self.agents:
            logger.error(f"智能体 {agent_id} 不存在")
            raise ValueError(f"智能体 {agent_id} 不存在")
        return self.agent_errors[agent_id]

    def is_active(self, agent_id: str) -> bool:
        """
        检查智能体是否活跃

        Args:
            agent_id: 智能体ID

        Returns:
            bool: 是否活跃
        """
        if agent_id not in self.agents:
            logger.error(f"智能体 {agent_id} 不存在")
            raise ValueError(f"智能体 {agent_id} 不存在")
        return self.agent_states[agent_id] == "ACTIVE"

    def has_active_agents(self) -> bool:
        """
        检查是否有活跃的智能体

        Returns:
            bool: 是否有活跃的智能体
        """
        return len(self.active_agents) > 0

    def get_active_agents(self) -> Set[str]:
        """
        获取所有活跃的智能体

        Returns:
            Set[str]: 活跃的智能体ID集合
        """
        return self.active_agents

    async def wait_for_completion(self, timeout: Optional[float] = None) -> None:
        """
        等待所有智能体完成

        Args:
            timeout: 超时时间(秒)

        Raises:
            TimeoutError: 如果超时
            RuntimeError: 如果有智能体出错
        """
        start_time = asyncio.get_event_loop().time()

        while self.has_active_agents():
            # 检查超时
            if timeout is not None:
                current_time = asyncio.get_event_loop().time()
                if current_time - start_time > timeout:
                    active_agents = ", ".join(self.get_active_agents())
                    logger.error(
                        f"等待智能体完成超时，仍在活跃的智能体: {active_agents}"
                    )
                    raise TimeoutError(
                        f"等待智能体完成超时，仍在活跃的智能体: {active_agents}"
                    )

            # 检查错误
            for agent_id in list(self.agents.keys()):
                if self.agent_states[agent_id] == "ERROR":
                    error = self.agent_errors[agent_id]
                    logger.error(f"智能体 {agent_id} 出错: {error}")
                    raise RuntimeError(f"智能体 {agent_id} 出错: {error}")

            # 等待一段时间
            await asyncio.sleep(0.1)

        # 最终检查是否有错误
        for agent_id in list(self.agents.keys()):
            if self.agent_states[agent_id] == "ERROR":
                error = self.agent_errors[agent_id]
                logger.error(f"智能体 {agent_id} 出错: {error}")
                raise RuntimeError(f"智能体 {agent_id} 出错: {error}")
