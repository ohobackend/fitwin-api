from typing import TYPE_CHECKING
from uuid import UUID
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
if TYPE_CHECKING:
    from app.models.garment import Garment

class Asset3D(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "assets_3d"
    garment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("garments.id", ondelete="CASCADE"), unique=True, nullable=False)
    glb_url: Mapped[str | None] = mapped_column(Text)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="pending", server_default="pending")
    garment: Mapped["Garment"] = relationship(back_populates="asset_3d")
