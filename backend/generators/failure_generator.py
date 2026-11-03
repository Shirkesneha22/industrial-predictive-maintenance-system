"""
Deterministic Failure and Maintenance Work Order Generator for Industrial Predictive Maintenance.
Generates exactly 150 failure events (23 Type A progressive degradations + 127 Type B stochastic breakdowns)
and exactly 150 linked corrective maintenance work orders with full transactional rollback,
dry-run capability, strict idempotency, and anti-leakage feature evaluation guards.
"""

from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
import hashlib
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

try:
    from backend.database import SessionLocal
    from backend.models import (
        Machine,
        Sensor,
        Technician,
        FailureEvent,
        MaintenanceWorkOrder,
        TelemetryEvent,
    )
    from backend.generators.telemetry_constants import (
        WINDOW_START_UTC,
        WINDOW_END_UTC,
        SAMPLING_INTERVAL_MINUTES,
        QUALITY_NORMAL,
    )
    from backend.generators.telemetry_math import derive_machine_degradation_profile
    from backend.generators.failure_constants import (
        DEFAULT_FAILURE_SEED,
        TOTAL_FAILURE_COUNT,
        TYPE_A_FAILURE_COUNT,
        TYPE_B_FAILURE_COUNT,
        TOTAL_MACHINES_COUNT,
        ELIGIBLE_TYPE_B_MACHINES_COUNT,
        WORK_TYPE_CORRECTIVE,
        WORK_TYPE_PREVENTIVE,
        STATUS_COMPLETED,
        STATUS_IN_PROGRESS,
        STATUS_PENDING,
        TYPE_A_FAILURE_SPECS,
        TYPE_B_FAILURE_TEMPLATES,
    )
except ImportError:
    from database import SessionLocal
    from models import (
        Machine,
        Sensor,
        Technician,
        FailureEvent,
        MaintenanceWorkOrder,
        TelemetryEvent,
    )
    from generators.telemetry_constants import (
        WINDOW_START_UTC,
        WINDOW_END_UTC,
        SAMPLING_INTERVAL_MINUTES,
        QUALITY_NORMAL,
    )
    from generators.telemetry_math import derive_machine_degradation_profile
    from generators.failure_constants import (
        DEFAULT_FAILURE_SEED,
        TOTAL_FAILURE_COUNT,
        TYPE_A_FAILURE_COUNT,
        TYPE_B_FAILURE_COUNT,
        TOTAL_MACHINES_COUNT,
        ELIGIBLE_TYPE_B_MACHINES_COUNT,
        WORK_TYPE_CORRECTIVE,
        WORK_TYPE_PREVENTIVE,
        STATUS_COMPLETED,
        STATUS_IN_PROGRESS,
        STATUS_PENDING,
        TYPE_A_FAILURE_SPECS,
        TYPE_B_FAILURE_TEMPLATES,
    )


