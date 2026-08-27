from io import BytesIO
from uuid import UUID, uuid4
from fastapi.concurrency import run_in_threadpool
from rembg import remove
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.garment import Garment
from app.models.user import User
from app.services.garment_classifier import classify_category, classify_dominant_color
from app.services.storage import ObjectStorageService

class UserNotFoundError(Exception):
    pass

class GarmentProcessingError(Exception):
    def __init__(self, garment_id: UUID) -> None:
        self.garment_id = garment_id
        super().__init__(f"Garment {garment_id} processing failed")

def remove_background(image_bytes: bytes) -> bytes:
    result = remove(image_bytes)
    if not isinstance(result, bytes):
        raise ValueError("rembg did not return image bytes")
    return result

async def upload_and_process_garment(
    session: AsyncSession, storage: ObjectStorageService, user_id: UUID,
    image_bytes: bytes, filename: str | None, content_type: str,
) -> Garment:
    if await session.scalar(select(User.id).where(User.id == user_id)) is None:
        raise UserNotFoundError

    garment_id = uuid4()
    extension = ".png" if content_type == "image/png" else ".jpg"
    original_key = f"garments/{user_id}/{garment_id}/original{extension}"
    processed_key = f"garments/{user_id}/{garment_id}/processed.png"
    garment = Garment(
        id=garment_id, user_id=user_id, original_image_url=storage.get_object_url(original_key), status="uploaded"
    )
    session.add(garment)
    await session.commit()

    try:
        garment.status = "processing"
        await session.commit()
        await run_in_threadpool(storage.upload_fileobj, BytesIO(image_bytes), original_key, content_type)

        processed_bytes = await run_in_threadpool(remove_background, image_bytes)
        category = classify_category(filename)
        color = await run_in_threadpool(classify_dominant_color, processed_bytes)
        await run_in_threadpool(storage.upload_fileobj, BytesIO(processed_bytes), processed_key, "image/png")

        garment.processed_image_url = storage.get_object_url(processed_key)
        garment.category = category
        garment.color = color
        garment.status = "done"
        await session.commit()
        await session.refresh(garment)
        return garment
    except Exception as exc:
        await session.rollback()
        await session.execute(update(Garment).where(Garment.id == garment_id).values(status="failed"))
        await session.commit()
        raise GarmentProcessingError(garment_id) from exc
