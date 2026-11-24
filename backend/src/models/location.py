from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, Float, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from ..database import Base

if TYPE_CHECKING:
    from .asset import Asset
    from .substation import Substation


class Location(Base):
    """
    Represents a geospatial location entity within the GridGuard platform.
    Leverages PostGIS geometry with SRID 4326 (WGS 84 GPS coordinates) and GIST spatial indexing.
    """

    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    elevation_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # PostGIS Point geometry: POINT(longitude latitude) in SRID 4326
    # GIST spatial index enabled for sub-50ms radius/containment queries
    geom: Mapped[Optional[str]] = mapped_column(
        Geometry(
            geometry_type="POINT",
            srid=4326,
            spatial_index=True,
        ),
        nullable=True,
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
    assets: Mapped[List["Asset"]] = relationship(
        "Asset",
        back_populates="location",
    )
    substations: Mapped[List["Substation"]] = relationship(
        "Substation",
        back_populates="geo_location",
    )

    # Composite B-tree index on (latitude, longitude) for fast fallback queries
    __table_args__ = (
        Index("ix_locations_lat_lon", "latitude", "longitude"),
    )

    def __repr__(self) -> str:
        return f"<Location(id={self.id}, lat={self.latitude}, lon={self.longitude}, name='{self.name}')>"
