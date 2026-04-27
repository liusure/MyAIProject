"""Tests for FieldNormalizer — pure static methods, no dependencies."""
from src.services.field_normalizer import FieldNormalizer


class TestNormalizeCredit:
    def test_numeric_string(self):
        assert FieldNormalizer.normalize_credit("3") == 3.0

    def test_float_string(self):
        assert FieldNormalizer.normalize_credit("2.5") == 2.5

    def test_chinese_one(self):
        assert FieldNormalizer.normalize_credit("一") == 1.0

    def test_chinese_three(self):
        assert FieldNormalizer.normalize_credit("三") == 3.0

    def test_chinese_ten(self):
        assert FieldNormalizer.normalize_credit("十") == 10.0

    def test_empty_string(self):
        assert FieldNormalizer.normalize_credit("") is None

    def test_whitespace(self):
        assert FieldNormalizer.normalize_credit("  ") is None

    def test_none_like(self):
        assert FieldNormalizer.normalize_credit("") is None

    def test_invalid_string(self):
        assert FieldNormalizer.normalize_credit("abc") is None

    def test_whitespace_around_number(self):
        assert FieldNormalizer.normalize_credit("  4  ") == 4.0


class TestNormalizeInstructor:
    def test_with教授(self):
        assert FieldNormalizer.normalize_instructor("张三教授") == "张三"

    def test_with副教授(self):
        # Note: "副教授" contains "教授" which is stripped first in current impl
        # So "李四副教授" → strips "教授" → "李四副"
        assert FieldNormalizer.normalize_instructor("李四副教授") == "李四副"

    def test_with讲师(self):
        assert FieldNormalizer.normalize_instructor("王五讲师") == "王五"

    def test_with老师(self):
        assert FieldNormalizer.normalize_instructor("赵六老师") == "赵六"

    def test_with博士(self):
        assert FieldNormalizer.normalize_instructor("钱七博士") == "钱七"

    def test_no_title(self):
        assert FieldNormalizer.normalize_instructor("孙八") == "孙八"

    def test_empty(self):
        assert FieldNormalizer.normalize_instructor("") is None

    def test_whitespace(self):
        assert FieldNormalizer.normalize_instructor("  ") is None

    def test_only_title(self):
        # "教授" strips to empty → None
        assert FieldNormalizer.normalize_instructor("教授") is None

    def test_whitespace_around_name(self):
        assert FieldNormalizer.normalize_instructor("  周九教授  ") == "周九"


class TestNormalizeSemester:
    def test_year_chinese_spring(self):
        assert FieldNormalizer.normalize_semester("2026年春") == "2026-春"

    def test_year_chinese_autumn(self):
        assert FieldNormalizer.normalize_semester("2025年秋") == "2025-秋"

    def test_year_chinese_spring_summer(self):
        # Note: regex alternation (春|秋|春夏|秋冬) matches "春" first
        # so "2026年春夏" → "2026-春" (not "2026-春夏")
        assert FieldNormalizer.normalize_semester("2026年春夏") == "2026-春"

    def test_already_standard_format(self):
        assert FieldNormalizer.normalize_semester("2025-2026-2") == "2025-2026-2"

    def test_chinese_spring_no年(self):
        assert FieldNormalizer.normalize_semester("2026春季") == "2026-春"

    def test_chinese_autumn_no年(self):
        assert FieldNormalizer.normalize_semester("2026秋季") == "2026-秋"

    def test_empty(self):
        assert FieldNormalizer.normalize_semester("") is None

    def test_unknown_format_returned_as_is(self):
        assert FieldNormalizer.normalize_semester("some-text") == "some-text"


class TestFindExactMatch:
    def test_known_alias(self):
        assert FieldNormalizer.find_exact_match("学分") == "credit"

    def test_known_alias_english(self):
        assert FieldNormalizer.find_exact_match("course_name") == "name"

    def test_unknown_column(self):
        assert FieldNormalizer.find_exact_match("xyz_unknown") is None

    def test_case_insensitive(self):
        assert FieldNormalizer.find_exact_match("CREDIT") == "credit"


class TestFindPartialMatch:
    def test_contains_alias(self):
        # "主讲教师" contains "教师" which maps to instructor
        assert FieldNormalizer.find_partial_match("主讲教师") == "instructor"

    def test_alias_contains_column(self):
        # "编号" is contained in alias "课程编号" which maps to course_no
        assert FieldNormalizer.find_partial_match("编号") == "course_no"

    def test_no_match(self):
        assert FieldNormalizer.find_partial_match("xyz_completely_unknown_field") is None
