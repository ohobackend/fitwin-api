from typing import Literal
from uuid import UUID
from pydantic import BaseModel

class Asset3DGenerateRequest(BaseModel):
    garment_id: UUID

class Asset3DResponse(BaseModel):
    id: UUID
    garment_id: UUID
    job_id: str | None
    glb_url: str | None
    thumbnail_url: str | None
    status: Literal["pending", "processing", "done", "failed"]
    error: str | None = None
    cache_hit: bool = False
