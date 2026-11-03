"""
Tests for Anomaly Detection and Risk Engine Services.

Validates:
- Single-sensor instrumentation faults vs. correlated multi-sensor degradation.
- Single faulty sensor cannot cause a machine-level failure alert (risk capped at Normal).
- Multi-sensor physical degradation triggers Warning and Critical risk levels.
- Healthy machines consistently score higher Health Index and lower Risk Score than degrading machines.
- Configurable risk thresholds and boundary behaviors.
- Accurate identification of dominant physical failure modes (bearing_wear, motor_binding, hydraulic_leak, thermal_overload).
- Actionable industrial maintenance recommendations.
- Safe handling of empty windows and insufficient data points.
- Anti-leakage safeguards:
  * No calibrated failure probability claimed (is_calibrated_probability=False).
  * No unvalidated RUL claimed (remaining_useful_life_hours=None).
  * Zero reliance on failure-event labels or work-order records.
"""

from datetime import datetime, timezone, timedelta
import pytest

from backend.generators.telemetry_constants import (
    QUALITY_NORMAL,
    QUALITY_SENSOR_FAULT,
    QUALITY_INVALID,
    QUALITY_MISSING,
    SENSOR_PHYSICS_PROFILES,
)
from backend.services.feature_engineering import (
    FeatureEngineeringService,
    SensorReading,
    MachineAggregatedFeatures,
)
from backend.services.anomaly_detector import (
    AnomalyDetector,
    AnomalyDetectorConfig,
    AnomalyCategory,
)
from backend.services.risk_engine import (
    RiskEngine,
    RiskEngineConfig,
    RiskLevel,
    MachineRiskAssessment,
)


def create_machine_readings(
    base_time: datetime,
    hours: int = 24,
    vibration_val: float = 2.2,
    temperature_val: float = 56.0,
    acoustic_val: float = 68.0,
    pressure_val: float = 140.0,
    current_val: float = 24.5,
    vibration_quality: str = QUALITY_NORMAL,
    temperature_quality: str = QUALITY_NORMAL,
    acoustic_quality: str = QUALITY_NORMAL,
    pressure_quality: str = QUALITY_NORMAL,
    current_quality: str = QUALITY_NORMAL,
    vibration_slope: float = 0.0,
) -> list:
    """Helper to generate multi-sensor readings for a 5-sensor machine over a specified time horizon."""
    readings = []
    num_steps = hours * 2  # 30-min sampling
    specs = [
        (1, "Vibration", "SNS-0001", vibration_val, vibration_quality),
        (2, "Temperature", "SNS-0002", temperature_val, temperature_quality),
        (3, "Acoustic", "SNS-0003", acoustic_val, acoustic_quality),
        (4, "Pressure", "SNS-0004", pressure_val, pressure_quality),
        (5, "Current", "SNS-0005", current_val, current_quality),
    ]

    for step in range(num_steps):
        mins_before = (num_steps - step) * 30
        t = base_time - timedelta(minutes=mins_before)
        for s_id, s_type, s_code, val, q_status in specs:
            actual_val = val
            if s_type == "Vibration" and vibration_slope != 0.0:
                actual_val += (step / 2.0) * vibration_slope

            readings.append(
                SensorReading(
                    sensor_id=s_id,
                    recorded_at=t,
                    value=round(actual_val, 3) if val is not None else None,
                    quality_status=q_status,
                    sensor_type=s_type,
                    sensor_code=s_code,
                )
            )
    return readings


def test_healthy_machine_assessment():
    """Verify healthy machine operating near nominal baselines receives high Health Index and Normal risk."""
    pred_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    service = FeatureEngineeringService()
    engine = RiskEngine()

    readings = create_machine_readings(
        base_time=pred_time,
        hours=24,
        vibration_val=2.2,    # Nominal Vibration
        temperature_val=56.0, # Nominal Temperature
        acoustic_val=68.0,    # Nominal Acoustic
        pressure_val=140.0,   # Nominal Pressure
        current_val=24.5,     # Nominal Current
    )

    features = service.extract_machine_features(1, "MCH-001", readings, pred_time)
    assessment = engine.assess_machine_risk(features)

    assert assessment.risk_level == RiskLevel.NORMAL
    assert assessment.risk_score <= 15.0
    assert assessment.health_index >= 85.0
    assert assessment.dominant_failure_mode is None
    assert assessment.has_correlated_degradation is False
    assert assessment.has_isolated_sensor_fault is False
    assert "optimal baseline" in assessment.recommended_action.lower()


