"""Tests for ImportParser — applies column mapping, pure logic with schema inputs."""
import pytest

from src.schemas.import_result import ColumnMapping, MappingResult
from src.services.import_parser import ImportParser


def _mapping(pairs: dict[str, str]) -> MappingResult:
    """Build MappingResult from {source: target} dict."""
    return MappingResult(
        mappings=[ColumnMapping(source=s, target=t, confidence=0.9) for s, t in pairs.items()]
    )


class TestApplyMapping:
    def test_basic_mapping(self):
        raw = [{"课程名称": "高等数学", "学分": "3"}]
        mapping = _mapping({"课程名称": "name", "学分": "credit"})
        courses, errors = ImportParser.apply_mapping(raw, mapping)
        assert len(errors) == 0
        assert len(courses) == 1
        assert courses[0]["name"] == "高等数学"
        assert courses[0]["credit"] == 3.0

    def test_chinese_credit(self):
        raw = [{"课程名称": "数学", "学分": "三"}]
        mapping = _mapping({"课程名称": "name", "学分": "credit"})
        courses, errors = ImportParser.apply_mapping(raw, mapping)
        assert len(errors) == 0
        assert courses[0]["credit"] == 3.0

    def test_invalid_credit_skips_row(self):
        raw = [{"课程名称": "数学", "学分": "abc"}]
        mapping = _mapping({"课程名称": "name", "学分": "credit"})
        courses, errors = ImportParser.apply_mapping(raw, mapping)
        assert len(courses) == 0
        assert len(errors) == 1
        assert "学分" in errors[0].message

    def test_missing_name_skips_row(self):
        raw = [{"课程名称": "", "学分": "3"}]
        mapping = _mapping({"课程名称": "name", "学分": "credit"})
        courses, errors = ImportParser.apply_mapping(raw, mapping)
        assert len(courses) == 0
        assert len(errors) == 1

    def test_instructor_normalization(self):
        raw = [{"课程名称": "数学", "学分": "3", "教师": "张三教授"}]
        mapping = _mapping({"课程名称": "name", "学分": "credit", "教师": "instructor"})
        courses, _ = ImportParser.apply_mapping(raw, mapping)
        assert courses[0]["instructor"] == "张三"

    def test_semester_normalization(self):
        raw = [{"课程名称": "数学", "学分": "3", "学期": "2026年春"}]
        mapping = _mapping({"课程名称": "name", "学分": "credit", "学期": "semester"})
        courses, _ = ImportParser.apply_mapping(raw, mapping)
        assert courses[0]["semester"] == "2026-春"

    def test_multiple_rows(self):
        raw = [
            {"课程名称": "数学", "学分": "3"},
            {"课程名称": "物理", "学分": "4"},
        ]
        mapping = _mapping({"课程名称": "name", "学分": "credit"})
        courses, errors = ImportParser.apply_mapping(raw, mapping)
        assert len(courses) == 2
        assert len(errors) == 0

    def test_ensures_optional_fields(self):
        raw = [{"课程名称": "数学", "学分": "3"}]
        mapping = _mapping({"课程名称": "name", "学分": "credit"})
        courses, _ = ImportParser.apply_mapping(raw, mapping)
        record = courses[0]
        # All optional fields should exist
        assert "course_no" in record
        assert "instructor" in record
        assert "schedule" in record
        assert record["schedule"] == []

    def test_empty_raw_data(self):
        mapping = _mapping({"课程名称": "name", "学分": "credit"})
        courses, errors = ImportParser.apply_mapping([], mapping)
        assert courses == []
        assert errors == []

    def test_weeks_field_kept_as_string(self):
        raw = [{"课程名称": "数学", "学分": "3", "开课周": "第1-12周"}]
        mapping = MappingResult(
            mappings=[
                ColumnMapping(source="课程名称", target="name", confidence=0.9),
                ColumnMapping(source="学分", target="credit", confidence=0.9),
                ColumnMapping(source="开课周", target="weeks", confidence=0.9),
            ],
            unmapped_source=[],
            unmapped_target=[],
        )
        courses, errors = ImportParser.apply_mapping(raw, mapping)
        assert len(courses) == 1
        assert courses[0]["weeks"] == "第1-12周"

    def test_schedule_string_kept_for_parsing(self):
        raw = [{"课程名称": "数学", "学分": "3", "星期节次": "周一(7-8)"}]
        mapping = MappingResult(
            mappings=[
                ColumnMapping(source="课程名称", target="name", confidence=0.9),
                ColumnMapping(source="学分", target="credit", confidence=0.9),
                ColumnMapping(source="星期节次", target="schedule", confidence=0.9),
            ],
            unmapped_source=[],
            unmapped_target=[],
        )
        courses, errors = ImportParser.apply_mapping(raw, mapping)
        assert len(courses) == 1
        assert courses[0]["schedule"] == "周一(7-8)"
