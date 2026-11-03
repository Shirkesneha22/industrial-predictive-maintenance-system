# Data Validation Summary & Integrity Audit

This report presents the validation results executed by `DataValidator` against the production dataset and edge-case validation suite.

**Audit Status:** `PASS (100% Valid)`  
**Database Records Analyzed:** 2,160,000 telemetry events, 100 machines, 500 sensors, 150 failure events, 150 work orders.

---

## 1. Relational Integrity Checks

| Verification Check | Target Entities | Rule Enforced | Result | Audit Note |
| :--- | :--- | :--- | :--- | :--- |
| **Primary-Key Uniqueness** | All 10 Entities | `COUNT(PK) == COUNT(DISTINCT PK)` | **PASS** | No duplicate primary keys across any table. |
| **Foreign-Key Integrity** | Lines, Machines, Sensors, Orders, Events | No orphaned child records | **PASS** | 100% of foreign keys resolve to valid parent IDs. |
| **Allowed Values** | Telemetry, Failures, Orders | Categorical enumerations | **PASS** | All quality statuses, severities, and statuses are valid. |
| **Timestamp Ordering** | Maintenance Work Orders | `completed_at >= created_at` | **PASS** | Zero negative-duration maintenance work orders in production. |
| **Duplicate Business Keys**| Machines, Sensors, Technicians | Unique barcodes and emails | **PASS** | All machine codes, sensor codes, and emails are unique. |
| **Arithmetic Reconciliation** | Database vs Constants | Expected record counts | **PASS** | 3 plants, 12 lines, 100 machines, 500 sensors, 2.16M readings. |
| **Lifecycle Consistency** | Work Orders | Status-timestamp alignment | **PASS** | All completed orders have recorded completion times. |
| **Maintenance-Failure Reconciliation** | Failure Events vs Work Orders | Failure mapping | **PASS** | 150 failure incidents mapped to 150 corrective work orders. |

---

## 2. Mandatory Edge Cases Verification

All 5 assignment edge-case scenarios were tested using deliberate test records with explicit `issue_type` and `ground_truth_label` tags, verifying that system guards detect each anomaly without corrupting baseline data:

| # | Scenario Name | Deliberate Anomaly Payload | Issue Type | Ground Truth Label | Detection Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | Unknown Sensor Reference | `sensor_id: 999999` (non-existent) | `UNKNOWN_SENSOR_REFERENCE` | `FOREIGN_KEY_VIOLATION` | **DETECTED & BLOCKED** |
| **2** | Impossible Unit / Value | `value: 9999.0 °C`, `unit: UNKNOWN_UNIT_FOO` | `IMPOSSIBLE_SENSOR_VALUE_OR_UNIT` | `PHYSICAL_DOMAIN_VIOLATION` | **DETECTED & FLAGGED** |
| **3** | Failure Precedes Symptom | `failure_time` is 10 hours earlier than symptom onset | `TEMPORAL_CAUSALITY_VIOLATION` | `FAILURE_BEFORE_SYMPTOM` | **DETECTED & FLAGGED** |
| **4** | Maintenance End Before Start | `completed_at` is 4 hours earlier than `created_at` | `NEGATIVE_DURATION_WORK_ORDER` | `TEMPORAL_ORDERING_VIOLATION` | **DETECTED & REJECTED** |
| **5** | Missing Represented as Zero | Numerical `0.0` with `quality_status: 'missing'` | `MISSING_DATA_REPRESENTED_AS_ZERO` | `DATA_QUALITY_ANOMALY` | **DETECTED & ISOLATED** |
