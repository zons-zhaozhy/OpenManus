"""
协调中心 - 多智能体联盟全局协调器

负责：
1. 全局任务调度和分配
2. 助手间通信协调
3. 资源调度和冲突解决
4. 系统状态监控
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from .multi_agent_alliance import AssistantRole, WorkItem


@dataclass
class TaskStatus:
    """任务状态"""

    task_id: str
    assistant: AssistantRole
    status: str  # pending, running, completed, failed
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict] = None
    error: Optional[str] = None


class CoordinationHub:
    """协调中心"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_tasks: Dict[str, TaskStatus] = {}
        self.task_queue: List[WorkItem] = []
        self.assistant_status: Dict[AssistantRole, str] = {}

    async def coordinate_workflow(self, work_items: List[WorkItem]) -> Dict:
        """协调整个工作流程"""
        self.logger.info(f"开始协调工作流程，共 {len(work_items)} 个工作项")

        try:
            # 初始化任务队列
            self.task_queue = work_items.copy()
            results = {}

            # 按依赖关系执行任务
            while self.task_queue:
                # 找到可以执行的任务（依赖已完成）
                ready_tasks = self._get_ready_tasks(results)

                if not ready_tasks:
                    self.logger.error("检测到循环依赖或无法满足的依赖")
                    break

                # 并行执行就绪的任务
                batch_results = await self._execute_task_batch(ready_tasks)
                results.update(batch_results)

                # 从队列中移除已完成的任务
                for task in ready_tasks:
                    self.task_queue.remove(task)

            return {
                "status": "success",
                "results": results,
                "completed_tasks": len(results),
                "total_tasks": len(work_items),
            }

        except Exception as e:
            self.logger.error(f"工作流程协调失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "completed_tasks": len(results) if "results" in locals() else 0,
            }

    def _get_ready_tasks(self, completed_results: Dict) -> List[WorkItem]:
        """获取可以执行的任务"""
        ready_tasks = []

        for task in self.task_queue:
            # 检查依赖是否都已完成
            dependencies_met = all(
                dep in completed_results for dep in task.dependencies
            )

            if dependencies_met:
                ready_tasks.append(task)

        return ready_tasks

    async def _execute_task_batch(self, tasks: List[WorkItem]) -> Dict:
        """并行执行一批任务"""
        batch_results = {}

        # 创建协程任务
        coroutines = []
        for task in tasks:
            coroutine = self._execute_single_task(task)
            coroutines.append(coroutine)

        # 并行执行
        results = await asyncio.gather(*coroutines, return_exceptions=True)

        # 处理结果
        for task, result in zip(tasks, results):
            if isinstance(result, Exception):
                self.logger.error(f"任务 {task.name} 执行失败: {result}")
                batch_results[task.name] = {"status": "error", "error": str(result)}
            else:
                batch_results[task.name] = result

        return batch_results

    async def _execute_single_task(self, task: WorkItem) -> Dict:
        """执行单个任务"""
        task_id = (
            f"{task.from_assistant.value}_{task.name}_{datetime.now().timestamp()}"
        )

        # 创建任务状态
        status = TaskStatus(
            task_id=task_id,
            assistant=task.from_assistant,
            status="running",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.active_tasks[task_id] = status

        try:
            self.logger.info(
                f"执行任务: {task.name} (助手: {task.from_assistant.value})"
            )

            # 模拟任务执行
            await asyncio.sleep(0.1)  # 模拟处理时间

            result = {
                "task_name": task.name,
                "assistant": task.from_assistant.value,
                "status": "completed",
                "output": f"Task {task.name} completed successfully",
                "timestamp": datetime.now().isoformat(),
            }

            # 更新任务状态
            status.status = "completed"
            status.updated_at = datetime.now()
            status.result = result

            return result

        except Exception as e:
            # 更新任务状态为失败
            status.status = "failed"
            status.updated_at = datetime.now()
            status.error = str(e)

            raise e

    def get_system_status(self) -> Dict:
        """获取系统状态"""
        return {
            "active_tasks": len(self.active_tasks),
            "queued_tasks": len(self.task_queue),
            "assistant_status": {
                assistant.value: status
                for assistant, status in self.assistant_status.items()
            },
            "timestamp": datetime.now().isoformat(),
        }

    def cleanup_completed_tasks(self):
        """清理已完成的任务"""
        completed_tasks = [
            task_id
            for task_id, task in self.active_tasks.items()
            if task.status in ["completed", "failed"]
        ]

        for task_id in completed_tasks:
            del self.active_tasks[task_id]

        self.logger.info(f"清理了 {len(completed_tasks)} 个已完成的任务")
