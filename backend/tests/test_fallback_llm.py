"""Tests for FallbackLLMProvider — pure logic, no network."""
import pytest

from src.services.llm.fallback import FallbackLLMProvider


@pytest.fixture
def fallback():
    return FallbackLLMProvider()


class TestFallbackGenerate:
    @pytest.mark.asyncio
    async def test_returns_string(self, fallback):
        result = await fallback.generate([{"role": "user", "content": "推荐计算机课程"}])
        assert isinstance(result, str)
        assert "计算机" in result

    @pytest.mark.asyncio
    async def test_empty_messages(self, fallback):
        result = await fallback.generate([])
        assert isinstance(result, str)


class TestFallbackGenerateStructured:
    @pytest.mark.asyncio
    async def test_returns_dict(self, fallback):
        result = await fallback.generate_structured(
            [{"role": "user", "content": "推荐计算机"}],
            schema={"type": "object"},
        )
        assert isinstance(result, dict)
        assert "reply" in result
        assert "recommendations" in result
        assert result["recommendations"] == []

    @pytest.mark.asyncio
    async def test_contains_keywords(self, fallback):
        result = await fallback.generate_structured(
            [{"role": "user", "content": "推荐计算机课程"}],
            schema={"type": "object"},
        )
        assert "计算机" in result["keywords"]

    @pytest.mark.asyncio
    async def test_degraded_flag(self, fallback):
        result = await fallback.generate_structured(
            [{"role": "user", "content": "推荐"}],
            schema={"type": "object"},
        )
        assert result["degraded"] is True


class TestExtractKeywords:
    def test_computer_keyword(self, fallback):
        keywords = fallback._extract_keywords("我想学计算机编程")
        assert "计算机" in keywords

    def test_math_keyword(self, fallback):
        keywords = fallback._extract_keywords("推荐数学课")
        assert "数学" in keywords

    def test_multiple_keywords(self, fallback):
        keywords = fallback._extract_keywords("计算机和数学")
        assert "计算机" in keywords
        assert "数学" in keywords

    def test_no_match(self, fallback):
        keywords = fallback._extract_keywords("随便推荐一些课程")
        # Falls back to first 20 chars
        assert len(keywords) == 1
        assert keywords[0] == "随便推荐一些课程"
