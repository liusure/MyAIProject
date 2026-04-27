"""Field normalization: algorithmic processing for deterministic fields (no LLM)."""
import re


class FieldDefinition:
    def __init__(self, label: str, aliases: list[str], required: bool) -> None:
        self.label = label
        self.aliases = [a.lower() for a in aliases]
        self.required = required


FIELD_DEFINITIONS: dict[str, FieldDefinition] = {
    "name": FieldDefinition("课程名称", [
        "课程名称", "课程名", "course", "name", "课程", "course_name",
        "中文名称", "课程标题", "科目名称", "英文名称",
    ], True),
    "credit": FieldDefinition("学分", [
        "学分", "credit", "credits", "score", "课时/学分", "学时/学分",
    ], True),
    "course_no": FieldDefinition("课程编号", [
        "课程编号", "编号", "code", "course_no", "course_code", "id",
        "序号", "课程编码", "课程号", "课号", "课程代码",
    ], False),
    "instructor": FieldDefinition("主讲人", [
        "主讲人", "教师", "老师", "instructor", "teacher", "lecturer",
        "主讲教师", "首席教授", "授课教师", "任课教师", "任课老师",
    ], False),
    "capacity": FieldDefinition("容量", [
        "容量", "名额", "capacity", "seats", "max_students",
        "限选人数", "选课人数", "人数限制", "最大人数",
    ], False),
    "location": FieldDefinition("上课地点", [
        "上课地点", "地点", "教室", "location", "room", "classroom",
        "教学楼", "上课教室", "授课地点",
    ], False),
    "campus": FieldDefinition("校区", [
        "校区", "campus", "area", "院区",
    ], False),
    "category": FieldDefinition("分类", [
        "分类", "类别", "category", "type", "kind",
        "课程属性", "课程类型", "课程分类", "课程性质",
    ], False),
    "semester": FieldDefinition("学期", [
        "学期", "semester", "term", "学年学期", "开课学期",
    ], False),
    "schedule": FieldDefinition("上课时间", [
        "上课时间", "时间", "schedule", "time", "上课安排",
        "星期节次", "开课时间", "上课节次", "节次",
    ], False),
    "weeks": FieldDefinition("开课周", [
        "开课周", "周次", "weeks", "教学周",
    ], False),
}

CHINESE_CREDIT_MAP: dict[str, float] = {
    "零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
}

INSTRUCTOR_TITLES = ["教授", "副教授", "首席教授", "讲师", "助教", "老师", "博士", "研究员"]


class FieldNormalizer:
    """Algorithmic field normalization. No LLM calls."""

    @staticmethod
    def normalize_credit(value: str) -> float | None:
        """Convert credit value to float. Handles Chinese numbers."""
        if not value or not value.strip():
            return None
        value = value.strip()

        # Try direct numeric conversion
        try:
            return float(value)
        except ValueError:
            pass

        # Try Chinese number conversion
        if value in CHINESE_CREDIT_MAP:
            return float(CHINESE_CREDIT_MAP[value])

        return None

    @staticmethod
    def normalize_instructor(value: str) -> str | None:
        """Extract clean instructor name by stripping titles."""
        if not value or not value.strip():
            return None
        name = value.strip()
        for title in INSTRUCTOR_TITLES:
            name = name.replace(title, "")
        name = name.strip()
        return name if name else None

    @staticmethod
    def normalize_semester(value: str) -> str | None:
        """Normalize semester/term strings to standard format."""
        if not value or not value.strip():
            return None
        value = value.strip()

        # "2026年春" → "2026-春"
        m = re.match(r"(\d{4})年(春|秋|春夏|秋冬)", value)
        if m:
            return f"{m.group(1)}-{m.group(2)}"

        # "2025-2026-2" → "2025-2026-2" (keep as-is)
        m = re.match(r"\d{4}-\d{4}-\d", value)
        if m:
            return value

        # "2026春季" → "2026-春"
        m = re.match(r"(\d{4})春季", value)
        if m:
            return f"{m.group(1)}-春"

        # "2026秋季" → "2026-秋"
        m = re.match(r"(\d{4})秋季", value)
        if m:
            return f"{m.group(1)}-秋"

        return value

    @staticmethod
    def find_exact_match(column_name: str) -> str | None:
        """Try to match column name to a field definition by exact alias match."""
        col_lower = column_name.strip().lower()
        for field_key, definition in FIELD_DEFINITIONS.items():
            if col_lower in definition.aliases:
                return field_key
        return None

    @staticmethod
    def find_partial_match(column_name: str) -> str | None:
        """Try to match column name by checking if it contains an alias or alias contains it."""
        col_lower = column_name.strip().lower()
        best_match = None
        best_len = 0

        for field_key, definition in FIELD_DEFINITIONS.items():
            for alias in definition.aliases:
                # Column contains alias (e.g., "主讲教师" contains "教师")
                if alias in col_lower and len(alias) > best_len:
                    best_match = field_key
                    best_len = len(alias)
                # Alias contains column (e.g., alias "课程编号" contains column "编号")
                elif col_lower in alias and len(col_lower) > best_len:
                    best_match = field_key
                    best_len = len(col_lower)

        return best_match
