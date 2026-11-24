from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from ..models.asset import AssetStatus, AssetType


class LocationBase(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    elevation_m: Optional[float] = None


class LocationCreate(LocationBase):
    pass


class LocationResponse(LocationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetBase(BaseModel):
    asset_id: str = Field(..., min_length=3, max_length=50, description="Unique asset code e.g. AST-TRF-001")
    name: str = Field(..., min_length=2, max_length=120)
    asset_type: AssetType = Field(default=AssetType.TRANSFORMER)
    manufacturer: str = Field(..., min_length=2, max_length=100)
    model_number: Optional[str] = None
    serial_number: Optional[str] = None
    capacity_kva: Optional[float] = Field(None, ge=0.0)
    voltage_rating_kv: Optional[float] = Field(None, ge=0.0)
    status: AssetStatus = Field(default=AssetStatus.ACTIVE)
    health_score: float = Field(default=100.0, ge=0.0, le=100.0)
    substation_id: int
    feeder_id: Optional[int] = None
    installation_date: Optional[datetime] = None


class AssetCreate(AssetBase):
    location: Optional[LocationCreate] = None
    location_id: Optional[int] = None


class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    asset_type: Optional[AssetType] = None
    manufacturer: Optional[str] = Field(None, min_length=2, max_length=100)
    model_number: Optional[str] = None
    serial_number: Optional[str] = None
    capacity_kva: Optional[float] = Field(None, ge=0.0)
    voltage_rating_kv: Optional[float] = Field(None, ge=0.0)
    status: Optional[AssetStatus] = None
    health_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    substation_id: Optional[int] = None
    feeder_id: Optional[int] = None
    location_id: Optional[int] = None
    location: Optional[LocationCreate] = None
    last_inspection_date: Optional[datetime] = None


class SubstationBrief(BaseModel):
    id: int
    name: str
    code: str
    voltage_level_kv: float

    model_config = ConfigDict(from_attributes=True)


class FeederBrief(BaseModel):
    id: int
    name: str
    code: str
    voltage_level_kv: float

    model_config = ConfigDict(from_attributes=True)


class AssetResponse(BaseModel):
    id: int
    asset_id: str
    name: str
    asset_type: str
    manufacturer: str
    model_number: Optional[str]
    serial_number: Optional[str]
    capacity_kva: Optional[float]
    voltage_rating_kv: Optional[float]
    status: str
    health_score: float
    substation_id: int
    feeder_id: Optional[int]
    location_id: Optional[int]
    installation_date: Optional[datetime]
    last_inspection_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    location: Optional[LocationResponse] = None
    substation: Optional[SubstationBrief] = None
    feeder: Optional[FeederBrief] = None

    model_config = ConfigDict(from_attributes=True)


class AssetListResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[AssetResponse]


class SpatialRadiusFilter(BaseModel):
    center_lat: float = Field(..., ge=-90.0, le=90.0)
    center_lon: float = Field(..., ge=-180.0, le=180.0)
    radius_km: float = Field(..., gt=0.0, le=500.0, description="Search radius in kilometers")
    asset_type: Optional[AssetType] = None
    substation_id: Optional[int] = None
