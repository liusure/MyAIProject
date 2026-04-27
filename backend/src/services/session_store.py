"""In-memory session course storage keyed by device_id."""
import uuid
from typing import Optional

from src.schemas.course import SessionCourse


class SessionStore:
    """Stores session courses in memory. Data is cleared on new upload or session end."""

    _store: dict[str, list[SessionCourse]] = {}
    _raw_data: dict[str, list[dict]] = {}

    @classmethod
    def set_courses(cls, device_id: str, courses: list[SessionCourse]) -> None:
        for course in courses:
            if course.id is None:
                course.id = str(uuid.uuid4())
        cls._store[device_id] = courses

    @classmethod
    def get_courses(cls, device_id: str) -> Optional[list[SessionCourse]]:
        return cls._store.get(device_id)

    @classmethod
    def clear(cls, device_id: str) -> None:
        cls._store.pop(device_id, None)
        cls._raw_data.pop(device_id, None)

    @classmethod
    def has_courses(cls, device_id: str) -> bool:
        return device_id in cls._store and len(cls._store[device_id]) > 0

    @classmethod
    def set_raw_data(cls, device_id: str, raw_data: list[dict]) -> None:
        cls._raw_data[device_id] = raw_data

    @classmethod
    def get_raw_data(cls, device_id: str) -> Optional[list[dict]]:
        return cls._raw_data.get(device_id)
