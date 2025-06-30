"""
ID生成器工具类
"""

import uuid
from datetime import datetime


class IDGenerator:
    """ID生成器"""

    @staticmethod
    def generate_project_id() -> str:
        """
        生成项目ID

        Returns:
            str: 项目ID，格式：PRJ-{uuid4的前8位}-{时间戳后6位}
        """
        uuid_part = str(uuid.uuid4())[:8]
        timestamp_part = str(int(datetime.now().timestamp()))[-6:]
        return f"PRJ-{uuid_part}-{timestamp_part}"

    @staticmethod
    def generate_requirement_id(project_id: str, sequence: int) -> str:
        """
        生成需求ID

        Args:
            project_id: 项目ID
            sequence: 序号

        Returns:
            str: 需求ID，格式：REQ-{项目ID最后6位}-{序号补零到4位}
        """
        project_part = project_id[-6:]
        sequence_part = str(sequence).zfill(4)
        return f"REQ-{project_part}-{sequence_part}"

    @staticmethod
    def generate_member_id() -> str:
        """
        生成成员ID

        Returns:
            str: 成员ID，格式：MBR-{uuid4的前12位}
        """
        uuid_part = str(uuid.uuid4())[:12]
        return f"MBR-{uuid_part}"

    @staticmethod
    def generate_session_id() -> str:
        """
        生成会话ID

        Returns:
            str: 会话ID，格式：SES-{uuid4的前8位}-{时间戳后6位}
        """
        uuid_part = str(uuid.uuid4())[:8]
        timestamp_part = str(int(datetime.now().timestamp()))[-6:]
        return f"SES-{uuid_part}-{timestamp_part}"
