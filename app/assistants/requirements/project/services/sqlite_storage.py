"""
SQLite存储实现
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from ..interfaces.storage import IProjectStorage, IRequirementStorage
from ..models.base import Project, Requirement
from ..utils.exceptions import StorageError


class SQLiteStorage(IProjectStorage, IRequirementStorage):
    """SQLite存储实现"""

    def __init__(self, db_path: Union[str, Path], table_prefix: str = "pm_"):
        """初始化SQLite存储

        Args:
            db_path: 数据库文件路径
            table_prefix: 表名前缀
        """
        self.db_path = Path(db_path)
        self.table_prefix = table_prefix
        self._ensure_tables()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            raise StorageError(f"Failed to connect to database: {e}")

    def _ensure_tables(self):
        """确保数据库表存在"""
        conn = self._get_connection()
        try:
            # 项目表
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.table_prefix}projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT
                )
            """
            )

            # 需求表
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.table_prefix}requirements (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    priority TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT,
                    dependencies TEXT,
                    FOREIGN KEY (project_id) REFERENCES {self.table_prefix}projects (id)
                        ON DELETE CASCADE
                )
            """
            )

            conn.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Failed to create tables: {e}")
        finally:
            conn.close()

    async def create_project(self, project: Project) -> Project:
        """创建项目"""
        conn = self._get_connection()
        try:
            conn.execute(
                f"""
                INSERT INTO {self.table_prefix}projects
                (id, name, description, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    project.id,
                    project.name,
                    project.description,
                    project.created_at.isoformat(),
                    project.updated_at.isoformat(),
                    json.dumps(project.metadata) if project.metadata else None,
                ),
            )
            conn.commit()
            return project
        except sqlite3.Error as e:
            raise StorageError(f"Failed to create project: {e}")
        finally:
            conn.close()

    async def update_project(self, project: Project) -> Project:
        """更新项目"""
        conn = self._get_connection()
        try:
            conn.execute(
                f"""
                UPDATE {self.table_prefix}projects
                SET name = ?, description = ?, updated_at = ?, metadata = ?
                WHERE id = ?
                """,
                (
                    project.name,
                    project.description,
                    project.updated_at.isoformat(),
                    json.dumps(project.metadata) if project.metadata else None,
                    project.id,
                ),
            )
            conn.commit()
            return project
        except sqlite3.Error as e:
            raise StorageError(f"Failed to update project: {e}")
        finally:
            conn.close()

    async def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                f"DELETE FROM {self.table_prefix}projects WHERE id = ?", (project_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise StorageError(f"Failed to delete project: {e}")
        finally:
            conn.close()

    async def get_project(self, project_id: str) -> Optional[Project]:
        """获取项目"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                f"SELECT * FROM {self.table_prefix}projects WHERE id = ?", (project_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Project(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            )
        except sqlite3.Error as e:
            raise StorageError(f"Failed to get project: {e}")
        finally:
            conn.close()

    async def list_projects(self) -> List[Project]:
        """获取所有项目"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(f"SELECT * FROM {self.table_prefix}projects")
            return [
                Project(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                )
                for row in cursor.fetchall()
            ]
        except sqlite3.Error as e:
            raise StorageError(f"Failed to list projects: {e}")
        finally:
            conn.close()

    async def create_requirement(self, requirement: Requirement) -> Requirement:
        """创建需求"""
        conn = self._get_connection()
        try:
            conn.execute(
                f"""
                INSERT INTO {self.table_prefix}requirements
                (id, project_id, title, description, status, priority,
                created_at, updated_at, metadata, dependencies)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    requirement.id,
                    requirement.project_id,
                    requirement.title,
                    requirement.description,
                    requirement.status,
                    requirement.priority,
                    requirement.created_at.isoformat(),
                    requirement.updated_at.isoformat(),
                    json.dumps(requirement.metadata) if requirement.metadata else None,
                    (
                        json.dumps(requirement.dependencies)
                        if requirement.dependencies
                        else None
                    ),
                ),
            )
            conn.commit()
            return requirement
        except sqlite3.Error as e:
            raise StorageError(f"Failed to create requirement: {e}")
        finally:
            conn.close()

    async def update_requirement(self, requirement: Requirement) -> Requirement:
        """更新需求"""
        conn = self._get_connection()
        try:
            conn.execute(
                f"""
                UPDATE {self.table_prefix}requirements
                SET title = ?, description = ?, status = ?, priority = ?,
                    updated_at = ?, metadata = ?, dependencies = ?
                WHERE id = ?
                """,
                (
                    requirement.title,
                    requirement.description,
                    requirement.status,
                    requirement.priority,
                    requirement.updated_at.isoformat(),
                    json.dumps(requirement.metadata) if requirement.metadata else None,
                    (
                        json.dumps(requirement.dependencies)
                        if requirement.dependencies
                        else None
                    ),
                    requirement.id,
                ),
            )
            conn.commit()
            return requirement
        except sqlite3.Error as e:
            raise StorageError(f"Failed to update requirement: {e}")
        finally:
            conn.close()

    async def delete_requirement(self, requirement_id: str) -> bool:
        """删除需求"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                f"DELETE FROM {self.table_prefix}requirements WHERE id = ?",
                (requirement_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise StorageError(f"Failed to delete requirement: {e}")
        finally:
            conn.close()

    async def get_requirement(self, requirement_id: str) -> Optional[Requirement]:
        """获取需求"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                f"SELECT * FROM {self.table_prefix}requirements WHERE id = ?",
                (requirement_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Requirement(
                id=row["id"],
                project_id=row["project_id"],
                title=row["title"],
                description=row["description"],
                status=row["status"],
                priority=row["priority"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                dependencies=(
                    json.loads(row["dependencies"]) if row["dependencies"] else None
                ),
            )
        except sqlite3.Error as e:
            raise StorageError(f"Failed to get requirement: {e}")
        finally:
            conn.close()

    async def list_requirements(self, project_id: str) -> List[Requirement]:
        """获取项目下的所有需求"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                f"SELECT * FROM {self.table_prefix}requirements WHERE project_id = ?",
                (project_id,),
            )
            return [
                Requirement(
                    id=row["id"],
                    project_id=row["project_id"],
                    title=row["title"],
                    description=row["description"],
                    status=row["status"],
                    priority=row["priority"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                    dependencies=(
                        json.loads(row["dependencies"]) if row["dependencies"] else None
                    ),
                )
                for row in cursor.fetchall()
            ]
        except sqlite3.Error as e:
            raise StorageError(f"Failed to list requirements: {e}")
        finally:
            conn.close()

    async def get_requirements_by_status(
        self, project_id: str, status: str
    ) -> List[Requirement]:
        """获取项目下指定状态的需求"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                f"""
                SELECT * FROM {self.table_prefix}requirements
                WHERE project_id = ? AND status = ?
                """,
                (project_id, status),
            )
            return [
                Requirement(
                    id=row["id"],
                    project_id=row["project_id"],
                    title=row["title"],
                    description=row["description"],
                    status=row["status"],
                    priority=row["priority"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                    dependencies=(
                        json.loads(row["dependencies"]) if row["dependencies"] else None
                    ),
                )
                for row in cursor.fetchall()
            ]
        except sqlite3.Error as e:
            raise StorageError(f"Failed to get requirements by status: {e}")
        finally:
            conn.close()
