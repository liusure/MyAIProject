"""Tests for LLMCache — key generation and Pydantic serialization."""
import json

import pytest

from src.services.llm.cache import _pydantic_default, LLMCache


class TestPydanticDefault:
    def test_with_model_dump(self):
        class FakeModel:
            def model_dump(self, mode=None):
                return {"key": "value"}

        result = _pydantic_default(FakeModel())
        assert result == {"key": "value"}

    def test_without_model_dump_raises(self):
        with pytest.raises(TypeError, match="not JSON serializable"):
            _pydantic_default(object())


class TestMakeKey:
    def test_deterministic(self):
        messages = [{"role": "user", "content": "hello"}]
        key1 = LLMCache._make_key(messages)
        key2 = LLMCache._make_key(messages)
        assert key1 == key2

    def test_different_messages_different_keys(self):
        key1 = LLMCache._make_key([{"role": "user", "content": "hello"}])
        key2 = LLMCache._make_key([{"role": "user", "content": "world"}])
        assert key1 != key2

    def test_key_format(self):
        messages = [{"role": "user", "content": "hello"}]
        key = LLMCache._make_key(messages)
        assert key.startswith("llm_cache:")
        assert len(key) == len("llm_cache:") + 32  # MD5 hex = 32 chars
