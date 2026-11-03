"""
Master Data and Telemetry Generators Package.
Provides industrial master asset generators and telemetry simulators.
"""

from backend.generators.master_data_constants import (
    DEFAULT_RANDOM_SEED,
    PLANTS_DATA,
    PRODUCTION_LINES_DATA,
    TECHNICIANS_DATA,
    SPARE_PARTS_DATA,
    MACHINE_TYPES_POOL,
    SENSOR_CONFIGURATIONS,
)
from backend.generators.master_data_generator import MasterDataGenerator
from backend.generators.telemetry_constants import (
    DEFAULT_TELEMETRY_SEED,
    WINDOW_START_UTC,
    WINDOW_END_UTC,
    READINGS_PER_SENSOR,
    TARGET_SENSOR_COUNT,
    TOTAL_TELEMETRY_RECORDS,
    QUALITY_NORMAL,
    QUALITY_SENSOR_FAULT,
    QUALITY_INVALID,
    QUALITY_MISSING,
)
from backend.generators.telemetry_generator import TelemetryGenerator

__all__ = [
    "DEFAULT_RANDOM_SEED",
    "PLANTS_DATA",
    "PRODUCTION_LINES_DATA",
    "TECHNICIANS_DATA",
    "SPARE_PARTS_DATA",
    "MACHINE_TYPES_POOL",
    "SENSOR_CONFIGURATIONS",
    "MasterDataGenerator",
    "DEFAULT_TELEMETRY_SEED",
    "WINDOW_START_UTC",
    "WINDOW_END_UTC",
    "READINGS_PER_SENSOR",
    "TARGET_SENSOR_COUNT",
    "TOTAL_TELEMETRY_RECORDS",
    "QUALITY_NORMAL",
    "QUALITY_SENSOR_FAULT",
    "QUALITY_INVALID",
    "QUALITY_MISSING",
    "TelemetryGenerator",
]
