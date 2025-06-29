"""
Mixins for OpenManus flows
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.logger import logger
from app.schema import ProjectContext


class ErrorSeverity(str, Enum):
    """错误严重程度"""

    LOW = "low"  # 轻微错误，可以继续执行
    MEDIUM = "medium"  # 中等错误，需要注意但可以继续
    HIGH = "high"  # 严重错误，需要处理
    CRITICAL = "critical"  # 致命错误，必须立即停止


class BaseMixin(BaseModel):
    """所有Mixin的基类"""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")


class ErrorHandlingMixin(BaseMixin):
    """错误处理Mixin - 提供增强的错误处理能力"""

    error_history: List[Dict[str, Any]] = Field(default_factory=list)
    max_retries: int = Field(default=3)
    current_retry: int = Field(default=0)
    retry_delay: float = Field(default=1.0)  # 重试延迟（秒）
    non_retryable_errors: List[Type[Exception]] = Field(
        default_factory=lambda: [
            NotImplementedError,  # 未实现的功能
            PermissionError,  # 权限错误
            KeyboardInterrupt,  # 用户中断
            SystemExit,  # 系统退出
            MemoryError,  # 内存错误
        ]
    )

    def record_error(
        self,
        error: Exception,
        stage: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict] = None,
    ) -> None:
        """记录错误信息"""
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stage": stage,
            "severity": severity,
            "context": context or {},
            "retry_count": self.current_retry,
            "stack_trace": getattr(error, "__traceback__", None),
        }

        self.error_history.append(error_info)
        self._update_state_manager(error_info)
        self._log_error(error_info)

    def can_retry(self, error: Exception) -> bool:
        """判断是否可以重试"""
        # 检查重试次数
        if self.current_retry >= self.max_retries:
            logger.warning(f"已达到最大重试次数 ({self.max_retries})")
            return False

        # 检查错误类型是否可重试
        if any(isinstance(error, e) for e in self.non_retryable_errors):
            logger.warning(f"错误类型 {type(error).__name__} 不可重试")
            return False

        # 检查错误严重程度
        if hasattr(error, "severity") and error.severity == ErrorSeverity.CRITICAL:
            logger.error("致命错误不可重试")
            return False

        return True

    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        if not self.error_history:
            return {"status": "healthy", "error_count": 0}

        latest_error = self.error_history[-1]
        severity_counts = {
            severity: len([e for e in self.error_history if e["severity"] == severity])
            for severity in ErrorSeverity
        }

        return {
            "status": "error",
            "error_count": len(self.error_history),
            "latest_error": latest_error,
            "error_types": list(set(e["error_type"] for e in self.error_history)),
            "severity_counts": severity_counts,
            "retry_attempts": self.current_retry,
            "can_retry": self.can_retry(
                Exception(latest_error["error_message"])
            ),  # 简单判断
        }

    def reset_error_state(self) -> None:
        """重置错误状态"""
        self.error_history.clear()
        self.current_retry = 0
        if hasattr(self, "state_manager"):
            self.state_manager.reset_errors()

    def _update_state_manager(self, error_info: Dict[str, Any]) -> None:
        """更新状态管理器"""
        if hasattr(self, "state_manager"):
            self.state_manager.record_error(error_info["error_message"])

            # 根据严重程度决定是否转换到失败状态
            if error_info["severity"] in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                self.state_manager.transition_to("failed")

    def _log_error(self, error_info: Dict[str, Any]) -> None:
        """记录错误日志"""
        log_message = (
            f"错误发生 [{error_info['severity']}] - {error_info['stage']}: "
            f"{error_info['error_message']} (重试次数: {error_info['retry_count']})"
        )

        if error_info["severity"] in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logger.error(log_message, extra={"error_info": error_info})
        else:
            logger.warning(log_message, extra={"error_info": error_info})

    async def handle_error_with_retry(
        self,
        error: Exception,
        stage: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict] = None,
    ) -> bool:
        """处理错误并尝试重试

        Returns:
            bool: 是否应该继续重试
        """
        self.record_error(error, stage, severity, context)

        if not self.can_retry(error):
            return False

        self.current_retry += 1
        return True


class ProjectManagementMixin(BaseMixin):
    """项目管理Mixin - 为Flow提供项目制管理能力"""

    project_id: Optional[str] = Field(default=None, description="项目ID")
    project_context: Optional[Dict] = Field(default=None, description="项目上下文")

    def _load_project_context(self) -> None:
        """加载项目上下文（项目制管理支持）"""
        try:
            # 这里应该从项目管理API获取项目上下文
            # 简化实现，实际应该调用项目管理服务
            if not self.project_id:
                logger.warning("未指定项目ID，跳过加载项目上下文")
                return

            # 模拟项目上下文获取
            self.project_context = {
                "project_id": self.project_id,
                "objective_guidance": "基于项目目标进行需求分析",
                "background_context": "项目背景上下文",
                "success_criteria": ["明确的需求规格", "可实施的技术方案"],
                "constraints": ["时间约束", "资源约束"],
                "current_stage": "requirements_analysis",
                "available_knowledge_bases": [],
                "codebase_info": None,
            }

            # 如果有上下文管理器，更新全局状态
            if hasattr(self, "context_manager"):
                self.context_manager.update_global_state(
                    "project_context", self.project_context
                )

            logger.info(f"加载项目上下文成功: {self.project_id}")

        except Exception as e:
            logger.warning(f"加载项目上下文失败: {e}")
            self.project_context = None

    def _build_project_guidance_prompt(self) -> str:
        """构建项目指引提示词"""
        if not self.project_context:
            return ""

        guidance_prompt = f"""
## 项目上下文指引

**项目目标：** {self.project_context.get('objective_guidance', '未指定')}

**项目背景：** {self.project_context.get('background_context', '未指定')}

**成功标准：**
{chr(10).join([f"- {criteria}" for criteria in self.project_context.get('success_criteria', [])])}

**约束条件：**
{chr(10).join([f"- {constraint}" for constraint in self.project_context.get('constraints', [])])}

**当前阶段：** {self.project_context.get('current_stage', '未指定')}

---
⚠️ **重要提醒：** 所有工作都必须紧密围绕上述项目目标和背景展开，确保不偏离项目整体方向！
---
"""
        return guidance_prompt
