"""Tests for ConversationService — requires mocked AsyncSession."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.conversation import ConversationService


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


@pytest.fixture
def service(mock_db):
    return ConversationService(mock_db)


class TestCreate:
    @pytest.mark.asyncio
    async def test_creates_conversation(self, service, mock_db):
        conv = await service.create("device-1")
        assert conv.device_id == "device-1"
        assert conv.messages == []
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_generates_uuid(self, service):
        conv = await service.create("device-1")
        assert conv.id is not None
        # Verify it's a valid UUID
        uuid.UUID(str(conv.id))


class TestAddMessage:
    @pytest.mark.asyncio
    async def test_adds_message(self, service, mock_db):
        conv = MagicMock()
        conv.messages = []
        conv.updated_at = None

        result = await service.add_message(conv, "user", "你好")

        assert len(conv.messages) == 1
        assert conv.messages[0]["role"] == "user"
        assert conv.messages[0]["content"] == "你好"
        assert "timestamp" in conv.messages[0]
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_adds_structured_data(self, service, mock_db):
        conv = MagicMock()
        conv.messages = []
        conv.updated_at = None

        await service.add_message(conv, "assistant", "推荐", {"rec": "data"})

        assert conv.messages[0]["structured_data"] == {"rec": "data"}

    @pytest.mark.asyncio
    async def test_appends_to_existing(self, service, mock_db):
        conv = MagicMock()
        conv.messages = [{"role": "user", "content": "first", "timestamp": "t1"}]
        conv.updated_at = None

        await service.add_message(conv, "assistant", "second")

        assert len(conv.messages) == 2
        assert conv.messages[1]["content"] == "second"


class TestGetContextMessages:
    @pytest.mark.asyncio
    async def test_returns_role_and_content(self, service):
        conv = MagicMock()
        conv.messages = [
            {"role": "user", "content": "hi", "timestamp": "t1"},
            {"role": "assistant", "content": "hello", "timestamp": "t2"},
        ]

        context = await service.get_context_messages(conv)
        assert len(context) == 2
        assert context[0] == {"role": "user", "content": "hi"}
        assert "timestamp" not in context[0]

    @pytest.mark.asyncio
    async def test_limits_turns(self, service):
        messages = [
            {"role": "user", "content": f"msg{i}", "timestamp": f"t{i}"}
            for i in range(30)
        ]
        conv = MagicMock()
        conv.messages = messages

        context = await service.get_context_messages(conv, max_turns=5)
        # max_turns=5 → last 10 messages
        assert len(context) == 10

    @pytest.mark.asyncio
    async def test_empty_messages(self, service):
        conv = MagicMock()
        conv.messages = []
        context = await service.get_context_messages(conv)
        assert context == []
