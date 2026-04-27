import uuid
from datetime import datetime

from pydantic import BaseModel

from src.schemas.course import CourseResponse


class ConflictItem(BaseModel):
    type: str
    severity: str
    course_a: uuid.UUID
    course_b: uuid.UUID
    message: str


class RecommendationPlan(BaseModel):
    plan_name: str
    courses: list[CourseResponse]
    total_credits: float
    match_score: float
    conflicts: list[ConflictItem] = []


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    reply: str
    recommendations: list[RecommendationPlan] = []
    conflicts: list[ConflictItem] = []
    degraded: bool = False


class SavedPlanCreate(BaseModel):
    name: str
    course_ids: list[uuid.UUID]
    notes: str | None = None


class SavedPlanResponse(BaseModel):
    id: uuid.UUID
    name: str
    course_ids: list[uuid.UUID]
    total_credits: float
    match_score: float | None = None
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class SavedPlanList(BaseModel):
    plans: list[SavedPlanResponse]
