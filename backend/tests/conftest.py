"""Shared fixtures for all tests."""
import uuid
from datetime import datetime, time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.schemas.course import ScheduleItem, SessionCourse


# ─── SessionStore cleanup ───────────────────────────────────────────

@pytest.fixture(autouse=True)
def _clear_session_store():
    """Clear SessionStore between tests."""
    from src.services.session_store import SessionStore
    SessionStore._store.clear()
    SessionStore._raw_data.clear()
    yield
    SessionStore._store.clear()
    SessionStore._raw_data.clear()


# ─── API dependency override cleanup ────────────────────────────────

@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    """Clear FastAPI dependency overrides between tests."""
    from src.main import app
    yield
    app.dependency_overrides.clear()


# ─── Mock LLM Provider ──────────────────────────────────────────────

class MockLLMProvider:
    """Deterministic LLM for testing."""

    def __init__(self, structured_result=None):
        self.structured_result = structured_result or {
            "reply": "测试推荐回复",
            "recommendations": [
                {
                    "plan_name": "测试方案",
                    "course_ids": ["course-1"],
                    "reason": "测试理由",
                    "match_score": 85,
                }
            ],
        }
        self.generate_calls = []
        self.structured_calls = []

    async def generate(self, messages, *, temperature=0.7):
        self.generate_calls.append(messages)
        return "测试回复"

    async def generate_structured(self, messages, *, schema):
        self.structured_calls.append({"messages": messages, "schema": schema})
        return self.structured_result

    async def generate_stream(self, messages, *, temperature=0.7):
        yield "测试"
        yield "流式"
        yield "回复"


@pytest.fixture
def mock_llm():
    return MockLLMProvider()


# ─── Sample course data ─────────────────────────────────────────────

@pytest.fixture
def sample_session_course():
    return SessionCourse(
        id="course-1",
        name="高等数学",
        credit=4.0,
        course_no="MATH101",
        instructor="张教授",
        capacity=60,
        schedule=[
            ScheduleItem(
                day_of_week=1,
                start_period=time(8, 0),
                end_period=time(9, 40),
                weeks=list(range(1, 17)),
            )
        ],
        location="教学楼A101",
        campus="主校区",
        category="专业必修",
        semester="2026-春",
    )


@pytest.fixture
def sample_session_courses():
    return [
        SessionCourse(
            id="course-1",
            name="高等数学",
            credit=4.0,
            course_no="MATH101",
            instructor="张教授",
            capacity=60,
            schedule=[
                ScheduleItem(
                    day_of_week=1,
                    start_period=time(8, 0),
                    end_period=time(9, 40),
                    weeks=list(range(1, 17)),
                )
            ],
            location="教学楼A101",
            campus="主校区",
            category="专业必修",
            semester="2026-春",
        ),
        SessionCourse(
            id="course-2",
            name="数据结构",
            credit=3.0,
            course_no="CS201",
            instructor="李教授",
            capacity=50,
            schedule=[
                ScheduleItem(
                    day_of_week=3,
                    start_period=time(10, 0),
                    end_period=time(11, 40),
                    weeks=list(range(1, 17)),
                )
            ],
            location="教学楼B202",
            campus="主校区",
            category="专业必修",
            semester="2026-春",
        ),
    ]


@pytest.fixture
def sample_course_dicts():
    """Sample course dicts for conflict detection tests."""
    return [
        {
            "id": str(uuid.uuid4()),
            "name": "课程A",
            "credit": 3.0,
            "schedule": [
                {
                    "day_of_week": 1,
                    "start_period": "1",
                    "end_period": "2",
                    "weeks": list(range(1, 17)),
                }
            ],
            "campus": "主校区",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "课程B",
            "credit": 3.0,
            "schedule": [
                {
                    "day_of_week": 1,
                    "start_period": "2",
                    "end_period": "10:40",
                    "weeks": list(range(1, 17)),
                }
            ],
            "campus": "主校区",
        },
    ]


# ─── Mock DB session ────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    """Mock AsyncSession for service tests."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.execute = AsyncMock()
    return db
