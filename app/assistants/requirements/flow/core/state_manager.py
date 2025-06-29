"""
状态管理器模块
"""

from typing import Any, Dict, Optional

from app.logger import logger


class StateManager:
    """状态管理器"""

    def __init__(self) -> None:
        """初始化状态管理器"""
        self.current_state = "INITIALIZED"
        self.previous_state = None
        self.data: Dict[str, Any] = {}
        self.last_error: Optional[str] = None
        self.state_history = []
        self._record_state_change("INITIALIZED", None)

    def set_state(self, state: str, error: Optional[str] = None) -> None:
        """
        设置状态

        Args:
            state: 新状态
            error: 错误信息（如果有）
        """
        logger.info(f"状态变更: {self.current_state} -> {state}")
        
        # 特殊处理READY状态
        if state == "READY" and self.current_state == "INITIALIZED":
            logger.info("从INITIALIZED转换到READY状态")
        elif state == "READY" and self.current_state != "INITIALIZED":
            logger.warning(f"尝试将状态从 {self.current_state} 设置为 READY，这可能不是预期行为")
        
        self.previous_state = self.current_state
        self.current_state = state
        
        if error:
            self.last_error = error
            logger.error(f"状态错误: {error}")
        
        self._record_state_change(state, error)

    def _record_state_change(self, state: str, error: Optional[str]) -> None:
        """
        记录状态变更

        Args:
            state: 状态
            error: 错误信息（如果有）
        """
        self.state_history.append({
            "state": state,
            "error": error,
            "data": self.data.copy()
        })

    def update_data(self, key: str, value: Any) -> None:
        """
        更新状态数据

        Args:
            key: 数据键
            value: 数据值
        """
        self.data[key] = value
        logger.debug(f"状态数据更新: {key}")

    def get_data(self, key: str, default: Any = None) -> Any:
        """
        获取状态数据

        Args:
            key: 数据键
            default: 默认值

        Returns:
            Any: 数据值
        """
        return self.data.get(key, default)

    def get_state_history(self) -> list:
        """
        获取状态历史

        Returns:
            list: 状态历史记录
        """
        return self.state_history.copy()

    def reset(self) -> None:
        """重置状态管理器"""
        self.current_state = "INITIALIZED"
        self.previous_state = None
        self.data = {}
        self.last_error = None
        self.state_history = []
        self._record_state_change("INITIALIZED", None)
        logger.info("状态管理器已重置")

    def can_transition(self, from_state: str, to_state: str) -> bool:
        """
        检查状态转换是否有效

        Args:
            from_state: 起始状态
            to_state: 目标状态

        Returns:
            bool: 是否可以转换
        """
        valid_transitions = {
            "INITIALIZED": ["READY"],
            "READY": ["PROCESSING"],
            "PROCESSING": ["COMPLETED", "ERROR", "PAUSED"],
            "PAUSED": ["PROCESSING", "ERROR"],
            "ERROR": ["READY", "PROCESSING"],
            "COMPLETED": ["READY"]
        }
        
        return to_state in valid_transitions.get(from_state, [])
