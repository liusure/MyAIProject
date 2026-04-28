"""Tests for RecommendService — with mocked LLM and DB."""
import uuid
from datetime import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.schemas.course import ScheduleItem, SessionCourse
from src.services.recommend import RecommendService


class MockLLM:
    """Deterministic LLM that returns course_ids from the session courses."""

    def __init__(self, structured_result=None):
        self._custom_result = structured_result
        self.structured_calls = []

    def _build_default_result(self):
        return {
            "reply": "推荐方案如下",
            "recommendations": [
                {
                    "plan_name": "测试方案",
                    "course_ids": [],  # filled by caller
                    "reason": "匹配需求",
                    "match_score": 90,
                }
            ],
        }

    async def generate(self, messages, *, temperature=0.7):
        return "测试回复"

    async def generate_structured(self, messages, *, schema):
        self.structured_calls.append({"messages": messages, "schema": schema})
        if self._custom_result:
            return self._custom_result
        # Return result with empty course_ids — tests that need matching
        # should pass structured_result with valid UUIDs
        return self._build_default_result()

    async def generate_stream(self, messages, *, temperature=0.7):
        yield "测试"


def _make_course(id=None, name="高等数学", credit=4.0, course_no="MATH101"):
    if id is None:
        id = str(uuid.uuid4())
    return SessionCourse(
        id=id,
        name=name,
        credit=credit,
        course_no=course_no,
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
        location="A101",
        campus="主校区",
        category="专业必修",
        semester="2026-春",
    )


class TestRecommend:
    @pytest.mark.asyncio
    async def test_no_session_courses_returns_hint(self):
        db = AsyncMock()
        llm = MockLLM()
        service = RecommendService(db, llm, session_courses=None)

        result = await service.recommend("推荐课程")

        assert "请先上传课表" in result["reply"]
        assert result["recommendations"] == []

    @pytest.mark.asyncio
    async def test_empty_session_courses_returns_hint(self):
        db = AsyncMock()
        llm = MockLLM()
        service = RecommendService(db, llm, session_courses=[])

        result = await service.recommend("推荐课程")

        assert "请先上传课表" in result["reply"]

    @pytest.mark.asyncio
    async def test_returns_recommendations(self):
        db = AsyncMock()
        course = _make_course()
        llm = MockLLM(structured_result={
            "reply": "推荐方案如下",
            "recommendations": [
                {
                    "plan_name": "测试方案",
                    "course_ids": [course.id],
                    "reason": "匹配需求",
                    "match_score": 90,
                }
            ],
        })
        service = RecommendService(db, llm, session_courses=[course])

        result = await service.recommend("推荐数学课")

        assert result["reply"] == "推荐方案如下"
        assert len(result["recommendations"]) == 1
        assert result["recommendations"][0].plan_name == "测试方案"

    @pytest.mark.asyncio
    async def test_recommendation_contains_full_snapshot(self):
        db = AsyncMock()
        course = _make_course()
        llm = MockLLM(structured_result={
            "reply": "推荐",
            "recommendations": [
                {
                    "plan_name": "方案",
                    "course_ids": [course.id],
                    "reason": "匹配",
                    "match_score": 80,
                }
            ],
        })
        service = RecommendService(db, llm, session_courses=[course])

        result = await service.recommend("推荐")
        plan = result["recommendations"][0]
        crs = plan.courses[0]

        assert crs.name == "高等数学"
        assert crs.credit == 4.0
        assert crs.course_no == "MATH101"
        assert crs.instructor == "张教授"
        assert len(crs.schedule) == 1

    @pytest.mark.asyncio
    async def test_llm_called_with_messages(self):
        db = AsyncMock()
        course = _make_course()
        llm = MockLLM(structured_result={
            "reply": "推荐",
            "recommendations": [
                {"plan_name": "方案", "course_ids": [course.id], "reason": "匹配", "match_score": 80}
            ],
        })
        service = RecommendService(db, llm, session_courses=[course])

        context = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
        await service.recommend("推荐", context)

        assert len(llm.structured_calls) == 1
        # Messages should include system + context + user
        msgs = llm.structured_calls[0]["messages"]
        assert msgs[0]["role"] == "system"
        assert msgs[-1]["content"] == "推荐"

    @pytest.mark.asyncio
    async def test_no_matching_course_returns_empty(self):
        db = AsyncMock()
        llm = MockLLM(structured_result={
            "reply": "无匹配",
            "recommendations": [
                {
                    "plan_name": "方案",
                    "course_ids": [str(uuid.uuid4())],  # valid UUID but not in courses
                    "reason": "无",
                    "match_score": 0,
                }
            ],
        })
        service = RecommendService(db, llm, session_courses=[_make_course()])

        result = await service.recommend("推荐")

        assert result["recommendations"] == []

    @pytest.mark.asyncio
    async def test_llm_error_propagates(self):
        db = AsyncMock()

        class ErrorLLM:
            async def generate_structured(self, messages, *, schema):
                raise RuntimeError("API error")
            async def generate(self, messages, *, temperature=0.7):
                return "error"
            async def generate_stream(self, messages, *, temperature=0.7):
                yield "error"

        service = RecommendService(db, ErrorLLM(), session_courses=[_make_course()])

        with pytest.raises(RuntimeError, match="API error"):
            await service.recommend("推荐")


