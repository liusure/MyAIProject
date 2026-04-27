import json

from src.services.llm.base import LLMProvider


class FallbackLLMProvider(LLMProvider):
    """LLM 降级策略：基于关键词的搜索替代方案"""

    KEYWORD_MAP = {
        "计算机": ["计算机", "CS", "编程", "软件"],
        "数学": ["数学", "统计", "概率"],
        "物理": ["物理", "力学", "电磁"],
        "英语": ["英语", "翻译", "语言"],
        "周三": ["周三", "星期三"],
        "下午": ["下午", "PM", "14:", "15:", "16:"],
        "上午": ["上午", "AM", "08:", "09:", "10:"],
    }

    async def generate(self, messages: list[dict], *, temperature: float = 0.7) -> str:
        last_message = messages[-1]["content"] if messages else ""
        keywords = self._extract_keywords(last_message)
        return f"LLM 服务不可用，已切换至关键词搜索模式。搜索关键词：{', '.join(keywords)}"

    async def generate_structured(self, messages: list[dict], *, schema: dict) -> dict:
        last_message = messages[-1]["content"] if messages else ""
        keywords = self._extract_keywords(last_message)
        return {
            "keywords": keywords,
            "degraded": True,
            "reply": f"LLM 服务暂时不可用，已为您提取搜索关键词：{', '.join(keywords)}",
            "recommendations": [],
        }

    def _extract_keywords(self, text: str) -> list[str]:
        keywords = []
        for key, aliases in self.KEYWORD_MAP.items():
            if any(alias in text for alias in aliases):
                keywords.append(key)
        if not keywords:
            keywords = [text[:20]]
        return keywords
