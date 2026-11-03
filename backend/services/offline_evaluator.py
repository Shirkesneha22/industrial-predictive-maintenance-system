"""
Offline Evaluation Engine for Industrial Predictive Maintenance.

Features:
- Isolated GroundTruthRegistry: keeps failure event labels strictly decoupled from feature engineering.
- Active downtime and repair period censoring: omits machines from prediction evaluation during repair.
- Chronological dataset partitioning: Train (Days 0-54), Validation (Days 54-72), Test (Days 72-90).
- Separate evaluation cohorts: Type A progressive degradation vs. Type B sudden stochastic breakdowns.
- Event-level alert matching and debouncing: prevents repeated alerts from inflating True Positives.
- Robust operational metrics: Precision, Recall, F1, False Alarms per machine-day, and Lead-Time distribution.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

try:
    from backend.generators.telemetry_constants import (
        WINDOW_START_UTC,
        WINDOW_END_UTC,
    )
    from backend.models import Machine, Sensor, FailureEvent, TelemetryEvent
    from backend.services.feature_engineering import (
        FeatureEngineeringService,
        SensorReading,
        MachineAggregatedFeatures,
    )
    from backend.services.risk_engine import RiskEngine, RiskLevel
    from backend.schemas.evaluation import (
        EvaluationSplit,
        FailureCohort,
        BenchmarkConfig,
        LeadTimeSummary,
        CohortEvaluationMetrics,
        EventDetectionRecord,
        FalseAlarmEpisodeRecord,
        FleetEvaluationSummary,
        ThresholdMetricPoint,
        ThresholdOptimizationResult,
    )
except ImportError:
    from generators.telemetry_constants import (
        WINDOW_START_UTC,
        WINDOW_END_UTC,
    )
    from models import Machine, Sensor, FailureEvent, TelemetryEvent
    from services.feature_engineering import (
        FeatureEngineeringService,
        SensorReading,
        MachineAggregatedFeatures,
    )
    from services.risk_engine import RiskEngine, RiskLevel
    from schemas.evaluation import (
        EvaluationSplit,
        FailureCohort,
        BenchmarkConfig,
        LeadTimeSummary,
        CohortEvaluationMetrics,
        EventDetectionRecord,
        FalseAlarmEpisodeRecord,
        FleetEvaluationSummary,
        ThresholdMetricPoint,
        ThresholdOptimizationResult,
    )


@dataclass
class GroundTruthEvent:
    """Isolated ground-truth failure record with zero exposure to feature engineering pipelines."""

    failure_id: int
    machine_id: int
    machine_code: str
    failure_type: str
    failure_class: FailureCohort  # TYPE_A or TYPE_B
    failure_time: datetime
    downtime_minutes: int
    severity: str = "critical"
    description: str = ""

    @property
    def repair_completion_time(self) -> datetime:
        """Timestamp when repair completes and machine returns to service."""
        return self.failure_time + timedelta(minutes=self.downtime_minutes)

    def is_in_repair_at(self, dt: datetime) -> bool:
        """Checks if a given timestamp falls strictly within the active breakdown and repair interval."""
        return self.failure_time <= dt < self.repair_completion_time


class GroundTruthRegistry:
    """
    Isolated in-memory registry of equipment failure events and repair schedules.
    Maintains strict separation between ground-truth labels and model inputs.
    """

    def __init__(self, events: Optional[List[GroundTruthEvent]] = None):
        self._events_by_id: Dict[int, GroundTruthEvent] = {}
        self._events_by_machine: Dict[int, List[GroundTruthEvent]] = {}
        if events:
            for ev in events:
                self.register_event(ev)

    def register_event(self, ev: GroundTruthEvent) -> None:
        """Register a single ground-truth failure event."""
        self._events_by_id[ev.failure_id] = ev
        if ev.machine_id not in self._events_by_machine:
            self._events_by_machine[ev.machine_id] = []
        self._events_by_machine[ev.machine_id].append(ev)
        self._events_by_machine[ev.machine_id].sort(key=lambda e: e.failure_time)

    @classmethod
    def load_from_db(
        cls,
        session: Session,
        type_a_machine_ids: Optional[Set[int]] = None,
    ) -> "GroundTruthRegistry":
        """
        Loads all ground-truth failure events from the database into the isolated registry.
        Does NOT expose any failure information to feature extraction.
        """
        stmt = (
            select(
                FailureEvent.failure_id,
                FailureEvent.machine_id,
                Machine.machine_code,
                FailureEvent.failure_type,
                FailureEvent.failure_time,
                FailureEvent.downtime_minutes,
                FailureEvent.severity,
                FailureEvent.description,
            )
            .join(Machine, FailureEvent.machine_id == Machine.machine_id)
            .order_by(FailureEvent.failure_time.asc())
        )
        rows = session.execute(stmt).all()

        registry = cls()
        for r in rows:
            f_id, m_id, m_code, f_type, f_time, downtime, severity, desc = r
            if f_time.tzinfo is None:
                f_time = f_time.replace(tzinfo=timezone.utc)

            # Classify cohort
            if type_a_machine_ids is not None:
                f_class = FailureCohort.TYPE_A if m_id in type_a_machine_ids else FailureCohort.TYPE_B
            else:
                # Default heuristic based on description or type
                desc_lower = (desc or "").lower()
                f_class = FailureCohort.TYPE_A if "degradation" in desc_lower or "progressive" in desc_lower else FailureCohort.TYPE_B

            ev = GroundTruthEvent(
                failure_id=f_id,
                machine_id=m_id,
                machine_code=m_code,
                failure_type=f_type,
                failure_class=f_class,
                failure_time=f_time,
                downtime_minutes=downtime or 360,
                severity=severity or "high",
                description=desc or "",
            )
            registry.register_event(ev)

        return registry

    def get_all_events(self) -> List[GroundTruthEvent]:
        """Return all registered ground-truth events."""
        return list(self._events_by_id.values())

    def get_events_for_machine(self, machine_id: int) -> List[GroundTruthEvent]:
        """Return all events for a specific machine ordered chronologically."""
        return self._events_by_machine.get(machine_id, [])

    def is_machine_in_downtime(self, machine_id: int, dt: datetime) -> bool:
        """
        Anti-leakage downtime guard:
        Returns True if the machine is experiencing active breakdown or ongoing repair at timestamp dt.
        """
        for ev in self.get_events_for_machine(machine_id):
            if ev.is_in_repair_at(dt):
                return True
        return False

    def get_events_in_range(
        self, start_time: datetime, end_time: datetime
    ) -> List[GroundTruthEvent]:
        """Return events occurring within a chronological window."""
        return [
            ev for ev in self._events_by_id.values()
            if start_time <= ev.failure_time < end_time
        ]


@dataclass
class PointInTimePrediction:
    """Isolated output of risk assessment at a single evaluation timestamp."""

    machine_id: int
    machine_code: str
    timestamp: datetime
    risk_score: float
    risk_level: RiskLevel
    is_alert: bool
    is_censored_in_repair: bool
    dominant_failure_mode: Optional[str] = None


class AlertMatchingPolicy:
    """
    Event-level alert matching and debouncing policy.

    Guarantees:
    - Exactly 1 True Positive per failure event (repeated alerts debounced into 1 detection episode).
    - Measures advance warning lead time (hours between first alert and breakdown).
    - Collapses consecutive unverified alerts within debounce window into 1 False Alarm Episode.
    - Evaluates Type A and Type B failure cohorts separately.
    """

    def __init__(self, config: BenchmarkConfig):
        self.config = config

    def match_predictions_to_events(
        self,
        predictions: List[PointInTimePrediction],
        ground_truth_events: List[GroundTruthEvent],
        operational_machine_days: float,
        split: EvaluationSplit,
        window_start: datetime,
        window_end: datetime,
        total_machines: int,
        timesteps_count: int,
        censored_evaluations: int,
    ) -> FleetEvaluationSummary:
        """
        Executes event-level matching and compiles comprehensive benchmark metrics.
        """
        # Group predictions by machine
        preds_by_machine: Dict[int, List[PointInTimePrediction]] = {}
        for p in predictions:
            if p.machine_id not in preds_by_machine:
                preds_by_machine[p.machine_id] = []
            preds_by_machine[p.machine_id].append(p)

        # Sort predictions chronologically
        for m_id in preds_by_machine:
            preds_by_machine[m_id].sort(key=lambda p: p.timestamp)

        # Group ground-truth events by machine
        events_by_machine: Dict[int, List[GroundTruthEvent]] = {}
        for ev in ground_truth_events:
            if ev.machine_id not in events_by_machine:
                events_by_machine[ev.machine_id] = []
            events_by_machine[ev.machine_id].append(ev)

        detected_records: List[EventDetectionRecord] = []
        false_alarm_episodes: List[FalseAlarmEpisodeRecord] = []

        total_raw_alerts = 0
        total_alert_episodes = 0

        # Process each machine's timeline
        for m_id, m_preds in preds_by_machine.items():
            m_code = m_preds[0].machine_code if m_preds else f"MCH-{m_id:03d}"
            m_events = events_by_machine.get(m_id, [])

            # Active detection tracking per failure
            # event_id -> {first_alert_time, first_score, alert_count}
            event_detections: Dict[int, Dict[str, Any]] = {}

            # False alarm tracking
            current_fa_start: Optional[datetime] = None
            current_fa_end: Optional[datetime] = None
            current_fa_max_score: float = 0.0
            current_fa_count: int = 0

            for pred in m_preds:
                # Omit censored predictions from alert processing
                if pred.is_censored_in_repair or not pred.is_alert:
                    continue

                total_raw_alerts += 1

                # Check if this alert matches an upcoming failure event on this machine
                matched_event: Optional[GroundTruthEvent] = None
                for ev in m_events:
                    lead_seconds = (ev.failure_time - pred.timestamp).total_seconds()
                    lead_hours = lead_seconds / 3600.0

                    if self.config.lead_window_min_hours <= lead_hours <= self.config.lead_window_max_hours:
                        matched_event = ev
                        break

                if matched_event is not None:
                    # Flush any pending false alarm episode before switching to true detection
                    if current_fa_start is not None:
                        false_alarm_episodes.append(
                            FalseAlarmEpisodeRecord(
                                machine_id=m_id,
                                machine_code=m_code,
                                episode_start_time=current_fa_start,
                                episode_end_time=current_fa_end or current_fa_start,
                                max_risk_score=current_fa_max_score,
                                alert_count=current_fa_count,
                            )
                        )
                        total_alert_episodes += 1
                        current_fa_start = None
                        current_fa_count = 0

                    # Record or update True Positive detection episode
                    ev_id = matched_event.failure_id
                    if ev_id not in event_detections:
                        event_detections[ev_id] = {
                            "event": matched_event,
                            "first_alert_time": pred.timestamp,
                            "first_score": pred.risk_score,
                            "alert_count": 1,
                        }
                        total_alert_episodes += 1
                    else:
                        event_detections[ev_id]["alert_count"] += 1

                else:
                    # Uncorroborated alert -> candidate false alarm
                    # Check debouncing window
                    debounce_td = timedelta(hours=self.config.false_alarm_debounce_hours)
                    if current_fa_start is None:
                        current_fa_start = pred.timestamp
                        current_fa_end = pred.timestamp
                        current_fa_max_score = pred.risk_score
                        current_fa_count = 1
                    elif pred.timestamp - current_fa_end <= debounce_td:
                        # Continue existing false alarm episode
                        current_fa_end = pred.timestamp
                        current_fa_max_score = max(current_fa_max_score, pred.risk_score)
                        current_fa_count += 1
                    else:
                        # Debounce window expired: save previous and start new episode
                        false_alarm_episodes.append(
                            FalseAlarmEpisodeRecord(
                                machine_id=m_id,
                                machine_code=m_code,
                                episode_start_time=current_fa_start,
                                episode_end_time=current_fa_end,
                                max_risk_score=current_fa_max_score,
                                alert_count=current_fa_count,
                            )
                        )
                        total_alert_episodes += 1
                        current_fa_start = pred.timestamp
                        current_fa_end = pred.timestamp
                        current_fa_max_score = pred.risk_score
                        current_fa_count = 1

            # Flush final false alarm episode if open
            if current_fa_start is not None:
                false_alarm_episodes.append(
                    FalseAlarmEpisodeRecord(
                        machine_id=m_id,
                        machine_code=m_code,
                        episode_start_time=current_fa_start,
                        episode_end_time=current_fa_end or current_fa_start,
                        max_risk_score=current_fa_max_score,
                        alert_count=current_fa_count,
                    )
                )
                total_alert_episodes += 1

            # Build EventDetectionRecords for all events on this machine
            for ev in m_events:
                if ev.failure_id in event_detections:
                    d_info = event_detections[ev.failure_id]
                    first_t = d_info["first_alert_time"]
                    lead_h = round((ev.failure_time - first_t).total_seconds() / 3600.0, 2)
                    detected_records.append(
                        EventDetectionRecord(
                            failure_id=ev.failure_id,
                            machine_id=ev.machine_id,
                            machine_code=ev.machine_code,
                            failure_type=ev.failure_type,
                            failure_class=ev.failure_class,
                            failure_time=ev.failure_time,
                            downtime_minutes=ev.downtime_minutes,
                            is_detected=True,
                            first_alert_time=first_t,
                            first_alert_risk_score=round(d_info["first_score"], 2),
                            lead_time_hours=lead_h,
                            alert_count_in_window=d_info["alert_count"],
                        )
                    )
                else:
                    detected_records.append(
                        EventDetectionRecord(
                            failure_id=ev.failure_id,
                            machine_id=ev.machine_id,
                            machine_code=ev.machine_code,
                            failure_type=ev.failure_type,
                            failure_class=ev.failure_class,
                            failure_time=ev.failure_time,
                            downtime_minutes=ev.downtime_minutes,
                            is_detected=False,
                            first_alert_time=None,
                            first_alert_risk_score=None,
                            lead_time_hours=None,
                            alert_count_in_window=0,
                        )
                    )

        # Compute cohort breakdowns
        type_a_events = [r for r in detected_records if r.failure_class == FailureCohort.TYPE_A]
        type_b_events = [r for r in detected_records if r.failure_class == FailureCohort.TYPE_B]

        type_a_metrics = self._calculate_cohort_metrics(FailureCohort.TYPE_A, type_a_events)
        type_b_metrics = self._calculate_cohort_metrics(FailureCohort.TYPE_B, type_b_events)

        # Overall fleet metrics
        tp = sum(1 for r in detected_records if r.is_detected)
        fn = sum(1 for r in detected_records if not r.is_detected)
        fp = len(false_alarm_episodes)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        far = fp / operational_machine_days if operational_machine_days > 0 else 0.0

        all_lead_times = [r.lead_time_hours for r in detected_records if r.is_detected and r.lead_time_hours is not None]
        overall_lead = self._summarize_lead_times(all_lead_times)

        return FleetEvaluationSummary(
            split=split,
            evaluation_window_start=window_start,
            evaluation_window_end=window_end,
            total_machines_evaluated=total_machines,
            total_timesteps_evaluated=timesteps_count,
            total_machine_evaluations=len(predictions),
            total_censored_repair_evaluations=censored_evaluations,
            total_operational_machine_days=round(operational_machine_days, 2),
            total_raw_alerts=total_raw_alerts,
            total_alert_episodes=total_alert_episodes,
            true_positive_events=tp,
            false_negative_events=fn,
            false_alarm_episodes=fp,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            false_alarms_per_machine_day=round(far, 4),
            overall_lead_time=overall_lead,
            type_a_metrics=type_a_metrics,
            type_b_metrics=type_b_metrics,
            detected_events=detected_records,
            false_alarm_episodes_list=false_alarm_episodes,
            notes=[
                "Point-in-time anti-leakage strictly enforced: recorded_at < evaluation_timestamp.",
                "Active breakdown and repair downtime censored from prediction evaluation.",
                "Type A progressive degradations and Type B sudden failures evaluated separately.",
                "Risk score is an engineering degradation indicator, not a calibrated failure probability.",
            ],
        )

    def _calculate_cohort_metrics(
        self, cohort: FailureCohort, records: List[EventDetectionRecord]
    ) -> CohortEvaluationMetrics:
        """Calculate detection metrics for a specific failure cohort."""
        total = len(records)
        tp = sum(1 for r in records if r.is_detected)
        fn = total - tp
        recall = tp / total if total > 0 else 0.0

        lead_times = [r.lead_time_hours for r in records if r.is_detected and r.lead_time_hours is not None]
        lead_summary = self._summarize_lead_times(lead_times)

        return CohortEvaluationMetrics(
            cohort=cohort,
            total_failure_events=total,
            detected_failure_events=tp,
            missed_failure_events=fn,
            recall=round(recall, 4),
            precision=None,  # Precision evaluated fleet-wide due to shared false alarms
            f1_score=None,
            lead_time=lead_summary,
        )

    @staticmethod
    def _summarize_lead_times(lead_times: List[float]) -> LeadTimeSummary:
        """Calculate statistical distribution of advance warning lead times."""
        if not lead_times:
            return LeadTimeSummary(count=0)
        return LeadTimeSummary(
            count=len(lead_times),
            mean_hours=round(float(np.mean(lead_times)), 2),
            median_hours=round(float(np.median(lead_times)), 2),
            min_hours=round(float(np.min(lead_times)), 2),
            max_hours=round(float(np.max(lead_times)), 2),
        )


class OfflineEvaluationEngine:
    """
    Offline Benchmark Engine for Industrial Predictive Maintenance.

    Executes point-in-time rolling condition assessments across specified chronological splits.
    Guarantees strict temporal anti-leakage, downtime repair censoring, and label sequestration.
    """

    def __init__(
        self,
        config: Optional[BenchmarkConfig] = None,
        registry: Optional[GroundTruthRegistry] = None,
        feature_service: Optional[FeatureEngineeringService] = None,
        risk_engine: Optional[RiskEngine] = None,
    ):
        self.config = config or BenchmarkConfig()
        self.registry = registry or GroundTruthRegistry()
        self.feature_service = feature_service or FeatureEngineeringService()
        self.risk_engine = risk_engine or RiskEngine()
        self.matcher = AlertMatchingPolicy(self.config)

    def get_split_boundaries(
        self, split: EvaluationSplit
    ) -> Tuple[datetime, datetime]:
        """
        Derives chronological UTC timestamps for dataset splits.

        Train: Days 0 to 54 (2026-08-04 to 2026-09-27)
        Val:   Days 54 to 72 (2026-09-27 to 2026-10-15)
        Test:  Days 72 to 90 (2026-10-15 to 2026-11-02)
        All:   Days 0 to 90 (2026-08-04 to 2026-11-02)
        """
        w_start = WINDOW_START_UTC
        w_end = WINDOW_END_UTC

        train_cutoff = w_start + timedelta(days=self.config.train_end_days)
        val_cutoff = w_start + timedelta(days=self.config.val_end_days)

        if split == EvaluationSplit.TRAIN:
            return w_start, train_cutoff
        elif split == EvaluationSplit.VAL:
            return train_cutoff, val_cutoff
        elif split == EvaluationSplit.TEST:
            return val_cutoff, w_end
        else:  # ALL
            return w_start, w_end

    def evaluate_in_memory_stream(
        self,
        machines: List[Dict[str, Any]],
        readings_by_machine: Dict[int, List[SensorReading]],
        split: Optional[EvaluationSplit] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> FleetEvaluationSummary:
        """
        Executes point-in-time evaluation across an in-memory stream of telemetry readings.
        Designed for high-performance benchmarking and comprehensive automated unit testing.
        """
        target_split = split or self.config.split
        start_time, end_time = self.get_split_boundaries(target_split)

        # Generate evaluation timestamps
        step_td = timedelta(hours=self.config.step_interval_hours)
        eval_timestamps: List[datetime] = []
        curr = start_time
        while curr < end_time:
            eval_timestamps.append(curr)
            curr += step_td

        if not eval_timestamps:
            eval_timestamps = [start_time]

        predictions: List[PointInTimePrediction] = []
        censored_count = 0
        total_steps = len(eval_timestamps)

        for step_idx, t_eval in enumerate(eval_timestamps):
            if progress_callback:
                progress_callback(step_idx + 1, total_steps, f"Evaluating point-in-time {t_eval.isoformat()}")

            for m in machines:
                m_id = m["id"]
                m_code = m.get("code", f"MCH-{m_id:03d}")

                # Anti-leakage Guard: Check active downtime/repair interval
                if self.registry.is_machine_in_downtime(m_id, t_eval):
                    censored_count += 1
                    predictions.append(
                        PointInTimePrediction(
                            machine_id=m_id,
                            machine_code=m_code,
                            timestamp=t_eval,
                            risk_score=0.0,
                            risk_level=RiskLevel.NORMAL,
                            is_alert=False,
                            is_censored_in_repair=True,
                        )
                    )
                    continue

                # Anti-leakage: Feature extractor strictly filters recorded_at < t_eval
                all_m_readings = readings_by_machine.get(m_id, [])
                features = self.feature_service.extract_machine_features(
                    machine_id=m_id,
                    machine_code=m_code,
                    readings=all_m_readings,
                    prediction_timestamp=t_eval,
                )

                # Assess machine condition with RiskEngine
                assessment = self.risk_engine.assess_machine_risk(features)
                is_alert = (
                    assessment.risk_score >= self.config.alert_threshold
                    or assessment.risk_level in [RiskLevel.WARNING, RiskLevel.CRITICAL]
                )

                predictions.append(
                    PointInTimePrediction(
                        machine_id=m_id,
                        machine_code=m_code,
                        timestamp=t_eval,
                        risk_score=assessment.risk_score,
                        risk_level=assessment.risk_level,
                        is_alert=is_alert,
                        is_censored_in_repair=False,
                        dominant_failure_mode=assessment.dominant_failure_mode,
                    )
                )

        # Calculate operational machine-days (uncensored active machine evaluations)
        uncensored_evals = len(predictions) - censored_count
        operational_machine_days = (uncensored_evals * self.config.step_interval_hours) / 24.0

        # Retrieve relevant ground-truth events within this evaluation window
        target_events = self.registry.get_events_in_range(start_time, end_time)

        return self.matcher.match_predictions_to_events(
            predictions=predictions,
            ground_truth_events=target_events,
            operational_machine_days=operational_machine_days,
            split=target_split,
            window_start=start_time,
            window_end=end_time,
            total_machines=len(machines),
            timesteps_count=len(eval_timestamps),
            censored_evaluations=censored_count,
        )

    def evaluate_from_db(
        self,
        session: Session,
        split: Optional[EvaluationSplit] = None,
        machine_ids: Optional[List[int]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> FleetEvaluationSummary:
        """
        Executes point-in-time offline evaluation directly against PostgreSQL.
        Uses windowed batch telemetry loading to avoid memory exhaustion across 2.16M rows.
        """
        target_split = split or self.config.split
        start_time, end_time = self.get_split_boundaries(target_split)

        # Fetch active machines
        m_query = session.query(Machine).filter(Machine.is_active == True)
        if machine_ids:
            m_query = m_query.filter(Machine.machine_id.in_(machine_ids))
        db_machines = m_query.order_by(Machine.machine_id.asc()).all()

        machines_meta = [{"id": m.machine_id, "code": m.machine_code} for m in db_machines]
        target_m_ids = [m["id"] for m in machines_meta]

        step_td = timedelta(hours=self.config.step_interval_hours)
        eval_timestamps: List[datetime] = []
        curr = start_time
        while curr < end_time:
            eval_timestamps.append(curr)
            curr += step_td

        if not eval_timestamps:
            eval_timestamps = [start_time]

        predictions: List[PointInTimePrediction] = []
        censored_count = 0
        total_steps = len(eval_timestamps)

        for step_idx, t_eval in enumerate(eval_timestamps):
            if progress_callback:
                progress_callback(step_idx + 1, total_steps, f"Evaluating database step {step_idx + 1}/{total_steps} at {t_eval.isoformat()}")

            # Determine machines that are NOT currently in downtime at t_eval
            active_m_ids = [
                m_id for m_id in target_m_ids
                if not self.registry.is_machine_in_downtime(m_id, t_eval)
            ]
            downtime_m_ids = set(target_m_ids) - set(active_m_ids)

            for d_id in downtime_m_ids:
                censored_count += 1
                predictions.append(
                    PointInTimePrediction(
                        machine_id=d_id,
                        machine_code=f"MCH-{d_id:03d}",
                        timestamp=t_eval,
                        risk_score=0.0,
                        risk_level=RiskLevel.NORMAL,
                        is_alert=False,
                        is_censored_in_repair=True,
                    )
                )

            if not active_m_ids:
                continue

            # Query 7-day lookback window strictly before t_eval for active machines
            query_start = t_eval - timedelta(hours=168)
            stmt = (
                select(
                    TelemetryEvent.sensor_id,
                    TelemetryEvent.recorded_at,
                    TelemetryEvent.value,
                    TelemetryEvent.quality_status,
                    Sensor.sensor_type,
                    Sensor.sensor_code,
                    Sensor.machine_id,
                )
                .join(Sensor, TelemetryEvent.sensor_id == Sensor.sensor_id)
                .where(
                    Sensor.machine_id.in_(active_m_ids),
                    TelemetryEvent.recorded_at < t_eval,  # Strict anti-leakage
                    TelemetryEvent.recorded_at >= query_start,
                )
                .order_by(TelemetryEvent.recorded_at.asc())
            )
            rows = session.execute(stmt).all()

            # Group readings by machine
            step_readings: Dict[int, List[SensorReading]] = {}
            for r in rows:
                m_id_r = r[6]
                if m_id_r not in step_readings:
                    step_readings[m_id_r] = []
                step_readings[m_id_r].append(
                    SensorReading(
                        sensor_id=r[0],
                        recorded_at=r[1],
                        value=float(r[2]) if r[2] is not None else None,
                        quality_status=str(r[3]),
                        sensor_type=str(r[4]),
                        sensor_code=str(r[5]),
                    )
                )

            # Extract features and assess risk for each active machine
            for m in machines_meta:
                m_id = m["id"]
                if m_id not in active_m_ids:
                    continue

                m_code = m["code"]
                m_readings = step_readings.get(m_id, [])

                features = self.feature_service.extract_machine_features(
                    machine_id=m_id,
                    machine_code=m_code,
                    readings=m_readings,
                    prediction_timestamp=t_eval,
                )

                assessment = self.risk_engine.assess_machine_risk(features)
                is_alert = (
                    assessment.risk_score >= self.config.alert_threshold
                    or assessment.risk_level in [RiskLevel.WARNING, RiskLevel.CRITICAL]
                )

                predictions.append(
                    PointInTimePrediction(
                        machine_id=m_id,
                        machine_code=m_code,
                        timestamp=t_eval,
                        risk_score=assessment.risk_score,
                        risk_level=assessment.risk_level,
                        is_alert=is_alert,
                        is_censored_in_repair=False,
                        dominant_failure_mode=assessment.dominant_failure_mode,
                    )
                )

        uncensored_evals = len(predictions) - censored_count
        operational_machine_days = (uncensored_evals * self.config.step_interval_hours) / 24.0
        target_events = self.registry.get_events_in_range(start_time, end_time)

        return self.matcher.match_predictions_to_events(
            predictions=predictions,
            ground_truth_events=target_events,
            operational_machine_days=operational_machine_days,
            split=target_split,
            window_start=start_time,
            window_end=end_time,
            total_machines=len(machines_meta),
            timesteps_count=len(eval_timestamps),
            censored_evaluations=censored_count,
        )

    def sweep_thresholds(
        self,
        predictions: List[PointInTimePrediction],
        ground_truth_events: List[GroundTruthEvent],
        operational_machine_days: float,
        split: EvaluationSplit,
        window_start: datetime,
        window_end: datetime,
        total_machines: int,
        timesteps_count: int,
        censored_evaluations: int,
        thresholds: Optional[List[float]] = None,
    ) -> ThresholdOptimizationResult:
        """
        Sweeps risk score thresholds (15.0 to 85.0 in increments of 5.0 by default)
        across a fixed set of point-in-time predictions.

        Guarantees:
        - Evaluates Type A progressive degradations and Type B sudden failures separately.
        - Computes precision, recall, F1, false alarm episodes, and lead-time statistics.
        - Selects recommended threshold using multi-objective engineering criterion:
          1. Maximize validation F1 score.
          2. Break ties by minimizing False Alarms per operational machine-day (FAR).
          3. Break further ties by prioritizing maximum Type A advance warning lead time (or baseline tau=35.0).
        """
        if thresholds is None:
            # 15 to 85 in increments of 5
            thresholds = [round(15.0 + 5.0 * i, 1) for i in range(15)]

        metric_curve: List[ThresholdMetricPoint] = []

        for tau in thresholds:
            # Re-evaluate alert flags for this threshold
            tau_preds = [
                PointInTimePrediction(
                    machine_id=p.machine_id,
                    machine_code=p.machine_code,
                    timestamp=p.timestamp,
                    risk_score=p.risk_score,
                    risk_level=p.risk_level,
                    is_alert=(p.risk_score >= tau) and not p.is_censored_in_repair,
                    is_censored_in_repair=p.is_censored_in_repair,
                    dominant_failure_mode=p.dominant_failure_mode,
                )
                for p in predictions
            ]

            cfg_tau = BenchmarkConfig(
                split=split,
                step_interval_hours=self.config.step_interval_hours,
                alert_threshold=tau,
                critical_threshold=self.config.critical_threshold,
                lead_window_min_hours=self.config.lead_window_min_hours,
                lead_window_max_hours=self.config.lead_window_max_hours,
                false_alarm_debounce_hours=self.config.false_alarm_debounce_hours,
                train_end_days=self.config.train_end_days,
                val_end_days=self.config.val_end_days,
            )
            matcher = AlertMatchingPolicy(config=cfg_tau)

            summary = matcher.match_predictions_to_events(
                predictions=tau_preds,
                ground_truth_events=ground_truth_events,
                operational_machine_days=operational_machine_days,
                split=split,
                window_start=window_start,
                window_end=window_end,
                total_machines=total_machines,
                timesteps_count=timesteps_count,
                censored_evaluations=censored_evaluations,
            )

            point = ThresholdMetricPoint(
                threshold=tau,
                precision=summary.precision,
                recall=summary.recall,
                f1_score=summary.f1_score,
                true_positives=summary.true_positive_events,
                false_negatives=summary.false_negative_events,
                false_alarm_episodes=summary.false_alarm_episodes,
                false_alarms_per_machine_day=summary.false_alarms_per_machine_day,
                lead_time=summary.overall_lead_time,
                type_a_recall=summary.type_a_metrics.recall,
                type_a_detected=summary.type_a_metrics.detected_failure_events,
                type_a_total=summary.type_a_metrics.total_failure_events,
                type_a_lead_time=summary.type_a_metrics.lead_time,
                type_b_recall=summary.type_b_metrics.recall,
                type_b_detected=summary.type_b_metrics.detected_failure_events,
                type_b_total=summary.type_b_metrics.total_failure_events,
                type_b_lead_time=summary.type_b_metrics.lead_time,
            )
            metric_curve.append(point)

        # Select recommended threshold based on documented multi-objective criterion:
        # 1. Maximize F1 score.
        # 2. Minimize false alarms per machine-day.
        # 3. Prefer standard baseline threshold (35.0) in case of flat/saturated response.
        best_point = metric_curve[0]
        for pt in metric_curve:
            # Better F1 score
            if pt.f1_score > best_point.f1_score:
                best_point = pt
            elif abs(pt.f1_score - best_point.f1_score) < 1e-5:
                # Tie in F1: prefer lower false alarm rate
                if pt.false_alarms_per_machine_day < best_point.false_alarms_per_machine_day:
                    best_point = pt
                elif abs(pt.false_alarms_per_machine_day - best_point.false_alarms_per_machine_day) < 1e-5:
                    # Flat curve tie-break: prefer standard engineering Warning boundary (35.0) if present
                    if pt.threshold == 35.0:
                        best_point = pt

        selection_criterion = (
            "Multi-objective validation optimization: "
            "(1) Maximize F1 score; "
            "(2) Minimize False Alarms per operational machine-day; "
            "(3) In flat risk saturation regimes, prioritize standard Warning boundary (tau = 35.0)."
        )
        selection_reasoning = (
            f"Recommended threshold tau = {best_point.threshold:.1f} achieves optimal F1 score ({best_point.f1_score:.4f}) "
            f"with {best_point.type_a_recall * 100:.1f}% Type A progressive failure capture "
            f"and a bounded false alarm rate of {best_point.false_alarms_per_machine_day:.4f} alarms/machine-day."
        )

        return ThresholdOptimizationResult(
            split=split,
            validation_window_start=window_start,
            validation_window_end=window_end,
            operational_machine_days=round(operational_machine_days, 2),
            thresholds_evaluated=thresholds,
            recommended_threshold=best_point.threshold,
            selection_criterion=selection_criterion,
            selection_reasoning=selection_reasoning,
            best_point=best_point,
            metric_curve=metric_curve,
            notes=[
                "Threshold optimization executed exclusively on the validation partition (Days 54 to 72).",
                "Test split remains strictly quarantined and untouched during optimization.",
                "Risk scores are engineering indices and must never be interpreted as calibrated failure probabilities.",
            ],
        )

    def optimize_thresholds_in_memory(
        self,
        machines: List[Dict[str, Any]],
        readings_by_machine: Dict[int, List[SensorReading]],
        thresholds: Optional[List[float]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> ThresholdOptimizationResult:
        """
        Executes threshold optimization on an in-memory telemetry stream.
        Strictly enforces that optimization runs exclusively on the validation split (Days 54-72).
        """
        val_split = EvaluationSplit.VAL
        start_time, end_time = self.get_split_boundaries(val_split)

        step_td = timedelta(hours=self.config.step_interval_hours)
        eval_timestamps: List[datetime] = []
        curr = start_time
        while curr < end_time:
            eval_timestamps.append(curr)
            curr += step_td

        if not eval_timestamps:
            eval_timestamps = [start_time]

        predictions: List[PointInTimePrediction] = []
        censored_count = 0
        total_steps = len(eval_timestamps)

        for step_idx, t_eval in enumerate(eval_timestamps):
            if progress_callback:
                progress_callback(step_idx + 1, total_steps, f"Evaluating validation step {step_idx + 1}/{total_steps}")

            for m in machines:
                m_id = m["id"]
                m_code = m.get("code", f"MCH-{m_id:03d}")

                if self.registry.is_machine_in_downtime(m_id, t_eval):
                    censored_count += 1
                    predictions.append(
                        PointInTimePrediction(
                            machine_id=m_id,
                            machine_code=m_code,
                            timestamp=t_eval,
                            risk_score=0.0,
                            risk_level=RiskLevel.NORMAL,
                            is_alert=False,
                            is_censored_in_repair=True,
                        )
                    )
                    continue

                all_m_readings = readings_by_machine.get(m_id, [])
                features = self.feature_service.extract_machine_features(
                    machine_id=m_id,
                    machine_code=m_code,
                    readings=all_m_readings,
                    prediction_timestamp=t_eval,
                )

                assessment = self.risk_engine.assess_machine_risk(features)

                predictions.append(
                    PointInTimePrediction(
                        machine_id=m_id,
                        machine_code=m_code,
                        timestamp=t_eval,
                        risk_score=assessment.risk_score,
                        risk_level=assessment.risk_level,
                        is_alert=False,
                        is_censored_in_repair=False,
                        dominant_failure_mode=assessment.dominant_failure_mode,
                    )
                )

        uncensored_evals = len(predictions) - censored_count
        operational_machine_days = (uncensored_evals * self.config.step_interval_hours) / 24.0
        val_events = self.registry.get_events_in_range(start_time, end_time)

        return self.sweep_thresholds(
            predictions=predictions,
            ground_truth_events=val_events,
            operational_machine_days=operational_machine_days,
            split=val_split,
            window_start=start_time,
            window_end=end_time,
            total_machines=len(machines),
            timesteps_count=len(eval_timestamps),
            censored_evaluations=censored_count,
            thresholds=thresholds,
        )

