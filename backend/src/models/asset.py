from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .location import Location
    from .substation import Feeder, Substation
    from .work_order import WorkOrder


class AssetType(str, Enum):
    """Recognized physical electrical asset categories in GridGuard."""
    TRANSFORMER = "Transformer"
    SWITCH = "Switch"
    CABLE = "Cable"
    METER = "Meter"
    POLE = "Pole"


class AssetStatus(str, Enum):
    """Operational lifecycle states of grid infrastructure."""
    ACTIVE = "Active"
    MAINTENANCE = "Maintenance"
    FAULT = "Fault"
    DECOMMISSIONED = "Decommissioned"


class Asset(Base):
    """
    Core electrical asset entity representing physical power grid equipment.
    Includes foreign key indices and tenant/substation scoping support.
    """

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    asset_id: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    asset_type: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False, default=AssetType.TRANSFORMER.value
    )
    manufacturer: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False
    )
    model_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )
    capacity_kva: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    voltage_rating_kv: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False, default=AssetStatus.ACTIVE.value
    )
    health_score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)

    # Substation scoping foreign key (Mandatory for multi-tenant / zone isolation)
    substation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("substations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Feeder scoping foreign key (Optional)
    feeder_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("feeders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Location foreign key (Spatial PostGIS linkage)
    location_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    installation_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_inspection_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
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
        back_populates="assets",
        lazy="selectin",
    )
    feeder: Mapped[Optional["Feeder"]] = relationship(
        "Feeder",
        back_populates="assets",
        lazy="selectin",
    )
    location: Mapped[Optional["Location"]] = relationship(
        "Location",
        back_populates="assets",
        lazy="selectin",
    )
    work_orders: Mapped[List["WorkOrder"]] = relationship(
        "WorkOrder",
        back_populates="asset",
        cascade="all, delete-orphan",
    )

    # Multi-column indexing for optimized sub-50ms dashboard filtering
    __table_args__ = (
        Index("ix_assets_substation_status", "substation_id", "status"),
        Index("ix_assets_type_status", "asset_type", "status"),
        Index("ix_assets_manufacturer_type", "manufacturer", "asset_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<Asset(id={self.id}, asset_id='{self.asset_id}', "
            f"type='{self.asset_type}', status='{self.status}', "
            f"substation_id={self.substation_id})>"
        )
