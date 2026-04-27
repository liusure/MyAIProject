from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.course import Course
from src.schemas.course import CourseResponse


class CourseSearchService:
    """课程搜索服务（降级方案）"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search(self, query: str, semester: str | None = None, category: str | None = None) -> list[CourseResponse]:
        stmt = select(Course).where(Course.is_active == True)

        if semester:
            stmt = stmt.where(Course.semester == semester)
        if category:
            stmt = stmt.where(Course.category == category)

        # 关键词搜索：匹配课程名称、编号、教师
        stmt = stmt.where(
            Course.name.ilike(f"%{query}%")
            | Course.course_no.ilike(f"%{query}%")
            | Course.instructor.ilike(f"%{query}%")
            | Course.description.ilike(f"%{query}%")
        )

        result = await self.db.execute(stmt)
        courses = result.scalars().all()
        return [CourseResponse.model_validate(c) for c in courses]
