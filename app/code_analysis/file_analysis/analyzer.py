"""
代码文件分析器
"""

import ast
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.logger import logger


class FileAnalyzer:
    """文件分析器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()

    def get_project_overview(self) -> Dict[str, Any]:
        """获取项目概览"""
        overview = {
            "project_root": self.project_root,
            "total_files": 0,
            "code_files": 0,
            "languages": {},
            "file_structure": {},
        }

        # 只分析项目目录，不遍历整个系统
        project_dirs_to_scan = ["app", "src", "lib", "tests"]

        for project_dir in project_dirs_to_scan:
            dir_path = os.path.join(self.project_root, project_dir)
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    # 跳过常见的隐藏目录和缓存目录
                    dirs[:] = [
                        d
                        for d in dirs
                        if not d.startswith(".")
                        and d not in ["__pycache__", "node_modules", ".git"]
                    ]

                    for file in files:
                        if not file.startswith("."):
                            overview["total_files"] += 1

                            # 分析文件类型
                            ext = Path(file).suffix.lower()
                            if ext in [
                                ".py",
                                ".js",
                                ".ts",
                                ".java",
                                ".cpp",
                                ".c",
                                ".html",
                                ".css",
                            ]:
                                overview["code_files"] += 1
                                overview["languages"][ext] = (
                                    overview["languages"].get(ext, 0) + 1
                                )

        return overview

    def analyze_directory(self, dir_path: str) -> List[str]:
        """分析目录"""
        python_files = []
        for root, dirs, files in os.walk(dir_path):
            # 跳过隐藏目录和缓存目录
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".") and d not in ["__pycache__", "node_modules"]
            ]

            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    if self._is_project_file(file_path):
                        python_files.append(file_path)

        return python_files

    def read_python_file(self, file_path: str) -> Optional[ast.AST]:
        """读取并解析Python文件"""
        try:
            content = self._read_file_safely(file_path)
            if content is not None:
                return ast.parse(content)
        except Exception as e:
            logger.error(f"解析Python文件失败 {file_path}: {str(e)}")
        return None

    def _is_project_file(self, file_path: str) -> bool:
        """检查是否为项目文件"""
        # 跳过系统文件和非项目文件
        if any(
            part.startswith(".")
            or part in ["__pycache__", "node_modules", "venv", "env", "site-packages"]
            for part in file_path.split(os.sep)
        ):
            return False
        return True

    def _read_file_safely(self, file_path: str) -> Optional[str]:
        """安全地读取文件内容"""
        encodings = ["utf-8", "latin1", "cp1252"]
        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"读取文件失败 {file_path}: {str(e)}")
                break
        return None
