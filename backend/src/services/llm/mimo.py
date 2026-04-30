import json
import logging
from collections.abc import AsyncIterator

import httpx

from src.core.config import settings
from src.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class ContentFilteredError(Exception):
    """MiMo API 内容过滤触发"""
    pass


class MiMoProvider(LLMProvider):
    """MiMo API 集成"""

    def __init__(self) -> None:
        self.base_url = settings.MIMO_API_BASE_URL
        self.api_key = settings.MIMO_API_KEY
        self._client = httpx.AsyncClient(timeout=60.0)

    async def generate(self, messages: list[dict], *, temperature: float = 0.7) -> str:
        response = await self._client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": settings.MIMO_MODEL,
                "messages": messages,
                "temperature": temperature,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def generate_structured(self, messages: list[dict], *, schema: dict) -> dict:
        schema_instruction = (
            "请严格按照 JSON Schema 格式回复，不要添加额外文本。\n"
            f"JSON Schema:\n{json.dumps(schema, ensure_ascii=False)}"
        )
        # Append schema to existing system message instead of overwriting it
        full_messages = list(messages)
        for msg in full_messages:
            if msg.get("role") == "system":
                msg["content"] = msg["content"] + "\n\n" + schema_instruction
                break
        else:
            full_messages.insert(0, {"role": "system", "content": schema_instruction})

        # Log prompt size for debugging
        total_chars = sum(len(m.get("content", "")) for m in full_messages)
        logger.info(f"[MIMO_REQUEST] messages={len(full_messages)}, total_chars={total_chars}")
        logger.debug(f"[MIMO_REQUEST_BODY] {json.dumps(full_messages, ensure_ascii=False)}")

        response = await self._client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": settings.MIMO_MODEL,
                "messages": full_messages,
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        finish_reason = data["choices"][0].get("finish_reason", "unknown")
        if finish_reason == "content_filter":
            logger.warning(f"[MIMO_FILTERED] content_filter triggered, prompt_chars={total_chars}")
            raise ContentFilteredError("请求被内容安全策略拦截，请调整描述后重试")
        if not content or not content.strip():
            logger.error(
                f"[MIMO_EMPTY] finish_reason={finish_reason}, "
                f"prompt_chars={total_chars}, "
                f"raw_response={json.dumps(data, ensure_ascii=False)[:500]}"
            )
            raise ValueError(f"MiMo API returned empty response (finish_reason={finish_reason})")
        logger.info(f"[MIMO_OK] finish_reason={finish_reason}, content_len={len(content)}")
        logger.debug(f"[MIMO_RESPONSE] {content}")
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(
                f"[MIMO_INVALID_JSON] finish_reason={finish_reason}, "
                f"content_len={len(content)}, "
                f"content_preview={content[:300]!r}"
            )
            raise

    async def generate_stream(self, messages: list[dict], *, temperature: float = 0.7) -> AsyncIterator[str]:
        """MiMo API SSE 流式输出"""
        async with self._client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "text/event-stream",
            },
            json={
                "model": settings.MIMO_MODEL,
                "messages": messages,
                "temperature": temperature,
                "stream": True,
            },
            timeout=60.0,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, IndexError):
                    continue

    async def close(self) -> None:
        await self._client.aclose()
