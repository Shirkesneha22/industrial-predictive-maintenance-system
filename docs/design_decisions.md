# Technical Design Decisions & Trade-Offs

This document explains the key engineering and architectural decisions made in the Industrial Predictive Maintenance System, written in clear and accessible language.

---

## 1. Core Technology Decisions

### Why PostgreSQL?
- **Relational Consistency:** Industrial assets have strict hierarchical relationships (`Plant` $\rightarrow$ `Line` $\rightarrow$ `Machine` $\rightarrow$ `Sensor` $\rightarrow$ `Telemetry`). Foreign keys ensure referential integrity, preventing orphaned sensor streams.
- **Time-Series Efficiency:** PostgreSQL handles indexed time-series data effectively using composite indexes (`sensor_id`, `recorded_at`) and high-throughput streaming bulk inserts (`COPY`).
- **Trade-Off:** A dedicated time-series database (such as TimescaleDB or InfluxDB) or distributed storage (like ClickHouse) could yield higher compression at multi-billion-row scale, but standard PostgreSQL keeps the operational footprint minimal and avoids multi-database synchronization overhead.

### Why FastAPI?
- **Modern Asynchronous Python:** Built on Starlette and Pydantic, FastAPI delivers high throughput, native type validation, and automatic OpenAPI (Swagger) documentation out of the box.
- **Python Ecosystem Integration:** Python provides rich numeric and statistical packages (NumPy, SciPy) essential for telemetry signal processing and feature calculation.
- **Trade-Off:** FastAPI is slightly higher-level than raw ASGI frameworks, but the built-in validation and interactive Swagger documentation significantly accelerate development and testing.

### Why React?
- **Interactive Component State:** Industrial monitoring requires dynamic UI controls, such as asset search, real-time filtering across plants and production lines, and interactive multi-channel charts (Recharts).
- **Single Page Architecture:** A responsive SPA provides factory operators with seamless navigation between high-level fleet health overviews and granular sensor time-series views without full page reloads.
- **Trade-Off:** Adds client-side build complexity (Webpack, Babel), but delivers a smooth, low-latency operator experience.

---

## 2. Modeling & Architecture Decisions

### Why Synthetic Data?
- **Controlled Failure Profiles:** Real industrial equipment failure logs are proprietary, scarce, and rarely public. Deterministic synthetic generation allows us to simulate controlled mechanical degradation (e.g., bearing wear, thermal runaway) alongside realistic operational noise.
- **Deterministic Reproducibility:** Using a fixed seed (`20261022`) guarantees that all reviewers, automated tests, and verification scripts observe identical numbers and failure events across test runs.
- **Trade-Off:** Synthetic telemetry cannot capture every subtle anomaly present in physical manufacturing environments, but it provides a rigorous, reproducible benchmark for pipeline verification.

### Why Rule-Based Risk Scoring Instead of Deep Learning / ML?
- **Explainability:** In industrial maintenance, operators need clear, physics-informed reasons before halting multimillion-dollar machinery (e.g., *"Elevated vibration accompanied by high bearing temperature"*), rather than opaque probability outputs from a black-box neural network.
- **Transparent Boundaries:** The rule-based engine normalizes rolling standard deviations and Z-scores into an intuitive Health Index (0–100) and Risk Score (0–100) with clear operational tiers: Normal ($<35$), Warning ($35–65$), and Critical ($>65$).
- **No Uncalibrated RUL Claim:** Remaining Useful Life (RUL) prediction requires extensive run-to-failure runtimes across various operational loads. Because an uncalibrated machine learning model risks false confidence, RUL is explicitly marked as uncalibrated (`None`) in API responses rather than inventing artificial values.
- **Trade-Off:** Rule-based heuristics require manual threshold tuning and domain knowledge, whereas supervised ML models could potentially uncover non-linear interactions if vast historical training datasets existed.

### Why Multi-Sensor Correlation?
- **Preventing False Alarms:** In real industrial plants, individual sensors frequently produce noise, spikes, or calibration drift due to wiring issues or electrical interference.
- **Physics Logic:** True mechanical breakdowns involve multiple physical symptoms simultaneously (e.g., increased friction produces both vibration and heat). The risk engine requires anomalies across $\ge 2$ physical channels to trigger a Warning or Critical alert. Single-channel anomalies are capped at a low risk score ($30.0$) and flagged for sensor inspection.
- **Trade-Off:** A failure mode that manifests exclusively in a single sensor type could be slightly delayed in detection, but false alarms that unnecessarily halt production lines are substantially reduced.

### Why Ground-Truth Separation (Anti-Leakage)?
- **Strict Predictive Integrity:** Failure event timestamps and maintenance logs are stored in separate relational tables (`failure_events`, `maintenance_work_orders`) and are completely sequestered during feature extraction.
- **Point-in-Time Cutoff:** The feature pipeline strictly filters telemetry with `recorded_at < prediction_timestamp`. No future telemetry or failure labels are accessible to the risk evaluation engine.
- **Trade-Off:** Querying point-in-time slices requires explicit timestamp filtering on indexed columns, but guarantees that offline evaluation metrics reflect realistic forward-looking operational conditions.
