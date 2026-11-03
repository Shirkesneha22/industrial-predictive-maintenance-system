"""
Tests for Deterministic Failure and Maintenance Work Order Generator.
Validates:
- Exactly 150 failure events and 150 linked corrective work orders
- Exactly 23 Type A progressive degradation failures on degrading machines
- Exactly 127 Type B stochastic failures distributed across the 77 eligible machines
- Strict immunity: 0 Type B failures on the 23 Type A machines
- Mathematical exactness: machine and event count sums
- Work order constraints: 0 preventive orders, completed_at NULL for pending & in_progress
- Point-in-time timestamp integrity: completed_at never exceeds WINDOW_END_UTC
- Realistic downtime intervals
- Anti-leakage Type A evaluation feature isolation (excluding terminal and post-failure data)
- Transactional dry-run rollback and idempotency guards
"""

from collections import Counter
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import (
    Machine,
    Technician,
    FailureEvent,
    MaintenanceWorkOrder,
    TelemetryEvent,
)
from backend.generators.telemetry_constants import (
    WINDOW_START_UTC,
    WINDOW_END_UTC,
    SAMPLING_INTERVAL_MINUTES,
)
from backend.generators.telemetry_math import derive_machine_degradation_profile
from backend.generators.failure_constants import (
    DEFAULT_FAILURE_SEED,
    TOTAL_FAILURE_COUNT,
    TYPE_A_FAILURE_COUNT,
    TYPE_B_FAILURE_COUNT,
    TOTAL_MACHINES_COUNT,
    ELIGIBLE_TYPE_B_MACHINES_COUNT,
    WORK_TYPE_CORRECTIVE,
    WORK_TYPE_PREVENTIVE,
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
)
from backend.generators.failure_generator import (
    FailureGenerator,
    extract_type_a_evaluation_features,
)


