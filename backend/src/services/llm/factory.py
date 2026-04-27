from src.core.config import settings
from src.services.llm.base import LLMProvider
from src.services.llm.mimo import MiMoProvider


class LLMFactory:
    """LLM 提供商工厂"""

    _providers: dict[str, type[LLMProvider]] = {
        "mimo": MiMoProvider,
    }

    @classmethod
    def create(cls, provider_name: str | None = None) -> LLMProvider:
        name = provider_name or "mimo"
        if name not in cls._providers:
            raise ValueError(f"未知的 LLM 提供商: {name}")
        return cls._providers[name]()

    @classmethod
    def get_available(cls) -> LLMProvider:
        """获取可用的 LLM 提供商（优先 MiMo）"""
        if settings.MIMO_API_KEY:
            return cls.create("mimo")
        raise ValueError("没有可用的 LLM 提供商，请配置 MIMO_API_KEY")
