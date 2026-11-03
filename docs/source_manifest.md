# Source Manifest — Industrial Predictive Maintenance System

Comprehensive index of source code, configuration files, exports, and test suites in this repository.

---

## 1. Backend Architecture (`/backend`)

### Core Entry & Database Configuration
- `backend/main.py`: FastAPI application entry point, CORS middleware, route registration, and `/health` probe.
- `backend/database.py`: SQLAlchemy engine, `SessionLocal` factory, declarative base, and dependency injection `get_db()`.
- `backend/config.py`: Pydantic settings loading `.env` variables (database URL, CORS origins, debug mode).

### Database Models (`backend/models/`)
- `backend/models/plant.py`: `Plant` model (3 industrial facilities).
- `backend/models/production_line.py`: `ProductionLine` model (12 production lines).
- `backend/models/machine.py`: `Machine` model (100 equipment assets).
- `backend/models/sensor.py`: `Sensor` model (500 IoT sensors).
- `backend/models/telemetry_event.py`: `TelemetryEvent` model (2,160,000 time-series records).
- `backend/models/operating_shift.py`: `OperatingShift` model (9 shift schedules).
- `backend/models/maintenance_work_order.py`: `MaintenanceWorkOrder` model (150 work orders).
- `backend/models/failure_event.py`: `FailureEvent` model (150 failure records).
- `backend/models/part.py`: `Part` model (50 spare parts) and `machine_parts` bridge table (449 associations).
- `backend/models/technician.py`: `Technician` model (20 certified field engineers).
- `backend/models/__init__.py`: Package model exports.

### API Routes (`backend/routes/`)
- `backend/routes/machines.py`: Equipment catalog, machine details, sensor topology, point-in-time risk evaluation, and machine maintenance history.
- `backend/routes/predictions.py`: Fleet-wide anomaly detection, health index ranking, and RUL estimation with anti-leakage guarantee.
- `backend/routes/telemetry.py`: Historical sensor time-series streams, latest readings, and paginated queries.
- `backend/routes/maintenance.py`: Work orders log, failure events, and aggregate maintenance overview.
- `backend/routes/evaluation.py`: Supervised offline evaluation metrics, Type A vs Type B cohort breakdown, edge-case validation, and database audit.
- `backend/routes/__init__.py`: Package router exports.

### Domain Schemas (`backend/schemas/`)
- `backend/schemas/risk.py`: Machine responses, risk scores, contributing sensor signals, fleet anomaly summaries.
- `backend/schemas/evaluation.py`: Evaluation splits, cohort breakdown, lead times, detection records.
- `backend/schemas/maintenance.py`: Work order and failure event schemas, pagination containers.
- `backend/schemas/__init__.py`: Package schema exports.

### Business Logic Services (`backend/services/`)
- `backend/services/risk_engine.py`: Explainable, rule-based machine health index (0-100) and risk score (0-100) calculation.
- `backend/services/feature_engineering.py`: Temporal feature extraction strictly before point-in-time cutoffs (Z-score, trends, multi-channel aggregation).
- `backend/services/anomaly_detector.py`: Physics-informed anomaly detection distinguishing isolated sensor faults from correlated wear.
- `backend/services/offline_evaluator.py`: Supervised offline evaluation engine comparing risk alerts with sequestered ground truth.

### Data Generators (`backend/generators/`)
- `backend/generators/cli.py`: Command-line interface for synthetic master data, telemetry, and failure generation.
- `backend/generators/master_data_constants.py`: Constants for 3 plants, 12 lines, 100 machines, 500 sensors, 50 parts, 20 technicians.
- `backend/generators/master_data_generator.py`: Deterministic master data generation with seed `20261022`.
- `backend/generators/telemetry_constants.py`: 90-day time window, 30-min sampling cadence, physical sensor baselines.
- `backend/generators/telemetry_generator.py`: High-throughput PostgreSQL COPY streaming generator.
- `backend/generators/telemetry_math.py`: Signal synthesis formulas (diurnal cycles, shift loads, degradation curves).
- `backend/generators/failure_constants.py`: Failure classifications (150 total: 23 Type A progressive, 127 Type B sudden).
- `backend/generators/failure_generator.py`: Failure events and corrective maintenance work orders generation.

### Validators & Edge Cases (`backend/validators/`)
- `backend/validators/edge_cases.py`: Implementation and verification of the 5 mandatory edge-case scenarios with explicit issue_type and ground_truth tags.
- `backend/validators/data_validator.py`: Comprehensive relational, foreign-key, timestamp, and lifecycle validation suite.

### Utilities (`backend/utils/`)
- `backend/utils/exporter.py`: Automated export of database tables to CSV, JSON, SQL seed, and sequestered ground truth.
- `backend/utils/reproducibility_checker.py`: Dual-run reproducibility verification script with SHA-256 checksum comparison.

