from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .user import User
    from .substation import Substation


class WorkOrder(Base):
    """
    Represents an electrical substation maintenance or outage work order.
    Enforces atomic state transitions, optimistic locking, outage categorization,
    and mobile technician dispatch metadata.
    """

    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Substation & Equipment reference
    substation_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("substations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    equipment_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )

    # State Machine: Pending -> Assigned -> In Progress -> Completed -> Verified
    status: Mapped[str] = mapped_column(
        String(50), default="Pending", nullable=False, index=True
    )
    priority: Mapped[str] = mapped_column(
        String(20), default="Medium", nullable=False
    )

    # Outage cause tagging & customer tracking
    outage_cause: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )
    affected_customers_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    # Assignment & Ownership
    assigned_to_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Optimistic locking column for atomic transactional safety
    version_id: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    assigned_to: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_to_id],
        lazy="selectin",
    )
    created_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_id],
        lazy="selectin",
    )
    substation: Mapped[Optional["Substation"]] = relationship(
        "Substation",
        lazy="selectin",
    )

    __mapper_args__ = {
        "version_id_col": version_id
    }

    def __repr__(self) -> str:
        return (
            f"<WorkOrder(id={self.id}, title='{self.title}', status='{self.status}', "
            f"priority='{self.priority}', assigned_to={self.assigned_to_id}, version={self.version_id})>"
        )
