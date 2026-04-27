"""Tests for RuleValidator — class methods, pure logic."""
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from src.services.rule_validator import RuleValidator


def _make_rule(min_credits=10, max_credits=25, start=None, end=None):
    rule = MagicMock()
    rule.min_credits = min_credits
    rule.max_credits = max_credits
    rule.enrollment_start = start or datetime(2026, 3, 1)
    rule.enrollment_end = end or datetime(2026, 6, 30)
    return rule


class TestValidateCredits:
    def test_within_range(self):
        rule = _make_rule(10, 25)
        assert RuleValidator.validate_credits(15.0, rule) == []

    def test_above_max(self):
        rule = _make_rule(10, 25)
        errors = RuleValidator.validate_credits(30.0, rule)
        assert len(errors) == 1
        assert "超过上限" in errors[0]

    def test_below_min(self):
        rule = _make_rule(10, 25)
        errors = RuleValidator.validate_credits(5.0, rule)
        assert len(errors) == 1
        assert "低于下限" in errors[0]

    def test_at_max_boundary(self):
        rule = _make_rule(10, 25)
        assert RuleValidator.validate_credits(25.0, rule) == []

    def test_at_min_boundary(self):
        rule = _make_rule(10, 25)
        assert RuleValidator.validate_credits(10.0, rule) == []


class TestValidateEnrollmentPeriod:
    def test_within_period(self):
        rule = _make_rule()
        now = datetime(2026, 4, 15)
        assert RuleValidator.validate_enrollment_period(rule, now) == []

    def test_before_start(self):
        rule = _make_rule()
        now = datetime(2026, 2, 1)
        errors = RuleValidator.validate_enrollment_period(rule, now)
        assert len(errors) == 1
        assert "尚未开始" in errors[0]

    def test_after_end(self):
        rule = _make_rule()
        now = datetime(2026, 7, 1)
        errors = RuleValidator.validate_enrollment_period(rule, now)
        assert len(errors) == 1
        assert "已结束" in errors[0]

    def test_at_start_boundary(self):
        rule = _make_rule()
        now = datetime(2026, 3, 1)
        assert RuleValidator.validate_enrollment_period(rule, now) == []

    def test_at_end_boundary(self):
        rule = _make_rule()
        now = datetime(2026, 6, 30)
        assert RuleValidator.validate_enrollment_period(rule, now) == []
