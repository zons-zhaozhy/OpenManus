"""
全局工具函数模块

提供全局共享的工具函数和常量
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from app.logger import logger

# 活跃会话存储
active_sessions: Dict = {}


def format_timestamp(timestamp: Union[float, datetime]) -> str:
    """格式化时间戳"""
    if isinstance(timestamp, datetime):
        dt = timestamp
    else:
        dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def load_json_file(file_path: str) -> Dict:
    """加载JSON文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载JSON文件失败: {str(e)}")
        return {}


def save_json_file(file_path: str, data: Dict) -> bool:
    """保存JSON文件"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存JSON文件失败: {str(e)}")
        return False


def get_file_size(file_path: str) -> int:
    """获取文件大小（字节）"""
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"获取文件大小失败: {str(e)}")
        return 0


def get_file_lines(file_path: str) -> int:
    """获取文件行数"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except Exception as e:
        logger.error(f"获取文件行数失败: {str(e)}")
        return 0


def ensure_directory(directory: str) -> bool:
    """确保目录存在"""
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"创建目录失败: {str(e)}")
        return False


def remove_file(file_path: str) -> bool:
    """删除文件"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        return False


def get_file_modification_time(file_path: str) -> Optional[datetime]:
    """获取文件修改时间"""
    try:
        return datetime.fromtimestamp(os.path.getmtime(file_path))
    except Exception as e:
        logger.error(f"获取文件修改时间失败: {str(e)}")
        return None


async def run_with_timeout(coro: Any, timeout: float) -> Any:
    """运行协程，带超时控制"""
    try:
        return await asyncio.wait_for(coro, timeout)
    except asyncio.TimeoutError:
        logger.warning(f"操作超时 (timeout={timeout}s)")
        raise


def measure_execution_time(func: Any) -> Any:
    """测量函数执行时间的装饰器"""

    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"函数 {func.__name__} 执行完成，耗时: {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"函数 {func.__name__} 执行失败，耗时: {execution_time:.2f}s, 错误: {str(e)}"
            )
            raise

    return wrapper
