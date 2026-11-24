from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..helpers.auth import get_current_user
from ..models.user import User
from ..schemas.asset import (
    AssetCreate,
    AssetListResponse,
    AssetResponse,
    AssetUpdate,
    LocationResponse,
    SpatialRadiusFilter,
)
from ..services.asset_service import AssetService

router = APIRouter(
    prefix="/assets",
    tags=["Grid Asset Inventory"],
)


def _get_user_substation_scope(user: User) -> Optional[int]:
    """
    Extracts regional substation boundary from user permissions/role.
    Admin users have global visibility (None); localized operators are scoped to their assigned substation.
    """
    # If the user has Admin or SuperAdmin role, they have global visibility
    if user.role and user.role.name in ["Admin", "SuperAdmin"]:
        return None

    # For operators and technicians, enforce isolation if user is linked to specific substation
    # If the user has a substation attribute or is scoped, return it; otherwise default to unrestricted or check user
    if hasattr(user, "substation_id") and getattr(user, "substation_id") is not None:
        return getattr(user, "substation_id")

    return None


@router.post(
    "",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new electrical grid asset",
)
def create_asset(
    asset_in: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates a new electrical asset (Transformer, Switch, Cable, Meter, Pole).
    Enforces tenant/substation isolation to prevent cross-region asset assignment.
    """
    scope = _get_user_substation_scope(current_user)
    asset = AssetService.create_asset(db, asset_in, scoped_substation_id=scope)
    return asset


@router.get(
    "",
    response_model=AssetListResponse,
    status_code=status.HTTP_200_OK,
    summary="List electrical assets with pagination and filters",
)
def list_assets(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=500, description="Items per page (supports 500+ records)"),
    search: Optional[str] = Query(None, description="Debounced search query (Asset ID, Name, Manufacturer)"),
    status: Optional[str] = Query(None, description="Filter by status (Active, Maintenance, Fault)"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    substation_id: Optional[int] = Query(None, description="Filter by specific substation ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves paginated grid assets with debounced search and multi-criteria filters.
    Optimized for smooth rendering of 500+ records in the Next.js asset data table.
    """
    scope = _get_user_substation_scope(current_user)
    skip = (page - 1) * limit
    items, total = AssetService.list_assets(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        status_filter=status,
        asset_type=asset_type,
        substation_id=substation_id,
        scoped_substation_id=scope,
    )
    return AssetListResponse(
        total=total,
        page=page,
        limit=limit,
        items=items,
    )


@router.get(
    "/spatial/radius",
    status_code=status.HTTP_200_OK,
    summary="PostGIS spatial radius query for assets within designated zone",
)
def get_assets_in_radius(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Center latitude"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="Center longitude"),
    radius_km: float = Query(5.0, gt=0.0, le=500.0, description="Radius in kilometers"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    substation_id: Optional[int] = Query(None, description="Filter by substation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Spatial PostGIS query retrieving all electrical assets located within a designated zone radius.
    Calculates geographic distance and sorts results by proximity.
    """
    scope = _get_user_substation_scope(current_user)
    results = AssetService.find_assets_within_radius(
        db=db,
        center_lat=lat,
        center_lon=lon,
        radius_km=radius_km,
        asset_type=asset_type,
        substation_id=substation_id,
        scoped_substation_id=scope,
    )

    return [
        {
            "asset": AssetResponse.model_validate(asset),
            "distance_km": dist_km,
        }
        for asset, dist_km in results
    ]


@router.get(
    "/{id}",
    response_model=AssetResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single electrical asset by ID",
)
def get_asset(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves full specification, status, and spatial coordinates of an asset."""
    scope = _get_user_substation_scope(current_user)
    asset = AssetService.get_asset_by_id(db, id, scoped_substation_id=scope)
    return asset


@router.put(
    "/{id}",
    response_model=AssetResponse,
    status_code=status.HTTP_200_OK,
    summary="Update electrical asset details",
)
def update_asset(
    id: int,
    asset_in: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Updates operational state, capacity ratings, or spatial location of an asset."""
    scope = _get_user_substation_scope(current_user)
    asset = AssetService.update_asset(db, id, asset_in, scoped_substation_id=scope)
    return asset


@router.delete(
    "/{id}",
    status_code=status.HTTP_200_OK,
    summary="Delete electrical asset record",
)
def delete_asset(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Removes asset record while validating regional security clearance."""
    scope = _get_user_substation_scope(current_user)
    AssetService.delete_asset(db, id, scoped_substation_id=scope)
    return {"message": f"Asset with ID {id} successfully deleted."}
