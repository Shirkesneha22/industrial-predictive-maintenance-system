"""
Tests for Offline Evaluation Engine, Ground-Truth Registry, and Alert Matching.

Validates:
- Temporal anti-leakage: readings at or after evaluation timestamp are strictly ignored.
- Label isolation: feature extraction and risk assessment operate completely decoupled from FailureEvent records.
- Active downtime and repair period censoring: predictions are omitted during breakdown and repair.
- Repeated-alert debouncing: multiple consecutive alerts for 1 failure event register as exactly 1 True Positive.
- False alarm episode debouncing: consecutive unverified alerts within debounce window collapse to 1 episode.
- Separate cohort evaluation: Type A progressive degradations vs Type B sudden stochastic breakdowns.
- Exact chronological split boundaries (Train: Days 0-54, Val: Days 54-72, Test: Days 72-90).
"""

from datetime import datetime, timezone, timedelta
import pytest

from backend.generators.telemetry_constants import (
    WINDOW_START_UTC,
    WINDOW_END_UTC,
    QUALITY_NORMAL,
    QUALITY_SENSOR_FAULT,
)
from backend.services.feature_engineering import (
    FeatureEngineeringService,
    SensorReading,
)
from backend.services.risk_engine import RiskEngine, RiskLevel
from backend.schemas.evaluation import (
    EvaluationSplit,
    FailureCohort,
    BenchmarkConfig,
    FleetEvaluationSummary,
)
from backend.services.offline_evaluator import (
    GroundTruthEvent,
    GroundTruthRegistry,
    PointInTimePrediction,
    AlertMatchingPolicy,
    OfflineEvaluationEngine,
)


def create_sensor_stream(
    base_time: datetime,
    hours: int = 24,
    vibration_val: float = 2.2,
    temp_val: float = 56.0,
    acoustic_val: float = 68.0,
    pressure_val: float = 140.0,
    current_val: float = 24.5,
    machine_id: int = 1,
) -> list:
    """Helper to generate realistic 5-sensor normal telemetry readings."""
    readings = []
    num_steps = hours * 2  # 30-min sampling
    specs = [
        (1, "Vibration", "SNS-0001", vibration_val),
        (2, "Temperature", "SNS-0002", temp_val),
        (3, "Acoustic", "SNS-0003", acoustic_val),
        (4, "Pressure", "SNS-0004", pressure_val),
        (5, "Current", "SNS-0005", current_val),
    ]
    for step in range(num_steps):
        mins_before = (num_steps - step) * 30
        t = base_time - timedelta(minutes=mins_before)
        for s_id, s_type, s_code, val in specs:
            readings.append(
                SensorReading(
                    sensor_id=s_id,
                    recorded_at=t,
                    value=val,
                    quality_status=QUALITY_NORMAL,
                    sensor_type=s_type,
                    sensor_code=s_code,
                )
            )
    return readings


def test_chronological_split_boundaries():
    """Verify exact chronological split boundaries adhere to 54 / 18 / 18 day partitioning."""
    config = BenchmarkConfig(train_end_days=54, val_end_days=72)
    engine = OfflineEvaluationEngine(config=config)

    t_start, t_train_end = engine.get_split_boundaries(EvaluationSplit.TRAIN)
    assert t_start == WINDOW_START_UTC
    assert t_train_end == WINDOW_START_UTC + timedelta(days=54)

    t_val_start, t_val_end = engine.get_split_boundaries(EvaluationSplit.VAL)
    assert t_val_start == WINDOW_START_UTC + timedelta(days=54)
    assert t_val_end == WINDOW_START_UTC + timedelta(days=72)

    t_test_start, t_test_end = engine.get_split_boundaries(EvaluationSplit.TEST)
    assert t_test_start == WINDOW_START_UTC + timedelta(days=72)
    assert t_test_end == WINDOW_END_UTC

    t_all_start, t_all_end = engine.get_split_boundaries(EvaluationSplit.ALL)
    assert t_all_start == WINDOW_START_UTC
    assert t_all_end == WINDOW_END_UTC


