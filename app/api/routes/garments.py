from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.db.session import get_db_session
from app.schemas.garment import GarmentUploadResponse
from app.services.garment_service import GarmentProcessingError, UserNotFoundError, upload_and_process_garment
from app.services.storage import ObjectStorageService

router = APIRouter(prefix="/garments", tags=["garments"])
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}

def get_storage_service() -> ObjectStorageService:
    return ObjectStorageService()

@router.post("/upload", response_model=GarmentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_garment(
    request: Request,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    storage: ObjectStorageService = Depends(get_storage_service),
) -> GarmentUploadResponse:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Only JPEG and PNG images are supported")
    max_bytes = get_settings().upload_max_bytes
    image_bytes = await file.read(max_bytes + 1)
    await file.close()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Image file is empty")
    if len(image_bytes) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Image exceeds the {max_bytes}-byte limit")
    try:
        user_id = UUID(str(request.state.user["sub"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Token subject must be a user UUID") from exc
    try:
        garment = await upload_and_process_garment(session, storage, user_id, image_bytes, file.filename, file.content_type)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Authenticated user does not exist") from exc
    except GarmentProcessingError as exc:
        raise HTTPException(status_code=500, detail={"message": "Garment preprocessing failed", "garment_id": str(exc.garment_id)}) from exc
    return GarmentUploadResponse.model_validate(garment)
