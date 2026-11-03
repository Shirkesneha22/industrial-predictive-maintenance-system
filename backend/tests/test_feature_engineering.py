"""
Tests for Feature Engineering Service and Anti-Leakage Safeguards.

Validates:
- Multi-window rolling feature calculations (6h, 24h, 7d).
- Accurate statistical properties (mean, std, min, max, trend/slope).
- Strict timestamp cutoff enforcement (recorded_at < prediction_timestamp).
- Terminal failure and post-failure/repair reading exclusion.
- Exclusion of sensor_fault, missing, and invalid readings from machine condition features.
- Reliability indicators tracking missing, invalid, and faulty readings separately.
- Gap detection without unvalidated forward-filling across long intervals.
- Machine-level aggregation and faulty sensor isolation.
- Safe handling of empty windows and insufficient data points.
- Zero reliance on failure-event labels, failure severity, or work-order tables.
"""

from datetime import datetime, timezone, timedelta
import pytest
import numpy as np

from backend.generators.telemetry_constants import (
    QUALITY_NORMAL,
    QUALITY_SENSOR_FAULT,
    QUALITY_INVALID,
    QUALITY_MISSING,
)
from backend.services.feature_engineering import (
    FeatureEngineeringService,
    SensorReading,
    compute_linear_trend_slope,
    compute_sensor_reliability,
    compute_window_sensor_features,
    LOOKBACK_WINDOWS,
)


def create_reading(
    sensor_id: int,
    offset_minutes: int,
    value: float,
    base_time: datetime,
    quality_status: str = QUALITY_NORMAL,
    sensor_type: str = "Vibration",
    sensor_code: str = "SNS-0001",
) -> SensorReading:
    """Helper to create a timestamped sensor reading relative to base_time."""
    recorded_at = base_time + timedelta(minutes=offset_minutes)
    return SensorReading(
        sensor_id=sensor_id,
        recorded_at=recorded_at,
        value=value,
        quality_status=quality_status,
        sensor_type=sensor_type,
        sensor_code=sensor_code,
    )


def test_rolling_feature_calculations_all_windows():
    """Verify rolling statistical features (mean, std, min, max, slope) across 6h, 24h, 7d windows."""
    pred_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    service = FeatureEngineeringService()

    # Generate 7 days of 30-minute readings (336 readings) strictly before pred_time
    readings = []
    # Values linearly increasing from 2.0 to 3.68 over 7 days (168 hours)
    for step in range(336):
        # step 0 is 168 hours before pred_time, step 335 is 30 mins before pred_time
        mins_before = (336 - step) * 30
        t = pred_time - timedelta(minutes=mins_before)
        val = 2.0 + (step * 0.005)
        readings.append(
            SensorReading(
                sensor_id=1,
                recorded_at=t,
                value=round(val, 3),
                quality_status=QUALITY_NORMAL,
                sensor_type="Vibration",
                sensor_code="SNS-0001",
            )
        )

    mch_features = service.extract_machine_features(
        machine_id=1,
        machine_code="MCH-001",
        readings=readings,
        prediction_timestamp=pred_time,
    )

    # 1. Verify all windows present
    assert set(mch_features.windows.keys()) == {"6h", "24h", "7d"}

    feat_6h = mch_features.windows["6h"]["Vibration"]
    feat_24h = mch_features.windows["24h"]["Vibration"]
    feat_7d = mch_features.windows["7d"]["Vibration"]

    # 6h window: 12 readings (6 hours * 2 readings/hr)
    assert feat_6h.count_normal == 12
    assert feat_6h.is_sufficient is True
    assert feat_6h.mean is not None
    assert feat_6h.min is not None
    assert feat_6h.max is not None
    assert feat_6h.min <= feat_6h.mean <= feat_6h.max
    assert feat_6h.trend_slope > 0.0  # Positive trend

    # 24h window: 48 readings
    assert feat_24h.count_normal == 48
    assert feat_24h.is_sufficient is True
    assert feat_24h.mean < feat_6h.mean  # Since values trend upward, 6h recent mean > 24h mean

    # 7d window: 336 readings
    assert feat_7d.count_normal == 336
    assert feat_7d.is_sufficient is True
    assert feat_7d.mean < feat_24h.mean