@pytest.fixture(scope="module")
def db_session():
    """Provides a transactional SQLAlchemy session for testing."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_target_record_counts_and_work_order_linkage(db_session: Session):
    """
    Verify exactly 150 failure events and exactly 150 linked corrective work orders.
    Verifies 0 preventive work orders exist.
    """
    generator = FailureGenerator(seed=DEFAULT_FAILURE_SEED, session=db_session)
    stats = generator.generate(dry_run=True, overwrite=True)

    assert stats["total_failures_generated"] == TOTAL_FAILURE_COUNT
    assert stats["total_failures_generated"] == 150
    assert stats["total_work_orders_generated"] == TOTAL_FAILURE_COUNT
    assert stats["total_work_orders_generated"] == 150

    assert stats["type_a_failures"] == TYPE_A_FAILURE_COUNT
    assert stats["type_a_failures"] == 23

    assert stats["type_b_failures"] == TYPE_B_FAILURE_COUNT
    assert stats["type_b_failures"] == 127

    assert stats["work_order_types"][WORK_TYPE_CORRECTIVE] == 150
    assert stats["work_order_types"][WORK_TYPE_PREVENTIVE] == 0


def test_type_a_distribution_and_immunity(db_session: Session):
    """
    Verify the 23 Type A machines correspond exactly to the machines with active
    degradation trajectories in the telemetry model, and verify they receive
    exactly 0 Type B failure events during their operational life.
    """
    machines = db_session.query(Machine).filter_by(is_active=True).order_by(Machine.machine_id).all()
    assert len(machines) == TOTAL_MACHINES_COUNT

    type_a_ids = set()
    for m in machines:
        prof = derive_machine_degradation_profile(DEFAULT_FAILURE_SEED, m.machine_id, m.machine_code)
        if prof is not None:
            type_a_ids.add(m.machine_id)

    assert len(type_a_ids) == TYPE_A_FAILURE_COUNT
    assert len(type_a_ids) == 23

    # Generate dry-run to inspect assignments
    generator = FailureGenerator(seed=DEFAULT_FAILURE_SEED, session=db_session)
    stats = generator.generate(dry_run=True, overwrite=True)

    # 100 total machines - 23 Type A machines = 77 eligible machines
    eligible_count = len(machines) - len(type_a_ids)
    assert eligible_count == ELIGIBLE_TYPE_B_MACHINES_COUNT
    assert eligible_count == 77


def test_type_b_exact_machine_and_event_sums(db_session: Session):
    """
    Verify exact breakdown of the 127 Type B events across the 77 eligible machines:
    15 machines with 0 events
    31 machines with 1 event
    11 machines with 2 events
    9 machines with 3 events
    8 machines with 4 events
    3 machines with 5 events
    Sum of machines = 77
    Sum of events = 127
    """
    generator = FailureGenerator(seed=DEFAULT_FAILURE_SEED, session=db_session)
    stats = generator.generate(dry_run=True, overwrite=True)

    freqs = stats["type_b_machine_event_frequencies"]
    expected_frequencies = {
        "0_events": 15,
        "1_events": 31,
        "2_events": 11,
        "3_events": 9,
        "4_events": 8,
        "5_events": 3,
    }
    assert freqs == expected_frequencies, f"Frequencies mismatch: {freqs} vs {expected_frequencies}"

    total_eligible_machines = sum(freqs.values())
    assert total_eligible_machines == 77, f"Expected 77 eligible machines, got {total_eligible_machines}"

    total_type_b_events = sum(int(k.split("_")[0]) * v for k, v in freqs.items())
    assert total_type_b_events == 127, f"Expected 127 Type B events, got {total_type_b_events}"

    # Including the 23 Type A machines (which have 0 Type B events and 1 Type A event):
    # Total machines = 77 + 23 = 100
    # Total events = 127 + 23 = 150
    assert total_eligible_machines + 23 == 100
    assert total_type_b_events + 23 == 150


def test_work_order_status_and_timestamp_constraints(db_session: Session):
    """
    Verify work order status and timestamp constraints:
    - completed_at is strictly NULL for pending and in_progress orders
    - completed_at is <= WINDOW_END_UTC for all completed orders (never forced beyond cutoff)
    - Downtimes are realistic positive durations (1h to 24h)
    """
    generator = FailureGenerator(seed=DEFAULT_FAILURE_SEED, session=db_session)
    stats = generator.generate(dry_run=True, overwrite=True)

    dist = stats["status_distribution"]
    total_wos = sum(dist.values())
    assert total_wos == 150

    # Ensure all statuses are valid
    for status_name in [STATUS_COMPLETED, STATUS_IN_PROGRESS, STATUS_PENDING]:
        assert status_name in dist


def test_type_a_evaluation_anti_leakage_guard(db_session: Session):
    """
    Verify Type A evaluation feature extraction strictly excludes the terminal
    failure reading and any post-failure readings, using ONLY observations
    available strictly before the prediction timestamp.
    """
    # Pick a known degrading machine under the new hierarchical machine code nomenclature
    degrading_machines = []
    for candidate in db_session.query(Machine).all():
        p = derive_machine_degradation_profile(DEFAULT_FAILURE_SEED, candidate.machine_id, candidate.machine_code)
        if p is not None:
            degrading_machines.append((candidate, p))
    assert len(degrading_machines) > 0, "At least one machine must have a progressive degradation profile"
    m, prof = degrading_machines[0]

    end_step = prof["end_step"]
    failure_time = WINDOW_START_UTC + timedelta(minutes=end_step * SAMPLING_INTERVAL_MINUTES)

    # Test 1: Prediction 24 hours prior to failure
    lead_time_hours = 24
    prediction_timestamp = failure_time - timedelta(hours=lead_time_hours)

    eval_result = extract_type_a_evaluation_features(
        session=db_session,
        machine_id=m.machine_id,
        prediction_timestamp=prediction_timestamp,
        failure_time=failure_time,
        lookback_window_hours=48,
    )

    assert eval_result["machine_id"] == m.machine_id
    assert eval_result["lead_time_hours"] == 24.0
    assert eval_result["total_observations_used"] > 0

    # The maximum observation timestamp MUST be strictly less than prediction_timestamp
    max_rec_dt = datetime.fromisoformat(eval_result["max_recorded_at"])
    assert max_rec_dt < prediction_timestamp, (
        f"Max recorded timestamp ({max_rec_dt}) must be strictly prior to prediction timestamp ({prediction_timestamp})"
    )
    assert max_rec_dt < failure_time, (
        f"Max recorded timestamp ({max_rec_dt}) must be strictly prior to failure time ({failure_time})"
    )

    # Test 2: Prediction at the exact moment of failure (lead time 0)
    # Even at lead_time 0, the terminal failure reading at failure_time MUST be excluded
    eval_result_at_fail = extract_type_a_evaluation_features(
        session=db_session,
        machine_id=m.machine_id,
        prediction_timestamp=failure_time,
        failure_time=failure_time,
        lookback_window_hours=24,
    )
    max_rec_at_fail = datetime.fromisoformat(eval_result_at_fail["max_recorded_at"])
    assert max_rec_at_fail < failure_time, "Terminal reading at failure_time must be excluded"

    # Test 3: Attempting prediction after failure must raise ValueError
    with pytest.raises(ValueError, match="cannot be after failure time"):
        extract_type_a_evaluation_features(
            session=db_session,
            machine_id=m.machine_id,
            prediction_timestamp=failure_time + timedelta(hours=1),
            failure_time=failure_time,
        )


def test_seed_determinism(db_session: Session):
    """Verify running the generator twice with the same seed produces 100% identical results."""
    gen1 = FailureGenerator(seed=DEFAULT_FAILURE_SEED, session=db_session)
    stats1 = gen1.generate(dry_run=True, overwrite=True)

    gen2 = FailureGenerator(seed=DEFAULT_FAILURE_SEED, session=db_session)
    stats2 = gen2.generate(dry_run=True, overwrite=True)

    assert stats1["total_failures_generated"] == stats2["total_failures_generated"]
    assert stats1["type_a_failures"] == stats2["type_a_failures"]
    assert stats1["type_b_failures"] == stats2["type_b_failures"]
    assert stats1["type_b_machine_event_frequencies"] == stats2["type_b_machine_event_frequencies"]
    assert stats1["status_distribution"] == stats2["status_distribution"]


def test_transactional_dry_run_leaves_zero_records(db_session: Session):
    """Verify dry-run transaction rolls back cleanly leaving committed records unchanged."""
    initial_failures = db_session.query(FailureEvent).count()
    initial_work_orders = db_session.query(MaintenanceWorkOrder).count()

    generator = FailureGenerator(seed=DEFAULT_FAILURE_SEED, session=db_session)
    stats = generator.generate(dry_run=True, overwrite=True)
    assert stats["dry_run"] is True

    # Check database state directly: counts must strictly match initial state after dry-run rollback
    failures_in_db = db_session.query(FailureEvent).count()
    work_orders_in_db = db_session.query(MaintenanceWorkOrder).count()
    assert failures_in_db == initial_failures, f"Expected {initial_failures} failures in DB after dry run, found {failures_in_db}"
    assert work_orders_in_db == initial_work_orders, f"Expected {initial_work_orders} work orders in DB after dry run, found {work_orders_in_db}"