def test_temporal_anti_leakage_guard():
    """
    Verify that telemetry recorded at or after the prediction timestamp
    is strictly excluded and cannot alter the risk assessment.
    """
    eval_time = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    engine = OfflineEvaluationEngine()

    # Pre-cutoff telemetry (normal healthy operating conditions)
    normal_readings = create_sensor_stream(eval_time, hours=24)

    # Post-cutoff telemetry (extreme catastrophic spike 10 minutes AFTER eval_time)
    future_spike_time = eval_time + timedelta(minutes=10)
    future_readings = [
        SensorReading(
            sensor_id=1,
            recorded_at=future_spike_time,
            value=999.0,  # Extreme vibration spike
            quality_status=QUALITY_NORMAL,
            sensor_type="Vibration",
            sensor_code="SNS-0001",
        ),
        SensorReading(
            sensor_id=2,
            recorded_at=future_spike_time,
            value=199.0,  # Extreme temperature spike
            quality_status=QUALITY_NORMAL,
            sensor_type="Temperature",
            sensor_code="SNS-0002",
        ),
    ]

    # Combine clean pre-cutoff readings with future post-cutoff readings
    combined_readings = normal_readings + future_readings

    # Extract features strictly at eval_time
    features = engine.feature_service.extract_machine_features(
        machine_id=1,
        machine_code="MCH-001",
        readings=combined_readings,
        prediction_timestamp=eval_time,
    )
    assessment = engine.risk_engine.assess_machine_risk(features)

    # Future spikes must NOT leak into the prediction at eval_time
    assert assessment.risk_level == RiskLevel.NORMAL
    assert assessment.risk_score <= 15.0
    assert assessment.has_correlated_degradation is False


def test_label_isolation_independence():
    """
    Verify that feature engineering and risk scoring are strictly decoupled
    from the GroundTruthRegistry and produce identical results regardless
    of whether a failure is registered.
    """
    eval_time = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)
    readings = create_sensor_stream(eval_time, hours=24)

    # Scenario A: Machine has NO failure event in registry
    registry_empty = GroundTruthRegistry()
    engine_empty = OfflineEvaluationEngine(registry=registry_empty)

    features_a = engine_empty.feature_service.extract_machine_features(
        machine_id=1,
        machine_code="MCH-001",
        readings=readings,
        prediction_timestamp=eval_time,
    )
    assessment_a = engine_empty.risk_engine.assess_machine_risk(features_a)

    # Scenario B: Machine HAS an imminent failure event in registry 2 hours later
    registry_with_event = GroundTruthRegistry([
        GroundTruthEvent(
            failure_id=101,
            machine_id=1,
            machine_code="MCH-001",
            failure_type="Bearing Seizure",
            failure_class=FailureCohort.TYPE_A,
            failure_time=eval_time + timedelta(hours=2),
            downtime_minutes=720,
        )
    ])
    engine_with_event = OfflineEvaluationEngine(registry=registry_with_event)

    features_b = engine_with_event.feature_service.extract_machine_features(
        machine_id=1,
        machine_code="MCH-001",
        readings=readings,
        prediction_timestamp=eval_time,
    )
    assessment_b = engine_with_event.risk_engine.assess_machine_risk(features_b)

    # Risk scores and feature extractions must be 100% bitwise identical
    assert assessment_a.risk_score == assessment_b.risk_score
    assert assessment_a.health_index == assessment_b.health_index
    assert assessment_a.risk_level == assessment_b.risk_level


