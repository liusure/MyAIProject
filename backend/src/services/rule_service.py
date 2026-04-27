import uuid
from datetime import datetime

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.selection_rule import SelectionRule, PriorityStrategy


class RuleService:
    """选课规则 CRUD 服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        name: str,
        max_credits: int,
        min_credits: int,
        enrollment_start: datetime,
        enrollment_end: datetime,
        semester: str,
        priority_strategy: PriorityStrategy,
    ) -> SelectionRule:
        rule = SelectionRule(
            id=uuid.uuid4(),
            name=name,
            max_credits=max_credits,
            min_credits=min_credits,
            enrollment_start=enrollment_start,
            enrollment_end=enrollment_end,
            semester=semester,
            priority_strategy=priority_strategy,
            is_active=True,
        )
        self.db.add(rule)
        await self.db.flush()
        return rule

    async def list_all(self, semester: str | None = None) -> list[SelectionRule]:
        stmt = select(SelectionRule).where(SelectionRule.is_active == True)
        if semester:
            stmt = stmt.where(SelectionRule.semester == semester)
        result = await self.db.execute(stmt.order_by(SelectionRule.created_at.desc()))
        return list(result.scalars().all())

    async def get(self, rule_id: uuid.UUID) -> SelectionRule | None:
        result = await self.db.execute(select(SelectionRule).where(SelectionRule.id == rule_id))
        return result.scalar_one_or_none()

    async def delete(self, rule_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            delete(SelectionRule).where(SelectionRule.id == rule_id)
        )
        return result.rowcount > 0
