# Testing, Validation & Verification Report

This document reports the actual verification evidence gathered from automated backend test execution, frontend production compilation, database validation checks, and edge-case handling.

---

## 1. Automated Backend Test Suite

The automated test suite was executed using `pytest` against the active environment:

```powershell
.\venv\Scripts\pytest backend/tests -v
```

### Execution Results
- **Collected Test Items:** 89 tests
- **Passing Tests:** 89 passed (100.0%)
- **Failing Tests:** 0 failed
- **Execution Time:** ~18.3 seconds

### Breakdown by Test Module

| Test Module | Tests | Passed | Failed | Focus Areas |
| :--- | :---: | :---: | :---: | :--- |
| `backend/tests/test_api_endpoints.py` | 25 | 25 | 0 | Pagination, filtering, HTTP 400/404/422 responses, anti-leakage cutoff. |
| `backend/tests/test_failure_generator.py` | 7 | 7 | 0 | Failure event distributions, Type A vs Type B breakdown, work order creation. |
| `backend/tests/test_feature_engineering.py` | 9 | 9 | 0 | Rolling mean, standard deviation, Z-scores, strictly enforced 7-day lookback. |
| `backend/tests/test_health.py` | 1 | 1 | 0 | FastAPI `/health` endpoint status. |
| `backend/tests/test_maintenance_endpoints.py` | 6 | 6 | 0 | Work orders, failure logs, and maintenance summary queries. |
| `backend/tests/test_master_data_generator.py` | 7 | 7 | 0 | Master data entity counts (3 plants, 12 lines, 100 machines, 500 sensors, etc.). |
| `backend/tests/test_offline_evaluation.py` | 9 | 9 | 0 | Supervised metrics calculation (precision, recall, lead time, confusion matrix). |
| `backend/tests/test_risk_engine.py` | 10 | 10 | 0 | Explainable health index, single-channel noise vs multi-sensor degradation. |
| `backend/tests/test_telemetry_generator.py` | 7 | 7 | 0 | Telemetry synthesis math, diurnal curves, and PostgreSQL `raw_cursor.copy()` streaming. |
| `backend/tests/test_validation_and_edge_cases.py` | 8 | 8 | 0 | Relational validation suite, 5 deliberate edge cases, and cross-table join integrity. |
| **Total** | **89** | **89** | **0** | **Overall Pass Rate: 100.0%** |

### Transactional Streaming & Rollback Verification
- **Test:** `backend/tests/test_telemetry_generator.py::test_small_chunk_copy_with_transactional_rollback`
- **Status:** **PASS**
- **Verification Details:** High-speed streaming is implemented via `psycopg` (v3) `cursor.copy()` protocol in `backend/generators/telemetry_generator.py`. The test verifies that 240,000 telemetry readings stream through the database buffer inside a transaction and execute a clean rollback, leaving zero residual or corrupted rows in the database.

---

## 2. Frontend Production Build

The React single-page frontend was verified by executing a full production Webpack compilation:

```powershell
npm --prefix frontend run build
```

- **Build Tool:** Webpack 5.112.2 with Babel loader
- **Exit Code:** `0` (Success, 0 errors)
- **Compilation Time:** 15.7 seconds
- **Generated Bundle Artifacts:**
  - `dist/index.html` (485 B)
  - `dist/js/main.cc555d35.js` (161 KiB)
  - `dist/js/179.737f2b3e.js` (635 KiB - includes React, Recharts, and Router)

---

## 3. Database Validation & Integrity Audit

Comprehensive database validation was performed using `DataValidator` across the 2,160,000 telemetry readings, 150 failure incidents, and 150 work orders:

| Audit Check | Target Scope | Criteria | Result |
| :--- | :--- | :--- | :--- |
| **Primary-Key Uniqueness** | All 10 Entities | `COUNT(PK) == COUNT(DISTINCT PK)` | **PASS** (Zero duplicates across all tables) |
| **Foreign-Key Integrity** | Lines, Machines, Sensors, Work Orders, Failures | No orphaned records | **PASS** (100% valid parent references, 0 orphaned rows) |
| **Allowed Values & Enums** | Telemetry, Work Orders, Failures | Categorical domain constraints | **PASS** (All quality statuses, severities, and work types valid) |
| **Timestamp Sequence** | Maintenance Work Orders | `completed_at >= created_at` | **PASS** (100% completed orders valid; 0 negative durations) |
| **Business Code Uniqueness** | Machines, Sensors, Technicians, Parts | Unique natural keys | **PASS** (100% of equipment, sensor, and technician codes unique) |
| **Volume Reconciliation** | Active Entities | Expected counts | **PASS** (3 Plants, 12 Lines, 100 Machines, 500 Sensors, 150 Failures, 150 Work Orders, 2.16M Telemetry) |
| **Lifecycle Progression** | Work Orders | Status consistency | **PASS** (Completed orders strictly have valid `completed_at` timestamps) |
| **Arithmetic Reconciliation** | Failures vs Work Orders | `(completed_at - created_at) == downtime_minutes` | **PASS** (150/150 failures arithmetically reconcile with corrective work order downtime) |
| **Parts Compatibility Linkage** | Machines to Spare Parts | Associative bridge table `machine_parts` | **PASS** (449 spare part mappings verified across 100% of active machines) |
| **Spec-Compliant ID Nomenclature** | All CSV/JSON Export Files | Regex validation & join referential integrity | **PASS** (100% compliance with `PLT-*`, `LINE-*`, `MCH-*`, `SNS-*`, `TEL-*`, `WO-*`; 0 broken joins) |
| **Deliberate Anomaly Reconciliation** | Injected Edge Cases vs Ground Truth | 50 anomaly rows reconciled against ground truth | **PASS** (100% recall, 0 baseline false positives) |

