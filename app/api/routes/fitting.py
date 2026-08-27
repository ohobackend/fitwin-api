from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.concurrency import run_in_threadpool
from app.core.config import get_settings
from app.db.session import get_db_session
from app.schemas.fitting import Fitting2DResponse
from app.services.fitting_service import (
    FittingQueueError, GarmentNotFoundError, UnsupportedGarmentCategoryError,
    create_or_get_fitting_job,
)
from app.services.storage import ObjectStorageService
from app.services.image_validator import InvalidImageError, validate_image_bytes

router = APIRouter(prefix="/fitting", tags=["fitting"])

def get_storage_service() -> ObjectStorageService:
    return ObjectStorageService()

@router.post("/2d", response_model=Fitting2DResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_fitting_2d(
    request: Request, response: Response,
    garment_id: UUID = Form(...), model_image: UploadFile = File(...),
    category: Literal["upperbody", "lowerbody", "dress"] | None = Form(None),
    model_type: Literal["hd", "dc"] | None = Form(None),
    session: AsyncSession = Depends(get_db_session),
    storage: ObjectStorageService = Depends(get_storage_service),
) -> Fitting2DResponse:
    if model_image.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(status_code=415, detail="Only JPEG and PNG model images are supported")
    limit = get_settings().upload_max_bytes
    image_bytes = await model_image.read(limit + 1)
    await model_image.close()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Model image is empty")
    if len(image_bytes) > limit:
        raise HTTPException(status_code=413, detail=f"Model image exceeds the {limit}-byte limit")
    try:
        await run_in_threadpool(validate_image_bytes, image_bytes)
    except InvalidImageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        user_id = UUID(str(request.state.user["sub"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Token subject must be a user UUID") from exc
    try:
        fitting, cache_hit = await create_or_get_fitting_job(
            session, storage, user_id, garment_id, image_bytes, model_image.content_type,
            category, model_type,
        )
    except GarmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Processed garment was not found") from exc
    except UnsupportedGarmentCategoryError as exc:
        raise HTTPException(status_code=422, detail="Specify a compatible OOTDiffusion category and model_type") from exc
    except FittingQueueError as exc:
        raise HTTPException(status_code=503, detail="Could not queue 2D fitting") from exc
    if cache_hit and fitting.status == "done":
        response.status_code = status.HTTP_200_OK
    return Fitting2DResponse(
        fitting_result_id=fitting.id, job_id=fitting.job_id, status=fitting.status,
        result_url=fitting.result_url, cache_hit=cache_hit,
    )
