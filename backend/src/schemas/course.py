import uuid

from pydantic import BaseModel


class ScheduleItem(BaseModel):
    day_of_week: int
    start_period: int
    end_period: int
    weeks: list[int]


class CourseBase(BaseModel):
    course_no: str
    name: str
    credit: float
    instructor: str
    capacity: int
    schedule: list[ScheduleItem]
    location: str
    campus: str
    category: str
    description: str | None = None
    semester: str


class CourseResponse(CourseBase):
    id: uuid.UUID
    is_active: bool

    class Config:
        from_attributes = True


class CourseSearchResult(BaseModel):
    courses: list[CourseResponse]


class SessionCourse(BaseModel):
    """In-memory course from student Excel upload. Not persisted to DB."""
    id: str | None = None
    name: str
    credit: float
    course_no: str | None = None
    instructor: str | None = None
    capacity: int | None = None
    schedule: list[ScheduleItem] = []
    location: str | None = None
    campus: str | None = None
    category: str | None = None
    semester: str | None = None
    description: str | None = None