def test_downtime_and_repair_censoring():
    """
    Verify that predictions during active failure and repair intervals
    are strictly censored and do not trigger false alarms or evaluate offline.
    """
    fail_time = datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc)
    downtime_mins = 480  # 8 hours of repair (until 18:00 UTC)

    registry = GroundTruthRegistry([
        GroundTruthEvent(
            failure_id=201,
            machine_id=10,
            machine_code="MCH-010",
            failure_type="Hydraulic Seal Rupture",
            failure_class=FailureCohort.TYPE_A,
            failure_time=fail_time,
            downtime_minutes=downtime_mins,
        )
    ])

    # 1. Check downtime guard directly
    assert registry.is_machine_in_downtime(10, fail_time - timedelta(minutes=1)) is False
    assert registry.is_machine_in_downtime(10, fail_time) is True
    assert registry.is_machine_in_downtime(10, fail_time + timedelta(hours=4)) is True
    assert registry.is_machine_in_downtime(10, fail_time + timedelta(minutes=downtime_mins - 1)) is True
    assert registry.is_machine_in_downtime(10, fail_time + timedelta(minutes=downtime_mins)) is False

    # 2. Test within evaluation simulation
    config = BenchmarkConfig(step_interval_hours=4)
    engine = OfflineEvaluationEngine(config=config, registry=registry)

    # Simulate 3 steps: Before failure (08:00), During repair (12:00), After repair (20:00)
    machines = [{"id": 10, "code": "MCH-010"}]
    readings = {10: create_sensor_stream(fail_time + timedelta(hours=12), hours=48)}

    summary = engine.evaluate_in_memory_stream(
        machines=machines,
        readings_by_machine=readings,
        split=EvaluationSplit.ALL,
    )

    # Assert that censored repair evaluations were detected and logged
    assert summary.total_censored_repair_evaluations >= 1


def test_repeated_alert_debouncing_and_lead_time():
    """
    Verify that multiple consecutive alerts preceding a single failure event
    are grouped into exactly 1 True Positive, with accurate lead time tracking.
    """
    fail_time = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
    config = BenchmarkConfig(
        alert_threshold=35.0,
        lead_window_min_hours=1.0,
        lead_window_max_hours=168.0,
    )

    events = [
        GroundTruthEvent(
            failure_id=501,
            machine_id=2,
            machine_code="MCH-002",
            failure_type="Bearing Spalling",
            failure_class=FailureCohort.TYPE_A,
            failure_time=fail_time,
            downtime_minutes=600,
        )
    ]

    # Generate 5 alerts leading up to failure:
    # 48h before, 36h before, 24h before, 12h before, 6h before
    predictions = [
        PointInTimePrediction(
            machine_id=2,
            machine_code="MCH-002",
            timestamp=fail_time - timedelta(hours=hours_before),
            risk_score=75.0,
            risk_level=RiskLevel.CRITICAL,
            is_alert=True,
            is_censored_in_repair=False,
        )
        for hours_before in [48, 36, 24, 12, 6]
    ]

    matcher = AlertMatchingPolicy(config=config)
    summary = matcher.match_predictions_to_events(
        predictions=predictions,
        ground_truth_events=events,
        operational_machine_days=10.0,
        split=EvaluationSplit.TEST,
        window_start=fail_time - timedelta(days=7),
        window_end=fail_time + timedelta(days=1),
        total_machines=1,
        timesteps_count=5,
        censored_evaluations=0,
    )

    # Crucial assertion: 5 alerts must produce exactly 1 True Positive (NOT 5!)
    assert summary.true_positive_events == 1
    assert summary.false_negative_events == 0
    assert summary.false_alarm_episodes == 0
    assert summary.precision == 1.0
    assert summary.recall == 1.0
    assert summary.f1_score == 1.0

    # Advance warning lead time must be measured from the FIRST alert (48.0 hours)
    detected = summary.detected_events[0]
    assert detected.is_detected is True
    assert detected.lead_time_hours == 48.0
    assert detected.alert_count_in_window == 5


