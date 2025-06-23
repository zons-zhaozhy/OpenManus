"""
配置管理器 - 支持动态配置加载和更新
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import toml


class ConfigManager:
    """动态配置管理器"""

    def __init__(self, config_path: str = "config/config.toml"):
        self.config_path = Path(config_path)
        self._config = None
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        if self.config_path.exists():
            self._config = toml.load(self.config_path)
        else:
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

    def reload(self):
        """重新加载配置"""
        self._load_config()

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值，支持点分割路径
        例如: get("llm.performance.timeout_seconds")
        """
        keys = key_path.split(".")
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM基础配置"""
        return self.get("llm", {})

    def get_llm_performance_config(self) -> Dict[str, Any]:
        """获取LLM性能配置"""
        return self.get("llm.performance", {})

    def get_requirements_analysis_config(self) -> Dict[str, Any]:
        """获取需求分析配置"""
        return self.get("requirements_analysis", {})

    def is_llm_analysis_enabled(self) -> bool:
        """是否启用LLM分析"""
        return self.get("requirements_analysis.enable_llm_analysis", True)

    def is_llm_priority(self) -> bool:
        """LLM是否优先"""
        return self.get("requirements_analysis.llm_priority", True)

    def get_llm_timeout(self) -> float:
        """获取LLM超时时间"""
        return self.get("llm.performance.timeout_seconds", 25.0)

    def get_llm_max_retries(self) -> int:
        """获取LLM最大重试次数"""
        return self.get("llm.performance.max_retries", 2)

    def get_analysis_temperature(self) -> float:
        """获取分析专用温度"""
        return self.get("requirements_analysis.temperature", 0.3)

    def is_fallback_enabled(self) -> bool:
        """降级模式已被彻底禁用"""
        return False


# 全局配置管理器实例
config_manager = ConfigManager()
