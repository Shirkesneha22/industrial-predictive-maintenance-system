"""
Anomaly Detection Service for Industrial Predictive Maintenance System.

Detects unusual sensor behavior across rolling telemetry windows.
Enforces physical and domain integrity:
- Distinguishes isolated sensor instrumentation faults from correlated multi-sensor degradation.
- Prevents a single faulty or anomalous sensor from creating a machine failure alert.
- Provides human-interpretable and structured explanations for each anomaly.
- Uses configurable statistical and physical thresholds.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from backend.generators.telemetry_constants import (
        SENSOR_PHYSICS_PROFILES,
        QUALITY_NORMAL,
        QUALITY_SENSOR_FAULT,
        QUALITY_INVALID,
    )
    from backend.services.feature_engineering import (
        MachineAggregatedFeatures,
        SensorWindowFeatures,
    )
except ImportError:
    from generators.telemetry_constants import (
        SENSOR_PHYSICS_PROFILES,
        QUALITY_NORMAL,
        QUALITY_SENSOR_FAULT,
        QUALITY_INVALID,
    )
    from services.feature_engineering import (
        MachineAggregatedFeatures,
        SensorWindowFeatures,
    )


class AnomalyCategory(str, Enum):
    """Categorical classification of detected sensor behavior."""

    NORMAL = "normal"
    SENSOR_FAULT = "sensor_fault"
    ISOLATED_ANOMALY = "isolated_anomaly"
    CORRELATED_DEGRADATION = "correlated_degradation"


# Sensor Physical Correlation Groups:
# Sensors that naturally co-vary during progressive mechanical failure modes.
PHYSICAL_CORRELATION_GROUPS: List[Set[str]] = [
    # Mechanical Spindle & Rotor Wear (Bearing wear, rotor imbalance)
    {"Vibration", "Acoustic", "Temperature"},
    # Electrical Drive & Coupling (Motor binding, electrical overload)
    {"Current", "Temperature", "Vibration"},
    # Fluid Power Circuit (Hydraulic leaks, cavitation, seal blowout)
    {"Pressure", "Acoustic", "Temperature"},
]


@dataclass
class AnomalyDetectorConfig:
    """Configurable detection thresholds and physical parameters."""

    z_warning_threshold: float = 2.5
    z_critical_threshold: float = 4.0
    trend_warning_threshold: float = 0.08  # change per hour
    fault_rate_threshold: float = 0.15
    min_readings_required: int = 3
    primary_window: str = "24h"
    trend_window: str = "6h"


@dataclass
class SensorAnomalyReport:
    """Detailed anomaly report for a single sensor."""

    sensor_id: int
    sensor_type: str
    sensor_code: str
    is_anomaly: bool
    category: AnomalyCategory
    severity_score: float  # 0.0 to 1.0
    observed_mean: Optional[float]
    nominal_mean: float
    nominal_std: float
    z_score: float
    trend_slope: float
    is_instrumentation_fault: bool
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary format."""
        return {
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "sensor_code": self.sensor_code,
            "is_anomaly": self.is_anomaly,
            "category": self.category.value,
            "severity_score": round(self.severity_score, 4),
            "observed_mean": self.observed_mean,
            "nominal_mean": self.nominal_mean,
            "nominal_std": self.nominal_std,
            "z_score": round(self.z_score, 3),
            "trend_slope": round(self.trend_slope, 4),
            "is_instrumentation_fault": self.is_instrumentation_fault,
            "explanation": self.explanation,
        }


