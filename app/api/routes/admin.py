from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.models.job_failure_log import JobFailureLog
from app.schemas.admin import FailureLogPage, FailureLogResponse

router = APIRouter(prefix="/admin", tags=["admin"])

def require_admin(request: Request) -> None:
    claims = request.state.user
    if claims.get("role") != "admin" and claims.get("is_admin") is not True:
        raise HTTPException(status_code=403, detail="Administrator permission required")

@router.get("/failures", response_model=FailureLogPage, dependencies=[Depends(require_admin)])
async def list_failures(
    task_name: str | None = None,
    entity_type: Literal["garment", "fitting_result", "asset_3d"] | None = None,
    limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> FailureLogPage:
    filters = []
    if task_name:
        filters.append(JobFailureLog.task_name == task_name)
    if entity_type:
        filters.append(JobFailureLog.entity_type == entity_type)
    total = await session.scalar(select(func.count()).select_from(JobFailureLog).where(*filters)) or 0
    rows = (await session.scalars(
        select(JobFailureLog).where(*filters).order_by(JobFailureLog.created_at.desc()).limit(limit).offset(offset)
    )).all()
    return FailureLogPage(
        items=[FailureLogResponse.model_validate(row) for row in rows],
        total=total, limit=limit, offset=offset,
    )
