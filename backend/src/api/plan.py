import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_or_create_device
from src.schemas.plan import SavedPlanCreate, SavedPlanResponse, SavedPlanList
from src.services.plan_service import PlanService
from src.services.pdf_export import PDFExportService
from src.services.session_store import SessionStore

router = APIRouter(prefix="/plans", tags=["方案"])


@router.post("", response_model=SavedPlanResponse, status_code=status.HTTP_201_CREATED)
async def save_plan(
    req: SavedPlanCreate,
    response: Response,
    device_id: Annotated[str, Depends(get_or_create_device)],
    db: AsyncSession = Depends(get_db),
):
    service = PlanService(db)
    session_courses = SessionStore.get_courses(device_id)
    course_map = {c.id: c for c in session_courses if c.id}
    total_credits = sum(
        course_map[str(cid)].credit for cid in req.course_ids
        if str(cid) in course_map
    )
    plan = await service.save(
        device_id=device_id,
        name=req.name,
        course_ids=req.course_ids,
        total_credits=total_credits,
        notes=req.notes,
    )
    return SavedPlanResponse(
        id=plan.id,
        name=plan.name,
        course_ids=[uuid.UUID(cid) for cid in plan.course_ids],
        total_credits=float(plan.total_credits),
        match_score=float(plan.match_score) if plan.match_score else None,
        notes=plan.notes,
        created_at=plan.created_at,
    )


@router.get("", response_model=SavedPlanList)
async def list_plans(
    response: Response,
    device_id: Annotated[str, Depends(get_or_create_device)],
    db: AsyncSession = Depends(get_db),
):
    service = PlanService(db)
    plans = await service.list_by_device(device_id)
    return SavedPlanList(plans=[
        SavedPlanResponse(
            id=p.id,
            name=p.name,
            course_ids=[uuid.UUID(cid) for cid in p.course_ids],
            total_credits=float(p.total_credits),
            match_score=float(p.match_score) if p.match_score else None,
            notes=p.notes,
            created_at=p.created_at,
        )
        for p in plans
    ])


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: uuid.UUID,
    response: Response,
    device_id: Annotated[str, Depends(get_or_create_device)],
    db: AsyncSession = Depends(get_db),
):
    service = PlanService(db)
    deleted = await service.delete(plan_id, device_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="方案不存在")


@router.get("/{plan_id}/export")
async def export_plan(
    plan_id: uuid.UUID,
    response: Response,
    device_id: Annotated[str, Depends(get_or_create_device)],
    db: AsyncSession = Depends(get_db),
):
    service = PlanService(db)
    plan = await service.get(plan_id)
    if not plan or plan.device_id != device_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="方案不存在")

    pdf_service = PDFExportService(db)
    pdf_bytes = await pdf_service.export_plan(plan)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{plan.name}.pdf"'},
    )
