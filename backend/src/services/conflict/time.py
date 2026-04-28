from src.schemas.plan import ConflictItem


def detect_time_conflicts(courses: list[dict]) -> list[ConflictItem]:
    """检测时间冲突：课程时间段重叠"""
    conflicts = []
    for i, a in enumerate(courses):
        for b in courses[i + 1:]:
            # Skip comparing a course with itself (same id)
            if a.get("id") == b.get("id"):
                continue
            for slot_a in a.get("schedule", []):
                for slot_b in b.get("schedule", []):
                    if _slots_overlap(slot_a, slot_b):
                        conflicts.append(ConflictItem(
                            type="time",
                            severity="error",
                            course_a=a["id"],
                            course_b=b["id"],
                            message=f"时间冲突：{a['name']} 与 {b['name']} 在 {_day_name(slot_a['day_of_week'])} 第{slot_a['start_period']}-{slot_a['end_period']}节 重叠",
                        ))
    return conflicts


def _slots_overlap(a: dict, b: dict) -> bool:
    if a["day_of_week"] != b["day_of_week"]:
        return False
    a_weeks = set(a.get("weeks", []))
    b_weeks = set(b.get("weeks", []))
    if a_weeks and b_weeks and not (a_weeks & b_weeks):
        return False
    return a["start_period"] < b["end_period"] and b["start_period"] < a["end_period"]


def _day_name(day: int) -> str:
    return ["", "周一", "周二", "周三", "周四", "周五", "周六", "周日"][day]
