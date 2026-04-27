"""Integration test: full import → schedule parse → recommend pipeline."""
import uuid
from datetime import time
from unittest.mock import AsyncMock

import pytest

from src.schemas.course import SessionCourse, ScheduleItem
from src.schemas.import_result import ColumnMapping, MappingResult
from src.services.import_parser import ImportParser
from src.services.schedule_parser import ScheduleParser
from src.services.recommend import RecommendService
from src.services.session_store import SessionStore


def _make_mapping() -> MappingResult:
    """Simulate LLM column mapping for a typical Chinese course Excel."""
    return MappingResult(
        mappings=[
            ColumnMapping(source="课程名称", target="name", confidence=0.95),
            ColumnMapping(source="学分", target="credit", confidence=0.95),
            ColumnMapping(source="课程编码", target="course_no", confidence=0.9),
            ColumnMapping(source="课程属性", target="category", confidence=0.9),
            ColumnMapping(source="教室", target="location", confidence=0.9),
            ColumnMapping(source="主讲教师", target="instructor", confidence=0.9),
            ColumnMapping(source="限选人数", target="capacity", confidence=0.9),
            ColumnMapping(source="星期节次", target="schedule", confidence=0.9),
            ColumnMapping(source="开课周", target="weeks", confidence=0.9),
        ],
        unmapped_source=[],
        unmapped_target=["campus", "semester"],
    )


RAW_DATA = [
    {
        "课程名称": "高等数学",
        "学分": "4.0",
        "课程编码": "MATH101",
        "课程属性": "专业必修",
        "教室": "教一楼101",
        "主讲教师": "张教授",
        "限选人数": "60",
        "星期节次": "周一(1-2)",
        "开课周": "第1-16周",
    },
    {
        "课程名称": "大学英语",
        "学分": "3.0",
        "课程编码": "ENG101",
        "课程属性": "专业必修",
        "教室": "教二楼201",
        "主讲教师": "李教授",
        "限选人数": "50",
        "星期节次": "周三(3-4)",
        "开课周": "第1-16周",
    },
    {
        "课程名称": "体育（篮球）",
        "学分": "1.0",
        "课程编码": "PE101",
        "课程属性": "公共选修",
        "教室": "体育馆",
        "主讲教师": "王教练",
        "限选人数": "30",
        "星期节次": "周五(5-6)",
        "开课周": "第1-12周",
    },
    {
        "课程名称": "Python编程",
        "学分": "2.0",
        "课程编码": "CS101",
        "课程属性": "通识选修",
        "教室": "机房301",
        "主讲教师": "赵教授",
        "限选人数": "80",
        "星期节次": "周二(7-8)",
        "开课周": "第1-12周",
    },
]