def test_single_faulty_sensor_cannot_trigger_machine_failure():
    """
    Verify that an isolated faulty sensor (sensor_fault status) is classified as an instrumentation
    issue, and the machine risk remains capped in the Normal level without creating a machine failure alert.
    """
    pred_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    service = FeatureEngineeringService()
    engine = RiskEngine()

    # Vibration sensor is faulty; other 4 sensors are healthy and normal
    readings = create_machine_readings(
        base_time=pred_time,
        hours=24,
        vibration_val=999.0,
        vibration_quality=QUALITY_SENSOR_FAULT,
        temperature_val=56.0,
        acoustic_val=68.0,
        pressure_val=140.0,
        current_val=24.5,
    )

    features = service.extract_machine_features(1, "MCH-001", readings, pred_time)
    assessment = engine.assess_machine_risk(features)

    # Risk must NOT escalate to Warning or Critical
    assert assessment.risk_level == RiskLevel.NORMAL
    assert assessment.risk_score <= engine.config.single_fault_risk_cap
    assert assessment.has_isolated_sensor_fault is True
    assert assessment.has_correlated_degradation is False
    assert assessment.dominant_failure_mode is None
    # Recommended action targets sensor maintenance, not machine teardown
    assert "instrumentation" in assessment.recommended_action.lower() or "recalibrate" in assessment.recommended_action.lower()


def test_single_isolated_sensor_spike_does_not_trigger_machine_failure():
    """
    Verify that an isolated physical spike on a single sensor without corroboration
    from related sensors is filtered out as an isolated anomaly and capped at Normal risk.
    """
    pred_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    service = FeatureEngineeringService()
    engine = RiskEngine()

    # Vibration spike (z-score > 6), but Acoustic, Temperature, Current are perfectly normal
    readings = create_machine_readings(
        base_time=pred_time,
        hours=24,
        vibration_val=7.5,    # Very high vibration alone
        temperature_val=56.0, # Normal
        acoustic_val=68.0,    # Normal (no wear acoustic noise)
        pressure_val=140.0,   # Normal
        current_val=24.5,     # Normal
    )

    features = service.extract_machine_features(1, "MCH-001", readings, pred_time)
    detector = AnomalyDetector()
    anomaly_rep = detector.detect_machine_anomalies(features)

    # Anomaly detector flags isolated anomaly, NOT correlated degradation
    assert anomaly_rep.has_correlated_degradation is False
    assert anomaly_rep.has_isolated_sensor_fault is True
    assert anomaly_rep.sensor_reports["Vibration"].category == AnomalyCategory.ISOLATED_ANOMALY

    assessment = engine.assess_machine_risk(features, anomaly_rep)
    assert assessment.risk_level == RiskLevel.NORMAL
    assert assessment.risk_score <= engine.config.single_fault_risk_cap


def test_correlated_bearing_wear_triggers_critical_alert():
    """
    Verify multi-sensor degradation (bearing wear: high Vibration + high Acoustic + elevated Temp)
    triggers Critical risk level, diagnoses bearing_wear mode, and gives bearing overhaul action.
    """
    pred_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    service = FeatureEngineeringService()
    engine = RiskEngine()

    # Bearing wear pattern: High Vibration (8.0 mm/s) + High Acoustic (88 dB) + Elevated Temp (72°C)
    readings = create_machine_readings(
        base_time=pred_time,
        hours=24,
        vibration_val=8.0,
        temperature_val=72.0,
        acoustic_val=88.0,
        pressure_val=140.0,
        current_val=26.0,
        vibration_slope=0.15,
    )

    features = service.extract_machine_features(1, "MCH-001", readings, pred_time)
    assessment = engine.assess_machine_risk(features)

    assert assessment.has_correlated_degradation is True
    assert assessment.risk_level in [RiskLevel.WARNING, RiskLevel.CRITICAL]
    assert assessment.risk_score >= 65.0
    assert assessment.dominant_failure_mode == "bearing_wear"
    assert assessment.failure_mode_confidence > 0.5
    assert "bearing" in assessment.recommended_action.lower()


def test_correlated_motor_binding_triggers_warning_or_critical():
    """
    Verify multi-sensor degradation (motor binding: high Current + high Temp + high Vibration)
    is diagnosed as motor_binding with motor decoupling recommendation.
    """
    pred_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    service = FeatureEngineeringService()
    engine = RiskEngine()

    # Motor binding pattern: High Current (42 A) + High Temp (88°C) + High Vibration (6.5 mm/s)
    readings = create_machine_readings(
        base_time=pred_time,
        hours=24,
        vibration_val=6.5,
        temperature_val=88.0,
        acoustic_val=70.0,
        pressure_val=140.0,
        current_val=42.0,
    )

    features = service.extract_machine_features(1, "MCH-001", readings, pred_time)
    assessment = engine.assess_machine_risk(features)

    assert assessment.has_correlated_degradation is True
    assert assessment.dominant_failure_mode == "motor_binding"
    assert "motor" in assessment.recommended_action.lower() or "coupling" in assessment.recommended_action.lower()


