"""
存储工厂类
"""

from pathlib import Path
from typing import Optional, Union

from ..config.settings import StorageConfig
from ..interfaces.storage import IProjectStorage, IRequirementStorage
from .memory_storage import MemoryStorage
from .sqlite_storage import SQLiteStorage


class StorageFactory:
    """存储工厂类"""

    @staticmethod
    def create_storage(
        config: StorageConfig, db_path: Optional[Union[str, Path]] = None
    ) -> Union[IProjectStorage, IRequirementStorage]:
        """创建存储实例

        Args:
            config: 存储配置
            db_path: 数据库文件路径（仅用于SQLite）

        Returns:
            存储实例

        Raises:
            ValueError: 不支持的存储类型
        """
        if config.type == "memory":
            return MemoryStorage()
        elif config.type == "sqlite":
            if not db_path and not config.connection_string:
                raise ValueError("SQLite storage requires db_path or connection_string")
            return SQLiteStorage(
                db_path=db_path or config.connection_string,
                table_prefix=config.table_prefix,
            )
        else:
            raise ValueError(f"Unsupported storage type: {config.type}")

    @classmethod
    def create_from_config(
        cls, config: StorageConfig
    ) -> Union[IProjectStorage, IRequirementStorage]:
        """从配置创建存储实例"""
        return cls.create_storage(config)
