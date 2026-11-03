# Reproducibility Verification Report

**Verification Timestamp (UTC):** 2026-11-03T20:28:08.011361+00:00  
**Evaluation Master Seed:** `20261022`  
**Overall Reproducibility Result:** PASS (100% Deterministic & Invariant)  
**Composite Dataset SHA-256 Digest:** `bb1679e29e63ff0c4557a81e4918013627e275154076a9c047fd62a7bc2c85cd`

---

## 1. Executive Summary & Checksum Audit

This report verifies bit-for-bit reproducibility of the Industrial Predictive Maintenance System across two independent runs using fixed seed `20261022`.

All disk-persisted CSV files (under `data/exports/csv/` and `data/ground_truth/`) containing spec-compliant hierarchical string identifiers (`PLT-*`, `LINE-*`, `MCH-*`, `SNS-*`, `WO-*`, `PRT-*`, `TECH-*`) were audited and hashed.

| Exported File | Row Count | File Size | Run 1 SHA-256 Checksum | Run 2 SHA-256 Checksum | Match Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `anomalies_failure_events.csv` | 10 | 2,819 B | `ec18295da65cdcc12e82334033d640d3f95a74378babe6d49ac106a592d04660` | `ec18295da65cdcc12e82334033d640d3f95a74378babe6d49ac106a592d04660` | **MATCH** |
| `anomalies_maintenance_work_orders.csv` | 10 | 2,524 B | `a6b7eb5c3ebadde33ca4a3e1412e435a031215f103d755ecce7bf0a85bcc0b65` | `a6b7eb5c3ebadde33ca4a3e1412e435a031215f103d755ecce7bf0a85bcc0b65` | **MATCH** |
| `anomalies_telemetry_events.csv` | 30 | 4,892 B | `998224f1b4ea7589320b4107d1bc5874b29949a2d3b5d0b5527560cbaed0321d` | `998224f1b4ea7589320b4107d1bc5874b29949a2d3b5d0b5527560cbaed0321d` | **MATCH** |
| `failure_events.csv` | 150 | 51,669 B | `ebe51f9f25af8c8607ddfb7d2aad6a5e81a1499fb1106824420dd8afc49bb8e7` | `ebe51f9f25af8c8607ddfb7d2aad6a5e81a1499fb1106824420dd8afc49bb8e7` | **MATCH** |
| `failures_ground_truth.csv` | 150 | 54,813 B | `9e4d8d10630059dd853b91bed6be16b35995f92b970f9ad2ccc7f960939a2610` | `9e4d8d10630059dd853b91bed6be16b35995f92b970f9ad2ccc7f960939a2610` | **MATCH** |
| `ground_truth.csv` | 50 | 13,666 B | `48197075b9260ceb5d0c91d7a5c66ccb6ec239bc26956faf71d64be863bb03a0` | `48197075b9260ceb5d0c91d7a5c66ccb6ec239bc26956faf71d64be863bb03a0` | **MATCH** |
| `machine_parts.csv` | 449 | 15,735 B | `07d7db3fe75c7b86e392509014513481e0b06cc58d1f06b4851c79f4627ed9c4` | `07d7db3fe75c7b86e392509014513481e0b06cc58d1f06b4851c79f4627ed9c4` | **MATCH** |
| `machines.csv` | 100 | 22,463 B | `787bc6b93f4167f63344e1b28f2ffe84a6058339d0ce0330f6c96e812920115d` | `787bc6b93f4167f63344e1b28f2ffe84a6058339d0ce0330f6c96e812920115d` | **MATCH** |
| `maintenance_work_orders.csv` | 150 | 53,785 B | `bff015e867a95838af46bf7646a83f93a00ffac220c5557fe6f9bcb0113d37a2` | `bff015e867a95838af46bf7646a83f93a00ffac220c5557fe6f9bcb0113d37a2` | **MATCH** |
| `operating_shifts.csv` | 9 | 1,168 B | `896daf505c4d53f1cb2c366451ab735d36d8024ca5f440c75cb6dd6520d8a60b` | `896daf505c4d53f1cb2c366451ab735d36d8024ca5f440c75cb6dd6520d8a60b` | **MATCH** |
| `parts.csv` | 50 | 8,536 B | `24b2bb775cca1ab0fd5a2333bb886cac707bbeee13ade599082eef0965b5c9ca` | `24b2bb775cca1ab0fd5a2333bb886cac707bbeee13ade599082eef0965b5c9ca` | **MATCH** |
| `plants.csv` | 3 | 409 B | `8a3ea503bb8cd15605bdf61a97f4b9ae8efdc3f562baa3ac3e87c93a4c3f6fba` | `8a3ea503bb8cd15605bdf61a97f4b9ae8efdc3f562baa3ac3e87c93a4c3f6fba` | **MATCH** |
| `production_lines.csv` | 12 | 1,521 B | `cd90152b0d4c8e8aad4835ce9865f824e1e23a4c191ba29a03cbece1872cb9fe` | `cd90152b0d4c8e8aad4835ce9865f824e1e23a4c191ba29a03cbece1872cb9fe` | **MATCH** |
| `sensors.csv` | 500 | 80,390 B | `63b38dfc4c0eff567a664acb496a8b2777caabbdc0d8c49a27c18f10dbc892a0` | `63b38dfc4c0eff567a664acb496a8b2777caabbdc0d8c49a27c18f10dbc892a0` | **MATCH** |
| `technicians.csv` | 20 | 2,710 B | `d024fc954e7bb97c5693ed161a1328751085c92741a329d647c2739a20757bd9` | `d024fc954e7bb97c5693ed161a1328751085c92741a329d647c2739a20757bd9` | **MATCH** |
| `telemetry_sample.csv` | 5,000 | 797,693 B | `1947d93999c7669ab968eff9b9bdf996693a59b2b0c85c3632dcd1e91b3ad556` | `1947d93999c7669ab968eff9b9bdf996693a59b2b0c85c3632dcd1e91b3ad556` | **MATCH** |

---

## 2. Composite Digest Comparison

- **Run 1 Composite Digest:** `bb1679e29e63ff0c4557a81e4918013627e275154076a9c047fd62a7bc2c85cd`
- **Run 2 Composite Digest:** `bb1679e29e63ff0c4557a81e4918013627e275154076a9c047fd62a7bc2c85cd`
- **Bit-for-Bit Identity:** `100% MATCH`

---

## 3. Explanation of Previous Hash (`47b9e046...`)

The legacy reproducibility checker did not inspect disk-exported CSV files. Instead, it evaluated an in-memory dictionary consisting of static count integers (`len(PLANTS_DATA)=3`, `machines=100`, `sensors=500`), sample sensor slices using old `MCH-001` format strings, and failure count constants. Because that in-memory simulation never read from disk or reflected the spec-compliant hierarchical ID nomenclature, it generated an invariant hash (`47b9e046...`).

The updated checker computes cryptographic SHA-256 digests directly from the exported CSV files and ground-truth datasets on disk. The new composite digest (`bb1679e29e63ff0c4557a81e4918013627e275154076a9c047fd62a7bc2c85cd`) fully incorporates all hierarchical string IDs and physical plausibility anomaly formatting.
