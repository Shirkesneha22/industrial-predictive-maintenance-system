"""
High-Performance Synthetic Telemetry Generator for Industrial Predictive Maintenance.
Features chunked PostgreSQL COPY streaming, atomic single-transaction execution,
SHA-256 deterministic seeding, and strict idempotency with overwrite protection.
"""

from datetime import datetime, timezone
import io
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

try:
    from backend.database import SessionLocal, engine
    from backend.models import Sensor, Machine, TelemetryEvent
    from backend.generators.telemetry_constants import (
        DEFAULT_TELEMETRY_SEED,
        WINDOW_START_UTC,
        WINDOW_END_UTC,
        READINGS_PER_SENSOR,
        TARGET_SENSOR_COUNT,
        TOTAL_TELEMETRY_RECORDS,
        STEPS_PER_CHUNK,
        TOTAL_CHUNKS,
        QUALITY_NORMAL,
        QUALITY_SENSOR_FAULT,
        QUALITY_INVALID,
        QUALITY_MISSING,
    )
    from backend.generators.telemetry_math import generate_sensor_chunk_readings
except ImportError:
    from database import SessionLocal, engine
    from models import Sensor, Machine, TelemetryEvent
    from generators.telemetry_constants import (
        DEFAULT_TELEMETRY_SEED,
        WINDOW_START_UTC,
        WINDOW_END_UTC,
        READINGS_PER_SENSOR,
        TARGET_SENSOR_COUNT,
        TOTAL_TELEMETRY_RECORDS,
        STEPS_PER_CHUNK,
        TOTAL_CHUNKS,
        QUALITY_NORMAL,
        QUALITY_SENSOR_FAULT,
        QUALITY_INVALID,
        QUALITY_MISSING,
    )
    from generators.telemetry_math import generate_sensor_chunk_readings


