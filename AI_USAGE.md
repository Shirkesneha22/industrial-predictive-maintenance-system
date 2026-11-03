# AI Usage & Transparent Prompt History

This document details the transparent disclosure of AI assistance used during the 72-Hour Candidate Project, including tools used, representative prompts, human review processes, and validation procedures.

---

## 1. AI Tools & Environment

- **Primary AI Assistant:** Google Antigravity (powered by Gemini models)
- **Role:** Pair programmer for scaffolding boilerplate, proposing schema relationships, assisting with synthetic math signals, generating unit test templates, and reviewing code against candidate project specifications.
- **Candidate Ownership:** All AI-suggested code, schema designs, and test suites were independently reviewed, validated against business logic, debugged, and executed in the local Windows environment.

---

## 2. Representative Prompt History

The following 9 summarized prompts represent the major phases of AI interaction throughout the project lifecycle:

### Phase 1: Project Planning & Architecture Scaffolding
- **Summarized Prompt:** *"Help outline a clean, maintainable architecture for an industrial predictive maintenance system using FastAPI, PostgreSQL, and React.js. The system needs to simulate 100 machines across 3 plants, ingest 90 days of sensor data, and provide explainable risk scoring without data leakage."*
- **Purpose:** Establish clean separation of concerns across backend routes, services, models, validators, and the React frontend.
- **Assistance Provided:** Recommended modular directory structure, point-in-time querying strategy to avoid data leakage, and separation between sequestered failure ground truth and operational telemetry.

### Phase 2: Database Schema & Relational Design
- **Summarized Prompt:** *"Design a normalized PostgreSQL schema with 10 core entities covering industrial plants, production lines, machines, sensors, time-series telemetry, operating shifts, maintenance work orders, failure events, spare parts, and technicians. Include a many-to-many bridge table between machines and parts."*
- **Purpose:** Create standard SQLAlchemy models with proper foreign keys, indexes, and delete behaviors (`RESTRICT` vs `CASCADE`).
- **Assistance Provided:** Generated initial SQLAlchemy ORM models with composite indexing on `(sensor_id, recorded_at)` for high-throughput time-series queries.

### Phase 3: High-Volume Synthetic Telemetry Generation
- **Summarized Prompt:** *"Write a deterministic synthetic data generator in Python using seed 20261022. It should produce 2,160,000 readings across 500 sensors over 90 days with diurnal thermal cycling, shift load adjustments, and progressive degradation curves for bearing failures."*
- **Purpose:** Produce realistic industrial telemetry without needing external proprietary datasets.
- **Assistance Provided:** Provided mathematical formulas for diurnal sine waves, shift multiplier factors, Gaussian noise, and fast bulk ingestion using in-memory string buffers.

### Phase 4: Anti-Leakage Feature Engineering
- **Summarized Prompt:** *"Create a feature engineering service that calculates rolling 7-day mean, standard deviation, Z-score, and trend slope per sensor. Strictly ensure that only telemetry recorded prior to the prediction timestamp is queried."*
- **Purpose:** Prevent future data leakage during retrospective and real-time risk evaluation.
- **Assistance Provided:** Implemented strict temporal boundary queries (`recorded_at < prediction_timestamp`) and rolling statistics calculations.

### Phase 5: Physics-Informed Rule-Based Risk Engine
- **Summarized Prompt:** *"Implement an explainable rule-based risk engine that evaluates machine health on a 0-100 scale. Distinguish single-sensor noise from multi-sensor mechanical degradation, and return null for Remaining Useful Life (RUL) since an uncalibrated model should not make unverified claims."*
- **Purpose:** Build transparent risk scoring that industrial operators can understand and act upon.
- **Assistance Provided:** Scaffolded logic capping isolated single-sensor spikes at Risk Score 30.0 (Normal) while escalating multi-sensor anomalies to Warning ($\ge 35$) and Critical ($\ge 65$).

