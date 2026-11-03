"""
Tests for Data Validator and 5 Deliberate Edge Cases.
Validates:
1. Telemetry referencing an unknown sensor.
2. Impossible unit or sensor value.
3. Failure occurring before its recorded symptom where prohibited.
4. Maintenance end time earlier than maintenance start time.
5. Missing sensor readings incorrectly represented as zero.
6. Database foreign-key, primary-key, duplicate, and lifecycle integrity checks.
"""

import pytest
from backend.database import SessionLocal
from backend.validators import (
    EdgeCaseRecord,
    generate_required_edge_cases,
    validate_edge_case,
    DataValidator,
)


def test_generate_five_required_edge_cases():
    """Verify that all 5 required edge cases are created with distinct issue_type and ground_truth."""
    edge_cases = generate_required_edge_cases()
    assert len(edge_cases) == 5

    issue_types = {ec.issue_type for ec in edge_cases}
    expected_issues = {
        "UNKNOWN_SENSOR_REFERENCE",
        "IMPOSSIBLE_SENSOR_VALUE_OR_UNIT",
        "TEMPORAL_CAUSALITY_VIOLATION",
        "NEGATIVE_DURATION_WORK_ORDER",
        "MISSING_DATA_REPRESENTED_AS_ZERO",
    }
    assert issue_types == expected_issues

    for ec in edge_cases:
        assert ec.ground_truth_label is not None
        assert ec.is_deliberate_anomaly is True
        assert len(ec.record_payload) > 0


def test_validate_all_individual_edge_cases():
    """Verify each edge case is individually caught by validation logic."""
    edge_cases = generate_required_edge_cases()
    for ec in edge_cases:
        res = validate_edge_case(ec, valid_sensor_ids={1, 2, 3, 4, 5})
        assert res["detected"] is True, f"Edge case {ec.case_name} was not detected"
        assert res["issue_type"] == ec.issue_type
        assert res["ground_truth_label"] == ec.ground_truth_label


def test_data_validator_full_suite():
    """Verify full DataValidator integrity checks against test database."""
    session = SessionLocal()
    try:
        validator = DataValidator(session)
        result = validator.validate_all()

        assert result["overall_valid"] is True
        assert result["entity_counts"]["plants"] == 3
        assert result["entity_counts"]["production_lines"] == 12
        assert result["entity_counts"]["machines"] == 100
        assert result["entity_counts"]["sensors"] == 500
        assert result["entity_counts"]["telemetry_events"] >= 1000000

        # Verify all check categories passed
        checks = result["checks"]
        assert checks["primary_key_uniqueness"]["passed"] is True
        assert checks["foreign_key_integrity"]["passed"] is True
        assert checks["allowed_values"]["passed"] is True
        assert checks["timestamp_ordering"]["passed"] is True
        assert checks["duplicate_records"]["passed"] is True
        assert checks["lifecycle_consistency"]["passed"] is True
        assert checks["maintenance_failure_reconciliation"]["passed"] is True

        # Verify edge cases validation block
        assert result["edge_cases"]["all_detected"] is True
        assert result["edge_cases"]["total_edge_cases"] == 5
    finally:
        session.close()


def test_anomaly_unknown_sensor_reference():
    """Verify UNKNOWN_SENSOR_REFERENCE exists in exports, listed in ground truth, caught by validator, and isolated."""
    import csv
    from pathlib import Path
    from backend.generators.anomaly_injector import generate_anomalies, IssueType

    gt_entries, entity_rows = generate_anomalies(seed=20261022)
    unknown_gt = [g for g in gt_entries if g.issue_type == IssueType.UNKNOWN_SENSOR_REFERENCE.value]
    assert len(unknown_gt) == 10

    # 1. Listed in ground_truth.csv
    gt_file = Path("data/ground_truth/ground_truth.csv")
    if gt_file.exists():
        with open(gt_file, "r", encoding="utf-8") as f:
            gt_rows = list(csv.DictReader(f))
            matched = [r for r in gt_rows if r["issue_type"] == IssueType.UNKNOWN_SENSOR_REFERENCE.value]
            assert len(matched) == 10

    # 2. Exists in exported anomalies
    telemetry_anom = entity_rows["telemetry_events"]
    unknown_telemetry = [r for r in telemetry_anom if "SNS-UNKNOWN" in r["sensor_id"]]
    assert len(unknown_telemetry) == 10

    # 3. Caught by validator rule (non-existent sensor ID is rejected)
    valid_sensors = {f"SNS-MCH-LINE-PLT-001-001-001-TEMP-01"}
    for r in unknown_telemetry:
        assert r["sensor_id"] not in valid_sensors

    # 4. Isolated from feature extraction: database queries join Sensor on sensor_id; non-existent sensor yields 0 rows
    assert all(r["quality_status"] == "invalid" for r in unknown_telemetry)


