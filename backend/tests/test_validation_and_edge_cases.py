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
