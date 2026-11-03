# Reproducibility Verification Report

**Verification Timestamp (UTC):** 2026-11-03T05:13:36.580890+00:00  
**Evaluation Master Seed:** `20261022`  
**Environment:** Safe isolated dry-run (No production database modification)  
**Overall Reproducibility Result:** PASS (100% Deterministic & Invariant)

---

## 1. Executive Summary

This report documents the double-blind reproducible verification of the synthetic data generation pipeline for the Industrial Predictive Maintenance System. The generator was executed twice in complete isolation using fixed seed `20261022`.

All record counts, mathematical sensor signal trajectories, and cryptographic SHA-256 digests were audited.

| Benchmark Aspect | Run 1 | Run 2 | Invariance Status |
| :--- | :--- | :--- | :--- |
| **Plants Count** | 3 | 3 | **MATCH** |
| **Production Lines Count** | 12 | 12 | **MATCH** |
| **Machines Count** | 100 | 100 | **MATCH** |
| **Sensors Count** | 500 | 500 | **MATCH** |
| **Telemetry Volume** | 2,160,000 | 2,160,000 | **MATCH** |
| **Failure Events Volume** | 150 | 150 | **MATCH** |
| **Type A Failures** | 23 | 23 | **MATCH** |
| **Type B Failures** | 127 | 127 | **MATCH** |

---

## 2. Cryptographic SHA-256 Checksum Audit

| Artifact Hash Domain | Run 1 SHA-256 | Run 2 SHA-256 | Match |
| :--- | :--- | :--- | :--- |
| **Master Data Hash** | `6d76b2503fbbde0af60aca191f1471f26ca7b34cec517969730cc6ea5e960a63` | `6d76b2503fbbde0af60aca191f1471f26ca7b34cec517969730cc6ea5e960a63` | YES |
| **Telemetry Math Hash** | `a249087c4d02870c0124a746fbae161dd7510282c12517901335f0e91b56532c` | `a249087c4d02870c0124a746fbae161dd7510282c12517901335f0e91b56532c` | YES |
| **Failure Data Hash** | `25a471bc62ce3f8e142810cb82b9bdf9cf4a20db973818b53f1552801af8b5e2` | `25a471bc62ce3f8e142810cb82b9bdf9cf4a20db973818b53f1552801af8b5e2` | YES |
| **Overall Trial Hash** | `47b9e0467ab7334088b863f7d689eda706cc91b2eabb42f4afee0acb95a01de3` | `47b9e0467ab7334088b863f7d689eda706cc91b2eabb42f4afee0acb95a01de3` | YES |

---

## 3. Data Integrity & Safety Guarantee

- **Zero Database Degradation:** Neither verification trial performed `DROP TABLE`, `TRUNCATE`, or `DELETE` on the active PostgreSQL database.
- **Strict Seed Derivation:** Sensor-level pseudo-random numbers derive deterministically via SHA-256 seed hashing: `seed = SHA256(master_seed : sensor_id : sensor_code)`.
- **Temporal Alignment:** Telemetry sampling covers exact 90-day window (`2026-08-04T00:00:00Z` to `2026-11-02T00:00:00Z`) at 30-minute cadence (4,320 readings per sensor).
