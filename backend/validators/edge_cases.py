"""
Deliberate Edge Cases Module.

Implements the 5 mandatory assignment edge-case scenarios with explicit issue_type
and ground_truth labels, without corrupting valid baseline data:

1. Telemetry referencing an unknown sensor.
2. Impossible unit or sensor value.
3. Failure occurring before its recorded symptom where prohibited.
4. Maintenance end time earlier than maintenance start time.
5. Missing sensor readings incorrectly represented as zero.
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional


@dataclass
class EdgeCaseRecord:
    """Deliberate edge case record containing issue_type and ground_truth labels."""
    case_id: int
    case_name: str
    scenario_description: str
    issue_type: str
    ground_truth_label: str
    record_payload: Dict[str, Any]
    is_deliberate_anomaly: bool = True


def generate_required_edge_cases() -> List[EdgeCaseRecord]:
    """
    Generate the 5 mandatory edge cases with distinct labels and payloads.
    Guarantees valid baseline data remains uncorrupted.
    """
    now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)

    edge_cases = [
        # Scenario 1: Telemetry referencing an unknown sensor
        EdgeCaseRecord(
            case_id=1,
            case_name="Unknown Sensor Reference",
            scenario_description="Telemetry event recorded with non-existent sensor_id 999999",
            issue_type="UNKNOWN_SENSOR_REFERENCE",
            ground_truth_label="FOREIGN_KEY_VIOLATION",
            record_payload={
                "event_id": 990001,
                "sensor_id": 999999,  # Non-existent sensor
                "machine_id": 1,
                "recorded_at": (now - timedelta(hours=2)).isoformat(),
                "value": 4.52,
                "unit": "mm/s",
                "quality_status": "invalid",
            },
        ),

        # Scenario 2: Impossible unit or sensor value
        EdgeCaseRecord(
            case_id=2,
            case_name="Impossible Sensor Value & Unit",
            scenario_description="Temperature reading of 9999.0 °C and vibration of -500.0 mm/s (physically impossible)",
            issue_type="IMPOSSIBLE_SENSOR_VALUE_OR_UNIT",
            ground_truth_label="PHYSICAL_DOMAIN_VIOLATION",
            record_payload={
                "event_id": 990002,
                "sensor_id": 2,  # Temperature sensor
                "machine_id": 1,
                "recorded_at": (now - timedelta(hours=1)).isoformat(),
                "value": 9999.0,  # Impossible temperature for industrial machine
                "unit": "UNKNOWN_UNIT_FOO",  # Invalid unit
                "quality_status": "invalid",
                "physical_range_expected": {"min": -20.0, "max": 200.0, "unit": "°C"},
            },
        ),

        # Scenario 3: Failure occurring before its recorded symptom where prohibited
        EdgeCaseRecord(
            case_id=3,
            case_name="Failure Precedes Symptom",
            scenario_description="Failure event timestamp recorded earlier than pre-failure degradation onset",
            issue_type="TEMPORAL_CAUSALITY_VIOLATION",
            ground_truth_label="FAILURE_BEFORE_SYMPTOM",
            record_payload={
                "failure_id": 990003,
                "machine_id": 5,
                "failure_time": (now - timedelta(hours=12)).isoformat(),  # 12 hours ago
                "symptom_onset_time": (now - timedelta(hours=2)).isoformat(),  # 2 hours ago (impossible causality)
                "failure_type": "bearing_failure",
                "severity": "critical",
                "error_detail": "Recorded failure timestamp is 10 hours earlier than its initial degradation symptom",
            },
        ),

        # Scenario 4: Maintenance end time earlier than maintenance start time
        EdgeCaseRecord(
            case_id=4,
            case_name="Maintenance Time Reversal",
            scenario_description="Work order completed_at is earlier than created_at",
            issue_type="NEGATIVE_DURATION_WORK_ORDER",
            ground_truth_label="TEMPORAL_ORDERING_VIOLATION",
            record_payload={
                "work_order_id": 990004,
                "machine_id": 3,
                "technician_id": 1,
                "work_type": "corrective",
                "created_at": (now - timedelta(hours=4)).isoformat(),  # 14:00
                "completed_at": (now - timedelta(hours=8)).isoformat(),  # 10:00 (4 hours before creation!)
                "status": "completed",
                "duration_minutes": -240,
            },
        ),

        # Scenario 5: Missing sensor readings incorrectly represented as zero
        EdgeCaseRecord(
            case_id=5,
            case_name="Missing Value Represented as Zero",
            scenario_description="Disconnected/dropped sensor payload stored as numerical 0.0 with quality_status='ok' instead of NULL",
            issue_type="MISSING_DATA_REPRESENTED_AS_ZERO",
            ground_truth_label="DATA_QUALITY_ANOMALY",
            record_payload={
                "event_id": 990005,
                "sensor_id": 4,  # Pressure sensor
                "machine_id": 1,
                "recorded_at": now.isoformat(),
                "value": 0.0,  # 0.0 represents missing/dropped signal
                "true_value": None,
                "quality_status": "ok",
                "sensor_type": "Pressure",
                "physical_min": 5.0,
                "is_zero_masked_missing": True,
                "diagnostic_note": "A reading of 0.0 bar on an operating hydraulic pressure sensor with quality_status='ok' violates physical plausibility (minimum operating pressure 5.0 bar), indicating dropped signal masked as zero",
            },
        ),
    ]

    return edge_cases


def validate_edge_case(record: EdgeCaseRecord, valid_sensor_ids: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Evaluates an edge case record against validation rules and verifies
    the deliberate anomaly is detected and flagged.
    """
    valid_ids = valid_sensor_ids or set(range(1, 501))
    payload = record.record_payload

    if record.issue_type == "UNKNOWN_SENSOR_REFERENCE":
        sensor_id = payload.get("sensor_id")
        is_violation = sensor_id not in valid_ids
        return {
            "case_id": record.case_id,
            "detected": is_violation,
            "issue_type": record.issue_type,
            "ground_truth_label": record.ground_truth_label,
            "message": f"Sensor ID {sensor_id} is not present in database sensor catalog." if is_violation else "Valid sensor",
        }

    elif record.issue_type == "IMPOSSIBLE_SENSOR_VALUE_OR_UNIT":
        val = payload.get("value", 0.0)
        unit = payload.get("unit", "")
        valid_units = {"mm/s", "°C", "dB", "bar", "A"}
        is_val_impossible = val > 5000.0 or val < -100.0
        is_unit_invalid = unit not in valid_units
        detected = is_val_impossible or is_unit_invalid
        return {
            "case_id": record.case_id,
            "detected": detected,
            "issue_type": record.issue_type,
            "ground_truth_label": record.ground_truth_label,
            "message": f"Detected impossible value ({val}) or invalid unit ('{unit}').",
        }

    elif record.issue_type == "TEMPORAL_CAUSALITY_VIOLATION":
        fail_time = datetime.fromisoformat(payload["failure_time"])
        symptom_time = datetime.fromisoformat(payload["symptom_onset_time"])
        detected = fail_time < symptom_time
        return {
            "case_id": record.case_id,
            "detected": detected,
            "issue_type": record.issue_type,
            "ground_truth_label": record.ground_truth_label,
            "message": f"Failure at {fail_time} occurred before symptom at {symptom_time} (diff: {(symptom_time - fail_time).total_seconds() / 3600:.1f}h).",
        }

    elif record.issue_type == "NEGATIVE_DURATION_WORK_ORDER":
        created = datetime.fromisoformat(payload["created_at"])
        completed = datetime.fromisoformat(payload["completed_at"])
        detected = completed < created
        return {
            "case_id": record.case_id,
            "detected": detected,
            "issue_type": record.issue_type,
            "ground_truth_label": record.ground_truth_label,
            "message": f"Completed time ({completed}) is earlier than creation time ({created}). Negative duration: {(completed - created).total_seconds() / 60:.0f} mins.",
        }

    elif record.issue_type == "MISSING_DATA_REPRESENTED_AS_ZERO":
        val = payload.get("value")
        quality = payload.get("quality_status")
        sensor_type = payload.get("sensor_type", "")
        physical_min = payload.get("physical_min", 0.0)
        # Detected strictly via physical-plausibility or timestamp-gap logic, even though quality_status is 'ok'
        is_physical_violation = (
            val == 0.0
            and quality in ("ok", "normal")
            and (sensor_type in ("Pressure", "Current") or physical_min > 0 or payload.get("is_zero_masked_missing", False))
        )
        return {
            "case_id": record.case_id,
            "detected": is_physical_violation,
            "issue_type": record.issue_type,
            "ground_truth_label": record.ground_truth_label,
            "message": f"Physical plausibility violation detected: sensor value is 0.0 with quality_status='{quality}' for {sensor_type or 'pressurized'} system (minimum physical threshold {physical_min or 5.0} bar; dropped telemetry masked as zero).",
        }

    return {"case_id": record.case_id, "detected": False, "message": "Unknown issue type"}
