"""
Evaluation Schemas and Domain Contracts for Industrial Predictive Maintenance.

Defines standardized data structures for:
- Chronological evaluation splits (Train, Validation, Test, All).
- Benchmark configuration parameters (cadence, prediction horizons, debounce intervals).
- Event-level detection outcomes and lead times.
- Cohort-separated metrics (Type A progressive vs. Type B stochastic).
- Fleet-wide false alarm episodes and operational rates.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EvaluationSplit(str, Enum):
    """Chronological dataset partition for offline evaluation."""

    TRAIN = "train"
    VAL = "val"
    TEST = "test"
    ALL = "all"


class FailureCohort(str, Enum):
    """Categorical classification of failure mechanism cohort."""

    TYPE_A = "Type A"
    TYPE_B = "Type B"
    FLEET = "Fleet"


class BenchmarkConfig(BaseModel):
    """Configurable execution parameters for offline benchmark simulation."""

    split: EvaluationSplit = Field(
        default=EvaluationSplit.TEST,
        description="Chronological split to benchmark (train: days 0-54, val: days 54-72, test: days 72-90, all: 0-90)",
    )
    step_interval_hours: int = Field(
        default=6,
        ge=1,
        le=72,
        description="Temporal interval between consecutive fleet evaluation steps (hours)",
    )
    alert_threshold: float = Field(
        default=35.0,
        ge=0.0,
        le=100.0,
        description="Risk score threshold for triggering an alert (35.0 = Warning boundary)",
    )
    critical_threshold: float = Field(
        default=65.0,
        ge=0.0,
        le=100.0,
        description="Risk score threshold for triggering a critical emergency alert",
    )
    lead_window_min_hours: float = Field(
        default=1.0,
        ge=0.0,
        description="Minimum warning lead time for an alert to be considered predictive rather than reactive (hours)",
    )
    lead_window_max_hours: float = Field(
        default=168.0,
        ge=1.0,
        description="Maximum advance warning window horizon (hours, default: 168h / 7 days)",
    )
    false_alarm_debounce_hours: float = Field(
        default=24.0,
        ge=1.0,
        description="Temporal window to collapse repeated unverified alerts on a machine into a single false alarm episode",
    )
    train_end_days: int = Field(
        default=54,
        description="Elapsed days from window start for training split cutoff",
    )
    val_end_days: int = Field(
        default=72,
        description="Elapsed days from window start for validation split cutoff",
    )


class LeadTimeSummary(BaseModel):
    """Statistical summary of alert lead times for true positive detections."""

    count: int = Field(default=0, description="Total number of detected events with measurable lead time")
    mean_hours: Optional[float] = Field(default=None, description="Average advance warning lead time (hours)")
    median_hours: Optional[float] = Field(default=None, description="Median advance warning lead time (hours)")
    min_hours: Optional[float] = Field(default=None, description="Shortest advance warning lead time (hours)")
    max_hours: Optional[float] = Field(default=None, description="Longest advance warning lead time (hours)")


class CohortEvaluationMetrics(BaseModel):
    """Performance evaluation metrics for a specific failure cohort."""

    cohort: FailureCohort = Field(..., description="Failure cohort evaluated")
    total_failure_events: int = Field(..., ge=0, description="Ground-truth failure events in this cohort")
    detected_failure_events: int = Field(..., ge=0, description="Events successfully predicted within lead horizon (TP)")
    missed_failure_events: int = Field(..., ge=0, description="Events missed with no prior alert (FN)")
    recall: float = Field(..., ge=0.0, le=1.0, description="Cohort sensitivity / recall (TP / total_events)")
    precision: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Precision where false alarms can be attributed directly, otherwise fleet-wide",
    )
    f1_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Harmonic mean of precision and recall",
    )
    lead_time: LeadTimeSummary = Field(
        default_factory=LeadTimeSummary,
        description="Lead time distribution for captured events in this cohort",
    )


class EventDetectionRecord(BaseModel):
    """Evaluation log for an individual ground-truth failure event."""

    failure_id: int
    machine_id: int
    machine_code: str
    failure_type: str
    failure_class: FailureCohort
    failure_time: datetime
    downtime_minutes: int
    is_detected: bool
    first_alert_time: Optional[datetime] = None
    first_alert_risk_score: Optional[float] = None
    lead_time_hours: Optional[float] = None
    alert_count_in_window: int = 0


class FalseAlarmEpisodeRecord(BaseModel):
    """Record of an uncorroborated alert episode on a machine."""

    machine_id: int
    machine_code: str
    episode_start_time: datetime
    episode_end_time: datetime
    max_risk_score: float
    alert_count: int


class FleetEvaluationSummary(BaseModel):
    """Comprehensive offline evaluation benchmark results across all machines."""

    split: EvaluationSplit
    evaluation_window_start: datetime
    evaluation_window_end: datetime
    total_machines_evaluated: int
    total_timesteps_evaluated: int
    total_machine_evaluations: int
    total_censored_repair_evaluations: int
    total_operational_machine_days: float
    # Alert metrics
    total_raw_alerts: int
    total_alert_episodes: int
    true_positive_events: int
    false_negative_events: int
    false_alarm_episodes: int
    # Classification metrics
    precision: float = Field(..., ge=0.0, le=1.0)
    recall: float = Field(..., ge=0.0, le=1.0)
    f1_score: float = Field(..., ge=0.0, le=1.0)
    false_alarms_per_machine_day: float = Field(..., ge=0.0)
    # Lead time across all detections
    overall_lead_time: LeadTimeSummary
    # Cohort-specific breakdown
    type_a_metrics: CohortEvaluationMetrics
    type_b_metrics: CohortEvaluationMetrics
    # Detailed event audits
    detected_events: List[EventDetectionRecord] = Field(default_factory=list)
    false_alarm_episodes_list: List[FalseAlarmEpisodeRecord] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class ThresholdMetricPoint(BaseModel):
    """Performance evaluation metrics at a specific decision threshold."""

    threshold: float = Field(..., ge=0.0, le=100.0, description="Risk score decision threshold (tau)")
    precision: float = Field(..., ge=0.0, le=1.0)
    recall: float = Field(..., ge=0.0, le=1.0)
    f1_score: float = Field(..., ge=0.0, le=1.0)
    true_positives: int = Field(..., ge=0)
    false_negatives: int = Field(..., ge=0)
    false_alarm_episodes: int = Field(..., ge=0)
    false_alarms_per_machine_day: float = Field(..., ge=0.0)
    lead_time: LeadTimeSummary
    # Cohort breakdown
    type_a_recall: float = Field(..., ge=0.0, le=1.0)
    type_a_detected: int = Field(..., ge=0)
    type_a_total: int = Field(..., ge=0)
    type_a_lead_time: LeadTimeSummary
    type_b_recall: float = Field(..., ge=0.0, le=1.0)
    type_b_detected: int = Field(..., ge=0)
    type_b_total: int = Field(..., ge=0)
    type_b_lead_time: LeadTimeSummary


class ThresholdOptimizationResult(BaseModel):
    """Comprehensive output of threshold sweeping across the validation partition."""

    split: EvaluationSplit = EvaluationSplit.VAL
    validation_window_start: datetime
    validation_window_end: datetime
    operational_machine_days: float
    thresholds_evaluated: List[float]
    recommended_threshold: float
    selection_criterion: str
    selection_reasoning: str
    best_point: ThresholdMetricPoint
    metric_curve: List[ThresholdMetricPoint]
    notes: List[str] = Field(default_factory=list)