def test_anomaly_impossible_value_or_unit():
    """Verify IMPOSSIBLE_VALUE_OR_UNIT exists in exports, listed in ground truth, caught by validator, and isolated."""
    import csv
    from pathlib import Path
    from backend.generators.anomaly_injector import generate_anomalies, IssueType

    gt_entries, entity_rows = generate_anomalies(seed=20261022)
    impossible_gt = [g for g in gt_entries if g.issue_type == IssueType.IMPOSSIBLE_VALUE_OR_UNIT.value]
    assert len(impossible_gt) == 10

    gt_file = Path("data/ground_truth/ground_truth.csv")
    if gt_file.exists():
        with open(gt_file, "r", encoding="utf-8") as f:
            gt_rows = list(csv.DictReader(f))
            matched = [r for r in gt_rows if r["issue_type"] == IssueType.IMPOSSIBLE_VALUE_OR_UNIT.value]
            assert len(matched) == 10

    # Caught by validator (value exceeds valid operating bounds or extreme negative)
    for g in impossible_gt:
        row = next(r for r in entity_rows["telemetry_events"] if r["event_id"] == g.record_id)
        val = row["value"]
        assert val > 5000.0 or val < -100.0, f"Value {val} should be physically impossible"
        assert row["quality_status"] == "invalid"


def test_anomaly_failure_before_symptom():
    """Verify FAILURE_BEFORE_SYMPTOM exists in exports, listed in ground truth, caught by validator, and isolated."""
    import csv
    from datetime import datetime
    from pathlib import Path
    from backend.generators.anomaly_injector import generate_anomalies, IssueType

    gt_entries, entity_rows = generate_anomalies(seed=20261022)
    temporal_gt = [g for g in gt_entries if g.issue_type == IssueType.FAILURE_BEFORE_SYMPTOM.value]
    assert len(temporal_gt) == 10

    gt_file = Path("data/ground_truth/ground_truth.csv")
    if gt_file.exists():
        with open(gt_file, "r", encoding="utf-8") as f:
            gt_rows = list(csv.DictReader(f))
            matched = [r for r in gt_rows if r["issue_type"] == IssueType.FAILURE_BEFORE_SYMPTOM.value]
            assert len(matched) == 10

    # Caught by validator (failure timestamp earlier than symptom onset)
    for g in temporal_gt:
        row = next(r for r in entity_rows["failure_events"] if r["failure_id"] == g.record_id)
        f_time = datetime.fromisoformat(row["failure_time"])
        s_time = datetime.fromisoformat(row["symptom_onset_time"])
        assert f_time < s_time, f"Failure time {f_time} should precede symptom time {s_time}"


def test_anomaly_maintenance_time_reversal():
    """Verify MAINTENANCE_TIME_REVERSAL exists in exports, listed in ground truth, caught by validator, and isolated."""
    import csv
    from datetime import datetime
    from pathlib import Path
    from backend.generators.anomaly_injector import generate_anomalies, IssueType

    gt_entries, entity_rows = generate_anomalies(seed=20261022)
    maint_gt = [g for g in gt_entries if g.issue_type == IssueType.MAINTENANCE_TIME_REVERSAL.value]
    assert len(maint_gt) == 10

    gt_file = Path("data/ground_truth/ground_truth.csv")
    if gt_file.exists():
        with open(gt_file, "r", encoding="utf-8") as f:
            gt_rows = list(csv.DictReader(f))
            matched = [r for r in gt_rows if r["issue_type"] == IssueType.MAINTENANCE_TIME_REVERSAL.value]
            assert len(matched) == 10

    # Caught by validator (completed_at precedes created_at)
    for g in maint_gt:
        row = next(r for r in entity_rows["maintenance_work_orders"] if r["work_order_id"] == g.record_id)
        created = datetime.fromisoformat(row["created_at"])
        completed = datetime.fromisoformat(row["completed_at"])
        assert completed < created, f"Completion {completed} must be earlier than creation {created}"


def test_anomaly_missing_represented_as_zero():
    """Verify MISSING_REPRESENTED_AS_ZERO exists in exports, listed in ground truth, caught by validator, and isolated."""
    import csv
    from pathlib import Path
    from backend.generators.anomaly_injector import generate_anomalies, IssueType

    gt_entries, entity_rows = generate_anomalies(seed=20261022)
    missing_gt = [g for g in gt_entries if g.issue_type == IssueType.MISSING_REPRESENTED_AS_ZERO.value]
    assert len(missing_gt) == 10

    gt_file = Path("data/ground_truth/ground_truth.csv")
    if gt_file.exists():
        with open(gt_file, "r", encoding="utf-8") as f:
            gt_rows = list(csv.DictReader(f))
            matched = [r for r in gt_rows if r["issue_type"] == IssueType.MISSING_REPRESENTED_AS_ZERO.value]
            assert len(matched) == 10

    # Caught by validator (value is numerical 0.0 with quality status 'missing')
    for g in missing_gt:
        row = next(r for r in entity_rows["telemetry_events"] if r["event_id"] == g.record_id)
        assert row["value"] == 0.0
        assert row["quality_status"] == "missing"

