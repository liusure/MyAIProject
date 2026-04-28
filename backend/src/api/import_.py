"""Import API router — Excel upload, column mapping, session course management."""
from typing import Annotated

from fastapi import APIRouter, Depends, File, Response, UploadFile

from src.core.security import get_or_create_device
from src.schemas.import_result import (
    ImportAnalyzeResponse,
    ImportConfirmRequest,
    ImportConfirmResponse,
)
from src.schemas.course import SessionCourse
from src.services.import_analyzer import ImportAnalyzer
from src.services.import_parser import ImportParser
from src.services.schedule_parser import ScheduleParser
from src.services.session_store import SessionStore

router = APIRouter(prefix="/import", tags=["导入"])

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/analyze", response_model=ImportAnalyzeResponse)
async def analyze_excel(
    response: Response,
    file: UploadFile = File(...),
    device_id: Annotated[str, Depends(get_or_create_device)] = "",
):
    if not file.filename:
        return Response(status_code=400, content="未提供文件")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("xlsx", "xls", "csv"):
        return Response(status_code=400, content="不支持的文件格式，请上传 .xlsx/.xls/.csv")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        return Response(status_code=413, content="文件超过 5MB 限制")

    try:
        mapping_result, raw_data = await ImportAnalyzer.analyze(content, file.filename)
    except ValueError as e:
        return Response(status_code=400, content=str(e))

    degradation = ImportAnalyzer.build_degradation_report(mapping_result)

    # Store full raw_data in session for confirm step
    SessionStore.set_raw_data(device_id, raw_data)

    sample_data = raw_data[:3] if len(raw_data) > 3 else raw_data

    return ImportAnalyzeResponse(
        mapping=mapping_result,
        sample_data=sample_data,
        degradation=degradation,
    )


@router.post("/confirm", response_model=ImportConfirmResponse)
async def confirm_import(
    body: ImportConfirmRequest,
    response: Response,
    device_id: Annotated[str, Depends(get_or_create_device)] = "",
):
    # Use full raw_data from session (not the 3-row sample from frontend)
    raw_data = SessionStore.get_raw_data(device_id) or body.raw_data
    courses, errors = ImportParser.apply_mapping(raw_data, body.mapping)

    # Parse schedule strings into ScheduleItem objects
    for c in courses:
        if isinstance(c.get("schedule"), str) and c["schedule"]:
            weeks_str = c.get("weeks")
            c["schedule"] = ScheduleParser.parse_schedule(c["schedule"], weeks_str)
        elif not isinstance(c.get("schedule"), list):
            c["schedule"] = []
        # Remove transient weeks field (not part of SessionCourse schema)
        c.pop("weeks", None)

    session_courses = [SessionCourse(**c) for c in courses]
    SessionStore.set_courses(device_id, session_courses)

    degradation = ImportAnalyzer.build_degradation_report(body.mapping)

    return ImportConfirmResponse(
        courses=courses,
        total=len(courses),
        errors=errors,
        degradation=degradation,
    )


@router.get("/session/courses")
async def get_session_courses(
    response: Response,
    device_id: Annotated[str, Depends(get_or_create_device)] = "",
):
    courses = SessionStore.get_courses(device_id)
    if not courses:
        return Response(status_code=204)
    return {"courses": [c.model_dump() for c in courses]}


@router.delete("/session/courses")
async def clear_session_courses(
    response: Response,
    device_id: Annotated[str, Depends(get_or_create_device)] = "",
):
    SessionStore.clear(device_id)
    return Response(status_code=204)