class TelemetryGenerator:
    """
    Orchestrates high-volume synthetic telemetry streaming with PostgreSQL COPY ingestion.
    """

    def __init__(
        self,
        seed: int = DEFAULT_TELEMETRY_SEED,
        session: Optional[Session] = None,
    ):
        """
        Initialize the generator.

        :param seed: Master integer random seed.
        :param session: Optional existing SQLAlchemy session. If None, SessionLocal is used.
        """
        self.seed = seed
        self.provided_session = session

    def count_existing_window_records(self, session: Session) -> int:
        """
        Count existing records within the target 90-day time window.
        """
        query = (
            select(func.count())
            .select_from(TelemetryEvent)
            .where(
                TelemetryEvent.recorded_at >= WINDOW_START_UTC,
                TelemetryEvent.recorded_at < WINDOW_END_UTC,
            )
        )
        return session.execute(query).scalar() or 0

    def delete_window_records(self, session: Session) -> int:
        """
        Safely delete records strictly within the target 90-day time window.
        Never truncates tables or deletes data outside this window.
        """
        stmt = text(
            "DELETE FROM telemetry_events WHERE recorded_at >= :start_time AND recorded_at < :end_time"
        )
        result = session.execute(
            stmt,
            {"start_time": WINDOW_START_UTC, "end_time": WINDOW_END_UTC},
        )
        return result.rowcount

    def generate(
        self,
        dry_run: bool = False,
        overwrite: bool = False,
        max_chunks: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Execute telemetry generation in a single atomic database transaction.

        :param dry_run: If True, execute full generation & COPY, validate results, then rollback.
        :param overwrite: If True, overwrite existing records strictly within the 90-day window.
        :param max_chunks: Optional integer to limit the number of chunks processed (useful for testing).
        :param progress_callback: Optional callback receiving (current_chunk, total_chunks, message).
        :return: Execution summary statistics.
        """
        session_created = False
        if self.provided_session is not None:
            session = self.provided_session
        else:
            session = SessionLocal()
            session_created = True

        stats: Dict[str, Any] = {
            "window_start": WINDOW_START_UTC.isoformat(),
            "window_end": WINDOW_END_UTC.isoformat(),
            "target_sensors": TARGET_SENSOR_COUNT,
            "readings_per_sensor": READINGS_PER_SENSOR,
            "total_records_inserted": 0,
            "deleted_previous_records": 0,
            "quality_distribution": {
                QUALITY_NORMAL: 0,
                QUALITY_SENSOR_FAULT: 0,
                QUALITY_INVALID: 0,
                QUALITY_MISSING: 0,
            },
            "duration_seconds": 0.0,
            "dry_run": dry_run,
        }

        start_time = time.time()

        try:
            # 1. Idempotency Check
            existing_count = self.count_existing_window_records(session)
            if existing_count > 0:
                if not overwrite:
                    raise RuntimeError(
                        f"Existing telemetry data detected: {existing_count} records found in the "
                        f"target 90-day window ({WINDOW_START_UTC.date()} to {WINDOW_END_UTC.date()}). "
                        f"Refusing to insert duplicates. Provide '--overwrite' to safely replace them."
                    )
                # Overwrite is explicitly permitted
                deleted = self.delete_window_records(session)
                stats["deleted_previous_records"] = deleted
                session.flush()

            # 2. Query all active sensors with machine details
            sensors_query = (
                select(
                    Sensor.sensor_id,
                    Sensor.sensor_code,
                    Sensor.sensor_type,
                    Machine.machine_id,
                    Machine.machine_code,
                )
                .join(Machine, Sensor.machine_id == Machine.machine_id)
                .order_by(Sensor.sensor_id)
            )
            sensors_list = session.execute(sensors_query).all()

            if len(sensors_list) != TARGET_SENSOR_COUNT:
                raise ValueError(
                    f"Expected {TARGET_SENSOR_COUNT} sensors in database, but found {len(sensors_list)}."
                )

            # Get raw connection for high-throughput psycopg2 COPY
            # In SQLAlchemy 2.0, connection.connection.dbapi_connection gives the underlying DBAPI connection
            raw_connection = session.connection().connection.dbapi_connection
            raw_cursor = raw_connection.cursor()

            copy_sql = (
                "COPY telemetry_events (sensor_id, recorded_at, value, quality_status, created_at) "
                "FROM STDIN WITH (FORMAT text, DELIMITER '\t', NULL '\\N')"
            )

            total_inserted = 0
            chunks_to_run = TOTAL_CHUNKS if max_chunks is None else min(TOTAL_CHUNKS, max_chunks)

            # 3. Stream generation in temporal chunks (9 chunks of 10 days = 480 steps)
            for chunk_idx in range(chunks_to_run):
                chunk_start_step = chunk_idx * STEPS_PER_CHUNK
                chunk_steps = min(STEPS_PER_CHUNK, READINGS_PER_SENSOR - chunk_start_step)

                # In-memory buffer for TSV rows
                buffer = io.StringIO()

                for sensor_row in sensors_list:
                    s_id, s_code, s_type, m_id, m_code = sensor_row

                    readings = generate_sensor_chunk_readings(
                        sensor_id=s_id,
                        sensor_code=s_code,
                        sensor_type=s_type,
                        machine_id=m_id,
                        machine_code=m_code,
                        chunk_start_step=chunk_start_step,
                        chunk_num_steps=chunk_steps,
                        master_seed=self.seed,
                    )

                    for rec in readings:
                        rec_s_id, rec_time, rec_val, rec_q, rec_created = rec
                        # Track quality stats
                        stats["quality_distribution"][rec_q] += 1

                        val_str = r"\N" if rec_val is None else f"{rec_val:.4f}"
                        time_str = rec_time.strftime("%Y-%m-%d %H:%M:%S%z")
                        created_str = rec_created.strftime("%Y-%m-%d %H:%M:%S%z")

                        # Write tab-separated row
                        buffer.write(f"{rec_s_id}\t{time_str}\t{val_str}\t{rec_q}\t{created_str}\n")
                        total_inserted += 1

                # Execute fast COPY for this chunk buffer
                buffer.seek(0)
                raw_cursor.copy_expert(copy_sql, buffer)
                buffer.close()

                if progress_callback:
                    progress_callback(
                        chunk_idx + 1,
                        TOTAL_CHUNKS,
                        f"Chunk {chunk_idx + 1}/{TOTAL_CHUNKS} ingested ({total_inserted:,} rows)",
                    )

            stats["total_records_inserted"] = total_inserted

            # 4. Final Transaction Control
            if dry_run:
                session.rollback()
            else:
                session.commit()

            stats["duration_seconds"] = round(time.time() - start_time, 2)
            return stats

        except Exception:
            session.rollback()
            raise
        finally:
            if session_created:
                session.close()
