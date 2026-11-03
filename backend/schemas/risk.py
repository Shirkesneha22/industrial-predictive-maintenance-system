"""
Pydantic Schemas for Machine Health, Risk Assessment, and Fleet Telemetry.
Enforces strict anti-leakage principles and clear data contracts.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RiskLevelEnum(str, Enum):
    """Categorical risk severity level."""

    NORMAL = "Normal"
    WARNING = "Warning"
    CRITICAL = "Critical"


class ContributingSensorSignalSchema(BaseModel):
    """Structured detail of an individual sensor contributing to the risk assessment."""

    sensor_id: int
    sensor_type: str
    sensor_code: str
    observed_mean: Optional[float] = None
    nominal_baseline: float
    z_score: float
    trend_slope: float
    weight: float
    risk_contribution: float
    is_fault: bool
    explanation: str


class MachineRiskAssessmentResponse(BaseModel):
    """
    Explainable machine health and risk assessment response.
    Enforces anti-leakage guards: engineering indicator, not calibrated failure probability.
    """

    machine_id: int
    machine_code: str
    health_index: float = Field(..., ge=0.0, le=100.0, description="Machine health condition index (0-100)")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Machine degradation risk score (0-100)")
    risk_level: RiskLevelEnum = Field(..., description="Categorical risk classification")
    dominant_failure_mode: Optional[str] = Field(None, description="Diagnosed mechanical failure mode")
    failure_mode_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Diagnostic confidence (0-1)")
    contributing_signals: List[ContributingSensorSignalSchema] = Field(
        default_factory=list, description="Sensor channels contributing to risk"
    )
    recommended_action: str = Field(..., description="Contextual maintenance recommendation")
    has_isolated_sensor_fault: bool = Field(False, description="Flag for single-sensor instrumentation fault")
    has_correlated_degradation: bool = Field(False, description="Flag for multi-sensor physical wear")
    sensor_reliability_index: float = Field(100.0, ge=0.0, le=100.0, description="Instrumentation reliability score")
    is_calibrated_probability: bool = Field(
        False, description="Explicit anti-leakage indicator: risk score is NOT a calibrated probability"
    )
    remaining_useful_life_hours: Optional[float] = Field(
        None, description="Remaining useful life in hours (None unless validated)"
    )
    data_status: str = Field("sufficient", description="Data completeness status (e.g., sufficient, insufficient_telemetry)")
    explanation_summary: str = Field("", description="Human-readable synthesis of asset condition")
    prediction_timestamp: Optional[datetime] = Field(
        None, description="Point-in-time timestamp cutoff used for anti-leakage evaluation"
    )


class SensorBriefSchema(BaseModel):
    """Brief representation of an IoT sensor attached to a machine."""

    model_config = ConfigDict(from_attributes=True)

    sensor_id: int
    machine_id: int
    sensor_code: str
    sensor_type: str
    unit: str
    installation_date: Optional[date] = None
    is_active: bool


class MachineResponse(BaseModel):
    """Standard machine entity response."""

    model_config = ConfigDict(from_attributes=True)

    machine_id: int
    line_id: int
    machine_code: str
    name: str
    machine_type: str
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    installation_date: Optional[date] = None
    is_active: bool
    created_at: datetime


class MachineDetailResponse(MachineResponse):
    """Detailed machine entity response with mounted sensors."""

    sensors: List[SensorBriefSchema] = []


class PaginatedMachineResponse(BaseModel):
    """Paginated list container for machine entities."""

    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)
    items: List[MachineResponse]


class FleetAnomalySummary(BaseModel):
    """Fleet-wide summary statistics of machine health and risk levels."""

    total_machines_evaluated: int = Field(..., ge=0)
    normal_count: int = Field(..., ge=0)
    warning_count: int = Field(..., ge=0)
    critical_count: int = Field(..., ge=0)
    correlated_degradation_count: int = Field(..., ge=0)
    isolated_sensor_fault_count: int = Field(..., ge=0)
    total_plants: int = Field(default=3, ge=0)
    total_lines: int = Field(default=12, ge=0)
    total_sensors: int = Field(default=500, ge=0)
    average_health_index: float = Field(default=85.0, ge=0.0, le=100.0)


class FleetAnomalyItem(BaseModel):
    """Machine anomaly item in fleet-wide prediction report."""

    machine_id: int
    machine_code: str
    machine_name: str
    machine_type: str
    line_id: int
    health_index: float
    risk_score: float
    risk_level: RiskLevelEnum
    dominant_failure_mode: Optional[str] = None
    failure_mode_confidence: float = 0.0
    has_correlated_degradation: bool = False
    has_isolated_sensor_fault: bool = False
    sensor_reliability_index: float = 100.0
    recommended_action: str
    data_status: str = "sufficient"
    explanation_summary: str = ""


class FleetAnomalyResponse(BaseModel):
    """Paginated fleet-wide anomaly detection response."""

    prediction_timestamp: datetime
    summary: FleetAnomalySummary
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)
    items: List[FleetAnomalyItem]


class TelemetryEventResponse(BaseModel):
    """Individual telemetry reading response."""

    model_config = ConfigDict(from_attributes=True)

    event_id: int
    sensor_id: int
    sensor_code: Optional[str] = None
    sensor_type: Optional[str] = None
    unit: Optional[str] = None
    recorded_at: datetime
    value: Optional[float] = None
    quality_status: str


class PaginatedTelemetryResponse(BaseModel):
    """Paginated container for historical telemetry events."""

    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)
    items: List[TelemetryEventResponse]


class RulEstimationResponse(BaseModel):
    """Remaining useful life estimation response with anti-leakage disclaimer."""

    machine_id: int
    machine_code: str
    prediction_timestamp: datetime
    remaining_useful_life_hours: Optional[float] = None
    is_calibrated: bool = False
    message: str = "Unvalidated RUL is not claimed under anti-leakage guidelines."
