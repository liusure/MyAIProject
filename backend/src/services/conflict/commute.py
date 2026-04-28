from src.schemas.plan import ConflictItem

# 校区间最短通勤时间（分钟）
CAMPUS_COMMUTE: dict[tuple[str, str], int] = {
    ("主校区", "东校区"): 15,
    ("主校区", "西校区"): 10,
    ("主校区", "南校区"): 20,
    ("东校区", "西校区"): 25,
    ("东校区", "南校区"): 15,
    ("西校区", "南校区"): 30,
}

MIN_COMMUTE_GAP = 15  # 最少休息时间（分钟）


def detect_commute_conflicts(courses: list[dict]) -> list[ConflictItem]:
    """检测通勤冲突：校区距离 + 时间间隔"""
    conflicts = []
    for i, a in enumerate(courses):
        for b in courses[i + 1:]:
            # Skip comparing a course with itself (same id)
            if a.get("id") == b.get("id"):
                continue
            for slot_a in a.get("schedule", []):
                for slot_b in b.get("schedule", []):
                    if slot_a["day_of_week"] != slot_b["day_of_week"]:
                        continue
                    campus_a = a.get("campus", "")
                    campus_b = b.get("campus", "")
                    if campus_a == campus_b:
                        continue
                    commute_time = _get_commute_time(campus_a, campus_b)
                    if commute_time is None:
                        continue
                    gap = _period_gap_minutes(slot_a["end_period"], slot_b["start_period"])
                    if gap is not None and 0 <= gap < commute_time + MIN_COMMUTE_GAP:
                        conflicts.append(ConflictItem(
                            type="commute",
                            severity="warning",
                            course_a=a["id"],
                            course_b=b["id"],
                            message=f"通勤冲突：{a['name']}（{campus_a}）结束后仅 {gap} 分钟，不足以赶到 {b['name']}（{campus_b}），最少需要 {commute_time + MIN_COMMUTE_GAP} 分钟",
                        ))
    return conflicts


def _get_commute_time(campus_a: str, campus_b: str) -> int | None:
    return CAMPUS_COMMUTE.get((campus_a, campus_b)) or CAMPUS_COMMUTE.get((campus_b, campus_a))


def _period_gap_minutes(end_period: int, start_period: int) -> int | None:
    """估算两节课之间的间隔分钟数（每节约50分钟含休息）"""
    if start_period <= end_period:
        return None
    return (start_period - end_period) * 50
