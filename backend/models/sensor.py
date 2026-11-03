"""
Sensor SQLAlchemy ORM Model.
Represents an industrial sensor attached to a monitored machine.
"""

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from backend.database import Base
except ImportError:
    from database import Base


class Sensor(Base):
    """
    SQLAlchemy model representing an IoT/telemetry sensor mounted on a machine.
    """

    __tablename__ = "sensors"

    sensor_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique primary key identifier for the sensor",
    )
    machine_id = Column(
        Integer,
        ForeignKey("machines.machine_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key reference to the monitored machine",
    )
    sensor_code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique business identifier or telemetry code for the sensor (e.g., SENS-VIB-01)",
    )
    sensor_type = Column(
        String(50),
        nullable=False,
        doc="Type of physical measurement (e.g., Vibration, Temperature, Pressure, Acoustic, RPM)",
    )
    unit = Column(
        String(20),
        nullable=False,
        doc="Physical unit of measurement (e.g., mm/s, °C, bar, kHz, RPM)",
    )
    installation_date = Column(
        Date,
        nullable=True,
        doc="Date when the sensor was installed or calibrated",
    )
    is_active = Column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        doc="Flag indicating whether telemetry data from this sensor is actively consumed",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of sensor registration (UTC timezone-aware)",
    )

    # Relationship to parent Machine
    machine = relationship("Machine", back_populates="sensors")

    # Relationship to child TelemetryEvents (preserves history; no cascade deletion)
    telemetry_events = relationship("TelemetryEvent", back_populates="sensor")

    def __repr__(self) -> str:
        return f"<Sensor(sensor_id={self.sensor_id}, sensor_code='{self.sensor_code}', sensor_type='{self.sensor_type}', unit='{self.unit}', machine_id={self.machine_id})>"