def test_false_alarm_episode_debouncing():
    """
    Verify that consecutive unverified alerts on a healthy machine
    within the false alarm debounce window collapse into a single false alarm episode.
    """
    base_t = datetime(2026, 8, 10, 0, 0, tzinfo=timezone.utc)
    config = BenchmarkConfig(false_alarm_debounce_hours=24.0)
    matcher = AlertMatchingPolicy(config=config)

    # 3 alerts within 12 hours (spaced by 6h): should collapse into 1 False Alarm Episode
    # 1 alert 48 hours later: should register as a 2nd False Alarm Episode
    predictions = [
        PointInTimePrediction(
            machine_id=5,
            machine_code="MCH-005",
            timestamp=base_t,
            risk_score=50.0,
            risk_level=RiskLevel.WARNING,
            is_alert=True,
            is_censored_in_repair=False,
        ),
        PointInTimePrediction(
            machine_id=5,
            machine_code="MCH-005",
            timestamp=base_t + timedelta(hours=6),
            risk_score=55.0,
            risk_level=RiskLevel.WARNING,
            is_alert=True,
            is_censored_in_repair=False,
        ),
        PointInTimePrediction(
            machine_id=5,
            machine_code="MCH-005",
            timestamp=base_t + timedelta(hours=12),
            risk_score=52.0,
            risk_level=RiskLevel.WARNING,
            is_alert=True,
            is_censored_in_repair=False,
        ),
        # Distinct episode after 48h gap
        PointInTimePrediction(
            machine_id=5,
            machine_code="MCH-005",
            timestamp=base_t + timedelta(hours=60),
            risk_score=45.0,
            risk_level=RiskLevel.WARNING,
            is_alert=True,
            is_censored_in_repair=False,
        ),
    ]

    summary = matcher.match_predictions_to_events(
        predictions=predictions,
        ground_truth_events=[],  # Zero ground truth failures -> all are false alarms
        operational_machine_days=10.0,
        split=EvaluationSplit.TRAIN,
        window_start=base_t,
        window_end=base_t + timedelta(days=5),
        total_machines=1,
        timesteps_count=4,
        censored_evaluations=0,
    )

    # Assert exactly 2 False Alarm Episodes (collapsed from 4 raw alerts)
    assert summary.total_raw_alerts == 4
    assert summary.false_alarm_episodes == 2
    assert summary.true_positive_events == 0
    assert summary.precision == 0.0
    assert summary.false_alarms_per_machine_day == 0.2  # 2 episodes / 10 machine-days


def test_cohort_separation_type_a_vs_type_b():
    """
    Verify that Type A progressive degradations and Type B sudden failures
    are tracked and reported separately in the evaluation summary.
    """
    base_t = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
    config = BenchmarkConfig()
    matcher = AlertMatchingPolicy(config=config)

    # Machine 1: Type A failure with advance warning alert (Detected TP)
    type_a_fail = GroundTruthEvent(
        failure_id=701,
        machine_id=1,
        machine_code="MCH-001",
        failure_type="Spindle Bearing Wear",
        failure_class=FailureCohort.TYPE_A,
        failure_time=base_t + timedelta(hours=24),
        downtime_minutes=720,
    )

    # Machine 2: Type B sudden failure with NO advance warning alert (Missed FN)
    type_b_fail = GroundTruthEvent(
        failure_id=702,
        machine_id=2,
        machine_code="MCH-002",
        failure_type="Solenoid Valve Burnout",
        failure_class=FailureCohort.TYPE_B,
        failure_time=base_t + timedelta(hours=12),
        downtime_minutes=180,
    )

    # Alert on Machine 1 only (24h lead time)
    predictions = [
        PointInTimePrediction(
            machine_id=1,
            machine_code="MCH-001",
            timestamp=base_t,
            risk_score=70.0,
            risk_level=RiskLevel.CRITICAL,
            is_alert=True,
            is_censored_in_repair=False,
        ),
        PointInTimePrediction(
            machine_id=2,
            machine_code="MCH-002",
            timestamp=base_t,
            risk_score=10.0,
            risk_level=RiskLevel.NORMAL,
            is_alert=False,
            is_censored_in_repair=False,
        ),
    ]

    summary = matcher.match_predictions_to_events(
        predictions=predictions,
        ground_truth_events=[type_a_fail, type_b_fail],
        operational_machine_days=5.0,
        split=EvaluationSplit.TEST,
        window_start=base_t - timedelta(days=1),
        window_end=base_t + timedelta(days=2),
        total_machines=2,
        timesteps_count=1,
        censored_evaluations=0,
    )

    # Type A cohort: 100% recall
    assert summary.type_a_metrics.total_failure_events == 1
    assert summary.type_a_metrics.detected_failure_events == 1
    assert summary.type_a_metrics.missed_failure_events == 0
    assert summary.type_a_metrics.recall == 1.0
    assert summary.type_a_metrics.lead_time.mean_hours == 24.0

    # Type B cohort: 0% recall (unheralded stoppage)
    assert summary.type_b_metrics.total_failure_events == 1
    assert summary.type_b_metrics.detected_failure_events == 0
    assert summary.type_b_metrics.missed_failure_events == 1
    assert summary.type_b_metrics.recall == 0.0

    # Overall fleet: 1 TP, 1 FN -> 50% recall
    assert summary.true_positive_events == 1
    assert summary.false_negative_events == 1
    assert summary.recall == 0.5