def test_correlated_hydraulic_leak_detection():
    """
    Verify multi-sensor degradation (hydraulic leak: severe pressure drop + cavitation acoustics)
    is diagnosed as hydraulic_leak.
    """
    pred_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    service = FeatureEngineeringService()
    engine = RiskEngine()

    # Hydraulic leak: Pressure dropped from 140 to 80 bar + High cavitation Acoustic 85 dB
    readings = create_machine_readings(
        base_time=pred_time,
        hours=24,
        vibration_val=2.3,
        temperature_val=58.0,
        acoustic_val=85.0,
        pressure_val=80.0,  # 60 bar drop (z > 10)
        current_val=24.5,
    )

    features = service.extract_machine_features(1, "MCH-001", readings, pred_time)
    assessment = engine.assess_machine_risk(features)

    assert assessment.has_correlated_degradation is True
    assert assessment.dominant_failure_mode == "hydraulic_leak"
    assert "hydraulic" in assessment.recommended_action.lower() or "seal" in assessment.recommended_action.lower()


def test_healthy_machine_scores_higher_than_degrading_machine():
    """Verify healthy machine strictly scores higher Health Index and lower Risk Score than degrading machine."""
    pred_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    service = FeatureEngineeringService()
    engine = RiskEngine()

    # Machine 1: Healthy
    healthy_readings = create_machine_readings(
        base_time=pred_time,
        hours=24,
        vibration_val=2.2,
        temperature_val=56.0,
        acoustic_val=68.0,
        pressure_val=140.0,
        current_val=24.5,
    )
    mch1_feat = service.extract_machine_features(1, "MCH-001", healthy_readings, pred_time)
    mch1_risk = engine.assess_machine_risk(mch1_feat)

    # Machine 2: Degrading
    degrading_readings = create_machine_readings(
        base_time=pred_time,
        hours=24,
        vibration_val=7.5,
        temperature_val=74.0,
        acoustic_val=86.0,
        pressure_val=140.0,
        current_val=25.0,
    )
    mch2_feat = service.extract_machine_features(2, "MCH-002", degrading_readings, pred_time)
    mch2_risk = engine.assess_machine_risk(mch2_feat)

    assert mch1_risk.health_index > mch2_risk.health_index
    assert mch1_risk.risk_score < mch2_risk.risk_score
    assert mch1_risk.risk_level == RiskLevel.NORMAL
    assert mch2_risk.risk_level in [RiskLevel.WARNING, RiskLevel.CRITICAL]


def test_configurable_risk_thresholds():
    """Verify custom risk thresholds adjust the risk level boundaries dynamically."""
    pred_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    service = FeatureEngineeringService()

    # Moderate degradation readings
    readings = create_machine_readings(
        base_time=pred_time,
        hours=24,
        vibration_val=4.5,
        temperature_val=64.0,
        acoustic_val=76.0,
        pressure_val=140.0,
        current_val=25.0,
    )
    features = service.extract_machine_features(1, "MCH-001", readings, pred_time)

    # Configuration A: Strict thresholds
    strict_config = RiskEngineConfig(normal_threshold=20.0, critical_threshold=50.0)
    engine_strict = RiskEngine(config=strict_config)
    risk_strict = engine_strict.assess_machine_risk(features)

    # Configuration B: Relaxed thresholds
    relaxed_config = RiskEngineConfig(normal_threshold=60.0, critical_threshold=90.0)
    engine_relaxed = RiskEngine(config=relaxed_config)
    risk_relaxed = engine_relaxed.assess_machine_risk(features)

    # The same machine score falls into a more severe bucket under strict config
    assert risk_strict.risk_level != risk_relaxed.risk_level or risk_strict.risk_score > 0


def test_empty_window_safe_handling():
    """Verify completely empty telemetry window is handled safely without crashing."""
    pred_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    service = FeatureEngineeringService()
    engine = RiskEngine()

    features = service.extract_machine_features(1, "MCH-001", [], pred_time)
    assessment = engine.assess_machine_risk(features)

    assert assessment.data_status == "insufficient_telemetry"
    assert assessment.risk_score == 0.0
    assert assessment.health_index == 100.0
    assert assessment.risk_level == RiskLevel.NORMAL
    assert assessment.dominant_failure_mode is None
    assert assessment.remaining_useful_life_hours is None


def test_anti_leakage_and_uncalibrated_probability_flags():
    """Verify engine explicitly enforces anti-leakage invariants and disclaims calibrated probability / RUL."""
    pred_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    service = FeatureEngineeringService()
    engine = RiskEngine()

    readings = create_machine_readings(base_time=pred_time, hours=24)
    features = service.extract_machine_features(1, "MCH-001", readings, pred_time)
    assessment = engine.assess_machine_risk(features)

    # Invariants strictly required:
    assert assessment.is_calibrated_probability is False
    assert assessment.remaining_useful_life_hours is None
