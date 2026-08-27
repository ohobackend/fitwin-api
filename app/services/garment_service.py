from io import BytesIO
from uuid import UUID, uuid4
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.garment import Garment
from app.models.user import User
from app.services.storage import ObjectStorageService
from app.worker.celery_app import celery_app

class UserNotFoundError(Exception):
    pass

class QueueSubmissionError(Exception):
    def __init__(self, garment_id: UUID) -> None:
        self.garment_id = garment_id
        super().__init__(f"Could not queue garment {garment_id}")

async def create_garment_job(
    session: AsyncSession, storage: ObjectStorageService, user_id: UUID,
    image_bytes: bytes, filename: str | None, content_type: str,
) -> tuple[Garment, str]:
    if await session.scalar(select(User.id).where(User.id == user_id)) is None:
        raise UserNotFoundError
    garment_id = uuid4()
    extension = ".png" if content_type == "image/png" else ".jpg"
    original_key = f"garments/{user_id}/{garment_id}/original{extension}"
    processed_key = f"garments/{user_id}/{garment_id}/processed.png"
    garment = Garment(
        id=garment_id, user_id=user_id,
        original_image_url=storage.get_object_url(original_key), status="uploaded",
    )
    session.add(garment)
    await session.commit()
    try:
        await run_in_threadpool(storage.upload_fileobj, BytesIO(image_bytes), original_key, content_type)
        task = await run_in_threadpool(
            celery_app.send_task,
            "garments.process",
            args=[str(garment_id), original_key, processed_key, filename],
        )
        await session.refresh(garment)
        return garment, task.id
    except Exception as exc:
        await session.rollback()
        await session.execute(update(Garment).where(Garment.id == garment_id).values(status="failed"))
        await session.commit()
        raise QueueSubmissionError(garment_id) from exc
