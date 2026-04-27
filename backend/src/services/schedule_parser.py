"""Schedule parser: converts Chinese schedule strings to ScheduleItem objects.

Handles formats like:
  - "周一(7-8)" → day=1, periods 7-8
  - "第1-12周" → weeks [1,2,...,12]
  - "第1-5,7-9,11周" → weeks [1,2,3,4,5,7,8,9,11]
"""
import re

from src.schemas.course import ScheduleItem

DAY_MAP: dict[str, int] = {
    "一": 1, "二": 2, "三": 3, "四": 4,
    "五": 5, "六": 6, "日": 7,
}


class ScheduleParser:
    """Parses Chinese schedule strings into structured ScheduleItem objects."""

    @classmethod
    def parse_schedule(cls, schedule_str: str, weeks_str: str | None = None) -> list[ScheduleItem]:
        """Parse schedule and week strings into ScheduleItem list.

        Args:
            schedule_str: e.g. "周一(7-8)" or "周一(1-2),周三(3-4)"
            weeks_str: e.g. "第1-12周" or None
        """
        if not schedule_str or not schedule_str.strip():
            return []

        weeks = cls.parse_weeks(weeks_str) if weeks_str else []

        # Split multiple schedule entries (comma or Chinese comma)
        entries = re.split(r"[,，]", schedule_str.strip())
        items = []
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue
            item = cls._parse_single_entry(entry, weeks)
            if item:
                items.append(item)
        return items

    @classmethod
    def _parse_single_entry(cls, entry: str, weeks: list[int]) -> ScheduleItem | None:
        """Parse a single entry like '周一(7-8)' into a ScheduleItem."""
        m = re.match(r"周([一二三四五六日])\((\d+)-(\d+)\)", entry)
        if not m:
            return None

        day_char = m.group(1)
        start_period = int(m.group(2))
        end_period = int(m.group(3))

        day_of_week = DAY_MAP.get(day_char)
        if day_of_week is None:
            return None

        return ScheduleItem(
            day_of_week=day_of_week,
            start_period=start_period,
            end_period=end_period,
            weeks=weeks,
        )

    @classmethod
    def parse_weeks(cls, weeks_str: str) -> list[int]:
        """Parse week string like '第1-12周' or '第1-5,7-9,11周' into list of ints."""
        if not weeks_str or not weeks_str.strip():
            return []

        # Remove "第" and "周"
        s = weeks_str.strip()
        s = re.sub(r"^第", "", s)
        s = re.sub(r"周$", "", s)

        weeks = []
        for part in re.split(r"[,，]", s):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                range_parts = part.split("-", 1)
                try:
                    start = int(range_parts[0])
                    end = int(range_parts[1])
                    weeks.extend(range(start, end + 1))
                except ValueError:
                    continue
            else:
                try:
                    weeks.append(int(part))
                except ValueError:
                    continue
        return sorted(set(weeks))
