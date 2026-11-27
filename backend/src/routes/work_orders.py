from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..helpers.auth import get_current_user
from ..models.user import User
from ..schemas.work_order import (
    OutageCause,
    WorkOrderAssign,
    WorkOrderCreate,
    WorkOrderPriority,
    WorkOrderResponse,
    WorkOrderStatus,
    WorkOrderStatusUpdate,
    WorkOrderWithDispatchResponse,
)
from ..services.work_order_service import WorkOrderService

router = APIRouter(prefix="/work-orders", tags=["Work Orders"])


def require_roles(allowed_roles: List[str]):
    """
    Role-based authorization dependency.
    Restricts access to users belonging to specific roles (e.g. Admin, Engineer).
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_name = getattr(current_user.role, "name", None)
        if user_role_name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access forbidden: requires one of {allowed_roles} roles. "
                    f"Current user role: '{user_role_name}'."
                ),
            )
        return current_user

    return role_checker


@router.post(
    "",
    response_model=WorkOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Work Order",
    description="Creates a work order in initial 'Pending' state. Restricted to Engineers and Admins.",
)
def create_work_order(
    payload: WorkOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Engineer"])),
):
    return WorkOrderService.create_work_order(
        db=db,
        payload=payload,
        creator=current_user,
    )


@router.get(
    "",
    response_model=List[WorkOrderResponse],
    summary="List Work Orders",
    description="Retrieves a list of work orders with optional filtering by status, priority, outage cause, or substation.",
)
def list_work_orders(
    status: Optional[WorkOrderStatus] = Query(None, description="Filter by state machine status"),
    priority: Optional[WorkOrderPriority] = Query(None, description="Filter by priority level"),
    outage_cause: Optional[OutageCause] = Query(None, description="Filter by outage root cause"),
    substation_id: Optional[int] = Query(None, description="Filter by substation ID"),
    assigned_to_id: Optional[int] = Query(None, description="Filter by assigned technician user ID"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return WorkOrderService.list_work_orders(
        db=db,
        status_filter=status.value if status else None,
        priority_filter=priority.value if priority else None,
        outage_cause_filter=outage_cause.value if outage_cause else None,
        substation_id=substation_id,
        assigned_to_id=assigned_to_id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{work_order_id}",
    response_model=WorkOrderResponse,
    summary="Get Work Order Details",
    description="Fetches full details of a single work order by its unique ID.",
)
def get_work_order(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return WorkOrderService.get_work_order_by_id(db=db, work_order_id=work_order_id)


@router.post(
    "/{work_order_id}/assign",
    response_model=WorkOrderWithDispatchResponse,
    summary="Assign Technician & Trigger Mobile Dispatch",
    description="Assigns a qualified technician to the work order, updates status to 'Assigned', and dispatches a mobile notification. Restricted to Engineers and Admins.",
)
def assign_technician(
    work_order_id: int,
    payload: WorkOrderAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Engineer"])),
):
    work_order, notification = WorkOrderService.assign_technician(
        db=db,
        work_order_id=work_order_id,
        payload=payload,
        assigner=current_user,
    )
    return WorkOrderWithDispatchResponse(
        work_order=WorkOrderResponse.model_validate(work_order),
        dispatch_notification=notification,
    )


@router.put(
    "/{work_order_id}/status",
    response_model=WorkOrderResponse,
    summary="Update Work Order Status (State Machine)",
    description="Executes a strictly validated status transition in the state machine (e.g., Assigned -> In Progress -> Completed -> Verified). Invalid jumps return HTTP 422.",
)
def update_status(
    work_order_id: int,
    payload: WorkOrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return WorkOrderService.update_status(
        db=db,
        work_order_id=work_order_id,
        payload=payload,
        updater=current_user,
    )
