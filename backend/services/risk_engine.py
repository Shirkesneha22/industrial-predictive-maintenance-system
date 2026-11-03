"""
Risk Engine Service for Industrial Predictive Maintenance System.

Implements an explainable, physics-informed, rule-based baseline for predictive maintenance:
- Calculates Machine Health Index (0-100) and Machine Risk Score (0-100).
- Determines Risk Level: Normal, Warning, or Critical using configurable thresholds.
- Identifies contributing sensor signals and dominant failure modes.
- Generates actionable industrial maintenance recommendations.
- Enforces strict anti-leakage principles:
  * Risk scores are engineering indicators, NOT calibrated failure probabilities.
  * Remaining Useful Life (RUL) is not claimed unless genuinely validated (set to None).
  * Isolated sensor faults are isolated to instrumentation maintenance and do not trigger machine failure alerts.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

try:
    from backend.generators.telemetry_constants import SENSOR_PHYSICS_PROFILES
    from backend.services.feature_engineering import (
        MachineAggregatedFeatures,
        SensorWindowFeatures,
    )
    from backend.services.anomaly_detector import (
        AnomalyCategory,
        AnomalyDetector,
        AnomalyDetectorConfig,
        MachineAnomalyReport,
    )
except ImportError:
    from generators.telemetry_constants import SENSOR_PHYSICS_PROFILES
    from services.feature_engineering import (
        MachineAggregatedFeatures,
        SensorWindowFeatures,
    )
    from services.anomaly_detector import (
        AnomalyCategory,
        AnomalyDetector,
        AnomalyDetectorConfig,
        MachineAnomalyReport,
    )


class RiskLevel(str, Enum):
    """Categorical risk severity level."""

    NORMAL = "Normal"
    WARNING = "Warning"
    CRITICAL = "Critical"


@dataclass
class RiskEngineConfig:
    """Configurable decision thresholds and weighting parameters for the Risk Engine."""

    # Risk level boundary thresholds (0-100 scale)
    normal_threshold: float = 35.0   # Risk Score < normal_threshold -> Normal
    critical_threshold: float = 65.0 # Risk Score >= critical_threshold -> Critical (else Warning)

    # Base nominal risk for an operating machine in healthy steady-state
    base_nominal_risk: float = 8.0

    # Risk ceiling for machines where ONLY an isolated sensor fault or isolated uncorroborated spike is present
    single_fault_risk_cap: float = 30.0

    # Minimum valid readings across sensors required for a conclusive risk evaluation
    min_readings_required: int = 2

    # Weight assigned to sensor physical deviation during correlated wear
    sensor_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "Vibration": 1.4,
            "Temperature": 1.2,
            "Acoustic": 1.2,
            "Pressure": 1.3,
            "Current": 1.1,
        }
    )


@dataclass
class ContributingSensorSignal:
    """Structured detail of an individual sensor contributing to the risk assessment."""

    sensor_id: int
    sensor_type: str
    sensor_code: str
    observed_mean: Optional[float]
    nominal_baseline: float
    z_score: float
    trend_slope: float
    weight: float
    risk_contribution: float
    is_fault: bool
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert signal breakdown to dictionary."""
        return {
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "sensor_code": self.sensor_code,
            "observed_mean": self.observed_mean,
            "nominal_baseline": self.nominal_baseline,
            "z_score": round(self.z_score, 3),
            "trend_slope": round(self.trend_slope, 4),
            "weight": self.weight,
            "risk_contribution": round(self.risk_contribution, 2),
            "is_fault": self.is_fault,
            "explanation": self.explanation,
        }


