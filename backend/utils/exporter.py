"""
Data Export Utility for Industrial Predictive Maintenance System.

Exports PostgreSQL database entities into:
- CSV files (data/exports/csv/)
- JSON files (data/exports/json/)
- SQL Seed script (data/exports/sql/)
- Ground truth failure files strictly isolated (data/ground_truth/)
"""

import csv
import json
import os
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Any, List, Dict
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from dataclasses import asdict
from backend.generators.anomaly_injector import generate_anomalies
from backend.models import (
    Plant,
    ProductionLine,
    Machine,
    Sensor,
    TelemetryEvent,
    OperatingShift,
    MaintenanceWorkOrder,
    FailureEvent,
    Part,
    Technician,
    machine_parts,
)


def json_serial(obj: Any) -> Any:
    """JSON serializer for date/datetime objects."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class DataExporter:
    """Exports all entities to CSV, JSON, SQL, and separate Ground Truth files."""

    def __init__(self, session: Session, base_dir: Path):
        self.session = session
        self.base_dir = base_dir
        self.csv_dir = base_dir / "data" / "exports" / "csv"
        self.json_dir = base_dir / "data" / "exports" / "json"
        self.sql_dir = base_dir / "data" / "exports" / "sql"
        self.gt_dir = base_dir / "data" / "ground_truth"
        self.anom_csv_dir = self.csv_dir / "anomalies"
        self.anom_json_dir = self.json_dir / "anomalies"

        for d in [self.csv_dir, self.json_dir, self.sql_dir, self.gt_dir, self.anom_csv_dir, self.anom_json_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def export_all(self) -> Dict[str, Any]:
        """Execute full export using spec-compliant hierarchical business IDs across all files."""
        print("[INFO] Starting database exports...")
        results = {}

        # 0. Fetch raw DB entities
        plants_db = self.session.query(Plant).order_by(Plant.plant_id).all()
        lines_db = self.session.query(ProductionLine).order_by(ProductionLine.line_id).all()
        machines_db = self.session.query(Machine).order_by(Machine.machine_id).all()
        sensors_db = self.session.query(Sensor).order_by(Sensor.sensor_id).all()
        shifts_db = self.session.query(OperatingShift).order_by(OperatingShift.shift_id).all()
        parts_db = self.session.query(Part).order_by(Part.part_id).all()
        techs_db = self.session.query(Technician).order_by(Technician.technician_id).all()

        # Build primary ID maps to string business codes
        plant_map = {p.plant_id: p.plant_code for p in plants_db}
        line_map = {l.line_id: l.line_code for l in lines_db}
        machine_map = {m.machine_id: m.machine_code for m in machines_db}
        sensor_map = {s.sensor_id: s.sensor_code for s in sensors_db}
        part_map = {pt.part_id: pt.part_code for pt in parts_db}
        tech_map = {tc.technician_id: tc.technician_code for tc in techs_db}

        # 1. Plants (PLT-001)
        plants = [
            {
                "plant_id": p.plant_code,
                "plant_code": p.plant_code,
                "name": p.name,
                "city": p.city,
                "state": p.state,
                "is_active": p.is_active,
                "created_at": p.created_at,
            }
            for p in plants_db
        ]
        self._write_csv_and_json("plants", plants)

        # 2. Production Lines (LINE-PLT-001-001)
        lines = [
            {
                "line_id": l.line_code,
                "plant_id": plant_map.get(l.plant_id, f"PLT-{l.plant_id:03d}"),
                "line_code": l.line_code,
                "name": l.name,
                "is_active": l.is_active,
                "created_at": l.created_at,
            }
            for l in lines_db
        ]
        self._write_csv_and_json("production_lines", lines)

        # 3. Machines (MCH-LINE-PLT-001-001-001)
        machines = [
            {
                "machine_id": m.machine_code,
                "line_id": line_map.get(m.line_id, f"LINE-{m.line_id:03d}"),
                "machine_code": m.machine_code,
                "name": m.name,
                "machine_type": m.machine_type,
                "manufacturer": m.manufacturer,
                "model_number": m.model_number,
                "installation_date": m.installation_date,
                "is_active": m.is_active,
                "created_at": m.created_at,
            }
            for m in machines_db
        ]
        self._write_csv_and_json("machines", machines)

        # 4. Sensors (SNS-MCH-LINE-PLT-001-001-001-TEMP-01)
        sensors = [
            {
                "sensor_id": s.sensor_code,
                "machine_id": machine_map.get(s.machine_id, f"MCH-{s.machine_id:03d}"),
                "sensor_code": s.sensor_code,
                "sensor_type": s.sensor_type,
                "unit": s.unit,
                "installation_date": s.installation_date,
                "is_active": s.is_active,
                "created_at": s.created_at,
            }
            for s in sensors_db
        ]
        self._write_csv_and_json("sensors", sensors)

        # 5. Operating Shifts (SHF-PLT-001-01)
        shift_suffix_map = {"Morning Shift": "01", "Afternoon Shift": "02", "Night Shift": "03"}
        shifts = []
        for sh in shifts_db:
            p_code = plant_map.get(sh.plant_id, f"PLT-{sh.plant_id:03d}")
            s_suf = shift_suffix_map.get(sh.shift_name, f"{sh.shift_id:02d}")
            shifts.append({
                "shift_id": f"SHF-{p_code}-{s_suf}",
                "plant_id": p_code,
                "shift_name": sh.shift_name,
                "start_time": str(sh.start_time),
                "end_time": str(sh.end_time),
                "created_at": sh.created_at,
            })
        self._write_csv_and_json("operating_shifts", shifts)

        # 6. Parts (PRT-0001)
        parts = [
            {
                "part_id": pt.part_code,
                "part_code": pt.part_code,
                "name": pt.name,
                "manufacturer": pt.manufacturer,
                "description": pt.description,
                "created_at": pt.created_at,
            }
            for pt in parts_db
        ]
        self._write_csv_and_json("parts", parts)

        # 7. Technicians (TECH-0001)
        techs = [
            {
                "technician_id": tc.technician_code,
                "technician_code": tc.technician_code,
                "name": tc.name,
                "specialization": tc.specialization,
                "email": tc.email,
                "is_active": tc.is_active,
                "created_at": tc.created_at,
            }
            for tc in techs_db
        ]
        self._write_csv_and_json("technicians", techs)

        # 8. Machine Parts Bridge (machine_id, part_id string keys)
        bridge_rows = self.session.execute(select(machine_parts)).all()
        bridge = [
            {
                "machine_id": machine_map.get(r[0], f"MCH-{r[0]:03d}"),
                "part_id": part_map.get(r[1], f"PRT-{r[1]:04d}"),
            }
            for r in bridge_rows
        ]
        self._write_csv_and_json("machine_parts", bridge)

        # 9. Maintenance Work Orders (WO-2026-000001)
        work_orders_db = self.session.query(MaintenanceWorkOrder).order_by(MaintenanceWorkOrder.work_order_id).all()
        work_orders = [
            {
                "work_order_id": f"WO-{w.created_at.year if w.created_at else 2026}-{idx:06d}",
                "machine_id": machine_map.get(w.machine_id, f"MCH-{w.machine_id:03d}"),
                "technician_id": tech_map.get(w.technician_id, "") if w.technician_id else "",
                "work_type": w.work_type,
                "priority": w.priority,
                "status": w.status,
                "description": w.description,
                "created_at": w.created_at,
                "completed_at": w.completed_at,
            }
            for idx, w in enumerate(work_orders_db, start=1)
        ]
        self._write_csv_and_json("maintenance_work_orders", work_orders)

        # 10. Failure Events (FAIL-2026-000001)
        failures_db = self.session.query(FailureEvent).order_by(FailureEvent.failure_id).all()
        failures = [
            {
                "failure_id": f"FAIL-{f.failure_time.year if f.failure_time else 2026}-{idx:06d}",
                "machine_id": machine_map.get(f.machine_id, f"MCH-{f.machine_id:03d}"),
                "failure_type": f.failure_type,
                "severity": f.severity,
                "failure_time": f.failure_time,
                "downtime_minutes": f.downtime_minutes,
                "description": f.description,
                "created_at": f.created_at,
            }
            for idx, f in enumerate(failures_db, start=1)
        ]
        self._write_csv_and_json("failure_events", failures)

        # 11. Telemetry Sample (TEL-SNS-...-timestamp)
        telemetry_db = self.session.query(TelemetryEvent).order_by(TelemetryEvent.event_id).limit(5000).all()
        sample_telemetry = [
            {
                "event_id": f"TEL-{sensor_map.get(t.sensor_id, f'SNS-{t.sensor_id:04d}')}-{t.recorded_at.strftime('%Y%m%dT%H%M%SZ')}",
                "sensor_id": sensor_map.get(t.sensor_id, f"SNS-{t.sensor_id:04d}"),
                "recorded_at": t.recorded_at,
                "value": t.value,
                "quality_status": t.quality_status,
                "created_at": t.created_at,
            }
            for t in telemetry_db
        ]
        self._write_csv_and_json("telemetry_sample", sample_telemetry)

        # 12. Isolated Ground-Truth Failures with cohort classification (Type A vs Type B)
        gt_failures = []
        for f in failures:
            desc = (f.get("description") or "").lower()
            is_type_a = "degradation" in desc or "progressive" in desc
            cohort = "Type A (Progressive)" if is_type_a else "Type B (Sudden Break)"
            gt_failures.append({
                "failure_id": f["failure_id"],
                "machine_id": f["machine_id"],
                "machine_code": f["machine_id"],
                "failure_cohort": cohort,
                "failure_type": f["failure_type"],
                "severity": f["severity"],
                "failure_time": f["failure_time"],
                "downtime_minutes": f["downtime_minutes"],
                "description": f["description"],
            })

        self._write_ground_truth("failures_ground_truth", gt_failures)

        # 13. SQL Seed script
        self._write_sql_seed(plants_db, lines_db, machines_db, sensors_db, shifts_db, parts_db, techs_db, bridge_rows, work_orders_db, failures_db)

        # 14. Deterministic Edge-Case Anomalies & Ground Truth Catalog (Phase 3)
        gt_anomalies, anomaly_rows = generate_anomalies(seed=20261022)
        gt_dict_list = [asdict(a) for a in gt_anomalies]
        self._write_ground_truth("ground_truth", gt_dict_list)

        for entity_name, rows in anomaly_rows.items():
            self._write_anomaly_csv_and_json(entity_name, rows)

        self._write_anomaly_sql_seed(anomaly_rows)

        results = {
            "plants": len(plants),
            "production_lines": len(lines),
            "machines": len(machines),
            "sensors": len(sensors),
            "operating_shifts": len(shifts),
            "parts": len(parts),
            "technicians": len(techs),
            "machine_parts": len(bridge),
            "maintenance_work_orders": len(work_orders),
            "failure_events": len(failures),
            "telemetry_sample_rows": len(sample_telemetry),
            "ground_truth_records": len(gt_failures),
            "injected_anomalies": len(gt_dict_list),
        }
        print(f"[SUCCESS] Export completed: {results}")
        return results

    def _write_anomaly_csv_and_json(self, name: str, data: List[Dict[str, Any]]) -> None:
        if not data:
            return

        # CSV in anomalies/
        csv_path = self.anom_csv_dir / f"{name}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            writer.writeheader()
            for row in data:
                formatted_row = {
                    k: (v.isoformat() if isinstance(v, (datetime, date)) else v)
                    for k, v in row.items()
                }
                writer.writerow(formatted_row)

        # JSON in anomalies/
        json_path = self.anom_json_dir / f"{name}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, default=json_serial, indent=2)

    def _write_anomaly_sql_seed(self, anomaly_rows: Dict[str, List[Dict[str, Any]]]) -> None:
        sql_path = self.sql_dir / "seed_anomalies.sql"
        with open(sql_path, "w", encoding="utf-8") as f:
            f.write("-- Deliberate Edge-Case Anomalies for Data Quality Validation\n\n")
            # Telemetry
            f.write("-- Telemetry Anomalies (30 rows)\n")
            for t in anomaly_rows.get("telemetry_events", []):
                val_str = "NULL" if t["value"] is None else str(t["value"])
                f.write(f"-- Anomaly: {t.get('anomaly_id')}\n")
                f.write(f"INSERT INTO telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) VALUES ((SELECT sensor_id FROM sensors WHERE sensor_code='{t['sensor_id']}'), '{t['recorded_at']}', {val_str}, '{t['quality_status']}', NOW()) ON CONFLICT DO NOTHING;\n")
            f.write("\n")

    def _write_csv_and_json(self, name: str, data: List[Dict[str, Any]]) -> None:
        if not data:
            return

        # CSV
        csv_path = self.csv_dir / f"{name}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            writer.writeheader()
            for row in data:
                formatted_row = {
                    k: (v.isoformat() if isinstance(v, (datetime, date)) else v)
                    for k, v in row.items()
                }
                writer.writerow(formatted_row)

        # JSON
        json_path = self.json_dir / f"{name}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, default=json_serial, indent=2)

    def _write_ground_truth(self, name: str, data: List[Dict[str, Any]]) -> None:
        # Ground truth CSV
        csv_path = self.gt_dir / f"{name}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            writer.writeheader()
            for row in data:
                formatted_row = {
                    k: (v.isoformat() if isinstance(v, (datetime, date)) else v)
                    for k, v in row.items()
                }
                writer.writerow(formatted_row)

        # Ground truth JSON
        json_path = self.gt_dir / f"{name}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, default=json_serial, indent=2)

    def _write_sql_seed(
        self, plants, lines, machines, sensors, shifts, parts, techs, bridge, work_orders, failures
    ) -> None:
        sql_path = self.sql_dir / "seed_master_and_events.sql"
        with open(sql_path, "w", encoding="utf-8") as f:
            f.write("-- Industrial Predictive Maintenance System\n")
            f.write(f"-- Deterministic Master Data & Event Seeds (Exported {datetime.now(timezone.utc).isoformat()})\n\n")

            # Plants
            f.write("-- Plants (3)\n")
            for p in plants:
                f.write(f"INSERT INTO plants (plant_id, plant_code, name, city, state, is_active) VALUES ({p.plant_id}, '{p.plant_code}', '{p.name}', '{p.city}', '{p.state}', {p.is_active}) ON CONFLICT (plant_code) DO NOTHING;\n")
            f.write("\n")

            # Lines
            f.write("-- Production Lines (12)\n")
            for l in lines:
                f.write(f"INSERT INTO production_lines (line_id, plant_id, line_code, name, is_active) VALUES ({l.line_id}, {l.plant_id}, '{l.line_code}', '{l.name}', {l.is_active}) ON CONFLICT (line_code) DO NOTHING;\n")
            f.write("\n")

            # Machines (100)
            f.write("-- Machines (100)\n")
            for m in machines:
                mfg = f"'{m.manufacturer}'" if m.manufacturer else "NULL"
                mdl = f"'{m.model_number}'" if m.model_number else "NULL"
                f.write(f"INSERT INTO machines (machine_id, line_id, machine_code, name, machine_type, manufacturer, model_number, is_active) VALUES ({m.machine_id}, {m.line_id}, '{m.machine_code}', '{m.name}', '{m.machine_type}', {mfg}, {mdl}, {m.is_active}) ON CONFLICT (machine_code) DO NOTHING;\n")
            f.write("\n")

            # Sensors (500)
            f.write("-- Sensors (500)\n")
            for s in sensors:
                f.write(f"INSERT INTO sensors (sensor_id, machine_id, sensor_code, sensor_type, unit, is_active) VALUES ({s.sensor_id}, {s.machine_id}, '{s.sensor_code}', '{s.sensor_type}', '{s.unit}', {s.is_active}) ON CONFLICT (sensor_code) DO NOTHING;\n")
            f.write("\n")


if __name__ == "__main__":
    db = SessionLocal()
    exporter = DataExporter(session=db, base_dir=Path(__file__).resolve().parent.parent.parent)
    exporter.export_all()
    db.close()
