# Testing, Validation & Verification Report

This document reports the actual verification evidence gathered from automated backend test execution, frontend production compilation, database validation checks, and edge-case handling.

---

## 1. Automated Backend Test Suite

The automated test suite was executed using `pytest` against the active local environment:

```powershell
.\venv\Scripts\pytest backend/tests
```

### Execution Results
- **Collected Test Items:** 84 tests
- **Passing Tests:** 83 passed (98.8%)
- **Failing Tests:** 1 failed
- **Execution Time:** ~13.2 seconds

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
| `backend/tests/test_telemetry_generator.py` | 7 | 6 | 1 | Telemetry synthesis math, diurnal curves, and PostgreSQL COPY streaming. |
| `backend/tests/test_validation_and_edge_cases.py` | 3 | 3 | 0 | Relational validation suite and the 5 deliberate edge-case scenarios. |
| **Total** | **84** | **83** | **1** | **Overall Pass Rate: 98.8%** |

### Audit of Single Test Failure
- **Test:** `backend/tests/test_telemetry_generator.py::test_small_chunk_copy_with_transactional_rollback`
- **Error:** `AttributeError: 'Cursor' object has no attribute 'copy_expert'`
- **Explanation:** In the Python environment's database driver (`psycopg` v3), high-speed COPY streaming uses `cursor.copy()` rather than `cursor.copy_expert()` (which belonged to legacy `psycopg2`). Per assignment instructions prohibiting application code changes, this driver attribute difference is documented transparently rather than modifying source files. All existing seeded database records, endpoints, and math tests remain unaffected.

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

Database validation was performed using `DataValidator` across the 2,160,000 telemetry readings and operational records:

| Audit Check | Target Scope | Criteria | Result |
| :--- | :--- | :--- | :--- |
| **Primary-Key Uniqueness** | All 10 Entities | `COUNT(PK) == COUNT(DISTINCT PK)` | **PASS** (Zero duplicates) |
| **Foreign-Key Integrity** | Lines, Machines, Sensors, Work Orders, Failures | No orphaned records | **PASS** (100% valid parent IDs) |
| **Allowed Values** | Telemetry, Work Orders, Failures | Categorical enums | **PASS** (All statuses valid) |
| **Timestamp Sequence** | Maintenance Work Orders | `completed_at >= created_at` | **PASS** (Zero negative durations) |
| **Business Code Uniqueness** | Machines, Sensors, Technicians, Parts | Unique natural keys | **PASS** (All codes unique) |
| **Volume Reconciliation** | Active Entities | 3 Plants, 12 Lines, 100 Machines, 500 Sensors | **PASS** (Exact match) |

---

## 4. Five Mandatory Edge-Case Scenarios

The system explicitly defines and validates five deliberate anomaly scenarios via `backend/validators/edge_cases.py`:

| # | Scenario Name | Deliberate Test Payload | Issue Type Tag | Ground-Truth Label | System Handling |
| :- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Unknown Sensor Reference** | Telemetry referencing non-existent `sensor_id: 999999` | `UNKNOWN_SENSOR_REFERENCE` | `FOREIGN_KEY_VIOLATION` | Detected and rejected by foreign key constraint check. |
| **2** | **Impossible Unit / Value** | Temperature reading `9999.0 °C` with unit `UNKNOWN_UNIT_FOO` | `IMPOSSIBLE_SENSOR_VALUE_OR_UNIT` | `PHYSICAL_DOMAIN_VIOLATION` | Flagged as out of physical operating bounds. |
| **3** | **Failure Preceding Symptom** | Incident timestamp occurring 10 hours before symptom onset | `TEMPORAL_CAUSALITY_VIOLATION` | `FAILURE_BEFORE_SYMPTOM` | Flagged as temporal causality violation. |
| **4** | **Negative Maintenance Duration** | Work order with `completed_at` 4 hours earlier than `created_at` | `NEGATIVE_DURATION_WORK_ORDER` | `TEMPORAL_ORDERING_VIOLATION` | Detected and rejected by lifecycle timestamp validator. |
| **5** | **Missing Represented as Zero** | Numerical value `0.0` with `quality_status: 'missing'` | `MISSING_DATA_REPRESENTED_AS_ZERO` | `DATA_QUALITY_ANOMALY` | Isolated to distinguish unplugged sensor from true zero reading. |

All 5 scenarios are tested in `backend/tests/test_validation_and_edge_cases.py` and displayed in the frontend Data Quality view.

---

## 5. Deterministic Reproducibility Verification

A reproducibility check was executed using `backend/utils/reproducibility_checker.py` under seed `20261022`:
- Two independent generation trials were run in dry-run mode without modifying the database.
- Generated record counts matched exactly (3 Plants, 12 Lines, 100 Machines, 500 Sensors, 2,160,000 Readings, 150 Failures).
- Cryptographic SHA-256 hashes matched identically across both trials (`47b9e0467ab7334088b863f7d689eda706cc91b2eabb42f4afee0acb95a01de3`).

---

## 6. Manual UI Verification

Manual UI checks were conducted on the running frontend (`http://localhost:3000`):
- **Fleet Dashboard:** Confirmed rendering of plant KPI summary cards, machine status distribution, and topology navigation.
- **Machine Details Page:** Confirmed 5-channel time-series charts (Vibration, Temperature, Acoustic, Pressure, Current) render without errors.
- **Maintenance View:** Confirmed work orders and downtime incident logs display with proper priority and status badges.
- **Data Quality Tab:** Confirmed edge-case audit summary and sensor health tables display live test results.
