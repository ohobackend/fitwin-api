from typing import Literal
from uuid import UUID
from pydantic import BaseModel

class Fitting2DResponse(BaseModel):
    fitting_result_id: UUID
    job_id: str | None
    status: Literal["pending", "processing", "done", "failed"]
    result_url: str | None
    cache_hit: bool
