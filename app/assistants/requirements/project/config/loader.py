"""
配置加载器
支持从多种来源加载配置：YAML文件、环境变量、命令行参数等
"""

import os
from pathlib import Path
from typing import Optional, Union

import yaml
from pydantic import ValidationError

from .settings import ProjectConfig, default_config


class ConfigLoader:
    """配置加载器"""

    @staticmethod
    def load_from_yaml(file_path: Union[str, Path]) -> ProjectConfig:
        """从YAML文件加载配置"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_dict = yaml.safe_load(f)
            return ProjectConfig(**config_dict)
        except FileNotFoundError:
            raise ValueError(f"配置文件不存在: {file_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"YAML格式错误: {e}")
        except ValidationError as e:
            raise ValueError(f"配置验证失败: {e}")

    @staticmethod
    def load_from_env(prefix: str = "PM_") -> ProjectConfig:
        """从环境变量加载配置"""
        config_dict = {}

        # 存储配置
        if os.getenv(f"{prefix}STORAGE_TYPE"):
            config_dict["storage"] = {
                "type": os.getenv(f"{prefix}STORAGE_TYPE"),
                "connection_string": os.getenv(f"{prefix}STORAGE_CONNECTION_STRING"),
                "table_prefix": os.getenv(f"{prefix}STORAGE_TABLE_PREFIX", "pm_"),
            }

        # 事件配置
        if os.getenv(f"{prefix}EVENTS_ENABLED"):
            config_dict["events"] = {
                "enabled": os.getenv(f"{prefix}EVENTS_ENABLED").lower() == "true",
                "async_processing": os.getenv(f"{prefix}EVENTS_ASYNC", "false").lower()
                == "true",
                "retry_count": int(os.getenv(f"{prefix}EVENTS_RETRY_COUNT", "3")),
            }

        try:
            return ProjectConfig(**config_dict)
        except ValidationError as e:
            raise ValueError(f"环境变量配置验证失败: {e}")

    @classmethod
    def load(
        cls, config_file: Optional[Union[str, Path]] = None, env_prefix: str = "PM_"
    ) -> ProjectConfig:
        """加载配置

        优先级：配置文件 > 环境变量 > 默认配置
        """
        config = default_config.copy()

        # 从环境变量加载
        try:
            env_config = cls.load_from_env(env_prefix)
            config = ProjectConfig(
                **{**config.dict(), **env_config.dict(exclude_unset=True)}
            )
        except ValueError as e:
            print(f"警告：从环境变量加载配置失败: {e}")

        # 从配置文件加载
        if config_file:
            try:
                file_config = cls.load_from_yaml(config_file)
                config = ProjectConfig(
                    **{**config.dict(), **file_config.dict(exclude_unset=True)}
                )
            except ValueError as e:
                print(f"警告：从配置文件加载配置失败: {e}")

        return config