def test_threshold_sweeping_metrics_curve():
    """
    Verify sweeping risk thresholds from 15.0 to 85.0 in increments of 5.0:
    - Exactly 15 evaluation points generated across the curve.
    - Captures trade-offs: as threshold increases, false alarms monotonically decrease or stay flat.
    - Evaluates Type A and Type B failure cohorts separately across all thresholds.
    - Recommended threshold selected using documented multi-objective criterion.
    """
    base_t = datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc)
    config = BenchmarkConfig(split=EvaluationSplit.VAL)
    engine = OfflineEvaluationEngine(config=config)

    # 1 Type A event at base_t + 48h
    type_a_event = GroundTruthEvent(
        failure_id=801,
        machine_id=1,
        machine_code="MCH-001",
        failure_type="Bearing Spalling",
        failure_class=FailureCohort.TYPE_A,
        failure_time=base_t + timedelta(hours=48),
        downtime_minutes=720,
    )

    # 1 Type B event at base_t + 24h
    type_b_event = GroundTruthEvent(
        failure_id=802,
        machine_id=2,
        machine_code="MCH-002",
        failure_type="Relay Trip",
        failure_class=FailureCohort.TYPE_B,
        failure_time=base_t + timedelta(hours=24),
        downtime_minutes=180,
    )

    # Predictions:
    # Machine 1 has strong correlated wear: risk score 75.0 (alerts up to tau=75.0)
    # Machine 2 has nominal operation: risk score 8.0 (no alert at any tau >= 15.0)
    # Machine 3 is healthy: risk score 8.0
    # Machine 4 has false alarm transient: risk score 45.0 (alerts when tau <= 45.0, suppressed when tau > 45.0)
    predictions = [
        PointInTimePrediction(
            machine_id=1,
            machine_code="MCH-001",
            timestamp=base_t,
            risk_score=75.0,
            risk_level=RiskLevel.CRITICAL,
            is_alert=True,
            is_censored_in_repair=False,
        ),
        PointInTimePrediction(
            machine_id=2,
            machine_code="MCH-002",
            timestamp=base_t,
            risk_score=8.0,
            risk_level=RiskLevel.NORMAL,
            is_alert=False,
            is_censored_in_repair=False,
        ),
        PointInTimePrediction(
            machine_id=3,
            machine_code="MCH-003",
            timestamp=base_t,
            risk_score=8.0,
            risk_level=RiskLevel.NORMAL,
            is_alert=False,
            is_censored_in_repair=False,
        ),
        PointInTimePrediction(
            machine_id=4,
            machine_code="MCH-004",
            timestamp=base_t,
            risk_score=45.0,
            risk_level=RiskLevel.WARNING,
            is_alert=True,
            is_censored_in_repair=False,
        ),
    ]

    opt_result = engine.sweep_thresholds(
        predictions=predictions,
        ground_truth_events=[type_a_event, type_b_event],
        operational_machine_days=10.0,
        split=EvaluationSplit.VAL,
        window_start=base_t,
        window_end=base_t + timedelta(days=5),
        total_machines=4,
        timesteps_count=1,
        censored_evaluations=0,
    )

    # 1. Exactly 15 thresholds from 15.0 to 85.0
    assert len(opt_result.thresholds_evaluated) == 15
    assert opt_result.thresholds_evaluated[0] == 15.0
    assert opt_result.thresholds_evaluated[-1] == 85.0
    assert len(opt_result.metric_curve) == 15

    # 2. Check trade-off across thresholds:
    # At tau <= 45.0: Machine 4 triggers a false alarm -> false_alarm_episodes == 1
    # At tau > 45.0: Machine 4 is suppressed -> false_alarm_episodes == 0
    pt_30 = next(pt for pt in opt_result.metric_curve if pt.threshold == 30.0)
    assert pt_30.false_alarm_episodes == 1
    assert pt_30.true_positives == 1  # Machine 1 captured
    assert pt_30.precision == 0.5     # 1 TP / (1 TP + 1 FP) = 0.5

    pt_50 = next(pt for pt in opt_result.metric_curve if pt.threshold == 50.0)
    assert pt_50.false_alarm_episodes == 0  # Machine 4 suppressed!
    assert pt_50.true_positives == 1        # Machine 1 still captured (75 >= 50)
    assert pt_50.precision == 1.0           # 1 TP / (1 TP + 0 FP) = 1.0

    # At tau > 75.0 (e.g. 80.0): Machine 1 is also suppressed -> TP drops to 0
    pt_80 = next(pt for pt in opt_result.metric_curve if pt.threshold == 80.0)
    assert pt_80.true_positives == 0
    assert pt_80.false_negatives == 2
    assert pt_80.recall == 0.0

    # 3. Type A vs Type B separation verified across all points:
    for pt in opt_result.metric_curve:
        assert pt.type_a_total == 1
        assert pt.type_b_total == 1
        assert pt.type_b_recall == 0.0  # Type B is never detected

    # 4. Selection criterion should recommend tau in [50.0, 75.0] where F1 is maximized
    assert 50.0 <= opt_result.recommended_threshold <= 75.0
    assert opt_result.best_point.precision == 1.0
    assert opt_result.best_point.false_alarm_episodes == 0


