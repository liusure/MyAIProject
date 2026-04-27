import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.prerequisite import Prerequisite
from src.schemas.plan import ConflictItem


async def detect_prerequisite_conflicts(
    db: AsyncSession,
    courses: list[dict],
    completed_course_ids: set[uuid.UUID] | None = None,
) -> list[ConflictItem]:
    """检测先修课程冲突：有向图检测"""
    completed = completed_course_ids or set()
    course_ids = {c["id"] for c in courses}
    course_map = {c["id"]: c for c in courses}

    # 获取所有相关先修关系
    result = await db.execute(
        select(Prerequisite).where(Prerequisite.course_id.in_(course_ids))
    )
    prereqs = result.scalars().all()

    conflicts = []
    for p in prereqs:
        if p.prerequisite_course_id not in completed and p.prerequisite_course_id not in course_ids:
            prereq_course = course_map.get(str(p.course_id), {})
            conflicts.append(ConflictItem(
                type="prerequisite",
                severity="warning",
                course_a=p.course_id,
                course_b=p.prerequisite_course_id,
                message=f"先修要求：{prereq_course.get('name', '未知课程')} 需要先修课程但未满足",
            ))

    return conflicts
