from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
if TYPE_CHECKING:
    from app.models.fitting_result import FittingResult
    from app.models.garment import Garment

class User(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    garments: Mapped[list["Garment"]] = relationship(back_populates="user")
    fitting_results: Mapped[list["FittingResult"]] = relationship(back_populates="user")
