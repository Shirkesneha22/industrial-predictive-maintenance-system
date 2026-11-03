# Data Dictionary

> [!NOTE]
> **Hierarchical ID Nomenclature in Data Exports:**
> While internal database tables utilize fast native integer surrogate primary keys for relational performance in PostgreSQL, **100% of exported dataset files (CSV, JSON, SQL seed files)** map primary and foreign keys to spec-compliant hierarchical string identifiers (`PLT-*`, `LINE-*`, `MCH-*`, `SNS-*`, `TEL-*`, `WO-*`, `FAIL-*`, `PRT-*`, `TECH-*`). All cross-file joins resolve with 100% referential integrity and 0 broken foreign keys.
 — Industrial Predictive Maintenance System

This document specifies the exact fields, data types, nullability, key constraints, and descriptions for all 10 relational entities and the `machine_parts` bridge table, based on the application's SQLAlchemy models.

---

## 1. Plant (`plants`)
Monitored industrial manufacturing facilities and regional factory sites.

| Field Name | Data Type | Nullable | Key | Constraints / Allowed Values | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `plant_id` | INTEGER | No | PK | Auto-increment sequence | Primary key identifier for the plant. |
| `plant_code` | VARCHAR(50) | No | Unique | Indexed, e.g., `PLANT-PUN-01` | Human-readable corporate facility code. |
| `name` | VARCHAR(100) | No | — | Free-text string | Full display name of the facility. |
| `city` | VARCHAR(100) | Yes | — | E.g., Pune, Chennai, Ahmedabad | Location city. |
| `state` | VARCHAR(100) | Yes | — | Maharashtra, Tamil Nadu, Gujarat | Location state. |
| `is_active` | BOOLEAN | No | — | Default: `TRUE` | Operational monitoring status. |
| `created_at` | TIMESTAMPTZ | No | — | Default: UTC now | Plant record creation timestamp. |

---

## 2. Production Line (`production_lines`)
Discrete manufacturing and assembly lines operating inside a plant.

| Field Name | Data Type | Nullable | Key | Constraints / Allowed Values | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `line_id` | INTEGER | No | PK | Auto-increment sequence | Primary key line identifier. |
| `plant_id` | INTEGER | No | FK | References `plants(plant_id)` ON DELETE CASCADE | Parent plant foreign key (1:N). |
| `line_code` | VARCHAR(50) | No | Unique | Indexed, e.g., `LINE-PUN-01` | Unique production line code. |
| `name` | VARCHAR(100) | No | — | E.g., Chassis Fabrication | Production line display name. |
| `is_active` | BOOLEAN | No | — | Default: `TRUE` | Active operational status flag. |
| `created_at` | TIMESTAMPTZ | No | — | Default: UTC now | Line registration timestamp. |

---

## 3. Machine (`machines`)
Monitored industrial equipment assets.

| Field Name | Data Type | Nullable | Key | Constraints / Allowed Values | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `machine_id` | INTEGER | No | PK | Auto-increment sequence | Primary key machine ID. |
| `line_id` | INTEGER | No | FK | References `production_lines(line_id)` ON DELETE CASCADE | Parent production line foreign key (1:N). |
| `machine_code` | VARCHAR(50) | No | Unique | Indexed, e.g., `MCH-LINE-PLT-001-001-001` | Unique equipment asset tag. |
| `name` | VARCHAR(100) | No | — | Free text | Asset name. |
| `machine_type` | VARCHAR(100) | No | — | Centrifugal Pump, CNC Milling, Industrial Compressor, Hydraulic Press, Robotic Welding Cell | Industrial equipment classification. |
| `manufacturer` | VARCHAR(100) | Yes | — | E.g., Siemens, Kirloskar, Fanuc | Equipment OEM manufacturer. |
| `model_number` | VARCHAR(100) | Yes | — | Free text | Model designation or serial reference. |
| `installation_date` | DATE | Yes | — | ISO-8601 Date (`YYYY-MM-DD`) | Commissioning / installation date. |
| `is_active` | BOOLEAN | No | — | Default: `TRUE` | Active monitoring status. |
| `created_at` | TIMESTAMPTZ | No | — | Default: UTC now | Machine registration timestamp. |

