import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.course import Course


class CourseImportService:
    """课程导入业务逻辑"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def import_courses(self, records: list[dict]) -> dict:
        """批量导入课程数据"""
        imported = 0
        failed = 0
        errors = []

        for i, record in enumerate(records):
            try:
                # 检查是否已存在
                existing = await self.db.execute(
                    select(Course).where(Course.course_no == record["course_no"])
                )
                if existing.scalar_one_or_none():
                    # 更新已有课程
                    course = existing.scalar_one()
                    for key, value in record.items():
                        if hasattr(course, key):
                            setattr(course, key, value)
                    course.updated_at = datetime.utcnow()
                else:
                    # 创建新课程
                    course = Course(
                        id=uuid.uuid4(),
                        schedule=[],  # 默认空时间表
                        is_active=True,
                        **record,
                    )
                    self.db.add(course)

                imported += 1
            except Exception as e:
                failed += 1
                errors.append({"row": i + 2, "message": str(e)})

        await self.db.flush()
        return {"imported": imported, "failed": failed, "errors": errors}
