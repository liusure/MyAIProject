from datetime import datetime

from src.models.selection_rule import SelectionRule


class RuleValidator:
    """选课规则校验服务"""

    @classmethod
    def validate_credits(cls, total_credits: float, rule: SelectionRule) -> list[str]:
        """校验学分限制"""
        errors = []
        if total_credits > rule.max_credits:
            errors.append(f"总学分 {total_credits} 超过上限 {rule.max_credits}")
        if total_credits < rule.min_credits:
            errors.append(f"总学分 {total_credits} 低于下限 {rule.min_credits}")
        return errors

    @classmethod
    def validate_enrollment_period(cls, rule: SelectionRule, now: datetime | None = None) -> list[str]:
        """校验选课时段"""
        errors = []
        current = now or datetime.utcnow()
        if current < rule.enrollment_start:
            errors.append(f"选课尚未开始，开始时间：{rule.enrollment_start}")
        if current > rule.enrollment_end:
            errors.append(f"选课已结束，结束时间：{rule.enrollment_end}")
        return errors