---

## 4. Sensor (`sensors`)
IoT sensor telemetry probes mounted on machines.

| Field Name | Data Type | Nullable | Key | Constraints / Allowed Values | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `sensor_id` | INTEGER | No | PK | Auto-increment sequence | Primary key sensor identifier. |
| `machine_id` | INTEGER | No | FK | References `machines(machine_id)` ON DELETE CASCADE | Monitored machine foreign key (1:N). |
| `sensor_code` | VARCHAR(50) | No | Unique | Indexed, e.g., `SNS-MCH-LINE-PLT-001-001-001-TEMP-01` | Unique sensor barcode identifier. |
| `sensor_type` | VARCHAR(50) | No | — | `Vibration`, `Temperature`, `Acoustic`, `Pressure`, `Current` | Physical measurement category. |
| `unit` | VARCHAR(20) | No | — | `mm/s`, `°C`, `dB`, `bar`, `A` | Engineering unit of measurement. |
| `installation_date` | DATE | Yes | — | ISO-8601 Date (`YYYY-MM-DD`) | Sensor commissioning / calibration date. |
| `is_active` | BOOLEAN | No | — | Default: `TRUE` | Data acquisition active flag. |
| `created_at` | TIMESTAMPTZ | No | — | Default: UTC now | Sensor registration timestamp. |

---

## 5. Telemetry Event (`telemetry_events`)
High-volume time-series telemetry records recorded by sensors.

| Field Name | Data Type | Nullable | Key | Constraints / Allowed Values | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `event_id` | BIGINT | No | PK | Bigint auto-increment sequence | Primary key telemetry event ID. |
| `sensor_id` | INTEGER | No | FK | References `sensors(sensor_id)` ON DELETE RESTRICT | Source sensor foreign key (1:N). |
| `recorded_at` | TIMESTAMPTZ | No | Index | UTC timestamp | Observation measurement timestamp. |
| `value` | DOUBLE PRECISION | Yes | — | Numeric value or `NULL` | Recorded physical measurement (nullable for missing sensor readings). |
| `quality_status` | VARCHAR(30) | No | — | `normal`, `sensor_fault`, `invalid`, `missing` | Telemetry signal quality flag. |
| `created_at` | TIMESTAMPTZ | No | — | Default: UTC now | Ingestion timestamp. |

*Indexes:* Composite index `ix_telemetry_events_sensor_recorded` on `(sensor_id, recorded_at)`.

---

## 6. Operating Shift (`operating_shifts`)
Plant operating shifts defining daily production intensity.

| Field Name | Data Type | Nullable | Key | Constraints / Allowed Values | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `shift_id` | INTEGER | No | PK | Auto-increment sequence | Primary key shift identifier. |
| `plant_id` | INTEGER | No | FK | References `plants(plant_id)` ON DELETE RESTRICT | Host plant foreign key (1:N). |
| `shift_name` | VARCHAR(50) | No | — | Morning Shift, Afternoon Shift, Night Shift | Shift display title. |
| `start_time` | TIMESTAMPTZ | No | — | Timezone-aware timestamp | Shift start time window. |
| `end_time` | TIMESTAMPTZ | No | — | Timezone-aware timestamp | Shift finish time window. |
| `created_at` | TIMESTAMPTZ | No | — | Default: UTC now | Shift creation timestamp. |

---

## 7. Maintenance Work Order (`maintenance_work_orders`)
Corrective and preventive maintenance work orders for machinery.

| Field Name | Data Type | Nullable | Key | Constraints / Allowed Values | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `work_order_id` | INTEGER | No | PK | Auto-increment sequence | Primary key work order identifier. |
| `machine_id` | INTEGER | No | FK | References `machines(machine_id)` ON DELETE RESTRICT | Target machine foreign key (1:N). |
| `technician_id` | INTEGER | Yes | FK | References `technicians(technician_id)` ON DELETE SET NULL | Assigned technician foreign key (1:N, nullable). |
| `work_type` | VARCHAR(50) | No | — | `preventive`, `corrective`, `predictive`, `inspection` | Category of maintenance intervention. |
| `priority` | VARCHAR(20) | No | — | `low`, `medium`, `high`, `critical` | Urgency classification. |
| `status` | VARCHAR(30) | No | Index | `pending`, `in_progress`, `completed`, `cancelled` | Current order status. |
| `description` | TEXT | Yes | — | Free text | Technician notes or failure symptoms. |
| `created_at` | TIMESTAMPTZ | No | — | Default: UTC now | Initiation timestamp. |
| `completed_at` | TIMESTAMPTZ | Yes | — | Must be $\ge$ `created_at` when completed | Work completion timestamp. |