class FailureGenerator:
    """
    Orchestrates deterministic synthetic failure event and maintenance work order generation.
    """

    def __init__(
        self,
        seed: int = DEFAULT_FAILURE_SEED,
        session: Optional[Session] = None,
    ):
        """
        Initialize the generator.

        :param seed: Master integer random seed (default: 20261022).
        :param session: Optional existing SQLAlchemy session. If None, SessionLocal is used.
        """
        self.seed = seed
        self.provided_session = session

    def count_existing_records(self, session: Session) -> Tuple[int, int]:
        """
        Count existing failure events and maintenance work orders in the target 90-day window.
        Returns: (failure_count, work_order_count)
        """
        failures_query = (
            select(func.count())
            .select_from(FailureEvent)
            .where(
                FailureEvent.failure_time >= WINDOW_START_UTC,
                FailureEvent.failure_time <= WINDOW_END_UTC,
            )
        )
        failures_count = session.execute(failures_query).scalar() or 0

        work_orders_query = (
            select(func.count())
            .select_from(MaintenanceWorkOrder)
            .where(
                MaintenanceWorkOrder.created_at >= WINDOW_START_UTC,
                MaintenanceWorkOrder.created_at <= WINDOW_END_UTC,
            )
        )
        work_orders_count = session.execute(work_orders_query).scalar() or 0

        return failures_count, work_orders_count

    def delete_existing_records(self, session: Session) -> Tuple[int, int]:
        """
        Safely delete failure events and maintenance work orders strictly within the 90-day window.
        Never touches telemetry records or master asset tables.
        """
        stmt_wo = text(
            "DELETE FROM maintenance_work_orders "
            "WHERE created_at >= :start_time AND created_at <= :end_time"
        )
        res_wo = session.execute(stmt_wo, {"start_time": WINDOW_START_UTC, "end_time": WINDOW_END_UTC})

        stmt_fe = text(
            "DELETE FROM failure_events "
            "WHERE failure_time >= :start_time AND failure_time <= :end_time"
        )
        res_fe = session.execute(stmt_fe, {"start_time": WINDOW_START_UTC, "end_time": WINDOW_END_UTC})

        return res_fe.rowcount, res_wo.rowcount

    def generate(
        self,
        dry_run: bool = False,
        overwrite: bool = False,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Execute failure events and linked work orders generation in a single atomic database transaction.

        :param dry_run: If True, execute full generation & validation, then rollback.
        :param overwrite: If True, overwrite existing records strictly within the 90-day window.
        :param progress_callback: Optional callback receiving (current_step, total_steps, message).
        :return: Execution summary statistics.
        """
        session_created = False
        if self.provided_session is not None:
            session = self.provided_session
        else:
            session = SessionLocal()
            session_created = True

        start_time = time.time()

        stats: Dict[str, Any] = {
            "master_seed": self.seed,
            "window_start": WINDOW_START_UTC.isoformat(),
            "window_end": WINDOW_END_UTC.isoformat(),
            "dry_run": dry_run,
            "total_failures_generated": 0,
            "type_a_failures": 0,
            "type_b_failures": 0,
            "total_work_orders_generated": 0,
            "work_order_types": {
                WORK_TYPE_CORRECTIVE: 0,
                WORK_TYPE_PREVENTIVE: 0,
            },
            "status_distribution": {
                STATUS_COMPLETED: 0,
                STATUS_IN_PROGRESS: 0,
                STATUS_PENDING: 0,
            },
            "type_b_machine_event_frequencies": {},
            "deleted_previous_failures": 0,
            "deleted_previous_work_orders": 0,
            "duration_seconds": 0.0,
        }

        try:
            # 1. Idempotency Check & Overwrite Protection
            existing_failures, existing_wos = self.count_existing_records(session)
            if existing_failures > 0 or existing_wos > 0:
                if not overwrite:
                    raise RuntimeError(
                        f"Existing failure records detected: {existing_failures} failures and "
                        f"{existing_wos} work orders found in the target 90-day window. "
                        f"Refusing to insert duplicates. Provide '--overwrite' to safely replace them."
                    )
                del_fe, del_wo = self.delete_existing_records(session)
                stats["deleted_previous_failures"] = del_fe
                stats["deleted_previous_work_orders"] = del_wo
                session.flush()

            # 2. Query all active machines and technicians
            machines = session.query(Machine).filter_by(is_active=True).order_by(Machine.machine_id).all()
            if len(machines) != TOTAL_MACHINES_COUNT:
                raise ValueError(
                    f"Expected {TOTAL_MACHINES_COUNT} active machines in database, found {len(machines)}."
                )

            technicians = session.query(Technician).filter_by(is_active=True).order_by(Technician.technician_id).all()
            if not technicians:
                raise ValueError("No active technicians found in database for work order assignment.")

            # Map technicians by specialization for realistic assignment
            techs_by_spec: Dict[str, List[Technician]] = defaultdict(list)
            for tech in technicians:
                techs_by_spec[tech.specialization].append(tech)

            # 3. Classify machines into Type A (degrading) and Type B eligible (non-degrading)
            type_a_machines: List[Tuple[Machine, Dict[str, Any]]] = []
            type_b_eligible: List[Machine] = []

            for m in machines:
                prof = derive_machine_degradation_profile(self.seed, m.machine_id, m.machine_code)
                if prof is not None:
                    type_a_machines.append((m, prof))
                else:
                    type_b_eligible.append(m)

            if len(type_a_machines) != TYPE_A_FAILURE_COUNT:
                raise ValueError(
                    f"Expected {TYPE_A_FAILURE_COUNT} Type A degrading machines, found {len(type_a_machines)}."
                )
            if len(type_b_eligible) != ELIGIBLE_TYPE_B_MACHINES_COUNT:
                raise ValueError(
                    f"Expected {ELIGIBLE_TYPE_B_MACHINES_COUNT} eligible Type B machines, found {len(type_b_eligible)}."
                )

            # Master random generator
            master_rng = np.random.default_rng(self.seed)

            failure_records: List[FailureEvent] = []
            work_order_records: List[MaintenanceWorkOrder] = []

            if progress_callback:
                progress_callback(1, 4, f"Classified assets: {len(type_a_machines)} Type A, {len(type_b_eligible)} Type B eligible")

            # 4. Generate Exactly 23 Type A Failures & Linked Work Orders
            # Each degrading machine experiences exactly 1 failure at the culmination of its degradation curve
            for m, prof in type_a_machines:
                mode = prof["mode"]
                spec = TYPE_A_FAILURE_SPECS[mode]

                end_step = prof["end_step"]
                failure_time = WINDOW_START_UTC + timedelta(minutes=end_step * SAMPLING_INTERVAL_MINUTES)

                # Deterministic machine RNG for realistic downtime variation
                m_hash = hashlib.sha256(f"{self.seed}:type_a:{m.machine_id}:{m.machine_code}".encode()).digest()
                m_rng = np.random.default_rng(int.from_bytes(m_hash[:8], "big"))

                downtime_minutes = int(m_rng.integers(spec["min_downtime_minutes"], spec["max_downtime_minutes"] + 1))
                completed_at = failure_time + timedelta(minutes=downtime_minutes)

                # All 23 Type A failures occur comfortably before WINDOW_END_UTC
                if completed_at <= WINDOW_END_UTC:
                    status = STATUS_COMPLETED
                    wo_completed_at = completed_at
                else:
                    status = STATUS_IN_PROGRESS
                    wo_completed_at = None

                failure_desc = (
                    f"[{m.machine_code}] {spec['description_template']} "
                    f"(Degradation mode: {mode}, Severity rating: {prof['severity']:.2f})"
                )

                fe = FailureEvent(
                    machine_id=m.machine_id,
                    failure_type=spec["failure_type"],
                    severity=spec["severity"],
                    failure_time=failure_time,
                    downtime_minutes=downtime_minutes,
                    description=failure_desc,
                    created_at=failure_time,
                )
                failure_records.append(fe)
                stats["type_a_failures"] += 1

                # Select specialized technician
                matching_techs = techs_by_spec.get(spec["required_specialization"], technicians)
                assigned_tech = matching_techs[int(m_rng.integers(0, len(matching_techs)))]

                wo = MaintenanceWorkOrder(
                    machine_id=m.machine_id,
                    technician_id=assigned_tech.technician_id,
                    work_type=WORK_TYPE_CORRECTIVE,
                    priority=spec["severity"],
                    status=status,
                    description=f"{spec['work_order_description']} Assigned to {assigned_tech.name} ({assigned_tech.specialization}).",
                    created_at=failure_time,
                    completed_at=wo_completed_at,
                )
                work_order_records.append(wo)
                stats["work_order_types"][WORK_TYPE_CORRECTIVE] += 1
                stats["status_distribution"][status] += 1

            if progress_callback:
                progress_callback(2, 4, f"Generated {len(type_a_machines)} Type A progressive degradation failures")

            # 5. Generate Exactly 127 Type B Failures & Linked Work Orders
            # Distributed across the 77 eligible machines only (Type A machines are 100% immune)
            eligible_draws = master_rng.choice(len(type_b_eligible), size=TYPE_B_FAILURE_COUNT)
            draw_counts = Counter(eligible_draws)

            # Record frequency distribution
            freq_counts = Counter(draw_counts[i] for i in range(len(type_b_eligible)))
            stats["type_b_machine_event_frequencies"] = {
                f"{k}_events": v for k, v in sorted(freq_counts.items())
            }

            total_window_minutes = int((WINDOW_END_UTC - WINDOW_START_UTC).total_seconds() / 60)

            for idx, m in enumerate(type_b_eligible):
                num_events = draw_counts[idx]
                if num_events == 0:
                    continue

                # Deterministic RNG for this machine's failure schedule
                m_hash = hashlib.sha256(f"{self.seed}:type_b:{m.machine_id}:{m.machine_code}".encode()).digest()
                m_rng = np.random.default_rng(int.from_bytes(m_hash[:8], "big"))

                # Generate event minutes spaced realistically across the 90 days
                # Ensure no overlapping downtime on the same machine
                raw_minutes = sorted(
                    m_rng.choice(total_window_minutes - 180, size=num_events, replace=False)
                )

                last_event_end = 0
                for rm in raw_minutes:
                    # Maintain minimal physical buffer between consecutive breakdowns on the same machine
                    if rm < last_event_end + 180:
                        rm = min(total_window_minutes - 60, last_event_end + 360)

                    failure_time = WINDOW_START_UTC + timedelta(minutes=int(rm))

                    # Pick realistic failure template
                    tmpl = TYPE_B_FAILURE_TEMPLATES[int(m_rng.integers(0, len(TYPE_B_FAILURE_TEMPLATES)))]
                    downtime = int(m_rng.integers(tmpl["min_downtime"], tmpl["max_downtime"] + 1))
                    last_event_end = rm + downtime

                    completed_time = failure_time + timedelta(minutes=downtime)

                    # Dispatch delay before technician starts wrench time (30 to 90 min)
                    dispatch_delay = int(m_rng.integers(30, 91))
                    dispatch_time = failure_time + timedelta(minutes=dispatch_delay)

                    # Work order status derivation strictly based on point-in-time snapshot at cutoff
                    if completed_time <= WINDOW_END_UTC:
                        status = STATUS_COMPLETED
                        wo_completed_at = completed_time
                    elif dispatch_time <= WINDOW_END_UTC:
                        # Breakdown occurred and repair commenced, but repair not finished by cutoff
                        status = STATUS_IN_PROGRESS
                        wo_completed_at = None  # Strictly NULL
                    else:
                        # Breakdown occurred immediately before cutoff; queued awaiting technician dispatch
                        status = STATUS_PENDING
                        wo_completed_at = None  # Strictly NULL

                    fe_desc = f"[{m.machine_code}] Unplanned stoppage: {tmpl['description']}"
                    fe = FailureEvent(
                        machine_id=m.machine_id,
                        failure_type=tmpl["failure_type"],
                        severity=tmpl["severity"],
                        failure_time=failure_time,
                        downtime_minutes=downtime,
                        description=fe_desc,
                        created_at=failure_time,
                    )
                    failure_records.append(fe)
                    stats["type_b_failures"] += 1

                    # Match technician specialization
                    matching_techs = techs_by_spec.get(tmpl["required_specialization"], technicians)
                    assigned_tech = matching_techs[int(m_rng.integers(0, len(matching_techs)))]

                    wo = MaintenanceWorkOrder(
                        machine_id=m.machine_id,
                        technician_id=assigned_tech.technician_id,
                        work_type=WORK_TYPE_CORRECTIVE,
                        priority=tmpl["severity"],
                        status=status,
                        description=f"{tmpl['work_order_description']} Handled by {assigned_tech.name}.",
                        created_at=failure_time,
                        completed_at=wo_completed_at,
                    )
                    work_order_records.append(wo)
                    stats["work_order_types"][WORK_TYPE_CORRECTIVE] += 1
                    stats["status_distribution"][status] += 1

            if progress_callback:
                progress_callback(3, 4, f"Generated {len(failure_records) - len(type_a_machines)} Type B stochastic failures")

            # 6. Verify Target Volumes and Constraints
            stats["total_failures_generated"] = len(failure_records)
            stats["total_work_orders_generated"] = len(work_order_records)

            if stats["total_failures_generated"] != TOTAL_FAILURE_COUNT:
                raise ValueError(
                    f"Generated {stats['total_failures_generated']} failure events; expected exactly {TOTAL_FAILURE_COUNT}."
                )
            if stats["total_work_orders_generated"] != TOTAL_FAILURE_COUNT:
                raise ValueError(
                    f"Generated {stats['total_work_orders_generated']} work orders; expected exactly {TOTAL_FAILURE_COUNT}."
                )
            if stats["work_order_types"][WORK_TYPE_PREVENTIVE] != 0:
                raise ValueError("Found preventive work orders. Only corrective/emergency work orders are permitted.")

            # 7. Persist to Database within the Atomic Transaction
            session.add_all(failure_records)
            session.add_all(work_order_records)
            session.flush()

            # 8. Transaction Control: Dry-Run vs Commit
            if dry_run:
                session.rollback()
            else:
                session.commit()

            stats["duration_seconds"] = round(time.time() - start_time, 3)

            if progress_callback:
                progress_callback(4, 4, "Generation complete and validated.")

            return stats

        except Exception:
            session.rollback()
            raise
        finally:
            if session_created:
                session.close()


def extract_type_a_evaluation_features(
    session: Session,
    machine_id: int,
    prediction_timestamp: datetime,
    failure_time: datetime,
    lookback_window_hours: int = 168,
) -> Dict[str, Any]:
    """
    Extracts anti-leakage telemetry observations strictly prior to the prediction timestamp
    for evaluating Type A predictive maintenance models.

    Constraints strictly enforced:
    - Never includes the terminal failure reading (at failure_time).
    - Never includes any post-failure or repair readings (after failure_time).
    - Strictly filters observations to:
      `prediction_timestamp - lookback_window <= recorded_at < prediction_timestamp <= failure_time`
    - Evaluates normal quality readings only, excluding synthetic missing or invalid artifacts.

    :param session: SQLAlchemy database session.
    :param machine_id: Primary key identifier of the asset being evaluated.
    :param prediction_timestamp: Point-in-time timestamp at which prediction is evaluated.
    :param failure_time: The verified future failure timestamp.
    :param lookback_window_hours: Window length in hours for feature calculation (default: 168h / 7 days).
    :return: Dictionary containing pre-failure observation statistics and record counts.
    """
    if prediction_timestamp > failure_time:
        raise ValueError(
            f"Prediction timestamp ({prediction_timestamp}) cannot be after failure time ({failure_time})."
        )

    window_start = prediction_timestamp - timedelta(hours=lookback_window_hours)

    # Strictly query telemetry recorded BEFORE the prediction timestamp
    stmt = (
        select(TelemetryEvent.recorded_at, TelemetryEvent.value, Sensor.sensor_type)
        .join(Sensor, TelemetryEvent.sensor_id == Sensor.sensor_id)
        .where(
            Sensor.machine_id == machine_id,
            TelemetryEvent.recorded_at < prediction_timestamp,  # Strict inequality
            TelemetryEvent.recorded_at >= window_start,
            TelemetryEvent.quality_status == QUALITY_NORMAL,
            TelemetryEvent.value.isnot(None),
        )
        .order_by(TelemetryEvent.recorded_at.asc())
    )

    rows = session.execute(stmt).all()

    values_by_type: Dict[str, List[float]] = defaultdict(list)
    max_recorded_at: Optional[datetime] = None

    for rec_at, val, s_type in rows:
        values_by_type[s_type].append(float(val))
        if max_recorded_at is None or rec_at > max_recorded_at:
            max_recorded_at = rec_at

    feature_metrics: Dict[str, Any] = {}
    for s_type, vals in values_by_type.items():
        key_prefix = s_type.lower()
        if vals:
            feature_metrics[f"{key_prefix}_mean"] = round(float(np.mean(vals)), 3)
            feature_metrics[f"{key_prefix}_std"] = round(float(np.std(vals)), 3)
            feature_metrics[f"{key_prefix}_max"] = round(float(np.max(vals)), 3)
            feature_metrics[f"{key_prefix}_min"] = round(float(np.min(vals)), 3)
            feature_metrics[f"{key_prefix}_count"] = len(vals)
        else:
            feature_metrics[f"{key_prefix}_count"] = 0

    return {
        "machine_id": machine_id,
        "prediction_timestamp": prediction_timestamp.isoformat(),
        "failure_time": failure_time.isoformat(),
        "lead_time_hours": round((failure_time - prediction_timestamp).total_seconds() / 3600.0, 2),
        "total_observations_used": len(rows),
        "max_recorded_at": max_recorded_at.isoformat() if max_recorded_at else None,
        "features": feature_metrics,
    }