@dataclass
class MachineRiskAssessment:
    """Comprehensive, explainable machine health and risk evaluation output."""

    machine_id: int
    machine_code: str
    health_index: float  # 0.0 to 100.0 (100 = optimal condition)
    risk_score: float    # 0.0 to 100.0 (0 = minimal risk)
    risk_level: RiskLevel
    dominant_failure_mode: Optional[str]
    failure_mode_confidence: float
    contributing_signals: List[ContributingSensorSignal]
    recommended_action: str
    has_isolated_sensor_fault: bool
    has_correlated_degradation: bool
    sensor_reliability_index: float
    # Anti-leakage / Integrity flags
    is_calibrated_probability: bool = False
    remaining_useful_life_hours: Optional[float] = None
    data_status: str = "sufficient"
    explanation_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert assessment result to dictionary."""
        return {
            "machine_id": self.machine_id,
            "machine_code": self.machine_code,
            "health_index": round(self.health_index, 2),
            "risk_score": round(self.risk_score, 2),
            "risk_level": self.risk_level.value,
            "dominant_failure_mode": self.dominant_failure_mode,
            "failure_mode_confidence": round(self.failure_mode_confidence, 2),
            "contributing_signals": [s.to_dict() for s in self.contributing_signals],
            "recommended_action": self.recommended_action,
            "has_isolated_sensor_fault": self.has_isolated_sensor_fault,
            "has_correlated_degradation": self.has_correlated_degradation,
            "sensor_reliability_index": round(self.sensor_reliability_index, 2),
            "is_calibrated_probability": self.is_calibrated_probability,
            "remaining_useful_life_hours": self.remaining_useful_life_hours,
            "data_status": self.data_status,
            "explanation_summary": self.explanation_summary,
        }


class RiskEngine:
    """
    Core Risk Detection and Health Assessment Engine.
    Combines feature extraction and anomaly classification into an explainable asset score.
    """

    def __init__(
        self,
        config: Optional[RiskEngineConfig] = None,
        anomaly_detector: Optional[AnomalyDetector] = None,
    ):
        self.config = config or RiskEngineConfig()
        self.anomaly_detector = anomaly_detector or AnomalyDetector()

    def identify_dominant_failure_mode(
        self,
        contributing_signals: List[ContributingSensorSignal],
        has_correlated_degradation: bool,
    ) -> Tuple[Optional[str], float]:
        """
        Diagnoses the dominant mechanical failure mode based on multi-sensor physics signatures.
        Only identifies a mode when corroborated evidence supports it.
        """
        if not has_correlated_degradation or not contributing_signals:
            return None, 0.0

        z_by_type = {s.sensor_type: max(0.0, s.z_score) for s in contributing_signals}

        z_vib = z_by_type.get("Vibration", 0.0)
        z_temp = z_by_type.get("Temperature", 0.0)
        z_acous = z_by_type.get("Acoustic", 0.0)
        z_press = z_by_type.get("Pressure", 0.0)
        z_curr = z_by_type.get("Current", 0.0)

        mode_scores: Dict[str, float] = {}

        # Mode 1: Bearing Wear & Mechanical Seizure
        # High vibration + high acoustic + moderate temperature
        if z_vib >= 2.0 and z_acous >= 2.0:
            mode_scores["bearing_wear"] = (z_vib * 1.5 + z_acous * 1.3 + z_temp * 0.8) / 3.6

        # Mode 2: Drive Motor Binding
        # High current + high temperature + elevated vibration
        if z_curr >= 2.0 and z_temp >= 1.8:
            mode_scores["motor_binding"] = (z_curr * 1.5 + z_temp * 1.3 + z_vib * 0.8) / 3.6

        # Mode 3: Hydraulic Pressure Loss & Seal Rupture
        # High pressure drop + high acoustic cavitation
        if z_press >= 2.0 and z_acous >= 1.5:
            mode_scores["hydraulic_leak"] = (z_press * 1.6 + z_acous * 1.2 + z_temp * 0.6) / 3.4

        # Mode 4: Thermal Overload & Spindle Overheating
        # Severe temperature rise with mild or secondary vibration
        if z_temp >= 2.5 and z_vib < 3.0:
            mode_scores["thermal_overload"] = (z_temp * 1.8 + z_acous * 0.6 + z_curr * 0.6) / 3.0

        if not mode_scores:
            return None, 0.0

        best_mode, best_raw_score = max(mode_scores.items(), key=lambda item: item[1])
        confidence = min(1.0, max(0.2, best_raw_score / 5.0))
        return best_mode, confidence

    def generate_recommended_action(
        self,
        risk_level: RiskLevel,
        dominant_failure_mode: Optional[str],
        has_isolated_sensor_fault: bool,
        has_correlated_degradation: bool,
        isolated_sensors: List[str],
    ) -> str:
        """
        Generates contextual industrial maintenance actions based on asset risk and physical diagnostics.
        """
        # Case 1: Healthy condition with optional isolated instrumentation fault
        if risk_level == RiskLevel.NORMAL:
            if has_isolated_sensor_fault:
                fault_list = ", ".join(isolated_sensors) if isolated_sensors else "instrumentation"
                return (
                    f"Machine mechanical condition is normal. Dispatch instrumentation technician to "
                    f"inspect cabling, connections, and recalibrate sensor ({fault_list})."
                )
            return "Asset operating within optimal baseline envelope. Continue routine scheduled monitoring."

        # Case 2: Warning Risk Level
        if risk_level == RiskLevel.WARNING:
            if dominant_failure_mode == "bearing_wear":
                return (
                    "Schedule high-frequency vibration spectrum analysis and drive spindle grease "
                    "replenishment within next 48 hours."
                )
            elif dominant_failure_mode == "motor_binding":
                return (
                    "Schedule drive motor current signature analysis (MCSA) and laser shaft alignment "
                    "check during next planned shift turnaround."
                )
            elif dominant_failure_mode == "hydraulic_leak":
                return (
                    "Inspect hydraulic cylinder rod seals, manifold valve blocks, and check accumulator "
                    "charge pressure for signs of leakage."
                )
            elif dominant_failure_mode == "thermal_overload":
                return (
                    "Inspect spindle cooling circuit: check coolant emulsion concentration, flush inline "
                    "strainers, and test thermostatic bypass valve."
                )
            else:
                return (
                    "Elevated mechanical degradation detected across multiple sensor channels. "
                    "Conduct comprehensive physical walkaround and condition audit within 48 hours."
                )

        # Case 3: Critical Risk Level
        if dominant_failure_mode == "bearing_wear":
            return (
                "EMERGENCY ACTION: Schedule immediate controlled machine shutdown. Overhaul spindle "
                "bearings, inspect raceway for spalling, and replace bearing assembly before restart."
            )
        elif dominant_failure_mode == "motor_binding":
            return (
                "EMERGENCY ACTION: Decouple drive motor immediately. Inspect flexible elastomeric "
                "coupling element and check motor winding insulation resistance."
            )
        elif dominant_failure_mode == "hydraulic_leak":
            return (
                "EMERGENCY ACTION: Depressurize hydraulic circuit. Replace blown cylinder rod seals "
                "and damaged Glyd rings; perform 250 bar pressure holding test."
            )
        elif dominant_failure_mode == "thermal_overload":
            return (
                "EMERGENCY ACTION: Halt high-load machining operations. Flush blocked spindle coolant "
                "jacket and replace seized thermal control valve."
            )
        else:
            return (
                "CRITICAL ALERT: Multi-sensor physical degradation has reached critical thresholds. "
                "Initiate immediate supervisory inspection and preventive shutdown."
            )

    def assess_machine_risk(
        self,
        machine_features: MachineAggregatedFeatures,
        anomaly_report: Optional[MachineAnomalyReport] = None,
    ) -> MachineRiskAssessment:
        """
        Computes Machine Health Index, Risk Score, and diagnostic recommendations for a machine.
        """
        # Safe handling of empty windows or insufficient readings
        if machine_features.has_insufficient_data or not machine_features.windows:
            return MachineRiskAssessment(
                machine_id=machine_features.machine_id,
                machine_code=machine_features.machine_code,
                health_index=100.0,
                risk_score=0.0,
                risk_level=RiskLevel.NORMAL,
                dominant_failure_mode=None,
                failure_mode_confidence=0.0,
                contributing_signals=[],
                recommended_action="Insufficient telemetry readings available in lookback window. Awaiting sensor stream ingestion.",
                has_isolated_sensor_fault=False,
                has_correlated_degradation=False,
                sensor_reliability_index=0.0,
                is_calibrated_probability=False,
                remaining_useful_life_hours=None,
                data_status="insufficient_telemetry",
                explanation_summary="No valid telemetry available for risk evaluation.",
            )

        # Run anomaly detection if not pre-computed
        if anomaly_report is None:
            anomaly_report = self.anomaly_detector.detect_machine_anomalies(machine_features)

        has_correlated = anomaly_report.has_correlated_degradation
        has_isolated_fault = anomaly_report.has_isolated_sensor_fault
        correlated_types = set(anomaly_report.correlated_sensor_types)

        contributing_signals: List[ContributingSensorSignal] = []
        raw_risk_accumulation: float = self.config.base_nominal_risk

        # Evaluate signals from the primary 24h window
        primary_w = machine_features.windows.get("24h", {})
        if not primary_w:
            primary_w = next(iter(machine_features.windows.values()))

        for s_type, feat in primary_w.items():
            rep = anomaly_report.sensor_reports.get(s_type)
            if rep is None:
                continue

            weight = self.config.sensor_weights.get(s_type, 1.0)
            z_score = rep.z_score
            slope = rep.trend_slope

            # Only CORRELATED degrading sensors contribute directly to machine failure risk
            risk_contrib = 0.0
            if s_type in correlated_types:
                # Correlated degradation contribution: z-score combined with positive slope
                z_factor = max(0.0, z_score)
                slope_factor = max(0.0, slope * 20.0)
                risk_contrib = (z_factor * 8.5 + slope_factor) * weight
                raw_risk_accumulation += risk_contrib

            contributing_signals.append(
                ContributingSensorSignal(
                    sensor_id=feat.sensor_id,
                    sensor_type=s_type,
                    sensor_code=feat.sensor_code,
                    observed_mean=feat.mean,
                    nominal_baseline=rep.nominal_mean,
                    z_score=z_score,
                    trend_slope=slope,
                    weight=weight,
                    risk_contribution=risk_contrib,
                    is_fault=rep.is_instrumentation_fault,
                    explanation=rep.explanation,
                )
            )

        # Anti-leakage / false alert guard:
        # If there is NO correlated multi-sensor degradation, cap the machine risk score
        # so that a single faulty sensor CANNOT drive machine risk to Warning or Critical.
        if not has_correlated:
            final_risk = min(self.config.single_fault_risk_cap, raw_risk_accumulation)
        else:
            final_risk = min(100.0, max(0.0, raw_risk_accumulation))

        # Determine Risk Level
        if final_risk < self.config.normal_threshold:
            risk_level = RiskLevel.NORMAL
        elif final_risk < self.config.critical_threshold:
            risk_level = RiskLevel.WARNING
        else:
            risk_level = RiskLevel.CRITICAL

        # Machine Health Index (0-100): inverse of risk score, adjusted for instrumentation health
        reliability_factor = machine_features.overall_sensor_reliability / 100.0
        # Condition health is primary (100 - risk), penalized slightly by poor reliability
        condition_health = max(0.0, 100.0 - final_risk)
        health_index = max(0.0, min(100.0, condition_health * (0.85 + 0.15 * reliability_factor)))

        # Diagnose dominant failure mode
        dominant_mode, mode_conf = self.identify_dominant_failure_mode(
            contributing_signals=contributing_signals,
            has_correlated_degradation=has_correlated,
        )

        # Recommended maintenance action
        recommended_action = self.generate_recommended_action(
            risk_level=risk_level,
            dominant_failure_mode=dominant_mode,
            has_isolated_sensor_fault=has_isolated_fault,
            has_correlated_degradation=has_correlated,
            isolated_sensors=anomaly_report.isolated_sensor_types,
        )

        return MachineRiskAssessment(
            machine_id=machine_features.machine_id,
            machine_code=machine_features.machine_code,
            health_index=round(health_index, 2),
            risk_score=round(final_risk, 2),
            risk_level=risk_level,
            dominant_failure_mode=dominant_mode,
            failure_mode_confidence=round(mode_conf, 2),
            contributing_signals=contributing_signals,
            recommended_action=recommended_action,
            has_isolated_sensor_fault=has_isolated_fault,
            has_correlated_degradation=has_correlated,
            sensor_reliability_index=round(machine_features.overall_sensor_reliability, 2),
            is_calibrated_probability=False,
            remaining_useful_life_hours=None,
            data_status="sufficient",
            explanation_summary=anomaly_report.summary,
        )