class TestBuildRecommendationPlan:
    """Tests for _build_recommendation_plan — the core matching logic."""

    @pytest.mark.asyncio
    async def test_match_by_exact_name(self):
        db = AsyncMock()
        course = _make_course(name="高等数学")
        service = RecommendService(db, AsyncMock(), session_courses=[course])

        plan = await service._build_recommendation_plan(
            {"plan_name": "方案", "course_ids": ["高等数学"], "reason": "匹配", "match_score": 90},
            [course],
        )
        assert plan is not None
        assert len(plan.courses) == 1

    @pytest.mark.asyncio
    async def test_match_by_exact_id(self):
        db = AsyncMock()
        course = _make_course()
        service = RecommendService(db, AsyncMock(), session_courses=[course])

        plan = await service._build_recommendation_plan(
            {"plan_name": "方案", "course_ids": [course.id], "reason": "匹配", "match_score": 90},
            [course],
        )
        assert plan is not None

    @pytest.mark.asyncio
    async def test_match_by_course_no(self):
        db = AsyncMock()
        course = _make_course(name="高等数学", course_no="MATH101")
        service = RecommendService(db, AsyncMock(), session_courses=[course])

        plan = await service._build_recommendation_plan(
            {"plan_name": "方案", "course_ids": ["MATH101"], "reason": "匹配", "match_score": 90},
            [course],
        )
        assert plan is not None
        assert len(plan.courses) == 1

    @pytest.mark.asyncio
    async def test_match_by_partial_name(self):
        """LLM often returns shortened names like '篮球' for '体育（篮球）'."""
        db = AsyncMock()
        course = _make_course(name="体育（篮球）", course_no="PE101")
        service = RecommendService(db, AsyncMock(), session_courses=[course])

        plan = await service._build_recommendation_plan(
            {"plan_name": "方案", "course_ids": ["篮球"], "reason": "匹配", "match_score": 80},
            [course],
        )
        assert plan is not None
        assert plan.courses[0].name == "体育（篮球）"

    @pytest.mark.asyncio
    async def test_no_match_returns_none(self):
        db = AsyncMock()
        course = _make_course(name="高等数学")
        service = RecommendService(db, AsyncMock(), session_courses=[course])

        plan = await service._build_recommendation_plan(
            {"plan_name": "方案", "course_ids": ["不存在的课"], "reason": "无", "match_score": 0},
            [course],
        )
        assert plan is None

    @pytest.mark.asyncio
    async def test_empty_course_ids_returns_none(self):
        db = AsyncMock()
        course = _make_course()
        service = RecommendService(db, AsyncMock(), session_courses=[course])

        plan = await service._build_recommendation_plan(
            {"plan_name": "方案", "course_ids": [], "reason": "无", "match_score": 0},
            [course],
        )
        assert plan is None

    @pytest.mark.asyncio
    async def test_multiple_courses_matched(self):
        db = AsyncMock()
        c1 = _make_course(name="高等数学", course_no="MATH101")
        c2 = _make_course(name="大学英语", course_no="ENG101")
        service = RecommendService(db, AsyncMock(), session_courses=[c1, c2])

        plan = await service._build_recommendation_plan(
            {"plan_name": "方案", "course_ids": ["高等数学", "大学英语"], "reason": "匹配", "match_score": 90},
            [c1, c2],
        )
        assert plan is not None
        assert len(plan.courses) == 2
        assert plan.total_credits == c1.credit + c2.credit

    @pytest.mark.asyncio
    async def test_schedule_included_in_response(self):
        db = AsyncMock()
        course = _make_course()
        service = RecommendService(db, AsyncMock(), session_courses=[course])

        plan = await service._build_recommendation_plan(
            {"plan_name": "方案", "course_ids": [course.id], "reason": "匹配", "match_score": 90},
            [course],
        )
        assert plan is not None
        assert len(plan.courses[0].schedule) == 1
        assert plan.courses[0].schedule[0].day_of_week == 1

    @pytest.mark.asyncio
    async def test_empty_schedule_no_crash(self):
        """Courses imported without schedule data should still produce plans."""
        db = AsyncMock()
        course = _make_course()
        course.schedule = []
        service = RecommendService(db, AsyncMock(), session_courses=[course])

        plan = await service._build_recommendation_plan(
            {"plan_name": "方案", "course_ids": [course.id], "reason": "匹配", "match_score": 90},
            [course],
        )
        assert plan is not None
        assert plan.courses[0].schedule == []


