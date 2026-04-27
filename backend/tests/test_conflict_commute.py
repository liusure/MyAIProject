"""Tests for detect_commute_conflicts — pure function, no dependencies."""
import uuid

from src.services.conflict.commute import detect_commute_conflicts, _time_gap_minutes, _get_commute_time


def _course(name, campus, day, start, end):
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "credit": 3.0,
        "schedule": [
            {
                "day_of_week": day,
                "start_period": start,
                "end_period": end,
                "weeks": list(range(1, 17)),
            }
        ],
        "campus": campus,
    }


class TestDetectCommuteConflicts:
    def test_no_conflict_same_campus(self):
        courses = [
            _course("A", "主校区", 1, "1", "2"),
            _course("B", "主校区", 1, "3", "4"),
        ]
        assert detect_commute_conflicts(courses) == []

    def test_no_conflict_different_days(self):
        courses = [
            _course("A", "主校区", 1, "1", "2"),
            _course("B", "东校区", 2, "3", "4"),
        ]
        assert detect_commute_conflicts(courses) == []

    def test_conflict_insufficient_gap(self):
        # 主校区→东校区 needs 15min commute + 15min rest = 30min
        # A ends 09:40, B starts 10:00 → gap=20min < 30min → conflict
        courses = [
            _course("A", "主校区", 1, "1", "2"),
            _course("B", "东校区", 1, "3", "4"),
        ]
        conflicts = detect_commute_conflicts(courses)
        assert len(conflicts) == 1
        assert conflicts[0].type == "commute"
        assert conflicts[0].severity == "warning"

    def test_no_conflict_sufficient_gap(self):
        # A ends 09:40, B starts 11:00 → gap=80min >= 30min → no conflict
        courses = [
            _course("A", "主校区", 1, "1", "2"),
            _course("B", "东校区", 1, "3", "4"),
        ]
        assert detect_commute_conflicts(courses) == []

    def test_reverse_direction(self):
        # 东校区→主校区 also needs 15min
        courses = [
            _course("A", "东校区", 1, "1", "2"),
            _course("B", "主校区", 1, "3", "4"),
        ]
        conflicts = detect_commute_conflicts(courses)
        assert len(conflicts) == 1

    def test_unknown_campus_pair(self):
        courses = [
            _course("A", "未知校区", 1, "1", "2"),
            _course("B", "另一个未知", 1, "3", "4"),
        ]
        assert detect_commute_conflicts(courses) == []

    def test_empty_list(self):
        assert detect_commute_conflicts([]) == []

    def test_message_contains_details(self):
        courses = [
            _course("高等数学", "主校区", 1, "1", "2"),
            _course("物理实验", "东校区", 1, "3", "4"),
        ]
        conflicts = detect_commute_conflicts(courses)
        assert "通勤冲突" in conflicts[0].message
        assert "主校区" in conflicts[0].message
        assert "东校区" in conflicts[0].message


class TestTimeGapMinutes:
    def test_basic(self):
        assert _time_gap_minutes("2", "3") == 20

    def test_one_hour(self):
        assert _time_gap_minutes("2", "3") == 60

    def test_same_time(self):
        assert _time_gap_minutes("3", "3") == 0

    def test_negative(self):
        # B starts before A ends
        assert _time_gap_minutes("3", "2") == -60

    def test_invalid(self):
        assert _time_gap_minutes("invalid", "3") is None


class TestGetCommuteTime:
    def test_known_pair(self):
        assert _get_commute_time("主校区", "东校区") == 15

    def test_reverse(self):
        assert _get_commute_time("东校区", "主校区") == 15

    def test_unknown_pair(self):
        assert _get_commute_time("未知A", "未知B") is None
