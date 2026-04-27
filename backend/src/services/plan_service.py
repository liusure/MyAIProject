import uuid

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.saved_plan import SavedPlan


class PlanService:
    """方案收藏业务逻辑"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def save(
        self,
        device_id: str,
        name: str,
        course_ids: list[uuid.UUID],
        total_credits: float,
        match_score: float | None = None,
        notes: str | None = None,
    ) -> SavedPlan:
        plan = SavedPlan(
            id=uuid.uuid4(),
            device_id=device_id,
            name=name,
            course_ids=[str(cid) for cid in course_ids],
            total_credits=total_credits,
            match_score=match_score,
            notes=notes,
        )
        self.db.add(plan)
        await self.db.flush()
        return plan

    async def list_by_device(self, device_id: str) -> list[SavedPlan]:
        result = await self.db.execute(
            select(SavedPlan)
            .where(SavedPlan.device_id == device_id)
            .order_by(SavedPlan.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, plan_id: uuid.UUID) -> SavedPlan | None:
        result = await self.db.execute(select(SavedPlan).where(SavedPlan.id == plan_id))
        return result.scalar_one_or_none()

    async def delete(self, plan_id: uuid.UUID, device_id: str) -> bool:
        result = await self.db.execute(
            delete(SavedPlan).where(SavedPlan.id == plan_id, SavedPlan.device_id == device_id)
        )
        return result.rowcount > 0
