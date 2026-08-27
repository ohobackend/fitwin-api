from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID
from celery.utils.log import get_task_logger
from sqlalchemy import select, update
from app.core.config import get_settings
from app.db.sync_session import SyncSessionFactory
from app.integrations.trellis import get_trellis_runner
from app.models.asset_3d import Asset3D
from app.models.garment import Garment
from app.services.glb_validator import validate_glb
from app.services.storage import ObjectStorageService
from app.worker.celery_app import celery_app

logger = get_task_logger(__name__)

@celery_app.task(bind=True, max_retries=3, name="assets.generate_3d")
def generate_asset_3d(self, asset_id: str) -> dict[str, str]:
    asset_uuid = UUID(asset_id)
    storage = ObjectStorageService()
    try:
        with SyncSessionFactory() as session:
            asset = session.scalar(select(Asset3D).where(Asset3D.id == asset_uuid))
            if asset is None:
                raise RuntimeError(f"3D asset {asset_id} does not exist")
            image_url = session.scalar(select(Garment.processed_image_url).where(Garment.id == asset.garment_id))
            if not image_url:
                raise RuntimeError("Processed garment image is unavailable")
            session.execute(update(Asset3D).where(Asset3D.id == asset_uuid).values(status="processing", error_message=None))
            session.commit()

        with TemporaryDirectory(prefix="fitwin-trellis-") as temp_dir:
            source_path = Path(temp_dir) / "garment.png"
            glb_path = Path(temp_dir) / "asset.glb"
            source_path.write_bytes(storage.download_bytes(storage.object_key_from_url(image_url)))
            settings = get_settings()
            get_trellis_runner().generate_glb(
                source_path, glb_path, seed=settings.trellis_seed,
                simplify=settings.trellis_mesh_simplify, texture_size=settings.trellis_texture_size,
            )
            validate_glb(glb_path)
            glb_key = f"assets/3d/{asset_id}/asset.glb"
            storage.upload_file(glb_path, glb_key, "model/gltf-binary")

        glb_url = storage.get_object_url(glb_key)
        with SyncSessionFactory() as session:
            session.execute(update(Asset3D).where(Asset3D.id == asset_uuid).values(status="done", glb_url=glb_url))
            session.commit()
        return {"asset_id": asset_id, "glb_url": glb_url, "status": "done"}
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            with SyncSessionFactory() as session:
                session.execute(
                    update(Asset3D).where(Asset3D.id == asset_uuid).values(
                        status="failed", error_message=str(exc)[:1000]
                    )
                )
                session.commit()
            logger.exception("3D asset %s failed after retries", asset_id)
            raise
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
