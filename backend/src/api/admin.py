from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.selection_rule import PriorityStrategy
from src.services.course_import import CourseImportService
from src.services.import_parser import ImportParser
from src.services.import_analyzer import ImportAnalyzer
from src.services.rule_service import RuleService

router = APIRouter(prefix="/admin", tags=["管理"])


@router.post("/courses/import", deprecated=True)
async def import_courses(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """已弃用：请使用 /api/v1/import/analyze + /api/v1/import/confirm"""
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请上传文件")

    content = await file.read()
    try:
        mapping_result, raw_data = await ImportAnalyzer.analyze(content, file.filename)
        records, errors = ImportParser.apply_mapping(raw_data, mapping_result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    service = CourseImportService(db)
    result = await service.import_courses(records)
    return result


class CreateRuleRequest(BaseModel):
    name: str
    max_credits: int
    min_credits: int = 0
    enrollment_start: datetime
    enrollment_end: datetime
    semester: str
    priority_strategy: PriorityStrategy


@router.post("/rules", status_code=status.HTTP_201_CREATED)
async def create_rule(
    req: CreateRuleRequest,
    db: AsyncSession = Depends(get_db),
):
    service = RuleService(db)
    rule = await service.create(
        name=req.name,
        max_credits=req.max_credits,
        min_credits=req.min_credits,
        enrollment_start=req.enrollment_start,
        enrollment_end=req.enrollment_end,
        semester=req.semester,
        priority_strategy=req.priority_strategy,
    )
    return {
        "id": str(rule.id),
        "name": rule.name,
        "max_credits": rule.max_credits,
        "min_credits": rule.min_credits,
        "enrollment_start": rule.enrollment_start.isoformat(),
        "enrollment_end": rule.enrollment_end.isoformat(),
        "semester": rule.semester,
        "priority_strategy": rule.priority_strategy.value,
    }
