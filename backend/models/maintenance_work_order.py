"""
MaintenanceWorkOrder SQLAlchemy ORM Model.
Represents an equipment maintenance task or work order.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from backend.database import Base
except ImportError:
    from database import Base


class MaintenanceWorkOrder(Base):
    """
    SQLAlchemy model representing a maintenance work order for a machine.
    Tracks corrective, preventive, and predictive work orders.
    """

    __tablename__ = "maintenance_work_orders"

    work_order_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique primary key identifier for the maintenance work order",
    )
    machine_id = Column(
        Integer,
        ForeignKey("machines.machine_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Foreign key reference to the machine undergoing maintenance",
    )
    technician_id = Column(
        Integer,
        ForeignKey("technicians.technician_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Foreign key reference to the assigned technician (nullable if unassigned)",
    )
    work_type = Column(
        String(50),
        nullable=False,
        doc="Classification of work: preventive, corrective, predictive, inspection",
    )
    priority = Column(
        String(20),
        nullable=False,
        doc="Priority level: low, medium, high, critical",
    )
    status = Column(
        String(30),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
        doc="Current status: pending, in_progress, completed, cancelled",
    )
    description = Column(
        Text,
        nullable=True,
        doc="Detailed diagnostic notes or technician instructions",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        doc="Creation timestamp of the work order (UTC timezone-aware)",
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when maintenance was completed and verified (UTC timezone-aware)",
    )

    # Relationship to parent Machine (preserves history; no cascade deletion)
    machine = relationship("Machine", back_populates="maintenance_work_orders")

    # Relationship to assigned Technician (preserves history; no cascade deletion)
    technician = relationship("Technician", back_populates="maintenance_work_orders")

    def __repr__(self) -> str:
        return (
            f"<MaintenanceWorkOrder(work_order_id={self.work_order_id}, machine_id={self.machine_id}, "
            f"work_type='{self.work_type}', priority='{self.priority}', status='{self.status}')>"
        )
