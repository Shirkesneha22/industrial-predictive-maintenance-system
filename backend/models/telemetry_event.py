"""
TelemetryEvent SQLAlchemy ORM Model.
Represents a time-series telemetry measurement recorded by an industrial sensor.
"""

from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from backend.database import Base
except ImportError:
    from database import Base


class TelemetryEvent(Base):
    """
    SQLAlchemy model representing an individual sensor telemetry data point.
    Designed for high-frequency time-series logging with quality assessment.
    """

    __tablename__ = "telemetry_events"

    event_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        doc="High-capacity primary key identifier for telemetry events",
    )
    sensor_id = Column(
        Integer,
        ForeignKey("sensors.sensor_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Foreign key referencing the sensor that recorded this telemetry reading",
    )
    recorded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Exact timestamp when the sensor measured this reading (UTC timezone-aware)",
    )
    value = Column(
        Float,
        nullable=True,
        doc="Numeric measurement value (nullable to explicitly represent missing readings)",
    )
    quality_status = Column(
        String(30),
        nullable=False,
        default="normal",
        server_default="normal",
        doc="Quality classification: normal, missing, invalid, sensor_fault",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        doc="System ingestion timestamp when the record was received (UTC timezone-aware)",
    )

    # Composite index for time-series range queries per sensor
    __table_args__ = (
        Index("ix_telemetry_events_sensor_recorded", "sensor_id", "recorded_at"),
    )

    # Relationship to parent Sensor (preserves history; no cascade deletion)
    sensor = relationship("Sensor", back_populates="telemetry_events")

    def __repr__(self) -> str:
        return (
            f"<TelemetryEvent(event_id={self.event_id}, sensor_id={self.sensor_id}, "
            f"recorded_at='{self.recorded_at}', value={self.value}, quality_status='{self.quality_status}')>"
        )
