"""
Deterministic Anomaly Injector and Ground Truth Catalog for Industrial Predictive Maintenance.

Generates the 5 deliberate edge-case anomalies:
1. UNKNOWN_SENSOR_REFERENCE (telemetry referencing non-existent sensor)
2. IMPOSSIBLE_VALUE_OR_UNIT (telemetry with physically impossible measurement)
3. FAILURE_BEFORE_SYMPTOM (failure event timestamp preceding symptom onset)
4. MAINTENANCE_TIME_REVERSAL (work order completed_at earlier than created_at)
5. MISSING_REPRESENTED_AS_ZERO (disconnected/missing sensor telemetry stored as 0.0)

All anomalies are strictly deterministic (seed: 20261022), bounded (exactly 10 rows per type = 50 total),
and fully cataloged in data/ground_truth/ground_truth.csv and .json.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
import random
from typing import Any, Dict, List, Tuple


class IssueType(str, Enum):
    """Enumeration of mandatory assignment edge-case anomaly types."""
    UNKNOWN_SENSOR_REFERENCE = "UNKNOWN_SENSOR_REFERENCE"
    IMPOSSIBLE_VALUE_OR_UNIT = "IMPOSSIBLE_VALUE_OR_UNIT"
    FAILURE_BEFORE_SYMPTOM = "FAILURE_BEFORE_SYMPTOM"
    MAINTENANCE_TIME_REVERSAL = "MAINTENANCE_TIME_REVERSAL"
    MISSING_REPRESENTED_AS_ZERO = "MISSING_REPRESENTED_AS_ZERO"


class ExpectedDecision(str, Enum):
    """Prescribed automated remediation or data pipeline decision."""
    REJECT_RECORD = "REJECT_RECORD"
    QUARANTINE_RECORD = "QUARANTINE_RECORD"
    FLAG_TEMPORAL_ANOMALY = "FLAG_TEMPORAL_ANOMALY"
    REJECT_WORK_ORDER = "REJECT_WORK_ORDER"
    CONVERT_ZERO_TO_NULL = "CONVERT_ZERO_TO_NULL"


@dataclass
class AnomalyGroundTruth:
    """Standardized ground-truth entry for deliberate anomaly records."""
    anomaly_id: str
    issue_type: str
    entity: str
    record_id: str
    machine_id: str
    expected_decision: str
    description: str
    injected_at_step: str


def generate_anomalies(seed: int = 20261022) -> Tuple[List[AnomalyGroundTruth], Dict[str, List[Dict[str, Any]]]]:
    """
    Generates exactly 10 deterministic anomaly rows for each of the 5 edge cases (50 total).
    Returns:
      (ground_truth_entries, exported_rows_by_entity)
    """
    rng = random.Random(seed)
    base_time = datetime(2026, 9, 15, 10, 0, 0, tzinfo=timezone.utc)

    gt_entries: List[AnomalyGroundTruth] = []
    entity_rows: Dict[str, List[Dict[str, Any]]] = {
        "telemetry_events": [],
        "failure_events": [],
        "maintenance_work_orders": [],
    }

    # -------------------------------------------------------------
    # 1. UNKNOWN_SENSOR_REFERENCE (10 rows in telemetry)
    # -------------------------------------------------------------
    for i in range(1, 11):
        anom_id = f"ANOM-{len(gt_entries) + 1:04d}"
        rec_time = base_time + timedelta(hours=i * 2)
        ts_compact = rec_time.strftime("%Y%m%dT%H%M%SZ")
        fake_sensor = f"SNS-UNKNOWN-{9000 + i:04d}"
        rec_id = f"TEL-{fake_sensor}-{ts_compact}"
        machine_code = f"MCH-LINE-PLT-001-001-{(i % 8) + 1:03d}"

        row = {
            "event_id": rec_id,
            "sensor_id": fake_sensor,
            "machine_id": machine_code,
            "recorded_at": rec_time.isoformat(),
            "value": round(rng.uniform(2.0, 15.0), 4),
            "quality_status": "invalid",
            "is_anomaly": True,
            "anomaly_id": anom_id,
        }
        entity_rows["telemetry_events"].append(row)

        gt_entries.append(
            AnomalyGroundTruth(
                anomaly_id=anom_id,
                issue_type=IssueType.UNKNOWN_SENSOR_REFERENCE.value,
                entity="telemetry_events",
                record_id=rec_id,
                machine_id=machine_code,
                expected_decision=ExpectedDecision.REJECT_RECORD.value,
                description=f"Telemetry reading references non-existent sensor identifier {fake_sensor}",
                injected_at_step="telemetry_generation",
            )
        )

    # -------------------------------------------------------------
    # 2. IMPOSSIBLE_VALUE_OR_UNIT (10 rows in telemetry)
    # -------------------------------------------------------------
    impossible_vals = [9999.0, -999.0, 8500.5, -450.0, 12000.0, -800.0, 9500.0, -600.0, 15000.0, -1000.0]
    for i in range(1, 11):
        anom_id = f"ANOM-{len(gt_entries) + 1:04d}"
        rec_time = base_time + timedelta(days=i, hours=4)
        ts_compact = rec_time.strftime("%Y%m%dT%H%M%SZ")
        machine_code = f"MCH-LINE-PLT-001-001-{(i % 8) + 1:03d}"
        channel = "TEMP" if i % 2 == 0 else "VIB"
        sensor_code = f"SNS-{machine_code}-{channel}-01"
        rec_id = f"TEL-{sensor_code}-{ts_compact}"
        imp_val = impossible_vals[i - 1]

        row = {
            "event_id": rec_id,
            "sensor_id": sensor_code,
            "machine_id": machine_code,
            "recorded_at": rec_time.isoformat(),
            "value": imp_val,
            "quality_status": "invalid",
            "is_anomaly": True,
            "anomaly_id": anom_id,
        }
        entity_rows["telemetry_events"].append(row)

        gt_entries.append(
            AnomalyGroundTruth(
                anomaly_id=anom_id,
                issue_type=IssueType.IMPOSSIBLE_VALUE_OR_UNIT.value,
                entity="telemetry_events",
                record_id=rec_id,
                machine_id=machine_code,
                expected_decision=ExpectedDecision.QUARANTINE_RECORD.value,
                description=f"Sensor measured physically impossible value ({imp_val}) outside operational bounds",
                injected_at_step="telemetry_generation",
            )
        )

    # -------------------------------------------------------------
    # 3. FAILURE_BEFORE_SYMPTOM (10 rows in failure_events)
    # -------------------------------------------------------------
    for i in range(1, 11):
        anom_id = f"ANOM-{len(gt_entries) + 1:04d}"
        rec_id = f"FAIL-2026-99{i:04d}"
        machine_code = f"MCH-LINE-PLT-002-001-{(i % 8) + 1:03d}"
        fail_time = base_time + timedelta(days=10 + i, hours=6)
        symptom_time = fail_time + timedelta(hours=8)  # Symptom recorded 8h AFTER failure!

        row = {
            "failure_id": rec_id,
            "machine_id": machine_code,
            "failure_type": "bearing_failure",
            "severity": "critical",
            "failure_time": fail_time.isoformat(),
            "symptom_onset_time": symptom_time.isoformat(),
            "downtime_minutes": 240,
            "description": f"[ANOMALY] Failure timestamp {fail_time.isoformat()} preceded symptom onset {symptom_time.isoformat()}",
            "created_at": fail_time.isoformat(),
            "is_anomaly": True,
            "anomaly_id": anom_id,
        }
        entity_rows["failure_events"].append(row)

        gt_entries.append(
            AnomalyGroundTruth(
                anomaly_id=anom_id,
                issue_type=IssueType.FAILURE_BEFORE_SYMPTOM.value,
                entity="failure_events",
                record_id=rec_id,
                machine_id=machine_code,
                expected_decision=ExpectedDecision.FLAG_TEMPORAL_ANOMALY.value,
                description=f"Temporal causality violation: failure recorded at {fail_time.isoformat()} occurred before symptom onset at {symptom_time.isoformat()}",
                injected_at_step="failure_generation",
            )
        )

    # -------------------------------------------------------------
    # 4. MAINTENANCE_TIME_REVERSAL (10 rows in maintenance_work_orders)
    # -------------------------------------------------------------
    for i in range(1, 11):
        anom_id = f"ANOM-{len(gt_entries) + 1:04d}"
        rec_id = f"WO-2026-99{i:04d}"
        machine_code = f"MCH-LINE-PLT-003-001-{(i % 8) + 1:03d}"
        created_time = base_time + timedelta(days=20 + i, hours=14)
        completed_time = created_time - timedelta(hours=4)  # Completed 4h BEFORE created!

        row = {
            "work_order_id": rec_id,
            "machine_id": machine_code,
            "technician_id": f"TECH-{(i % 20) + 1:04d}",
            "work_type": "corrective",
            "priority": "high",
            "status": "completed",
            "description": f"[ANOMALY] Completed at {completed_time.isoformat()} prior to creation at {created_time.isoformat()}",
            "created_at": created_time.isoformat(),
            "completed_at": completed_time.isoformat(),
            "is_anomaly": True,
            "anomaly_id": anom_id,
        }
        entity_rows["maintenance_work_orders"].append(row)

        gt_entries.append(
            AnomalyGroundTruth(
                anomaly_id=anom_id,
                issue_type=IssueType.MAINTENANCE_TIME_REVERSAL.value,
                entity="maintenance_work_orders",
                record_id=rec_id,
                machine_id=machine_code,
                expected_decision=ExpectedDecision.REJECT_WORK_ORDER.value,
                description=f"Negative duration work order: completion timestamp {completed_time.isoformat()} is earlier than creation timestamp {created_time.isoformat()}",
                injected_at_step="maintenance_generation",
            )
        )

    # -------------------------------------------------------------
    # 5. MISSING_REPRESENTED_AS_ZERO (10 rows in telemetry)
    # -------------------------------------------------------------
    for i in range(1, 11):
        anom_id = f"ANOM-{len(gt_entries) + 1:04d}"
        rec_time = base_time + timedelta(days=30 + i, hours=8)
        ts_compact = rec_time.strftime("%Y%m%dT%H%M%SZ")
        machine_code = f"MCH-LINE-PLT-001-002-{(i % 8) + 1:03d}"
        sensor_code = f"SNS-{machine_code}-PRS-01"
        rec_id = f"TEL-{sensor_code}-{ts_compact}"

        row = {
            "event_id": rec_id,
            "sensor_id": sensor_code,
            "machine_id": machine_code,
            "recorded_at": rec_time.isoformat(),
            "value": 0.0,  # 0.0 representing dropped signal on active pressurized system
            "quality_status": "ok",
            "is_anomaly": True,
            "anomaly_id": anom_id,
        }
        entity_rows["telemetry_events"].append(row)

        gt_entries.append(
            AnomalyGroundTruth(
                anomaly_id=anom_id,
                issue_type=IssueType.MISSING_REPRESENTED_AS_ZERO.value,
                entity="telemetry_events",
                record_id=rec_id,
                machine_id=machine_code,
                expected_decision=ExpectedDecision.CONVERT_ZERO_TO_NULL.value,
                description="Physical plausibility violation: active hydraulic pressure sensor recorded flat numerical 0.0 bar with quality_status='ok' during production shift",
                injected_at_step="telemetry_generation",
            )
        )

    return gt_entries, entity_rows
