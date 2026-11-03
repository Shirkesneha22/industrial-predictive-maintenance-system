"""
Business Logic Services Package.
Contains domain services, feature engineering, anomaly detection algorithms,
and risk assessment engines for industrial predictive maintenance.
"""

from backend.services.feature_engineering import (
    FeatureEngineeringService,
    MachineAggregatedFeatures,
    SensorWindowFeatures,
    SensorReading,
    SensorReliability,
    LOOKBACK_WINDOWS,
)
from backend.services.anomaly_detector import (
    AnomalyDetector,
    AnomalyDetectorConfig,
    AnomalyCategory,
    SensorAnomalyReport,
    MachineAnomalyReport,
)
from backend.services.risk_engine import (
    RiskEngine,
    RiskEngineConfig,
    RiskLevel,
    MachineRiskAssessment,
    ContributingSensorSignal,
)
from backend.services.offline_evaluator import (
    GroundTruthEvent,
    GroundTruthRegistry,
    PointInTimePrediction,
    AlertMatchingPolicy,
    OfflineEvaluationEngine,
    ThresholdMetricPoint,
    ThresholdOptimizationResult,
)

__all__ = [
    "FeatureEngineeringService",
    "MachineAggregatedFeatures",
    "SensorWindowFeatures",
    "SensorReading",
    "SensorReliability",
    "LOOKBACK_WINDOWS",
    "AnomalyDetector",
    "AnomalyDetectorConfig",
    "AnomalyCategory",
    "SensorAnomalyReport",
    "MachineAnomalyReport",
    "RiskEngine",
    "RiskEngineConfig",
    "RiskLevel",
    "MachineRiskAssessment",
    "ContributingSensorSignal",
    "GroundTruthEvent",
    "GroundTruthRegistry",
    "PointInTimePrediction",
    "AlertMatchingPolicy",
    "OfflineEvaluationEngine",
    "ThresholdMetricPoint",
    "ThresholdOptimizationResult",
]
