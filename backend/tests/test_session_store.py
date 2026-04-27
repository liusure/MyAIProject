"""Tests for SessionStore — in-memory class methods."""
import uuid

from src.schemas.course import SessionCourse
from src.services.session_store import SessionStore


class TestSessionStore:
    def test_set_and_get_courses(self):
        courses = [SessionCourse(name="数学", credit=3.0)]
        SessionStore.set_courses("device-1", courses)
        result = SessionStore.get_courses("device-1")
        assert result is not None
        assert len(result) == 1
        assert result[0].name == "数学"

    def test_auto_assigns_id(self):
        courses = [SessionCourse(name="数学", credit=3.0)]
        SessionStore.set_courses("device-1", courses)
        result = SessionStore.get_courses("device-1")
        assert result[0].id is not None
        # Verify it's a valid UUID
        uuid.UUID(result[0].id)

    def test_preserves_existing_id(self):
        courses = [SessionCourse(id="my-id", name="数学", credit=3.0)]
        SessionStore.set_courses("device-1", courses)
        result = SessionStore.get_courses("device-1")
        assert result[0].id == "my-id"

    def test_get_nonexistent(self):
        assert SessionStore.get_courses("nonexistent") is None

    def test_has_courses_true(self):
        courses = [SessionCourse(name="数学", credit=3.0)]
        SessionStore.set_courses("device-1", courses)
        assert SessionStore.has_courses("device-1") is True

    def test_has_courses_false(self):
        assert SessionStore.has_courses("nonexistent") is False

    def test_has_courses_empty_list(self):
        SessionStore.set_courses("device-1", [])
        assert SessionStore.has_courses("device-1") is False

    def test_clear(self):
        courses = [SessionCourse(name="数学", credit=3.0)]
        SessionStore.set_courses("device-1", courses)
        SessionStore.set_raw_data("device-1", [{"col": "val"}])

        SessionStore.clear("device-1")

        assert SessionStore.get_courses("device-1") is None
        assert SessionStore.get_raw_data("device-1") is None

    def test_clear_nonexistent(self):
        # Should not raise
        SessionStore.clear("nonexistent")

    def test_set_and_get_raw_data(self):
        raw = [{"name": "数学"}, {"name": "物理"}]
        SessionStore.set_raw_data("device-1", raw)
        result = SessionStore.get_raw_data("device-1")
        assert result == raw

    def test_get_raw_data_nonexistent(self):
        assert SessionStore.get_raw_data("nonexistent") is None

    def test_isolation_between_devices(self):
        SessionStore.set_courses("dev-1", [SessionCourse(name="A", credit=1.0)])
        SessionStore.set_courses("dev-2", [SessionCourse(name="B", credit=2.0)])

        dev1 = SessionStore.get_courses("dev-1")
        dev2 = SessionStore.get_courses("dev-2")
        assert dev1[0].name == "A"
        assert dev2[0].name == "B"
