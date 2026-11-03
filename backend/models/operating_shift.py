"""
OperatingShift SQLAlchemy ORM Model.
Represents an operating work shift for an industrial plant.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from backend.database import Base
except ImportError:
    from database import Base


class OperatingShift(Base):
    """
    SQLAlchemy model representing a plant operating shift.
    Stores explicit start and end timestamps to support shifts crossing midnight.
    """

    __tablename__ = "operating_shifts"

    shift_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique primary key identifier for the operating shift",
    )
    plant_id = Column(
        Integer,
        ForeignKey("plants.plant_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Foreign key reference to the plant where this shift operates",
    )
    shift_name = Column(
        String(50),
        nullable=False,
        doc="Display name of the shift (e.g., Morning Shift, Evening Shift, Night Shift)",
    )
    start_time = Column(
        DateTime(timezone=True),
        nullable=False,
        doc="Actual start timestamp for the operating shift (UTC timezone-aware)",
    )
    end_time = Column(
        DateTime(timezone=True),
        nullable=False,
        doc="Actual end timestamp for the operating shift (UTC timezone-aware)",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        doc="Record creation timestamp (UTC timezone-aware)",
    )

    # Composite index for shift window range lookups per plant
    __table_args__ = (
        Index("ix_operating_shifts_plant_start_end", "plant_id", "start_time", "end_time"),
    )

    # Relationship to parent Plant (preserves historical operational shift data)
    plant = relationship("Plant", back_populates="operating_shifts")

    def __repr__(self) -> str:
        return (
            f"<OperatingShift(shift_id={self.shift_id}, plant_id={self.plant_id}, "
            f"shift_name='{self.shift_name}', start_time='{self.start_time}', end_time='{self.end_time}')>"
        )
