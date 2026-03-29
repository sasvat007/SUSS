"""
Risk Detection Engine - Version 0.0.1

Detects and analyzes cash flow risks by simulating multiple scenarios.

Main entry point: detect_risks()
"""

from .engine import detect_risks
from .models import (
    RiskSeverity,
    UncertaintyLevel,
    CriticalRiskDate,
    RiskProjection,
    ScenarioComparison,
    RiskDetectionResult,
    ScenarioConfig,
    BEST_CASE_CONFIG,
    BASE_CASE_CONFIG,
    WORST_CASE_CONFIG,
)

__version__ = "0.0.1"
__all__ = [
    "detect_risks",
    "RiskSeverity",
    "UncertaintyLevel",
    "CriticalRiskDate",
    "RiskProjection",
    "ScenarioComparison",
    "RiskDetectionResult",
    "ScenarioConfig",
    "BEST_CASE_CONFIG",
    "BASE_CASE_CONFIG",
    "WORST_CASE_CONFIG",
]
