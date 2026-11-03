"""
Historical and Real-Time Sensor Telemetry Routes.
Provides endpoints for querying raw and quality-assessed IoT sensor telemetry streams.
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Machine, Sensor, TelemetryEvent
from backend.schemas.risk import (
    TelemetryEventResponse,
    PaginatedTelemetryResponse,
)

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedTelemetryResponse,
    summary="Query Historical Sensor Telemetry",
    description=(
        "Retrieve historical telemetry events with pagination and filtering by machine, "
        "sensor, quality status, and time range. "
        "Adheres to database efficiency limits to prevent memory exhaustion."
    ),
)
@router.get(
    "/history",
    response_model=PaginatedTelemetryResponse,
    include_in_schema=False,
)
def get_historical_telemetry(
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page (max 1000)"),
    machine_id: Optional[int] = Query(None, ge=1, description="Filter by monitored machine ID"),
    sensor_id: Optional[int] = Query(None, ge=1, description="Filter by specific sensor ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by physical sensor type"),
    quality_status: Optional[str] = Query(
        None, description="Filter by quality classification (normal, sensor_fault, invalid, missing)"
    ),
    start_time: Optional[datetime] = Query(None, description="Range start timestamp (inclusive)"),
    end_time: Optional[datetime] = Query(None, description="Range end timestamp (inclusive)"),
    db: Session = Depends(get_db),
):
    """Retrieve paginated historical telemetry records."""
    # Validate timestamp bounds
    if start_time is not None and end_time is not None:
        if start_time > end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_time must be earlier than or equal to end_time",
            )

    # Validate machine existence if filtered
    if machine_id is not None:
        machine = db.query(Machine).filter(Machine.machine_id == machine_id).first()
        if not machine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Machine with id {machine_id} not found",
            )

    # Validate sensor existence if filtered
    if sensor_id is not None:
        sensor = db.query(Sensor).filter(Sensor.sensor_id == sensor_id).first()
        if not sensor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sensor with id {sensor_id} not found",
            )

    # Base query joining TelemetryEvent with Sensor
    base_query = db.query(TelemetryEvent).join(Sensor, TelemetryEvent.sensor_id == Sensor.sensor_id)

    if machine_id is not None:
        base_query = base_query.filter(Sensor.machine_id == machine_id)
    if sensor_id is not None:
        base_query = base_query.filter(TelemetryEvent.sensor_id == sensor_id)
    if sensor_type is not None:
        base_query = base_query.filter(Sensor.sensor_type == sensor_type)
    if quality_status is not None:
        base_query = base_query.filter(TelemetryEvent.quality_status == quality_status)
    if start_time is not None:
        base_query = base_query.filter(TelemetryEvent.recorded_at >= start_time)
    if end_time is not None:
        base_query = base_query.filter(TelemetryEvent.recorded_at <= end_time)

    # Total count calculation
    total = base_query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    # Paginated select with sensor metadata projection
    stmt = (
        select(
            TelemetryEvent.event_id,
            TelemetryEvent.sensor_id,
            Sensor.sensor_code,
            Sensor.sensor_type,
            Sensor.unit,
            TelemetryEvent.recorded_at,
            TelemetryEvent.value,
            TelemetryEvent.quality_status,
        )
        .join(Sensor, TelemetryEvent.sensor_id == Sensor.sensor_id)
    )

    if machine_id is not None:
        stmt = stmt.where(Sensor.machine_id == machine_id)
    if sensor_id is not None:
        stmt = stmt.where(TelemetryEvent.sensor_id == sensor_id)
    if sensor_type is not None:
        stmt = stmt.where(Sensor.sensor_type == sensor_type)
    if quality_status is not None:
        stmt = stmt.where(TelemetryEvent.quality_status == quality_status)
    if start_time is not None:
        stmt = stmt.where(TelemetryEvent.recorded_at >= start_time)
    if end_time is not None:
        stmt = stmt.where(TelemetryEvent.recorded_at <= end_time)

    rows = (
        db.execute(
            stmt.order_by(TelemetryEvent.recorded_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .all()
    )

    items = [
        TelemetryEventResponse(
            event_id=r[0],
            sensor_id=r[1],
            sensor_code=r[2],
            sensor_type=r[3],
            unit=r[4],
            recorded_at=r[5],
            value=r[6],
            quality_status=r[7],
        )
        for r in rows
    ]

    return PaginatedTelemetryResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items,
    )


@router.get(
    "/latest",
    response_model=List[TelemetryEventResponse],
    summary="Get Latest Telemetry Readings",
    description="Retrieve the single most recent telemetry event recorded for each sensor of a machine.",
)
def get_latest_telemetry(
    machine_id: int = Query(..., ge=1, description="Machine ID to fetch latest telemetry for"),
    db: Session = Depends(get_db),
):
    """Fetch latest telemetry reading per sensor mounted on the machine."""
    machine = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine with id {machine_id} not found",
        )

    sensors = (
        db.query(Sensor)
        .filter(Sensor.machine_id == machine_id, Sensor.is_active == True)
        .order_by(Sensor.sensor_id.asc())
        .all()
    )

    results: List[TelemetryEventResponse] = []
    for s in sensors:
        latest_event = (
            db.query(TelemetryEvent)
            .filter(TelemetryEvent.sensor_id == s.sensor_id)
            .order_by(TelemetryEvent.recorded_at.desc())
            .first()
        )
        if latest_event:
            results.append(
                TelemetryEventResponse(
                    event_id=latest_event.event_id,
                    sensor_id=latest_event.sensor_id,
                    sensor_code=s.sensor_code,
                    sensor_type=s.sensor_type,
                    unit=s.unit,
                    recorded_at=latest_event.recorded_at,
                    value=latest_event.value,
                    quality_status=latest_event.quality_status,
                )
            )

    return results


@router.get(
    "/machines/{machine_id}",
    response_model=PaginatedTelemetryResponse,
    summary="Get Machine Telemetry Stream",
    description="Direct endpoint to query historical telemetry for a specific machine.",
)
def get_machine_telemetry(
    machine_id: int = Path(..., ge=1, description="Machine primary key identifier"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    sensor_type: Optional[str] = Query(None, description="Filter by physical sensor type"),
    quality_status: Optional[str] = Query(None, description="Filter by quality classification"),
    start_time: Optional[datetime] = Query(None, description="Start timestamp cutoff"),
    end_time: Optional[datetime] = Query(None, description="End timestamp cutoff"),
    db: Session = Depends(get_db),
):
    """Retrieve telemetry events for a specific machine."""
    return get_historical_telemetry(
        page=page,
        page_size=page_size,
        machine_id=machine_id,
        sensor_id=None,
        sensor_type=sensor_type,
        quality_status=quality_status,
        start_time=start_time,
        end_time=end_time,
        db=db,
    )
