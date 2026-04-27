"""Import-related Pydantic schemas for Excel column mapping and degradation."""
from pydantic import BaseModel


class ColumnMapping(BaseModel):
    source: str
    target: str
    confidence: float


class MappingResult(BaseModel):
    mappings: list[ColumnMapping]
    unmapped_source: list[str] = []
    unmapped_target: list[str] = []


class DegradationImpact(BaseModel):
    field: str
    impact: str
    fallback: str


class DegradationReport(BaseModel):
    missing_fields: list[str] = []
    impacts: list[DegradationImpact] = []


class ImportAnalyzeResponse(BaseModel):
    mapping: MappingResult
    sample_data: list[dict]
    degradation: DegradationReport


class ImportError(BaseModel):
    row: int
    message: str


class ImportConfirmRequest(BaseModel):
    mapping: MappingResult
    raw_data: list[dict]


class ImportConfirmResponse(BaseModel):
    courses: list[dict]
    total: int
    errors: list[ImportError] = []
    degradation: DegradationReport
