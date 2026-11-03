"""
Master Data Generator for Industrial Predictive Maintenance System.
Generates reproducible, realistic master data entities across plants, production lines,
operating shifts, technicians, spare parts, machines, sensors, and machine-part mappings.
"""

from datetime import date, datetime, timedelta, timezone
import random
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

try:
    from backend.database import SessionLocal
    from backend.models import (
        Plant,
        ProductionLine,
        Machine,
        Sensor,
        Part,
        machine_parts,
        Technician,
        OperatingShift,
    )
    from backend.generators.master_data_constants import (
        DEFAULT_RANDOM_SEED,
        PLANTS_DATA,
        PRODUCTION_LINES_DATA,
        TECHNICIANS_DATA,
        SPARE_PARTS_DATA,
        MACHINE_TYPES_POOL,
        SENSOR_CONFIGURATIONS,
    )
    from backend.generators.telemetry_math import (
        get_machine_canonical,
        get_sensor_canonical,
    )
except ImportError:
    from database import SessionLocal
    from models import (
        Plant,
        ProductionLine,
        Machine,
        Sensor,
        Part,
        machine_parts,
        Technician,
        OperatingShift,
    )
    from generators.master_data_constants import (
        DEFAULT_RANDOM_SEED,
        PLANTS_DATA,
        PRODUCTION_LINES_DATA,
        TECHNICIANS_DATA,
        SPARE_PARTS_DATA,
        MACHINE_TYPES_POOL,
        SENSOR_CONFIGURATIONS,
    )


