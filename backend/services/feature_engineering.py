"""
Feature Engineering Service for Industrial Predictive Maintenance System.

Computes rolling time-series features across 6-hour, 24-hour, and 7-day windows.
Enforces strict anti-leakage guards:
- Readings strictly before the prediction timestamp (recorded_at < prediction_timestamp).
- Machine condition features derived exclusively from quality_status == 'normal'.
- Missing, invalid, and sensor-fault readings tracked separately as reliability indicators.
- No forward-filling across long gaps.
- Multi-sensor machine aggregation that isolates faulty sensors from triggering false machine failure alerts.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

try:
    from backend.generators.telemetry_constants import (
        QUALITY_NORMAL,
        QUALITY_SENSOR_FAULT,
        QUALITY_INVALID,
        QUALITY_MISSING,
        SENSOR_PHYSICS_PROFILES,
        SAMPLING_INTERVAL_MINUTES,
    )
    from backend.models import Sensor, TelemetryEvent, Machine
except ImportError:
    from generators.telemetry_constants import (
        QUALITY_NORMAL,
        QUALITY_SENSOR_FAULT,
        QUALITY_INVALID,
        QUALITY_MISSING,
        SENSOR_PHYSICS_PROFILES,
        SAMPLING_INTERVAL_MINUTES,
    )
    from models import Sensor, TelemetryEvent, Machine


# Standard Lookback Windows
LOOKBACK_WINDOWS: Dict[str, int] = {
    "6h": 6,
    "24h": 24,
    "7d": 168,
}

# Maximum gap allowed between consecutive readings before flagging a data gap (minutes)
DEFAULT_MAX_GAP_MINUTES: float = 120.0  # 4 intervals of 30-min sampling
MIN_READINGS_FOR_TREND: int = 2


@dataclass
class SensorReading:
    """Standardized telemetry reading representation."""

    sensor_id: int
    recorded_at: datetime
    value: Optional[float]
    quality_status: str = QUALITY_NORMAL
    sensor_type: Optional[str] = None
    sensor_code: Optional[str] = None


@dataclass
class SensorReliability:
    """Instrumentation quality and data integrity indicators for a sensor over a window."""

    total_readings: int = 0
    normal_count: int = 0
    missing_count: int = 0
    invalid_count: int = 0
    sensor_fault_count: int = 0
    normal_rate: float = 0.0
    fault_rate: float = 0.0
    missing_rate: float = 0.0
    invalid_rate: float = 0.0
    has_long_gap: bool = False
    max_gap_minutes: float = 0.0
    reliability_score: float = 100.0  # 0.0 to 100.0
    is_reliable: bool = True


@dataclass
class SensorWindowFeatures:
    """Extracted statistical and reliability features for a sensor over a specific window."""

    window_name: str
    window_hours: int
    sensor_id: int
    sensor_type: str
    sensor_code: str
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    trend_slope: Optional[float] = None  # Rate of change per hour
    count_normal: int = 0
    reliability: SensorReliability = field(default_factory=SensorReliability)
    is_sufficient: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert feature data to structured dictionary."""
        return {
            "window_name": self.window_name,
            "window_hours": self.window_hours,
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "sensor_code": self.sensor_code,
            "mean": self.mean,
            "std": self.std,
            "min": self.min,
            "max": self.max,
            "trend_slope": self.trend_slope,
            "count_normal": self.count_normal,
            "is_sufficient": self.is_sufficient,
            "reliability": {
                "total_readings": self.reliability.total_readings,
                "normal_count": self.reliability.normal_count,
                "missing_count": self.reliability.missing_count,
                "invalid_count": self.reliability.invalid_count,
                "sensor_fault_count": self.reliability.sensor_fault_count,
                "normal_rate": round(self.reliability.normal_rate, 4),
                "fault_rate": round(self.reliability.fault_rate, 4),
                "missing_rate": round(self.reliability.missing_rate, 4),
                "invalid_rate": round(self.reliability.invalid_rate, 4),
                "has_long_gap": self.reliability.has_long_gap,
                "max_gap_minutes": round(self.reliability.max_gap_minutes, 2),
                "reliability_score": round(self.reliability.reliability_score, 2),
                "is_reliable": self.reliability.is_reliable,
            },
        }


