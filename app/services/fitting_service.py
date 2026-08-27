import hashlib
from io import BytesIO
from uuid import UUID, uuid4
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.models.fitting_result import FittingResult
from app.models.garment import Garment
from app.services.storage import ObjectStorageService
from app.worker.celery_app import celery_app

CATEGORY_MAP = {"top": "upperbody", "outerwear": "upperbody", "bottom": "lowerbody", "dress": "dress"}

class GarmentNotFoundError(Exception): pass
class UnsupportedGarmentCategoryError(Exception): pass
class FittingQueueError(Exception): pass

def build_combination_hash(
    user_id: UUID, garment_id: UUID, person_bytes: bytes, category: str, model_type: str,
) -> str:
    settings = get_settings()
    person_hash = hashlib.sha256(person_bytes).hexdigest()
    value = f"{user_id}:{garment_id}:{person_hash}:{category}:{model_type}:{settings.ootdiffusion_steps}:{settings.ootdiffusion_scale}:{settings.ootdiffusion_seed}"
    return hashlib.sha256(value.encode()).hexdigest()

async def create_or_get_fitting_job(
    session: AsyncSession, storage: ObjectStorageService, user_id: UUID, garment_id: UUID,
    person_bytes: bytes, person_content_type: str,
    category_override: str | None, model_type_override: str | None,
) -> tuple[FittingResult, bool]:
    garment = await session.scalar(
        select(Garment).where(Garment.id == garment_id, Garment.user_id == user_id, Garment.status == "done")
    )
    if garment is None or not garment.processed_image_url:
        raise GarmentNotFoundError
    category = category_override or CATEGORY_MAP.get(garment.category or "")
    if category not in {"upperbody", "lowerbody", "dress"}:
        raise UnsupportedGarmentCategoryError
    model_type = model_type_override or ("hd" if category == "upperbody" else "dc")
    if model_type not in {"hd", "dc"} or (model_type == "hd" and category != "upperbody"):
        raise UnsupportedGarmentCategoryError

    combination_hash = build_combination_hash(user_id, garment_id, person_bytes, category, model_type)
    lock_key = int(combination_hash[:16], 16) - (1 << 64 if int(combination_hash[:16], 16) >= 1 << 63 else 0)
    await session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_key})
    existing = await session.scalar(
        select(FittingResult).where(FittingResult.combination_hash == combination_hash)
    )
    if existing and existing.status in {"pending", "processing", "done"}:
        await session.commit()
        return existing, True

    result_id = existing.id if existing else uuid4()
    job_id = str(uuid4())
    extension = ".png" if person_content_type == "image/png" else ".jpg"
    person_key = f"fittings/2d/{result_id}/person{extension}"
    if existing:
        existing.status = "pending"
        existing.job_id = job_id
        existing.result_url = None
        fitting = existing
    else:
        fitting = FittingResult(
            id=result_id, garment_id=garment_id, user_id=user_id, result_type="2d",
            input_image_url=storage.get_object_url(person_key), combination_hash=combination_hash,
            job_id=job_id, status="pending",
        )
        session.add(fitting)
    await session.commit()
    try:
        await run_in_threadpool(storage.upload_fileobj, BytesIO(person_bytes), person_key, person_content_type)
        await run_in_threadpool(
            celery_app.send_task, "fitting.process_2d",
            args=[str(result_id), person_key, category, model_type], task_id=job_id, queue="gpu",
        )
        await session.refresh(fitting)
        return fitting, False
    except Exception as exc:
        await session.rollback()
        await session.execute(update(FittingResult).where(FittingResult.id == result_id).values(status="failed"))
        await session.commit()
        raise FittingQueueError from exc
