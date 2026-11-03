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

        for d in [self.csv_dir, self.json_dir, self.sql_dir, self.gt_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def export_all(self) -> Dict[str, Any]:
        """Execute full export."""
        print("[INFO] Starting database exports...")
        results = {}

        # 1. Plants
        plants = [
            {
                "plant_id": p.plant_id,
                "plant_code": p.plant_code,
                "name": p.name,
                "city": p.city,
                "state": p.state,
                "is_active": p.is_active,
                "created_at": p.created_at,
            }
            for p in self.session.query(Plant).order_by(Plant.plant_id).all()
        ]
        self._write_csv_and_json("plants", plants)

        # 2. Production Lines
        lines = [
            {
                "line_id": l.line_id,
                "plant_id": l.plant_id,
                "line_code": l.line_code,
                "name": l.name,
                "is_active": l.is_active,
                "created_at": l.created_at,
            }
            for l in self.session.query(ProductionLine).order_by(ProductionLine.line_id).all()
        ]
        self._write_csv_and_json("production_lines", lines)

        # 3. Machines
        machines = [
            {
                "machine_id": m.machine_id,
                "line_id": m.line_id,
                "machine_code": m.machine_code,
                "name": m.name,
                "machine_type": m.machine_type,
                "manufacturer": m.manufacturer,
                "model_number": m.model_number,
                "installation_date": m.installation_date,
                "is_active": m.is_active,
                "created_at": m.created_at,
            }
            for m in self.session.query(Machine).order_by(Machine.machine_id).all()
        ]
        self._write_csv_and_json("machines", machines)

        # 4. Sensors
        sensors = [
            {
                "sensor_id": s.sensor_id,
                "machine_id": s.machine_id,
                "sensor_code": s.sensor_code,
                "sensor_type": s.sensor_type,
                "unit": s.unit,
                "installation_date": s.installation_date,
                "is_active": s.is_active,
                "created_at": s.created_at,
            }
            for s in self.session.query(Sensor).order_by(Sensor.sensor_id).all()
        ]
        self._write_csv_and_json("sensors", sensors)

        # 5. Operating Shifts
        shifts = [
            {
                "shift_id": sh.shift_id,
                "plant_id": sh.plant_id,
                "shift_name": sh.shift_name,
                "start_time": str(sh.start_time),
                "end_time": str(sh.end_time),
                "created_at": sh.created_at,
            }
            for sh in self.session.query(OperatingShift).order_by(OperatingShift.shift_id).all()
        ]
        self._write_csv_and_json("operating_shifts", shifts)

        # 6. Parts
        parts = [
            {
                "part_id": pt.part_id,
                "part_code": pt.part_code,
                "name": pt.name,
                "manufacturer": pt.manufacturer,
                "description": pt.description,
                "created_at": pt.created_at,
            }
            for pt in self.session.query(Part).order_by(Part.part_id).all()
        ]
        self._write_csv_and_json("parts", parts)

        # 7. Technicians
        techs = [
            {
                "technician_id": tc.technician_id,
                "technician_code": tc.technician_code,
                "name": tc.name,
                "specialization": tc.specialization,
                "email": tc.email,
                "is_active": tc.is_active,
                "created_at": tc.created_at,
            }
            for tc in self.session.query(Technician).order_by(Technician.technician_id).all()
        ]
        self._write_csv_and_json("technicians", techs)

        # 8. Machine Parts Bridge
        bridge_rows = self.session.execute(select(machine_parts)).all()
        bridge = [
            {"machine_id": r[0], "part_id": r[1]}
            for r in bridge_rows
        ]
        self._write_csv_and_json("machine_parts", bridge)

        # 9. Maintenance Work Orders
        work_orders = [
            {
                "work_order_id": w.work_order_id,
                "machine_id": w.machine_id,
                "technician_id": w.technician_id,
                "work_type": w.work_type,
                "priority": w.priority,
                "status": w.status,
                "description": w.description,
                "created_at": w.created_at,
                "completed_at": w.completed_at,
            }
            for w in self.session.query(MaintenanceWorkOrder).order_by(MaintenanceWorkOrder.work_order_id).all()
        ]
        self._write_csv_and_json("maintenance_work_orders", work_orders)

        # 10. Failure Events
        failures = [
            {
                "failure_id": f.failure_id,
                "machine_id": f.machine_id,
                "failure_type": f.failure_type,
                "severity": f.severity,
                "failure_time": f.failure_time,
                "downtime_minutes": f.downtime_minutes,
                "description": f.description,
                "created_at": f.created_at,
            }
            for f in self.session.query(FailureEvent).order_by(FailureEvent.failure_id).all()
        ]
        self._write_csv_and_json("failure_events", failures)

        # 11. Telemetry Sample (first 5,000 events)
        sample_telemetry = [
            {
                "event_id": t.event_id,
                "sensor_id": t.sensor_id,
                "recorded_at": t.recorded_at,
                "value": t.value,
                "quality_status": t.quality_status,
                "created_at": t.created_at,
            }
            for t in self.session.query(TelemetryEvent).order_by(TelemetryEvent.event_id).limit(5000).all()
        ]
        self._write_csv_and_json("telemetry_sample", sample_telemetry)

        # 12. Isolated Ground-Truth Failures with cohort classification (Type A vs Type B)
        # Classify Type A (progressive) vs Type B (sudden)
        m_map = {m["machine_id"]: m["machine_code"] for m in machines}
        gt_failures = []
        for f in failures:
            desc = (f.get("description") or "").lower()
            is_type_a = "degradation" in desc or "progressive" in desc
            cohort = "Type A (Progressive)" if is_type_a else "Type B (Sudden Break)"
            gt_failures.append({
                "failure_id": f["failure_id"],
                "machine_id": f["machine_id"],
                "machine_code": m_map.get(f["machine_id"], f"MCH-{f['machine_id']}"),
                "failure_cohort": cohort,
                "failure_type": f["failure_type"],
                "severity": f["severity"],
                "failure_time": f["failure_time"],
                "downtime_minutes": f["downtime_minutes"],
                "description": f["description"],
            })

        self._write_ground_truth("failures_ground_truth", gt_failures)

        # 13. SQL Seed script
        self._write_sql_seed(plants, lines, machines, sensors, shifts, parts, techs, bridge, work_orders, failures)

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
        }
        print(f"[SUCCESS] Export completed: {results}")
        return results

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
                f.write(f"INSERT INTO plants (plant_id, plant_code, name, city, state, is_active) VALUES ({p['plant_id']}, '{p['plant_code']}', '{p['name']}', '{p['city']}', '{p['state']}', {p['is_active']}) ON CONFLICT (plant_code) DO NOTHING;\n")
            f.write("\n")

            # Lines
            f.write("-- Production Lines (12)\n")
            for l in lines:
                f.write(f"INSERT INTO production_lines (line_id, plant_id, line_code, name, is_active) VALUES ({l['line_id']}, {l['plant_id']}, '{l['line_code']}', '{l['name']}', {l['is_active']}) ON CONFLICT (line_code) DO NOTHING;\n")
            f.write("\n")

            # Machines (100)
            f.write("-- Machines (100)\n")
            for m in machines:
                mfg = f"'{m['manufacturer']}'" if m['manufacturer'] else "NULL"
                mdl = f"'{m['model_number']}'" if m['model_number'] else "NULL"
                f.write(f"INSERT INTO machines (machine_id, line_id, machine_code, name, machine_type, manufacturer, model_number, is_active) VALUES ({m['machine_id']}, {m['line_id']}, '{m['machine_code']}', '{m['name']}', '{m['machine_type']}', {mfg}, {mdl}, {m['is_active']}) ON CONFLICT (machine_code) DO NOTHING;\n")
            f.write("\n")

            # Sensors (500)
            f.write("-- Sensors (500)\n")
            for s in sensors:
                f.write(f"INSERT INTO sensors (sensor_id, machine_id, sensor_code, sensor_type, unit, is_active) VALUES ({s['sensor_id']}, {s['machine_id']}, '{s['sensor_code']}', '{s['sensor_type']}', '{s['unit']}', {s['is_active']}) ON CONFLICT (sensor_code) DO NOTHING;\n")
            f.write("\n")


if __name__ == "__main__":
    db = SessionLocal()
    exporter = DataExporter(session=db, base_dir=Path(__file__).resolve().parent.parent.parent)
    exporter.export_all()
    db.close()
