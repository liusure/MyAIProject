import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class StudentRole(str, enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    major: Mapped[str] = mapped_column(String(100), nullable=False)
    grade: Mapped[int] = mapped_column(nullable=False)
    email: Mapped[str | None] = mapped_column(String(100), unique=True)
    role: Mapped[StudentRole] = mapped_column(
        Enum(StudentRole, native_enum=False), nullable=False, default=StudentRole.STUDENT
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
