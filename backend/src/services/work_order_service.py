import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from ..models.user import User
from ..models.work_order import WorkOrder
from ..schemas.work_order import (
    DispatchNotification,
    OutageCause,
    WorkOrderAssign,
    WorkOrderCreate,
    WorkOrderStatus,
    WorkOrderStatusUpdate,
)

logger = logging.getLogger("gridguard.work_orders")

# Strict State Machine Transition Graph
ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    WorkOrderStatus.PENDING.value: {WorkOrderStatus.ASSIGNED.value},
    WorkOrderStatus.ASSIGNED.value: {
        WorkOrderStatus.IN_PROGRESS.value,
        WorkOrderStatus.PENDING.value,
    },
    WorkOrderStatus.IN_PROGRESS.value: {WorkOrderStatus.COMPLETED.value},
    WorkOrderStatus.COMPLETED.value: {WorkOrderStatus.VERIFIED.value},
    WorkOrderStatus.VERIFIED.value: set(),  # Terminal state
}


class WorkOrderService:
    """
    Manages Work Order business logic, state machine validation,
    atomic database mutations, and technician dispatch notification triggers.
    """

    @staticmethod
    def validate_transition(current_status: str, target_status: str) -> None:
        """
        Enforces strict state machine jumps:
        Pending -> Assigned -> In Progress -> Completed -> Verified.
        Rejects invalid transitions with HTTP 422.
        """
        if current_status == target_status:
            return

        allowed = ALLOWED_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            allowed_str = ", ".join(f"'{s}'" for s in sorted(allowed)) or "None (Terminal State)"
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Invalid status transition from '{current_status}' to '{target_status}'. "
                    f"Allowed transitions from '{current_status}': [{allowed_str}]."
                ),
            )

    @classmethod
    def create_work_order(
        cls,
        db: Session,
        payload: WorkOrderCreate,
        creator: User,
    ) -> WorkOrder:
        """
        Atomically creates a new Work Order in initial 'Pending' status.
        """
        work_order = WorkOrder(
            title=payload.title,
            description=payload.description,
            substation_id=payload.substation_id,
            equipment_id=payload.equipment_id,
            priority=payload.priority.value,
            status=WorkOrderStatus.PENDING.value,
            outage_cause=payload.outage_cause.value if payload.outage_cause else None,
            affected_customers_count=payload.affected_customers_count,
            created_by_id=creator.id,
            version_id=1,
        )

        try:
            db.add(work_order)
            db.commit()
            db.refresh(work_order)
            logger.info("Created WorkOrder #%d (%s) by User #%d", work_order.id, work_order.title, creator.id)
            return work_order
        except Exception as e:
            db.rollback()
            logger.error("Failed to create work order: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database transaction failed while creating work order.",
            )

    @classmethod
    def get_work_order_by_id(cls, db: Session, work_order_id: int) -> WorkOrder:
        """Retrieves a single work order or raises 404."""
        work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not work_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work Order with ID {work_order_id} does not exist.",
            )
        return work_order

    @classmethod
    def list_work_orders(
        cls,
        db: Session,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        outage_cause_filter: Optional[str] = None,
        substation_id: Optional[int] = None,
        assigned_to_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[WorkOrder]:
        """Queries work orders with optional filtering."""
        query = db.query(WorkOrder)

        if status_filter:
            query = query.filter(WorkOrder.status == status_filter)
        if priority_filter:
            query = query.filter(WorkOrder.priority == priority_filter)
        if outage_cause_filter:
            query = query.filter(WorkOrder.outage_cause == outage_cause_filter)
        if substation_id:
            query = query.filter(WorkOrder.substation_id == substation_id)
        if assigned_to_id:
            query = query.filter(WorkOrder.assigned_to_id == assigned_to_id)

        return query.order_by(WorkOrder.created_at.desc()).offset(skip).limit(limit).all()

    @classmethod
    def assign_technician(
        cls,
        db: Session,
        work_order_id: int,
        payload: WorkOrderAssign,
        assigner: User,
    ) -> tuple[WorkOrder, DispatchNotification]:
        """
        Assigns work order to a technician, transitions status to 'Assigned',
        and triggers mobile dispatch notification.
        """
        work_order = cls.get_work_order_by_id(db, work_order_id)

        # Work orders in Completed or Verified state cannot be re-assigned
        if work_order.status in [WorkOrderStatus.COMPLETED.value, WorkOrderStatus.VERIFIED.value]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot assign work order in '{work_order.status}' status.",
            )

        # Validate technician existence
        technician = db.query(User).filter(User.id == payload.technician_id).first()
        if not technician:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Technician with User ID {payload.technician_id} does not exist.",
            )
        if not technician.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign work order to an inactive technician account.",
            )

        # State transition: if Pending, transition to Assigned
        if work_order.status == WorkOrderStatus.PENDING.value:
            cls.validate_transition(work_order.status, WorkOrderStatus.ASSIGNED.value)
            work_order.status = WorkOrderStatus.ASSIGNED.value

        work_order.assigned_to_id = technician.id

        try:
            db.commit()
            db.refresh(work_order)
        except StaleDataError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Concurrent modification conflict detected. Please reload work order.",
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to assign technician: {str(e)}",
            )

        # Dispatch notification payload trigger (Mobile Technician Hub)
        notification = DispatchNotification(
            work_order_id=work_order.id,
            technician_id=technician.id,
            technician_email=technician.email,
            title=work_order.title,
            priority=work_order.priority,
            status=work_order.status,
            dispatched_at=datetime.now(timezone.utc),
        )

        logger.info(
            "DISPATCH ENGINE: Sent mobile notification for WorkOrder #%d to Technician %s (ID: %d)",
            work_order.id,
            technician.email,
            technician.id,
        )

        return work_order, notification

    @classmethod
    def update_status(
        cls,
        db: Session,
        work_order_id: int,
        payload: WorkOrderStatusUpdate,
        updater: User,
    ) -> WorkOrder:
        """
        Updates work order status strictly adhering to state machine transitions.
        """
        work_order = cls.get_work_order_by_id(db, work_order_id)
        target_status = payload.status.value

        # Enforce State Machine validation
        cls.validate_transition(work_order.status, target_status)

        # Business rules for specific target states
        now_utc = datetime.now(timezone.utc)

        if target_status == WorkOrderStatus.IN_PROGRESS.value:
            if not work_order.assigned_to_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Cannot move work order to 'In Progress' without an assigned technician.",
                )

        elif target_status == WorkOrderStatus.COMPLETED.value:
            work_order.completed_at = now_utc

        elif target_status == WorkOrderStatus.VERIFIED.value:
            # Only Engineers or Admins can verify
            updater_role = getattr(updater.role, "name", "")
            if updater_role not in ["Admin", "Engineer"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only Engineers and Admins are authorized to verify and close work orders.",
                )
            work_order.verified_at = now_utc

        work_order.status = target_status

        try:
            db.commit()
            db.refresh(work_order)
            logger.info("WorkOrder #%d transitioned to '%s' by User #%d", work_order.id, target_status, updater.id)
            return work_order
        except StaleDataError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Concurrent modification conflict detected. Please reload work order.",
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update work order status: {str(e)}",
            )
