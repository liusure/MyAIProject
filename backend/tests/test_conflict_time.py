"""Tests for detect_time_conflicts — pure function, no dependencies."""
import uuid

from src.services.conflict.time import detect_time_conflicts


def _course(name, day, start, end, weeks=None, campus="主校区"):
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "credit": 3.0,
        "schedule": [
            {
                "day_of_week": day,
                "start_period": start,
                "end_period": end,
                "weeks": weeks or list(range(1, 17)),
            }
        ],
        "campus": campus,
    }


class TestDetectTimeConflicts:
    def test_no_conflict_different_days(self):
        courses = [
            _course("A", 1, "1", "2"),
            _course("B", 2, "1", "2"),
        ]
        assert detect_time_conflicts(courses) == []

    def test_overlap_same_time(self):
        courses = [
            _course("A", 1, "1", "2"),
            _course("B", 1, "1", "2"),
        ]
        conflicts = detect_time_conflicts(courses)
        assert len(conflicts) == 1
        assert conflicts[0].type == "time"
        assert conflicts[0].severity == "error"

    def test_partial_overlap(self):
        courses = [
            _course("A", 1, "1", "2"),
            _course("B", 1, "2", "10:40"),
        ]
        conflicts = detect_time_conflicts(courses)
        assert len(conflicts) == 1

    def test_adjacent_no_conflict(self):
        # A ends at 09:40, B starts at 09:40 → no overlap
        courses = [
            _course("A", 1, "1", "2"),
            _course("B", 1, "2", "11:20"),
        ]
        assert detect_time_conflicts(courses) == []

    def test_no_overlap_different_weeks(self):
        courses = [
            _course("A", 1, "1", "2", weeks=[1, 2, 3]),
            _course("B", 1, "1", "2", weeks=[8, 9, 10]),
        ]
        assert detect_time_conflicts(courses) == []

    def test_overlap_shared_weeks(self):
        courses = [
            _course("A", 1, "1", "2", weeks=[1, 2, 3]),
            _course("B", 1, "1", "2", weeks=[3, 4, 5]),
        ]
        conflicts = detect_time_conflicts(courses)
        assert len(conflicts) == 1

    def test_empty_list(self):
        assert detect_time_conflicts([]) == []

    def test_single_course(self):
        assert detect_time_conflicts([_course("A", 1, "1", "2")]) == []

    def test_three_courses_two_overlap(self):
        courses = [
            _course("A", 1, "1", "2"),
            _course("B", 1, "2", "10:40"),
            _course("C", 3, "1", "2"),
        ]
        conflicts = detect_time_conflicts(courses)
        assert len(conflicts) == 1
        assert str(conflicts[0].course_a) == courses[0]["id"]
        assert str(conflicts[0].course_b) == courses[1]["id"]

    def test_message_contains_course_names(self):
        courses = [
            _course("高等数学", 1, "1", "2"),
            _course("线性代数", 1, "1", "2"),
        ]
        conflicts = detect_time_conflicts(courses)
        assert "高等数学" in conflicts[0].message
        assert "线性代数" in conflicts[0].message
