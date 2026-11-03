"""
Plant SQLAlchemy ORM Model.
Represents an industrial manufacturing facility or plant site.
"""

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from backend.database import Base
except ImportError:
    from database import Base


class Plant(Base):
    """
    SQLAlchemy model representing an industrial manufacturing plant.
    """

    __tablename__ = "plants"

    plant_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique primary key identifier for the plant",
    )
    plant_code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique business identifier or code for the plant (e.g., PLANT-01)",
    )
    name = Column(
        String(100),
        nullable=False,
        doc="Full display name of the industrial facility",
    )
    city = Column(
        String(100),
        nullable=True,
        doc="City where the plant is located",
    )
    state = Column(
        String(100),
        nullable=True,
        doc="State or province where the plant is located",
    )
    is_active = Column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        doc="Flag indicating whether the facility is currently operational",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of plant record creation (UTC timezone-aware)",
    )

    # Relationship to child production lines
    production_lines = relationship(
        "ProductionLine",
        back_populates="plant",
        cascade="all, delete-orphan",
    )

    # Relationship to operating shifts (preserves history; no cascade deletion)
    operating_shifts = relationship("OperatingShift", back_populates="plant")

    def __repr__(self) -> str:
        return f"<Plant(plant_id={self.plant_id}, plant_code='{self.plant_code}', name='{self.name}')>"