---

## 4. Five Mandatory Edge-Case Scenarios

The system explicitly defines, injects, and validates five deliberate anomaly scenarios via `backend/validators/edge_cases.py` and `backend/generators/anomaly_injector.py`:

| # | Scenario Name | Deliberate Test Payload | Issue Type Tag | Ground-Truth Label | System Handling & Dataset Persistence |
| :- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Unknown Sensor Reference** | Telemetry referencing non-existent `SNS-UNKNOWN-9001` on machine `MCH-LINE-PLT-001-001-001` | `UNKNOWN_SENSOR_REFERENCE` | `FOREIGN_KEY_VIOLATION` | Detected and rejected by foreign key constraint check. 10 labelled rows persisted in `data/exports/csv/anomalies/` and `data/ground_truth/ground_truth.csv`. |
| **2** | **Impossible Unit / Value** | Temperature reading `9999.0 °C` with invalid unit `UNKNOWN_UNIT_FOO` | `IMPOSSIBLE_SENSOR_VALUE_OR_UNIT` | `PHYSICAL_DOMAIN_VIOLATION` | Flagged as out of physical operating bounds. 10 labelled rows persisted in exported anomalies and ground truth. |
| **3** | **Failure Preceding Symptom** | Incident timestamp occurring 10 hours earlier than symptom degradation onset | `TEMPORAL_CAUSALITY_VIOLATION` | `FAILURE_BEFORE_SYMPTOM` | Flagged as temporal causality violation. 10 labelled rows persisted in exported anomalies and ground truth. |
| **4** | **Negative Maintenance Duration** | Work order with `completed_at` 4 hours earlier than `created_at` | `NEGATIVE_DURATION_WORK_ORDER` | `TEMPORAL_ORDERING_VIOLATION` | Detected and rejected by lifecycle timestamp validator. 10 labelled rows persisted in exported anomalies and ground truth. |
| **5** | **Missing Represented as Zero** | Transmission gap in continuous time series filled with numerical `0.0` with `quality_status='ok'` on active hydraulic circuit | `MISSING_DATA_REPRESENTED_AS_ZERO` | `DATA_QUALITY_ANOMALY` | Detected via physical plausibility logic (minimum operating pressure 5.0 bar; dropped signal masked as zero). 10 labelled rows persisted in exported anomalies and ground truth. |

### Presence in Exported Dataset
Unlike synthetic test fixtures, all 50 deliberate anomalies are physically persisted in:
- `data/exports/csv/anomalies/telemetry_events.csv`
- `data/exports/csv/anomalies/failure_events.csv`
- `data/exports/csv/anomalies/maintenance_work_orders.csv`
- Paired 1-to-1 with `data/ground_truth/ground_truth.csv` and `data/ground_truth/ground_truth.json`.

---

## 5. Deterministic Reproducibility Verification

A reproducibility check was executed using `backend/utils/reproducibility_checker.py` under master seed `20261022`:
- Two independent generation trials were run across all disk-persisted CSV files and ground-truth records.
- Generated record counts matched exactly (3 Plants, 12 Lines, 100 Machines, 500 Sensors, 2,160,000 Readings, 150 Failures, 150 Work Orders, 50 Ground Truth Anomalies).
- Cryptographic SHA-256 composite digest matched identically across both independent trials:
  ```text
  bb1679e29e63ff0c4557a81e4918013627e275154076a9c047fd62a7bc2c85cd
  ```

---

## 6. Manual UI Verification

Manual UI checks were conducted on the running frontend (`http://localhost:3000`):
- **Fleet Dashboard:** Confirmed rendering of plant KPI summary cards, machine status distribution, and topology navigation.
- **Machine Detail View:** Confirmed 5-channel multi-sensor time-series charts (Vibration, Temperature, Acoustic, Pressure, Current) over historical lookback windows.
- **Work Order Management:** Confirmed tabular rendering of corrective maintenance work orders with technician specialization assignments.
- **Data Quality & Anomaly Audit:** Confirmed active surfacing of the 5 deliberate edge-case anomalies with exact ground-truth reconciliation counts.
