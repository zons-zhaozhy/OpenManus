import asyncio
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict

from app.tool.base import BaseTool


class PythonExecute(BaseTool):
    """A tool for executing Python code with timeout and safety restrictions."""

    name: str = "python_execute"
    description: str = (
        "Executes Python code string. Note: Only print outputs are visible, function return values are not captured. Use print statements to see results."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The Python code to execute.",
            },
        },
        "required": ["code"],
    }

    async def execute(
        self,
        code: str,
        timeout: int = 5,
    ) -> Dict:
        """
        Executes the provided Python code with a timeout using asyncio subprocess.

        Args:
            code (str): The Python code to execute.
            timeout (int): Execution timeout in seconds.

        Returns:
            Dict: Contains 'observation' with execution output or error message and 'success' status.
        """

        # 创建临时文件来执行代码，避免multiprocessing问题
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            # 写入安全的代码包装器
            safe_code = f"""
import sys
import signal
import time

def timeout_handler(signum, frame):
    raise TimeoutError("Execution timeout")

# 设置信号处理器（仅在Unix系统上）
try:
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm({timeout})
except AttributeError:
    # Windows系统不支持SIGALRM
    pass

try:
    # 用户代码开始
{chr(10).join(['    ' + line for line in code.split(chr(10))])}
    # 用户代码结束
except Exception as e:
    print(f"Error: {{e}}", file=sys.stderr)
    sys.exit(1)
finally:
    try:
        signal.alarm(0)  # 取消alarm
    except AttributeError:
        pass
"""
            f.write(safe_code)
            temp_file_path = f.name

        try:
            # 使用asyncio subprocess执行，避免multiprocessing的资源问题
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                temp_file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024 * 1024,  # 1MB输出限制
            )

            try:
                # 等待进程完成，带超时
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout + 1,  # 比代码超时多1秒的宽限时间
                )

                # 获取输出
                stdout_text = stdout.decode("utf-8") if stdout else ""
                stderr_text = stderr.decode("utf-8") if stderr else ""

                # 合并输出
                output = stdout_text
                if stderr_text:
                    output += f"\nErrors:\n{stderr_text}"

                success = process.returncode == 0

                return {
                    "observation": output.strip() if output else "No output",
                    "success": success,
                }

            except asyncio.TimeoutError:
                # 超时处理
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    # 强制杀死进程
                    process.kill()
                    await process.wait()

                return {
                    "observation": f"Execution timeout after {timeout} seconds",
                    "success": False,
                }

        except Exception as e:
            return {
                "observation": f"Execution error: {str(e)}",
                "success": False,
            }
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass  # 文件可能已被删除
