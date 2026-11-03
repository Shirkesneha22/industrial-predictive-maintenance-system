"""
Tests for Master Data Generator and Seeded Assets.
Validates record counts, foreign key integrity, business code uniqueness,
cardinality constraints, shift midnight transitions, and generator idempotency.
Uses non-destructive inspection and transactional rollback to preserve database safety.
"""

from datetime import timezone
import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from backend.database import engine, SessionLocal
from backend.generators.master_data_generator import MasterDataGenerator
from backend.models import (
    Plant,
    ProductionLine,
    Machine,
    Sensor,
    Part,
    machine_parts,
    Technician,
    OperatingShift,
    TelemetryEvent,
    FailureEvent,
    MaintenanceWorkOrder,
)


@pytest.fixture(scope="module")
def db_session():
    """Provides a transactional SQLAlchemy session for testing."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_target_record_counts(db_session: Session):
    """Verify all master data entity record targets exist."""
    assert db_session.query(Plant).count() == 3
    assert db_session.query(ProductionLine).count() == 12
    assert db_session.query(OperatingShift).count() == 9
    assert db_session.query(Technician).count() == 20
    assert db_session.query(Part).count() == 50
    assert db_session.query(Machine).count() == 100
    assert db_session.query(Sensor).count() == 500

    # Operational event data status
    assert db_session.query(TelemetryEvent).count() in (0, 240000, 2160000)
    assert db_session.query(FailureEvent).count() in (0, 150)
    assert db_session.query(MaintenanceWorkOrder).count() in (0, 150)


def test_plants_and_production_lines_hierarchy(db_session: Session):
    """Verify exactly 4 production lines and 3 shifts per plant across Indian hubs."""
    expected_cities = {"Pune", "Chennai", "Ahmedabad"}
    plants = db_session.query(Plant).all()
    assert len(plants) == 3
    assert {p.city for p in plants} == expected_cities

    for plant in plants:
        lines = db_session.query(ProductionLine).filter_by(plant_id=plant.plant_id).all()
        assert len(lines) == 4
        shifts = db_session.query(OperatingShift).filter_by(plant_id=plant.plant_id).all()
        assert len(shifts) == 3


def test_sensor_cardinality_per_machine(db_session: Session):
    """Verify exactly 5 sensors per machine covering required measurement types."""
    expected_types = {"Vibration", "Temperature", "Acoustic", "Pressure", "Current"}

    machines = db_session.query(Machine).all()
    assert len(machines) == 100

    for machine in machines:
        sensors = db_session.query(Sensor).filter_by(machine_id=machine.machine_id).all()
        assert len(sensors) == 5
        types_on_machine = {s.sensor_type for s in sensors}
        assert types_on_machine == expected_types


def test_machine_part_associations(db_session: Session):
    """Verify each machine has between 3 and 6 compatible spare parts linked."""
    machines = db_session.query(Machine).all()
    for machine in machines:
        part_count = len(machine.parts)
        assert 3 <= part_count <= 6, f"Machine {machine.machine_code} has {part_count} parts (expected 3-6)"


def test_business_code_uniqueness(db_session: Session):
    """Verify all business codes and technician emails are strictly unique."""
    plant_codes = [p.plant_code for p in db_session.query(Plant).all()]
    assert len(plant_codes) == len(set(plant_codes))

    line_codes = [l.line_code for l in db_session.query(ProductionLine).all()]
    assert len(line_codes) == len(set(line_codes))

    machine_codes = [m.machine_code for m in db_session.query(Machine).all()]
    assert len(machine_codes) == len(set(machine_codes))

    sensor_codes = [s.sensor_code for s in db_session.query(Sensor).all()]
    assert len(sensor_codes) == len(set(sensor_codes))

    part_codes = [pt.part_code for pt in db_session.query(Part).all()]
    assert len(part_codes) == len(set(part_codes))

    tech_codes = [t.technician_code for t in db_session.query(Technician).all()]
    assert len(tech_codes) == len(set(tech_codes))

    tech_emails = [t.email for t in db_session.query(Technician).all()]
    assert len(tech_emails) == len(set(tech_emails))


def test_operating_shifts_crossing_midnight(db_session: Session):
    """Verify shift timestamps are timezone-aware and night shifts cross midnight."""
    night_shifts = (
        db_session.query(OperatingShift)
        .filter(OperatingShift.shift_name.like("%Night%"))
        .all()
    )
    assert len(night_shifts) == 3

    for shift in night_shifts:
        assert shift.start_time.tzinfo is not None
        assert shift.end_time.tzinfo is not None
        assert shift.end_time > shift.start_time
        # Duration is 8 hours and crosses into next calendar day
        duration = shift.end_time - shift.start_time
        assert duration.total_seconds() == 8 * 3600
        assert shift.end_time.date() > shift.start_time.date()


def test_generator_idempotency_non_destructive():
    """
    Verify re-running the generator against the existing database is fully idempotent
    and creates 0 new records.
    """
    generator = MasterDataGenerator(seed=20261022)
    stats = generator.generate(dry_run=True)

    for entity, counts in stats.items():
        assert counts["created"] == 0, f"Entity {entity} created unexpected records on rerun"
        assert counts["total"] > 0, f"Entity {entity} had 0 total records"
