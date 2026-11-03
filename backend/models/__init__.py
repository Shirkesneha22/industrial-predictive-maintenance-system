"""
Database Models Package.
Contains SQLAlchemy ORM models representing industrial entities and assets.
"""

try:
    from backend.models.plant import Plant
    from backend.models.production_line import ProductionLine
    from backend.models.machine import Machine
    from backend.models.sensor import Sensor
    from backend.models.telemetry_event import TelemetryEvent
    from backend.models.operating_shift import OperatingShift
    from backend.models.maintenance_work_order import MaintenanceWorkOrder
    from backend.models.failure_event import FailureEvent
    from backend.models.part import Part, machine_parts
    from backend.models.technician import Technician
except ImportError:
    from models.plant import Plant
    from models.production_line import ProductionLine
    from models.machine import Machine
    from models.sensor import Sensor
    from models.telemetry_event import TelemetryEvent
    from models.operating_shift import OperatingShift
    from models.maintenance_work_order import MaintenanceWorkOrder
    from models.failure_event import FailureEvent
    from models.part import Part, machine_parts
    from models.technician import Technician

__all__ = [
    "Plant",
    "ProductionLine",
    "Machine",
    "Sensor",
    "TelemetryEvent",
    "OperatingShift",
    "MaintenanceWorkOrder",
    "FailureEvent",
    "Part",
    "machine_parts",
    "Technician",
]