@dataclass
class MachineAggregatedFeatures:
    """Machine-level aggregation of multi-sensor features across lookback windows."""

    machine_id: int
    machine_code: str
    prediction_timestamp: datetime
    # Structure: windows[window_name][sensor_type] -> SensorWindowFeatures
    windows: Dict[str, Dict[str, SensorWindowFeatures]] = field(default_factory=dict)
    overall_sensor_reliability: float = 100.0  # 0.0 to 100.0
    faulty_sensor_count: int = 0
    sensors_monitored: List[str] = field(default_factory=list)
    has_insufficient_data: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert aggregated features to dictionary representation."""
        windows_dict: Dict[str, Dict[str, Any]] = {}
        for w_name, s_map in self.windows.items():
            windows_dict[w_name] = {s_type: feat.to_dict() for s_type, feat in s_map.items()}

        return {
            "machine_id": self.machine_id,
            "machine_code": self.machine_code,
            "prediction_timestamp": self.prediction_timestamp.isoformat(),
            "overall_sensor_reliability": round(self.overall_sensor_reliability, 2),
            "faulty_sensor_count": self.faulty_sensor_count,
            "sensors_monitored": self.sensors_monitored,
            "has_insufficient_data": self.has_insufficient_data,
            "windows": windows_dict,
            "metadata": self.metadata,
        }


def compute_linear_trend_slope(
    timestamps: List[datetime], values: List[float]
) -> float:
    """
    Computes linear regression trend/slope (change in value per hour) using ordinary least squares.
    Returns 0.0 if fewer than MIN_READINGS_FOR_TREND points are present or variance in time is zero.
    """
    if len(values) < MIN_READINGS_FOR_TREND or len(timestamps) != len(values):
        return 0.0

    t_0 = min(timestamps)
    # Convert timestamps to hours elapsed from earliest timestamp in window
    t_hours = np.array([(t - t_0).total_seconds() / 3600.0 for t in timestamps], dtype=float)
    y_vals = np.array(values, dtype=float)

    t_var = float(np.var(t_hours))
    if t_var < 1e-9:
        return 0.0

    covariance = float(np.cov(t_hours, y_vals)[0, 1])
    slope = covariance / t_var
    return float(slope)


def compute_sensor_reliability(
    readings: List[SensorReading],
    max_gap_threshold_minutes: float = DEFAULT_MAX_GAP_MINUTES,
) -> SensorReliability:
    """
    Evaluates sensor instrumentation reliability and data completeness over a window of readings.
    Identifies missing, invalid, and sensor-fault readings, as well as temporal data gaps.
    """
    total = len(readings)
    if total == 0:
        return SensorReliability(
            total_readings=0,
            normal_count=0,
            missing_count=0,
            invalid_count=0,
            sensor_fault_count=0,
            normal_rate=0.0,
            fault_rate=0.0,
            missing_rate=0.0,
            invalid_rate=0.0,
            has_long_gap=True,
            max_gap_minutes=0.0,
            reliability_score=0.0,
            is_reliable=False,
        )

    normal_count = sum(1 for r in readings if r.quality_status == QUALITY_NORMAL and r.value is not None)
    missing_count = sum(1 for r in readings if r.quality_status == QUALITY_MISSING or r.value is None)
    invalid_count = sum(1 for r in readings if r.quality_status == QUALITY_INVALID)
    fault_count = sum(1 for r in readings if r.quality_status == QUALITY_SENSOR_FAULT)

    normal_rate = normal_count / total
    missing_rate = missing_count / total
    invalid_rate = invalid_count / total
    fault_rate = fault_count / total

    # Check temporal gaps without forward-filling
    sorted_readings = sorted(readings, key=lambda r: r.recorded_at)
    max_gap = 0.0
    for i in range(len(sorted_readings) - 1):
        gap = (sorted_readings[i + 1].recorded_at - sorted_readings[i].recorded_at).total_seconds() / 60.0
        if gap > max_gap:
            max_gap = gap

    has_long_gap = max_gap > max_gap_threshold_minutes

    # Score calculation: base 100 scaled by normal rate, penalized heavily by active faults and invalids
    penalty = (fault_rate * 60.0) + (invalid_rate * 40.0) + (missing_rate * 20.0)
    if has_long_gap:
        penalty += 15.0
    reliability_score = max(0.0, min(100.0, (normal_rate * 100.0) - penalty))

    # Sensor considered reliable for machine condition analysis if fault rate is low and score >= 60
    is_reliable = (
        reliability_score >= 60.0
        and fault_rate <= 0.15
        and invalid_rate <= 0.15
        and normal_count >= 2
    )

    return SensorReliability(
        total_readings=total,
        normal_count=normal_count,
        missing_count=missing_count,
        invalid_count=invalid_count,
        sensor_fault_count=fault_count,
        normal_rate=normal_rate,
        fault_rate=fault_rate,
        missing_rate=missing_rate,
        invalid_rate=invalid_rate,
        has_long_gap=has_long_gap,
        max_gap_minutes=max_gap,
        reliability_score=reliability_score,
        is_reliable=is_reliable,
    )


def compute_window_sensor_features(
    readings: List[SensorReading],
    window_name: str,
    window_hours: int,
    sensor_id: int,
    sensor_type: str,
    sensor_code: str,
    max_gap_threshold_minutes: float = DEFAULT_MAX_GAP_MINUTES,
) -> SensorWindowFeatures:
    """
    Computes statistical features and separate reliability indicators for a single sensor window.
    Strictly uses ONLY normal readings for machine condition statistics (mean, std, min, max, trend).
    """
    reliability = compute_sensor_reliability(readings, max_gap_threshold_minutes)

    # Filter normal quality readings with non-null values
    normal_readings = [
        r for r in readings
        if r.quality_status == QUALITY_NORMAL and r.value is not None
    ]

    count_normal = len(normal_readings)
    is_sufficient = count_normal >= 2

    if not is_sufficient:
        # Handle empty or insufficient windows safely without throwing unhandled exceptions
        mean_val = float(normal_readings[0].value) if count_normal == 1 else None
        return SensorWindowFeatures(
            window_name=window_name,
            window_hours=window_hours,
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            sensor_code=sensor_code,
            mean=round(mean_val, 4) if mean_val is not None else None,
            std=0.0 if count_normal == 1 else None,
            min=round(mean_val, 4) if mean_val is not None else None,
            max=round(mean_val, 4) if mean_val is not None else None,
            trend_slope=0.0 if count_normal == 1 else None,
            count_normal=count_normal,
            reliability=reliability,
            is_sufficient=is_sufficient,
        )

    # Extract values and timestamps
    values = [float(r.value) for r in normal_readings]
    timestamps = [r.recorded_at for r in normal_readings]

    mean_val = float(np.mean(values))
    std_val = float(np.std(values, ddof=1)) if count_normal > 1 else 0.0
    min_val = float(np.min(values))
    max_val = float(np.max(values))
    trend_val = compute_linear_trend_slope(timestamps, values)

    return SensorWindowFeatures(
        window_name=window_name,
        window_hours=window_hours,
        sensor_id=sensor_id,
        sensor_type=sensor_type,
        sensor_code=sensor_code,
        mean=round(mean_val, 4),
        std=round(std_val, 4),
        min=round(min_val, 4),
        max=round(max_val, 4),
        trend_slope=round(trend_val, 5),
        count_normal=count_normal,
        reliability=reliability,
        is_sufficient=True,
    )


class FeatureEngineeringService:
    """
    Feature engineering service for industrial machines and telemetry streams.
    Extracts rolling window statistics with strict anti-leakage guards.
    """

    def __init__(
        self,
        windows: Optional[Dict[str, int]] = None,
        max_gap_minutes: float = DEFAULT_MAX_GAP_MINUTES,
    ):
        self.windows = windows or LOOKBACK_WINDOWS
        self.max_gap_minutes = max_gap_minutes

    def extract_machine_features(
        self,
        machine_id: int,
        machine_code: str,
        readings: List[SensorReading],
        prediction_timestamp: datetime,
        failure_time_cutoff: Optional[datetime] = None,
    ) -> MachineAggregatedFeatures:
        """
        Extract multi-window features for all sensors on a machine.

        Anti-leakage guards enforced:
        - Strict cutoff: Only readings with recorded_at < prediction_timestamp are included.
        - If failure_time_cutoff is specified, recorded_at < failure_time_cutoff is also strictly enforced.
        - Terminal and post-failure observations are strictly excluded.
        - No failure labels or maintenance work-order properties are accessed.
        """
        if prediction_timestamp.tzinfo is None:
            prediction_timestamp = prediction_timestamp.replace(tzinfo=timezone.utc)

        effective_cutoff = prediction_timestamp
        if failure_time_cutoff is not None:
            if failure_time_cutoff.tzinfo is None:
                failure_time_cutoff = failure_time_cutoff.replace(tzinfo=timezone.utc)
            if effective_cutoff > failure_time_cutoff:
                effective_cutoff = failure_time_cutoff

        # Strict cutoff filter
        filtered_readings = [
            r for r in readings
            if (r.recorded_at.replace(tzinfo=timezone.utc) if r.recorded_at.tzinfo is None else r.recorded_at) < effective_cutoff
        ]

        # Group readings by sensor
        readings_by_sensor: Dict[int, List[SensorReading]] = defaultdict(list)
        sensor_info: Dict[int, Tuple[str, str]] = {}  # sensor_id -> (sensor_type, sensor_code)

        for r in filtered_readings:
            readings_by_sensor[r.sensor_id].append(r)
            if r.sensor_id not in sensor_info:
                sensor_info[r.sensor_id] = (
                    r.sensor_type or "Unknown",
                    r.sensor_code or f"SNS-{r.sensor_id:04d}",
                )

        aggregated_windows: Dict[str, Dict[str, SensorWindowFeatures]] = {}
        reliability_scores: List[float] = []
        faulty_sensors: set = set()
        sensors_monitored: List[str] = sorted(list({s_type for s_type, _ in sensor_info.values()}))

        # Compute features for each window
        for w_name, w_hours in self.windows.items():
            window_start = effective_cutoff - timedelta(hours=w_hours)
            aggregated_windows[w_name] = {}

            for s_id, s_readings in readings_by_sensor.items():
                s_type, s_code = sensor_info[s_id]

                # Filter window slice
                window_slice = [
                    r for r in s_readings
                    if (r.recorded_at.replace(tzinfo=timezone.utc) if r.recorded_at.tzinfo is None else r.recorded_at) >= window_start
                ]

                features = compute_window_sensor_features(
                    readings=window_slice,
                    window_name=w_name,
                    window_hours=w_hours,
                    sensor_id=s_id,
                    sensor_type=s_type,
                    sensor_code=s_code,
                    max_gap_threshold_minutes=self.max_gap_minutes,
                )

                aggregated_windows[w_name][s_type] = features

                # Track reliability from the 24h window (or 6h if 24h empty)
                if w_name == "24h":
                    reliability_scores.append(features.reliability.reliability_score)
                    if not features.reliability.is_reliable or features.reliability.fault_rate > 0.15:
                        faulty_sensors.add(s_id)

        overall_rel = float(np.mean(reliability_scores)) if reliability_scores else 0.0
        has_insufficient = len(filtered_readings) == 0 or all(
            not f.is_sufficient for w in aggregated_windows.values() for f in w.values()
        )

        return MachineAggregatedFeatures(
            machine_id=machine_id,
            machine_code=machine_code,
            prediction_timestamp=prediction_timestamp,
            windows=aggregated_windows,
            overall_sensor_reliability=overall_rel,
            faulty_sensor_count=len(faulty_sensors),
            sensors_monitored=sensors_monitored,
            has_insufficient_data=has_insufficient,
            metadata={
                "total_readings_available": len(filtered_readings),
                "effective_cutoff": effective_cutoff.isoformat(),
                "windows_computed": list(self.windows.keys()),
            },
        )

    def extract_features_from_db(
        self,
        session: Session,
        machine_id: int,
        prediction_timestamp: datetime,
        failure_time_cutoff: Optional[datetime] = None,
    ) -> MachineAggregatedFeatures:
        """
        Queries telemetry events directly from the database for a machine and computes features.
        Respects strict cutoff and lookback window limits (7-day maximum query horizon).
        """
        if prediction_timestamp.tzinfo is None:
            prediction_timestamp = prediction_timestamp.replace(tzinfo=timezone.utc)

        max_lookback_hours = max(self.windows.values())
        query_start = prediction_timestamp - timedelta(hours=max_lookback_hours)

        effective_cutoff = prediction_timestamp
        if failure_time_cutoff is not None:
            if failure_time_cutoff.tzinfo is None:
                failure_time_cutoff = failure_time_cutoff.replace(tzinfo=timezone.utc)
            if effective_cutoff > failure_time_cutoff:
                effective_cutoff = failure_time_cutoff

        # Fetch machine details
        machine = session.query(Machine).filter(Machine.machine_id == machine_id).first()
        machine_code = machine.machine_code if machine else f"MCH-{machine_id:03d}"

        # Anti-leakage: Telemetry strictly before cutoff
        stmt = (
            select(
                TelemetryEvent.sensor_id,
                TelemetryEvent.recorded_at,
                TelemetryEvent.value,
                TelemetryEvent.quality_status,
                Sensor.sensor_type,
                Sensor.sensor_code,
            )
            .join(Sensor, TelemetryEvent.sensor_id == Sensor.sensor_id)
            .where(
                Sensor.machine_id == machine_id,
                TelemetryEvent.recorded_at < effective_cutoff,  # Strict inequality
                TelemetryEvent.recorded_at >= query_start,
            )
            .order_by(TelemetryEvent.recorded_at.asc())
        )

        rows = session.execute(stmt).all()

        readings: List[SensorReading] = [
            SensorReading(
                sensor_id=r[0],
                recorded_at=r[1],
                value=float(r[2]) if r[2] is not None else None,
                quality_status=str(r[3]),
                sensor_type=str(r[4]),
                sensor_code=str(r[5]),
            )
            for r in rows
        ]

        return self.extract_machine_features(
            machine_id=machine_id,
            machine_code=machine_code,
            readings=readings,
            prediction_timestamp=prediction_timestamp,
            failure_time_cutoff=failure_time_cutoff,
        )
