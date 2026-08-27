from typing import Any
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    status_code: int
    message: str
    detail: Any | None = None
