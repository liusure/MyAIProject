from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class LLMProvider(ABC):
    """LLM 提供商抽象基类"""

    @abstractmethod
    async def generate(self, messages: list[dict], *, temperature: float = 0.7) -> str:
        """生成自然语言回复"""

    @abstractmethod
    async def generate_structured(self, messages: list[dict], *, schema: dict) -> dict:
        """生成 JSON 结构化输出"""

    async def generate_stream(self, messages: list[dict], *, temperature: float = 0.7) -> AsyncIterator[str]:
        """流式生成自然语言回复（逐 token 产出）"""
        result = await self.generate(messages, temperature=temperature)
        yield result

    async def close(self) -> None:
        """释放资源（如 HTTP 连接池）"""
        pass
