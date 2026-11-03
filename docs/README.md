# Documentation Index

This directory contains the engineering documentation for the Industrial Predictive Maintenance platform:

- [System Architecture](architecture.md): Overview of frontend, backend, PostgreSQL, feature engineering, and predictive pipelines.
- [Database Schema & ERD](database_schema.md): PostgreSQL schema models, 10 core entities, many-to-many bridge table, and foreign-key constraints.
- [Data Dictionary](data_dictionary.md): Detailed specification of fields, data types, nullability, constraints, and descriptions.
- [Technical Design Decisions](design_decisions.md): Explanations for technology choices, rule-based risk scoring, and multi-sensor correlation trade-offs.
- [Testing & Validation Report](testing_and_validation.md): Verification evidence covering backend tests, frontend builds, database integrity, and 5 edge cases.
- [Assumptions & Limitations](limitations.md): Operational assumptions, Type A vs Type B breakdown detection performance, and RUL scope.
- [API Specification](api.md): REST API route groups, schemas, and query parameters.
- [Data Validation Summary](data_validation_summary.md): Summary audit of relational constraints and edge-case detection.
- [Reproducibility Verification Report](reproducibility_report.md): Dual-run cryptographic audit under fixed seed `20261022`.
- [Source Manifest](source_manifest.md): Complete repository file index.