class MasterDataGenerator:
    """
    Idempotent and reproducible generator for industrial predictive maintenance master data.
    """

    def __init__(self, seed: int = DEFAULT_RANDOM_SEED, session: Optional[Session] = None):
        """
        Initialize the generator with a deterministic seed and database session.

        :param seed: Integer random seed for reproducible generation.
        :param session: Optional existing SQLAlchemy session. If None, SessionLocal is used.
        """
        self.seed = seed
        self.rng = random.Random(seed)
        self.provided_session = session

    def generate(self, dry_run: bool = False) -> Dict[str, Dict[str, int]]:
        """
        Execute master data generation in a single atomic transaction.
        If any step fails, all changes are rolled back.
        If records already exist, they are reused safely without duplication.

        :param dry_run: If True, execute all logic and constraints, then rollback without committing.
        :return: Dictionary containing created, existing, and total counts for each entity.
        """
        session_created = False
        if self.provided_session is not None:
            session = self.provided_session
        else:
            session = SessionLocal()
            session_created = True

        stats: Dict[str, Dict[str, int]] = {
            "plants": {"created": 0, "existing": 0, "total": 0},
            "production_lines": {"created": 0, "existing": 0, "total": 0},
            "operating_shifts": {"created": 0, "existing": 0, "total": 0},
            "technicians": {"created": 0, "existing": 0, "total": 0},
            "parts": {"created": 0, "existing": 0, "total": 0},
            "machines": {"created": 0, "existing": 0, "total": 0},
            "sensors": {"created": 0, "existing": 0, "total": 0},
            "machine_parts": {"created": 0, "existing": 0, "total": 0},
        }

        try:
            # 1. Plants (3 target)
            plants_map = self._generate_plants(session, stats)

            # 2. Production Lines (12 target, 4 per plant)
            lines_map = self._generate_production_lines(session, plants_map, stats)

            # 3. Operating Shifts (3 per plant, 9 total, crossing midnight)
            self._generate_operating_shifts(session, plants_map, stats)

            # 4. Technicians (20 target)
            self._generate_technicians(session, stats)

            # 5. Spare Parts (50 target)
            parts_map = self._generate_parts(session, stats)

            # 6. Machines (100 target across 12 lines)
            machines_map = self._generate_machines(session, lines_map, stats)

            # 7. Sensors (500 target, exactly 5 per machine)
            self._generate_sensors(session, machines_map, stats)

            # 8. Machine-Part Associations (3 to 6 compatible parts per machine)
            self._generate_machine_parts(session, machines_map, parts_map, stats)

            if dry_run:
                session.rollback()
            else:
                session.commit()
            return stats

        except Exception:
            session.rollback()
            raise
        finally:
            if session_created:
                session.close()

    def _generate_plants(
        self, session: Session, stats: Dict[str, Dict[str, int]]
    ) -> Dict[str, Plant]:
        """Generate or retrieve 3 Indian industrial manufacturing plants."""
        plants_map: Dict[str, Plant] = {}
        for p_data in PLANTS_DATA:
            code = p_data["plant_code"]
            existing = session.query(Plant).filter(
                (Plant.plant_code == code) | (Plant.name == p_data["name"])
            ).first()
            if existing:
                if existing.plant_code != code:
                    existing.plant_code = code
                plants_map[code] = existing
                stats["plants"]["existing"] += 1
            else:
                plant = Plant(
                    plant_code=code,
                    name=p_data["name"],
                    city=p_data["city"],
                    state=p_data["state"],
                    is_active=p_data["is_active"],
                )
                session.add(plant)
                plants_map[code] = plant
                stats["plants"]["created"] += 1

        session.flush()
        stats["plants"]["total"] = len(plants_map)
        return plants_map

    def _generate_production_lines(
        self,
        session: Session,
        plants_map: Dict[str, Plant],
        stats: Dict[str, Dict[str, int]],
    ) -> Dict[str, ProductionLine]:
        """Generate or retrieve 12 production lines (4 per plant)."""
        lines_map: Dict[str, ProductionLine] = {}
        for l_data in PRODUCTION_LINES_DATA:
            code = l_data["line_code"]
            plant = plants_map[l_data["plant_code"]]
            existing = session.query(ProductionLine).filter(
                (ProductionLine.line_code == code) | (ProductionLine.name == l_data["name"])
            ).first()
            if existing:
                if existing.line_code != code:
                    existing.line_code = code
                if existing.plant_id != plant.plant_id:
                    existing.plant_id = plant.plant_id
                lines_map[code] = existing
                stats["production_lines"]["existing"] += 1
            else:
                line = ProductionLine(
                    plant_id=plant.plant_id,
                    line_code=code,
                    name=l_data["name"],
                    is_active=l_data["is_active"],
                )
                session.add(line)
                lines_map[code] = line
                stats["production_lines"]["created"] += 1

        session.flush()
        stats["production_lines"]["total"] = len(lines_map)
        return lines_map

    def _generate_operating_shifts(
        self,
        session: Session,
        plants_map: Dict[str, Plant],
        stats: Dict[str, Dict[str, int]],
    ) -> None:
        """
        Generate 3 operating shifts per plant (Morning, Afternoon, Night).
        Includes night shifts crossing midnight with actual UTC timezone-aware datetimes.
        """
        # Standard Indian industrial shift hours in IST (UTC+05:30)
        ist = timezone(timedelta(hours=5, minutes=30))
        ref_date = datetime(2026, 11, 2, tzinfo=ist)

        shift_definitions = [
            {
                "name": "Morning Shift",
                "start": ref_date.replace(hour=6, minute=0, second=0),
                "end": ref_date.replace(hour=14, minute=0, second=0),
            },
            {
                "name": "Afternoon Shift",
                "start": ref_date.replace(hour=14, minute=0, second=0),
                "end": ref_date.replace(hour=22, minute=0, second=0),
            },
            {
                "name": "Night Shift",  # 22:00 IST on Day 1 to 06:00 IST on Day 2 (crosses midnight)
                "start": ref_date.replace(hour=22, minute=0, second=0),
                "end": (ref_date + timedelta(days=1)).replace(hour=6, minute=0, second=0),
            },
        ]

        total_shifts = 0
        for plant in plants_map.values():
            for s_def in shift_definitions:
                existing = (
                    session.query(OperatingShift)
                    .filter_by(plant_id=plant.plant_id, shift_name=s_def["name"])
                    .first()
                )
                if existing:
                    existing.start_time = s_def["start"]
                    existing.end_time = s_def["end"]
                    stats["operating_shifts"]["existing"] += 1
                else:
                    shift = OperatingShift(
                        plant_id=plant.plant_id,
                        shift_name=s_def["name"],
                        start_time=s_def["start"],
                        end_time=s_def["end"],
                    )
                    session.add(shift)
                    stats["operating_shifts"]["created"] += 1
                total_shifts += 1

        session.flush()
        stats["operating_shifts"]["total"] = total_shifts

    def _generate_technicians(
        self, session: Session, stats: Dict[str, Dict[str, int]]
    ) -> None:
        """Generate or retrieve 20 maintenance technicians with unique codes and emails."""
        for t_data in TECHNICIANS_DATA:
            code = t_data["technician_code"]
            existing = session.query(Technician).filter(
                (Technician.technician_code == code) | (Technician.email == t_data["email"])
            ).first()
            if existing:
                if existing.technician_code != code:
                    existing.technician_code = code
                stats["technicians"]["existing"] += 1
            else:
                tech = Technician(
                    technician_code=code,
                    name=t_data["name"],
                    specialization=t_data["specialization"],
                    email=t_data["email"],
                    is_active=True,
                )
                session.add(tech)
                stats["technicians"]["created"] += 1

        session.flush()
        stats["technicians"]["total"] = len(TECHNICIANS_DATA)

    def _generate_parts(
        self, session: Session, stats: Dict[str, Dict[str, int]]
    ) -> Dict[str, Part]:
        """Generate or retrieve 50 industrial spare parts across key categories."""
        parts_map: Dict[str, Part] = {}
        for p_data in SPARE_PARTS_DATA:
            code = p_data["part_code"]
            existing = session.query(Part).filter(
                (Part.part_code == code) | (Part.name == p_data["name"])
            ).first()
            if existing:
                if existing.part_code != code:
                    existing.part_code = code
                parts_map[code] = existing
                stats["parts"]["existing"] += 1
            else:
                part = Part(
                    part_code=code,
                    name=p_data["name"],
                    manufacturer=p_data["manufacturer"],
                    description=p_data["description"],
                )
                session.add(part)
                parts_map[code] = part
                stats["parts"]["created"] += 1

        session.flush()
        stats["parts"]["total"] = len(parts_map)
        return parts_map

    def _generate_machines(
        self,
        session: Session,
        lines_map: Dict[str, ProductionLine],
        stats: Dict[str, Dict[str, int]],
    ) -> Dict[str, Machine]:
        """
        Generate or retrieve exactly 100 machines distributed across the 12 lines:
        4 lines have 9 machines (36 machines), 8 lines have 8 machines (64 machines).
        Total = 100 machines.
        """
        machines_map: Dict[str, Machine] = {}
        ordered_lines = sorted(lines_map.values(), key=lambda l: l.line_code)

        machine_idx = 1
        base_install_date = date(2022, 1, 15)

        for line_num, line in enumerate(ordered_lines):
            # 4 lines get 9 machines, 8 lines get 8 machines -> total 100
            machines_on_line = 9 if line_num < 4 else 8
            existing_line_machines = (
                session.query(Machine)
                .filter_by(line_id=line.line_id)
                .order_by(Machine.machine_id)
                .all()
            )

            for m_on_line in range(1, machines_on_line + 1):
                code = f"MCH-{line.line_code}-{m_on_line:03d}"
                existing = None
                if len(existing_line_machines) >= m_on_line:
                    existing = existing_line_machines[m_on_line - 1]
                else:
                    existing = session.query(Machine).filter_by(machine_code=code).first()

                if existing:
                    if existing.machine_code != code:
                        existing.machine_code = code
                    machines_map[code] = existing
                    stats["machines"]["existing"] += 1
                else:
                    # Select deterministic machine type and model based on machine index
                    type_template = MACHINE_TYPES_POOL[(machine_idx - 1) % len(MACHINE_TYPES_POOL)]
                    mfr_pair = type_template["manufacturers"][(machine_idx - 1) % len(type_template["manufacturers"])]
                    mfr_name, model_num = mfr_pair

                    # Deterministic staggered installation date within 3-4 years
                    m_num, legacy_m_code = get_machine_canonical(machine_idx, code)
                    m_rng = random.Random(f"{self.seed}_machine_{legacy_m_code}")
                    days_offset = m_rng.randint(0, 1200)
                    install_date = base_install_date + timedelta(days=days_offset)

                    machine = Machine(
                        line_id=line.line_id,
                        machine_code=code,
                        name=f"{type_template['type']} #{machine_idx:03d}",
                        machine_type=type_template["type"],
                        manufacturer=mfr_name,
                        model_number=model_num,
                        installation_date=install_date,
                        is_active=True,
                    )
                    session.add(machine)
                    machines_map[code] = machine
                    stats["machines"]["created"] += 1

                machine_idx += 1

        session.flush()
        stats["machines"]["total"] = len(machines_map)
        return machines_map

    def _generate_sensors(
        self,
        session: Session,
        machines_map: Dict[str, Machine],
        stats: Dict[str, Dict[str, int]],
    ) -> None:
        """
        Generate or retrieve exactly 500 sensors (5 sensors per machine).
        Sensor types: Vibration, Temperature, Acoustic, Pressure, Current.
        """
        ordered_machines = sorted(
            machines_map.values(),
            key=lambda m: (m.line_id, m.machine_code)
        )
        sensor_idx = 1

        for machine in ordered_machines:
            m_install = machine.installation_date or date(2022, 1, 15)
            existing_machine_sensors = (
                session.query(Sensor)
                .filter_by(machine_id=machine.machine_id)
                .all()
            )
            sensor_by_type = {s.sensor_type: s for s in existing_machine_sensors}

            for s_cfg in SENSOR_CONFIGURATIONS:
                code = f"SNS-{machine.machine_code}-{s_cfg['sensor_suffix']}-01"
                existing = sensor_by_type.get(s_cfg["sensor_type"]) or session.query(Sensor).filter_by(sensor_code=code).first()
                if existing:
                    if existing.sensor_code != code:
                        existing.sensor_code = code
                    stats["sensors"]["existing"] += 1
                else:
                    # Sensor installed concurrently or shortly after machine
                    _, legacy_s_code = get_sensor_canonical(0, code)
                    s_rng = random.Random(f"{self.seed}_sensor_{legacy_s_code}")
                    s_offset = s_rng.randint(0, 15)
                    s_install = m_install + timedelta(days=s_offset)

                    sensor = Sensor(
                        machine_id=machine.machine_id,
                        sensor_code=code,
                        sensor_type=s_cfg["sensor_type"],
                        unit=s_cfg["unit"],
                        installation_date=s_install,
                        is_active=True,
                    )
                    session.add(sensor)
                    stats["sensors"]["created"] += 1

                sensor_idx += 1

        session.flush()
        stats["sensors"]["total"] = sensor_idx - 1

    def _generate_machine_parts(
        self,
        session: Session,
        machines_map: Dict[str, Machine],
        parts_map: Dict[str, Part],
        stats: Dict[str, Dict[str, int]],
    ) -> None:
        """
        Associate each machine with 3 to 6 compatible spare parts.
        Queries existing machine_parts associations to maintain complete idempotency.
        """
        # Fetch existing association pairs from database
        existing_pairs_query = select(machine_parts.c.machine_id, machine_parts.c.part_id)
        existing_rows = session.execute(existing_pairs_query).all()
        existing_pairs: Set[Tuple[int, int]] = {(row[0], row[1]) for row in existing_rows}

        ordered_machines = sorted(machines_map.values(), key=lambda m: m.machine_code)
        total_links = 0

        # Build type to compatible codes lookup
        type_to_parts: Dict[str, List[str]] = {
            t["type"]: t["compatible_part_codes"] for t in MACHINE_TYPES_POOL
        }

        for m_idx, machine in enumerate(ordered_machines):
            m_id = machine.machine_id
            compat_codes = type_to_parts.get(machine.machine_type, [])

            # Deterministic RNG per machine ensures identical part associations regardless of execution history
            _, legacy_m_code = get_machine_canonical(machine.machine_id, machine.machine_code)
            m_part_rng = random.Random(f"{self.seed}_machine_parts_{legacy_m_code}")
            k = m_part_rng.randint(3, min(6, len(compat_codes)))
            selected_codes = m_part_rng.sample(compat_codes, k)

            for code in selected_codes:
                part = parts_map.get(code)
                if not part:
                    continue

                pair = (m_id, part.part_id)
                if pair in existing_pairs:
                    stats["machine_parts"]["existing"] += 1
                else:
                    session.execute(
                        machine_parts.insert().values(machine_id=m_id, part_id=part.part_id)
                    )
                    existing_pairs.add(pair)
                    stats["machine_parts"]["created"] += 1

                total_links += 1

        session.flush()
        stats["machine_parts"]["total"] = len(existing_pairs)
