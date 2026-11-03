"""
Part SQLAlchemy ORM Model and Machine-Part Association Table.
Represents industrial components, spare parts, and their equipment compatibility.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from backend.database import Base
except ImportError:
    from database import Base

# Many-to-Many Association Table
machine_parts = Table(
    "machine_parts",
    Base.metadata,
    Column(
        "machine_id",
        Integer,
        ForeignKey("machines.machine_id", ondelete="CASCADE"),
        primary_key=True,
        doc="Foreign key referencing the machine",
    ),
    Column(
        "part_id",
        Integer,
        ForeignKey("parts.part_id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        doc="Foreign key referencing the compatible part",
    ),
)


class Part(Base):
    """
    SQLAlchemy model representing a replacement or constituent machine part/spare.
    """

    __tablename__ = "parts"

    part_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique primary key identifier for the part",
    )
    part_code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique inventory SKU or manufacturer part code (e.g., BRG-SKF-6205)",
    )
    name = Column(
        String(100),
        nullable=False,
        doc="Display name of the part (e.g., Deep Groove Ball Bearing)",
    )
    manufacturer = Column(
        String(100),
        nullable=True,
        doc="Original component manufacturer (e.g., SKF, Timken, Bosch Rexroth)",
    )
    description = Column(
        Text,
        nullable=True,
        doc="Detailed specification, dimensions, or technical notes",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        doc="Part catalog registration timestamp (UTC timezone-aware)",
    )

    # Many-to-Many relationship with Machine
    machines = relationship(
        "Machine",
        secondary=machine_parts,
        back_populates="parts",
    )

    def __repr__(self) -> str:
        return f"<Part(part_id={self.part_id}, part_code='{self.part_code}', name='{self.name}')>"