class TestFullPipeline:
    """Test the full import → parse → recommend flow."""

    def test_import_and_parse_schedules(self):
        """Import raw data, apply mapping, parse schedules → SessionCourse with schedule."""
        mapping = _make_mapping()
        courses, errors = ImportParser.apply_mapping(RAW_DATA, mapping)
        assert len(errors) == 0
        assert len(courses) == 4

        # Parse schedule strings
        for c in courses:
            if isinstance(c.get("schedule"), str) and c["schedule"]:
                c["schedule"] = ScheduleParser.parse_schedule(c["schedule"], c.get("weeks"))
            c.pop("weeks", None)

        # Create SessionCourse objects
        session_courses = [SessionCourse(**c) for c in courses]
        assert all(sc.schedule for sc in session_courses)
        assert session_courses[0].schedule[0].day_of_week == 1  # Monday
        assert session_courses[0].schedule[0].start_period == time(8, 0)
        assert len(session_courses[0].schedule[0].weeks) == 16

    @pytest.mark.asyncio
    async def test_recommend_matches_by_name(self):
        """RecommendService should match LLM response by course name."""
        mapping = _make_mapping()
        courses, errors = ImportParser.apply_mapping(RAW_DATA, mapping)
        for c in courses:
            if isinstance(c.get("schedule"), str) and c["schedule"]:
                c["schedule"] = ScheduleParser.parse_schedule(c["schedule"], c.get("weeks"))
            c.pop("weeks", None)
        session_courses = [SessionCourse(**c) for c in courses]

        # Mock LLM returning course names (common behavior)
        class NameLLM:
            async def generate_structured(self, messages, *, schema):
                return {
                    "reply": "推荐数学和英语课程",
                    "recommendations": [{
                        "plan_name": "基础方案",
                        "course_ids": ["高等数学", "大学英语"],
                        "reason": "基础课程",
                        "match_score": 90,
                    }],
                }

        db = AsyncMock()
        service = RecommendService(db, NameLLM(), session_courses=session_courses)
        result = await service.recommend("推荐课程")

        assert len(result["recommendations"]) == 1
        plan = result["recommendations"][0]
        assert len(plan.courses) == 2
        names = {c.name for c in plan.courses}
        assert "高等数学" in names
        assert "大学英语" in names

    @pytest.mark.asyncio
    async def test_recommend_matches_partial_name(self):
        """LLM returning '篮球' should match '体育（篮球）'."""
        mapping = _make_mapping()
        courses, errors = ImportParser.apply_mapping(RAW_DATA, mapping)
        for c in courses:
            if isinstance(c.get("schedule"), str) and c["schedule"]:
                c["schedule"] = ScheduleParser.parse_schedule(c["schedule"], c.get("weeks"))
            c.pop("weeks", None)
        session_courses = [SessionCourse(**c) for c in courses]

        class PartialLLM:
            async def generate_structured(self, messages, *, schema):
                return {
                    "reply": "推荐体育课程",
                    "recommendations": [{
                        "plan_name": "体育方案",
                        "course_ids": ["篮球"],
                        "reason": "推荐体育",
                        "match_score": 80,
                    }],
                }

        db = AsyncMock()
        service = RecommendService(db, PartialLLM(), session_courses=session_courses)
        result = await service.recommend("推荐体育课")

        assert len(result["recommendations"]) == 1
        assert result["recommendations"][0].courses[0].name == "体育（篮球）"

    @pytest.mark.asyncio
    async def test_recommend_matches_by_course_no(self):
        """LLM returning course code should match."""
        mapping = _make_mapping()
        courses, errors = ImportParser.apply_mapping(RAW_DATA, mapping)
        for c in courses:
            if isinstance(c.get("schedule"), str) and c["schedule"]:
                c["schedule"] = ScheduleParser.parse_schedule(c["schedule"], c.get("weeks"))
            c.pop("weeks", None)
        session_courses = [SessionCourse(**c) for c in courses]

        class CodeLLM:
            async def generate_structured(self, messages, *, schema):
                return {
                    "reply": "推荐CS课程",
                    "recommendations": [{
                        "plan_name": "编程方案",
                        "course_ids": ["CS101"],
                        "reason": "学习编程",
                        "match_score": 95,
                    }],
                }

        db = AsyncMock()
        service = RecommendService(db, CodeLLM(), session_courses=session_courses)
        result = await service.recommend("推荐编程课")

        assert len(result["recommendations"]) == 1
        assert result["recommendations"][0].courses[0].course_no == "CS101"

    @pytest.mark.asyncio
    async def test_conflict_detection_with_schedules(self):
        """Two courses at same time should produce a conflict."""
        overlapping_data = [
            {
                "课程名称": "课程A",
                "学分": "3.0",
                "课程编码": "A001",
                "星期节次": "周一(1-2)",
                "开课周": "第1-12周",
            },
            {
                "课程名称": "课程B",
                "学分": "3.0",
                "课程编码": "B001",
                "星期节次": "周一(1-2)",
                "开课周": "第1-12周",
            },
        ]
        mapping = MappingResult(
            mappings=[
                ColumnMapping(source="课程名称", target="name", confidence=0.95),
                ColumnMapping(source="学分", target="credit", confidence=0.95),
                ColumnMapping(source="课程编码", target="course_no", confidence=0.9),
                ColumnMapping(source="星期节次", target="schedule", confidence=0.9),
                ColumnMapping(source="开课周", target="weeks", confidence=0.9),
            ],
            unmapped_source=[],
            unmapped_target=[],
        )
        courses, _ = ImportParser.apply_mapping(overlapping_data, mapping)
        for c in courses:
            if isinstance(c.get("schedule"), str) and c["schedule"]:
                c["schedule"] = ScheduleParser.parse_schedule(c["schedule"], c.get("weeks"))
            c.pop("weeks", None)
        session_courses = [SessionCourse(**c) for c in courses]

        class ConflictLLM:
            async def generate_structured(self, messages, *, schema):
                return {
                    "reply": "推荐两门课",
                    "recommendations": [{
                        "plan_name": "冲突方案",
                        "course_ids": ["课程A", "课程B"],
                        "reason": "都选",
                        "match_score": 50,
                    }],
                }

        db = AsyncMock()
        service = RecommendService(db, ConflictLLM(), session_courses=session_courses)
        result = await service.recommend("推荐课程")

        assert len(result["recommendations"]) == 1
        plan = result["recommendations"][0]
        assert len(plan.conflicts) > 0, "Should detect time conflict"
        assert "时间冲突" in plan.conflicts[0].message or "overlap" in plan.conflicts[0].message.lower()

    @pytest.mark.asyncio
    async def test_no_conflict_different_days(self):
        """Courses on different days should have no conflicts."""
        non_overlapping = [
            {
                "课程名称": "课程A",
                "学分": "3.0",
                "课程编码": "A001",
                "星期节次": "周一(1-2)",
                "开课周": "第1-12周",
            },
            {
                "课程名称": "课程B",
                "学分": "3.0",
                "课程编码": "B001",
                "星期节次": "周二(1-2)",
                "开课周": "第1-12周",
            },
        ]
        mapping = MappingResult(
            mappings=[
                ColumnMapping(source="课程名称", target="name", confidence=0.95),
                ColumnMapping(source="学分", target="credit", confidence=0.95),
                ColumnMapping(source="课程编码", target="course_no", confidence=0.9),
                ColumnMapping(source="星期节次", target="schedule", confidence=0.9),
                ColumnMapping(source="开课周", target="weeks", confidence=0.9),
            ],
            unmapped_source=[],
            unmapped_target=[],
        )
        courses, _ = ImportParser.apply_mapping(non_overlapping, mapping)
        for c in courses:
            if isinstance(c.get("schedule"), str) and c["schedule"]:
                c["schedule"] = ScheduleParser.parse_schedule(c["schedule"], c.get("weeks"))
            c.pop("weeks", None)
        session_courses = [SessionCourse(**c) for c in courses]

        class NoConflictLLM:
            async def generate_structured(self, messages, *, schema):
                return {
                    "reply": "推荐两门课",
                    "recommendations": [{
                        "plan_name": "无冲突方案",
                        "course_ids": ["课程A", "课程B"],
                        "reason": "时间不冲突",
                        "match_score": 90,
                    }],
                }

        db = AsyncMock()
        service = RecommendService(db, NoConflictLLM(), session_courses=session_courses)
        result = await service.recommend("推荐课程")

        assert len(result["recommendations"]) == 1
        plan = result["recommendations"][0]
        assert len(plan.conflicts) == 0, "Should have no conflicts"

    @pytest.mark.asyncio
    async def test_session_store_integration(self):
        """Full flow: import → store → retrieve → recommend."""
        mapping = _make_mapping()
        courses, errors = ImportParser.apply_mapping(RAW_DATA, mapping)
        for c in courses:
            if isinstance(c.get("schedule"), str) and c["schedule"]:
                c["schedule"] = ScheduleParser.parse_schedule(c["schedule"], c.get("weeks"))
            c.pop("weeks", None)
        session_courses = [SessionCourse(**c) for c in courses]

        # Store in SessionStore
        device_id = "test-pipeline-device"
        SessionStore.clear(device_id)
        SessionStore.set_courses(device_id, session_courses)

        # Retrieve
        stored = SessionStore.get_courses(device_id)
        assert stored is not None
        assert len(stored) == 4
        assert all(sc.schedule for sc in stored)

        # Recommend
        class PipelineLLM:
            async def generate_structured(self, messages, *, schema):
                return {
                    "reply": "推荐数学",
                    "recommendations": [{
                        "plan_name": "方案",
                        "course_ids": [stored[0].id],
                        "reason": "匹配",
                        "match_score": 90,
                    }],
                }

        db = AsyncMock()
        service = RecommendService(db, PipelineLLM(), session_courses=stored)
        result = await service.recommend("推荐数学课")
        assert len(result["recommendations"]) == 1

        SessionStore.clear(device_id)