def test_strict_timestamp_cutoff_anti_leakage():
    """Verify readings at or after prediction_timestamp are strictly excluded."""
    pred_time = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
    service = FeatureEngineeringService()

    readings = [
        # Before cutoff (valid)
        create_reading(1, -60, 2.2, pred_time),
        create_reading(1, -30, 2.3, pred_time),
        create_reading(1, -1, 2.4, pred_time),
        # Exactly at cutoff (MUST BE EXCLUDED)
        create_reading(1, 0, 99.9, pred_time),
        # After cutoff (MUST BE EXCLUDED)
        create_reading(1, 30, 100.0, pred_time),
        create_reading(1, 60, 105.0, pred_time),
    ]

    mch_features = service.extract_machine_features(
        machine_id=1,
        machine_code="MCH-001",
        readings=readings,
        prediction_timestamp=pred_time,
    )

    feat_6h = mch_features.windows["6h"]["Vibration"]
    # Only the 3 readings before cutoff should be included
    assert feat_6h.count_normal == 3
    # Max value should be 2.4, NOT 99.9 or 105.0
    assert feat_6h.max == 2.4
    assert feat_6h.mean == round((2.2 + 2.3 + 2.4) / 3.0, 4)


def test_failure_time_cutoff_and_terminal_exclusion():
    """Verify terminal failure readings and post-failure/repair readings are excluded."""
    pred_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    failure_time = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    service = FeatureEngineeringService()

    readings = [
        create_reading(1, -120, 2.5, pred_time),
        create_reading(1, -60, 3.8, pred_time),
        create_reading(1, -30, 5.2, pred_time),
        # Terminal failure event point
        create_reading(1, 0, 14.5, failure_time),
        # Post-failure repair / downtime readings
        create_reading(1, 30, 0.0, failure_time),
        create_reading(1, 60, 0.0, failure_time),
    ]

    mch_features = service.extract_machine_features(
        machine_id=1,
        machine_code="MCH-001",
        readings=readings,
        prediction_timestamp=pred_time,
        failure_time_cutoff=failure_time,
    )

    feat_6h = mch_features.windows["6h"]["Vibration"]
    assert feat_6h.count_normal == 3
    assert feat_6h.max == 5.2
    assert 14.5 not in [feat_6h.max, feat_6h.min]


def test_sensor_fault_exclusion_from_condition_features():
    """Verify sensor_fault readings are excluded from condition metrics and tracked in reliability."""
    pred_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    service = FeatureEngineeringService()

    readings = [
        create_reading(1, -180, 2.2, pred_time, quality_status=QUALITY_NORMAL),
        create_reading(1, -150, 2.3, pred_time, quality_status=QUALITY_NORMAL),
        # Sensor fault: flatline stuck reading or crazy artifact
        create_reading(1, -120, 999.0, pred_time, quality_status=QUALITY_SENSOR_FAULT),
        create_reading(1, -90, 999.0, pred_time, quality_status=QUALITY_SENSOR_FAULT),
        create_reading(1, -60, 2.4, pred_time, quality_status=QUALITY_NORMAL),
        create_reading(1, -30, 2.5, pred_time, quality_status=QUALITY_NORMAL),
    ]

    mch_features = service.extract_machine_features(
        machine_id=1,
        machine_code="MCH-001",
        readings=readings,
        prediction_timestamp=pred_time,
    )

    feat_6h = mch_features.windows["6h"]["Vibration"]
    # Only 4 normal readings contribute to condition statistics
    assert feat_6h.count_normal == 4
    assert feat_6h.max == 2.5
    assert feat_6h.mean == round((2.2 + 2.3 + 2.4 + 2.5) / 4.0, 4)

    # Reliability indicators must track the 2 sensor fault events
    assert feat_6h.reliability.total_readings == 6
    assert feat_6h.reliability.sensor_fault_count == 2
    assert feat_6h.reliability.fault_rate == pytest.approx(2 / 6, rel=1e-3)
    assert feat_6h.reliability.reliability_score < 100.0


def test_missing_and_invalid_readings_handling():
    """Verify missing (None) and invalid (negative) readings do not poison condition metrics."""
    pred_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    service = FeatureEngineeringService()

    readings = [
        create_reading(1, -120, 2.1, pred_time, quality_status=QUALITY_NORMAL),
        create_reading(1, -90, None, pred_time, quality_status=QUALITY_MISSING),
        create_reading(1, -60, -45.0, pred_time, quality_status=QUALITY_INVALID),
        create_reading(1, -30, 2.3, pred_time, quality_status=QUALITY_NORMAL),
    ]

    mch_features = service.extract_machine_features(
        machine_id=1,
        machine_code="MCH-001",
        readings=readings,
        prediction_timestamp=pred_time,
    )

    feat_6h = mch_features.windows["6h"]["Vibration"]
    # Only 2 normal readings contribute
    assert feat_6h.count_normal == 2
    assert feat_6h.min == 2.1
    assert feat_6h.max == 2.3
    assert feat_6h.mean == 2.2

    # Reliability indicators
    rel = feat_6h.reliability
    assert rel.missing_count == 1
    assert rel.invalid_count == 1
    assert rel.normal_count == 2
    assert rel.total_readings == 4


