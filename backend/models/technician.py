"""
Technician SQLAlchemy ORM Model.
Represents an industrial maintenance technician or specialist engineer.
"""

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from backend.database import Base
except ImportError:
    from database import Base


class Technician(Base):
    """
    SQLAlchemy model representing a field technician or maintenance personnel.
    """

    __tablename__ = "technicians"

    technician_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique primary key identifier for the technician",
    )
    technician_code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique employee or technician badge identifier (e.g., TECH-001)",
    )
    name = Column(
        String(100),
        nullable=False,
        doc="Full display name of the technician",
    )
    specialization = Column(
        String(100),
        nullable=True,
        doc="Engineering domain: Mechanical, Electrical, Hydraulics, Vibration Analysis, Robotics",
    )
    email = Column(
        String(150),
        unique=True,
        nullable=True,
        index=True,
        doc="Corporate email address for dispatch notifications",
    )
    is_active = Column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        doc="Flag indicating whether technician is active for work order assignment",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        doc="Technician onboarding timestamp (UTC timezone-aware)",
    )

    # One-to-Many relationship with MaintenanceWorkOrder (preserves history; no cascade deletion)
    maintenance_work_orders = relationship(
        "MaintenanceWorkOrder",
        back_populates="technician",
    )

    def __repr__(self) -> str:
        return f"<Technician(technician_id={self.technician_id}, technician_code='{self.technician_code}', name='{self.name}')>"
