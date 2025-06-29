import asyncio
import json
import os
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import aiohttp
from loguru import logger

from app.config import Config
from app.schema import Message

config = Config()


class LLM:
    """LLM client implementation"""

    def __init__(self, config_name: str = "default"):
        """Initialize LLM client"""
        self.config = config.get_llm_config(config_name)
        self.api_base = self.config.get("api_base")
        self.api_key = self.config.get("api_key")
        self.model = self.config.get("model")
        self.max_tokens = self.config.get("max_tokens", 2000)
        self.temperature = self.config.get("temperature", 0.7)
        self.timeout = self.config.get("timeout", 120)  # 默认超时时间为120秒

    async def ask(
        self,
        messages: List[Message],
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Send request to LLM"""
        try:
            # 构建请求
            data = {
                "model": self.model,
                "messages": [msg.dict() for msg in messages],
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
                "stream": stream,
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_base,
                    headers=headers,
                    json=data,
                    timeout=kwargs.get("timeout", self.timeout),  # 使用配置的超时时间
                ) as response:
                    if stream:
                        return self._handle_stream_response(response)
                    else:
                        return await self._handle_normal_response(response)

        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise

    async def _handle_normal_response(self, response: aiohttp.ClientResponse) -> str:
        """Handle normal response"""
        if response.status != 200:
            error_text = await response.text()
            raise Exception(
                f"LLM request failed with status {response.status}: {error_text}"
            )

        result = await response.json()
        return result["choices"][0]["message"]["content"]

    async def _handle_stream_response(
        self, response: aiohttp.ClientResponse
    ) -> AsyncGenerator[str, None]:
        """Handle stream response"""
        if response.status != 200:
            error_text = await response.text()
            raise Exception(
                f"LLM request failed with status {response.status}: {error_text}"
            )

        async for line in response.content:
            if line:
                try:
                    json_line = json.loads(line.decode("utf-8").strip())
                    if "choices" in json_line and json_line["choices"]:
                        content = (
                            json_line["choices"][0].get("delta", {}).get("content")
                        )
                        if content:
                            yield content
                except json.JSONDecodeError:
                    continue

    async def analyze_requirements(self, content: str) -> Dict[str, Any]:
        """分析需求"""
        try:
            messages = [
                Message.system_message("你是一个专业的需求分析专家。"),
                Message.user_message(f"请分析以下需求：\n{content}"),
            ]
            analysis = await self.ask(messages=messages)
            return {
                "clarified_content": content,
                "analysis": analysis,
            }
        except Exception as e:
            logger.error(f"需求分析失败: {e}")
            raise

    async def analyze_requirements_deeply(self, content: str) -> Dict[str, Any]:
        """深入分析需求"""
        try:
            messages = [
                Message.system_message("你是一个专业的需求分析专家。"),
                Message.user_message(f"请深入分析以下需求：\n{content}"),
            ]
            analysis = await self.ask(messages=messages)
            return {
                "detailed_analysis": analysis,
            }
        except Exception as e:
            logger.error(f"深入需求分析失败: {e}")
            raise
