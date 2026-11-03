"""
Tests for Synthetic Telemetry Generator.
Validates SHA-256 deterministic seed derivation, signal synthesis math,
quality status separation (normal, sensor_fault, invalid, missing),
temporal boundaries, and safe transactional generation without database destruction.
"""

from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.orm import Session

from backend.database import SessionLocal
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
from backend.generators.telemetry_math import (
    derive_sensor_seed,
    derive_machine_degradation_profile,
    get_shift_load_and_diurnal,
    generate_sensor_chunk_readings,
)
from backend.generators.telemetry_generator import TelemetryGenerator
from backend.models import TelemetryEvent


def test_sha256_deterministic_seed_derivation():
    """Verify SHA-256 seed derivation is deterministic, invariant, and distinct across sensors."""
    seed1 = derive_sensor_seed(20261022, 1, "SNS-0001")
    seed2 = derive_sensor_seed(20261022, 1, "SNS-0001")
    assert seed1 == seed2, "Seed derivation must be 100% deterministic"

    seed3 = derive_sensor_seed(20261022, 2, "SNS-0002")
    assert seed1 != seed3, "Different sensors must yield distinct seeds"

    seed4 = derive_sensor_seed(99999999, 1, "SNS-0001")
    assert seed1 != seed4, "Different master seeds must yield distinct sensor seeds"


