"""Tests for /api/v1/import endpoints."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.core.database import get_db
from src.main import app
from src.services.session_store import SessionStore


def _make_mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture(autouse=True)
def _override_db():
    app.dependency_overrides[get_db] = _make_mock_db
    yield
    app.dependency_overrides.pop(get_db, None)


client = TestClient(app)


class TestAnalyzeExcel:
    def test_unsupported_format_returns_400(self):
        resp = client.post(
            "/api/v1/import/analyze",
            files={"file": ("test.pdf", b"data", "application/pdf")},
        )
        assert resp.status_code == 400

    def test_file_too_large_returns_413(self):
        large_data = b"x" * (5 * 1024 * 1024 + 1)
        resp = client.post(
            "/api/v1/import/analyze",
            files={"file": ("test.csv", large_data, "text/csv")},
        )
        assert resp.status_code == 413


class TestGetSessionCourses:
    def test_empty_returns_204(self):
        resp = client.get("/api/v1/import/session/courses")
        assert resp.status_code == 204

    def test_with_courses_returns_data(self):
        from src.schemas.course import SessionCourse

        SessionStore.set_courses("test-device", [
            SessionCourse(name="数学", credit=3.0),
        ])
        client.cookies.set("device_id", "test-device")
        resp = client.get("/api/v1/import/session/courses")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["courses"]) == 1
        assert data["courses"][0]["name"] == "数学"


class TestClearSessionCourses:
    def test_clears_data(self):
        from src.schemas.course import SessionCourse

        SessionStore.set_courses("test-device", [
            SessionCourse(name="数学", credit=3.0),
        ])
        client.cookies.set("device_id", "test-device")

        resp = client.delete("/api/v1/import/session/courses")
        assert resp.status_code == 204
        assert SessionStore.get_courses("test-device") is None
