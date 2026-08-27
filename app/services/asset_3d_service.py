from uuid import UUID, uuid4
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.asset_3d import Asset3D
from app.models.garment import Garment
from app.worker.celery_app import celery_app

class GarmentNotReadyError(Exception): pass
class Asset3DNotFoundError(Exception): pass
class Asset3DQueueError(Exception): pass

async def create_or_get_asset_job(
    session: AsyncSession, user_id: UUID, garment_id: UUID,
) -> tuple[Asset3D, bool]:
    garment = await session.scalar(
        select(Garment).where(
            Garment.id == garment_id, Garment.user_id == user_id, Garment.status == "done"
        ).with_for_update()
    )
    if garment is None or not garment.processed_image_url:
        raise GarmentNotReadyError
    asset = await session.scalar(select(Asset3D).where(Asset3D.garment_id == garment_id))
    if asset and asset.status in {"pending", "processing", "done"}:
        await session.commit()
        return asset, True
    job_id = str(uuid4())
    if asset:
        asset.status = "pending"
        asset.job_id = job_id
        asset.glb_url = None
        asset.error_message = None
    else:
        asset = Asset3D(garment_id=garment_id, status="pending", job_id=job_id)
        session.add(asset)
    await session.commit()
    await session.refresh(asset)
    try:
        await run_in_threadpool(
            celery_app.send_task, "assets.generate_3d", args=[str(asset.id)],
            task_id=job_id, queue="gpu_3d",
        )
        return asset, False
    except Exception as exc:
        await session.rollback()
        await session.execute(update(Asset3D).where(Asset3D.id == asset.id).values(status="failed"))
        await session.commit()
        raise Asset3DQueueError from exc

async def get_asset_for_user(session: AsyncSession, user_id: UUID, garment_id: UUID) -> Asset3D:
    asset = await session.scalar(
        select(Asset3D).join(Garment).where(Asset3D.garment_id == garment_id, Garment.user_id == user_id)
    )
    if asset is None:
        raise Asset3DNotFoundError
    return asset
