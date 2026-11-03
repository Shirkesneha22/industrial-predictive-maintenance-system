"""
ProductionLine SQLAlchemy ORM Model.
Represents a production or manufacturing line within an industrial plant.
"""

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from backend.database import Base
except ImportError:
    from database import Base


class ProductionLine(Base):
    """
    SQLAlchemy model representing an assembly/production line within a plant.
    """

    __tablename__ = "production_lines"

    line_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique primary key identifier for the production line",
    )
    plant_id = Column(
        Integer,
        ForeignKey("plants.plant_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key reference to the parent plant",
    )
    line_code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique business identifier or code for the production line (e.g., LINE-01)",
    )
    name = Column(
        String(100),
        nullable=False,
        doc="Full display name of the production line",
    )
    is_active = Column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        doc="Flag indicating whether the line is currently operational",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of production line creation (UTC timezone-aware)",
    )

    # Relationship to parent Plant
    plant = relationship("Plant", back_populates="production_lines")

    # Relationship to child Machines
    machines = relationship(
        "Machine",
        back_populates="production_line",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ProductionLine(line_id={self.line_id}, line_code='{self.line_code}', name='{self.name}', plant_id={self.plant_id})>"
