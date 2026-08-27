from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID
from celery.utils.log import get_task_logger
from sqlalchemy import select, update
from app.core.config import get_settings
from app.db.sync_session import SyncSessionFactory
from app.integrations.ootdiffusion import get_ootdiffusion_runner
from app.models.fitting_result import FittingResult
from app.models.garment import Garment
from app.services.storage import ObjectStorageService
from app.worker.celery_app import celery_app

logger = get_task_logger(__name__)

@celery_app.task(bind=True, max_retries=3, name="fitting.process_2d")
def process_fitting_2d(
    self, fitting_result_id: str, person_key: str, category: str, model_type: str,
) -> dict[str, str]:
    result_id = UUID(fitting_result_id)
    storage = ObjectStorageService()
    try:
        with SyncSessionFactory() as session:
            fitting = session.scalar(select(FittingResult).where(FittingResult.id == result_id))
            if fitting is None:
                raise RuntimeError(f"Fitting result {result_id} does not exist")
            garment_url = session.scalar(select(Garment.processed_image_url).where(Garment.id == fitting.garment_id))
            if not garment_url:
                raise RuntimeError("Processed garment image is unavailable")
            session.execute(update(FittingResult).where(FittingResult.id == result_id).values(status="processing"))
            session.commit()

        with TemporaryDirectory(prefix="fitwin-ootd-") as temp_dir:
            temp = Path(temp_dir)
            person_path = temp / "person.png"
            garment_path = temp / "garment.png"
            person_path.write_bytes(storage.download_bytes(person_key))
            garment_path.write_bytes(storage.download_bytes(storage.object_key_from_url(garment_url)))
            settings = get_settings()
            image = get_ootdiffusion_runner(model_type).infer(
                person_path, garment_path, model_type=model_type, category=category,
                steps=settings.ootdiffusion_steps, scale=settings.ootdiffusion_scale,
                seed=settings.ootdiffusion_seed,
            )
            output = BytesIO()
            image.save(output, format="PNG")

        result_key = f"fittings/2d/{result_id}/result.png"
        output.seek(0)
        storage.upload_fileobj(output, result_key, "image/png")
        result_url = storage.get_object_url(result_key)
        with SyncSessionFactory() as session:
            session.execute(
                update(FittingResult).where(FittingResult.id == result_id).values(
                    result_url=result_url, status="done"
                )
            )
            session.commit()
        return {"fitting_result_id": fitting_result_id, "result_url": result_url, "status": "done"}
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            with SyncSessionFactory() as session:
                session.execute(update(FittingResult).where(FittingResult.id == result_id).values(status="failed"))
                session.commit()
            logger.exception("2D fitting %s failed after retries", fitting_result_id)
            raise
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
