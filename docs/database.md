# Database Design

> **See [database_schema.md](database_schema.md) for the complete entity-relationship documentation.**

The system uses **PostgreSQL 15+** with a normalized relational schema across **10 core entities** and one many-to-many bridge table.

## Summary

| Entity | Table | Records |
| :--- | :--- | :--- |
| Plant | `plants` | 3 |
| Production Line | `production_lines` | 12 |
| Machine | `machines` | 100 |
| Sensor | `sensors` | 500 |
| Telemetry Event | `telemetry_events` | 2,160,000 (full) / 240,000 (starter) |
| Operating Shift | `operating_shifts` | 9 |
| Failure Event | `failure_events` | 150 |
| Maintenance Work Order | `maintenance_work_orders` | 150 |
| Part | `parts` | 50 |
| Technician | `technicians` | 20 |
| Machine-Part (bridge) | `machine_parts` | 449 associations |

Full schema definitions, column types, constraints, indexes, and the ER diagram are documented in [`database_schema.md`](database_schema.md).
