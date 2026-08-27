from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class FailureLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    task_id: str
    task_name: str
    entity_type: str | None
    entity_id: UUID | None
    error_type: str
    error_message: str
    traceback: str | None = None
    retry_count: int
    created_at: datetime

class FailureLogPage(BaseModel):
    items: list[FailureLogResponse]
    total: int
    limit: int
    offset: int
