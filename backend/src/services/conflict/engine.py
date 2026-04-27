import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.plan import ConflictItem
from src.services.conflict.time import detect_time_conflicts
from src.services.conflict.prerequisite import detect_prerequisite_conflicts
from src.services.conflict.commute import detect_commute_conflicts


class ConflictEngine:
    """冲突检测引擎入口"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def detect(
        self,
        courses: list[dict],
        completed_course_ids: set[uuid.UUID] | None = None,
    ) -> list[ConflictItem]:
        """运行所有冲突检测器"""
        conflicts: list[ConflictItem] = []

        # 时间冲突
        conflicts.extend(detect_time_conflicts(courses))

        # 先修冲突
        conflicts.extend(await detect_prerequisite_conflicts(self.db, courses, completed_course_ids))

        # 通勤冲突
        conflicts.extend(detect_commute_conflicts(courses))

        return conflicts