@dataclass
class MachineAnomalyReport:
    """Consolidated machine-level anomaly assessment distinguishing faults from real degradation."""

    machine_id: int
    machine_code: str
    has_correlated_degradation: bool
    has_isolated_sensor_fault: bool
    correlated_sensor_types: List[str] = field(default_factory=list)
    isolated_sensor_types: List[str] = field(default_factory=list)
    sensor_reports: Dict[str, SensorAnomalyReport] = field(default_factory=dict)
    explanations: List[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert machine report to dictionary format."""
        return {
            "machine_id": self.machine_id,
            "machine_code": self.machine_code,
            "has_correlated_degradation": self.has_correlated_degradation,
            "has_isolated_sensor_fault": self.has_isolated_sensor_fault,
            "correlated_sensor_types": self.correlated_sensor_types,
            "isolated_sensor_types": self.isolated_sensor_types,
            "sensor_reports": {
                s_type: r.to_dict() for s_type, r in self.sensor_reports.items()
            },
            "explanations": self.explanations,
            "summary": self.summary,
        }


class AnomalyDetector:
    """
    Evaluates multi-sensor feature snapshots to identify anomalous mechanical degradation
    while filtering out isolated instrumentation faults.
    """

    def __init__(self, config: Optional[AnomalyDetectorConfig] = None):
        self.config = config or AnomalyDetectorConfig()

    def evaluate_sensor_deviation(
        self,
        features: SensorWindowFeatures,
        acute_features: Optional[SensorWindowFeatures] = None,
    ) -> Tuple[bool, bool, float, float, float, str]:
        """
        Calculates deviation against physics nominal profiles.

        Returns:
            (is_elevated, is_fault, z_score, severity, slope, reason)
        """
        sensor_type = features.sensor_type
        physics = SENSOR_PHYSICS_PROFILES.get(
            sensor_type,
            {"nominal_mean": 0.0, "nominal_std": 1.0, "unit": ""},
        )
        nom_mean = physics.get("nominal_mean", 0.0)
        nom_std = physics.get("nominal_std", 1.0)
        if nom_std <= 0:
            nom_std = 1.0

        rel = features.reliability

        # Check for instrumentation fault
        is_fault = (
            rel.fault_rate >= self.config.fault_rate_threshold
            or rel.invalid_rate >= self.config.fault_rate_threshold
            or not rel.is_reliable
            or rel.sensor_fault_count >= 2
        )

        if is_fault:
            reason = (
                f"Sensor fault detected on {sensor_type} ({features.sensor_code}): "
                f"{rel.sensor_fault_count} faults ({round(rel.fault_rate * 100, 1)}%), "
                f"{rel.invalid_count} invalids ({round(rel.invalid_rate * 100, 1)}%). "
                f"Reliability score is {round(rel.reliability_score, 1)}/100."
            )
            return False, True, 0.0, min(1.0, rel.fault_rate * 2.0), 0.0, reason

        if features.mean is None or features.count_normal < self.config.min_readings_required:
            return False, False, 0.0, 0.0, 0.0, f"Insufficient valid readings for {sensor_type}."

        obs_mean = features.mean
        slope = acute_features.trend_slope if (acute_features and acute_features.trend_slope is not None) else (features.trend_slope or 0.0)

        # For pressure, a severe DROP is the degradation indicator (e.g. hydraulic leak)
        if sensor_type == "Pressure":
            z_score = (nom_mean - obs_mean) / nom_std
        else:
            z_score = (obs_mean - nom_mean) / nom_std

        # Determine if physical deviation warrants elevation
        is_elevated = (
            z_score >= self.config.z_warning_threshold
            or (z_score >= 1.8 and slope > self.config.trend_warning_threshold)
        )

        # Compute severity 0.0 to 1.0
        severity = 0.0
        if z_score > 0:
            severity = min(1.0, z_score / self.config.z_critical_threshold)

        if is_elevated:
            direction = "drop" if sensor_type == "Pressure" else "elevation"
            reason = (
                f"{sensor_type} demonstrates abnormal {direction}: observed mean {obs_mean:.2f} "
                f"(nominal {nom_mean:.2f} ± {nom_std:.2f}, z-score {z_score:.2f}) with trend {slope:+.4f}/hr."
            )
        else:
            reason = f"{sensor_type} operating within expected nominal parameters (z-score {z_score:.2f})."

        return is_elevated, False, z_score, severity, slope, reason

    def detect_machine_anomalies(
        self, machine_features: MachineAggregatedFeatures
    ) -> MachineAnomalyReport:
        """
        Executes multi-sensor anomaly detection across machine sensors.
        Differentiates isolated sensor faults from correlated multi-sensor degradation.
        """
        w_primary = machine_features.windows.get(self.config.primary_window, {})
        w_acute = machine_features.windows.get(self.config.trend_window, {})

        sensor_evaluations: Dict[str, Dict[str, Any]] = {}
        elevated_sensor_types: List[str] = []
        fault_sensor_types: List[str] = []

        # Step 1: Evaluate each sensor individually
        for s_type, feat in w_primary.items():
            acute_feat = w_acute.get(s_type)
            is_elevated, is_fault, z_score, severity, slope, reason = self.evaluate_sensor_deviation(
                feat, acute_feat
            )
            physics = SENSOR_PHYSICS_PROFILES.get(s_type, {"nominal_mean": 0.0, "nominal_std": 1.0})

            sensor_evaluations[s_type] = {
                "features": feat,
                "is_elevated": is_elevated,
                "is_fault": is_fault,
                "z_score": z_score,
                "severity": severity,
                "slope": slope,
                "reason": reason,
                "nominal_mean": physics.get("nominal_mean", 0.0),
                "nominal_std": physics.get("nominal_std", 1.0),
            }

            if is_elevated:
                elevated_sensor_types.append(s_type)
            if is_fault:
                fault_sensor_types.append(s_type)

        # Step 2: Multi-sensor physical correlation check
        # Anomaly is considered genuine machine degradation ONLY if multiple correlated sensors agree.
        correlated_sensors: Set[str] = set()
        elevated_set = set(elevated_sensor_types)

        if len(elevated_set) >= 2:
            for group in PHYSICAL_CORRELATION_GROUPS:
                intersection = group.intersection(elevated_set)
                if len(intersection) >= 2:
                    correlated_sensors.update(intersection)

        isolated_elevated_sensors = [s for s in elevated_sensor_types if s not in correlated_sensors]

        # Step 3: Construct individual SensorAnomalyReports
        sensor_reports: Dict[str, SensorAnomalyReport] = {}
        machine_explanations: List[str] = []

        for s_type, eval_info in sensor_evaluations.items():
            feat: SensorWindowFeatures = eval_info["features"]
            is_fault = eval_info["is_fault"]
            is_elevated = eval_info["is_elevated"]
            z_score = eval_info["z_score"]
            severity = eval_info["severity"]
            slope = eval_info["slope"]
            base_reason = eval_info["reason"]

            if is_fault:
                cat = AnomalyCategory.SENSOR_FAULT
                explanation = (
                    f"[Instrumentation Reliability Warning] {base_reason} "
                    f"Machine physical baseline remains independent."
                )
                machine_explanations.append(explanation)
            elif s_type in correlated_sensors:
                cat = AnomalyCategory.CORRELATED_DEGRADATION
                peers = [p for p in correlated_sensors if p != s_type]
                explanation = (
                    f"[Correlated Machine Degradation] {base_reason} "
                    f"Corroborated by physical co-variance with: {', '.join(peers)}."
                )
                machine_explanations.append(explanation)
            elif s_type in isolated_elevated_sensors:
                cat = AnomalyCategory.ISOLATED_ANOMALY
                explanation = (
                    f"[Isolated Sensor Anomaly] {base_reason} "
                    f"No corroborating elevation observed on adjacent physical sensors. "
                    f"Filtered to prevent false machine alert."
                )
                machine_explanations.append(explanation)
            else:
                cat = AnomalyCategory.NORMAL
                explanation = base_reason

            sensor_reports[s_type] = SensorAnomalyReport(
                sensor_id=feat.sensor_id,
                sensor_type=s_type,
                sensor_code=feat.sensor_code,
                is_anomaly=(cat != AnomalyCategory.NORMAL),
                category=cat,
                severity_score=severity,
                observed_mean=feat.mean,
                nominal_mean=eval_info["nominal_mean"],
                nominal_std=eval_info["nominal_std"],
                z_score=z_score,
                trend_slope=slope,
                is_instrumentation_fault=is_fault,
                explanation=explanation,
            )

        has_correlated = len(correlated_sensors) >= 2
        has_isolated_fault = len(fault_sensor_types) > 0 or len(isolated_elevated_sensors) > 0

        # Formulate consolidated machine summary
        if has_correlated:
            summary = (
                f"Multi-sensor progressive degradation confirmed across {sorted(list(correlated_sensors))}. "
                f"Physical co-variance indicates asset wear."
            )
        elif has_isolated_fault:
            summary = (
                f"Isolated sensor anomaly/fault detected on "
                f"{sorted(fault_sensor_types + isolated_elevated_sensors)}. "
                f"Machine mechanical condition stable; sensor inspection advised."
            )
        else:
            summary = "All monitored sensors operating within normal nominal parameters."

        return MachineAnomalyReport(
            machine_id=machine_features.machine_id,
            machine_code=machine_features.machine_code,
            has_correlated_degradation=has_correlated,
            has_isolated_sensor_fault=has_isolated_fault,
            correlated_sensor_types=sorted(list(correlated_sensors)),
            isolated_sensor_types=sorted(isolated_elevated_sensors + fault_sensor_types),
            sensor_reports=sensor_reports,
            explanations=machine_explanations,
            summary=summary,
        )
