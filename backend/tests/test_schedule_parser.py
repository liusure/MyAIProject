"""Tests for ScheduleParser."""
import pytest

from src.services.schedule_parser import ScheduleParser


class TestParseWeeks:
    def test_basic_range(self):
        assert ScheduleParser.parse_weeks("第1-12周") == list(range(1, 13))

    def test_short_range(self):
        assert ScheduleParser.parse_weeks("第1-8周") == list(range(1, 9))

    def test_single_week(self):
        assert ScheduleParser.parse_weeks("第5周") == [5]

    def test_comma_separated(self):
        result = ScheduleParser.parse_weeks("第1-5,7-9,11周")
        assert result == [1, 2, 3, 4, 5, 7, 8, 9, 11]

    def test_chinese_comma(self):
        result = ScheduleParser.parse_weeks("第1-5，7-9周")
        assert result == [1, 2, 3, 4, 5, 7, 8, 9]

    def test_empty_string(self):
        assert ScheduleParser.parse_weeks("") == []
        assert ScheduleParser.parse_weeks(None) == []

    def test_deduplicates(self):
        result = ScheduleParser.parse_weeks("第1-3,2-4周")
        assert result == [1, 2, 3, 4]


class TestParseSchedule:
    def test_basic_monday(self):
        items = ScheduleParser.parse_schedule("周一(7-8)", "第1-12周")
        assert len(items) == 1
        assert items[0].day_of_week == 1
        assert len(items[0].weeks) == 12

    def test_tuesday(self):
        items = ScheduleParser.parse_schedule("周二(1-2)", "第1-16周")
        assert len(items) == 1
        assert items[0].day_of_week == 2

    def test_sunday(self):
        items = ScheduleParser.parse_schedule("周日(10-12)", "第1-8周")
        assert len(items) == 1
        assert items[0].day_of_week == 7

    def test_three_periods(self):
        items = ScheduleParser.parse_schedule("周二(5-7)", "第1-8周")
        assert len(items) == 1
        assert items[0].start_period.hour == 14  # period 5
        assert items[0].end_period.hour >= 15

    def test_empty_schedule(self):
        assert ScheduleParser.parse_schedule("", "第1-12周") == []
        assert ScheduleParser.parse_schedule(None, "第1-12周") == []

    def test_no_weeks(self):
        items = ScheduleParser.parse_schedule("周一(7-8)")
        assert len(items) == 1
        assert items[0].weeks == []

    def test_times_are_set(self):
        items = ScheduleParser.parse_schedule("周一(1-2)", "第1-8周")
        assert items[0].start_period is not None
        assert items[0].end_period is not None
        assert items[0].start_period < items[0].end_period