class TestFormatSessionCoursesForLLM:
    def test_basic_format(self):
        db = AsyncMock()
        llm = MockLLM()
        service = RecommendService(db, llm, session_courses=[])
        courses = [_make_course()]

        text = service._format_session_courses_for_llm(courses)

        assert "高等数学" in text
        assert "4.0学分" in text
        assert "张教授" in text
        assert "MATH101" in text

    def test_no_schedule(self):
        db = AsyncMock()
        llm = MockLLM()
        service = RecommendService(db, llm, session_courses=[])
        course = _make_course()
        course.schedule = []

        text = service._format_session_courses_for_llm([course])
        assert "高等数学" in text

    def test_multiple_courses(self):
        db = AsyncMock()
        llm = MockLLM()
        service = RecommendService(db, llm, session_courses=[])
        courses = [
            _make_course(name="数学"),
            _make_course(name="物理"),
        ]

        text = service._format_session_courses_for_llm(courses)
        assert "数学" in text
        assert "物理" in text

    def test_includes_course_id(self):
        db = AsyncMock()
        llm = MockLLM()
        service = RecommendService(db, llm, session_courses=[])
        course = _make_course()

        text = service._format_session_courses_for_llm([course])
        assert f"id:{course.id}" in text

    def test_includes_course_no(self):
        db = AsyncMock()
        llm = MockLLM()
        service = RecommendService(db, llm, session_courses=[])
        course = _make_course(course_no="CS201")

        text = service._format_session_courses_for_llm([course])
        assert "CS201" in text


class TestRecommendReason:
    """Tests for LLM recommendation reason (T005/T006)."""

    @pytest.mark.asyncio
    async def test_reason_used_as_reply(self):
        """When LLM returns reason, it should be used as the reply."""
        db = AsyncMock()
        course = _make_course()

        class ReasonLLM:
            def __init__(self):
                self.call_count = 0

            async def generate_structured(self, messages, *, schema):
                self.call_count += 1
                if self.call_count == 1:
                    # Step 1: field selection
                    return {"selected_fields": ["课程名称"]}
                else:
                    # Step 2: course filtering with reason
                    return {"matching_indices": [0], "reason": "这些课程匹配您对数学的需求，高数是计算机专业核心课。"}

            async def generate(self, messages, *, temperature=0.7):
                return "test"

            async def generate_stream(self, messages, *, temperature=0.7):
                yield "test"

        llm = ReasonLLM()
        service = RecommendService(db, llm, session_courses=[course])
        result = await service.recommend("推荐数学课")

        assert "这些课程匹配您对数学的需求" in result["reply"]
        assert "筛选出" not in result["reply"]

    @pytest.mark.asyncio
    async def test_fallback_template_when_no_reason(self):
        """When LLM doesn't return reason, fallback to template."""
        db = AsyncMock()
        course = _make_course()

        class NoReasonLLM:
            def __init__(self):
                self.call_count = 0

            async def generate_structured(self, messages, *, schema):
                self.call_count += 1
                if self.call_count == 1:
                    return {"selected_fields": ["课程名称"]}
                else:
                    return {"matching_indices": [0]}  # no reason field

            async def generate(self, messages, *, temperature=0.7):
                return "test"

            async def generate_stream(self, messages, *, temperature=0.7):
                yield "test"

        llm = NoReasonLLM()
        service = RecommendService(db, llm, session_courses=[course])
        result = await service.recommend("推荐数学课")

        assert "根据您的需求，筛选出 1 门相关课程。" == result["reply"]

    @pytest.mark.asyncio
    async def test_fallback_template_when_empty_reason(self):
        """When LLM returns empty reason string, fallback to template."""
        db = AsyncMock()
        course = _make_course()

        class EmptyReasonLLM:
            def __init__(self):
                self.call_count = 0

            async def generate_structured(self, messages, *, schema):
                self.call_count += 1
                if self.call_count == 1:
                    return {"selected_fields": ["课程名称"]}
                else:
                    return {"matching_indices": [0], "reason": ""}

            async def generate(self, messages, *, temperature=0.7):
                return "test"

            async def generate_stream(self, messages, *, temperature=0.7):
                yield "test"

        llm = EmptyReasonLLM()
        service = RecommendService(db, llm, session_courses=[course])
        result = await service.recommend("推荐数学课")

        assert "根据您的需求，筛选出 1 门相关课程。" == result["reply"]
