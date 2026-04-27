"""Tests for /api/v1/conversation endpoints."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.core.database import get_db
from src.main import app
from src.schemas.course import SessionCourse
from src.services.session_store import SessionStore


def _make_mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture(autouse=True)
def _override_db():
    app.dependency_overrides[get_db] = _make_mock_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
def _mock_redis():
    """Mock Redis so LLMCache doesn't try to connect."""
    with patch("src.services.llm.cache.get_redis") as mock_get_redis:
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)
        redis_mock.setex = AsyncMock()
        mock_get_redis.return_value = redis_mock
        yield redis_mock


client = TestClient(app)


class TestChatNoCourses:
    def test_returns_hint_without_courses(self):
        SessionStore.clear("conv-test")
        client.cookies.set("device_id", "conv-test")

        resp = client.post(
            "/api/v1/conversation/chat",
            json={"message": "推荐课程"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "请先上传课表" in data["reply"]
        assert data["recommendations"] == []


class TestChatWithCourses:
    def test_returns_recommendations(self):
        SessionStore.set_courses("conv-test", [
            SessionCourse(
                id="course-1",
                name="高等数学",
                credit=4.0,
                course_no="MATH101",
                instructor="张教授",
                capacity=60,
                location="A101",
                campus="主校区",
                category="必修",
                semester="2026-春",
            ),
        ])
        client.cookies.set("device_id", "conv-test")

        resp = client.post(
            "/api/v1/conversation/chat",
            json={"message": "推荐数学课程"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "reply" in data
        assert "conversation_id" in data


class TestChatStream:
    def test_stream_returns_sse(self):
        SessionStore.set_courses("conv-test", [
            SessionCourse(
                id="course-1",
                name="高等数学",
                credit=4.0,
                course_no="MATH101",
                instructor="张教授",
                capacity=60,
                location="A101",
                campus="主校区",
                category="必修",
                semester="2026-春",
            ),
        ])
        client.cookies.set("device_id", "conv-test")

        resp = client.post(
            "/api/v1/conversation/chat/stream",
            json={"message": "推荐课程"},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

    def test_stream_without_courses(self):
        SessionStore.clear("conv-test")
        client.cookies.set("device_id", "conv-test")

        resp = client.post(
            "/api/v1/conversation/chat/stream",
            json={"message": "推荐课程"},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
