from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class GarmentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    original_image_url: str
    processed_image_url: str | None
    category: str | None
    color: str | None
    status: Literal["uploaded", "processing", "done", "failed"]
    created_at: datetime

class GarmentUploadAccepted(BaseModel):
    job_id: str
    garment_id: UUID
    status: Literal["uploaded"]
