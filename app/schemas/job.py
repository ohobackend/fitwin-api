from typing import Any, Literal
from pydantic import BaseModel

JobStatus = Literal["pending", "processing", "retrying", "done", "failed"]

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: dict[str, Any] | None = None
    error: str | None = None
