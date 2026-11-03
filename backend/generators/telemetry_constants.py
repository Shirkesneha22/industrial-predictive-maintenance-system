"""
Telemetry Generator Constants for Industrial Predictive Maintenance System.
Defines temporal windows, sampling rates, physical sensor baselines,
IST shift schedules, and data quality error probabilities.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any

# Master Random Seed
DEFAULT_TELEMETRY_SEED = 20261022

# Temporal Window (90 calendar days, exclusive end)
WINDOW_START_UTC = datetime(2026, 8, 4, 0, 0, 0, tzinfo=timezone.utc)
WINDOW_END_UTC = datetime(2026, 11, 2, 0, 0, 0, tzinfo=timezone.utc)

SAMPLING_INTERVAL_MINUTES = 30
READINGS_PER_SENSOR = 4320  # 90 days * 24 hours/day * 2 readings/hour
TARGET_SENSOR_COUNT = 500
TOTAL_TELEMETRY_RECORDS = 2160000  # 500 * 4320

# Streaming Chunk Configuration (9 chunks of 10 days = 480 steps per chunk)
CHUNK_DAYS = 10
STEPS_PER_CHUNK = 480  # 10 days * 48 steps/day
TOTAL_CHUNKS = 9  # 9 * 480 = 4320 steps

# Timezone offsets
IST_OFFSET = timedelta(hours=5, minutes=30)

# Data Quality Statuses
QUALITY_NORMAL = "normal"
QUALITY_SENSOR_FAULT = "sensor_fault"
QUALITY_INVALID = "invalid"
QUALITY_MISSING = "missing"

# Target Quality Proportions across the dataset
PROB_MISSING = 0.015       # ~1.5%
PROB_INVALID = 0.015       # ~1.5%
PROB_SENSOR_FAULT = 0.020  # ~2.0%
# Remaining ~95.0% is normal (healthy operation + physical degradation)

# Physical Sensor Baseline Specifications
SENSOR_PHYSICS_PROFILES: Dict[str, Dict[str, Any]] = {
    "Vibration": {
        "unit": "mm/s",
        "nominal_mean": 2.2,
        "nominal_std": 0.35,
        "min_physical": 0.0,
        "max_physical": 45.0,
        "precision": 3,
        "degradation_peak": 14.5,
    },
    "Temperature": {
        "unit": "°C",
        "nominal_mean": 56.0,
        "nominal_std": 2.8,
        "min_physical": -10.0,
        "max_physical": 180.0,
        "precision": 2,
        "degradation_peak": 98.0,
    },
    "Acoustic": {
        "unit": "dB",
        "nominal_mean": 68.0,
        "nominal_std": 2.2,
        "min_physical": 20.0,
        "max_physical": 130.0,
        "precision": 2,
        "degradation_peak": 96.0,
    },
    "Pressure": {
        "unit": "bar",
        "nominal_mean": 140.0,
        "nominal_std": 5.5,
        "min_physical": 0.0,
        "max_physical": 320.0,
        "precision": 2,
        "degradation_drop": 75.0,  # Pressure drops during seal/valve degradation
    },
    "Current": {
        "unit": "A",
        "nominal_mean": 24.5,
        "nominal_std": 1.8,
        "min_physical": 0.0,
        "max_physical": 110.0,
        "precision": 2,
        "degradation_peak": 46.0,
    },
}

# IST Operating Shift Hourly Definitions (in local IST hours 0..23)
# Morning: 06:00 to 14:00 IST
# Afternoon: 14:00 to 22:00 IST
# Night: 22:00 to 06:00 IST next day
SHIFT_LOAD_FACTORS = {
    "morning": 1.00,      # Full rated production load
    "afternoon": 1.04,    # Peak production + thermal load
    "night": 0.80,        # Reduced nighttime throughput
    "maintenance": 0.15,  # Sunday 00:00 to 08:00 IST maintenance / idle
}
