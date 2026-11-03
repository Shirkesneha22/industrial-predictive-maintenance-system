# Project Assumptions & Limitations

This document outlines the real operational assumptions, known limitations, and non-implemented areas of the current system.

---

## 1. Predictive Performance & Breakdown Types

- **Type A (Progressive Degradation):**
  - **Result:** 100% recall (23 of 23 detected) with an average warning lead time of 38.4 hours.
  - Progressive mechanical wear exhibits multi-day statistical drift that the 7-day rolling window detects effectively.
- **Type B (Sudden Stochastic Breakdowns):**
  - **Result:** 0.0% recall (0 of 127 caught).
  - Sudden mechanical fractures or electrical shorts (e.g., instant shaft fracture or coil burnout) show zero prior telemetry degradation. Statistical time-series trend models cannot anticipate sudden random breaks in advance.
- **Overall Supervised Benchmark:**
  - Precision: **88.5%** (23 true positives, 3 false alarms).
  - Overall Recall: **15.3%** (23 of 150 total failures caught due to high prevalence of Type B sudden breakdowns).
  - F1 Score: **26.1%**.

---

## 2. Absence of Validated RUL Prediction

- Remaining Useful Life (RUL) estimation is **not calibrated** by a validated machine learning model.
- Because providing unverified numeric hour countdowns would introduce unsafe false confidence in factory operations, the API intentionally returns `null` for RUL fields.
- Equipment condition is communicated solely through the explainable **Health Index (0–100)** and **Risk Score (0–100)**.

---

## 3. Data Ingestion & Scalability Assumptions

- **Batch Telemetry Loading:** The current simulator uses PostgreSQL `COPY` bulk ingestion. In an industrial enterprise deployment, a streaming message broker (e.g., Apache Kafka or MQTT) and a stream processor (e.g., Apache Flink) would be required for sub-second sensor stream ingestion.
- **Single Node Database:** Telemetry storage resides on a single PostgreSQL instance. At multi-year enterprise volume (billions of readings), hypertable partitioning (TimescaleDB) or distributed column storage would be necessary.
- **Synthetic Data Limitations:** Although physics-informed formulas simulate shift thermal cycles and mechanical wear curves, real factory sensor feeds contain complex acoustic noise, unpredictable human interventions, and ambient weather fluctuations not fully replicated here.
