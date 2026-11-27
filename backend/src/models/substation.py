from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .asset import Asset
    from .location import Location
    from .user import User


class Substation(Base):
    """
    Represents an electrical power substation monitored by GridGuard.
    Acts as the primary multi-tenant isolation boundary for electrical assets.
    """

    __tablename__ = "substations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False, default="SUB-001"
    )
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    voltage_level_kv: Mapped[float] = mapped_column(
        Float, nullable=False, default=220.0
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="OPERATIONAL"
    )

    # Spatial location foreign key
    location_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Foreign key referencing creator with SET NULL cascade rule
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
    geo_location: Mapped[Optional["Location"]] = relationship(
        "Location",
        back_populates="substations",
    )
    feeders: Mapped[List["Feeder"]] = relationship(
        "Feeder",
        back_populates="substation",
        cascade="all, delete-orphan",
    )
    assets: Mapped[List["Asset"]] = relationship(
        "Asset",
        back_populates="substation",
    )

    def __repr__(self) -> str:
        return f"<Substation(id={self.id}, name='{self.name}', code='{self.code}', status='{self.status}', voltage={self.voltage_level_kv}kV)>"


class Feeder(Base):
    """
    Represents an electrical power distribution feeder emerging from a substation.
    """

    __tablename__ = "feeders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    voltage_level_kv: Mapped[float] = mapped_column(Float, nullable=False, default=33.0)
    nominal_capacity_mva: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="OPERATIONAL")

    substation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("substations.id", ondelete="CASCADE"),
        nullable=False,
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
    substation: Mapped["Substation"] = relationship(
        "Substation",
        back_populates="feeders",
    )
    assets: Mapped[List["Asset"]] = relationship(
        "Asset",
        back_populates="feeder",
    )

    def __repr__(self) -> str:
        return f"<Feeder(id={self.id}, name='{self.name}', code='{self.code}', substation_id={self.substation_id})>"