### Test Suite (`backend/tests/`)
- `backend/tests/conftest.py`: Pytest test client fixtures.
- `backend/tests/test_api_endpoints.py`: Integration tests for machines, telemetry, and predictions endpoints.
- `backend/tests/test_maintenance_endpoints.py`: Integration tests for maintenance, failures, and evaluation endpoints.
- `backend/tests/test_validation_and_edge_cases.py`: Unit tests for DataValidator and 5 mandatory edge cases.
- `backend/tests/test_risk_engine.py`: Unit tests for rule-based risk calculations and action recommendations.
- `backend/tests/test_feature_engineering.py`: Unit tests for anti-leakage temporal feature extraction.
- `backend/tests/test_offline_evaluation.py`: Unit tests for alert matching and cohort separation.
- `backend/tests/test_master_data_generator.py`: Unit tests for deterministic master data generation.
- `backend/tests/test_telemetry_generator.py`: Unit tests for signal synthesis math and quality statuses.
- `backend/tests/test_failure_generator.py`: Unit tests for failure event and work order generation.
- `backend/tests/test_health.py`: Basic API health check test.

---

## 2. Frontend Architecture (`/frontend`)

### Layouts & Navigation (`frontend/src/layouts/`)
- `DashboardLayout.jsx`: Application shell with sidebar, header, and main content area.
- `Sidebar.jsx`: Collapsible navigation sidebar linking Overview, Machines, Maintenance, Evaluation, Data Quality.
- `Header.jsx`: Top navigation header with system status indicators.

### Pages (`frontend/src/pages/`)
- `OverviewPage.jsx`: Fleet status dashboard showing total plants (3), lines (12), machines (100), sensors (500), overall machine health index, normal/warning/critical distribution, and urgent alerts.
- `MachinesPage.jsx`: Paginated machine inventory with production line, active status, risk level filters, and search.
- `MachineDetailPage.jsx`: Machine view displaying 5-sensor telemetry, time-series chart, contributing signal z-scores, contextual recommendation, and full maintenance history.
- `MaintenancePage.jsx`: Maintenance work orders, equipment failure events, downtime totals, and spare parts management.
- `EvaluationPage.jsx`: Model evaluation showing Precision, Recall, F1, Confusion Matrix, Type A vs Type B breakdown, and documented limitations.
- `DataQualityPage.jsx`: Telemetry data quality breakdown and verification of the 5 mandatory edge cases.
- `NotFoundPage.jsx`: 404 fallback page.

### API Client Services (`frontend/src/services/`)
- `api.js`: Axios client configured with base URL and timeout.
- `machineService.js`: Calls machine listing, details, risk score, and maintenance history.
- `predictionService.js`: Calls fleet-wide anomalies and RUL estimation.
- `telemetryService.js`: Calls historical telemetry, latest sensor readings, and quality counts.
- `maintenanceService.js`: Calls work orders, failure events, and maintenance overview.
- `evaluationService.js`: Calls evaluation summary, edge cases, and data validation audit.

### Reusable UI Components (`frontend/src/components/common/`)
- `StatCard.jsx`: Metric display card with icon, subtitle, and color variant.
- `Badge.jsx`: Categorical status pill (Normal, Warning, Critical, Missing).
- `Card.jsx`: Standard container card with title, subtitle, and action slot.
- `Pagination.jsx`: Numbered pagination navigation bar.
- `LoadingSpinner.jsx`: Async loading indicator.
- `ErrorAlert.jsx`: User-friendly error alert with retry button.
- `EmptyState.jsx`: Placeholder display for empty query results.

---

## 3. Data & Export Artifacts (`/data`)

- `data/exports/csv/`: 11 CSV files (plants, production_lines, machines, sensors, operating_shifts, parts, technicians, machine_parts, maintenance_work_orders, failure_events, telemetry_sample).
- `data/exports/json/`: 11 JSON files corresponding to all database tables and telemetry sample.
- `data/exports/sql/seed_master_and_events.sql`: SQL seed statements for deterministic setup.
- `data/ground_truth/failures_ground_truth.csv`: Isolated ground-truth failure records.
- `data/ground_truth/failures_ground_truth.json`: Isolated ground-truth failure records in JSON.

---

## 4. Documentation (`/docs`)

- `docs/data_dictionary.md`: Data dictionary for all 10 core entities and bridge table.
- `docs/database_schema.md`: Entity-relationship diagram, cardinality, and index documentation.
- `docs/data_validation_summary.md`: Integrity verification results and edge-cases validation summary.
- `docs/reproducibility_report.md`: Double-run reproducibility report with SHA-256 checksum verification.
- `docs/source_manifest.md`: Complete source manifest (this file).
- `docs/architecture.md`: High-level system architecture and component interactions.
- `docs/api.md`: API endpoints documentation.
- `README.md` (root): Complete project guide, setup instructions, generator commands, and execution guide.
