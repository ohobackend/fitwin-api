from datetime import datetime
from uuid import UUID
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDPrimaryKeyMixin

class JobFailureLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "job_failure_logs"
    task_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    task_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(30), index=True)
    entity_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), index=True)
    error_type: Mapped[str] = mapped_column(String(200), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    traceback: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
