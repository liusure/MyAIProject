"""Import parser: applies column mapping and converts raw data to structured course dicts."""
import logging
from typing import Any

from src.schemas.import_result import ImportError, MappingResult
from src.services.field_normalizer import FIELD_DEFINITIONS, FieldNormalizer

logger = logging.getLogger(__name__)


class ImportParser:
    """Parses raw Excel data using provided column mapping."""

    @classmethod
    def apply_mapping(
        cls, raw_data: list[dict], mapping: MappingResult
    ) -> tuple[list[dict], list[ImportError]]:
        """Apply column mapping to raw data, returning (courses, errors)."""
        # Build source→target lookup
        col_map = {m.source: m.target for m in mapping.mappings}

        courses: list[dict[str, Any]] = []
        errors: list[ImportError] = []

        for idx, row in enumerate(raw_data):
            try:
                record = cls._map_row(row, col_map, idx + 2)
                if record:
                    courses.append(record)
            except _RowSkipError as e:
                errors.append(ImportError(row=idx + 2, message=str(e)))
            except Exception as e:
                logger.debug(f"Row {idx + 2} parse error: {e}")
                errors.append(ImportError(row=idx + 2, message=str(e)))

        return courses, errors

    @classmethod
    def _map_row(cls, row: dict, col_map: dict[str, str], row_num: int) -> dict[str, Any] | None:
        """Map a single row using the column mapping."""
        record: dict[str, Any] = {}

        for source_col, target_field in col_map.items():
            raw_value = row.get(source_col)
            if raw_value is not None:
                raw_str = str(raw_value).strip()
            else:
                raw_str = ""

            if target_field == "credit":
                normalized = FieldNormalizer.normalize_credit(raw_str)
                if normalized is not None:
                    record["credit"] = normalized
                elif FIELD_DEFINITIONS[target_field].required and raw_str:
                    raise _RowSkipError(f"学分必须为数字，当前值: '{raw_str}'")
            elif target_field == "instructor":
                record["instructor"] = FieldNormalizer.normalize_instructor(raw_str)
            elif target_field == "semester":
                record["semester"] = FieldNormalizer.normalize_semester(raw_str)
            elif target_field == "name":
                val = raw_str
                if not val:
                    raise _RowSkipError("课程名称不能为空")
                record["name"] = val
            elif target_field == "weeks":
                # Keep as raw string for later schedule parsing
                record["weeks"] = raw_str if raw_str else None
            else:
                record[target_field] = raw_str if raw_str else None

        # Validate core fields
        if not record.get("name"):
            raise _RowSkipError("课程名称不能为空")
        if "credit" not in record or record["credit"] is None:
            raise _RowSkipError("学分不能为空")

        # Ensure all optional fields exist (default None)
        for field_key in FIELD_DEFINITIONS:
            if field_key not in record:
                if field_key == "schedule":
                    record[field_key] = []
                else:
                    record[field_key] = None

        return record


class _RowSkipError(Exception):
    """Internal exception to signal a row should be skipped."""
    pass
