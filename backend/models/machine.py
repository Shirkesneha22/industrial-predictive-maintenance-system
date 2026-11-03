"""
Machine SQLAlchemy ORM Model.
Represents an industrial machine or asset on a production line.
"""

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from backend.database import Base
except ImportError:
    from database import Base


class Machine(Base):
    """
    SQLAlchemy model representing an industrial machine or equipment.
    """

    __tablename__ = "machines"

    machine_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique primary key identifier for the machine",
    )
    line_id = Column(
        Integer,
        ForeignKey("production_lines.line_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key reference to the parent production line",
    )
    machine_code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique business identifier or code for the machine (e.g., CNC-01)",
    )
    name = Column(
        String(100),
        nullable=False,
        doc="Full display name of the machine",
    )
    machine_type = Column(
        String(100),
        nullable=False,
        doc="Category or type of machine (e.g., CNC Milling, Centrifugal Pump, Turbofan)",
    )
    manufacturer = Column(
        String(100),
        nullable=True,
        doc="Manufacturer or OEM of the equipment",
    )
    model_number = Column(
        String(100),
        nullable=True,
        doc="Model or serial identifier from the manufacturer",
    )
    installation_date = Column(
        Date,
        nullable=True,
        doc="Date when the machine was commissioned or installed",
    )
    is_active = Column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        doc="Flag indicating whether the machine is actively monitored/operational",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of machine registration (UTC timezone-aware)",
    )

    # Relationship to parent ProductionLine
    production_line = relationship("ProductionLine", back_populates="machines")

    # Relationship to child Sensors
    sensors = relationship(
        "Sensor",
        back_populates="machine",
        cascade="all, delete-orphan",
    )

    # Relationship to MaintenanceWorkOrders (preserves maintenance history; no cascade deletion)
    maintenance_work_orders = relationship(
        "MaintenanceWorkOrder",
        back_populates="machine",
    )

    # Relationship to FailureEvents (preserves failure incident history; no cascade deletion)
    failure_events = relationship(
        "FailureEvent",
        back_populates="machine",
    )

    # Many-to-Many relationship with Part via machine_parts association table
    parts = relationship(
        "Part",
        secondary="machine_parts",
        back_populates="machines",
    )

    def __repr__(self) -> str:
        return f"<Machine(machine_id={self.machine_id}, machine_code='{self.machine_code}', name='{self.name}', line_id={self.line_id})>"
