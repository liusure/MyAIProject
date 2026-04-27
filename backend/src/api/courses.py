from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.schemas.course import CourseSearchResult
from src.services.course_search import CourseSearchService

router = APIRouter(prefix="/courses", tags=["课程"])


@router.get("/search", response_model=CourseSearchResult)
async def search_courses(
    q: str = Query(..., description="搜索关键词"),
    semester: str | None = Query(None, description="学期"),
    category: str | None = Query(None, description="课程类别"),
    db: AsyncSession = Depends(get_db),
):
    service = CourseSearchService(db)
    courses = await service.search(q, semester=semester, category=category)
    return CourseSearchResult(courses=courses)
