"""State management for OpenManus flows"""

import traceback
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from app.logger import log_exception, logger


class FlowState(Enum):
    """流程状态"""

    INITIALIZED = 1  # 初始化完成
    READY = 2  # 准备就绪
    RUNNING = 3  # 正在运行
    PAUSED = 4  # 暂停
    COMPLETED = 5  # 完成
    FAILED = 6  # 失败
    CANCELLED = 7  # 取消

    @classmethod
    def is_terminal(cls, state: Enum) -> bool:
        """Check if a state is terminal"""
        return state in [cls.COMPLETED, cls.FAILED]

    @classmethod
    def can_transition(cls, from_state: "FlowState", to_state: "FlowState") -> bool:
        """检查状态转换是否有效"""
        valid_transitions = {
            cls.INITIALIZED: {cls.READY, cls.FAILED},
            cls.READY: {cls.RUNNING, cls.FAILED, cls.CANCELLED},
            cls.RUNNING: {cls.PAUSED, cls.COMPLETED, cls.FAILED, cls.CANCELLED},
            cls.PAUSED: {cls.RUNNING, cls.FAILED, cls.CANCELLED},
            cls.COMPLETED: {cls.FAILED},  # 允许完成状态转为失败
            cls.FAILED: set(),  # 失败是终态
            cls.CANCELLED: set(),  # 取消是终态
        }
        return to_state in valid_transitions.get(from_state, set())


class FlowStateManager(BaseModel):
    """Manages state for a flow execution"""

    current_state: Enum = Field(default=FlowState.INITIALIZED)
    state_data: Dict[str, Any] = Field(default_factory=dict)
    error_count: int = Field(default=0)
    max_errors: int = Field(default=3)
    last_error: Optional[str] = None

    def transition_to(self, new_state: Enum) -> bool:
        """
        Attempt to transition to a new state

        Args:
            new_state: The target state

        Returns:
            bool: True if transition was successful

        Raises:
            ValueError: If the transition is invalid
        """
        try:
            logger.info(f"尝试从 {self.current_state} 转换到 {new_state}")

            # 检查当前状态是否已经是目标状态
            if self.current_state == new_state:
                logger.warning(f"当前状态已经是 {new_state}，无需转换")
                return True

            # 检查转换是否有效
            if not FlowState.can_transition(self.current_state, new_state):
                error_msg = f"无效的状态转换: {self.current_state} -> {new_state}"
                logger.error(error_msg)
                logger.error(f"堆栈跟踪: {traceback.format_stack()}")

                # 如果尝试从 INITIALIZED 转换到 RUNNING，但没有经过 READY 状态
                if (
                    self.current_state == FlowState.INITIALIZED
                    and new_state == FlowState.RUNNING
                ):
                    logger.error(
                        "错误: 从 INITIALIZED 转换到 RUNNING 必须先经过 READY 状态"
                    )
                    # 抛出 READY 异常，表示需要先设置为 READY 状态
                    raise ValueError("READY")

                # 其他无效转换
                raise ValueError(error_msg)

            # 执行状态转换
            self.current_state = new_state
            logger.info(f"状态转换成功: {new_state}")
            return True

        except Exception as e:
            logger.error(f"状态转换失败: {self.current_state} -> {new_state}: {str(e)}")
            raise

    def record_error(self, error: str) -> bool:
        """
        Record an error and check if max errors exceeded

        Args:
            error: Error message to record

        Returns:
            bool: True if max errors exceeded
        """
        try:
            logger.info(f"记录错误: {error}")
            self.error_count += 1
            self.last_error = error
            logger.info(f"当前错误计数: {self.error_count}/{self.max_errors}")

            if self.error_count >= self.max_errors:
                logger.warning(
                    f"达到最大错误次数 ({self.max_errors})，转换到 FAILED 状态"
                )
                self.transition_to(FlowState.FAILED)
                return True

            return False
        except Exception as e:
            log_exception(logger, "记录错误失败", e)
            # 不抛出异常，继续执行
            return False

    def reset_errors(self) -> None:
        """Reset error count and last error"""
        self.error_count = 0
        self.last_error = None

    def update_data(self, key: str, value: Any) -> None:
        """Update state data"""
        self.state_data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        """Get state data"""
        return self.state_data.get(key, default)

    def clear_data(self) -> None:
        """Clear all state data"""
        self.state_data.clear()

    def is_terminal(self) -> bool:
        """Check if current state is terminal"""
        return FlowState.is_terminal(self.current_state)

    def can_proceed(self) -> bool:
        """Check if flow can proceed"""
        return self.current_state in [
            FlowState.INITIALIZED,
            FlowState.READY,
            FlowState.RUNNING,
            FlowState.PAUSED,
        ]