def test_no_forward_fill_across_long_gaps():
    """Verify long temporal gaps are detected and never forward-filled."""
    pred_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    service = FeatureEngineeringService(max_gap_minutes=120.0)

    # 4-hour gap between readings (-300 mins to -60 mins)
    readings = [
        create_reading(1, -300, 2.0, pred_time),
        create_reading(1, -60, 2.5, pred_time),
        create_reading(1, -30, 2.6, pred_time),
    ]

    mch_features = service.extract_machine_features(
        machine_id=1,
        machine_code="MCH-001",
        readings=readings,
        prediction_timestamp=pred_time,
    )

    feat_6h = mch_features.windows["6h"]["Vibration"]
    assert feat_6h.reliability.has_long_gap is True
    assert feat_6h.reliability.max_gap_minutes == 240.0  # 4 hours = 240 mins
    # Only exact readings exist; count is exactly 3 (no forward-filled points)
    assert feat_6h.count_normal == 3


def test_empty_and_insufficient_windows_safe_handling():
    """Verify service handles completely empty readings or single reading safely without error."""
    pred_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    service = FeatureEngineeringService()

    # Case A: 0 readings
    empty_features = service.extract_machine_features(
        machine_id=1,
        machine_code="MCH-001",
        readings=[],
        prediction_timestamp=pred_time,
    )
    assert empty_features.has_insufficient_data is True
    assert empty_features.faulty_sensor_count == 0

    # Case B: 1 reading (insufficient for std/trend)
    single_reading = [create_reading(1, -30, 2.2, pred_time)]
    single_feat = service.extract_machine_features(
        machine_id=1,
        machine_code="MCH-001",
        readings=single_reading,
        prediction_timestamp=pred_time,
    )
    feat_6h = single_feat.windows["6h"]["Vibration"]
    assert feat_6h.is_sufficient is False
    assert feat_6h.count_normal == 1
    assert feat_6h.mean == 2.2
    assert feat_6h.std == 0.0
    assert feat_6h.trend_slope == 0.0


def test_machine_level_aggregation_and_faulty_sensor_isolation():
    """Verify machine-level aggregation flags faulty sensors without dropping other healthy sensors."""
    pred_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    service = FeatureEngineeringService()

    readings = []
    # 4 normal sensors: Vibration, Temperature, Pressure, Acoustic
    for s_id, s_type in [(1, "Vibration"), (2, "Temperature"), (3, "Pressure"), (4, "Acoustic")]:
        for offset in [-120, -90, -60, -30]:
            readings.append(create_reading(s_id, offset, 50.0, pred_time, QUALITY_NORMAL, s_type, f"SNS-{s_id:04d}"))

    # 1 faulty sensor: Current (all sensor_fault readings)
    for offset in [-120, -90, -60, -30]:
        readings.append(create_reading(5, offset, 24.5, pred_time, QUALITY_SENSOR_FAULT, "Current", "SNS-0005"))

    mch_features = service.extract_machine_features(
        machine_id=1,
        machine_code="MCH-001",
        readings=readings,
        prediction_timestamp=pred_time,
    )

    assert set(mch_features.sensors_monitored) == {"Acoustic", "Current", "Pressure", "Temperature", "Vibration"}
    # The 1 faulty sensor is recognized in faulty_sensor_count
    assert mch_features.faulty_sensor_count == 1

    # Healthy sensors remain reliable
    vib_feat = mch_features.windows["24h"]["Vibration"]
    curr_feat = mch_features.windows["24h"]["Current"]

    assert vib_feat.reliability.is_reliable is True
    assert curr_feat.reliability.is_reliable is False
    assert curr_feat.reliability.sensor_fault_count == 4
    assert curr_feat.count_normal == 0


def test_no_failure_label_leakage():
    """Verify feature extractor relies strictly on telemetry events and has zero access to failure labels."""
    service = FeatureEngineeringService()
    # Confirm through introspection that service methods do not require or accept failure tables
    import inspect
    sig = inspect.signature(service.extract_machine_features)
    param_names = list(sig.parameters.keys())
    assert "failure_event" not in param_names
    assert "severity" not in param_names
    assert "downtime" not in param_names
    assert "work_order" not in param_names
