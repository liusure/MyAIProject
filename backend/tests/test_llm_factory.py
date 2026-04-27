"""Tests for LLMFactory."""
import pytest
from unittest.mock import patch

from src.services.llm.factory import LLMFactory
from src.services.llm.mimo import MiMoProvider


class TestLLMFactory:
    def test_create_mimo(self):
        provider = LLMFactory.create("mimo")
        assert isinstance(provider, MiMoProvider)

    def test_create_default(self):
        provider = LLMFactory.create()
        assert isinstance(provider, MiMoProvider)

    def test_create_unknown_raises(self):
        with pytest.raises(ValueError, match="未知"):
            LLMFactory.create("unknown")

    def test_get_available_with_key(self):
        with patch("src.services.llm.factory.settings") as mock_settings:
            mock_settings.MIMO_API_KEY = "test-key"
            provider = LLMFactory.get_available()
            assert isinstance(provider, MiMoProvider)

    def test_get_available_no_key_raises(self):
        with patch("src.services.llm.factory.settings") as mock_settings:
            mock_settings.MIMO_API_KEY = ""
            with pytest.raises(ValueError, match="没有可用"):
                LLMFactory.get_available()