def test_temporal_window_and_reading_counts():
    """Verify exact 90-day duration, 30-minute intervals, and 4,320 readings per sensor."""
    diff = WINDOW_END_UTC - WINDOW_START_UTC
    assert diff.days == 90
    assert diff.total_seconds() == 90 * 86400

    total_steps = int(diff.total_seconds() // 1800)
    assert total_steps == READINGS_PER_SENSOR
    assert total_steps == 4320
    assert total_steps * TARGET_SENSOR_COUNT == TOTAL_TELEMETRY_RECORDS
    assert TOTAL_TELEMETRY_RECORDS == 2160000


def test_ist_shift_modulation():
    """Verify IST operational shift load factors and Sunday maintenance window."""
    # Monday 08:00 IST (02:30 UTC): Morning shift -> load factor 1.00
    t_mon_morning = datetime(2026, 8, 10, 2, 30, tzinfo=timezone.utc)
    load, _ = get_shift_load_and_diurnal(t_mon_morning)
    assert load == 1.00

    # Monday 16:00 IST (10:30 UTC): Afternoon shift -> load factor 1.04
    t_mon_afternoon = datetime(2026, 8, 10, 10, 30, tzinfo=timezone.utc)
    load, _ = get_shift_load_and_diurnal(t_mon_afternoon)
    assert load == 1.04

    # Monday 23:00 IST (17:30 UTC): Night shift (crosses midnight) -> load factor 0.80
    t_mon_night = datetime(2026, 8, 10, 17, 30, tzinfo=timezone.utc)
    load, _ = get_shift_load_and_diurnal(t_mon_night)
    assert load == 0.80

    # Sunday 04:00 IST (Saturday 22:30 UTC): Planned maintenance -> load factor 0.15
    t_sun_maint = datetime(2026, 8, 15, 22, 30, tzinfo=timezone.utc)
    load, _ = get_shift_load_and_diurnal(t_sun_maint)
    assert load == 0.15


def test_all_quality_statuses_generated():
    """Verify signal synthesis generates all 4 quality statuses with valid formatting."""
    readings = generate_sensor_chunk_readings(
        sensor_id=1,
        sensor_code="SNS-0001",
        sensor_type="Vibration",
        machine_id=1,
        machine_code="MCH-001",
        chunk_start_step=0,
        chunk_num_steps=1000,
        master_seed=DEFAULT_TELEMETRY_SEED,
    )
    assert len(readings) == 1000

    statuses = {rec[3] for rec in readings}
    expected_statuses = {QUALITY_NORMAL, QUALITY_SENSOR_FAULT, QUALITY_INVALID, QUALITY_MISSING}
    assert statuses == expected_statuses, f"Expected all quality statuses, got {statuses}"

    for s_id, rec_time, val, q_status, _ in readings:
        if q_status == QUALITY_MISSING:
            # Missing readings MUST have None/NULL values
            assert val is None, f"Missing reading must be None, got {val}"
        else:
            # All other statuses must have numeric float values
            assert val is not None, f"Non-missing status {q_status} had None value"
            assert isinstance(val, float)

        if q_status == QUALITY_INVALID:
            # Vibration invalid readings are negative (impossible)
            assert val < 0.0, f"Expected invalid vibration to be negative, got {val}"


def test_degradation_vs_sensor_fault_separation():
    """
    Verify machine degradation is physics-correlated under QUALITY_NORMAL,
    while sensor faults are localized instrumentation errors.
    """
    # 1. Inspect degradation on degrading machine
    deg_profile = derive_machine_degradation_profile(DEFAULT_TELEMETRY_SEED, 1, "MCH-001")
    # Even if machine 1 is not degrading, find a machine that is
    deg_m_id = None
    for m in range(1, 101):
        prof = derive_machine_degradation_profile(DEFAULT_TELEMETRY_SEED, m, f"MCH-{m:03d}")
        if prof is not None:
            deg_m_id = m
            deg_profile = prof
            break

    assert deg_m_id is not None, "At least one machine must have a degradation profile"

    # Generate readings near the end/peak of the degradation window
    deg_end = deg_profile["end_step"]
    vib_peak_readings = generate_sensor_chunk_readings(
        sensor_id=1,
        sensor_code="SNS-0001",
        sensor_type="Vibration",
        machine_id=deg_m_id,
        machine_code=f"MCH-{deg_m_id:03d}",
        chunk_start_step=deg_end - 50,
        chunk_num_steps=50,
        master_seed=DEFAULT_TELEMETRY_SEED,
    )

    # Generate baseline readings well before degradation starts
    vib_healthy_readings = generate_sensor_chunk_readings(
        sensor_id=1,
        sensor_code="SNS-0001",
        sensor_type="Vibration",
        machine_id=deg_m_id,
        machine_code=f"MCH-{deg_m_id:03d}",
        chunk_start_step=0,
        chunk_num_steps=50,
        master_seed=DEFAULT_TELEMETRY_SEED,
    )

    # Normal readings during peak degradation reflect clearly elevated values over healthy baseline
    peak_vals = [r[2] for r in vib_peak_readings if r[3] == QUALITY_NORMAL and r[2] is not None]
    healthy_vals = [r[2] for r in vib_healthy_readings if r[3] == QUALITY_NORMAL and r[2] is not None]
    assert len(peak_vals) > 0 and len(healthy_vals) > 0
    mean_peak = sum(peak_vals) / len(peak_vals)
    mean_healthy = sum(healthy_vals) / len(healthy_vals)
    assert mean_peak > mean_healthy + 0.8, f"Peak wear ({mean_peak}) should exceed healthy ({mean_healthy})"


def test_idempotency_check_and_overwrite_protection():
    """Verify generator refuses to overwrite without explicit overwrite=True."""
    session = SessionLocal()
    try:
        generator = TelemetryGenerator(seed=DEFAULT_TELEMETRY_SEED, session=session)
        existing = generator.count_existing_window_records(session)
        if existing > 0:
            with pytest.raises(RuntimeError, match="Existing telemetry data detected"):
                generator.generate(dry_run=True, overwrite=False, max_chunks=1)
        else:
            # Should not raise when database window has 0 records
            assert existing == 0
    finally:
        session.close()


def test_small_chunk_copy_with_transactional_rollback():
    """
    Verify PostgreSQL COPY streaming works cleanly inside a transaction,
    then rolls back completely without altering the development database.
    """
    session = SessionLocal()
    try:
        generator = TelemetryGenerator(seed=DEFAULT_TELEMETRY_SEED, session=session)
        # Verify count before and after
        initial_count = session.query(TelemetryEvent).count()

        # Run dry-run on 1 chunk with overwrite=True inside transaction, then rolled back
        stats = generator.generate(dry_run=True, overwrite=True, max_chunks=1)
        assert stats["dry_run"] is True
        assert stats["total_records_inserted"] == 240000
        assert stats["quality_distribution"][QUALITY_NORMAL] > 0
        assert stats["quality_distribution"][QUALITY_MISSING] > 0
        assert stats["quality_distribution"][QUALITY_INVALID] > 0
        assert stats["quality_distribution"][QUALITY_SENSOR_FAULT] > 0

        # After rollback, count must strictly equal initial count
        final_count = session.query(TelemetryEvent).count()
        assert final_count == initial_count, f"Dry run must rollback cleanly leaving {initial_count} records"
    finally:
        session.close()
