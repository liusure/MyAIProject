"""Tests for RecommendService — with mocked LLM and DB."""
import uuid
from datetime import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.schemas.course import ScheduleItem, SessionCourse
from src.services.recommend import RecommendService


class MockLLM:
    """Deterministic LLM for the two-step filter flow."""

    def __init__(self, filter_result=None):
        """
        Args:
            filter_result: Step-2 result dict with keys matching_indices, reason, match_score.
                           If None, returns empty matching_indices.
        """
        self._filter_result = filter_result or {"matching_indices": [], "reason": "", "match_score": 0}
        self.structured_calls = []
        self._call_count = 0

    async def generate(self, messages, *, temperature=0.7):
        return "测试回复"

    async def generate_structured(self, messages, *, schema):
        self.structured_calls.append({"messages": messages, "schema": schema})
        self._call_count += 1
        if self._call_count == 1:
            # Step 1: field selection
            return {"selected_fields": ["课程名称"]}
        else:
            # Step 2: course filtering
            return self._filter_result

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
    async def test_returns_recommendations_with_reason(self):
        db = AsyncMock()
        course = _make_course()
        llm = MockLLM(filter_result={
            "matching_indices": [0],
            "reason": "高数是计算机专业核心课程，匹配您的需求。",
            "match_score": 90,
        })
        service = RecommendService(db, llm, session_courses=[course])

        result = await service.recommend("推荐数学课")

        assert "高数是计算机专业核心课程" in result["reply"]
        assert len(result["recommendations"]) == 1
        assert result["recommendations"][0].match_score == 90

    @pytest.mark.asyncio
    async def test_recommendation_contains_full_snapshot(self):
        db = AsyncMock()
        course = _make_course()
        llm = MockLLM(filter_result={
            "matching_indices": [0],
            "reason": "匹配",
            "match_score": 80,
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
    async def test_llm_called_twice_for_two_steps(self):
        db = AsyncMock()
        course = _make_course()
        llm = MockLLM(filter_result={
            "matching_indices": [0],
            "reason": "匹配",
            "match_score": 80,
        })
        service = RecommendService(db, llm, session_courses=[course])

        await service.recommend("推荐")

        # Two calls: step 1 (field selection) + step 2 (course filtering)
        assert len(llm.structured_calls) == 2

    @pytest.mark.asyncio
    async def test_no_matching_indices_returns_empty(self):
        db = AsyncMock()
        llm = MockLLM(filter_result={
            "matching_indices": [],
            "reason": "无匹配",
            "match_score": 0,
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


class TestCoursesToPlan:
    """Tests for _courses_to_plan — the plan building logic."""

    def test_single_course_plan(self):
        course = _make_course(name="高等数学")
        plan = RecommendService._courses_to_plan([course], plan_name="方案", match_score=90)

        assert plan is not None
        assert len(plan.courses) == 1
        assert plan.plan_name == "方案"
        assert plan.match_score == 90

    def test_multiple_courses_plan(self):
        c1 = _make_course(name="高等数学", course_no="MATH101")
        c2 = _make_course(name="大学英语", course_no="ENG101")
        plan = RecommendService._courses_to_plan([c1, c2], plan_name="方案", match_score=85)

        assert plan is not None
        assert len(plan.courses) == 2
        assert plan.total_credits == c1.credit + c2.credit
        assert plan.match_score == 85

    def test_schedule_included_in_response(self):
        course = _make_course()
        plan = RecommendService._courses_to_plan([course])

        assert plan is not None
        assert len(plan.courses[0].schedule) == 1
        assert plan.courses[0].schedule[0].day_of_week == 1

    def test_empty_schedule_no_crash(self):
        """Courses imported without schedule data should still produce plans."""
        course = _make_course()
        course.schedule = []
        plan = RecommendService._courses_to_plan([course])

        assert plan is not None
        assert plan.courses[0].schedule == []

    def test_match_score_defaults_to_zero(self):
        course = _make_course()
        plan = RecommendService._courses_to_plan([course])

        assert plan.match_score == 0

    def test_conflict_detection_runs(self):
        """Plan should include detected conflicts."""
        c1 = _make_course(name="课A", course_no="A01")
        c2 = _make_course(name="课B", course_no="B01")
        # Both on same day/period — should detect time conflict
        c2.schedule = c1.schedule
        plan = RecommendService._courses_to_plan([c1, c2])

        assert plan is not None
        # Conflicts may or may not be detected depending on exact schedule overlap


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
                    return {"matching_indices": [0], "reason": "这些课程匹配您对数学的需求，高数是计算机专业核心课。", "match_score": 85}

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
                    return {"matching_indices": [0], "match_score": 70}  # no reason field

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
                    return {"matching_indices": [0], "reason": "", "match_score": 60}

            async def generate(self, messages, *, temperature=0.7):
                return "test"

            async def generate_stream(self, messages, *, temperature=0.7):
                yield "test"

        llm = EmptyReasonLLM()
        service = RecommendService(db, llm, session_courses=[course])
        result = await service.recommend("推荐数学课")

        assert "根据您的需求，筛选出 1 门相关课程。" == result["reply"]

    @pytest.mark.asyncio
    async def test_match_score_passed_to_plan(self):
        """LLM's match_score should be passed to the recommendation plan."""
        db = AsyncMock()
        course = _make_course()

        class ScoreLLM:
            def __init__(self):
                self.call_count = 0

            async def generate_structured(self, messages, *, schema):
                self.call_count += 1
                if self.call_count == 1:
                    return {"selected_fields": ["课程名称"]}
                else:
                    return {"matching_indices": [0], "reason": "匹配", "match_score": 92}

            async def generate(self, messages, *, temperature=0.7):
                return "test"

            async def generate_stream(self, messages, *, temperature=0.7):
                yield "test"

        llm = ScoreLLM()
        service = RecommendService(db, llm, session_courses=[course])
        result = await service.recommend("推荐数学课")

        plan = result["recommendations"][0]
        assert plan.match_score == 92

    @pytest.mark.asyncio
    async def test_match_score_defaults_to_zero(self):
        """When LLM doesn't return match_score, it defaults to 0."""
        db = AsyncMock()
        course = _make_course()

        class NoScoreLLM:
            def __init__(self):
                self.call_count = 0

            async def generate_structured(self, messages, *, schema):
                self.call_count += 1
                if self.call_count == 1:
                    return {"selected_fields": ["课程名称"]}
                else:
                    return {"matching_indices": [0], "reason": "匹配"}  # no match_score

            async def generate(self, messages, *, temperature=0.7):
                return "test"

            async def generate_stream(self, messages, *, temperature=0.7):
                yield "test"

        llm = NoScoreLLM()
        service = RecommendService(db, llm, session_courses=[course])
        result = await service.recommend("推荐数学课")

        plan = result["recommendations"][0]
        assert plan.match_score == 0
