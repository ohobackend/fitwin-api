from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.schemas.asset_3d import Asset3DGenerateRequest, Asset3DResponse
from app.services.asset_3d_service import (
    Asset3DNotFoundError, Asset3DQueueError, GarmentNotReadyError,
    create_or_get_asset_job, get_asset_for_user,
)

router = APIRouter(prefix="/assets/3d", tags=["3d-assets"])

def authenticated_user_id(request: Request) -> UUID:
    try:
        return UUID(str(request.state.user["sub"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Token subject must be a user UUID") from exc

def to_response(asset, *, cache_hit: bool = False) -> Asset3DResponse:
    return Asset3DResponse(
        id=asset.id, garment_id=asset.garment_id, job_id=asset.job_id,
        glb_url=asset.glb_url, thumbnail_url=asset.thumbnail_url, status=asset.status,
        error=asset.error_message, cache_hit=cache_hit,
    )

@router.post("/generate", response_model=Asset3DResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_asset(
    payload: Asset3DGenerateRequest, request: Request, response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> Asset3DResponse:
    try:
        asset, cache_hit = await create_or_get_asset_job(
            session, authenticated_user_id(request), payload.garment_id
        )
    except GarmentNotReadyError as exc:
        raise HTTPException(status_code=404, detail="Processed garment was not found") from exc
    except Asset3DQueueError as exc:
        raise HTTPException(status_code=503, detail="Could not queue 3D generation") from exc
    if cache_hit and asset.status == "done":
        response.status_code = status.HTTP_200_OK
    return to_response(asset, cache_hit=cache_hit)

@router.get("/{garment_id}", response_model=Asset3DResponse)
async def get_asset(
    garment_id: UUID, request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> Asset3DResponse:
    try:
        asset = await get_asset_for_user(session, authenticated_user_id(request), garment_id)
    except Asset3DNotFoundError as exc:
        raise HTTPException(status_code=404, detail="3D asset was not found") from exc
    return to_response(asset)