def test_validation_and_test_split_quarantine():
    """
    Verify strict isolation between Validation and Test splits:
    - optimize_thresholds_in_memory executes exclusively on the validation split.
    - Test split window (Day 72 to 90) remains completely untouched and out-of-scope.
    """
    config = BenchmarkConfig()
    engine = OfflineEvaluationEngine(config=config)

    val_start, val_end = engine.get_split_boundaries(EvaluationSplit.VAL)
    test_start, test_end = engine.get_split_boundaries(EvaluationSplit.TEST)

    # Strict non-overlap: validation end is test start
    assert val_end == test_start
    assert val_start < val_end < test_end

    # Run optimization on in-memory validation data
    machines = [{"id": 1, "code": "MCH-001"}]
    readings = {1: create_sensor_stream(val_start + timedelta(hours=24), hours=48)}

    res = engine.optimize_thresholds_in_memory(
        machines=machines,
        readings_by_machine=readings,
    )

    # Optimization result must be strictly tagged as VAL
    assert res.split == EvaluationSplit.VAL
    assert res.validation_window_start == val_start
    assert res.validation_window_end == val_end

    # Verify notes document test split quarantine and non-probability nature
    assert any("validation" in n.lower() for n in res.notes)
    assert any("test split remains strictly quarantined" in n.lower() for n in res.notes)
    assert any("not a calibrated failure probability" in n.lower() or "never be interpreted" in n.lower() for n in res.notes)

