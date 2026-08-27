from typing import TYPE_CHECKING
from uuid import UUID
from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
if TYPE_CHECKING:
    from app.models.garment import Garment
    from app.models.user import User

class FittingResult(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "fitting_results"
    __table_args__ = (CheckConstraint("result_type IN ('2d', '3d')", name="ck_fitting_result_type"),)
    garment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("garments.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    result_type: Mapped[str] = mapped_column(String(2), nullable=False)
    result_url: Mapped[str] = mapped_column(Text, nullable=False)
    garment: Mapped["Garment"] = relationship(back_populates="fitting_results")
    user: Mapped["User"] = relationship(back_populates="fitting_results")
