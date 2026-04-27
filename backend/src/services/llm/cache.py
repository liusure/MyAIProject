import hashlib
import json

from src.core.redis import get_redis


def _pydantic_default(obj):
    """JSON encoder fallback for Pydantic models."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class LLMCache:
    """LLM 响应缓存（Redis）"""

    PREFIX = "llm_cache:"
    TTL = 3600  # 1 小时

    @classmethod
    def _make_key(cls, messages: list[dict]) -> str:
        content = json.dumps(messages, sort_keys=True, ensure_ascii=False)
        return f"{cls.PREFIX}{hashlib.md5(content.encode()).hexdigest()}"

    @classmethod
    async def get(cls, messages: list[dict]) -> dict | None:
        redis = await get_redis()
        data = await redis.get(cls._make_key(messages))
        if data:
            return json.loads(data)
        return None

    @classmethod
    async def set(cls, messages: list[dict], result: dict) -> None:
        redis = await get_redis()
        await redis.setex(cls._make_key(messages), cls.TTL, json.dumps(result, ensure_ascii=False, default=_pydantic_default))
