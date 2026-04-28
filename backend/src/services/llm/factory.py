from src.core.config import settings
from src.services.llm.base import LLMProvider
from src.services.llm.mimo import MiMoProvider


class LLMFactory:
    """LLM 提供商工厂"""

    _providers: dict[str, type[LLMProvider]] = {
        "mimo": MiMoProvider,
    }
    _instances: dict[str, LLMProvider] = {}

    @classmethod
    def create(cls, provider_name: str | None = None) -> LLMProvider:
        name = provider_name or "mimo"
        if name not in cls._providers:
            raise ValueError(f"未知的 LLM 提供商: {name}")
        if name not in cls._instances:
            cls._instances[name] = cls._providers[name]()
        return cls._instances[name]

    @classmethod
    def get_available(cls) -> LLMProvider:
        """获取可用的 LLM 提供商（优先 MiMo）"""
        if settings.MIMO_API_KEY:
            return cls.create("mimo")
        raise ValueError("没有可用的 LLM 提供商，请配置 MIMO_API_KEY")

    @classmethod
    async def close_all(cls) -> None:
        """关闭所有 provider 实例的连接（FastAPI shutdown 时调用）"""
        for instance in cls._instances.values():
            await instance.close()
        cls._instances.clear()
