from typing import TYPE_CHECKING
from uuid import UUID
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
if TYPE_CHECKING:
    from app.models.asset_3d import Asset3D
    from app.models.fitting_result import FittingResult
    from app.models.user import User

class Garment(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "garments"
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    original_image_url: Mapped[str] = mapped_column(Text, nullable=False)
    processed_image_url: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100))
    color: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="uploaded", server_default="uploaded")
    user: Mapped["User"] = relationship(back_populates="garments")
    fitting_results: Mapped[list["FittingResult"]] = relationship(back_populates="garment")
    asset_3d: Mapped["Asset3D | None"] = relationship(back_populates="garment", uselist=False)
