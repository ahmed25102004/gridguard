from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class WorkOrderStatus(str, Enum):
    PENDING = "Pending"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    VERIFIED = "Verified"


class OutageCause(str, Enum):
    OVERLOAD = "Overload"
    EQUIPMENT_FAILURE = "Equipment Failure"
    STORM = "Storm"
    TREE_CONTACT = "Tree Contact"
    MAINTENANCE = "Maintenance"


class WorkOrderPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    EMERGENCY = "Emergency"


class WorkOrderBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200, description="Short summary of work order")
    description: Optional[str] = Field(None, description="Detailed diagnostic or maintenance task description")
    substation_id: Optional[int] = Field(None, description="Associated substation ID")
    equipment_id: Optional[str] = Field(None, max_length=100, description="Specific asset/equipment tag, e.g. AST-TRF-001")
    priority: WorkOrderPriority = Field(default=WorkOrderPriority.MEDIUM, description="Task urgency level")
    outage_cause: Optional[OutageCause] = Field(None, description="Outage cause classification")
    affected_customers_count: int = Field(default=0, ge=0, description="Number of consumers affected by this outage")


class WorkOrderCreate(WorkOrderBase):
    pass


class WorkOrderStatusUpdate(BaseModel):
    status: WorkOrderStatus = Field(..., description="Target status in state machine")
    resolution_notes: Optional[str] = Field(None, description="Field technician observations or completion summary")


class WorkOrderAssign(BaseModel):
    technician_id: int = Field(..., description="User ID of the technician being assigned")


class DispatchNotification(BaseModel):
    work_order_id: int
    technician_id: int
    technician_email: str
    title: str
    priority: str
    status: str
    dispatched_at: datetime


class WorkOrderResponse(WorkOrderBase):
    id: int
    status: str
    priority: str
    outage_cause: Optional[str] = None
    affected_customers_count: int
    assigned_to_id: Optional[int] = None
    created_by_id: int
    version_id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WorkOrderWithDispatchResponse(BaseModel):
    work_order: WorkOrderResponse
    dispatch_notification: Optional[DispatchNotification] = None
