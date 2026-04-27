import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class PriorityStrategy(str, enum.Enum):
    CREDIT = "credit"
    INTEREST = "interest"
    MAJOR = "major"


class SelectionRule(Base):
    __tablename__ = "selection_rules"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    max_credits: Mapped[int] = mapped_column(nullable=False)
    min_credits: Mapped[int] = mapped_column(default=0)
    enrollment_start: Mapped[datetime] = mapped_column(nullable=False)
    enrollment_end: Mapped[datetime] = mapped_column(nullable=False)
    semester: Mapped[str] = mapped_column(String(20), nullable=False)
    priority_strategy: Mapped[PriorityStrategy] = mapped_column(
        Enum(PriorityStrategy, native_enum=False), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