### Phase 6: RESTful API Development
- **Summarized Prompt:** *"Implement FastAPI route endpoints for machine inventory, sensor topology, historical telemetry, latest readings, risk evaluation, maintenance work orders, and offline evaluation metrics with Pydantic validation."*
- **Purpose:** Expose clean REST endpoints with interactive Swagger UI documentation.
- **Assistance Provided:** Generated route handlers, query parameter parsers (`line_id`, `machine_type`), pagination schemas, and error responses (HTTP 400, 404, 422).

### Phase 7: React Frontend & Telemetry Visualizations
- **Summarized Prompt:** *"Create a React dashboard component using Recharts and Lucide icons that renders fleet status KPI cards, machine filtering, and a 5-sensor time-series chart showing vibration, temperature, acoustic, pressure, and current readings."*
- **Purpose:** Provide an intuitive web dashboard for factory supervisors.
- **Assistance Provided:** Drafted responsive UI layouts, time-series line chart components, and status badge indicators.

### Phase 8: Automated Test Suite & Edge-Case Validation
- **Summarized Prompt:** *"Write pytest integration tests covering all API endpoints, relational integrity checks, and 5 specific edge cases: non-existent sensor ID, impossible sensor reading/unit, failure time preceding symptom onset, negative maintenance duration, and missing data represented as zero."*
- **Purpose:** Build an automated test suite verifying edge cases and endpoint contracts.
- **Assistance Provided:** Generated test cases using FastAPI `TestClient` and created assertions validating the 5 assignment edge cases.

### Phase 9: Code Review & Requirement Verification
- **Summarized Prompt:** *"Review the entire project against the 72-hour candidate submission criteria. Audit for target leakage, verify that all 10 entities are implemented, confirm reproducible fixed seeds, and verify test suite pass rates."*
- **Purpose:** Final verification of rubric compliance and identification of edge cases.
- **Assistance Provided:** Helped identify where driver differences occurred and verified that all 10 core entities and 5 edge cases met the assignment specification.

---

## 3. Human Review, Refinements & Debugging

While AI accelerated initial code generation, all code was critically reviewed, tested, and modified by the developer:

1. **Anti-Leakage Cutoff Enforcement:**
   - *AI Draft:* Initial prompt outputs simply grouped telemetry by machine without strict lookback limits.
   - *Developer Refinement:* Enforced strict `recorded_at < prediction_timestamp` database filters and verified that failure tables were completely isolated from the feature computation pipeline.

2. **Database Driver API Debugging:**
   - *Observation:* During backend test execution, `test_small_chunk_copy_with_transactional_rollback` failed due to `AttributeError: 'Cursor' object has no attribute 'copy_expert'`.
   - *Developer Investigation:* Identified that the local environment used modern `psycopg` (v3) where `cursor.copy()` replaced legacy `psycopg2`'s `copy_expert`. Rather than masking this difference or modifying application code contrary to assignment instructions, the behavior was documented transparently.

3. **Temporal Ordering & Data Quality Edge Cases:**
   - *Developer Refinement:* Added explicit database validations checking that `completed_at >= created_at` for work orders and that `value = 0.0` with `quality_status = 'missing'` is treated as an unplugged sensor rather than an operating zero reading.

4. **Honest Evaluation & RUL Transparency:**
   - *Developer Decision:* AI originally suggested predicting hours remaining via simple regression. The developer explicitly rejected this to avoid claiming an uncalibrated Remaining Useful Life (RUL), configuring the API to return `null` and relying on the explainable 0–100 Health Index instead.

---

## 4. Summary of AI Contribution

- **Where AI Accelerated Development:** Rapid boilerplate scaffolding for SQLAlchemy models, Pydantic schemas, Webpack configuration, and pytest fixture templates.
- **Where Human Oversight Was Critical:** Enforcing anti-leakage guards, ensuring mathematical validity of degradation curves, verifying PostgreSQL relational constraints, and validating that the UI and tests reflected actual project reality.
