"""
FailureEvent SQLAlchemy ORM Model.
Represents an unexpected equipment breakdown, stoppage, or failure incident.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from backend.database import Base
except ImportError:
    from database import Base


class FailureEvent(Base):
    """
    SQLAlchemy model representing an equipment failure incident.
    Stores historical downtime and failure modes for predictive maintenance modeling.
    """

    __tablename__ = "failure_events"

    failure_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique primary key identifier for the failure incident",
    )
    machine_id = Column(
        Integer,
        ForeignKey("machines.machine_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Foreign key reference to the machine that experienced the failure",
    )
    failure_type = Column(
        String(100),
        nullable=False,
        doc="Classification of failure mode (e.g., Bearing Failure, Spindle Seizure, Cavitation, Overheating)",
    )
    severity = Column(
        String(20),
        nullable=False,
        doc="Severity rating of the incident: low, medium, high, critical",
    )
    failure_time = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Exact timestamp when the breakdown occurred (UTC timezone-aware)",
    )
    downtime_minutes = Column(
        Integer,
        nullable=True,
        doc="Total unplanned downtime duration in minutes",
    )
    description = Column(
        Text,
        nullable=True,
        doc="Detailed engineering report or root cause observation",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        doc="Record logging timestamp (UTC timezone-aware)",
    )

    # Relationship to parent Machine (preserves failure history; no cascade deletion)
    machine = relationship("Machine", back_populates="failure_events")

    def __repr__(self) -> str:
        return (
            f"<FailureEvent(failure_id={self.failure_id}, machine_id={self.machine_id}, "
            f"failure_type='{self.failure_type}', severity='{self.severity}', failure_time='{self.failure_time}')>"
        )
