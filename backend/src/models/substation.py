from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .user import User


class Substation(Base):
    """Represents an electrical power substation monitored by GridGuard."""

    __tablename__ = "substations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    voltage_level_kv: Mapped[float] = mapped_column(
        Float, nullable=False, default=220.0
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="OPERATIONAL"
    )

    # Foreign key referencing creator with SET NULL cascade rule to preserve infrastructure records
    created_by_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    created_by: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="substations",
    )

    def __repr__(self) -> str:
        return f"<Substation(id={self.id}, name='{self.name}', status='{self.status}', voltage={self.voltage_level_kv}kV)>"
