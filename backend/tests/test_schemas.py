"""Tests for Pydantic schemas — validation edge cases."""
import uuid
from datetime import datetime, time

from src.schemas.course import CourseResponse, ScheduleItem, SessionCourse
from src.schemas.plan import (
    ChatResponse,
    ConflictItem,
    RecommendationPlan,
    SavedPlanCreate,
    SavedPlanResponse,
)
from src.schemas.conversation import ChatRequest
from src.schemas.import_result import (
    ColumnMapping,
    DegradationImpact,
    DegradationReport,
    ImportAnalyzeResponse,
    ImportError,
    ImportConfirmRequest,
    ImportConfirmResponse,
    MappingResult,
)


class TestScheduleItem:
    def test_valid(self):
        item = ScheduleItem(
            day_of_week=1,
            start_period=time(8, 0),
            end_period=time(9, 40),
            weeks=[1, 2, 3],
        )
        assert item.day_of_week == 1

    def test_weeks_empty_list(self):
        item = ScheduleItem(
            day_of_week=1,
            start_period=time(8, 0),
            end_period=time(9, 40),
            weeks=[],
        )
        assert item.weeks == []


class TestSessionCourse:
    def test_minimal(self):
        c = SessionCourse(name="数学", credit=3.0)
        assert c.name == "数学"
        assert c.credit == 3.0
        assert c.id is None
        assert c.schedule == []

    def test_full(self):
        c = SessionCourse(
            id="id-1",
            name="数学",
            credit=3.0,
            course_no="MATH101",
            instructor="张教授",
            capacity=60,
            location="A101",
            campus="主校区",
            category="必修",
            semester="2026-春",
        )
        assert c.course_no == "MATH101"


class TestCourseResponse:
    def test_valid(self):
        c = CourseResponse(
            id=uuid.uuid4(),
            course_no="MATH101",
            name="高等数学",
            credit=4.0,
            instructor="张教授",
            capacity=60,
            schedule=[],
            location="A101",
            campus="主校区",
            category="必修",
            semester="2026-春",
            is_active=True,
        )
        assert c.name == "高等数学"

    def test_model_dump(self):
        c = CourseResponse(
            id=uuid.uuid4(),
            course_no="MATH101",
            name="高等数学",
            credit=4.0,
            instructor="张教授",
            capacity=60,
            schedule=[],
            location="A101",
            campus="主校区",
            category="必修",
            semester="2026-春",
            is_active=True,
        )
        d = c.model_dump()
        assert d["name"] == "高等数学"
        assert "id" in d


class TestChatRequest:
    def test_minimal(self):
        req = ChatRequest(message="你好")
        assert req.message == "你好"
        assert req.conversation_id is None

    def test_with_conversation_id(self):
        cid = uuid.uuid4()
        req = ChatRequest(message="你好", conversation_id=cid)
        assert req.conversation_id == cid


class TestConflictItem:
    def test_valid(self):
        item = ConflictItem(
            type="time",
            severity="error",
            course_a=uuid.uuid4(),
            course_b=uuid.uuid4(),
            message="时间冲突",
        )
        assert item.type == "time"


class TestRecommendationPlan:
    def test_valid(self):
        plan = RecommendationPlan(
            plan_name="方案A",
            courses=[],
            total_credits=15.0,
            match_score=85.0,
        )
        assert plan.plan_name == "方案A"
        assert plan.conflicts == []

    def test_with_conflicts(self):
        conflict = ConflictItem(
            type="time",
            severity="error",
            course_a=uuid.uuid4(),
            course_b=uuid.uuid4(),
            message="冲突",
        )
        plan = RecommendationPlan(
            plan_name="方案A",
            courses=[],
            total_credits=15.0,
            match_score=85.0,
            conflicts=[conflict],
        )
        assert len(plan.conflicts) == 1


class TestChatResponse:
    def test_defaults(self):
        resp = ChatResponse(
            conversation_id=uuid.uuid4(),
            reply="你好",
        )
        assert resp.recommendations == []
        assert resp.conflicts == []
        assert resp.degraded is False


class TestMappingResult:
    def test_valid(self):
        mr = MappingResult(
            mappings=[
                ColumnMapping(source="课程名称", target="name", confidence=0.95),
            ],
            unmapped_source=[],
            unmapped_target=["credit"],
        )
        assert len(mr.mappings) == 1

    def test_defaults(self):
        mr = MappingResult(mappings=[])
        assert mr.unmapped_source == []
        assert mr.unmapped_target == []


class TestDegradationReport:
    def test_defaults(self):
        dr = DegradationReport()
        assert dr.missing_fields == []
        assert dr.impacts == []


class TestImportConfirmRequest:
    def test_valid(self):
        req = ImportConfirmRequest(
            mapping=MappingResult(mappings=[]),
            raw_data=[{"name": "数学"}],
        )
        assert len(req.raw_data) == 1


class TestImportError:
    def test_valid(self):
        err = ImportError(row=2, message="学分无效")
        assert err.row == 2
        assert err.message == "学分无效"