---

## 8. Failure Event (`failure_events`)
Historical equipment failure incidents and unplanned downtime.

| Field Name | Data Type | Nullable | Key | Constraints / Allowed Values | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `failure_id` | INTEGER | No | PK | Auto-increment sequence | Primary key failure incident ID. |
| `machine_id` | INTEGER | No | FK | References `machines(machine_id)` ON DELETE RESTRICT | Broken down machine foreign key (1:N). |
| `failure_type` | VARCHAR(100) | No | — | `bearing_failure`, `thermal_overload`, `cavitation`, `fatigue_fracture`, `winding_short` | Mechanical or electrical failure mode. |
| `severity` | VARCHAR(20) | No | — | `low`, `medium`, `high`, `critical` | Severity classification. |
| `failure_time` | TIMESTAMPTZ | No | Index | UTC timestamp | Exact timestamp of equipment breakdown. |
| `downtime_minutes` | INTEGER | Yes | — | Positive integer (e.g., 30–1440) | Unplanned production downtime incurred. |
| `description` | TEXT | Yes | — | Free text | Diagnostic findings and root cause notes. |
| `created_at` | TIMESTAMPTZ | No | — | Default: UTC now | Incident logging timestamp. |

---

## 9. Part (`parts`)
Spare components inventory catalog.

| Field Name | Data Type | Nullable | Key | Constraints / Allowed Values | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `part_id` | INTEGER | No | PK | Auto-increment sequence | Primary key part identifier. |
| `part_code` | VARCHAR(50) | No | Unique | Indexed, e.g., `PRT-BRG-01` | SKU or manufacturer part code. |
| `name` | VARCHAR(100) | No | — | Free text | Part item name (e.g., Ball Bearing). |
| `manufacturer` | VARCHAR(100) | Yes | — | E.g., SKF, Timken, Bosch Rexroth | OEM manufacturer. |
| `description` | TEXT | Yes | — | Free text | Technical specifications and dimensions. |
| `created_at` | TIMESTAMPTZ | No | — | Default: UTC now | Catalog entry creation timestamp. |

---

## 10. Technician (`technicians`)
Field maintenance engineers and certified technicians.

| Field Name | Data Type | Nullable | Key | Constraints / Allowed Values | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `technician_id` | INTEGER | No | PK | Auto-increment sequence | Primary key technician identifier. |
| `technician_code` | VARCHAR(50) | No | Unique | Indexed, e.g., `TECH-001` | Employee badge identifier. |
| `name` | VARCHAR(100) | No | — | Full name | Technician display name. |
| `specialization` | VARCHAR(100) | Yes | — | Mechanical, Electrical, Hydraulics, Vibration Analysis, Robotics | Technical domain discipline. |
| `email` | VARCHAR(150) | Yes | Unique | Indexed, valid email format | Notification email address. |
| `is_active` | BOOLEAN | No | — | Default: `TRUE` | Active employment/dispatch status. |
| `created_at` | TIMESTAMPTZ | No | — | Default: UTC now | Onboarding registration timestamp. |

---

## 11. Machine-Parts Bridge Table (`machine_parts`)
Many-to-Many associative bridge mapping machines to compatible spare parts.

| Field Name | Data Type | Nullable | Key | Constraints / Allowed Values | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `machine_id` | INTEGER | No | Composite PK, FK | References `machines(machine_id)` ON DELETE CASCADE | Associated machine identifier. |
| `part_id` | INTEGER | No | Composite PK, FK | References `parts(part_id)` ON DELETE CASCADE, Indexed | Compatible spare part identifier. |
