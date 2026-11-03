"""
Machine Management and Health/Risk Assessment Routes.
Provides endpoints for querying machines, sensor configurations, and point-in-time asset risk evaluations.
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session, selectinload

from backend.database import get_db
from backend.models import Machine, Sensor, MaintenanceWorkOrder, FailureEvent
from backend.generators.telemetry_constants import WINDOW_END_UTC
from backend.services.feature_engineering import FeatureEngineeringService
from backend.services.risk_engine import RiskEngine
from backend.schemas.risk import (
    MachineResponse,
    MachineDetailResponse,
    PaginatedMachineResponse,
    MachineRiskAssessmentResponse,
    ContributingSensorSignalSchema,
    RiskLevelEnum,
)
from backend.schemas.maintenance import (
    MaintenanceWorkOrderResponse,
    FailureEventResponse,
)

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedMachineResponse,
    summary="List Monitored Machines",
    description="Retrieve a paginated list of industrial machines with optional filtering by line, type, or active status.",
)
def list_machines(
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    line_id: Optional[int] = Query(None, ge=1, description="Filter by production line ID"),
    machine_type: Optional[str] = Query(None, description="Filter by machine type category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
):
    """Retrieve paginated machines from database."""
    query = db.query(Machine)

    if line_id is not None:
        query = query.filter(Machine.line_id == line_id)
    if machine_type is not None:
        query = query.filter(Machine.machine_type == machine_type)
    if is_active is not None:
        query = query.filter(Machine.is_active == is_active)

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    machines = (
        query.order_by(Machine.machine_id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedMachineResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=[MachineResponse.model_validate(m) for m in machines],
    )


@router.get(
    "/{machine_id}",
    response_model=MachineDetailResponse,
    summary="Get Machine Details",
    description="Retrieve full details for an individual machine, including all attached IoT sensors.",
)
def get_machine(
    machine_id: int = Path(..., ge=1, description="Machine primary key identifier"),
    db: Session = Depends(get_db),
):
    """Retrieve machine details and sensor topology."""
    machine = (
        db.query(Machine)
        .options(selectinload(Machine.sensors))
        .filter(Machine.machine_id == machine_id)
        .first()
    )

    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine with id {machine_id} not found",
        )

    return MachineDetailResponse.model_validate(machine)


@router.get(
    "/{machine_id}/risk",
    response_model=MachineRiskAssessmentResponse,
    summary="Assess Machine Health & Risk",
    description=(
        "Calculate physics-informed Machine Health Index (0-100), Risk Score (0-100), "
        "and maintenance recommendations as of a point-in-time timestamp. "
        "Enforces strict anti-leakage guards (recorded_at < prediction_timestamp)."
    ),
)
def get_machine_risk(
    machine_id: int = Path(..., ge=1, description="Machine primary key identifier"),
    prediction_timestamp: Optional[datetime] = Query(
        None,
        description="Point-in-time cutoff timestamp (UTC). Telemetry at or after this timestamp is strictly excluded.",
    ),
    db: Session = Depends(get_db),
):
    """Compute point-in-time machine health index and degradation risk assessment."""
    machine = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine with id {machine_id} not found",
        )

    # Normalize prediction timestamp
    if prediction_timestamp is None:
        effective_cutoff = WINDOW_END_UTC
    elif prediction_timestamp.tzinfo is None:
        effective_cutoff = prediction_timestamp.replace(tzinfo=timezone.utc)
    else:
        effective_cutoff = prediction_timestamp

    # Extract time-series features strictly before cutoff (anti-leakage guard)
    feature_service = FeatureEngineeringService()
    risk_engine = RiskEngine()

    machine_features = feature_service.extract_features_from_db(
        session=db,
        machine_id=machine_id,
        prediction_timestamp=effective_cutoff,
    )

    assessment = risk_engine.assess_machine_risk(machine_features)
    assessment_dict = assessment.to_dict()
    assessment_dict["prediction_timestamp"] = effective_cutoff

    return MachineRiskAssessmentResponse(
        machine_id=assessment.machine_id,
        machine_code=assessment.machine_code,
        health_index=assessment.health_index,
        risk_score=assessment.risk_score,
        risk_level=RiskLevelEnum(assessment.risk_level.value),
        dominant_failure_mode=assessment.dominant_failure_mode,
        failure_mode_confidence=assessment.failure_mode_confidence,
        contributing_signals=[
            ContributingSensorSignalSchema(**s.to_dict()) for s in assessment.contributing_signals
        ],
        recommended_action=assessment.recommended_action,
        has_isolated_sensor_fault=assessment.has_isolated_sensor_fault,
        has_correlated_degradation=assessment.has_correlated_degradation,
        sensor_reliability_index=assessment.sensor_reliability_index,
        is_calibrated_probability=assessment.is_calibrated_probability,
        remaining_useful_life_hours=assessment.remaining_useful_life_hours,
        data_status=assessment.data_status,
        explanation_summary=assessment.explanation_summary,
        prediction_timestamp=effective_cutoff,
    )


@router.get(
    "/{machine_id}/health",
    response_model=MachineRiskAssessmentResponse,
    summary="Get Machine Health Index (Alias)",
    description="Convenience alias to the point-in-time machine risk and health index assessment.",
)
def get_machine_health(
    machine_id: int = Path(..., ge=1, description="Machine primary key identifier"),
    prediction_timestamp: Optional[datetime] = Query(
        None,
        description="Point-in-time cutoff timestamp (UTC). Telemetry at or after this timestamp is strictly excluded.",
    ),
    db: Session = Depends(get_db),
):
    """Alias for /risk endpoint returning full machine health and condition evaluation."""
    return get_machine_risk(machine_id=machine_id, prediction_timestamp=prediction_timestamp, db=db)


@router.get(
    "/{machine_id}/maintenance",
    summary="Get Machine Maintenance & Failure History",
    description="Retrieve all historical maintenance work orders and failure events for a machine.",
)
def get_machine_maintenance_history(
    machine_id: int = Path(..., ge=1, description="Machine primary key identifier"),
    db: Session = Depends(get_db),
):
    """Retrieve full maintenance history and recorded failures for a specific machine."""
    machine = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine with id {machine_id} not found",
        )

    work_orders = (
        db.query(MaintenanceWorkOrder)
        .filter(MaintenanceWorkOrder.machine_id == machine_id)
        .order_by(MaintenanceWorkOrder.created_at.desc())
        .all()
    )

    failures = (
        db.query(FailureEvent)
        .filter(FailureEvent.machine_id == machine_id)
        .order_by(FailureEvent.failure_time.desc())
        .all()
    )

    return {
        "machine_id": machine.machine_id,
        "machine_code": machine.machine_code,
        "total_work_orders": len(work_orders),
        "total_failures": len(failures),
        "work_orders": [MaintenanceWorkOrderResponse.model_validate(w) for w in work_orders],
        "failures": [FailureEventResponse.model_validate(f) for f in failures],
    }

