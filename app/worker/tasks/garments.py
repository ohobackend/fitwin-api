from io import BytesIO
from uuid import UUID
from celery.utils.log import get_task_logger
from rembg import remove
from sqlalchemy import update
from app.db.sync_session import SyncSessionFactory
from app.models.garment import Garment
from app.services.garment_classifier import classify_category, classify_dominant_color
from app.services.storage import ObjectStorageService
from app.worker.celery_app import celery_app

logger = get_task_logger(__name__)

@celery_app.task(bind=True, max_retries=3, name="garments.process")
def process_garment(self, garment_id: str, original_key: str, processed_key: str, filename: str | None) -> dict[str, str]:
    garment_uuid = UUID(garment_id)
    storage = ObjectStorageService()
    try:
        with SyncSessionFactory() as session:
            session.execute(update(Garment).where(Garment.id == garment_uuid).values(status="processing"))
            session.commit()

        original_bytes = storage.download_bytes(original_key)
        processed_bytes = remove(original_bytes)
        if not isinstance(processed_bytes, bytes):
            raise ValueError("rembg did not return image bytes")
        category = classify_category(filename)
        color = classify_dominant_color(processed_bytes)
        storage.upload_fileobj(BytesIO(processed_bytes), processed_key, "image/png")

        with SyncSessionFactory() as session:
            session.execute(
                update(Garment).where(Garment.id == garment_uuid).values(
                    processed_image_url=storage.get_object_url(processed_key),
                    category=category, color=color, status="done",
                )
            )
            session.commit()
        return {"garment_id": garment_id, "status": "done"}
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            with SyncSessionFactory() as session:
                session.execute(update(Garment).where(Garment.id == garment_uuid).values(status="failed"))
                session.commit()
            logger.exception("Garment %s failed after %s retries", garment_id, self.max_retries)
            raise
        countdown = 2 ** self.request.retries
        logger.warning("Retrying garment %s in %s seconds: %s", garment_id, countdown, exc)
        raise self.retry(exc=exc, countdown=countdown)
