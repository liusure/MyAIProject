"""Tests for ImportAnalyzer — non-LLM methods only."""
import pytest

from src.schemas.import_result import (
    ColumnMapping,
    DegradationImpact,
    MappingResult,
)
from src.services.import_analyzer import ImportAnalyzer, DEGRADATION_IMPACTS, SYSTEM_FIELDS_DESC


class TestReadRaw:
    def test_csv(self):
        content = b"name,credit\nMath,3\nPhysics,4"
        data, columns = ImportAnalyzer._read_raw(content, "test.csv")
        assert columns == ["name", "credit"]
        assert len(data) == 2
        assert data[0]["name"] == "Math"

    def test_csv_with_none_values(self):
        import math

        content = b"name,credit\nMath,\n,4"
        data, columns = ImportAnalyzer._read_raw(content, "test.csv")
        # Empty CSV cell may become NaN or None depending on pandas version
        assert data[0]["credit"] is None or (isinstance(data[0]["credit"], float) and math.isnan(data[0]["credit"]))
        assert data[1]["name"] is None or data[1]["name"] == "" or (isinstance(data[1]["name"], float) and math.isnan(data[1]["name"]))

    def test_unsupported_format(self):
        with pytest.raises(ValueError, match="不支持"):
            ImportAnalyzer._read_raw(b"data", "test.pdf")


class TestSplitCompoundHeaders:
    def test_simple_headers_no_split(self):
        raw = [{"name": "Math", "credit": "3"}]
        columns = ["name", "credit"]
        new_raw, new_cols = ImportAnalyzer._split_compound_headers(raw, columns)
        assert new_cols == ["name", "credit"]
        assert new_raw == raw

    def test_compound_header_split(self):
        raw = [{"课时/学分": "48/3"}]
        columns = ["课时/学分"]
        new_raw, new_cols = ImportAnalyzer._split_compound_headers(raw, columns)
        assert "课时" in new_cols
        assert "学分" in new_cols
        assert new_raw[0]["课时"] == "48"
        assert new_raw[0]["学分"] == "3"

    def test_compound_header_no_slash_value(self):
        raw = [{"课时/学分": "3"}]
        columns = ["课时/学分"]
        new_raw, new_cols = ImportAnalyzer._split_compound_headers(raw, columns)
        assert new_raw[0]["课时"] == "3"
        assert new_raw[0]["学分"] is None

    def test_mixed_headers(self):
        raw = [{"name": "Math", "课时/学分": "48/3"}]
        columns = ["name", "课时/学分"]
        new_raw, new_cols = ImportAnalyzer._split_compound_headers(raw, columns)
        assert "name" in new_cols
        assert "课时" in new_cols
        assert "学分" in new_cols

    def test_url_not_split(self):
        raw = [{"link": "http://example.com"}]
        columns = ["link"]
        new_raw, new_cols = ImportAnalyzer._split_compound_headers(raw, columns)
        assert new_cols == ["link"]


class TestDeduplicateMapping:
    def test_no_duplicates(self):
        mapping = MappingResult(
            mappings=[
                ColumnMapping(source="课程名称", target="name", confidence=0.9),
                ColumnMapping(source="学分", target="credit", confidence=0.9),
            ]
        )
        result = ImportAnalyzer._deduplicate_mapping(mapping)
        assert len(result.mappings) == 2

    def test_duplicates_keeps_best(self):
        mapping = MappingResult(
            mappings=[
                ColumnMapping(source="课时", target="credit", confidence=0.5),
                ColumnMapping(source="学分", target="credit", confidence=0.5),
            ]
        )
        result = ImportAnalyzer._deduplicate_mapping(mapping)
        assert len(result.mappings) == 1
        # "学分" is a closer match to credit aliases
        assert result.mappings[0].source == "学分"

    def test_populates_unmapped_targets(self):
        mapping = MappingResult(
            mappings=[
                ColumnMapping(source="课程名称", target="name", confidence=0.9),
            ]
        )
        result = ImportAnalyzer._deduplicate_mapping(mapping)
        # credit and other fields should be in unmapped_target
        assert "credit" in result.unmapped_target


class TestBuildDegradationReport:
    def test_empty_unmapped(self):
        mapping = MappingResult(mappings=[], unmapped_target=[])
        report = ImportAnalyzer.build_degradation_report(mapping)
        assert report.missing_fields == []

    def test_with_unmapped_optional(self):
        mapping = MappingResult(mappings=[], unmapped_target=["campus", "instructor"])
        report = ImportAnalyzer.build_degradation_report(mapping)
        assert "campus" in report.missing_fields
        assert "instructor" in report.missing_fields

    def test_ignores_required_fields(self):
        # name and credit should not appear in degradation
        mapping = MappingResult(mappings=[], unmapped_target=["name", "credit"])
        report = ImportAnalyzer.build_degradation_report(mapping)
        assert report.missing_fields == []


class TestEmptyMapping:
    def test_returns_all_unmapped(self):
        columns = ["课程名称", "学分", "教师"]
        result = ImportAnalyzer._empty_mapping(columns)
        assert result.mappings == []
        assert result.unmapped_source == columns
        assert len(result.unmapped_target) == len(SYSTEM_FIELDS_DESC)
