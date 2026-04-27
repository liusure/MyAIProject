import uuid
from datetime import datetime

from sqlalchemy import Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class SavedPlan(Base):
    __tablename__ = "saved_plans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    device_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    course_ids: Mapped[list] = mapped_column(JSONB, nullable=False)
    total_credits: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False)
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    notes: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
