"""
Data models for the Risk Detection Engine.

Defines data structures for risk scenarios, projections, and comprehensive
risk analysis outputs.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum


class ScenarioType(Enum):
    """Types of risk scenarios."""
    BEST = "best"
    BASE = "base"
    WORST = "worst"


class RiskSeverity(Enum):
    """Risk severity levels."""
    SAFE = "safe"
    CAUTION = "caution"
    WARNING = "warning"
    CRITICAL = "critical"


class UncertaintyLevel(Enum):
    """Uncertainty level between scenarios."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class CriticalRiskDate:
    """
    Marks a critical risk event date in scenario projection.
    
    Attributes:
        date: Date of the critical event (YYYY-MM-DD)
        event_type: Type of event (shortfall, minimum, recovery, zero_cash)
        days_from_today: How many days in the future
        description: Human-readable description
    """
    date: str
    event_type: str  # shortfall, minimum, recovery, zero_cash
    days_from_today: int
    description: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class RiskProjection:
    """
    Risk projection for a single scenario (Best/Base/Worst).
    
    This is the complete risk analysis for one scenario, including timeline,
    critical dates, and severity assessment.
    
    Attributes:
        scenario_type: "best", "base", or "worst"
        simulation_timeline: Day-by-day cash flow events in this scenario
        first_shortfall_date: First date available_cash < 0 (or None)
        days_to_shortfall: Days from today to first shortfall
        minimum_cash_amount: Absolute minimum balance reached
        minimum_cash_date: Date when minimum balance occurs
        days_to_minimum: Days from today to minimum (can be > horizon if no minimum)
        zero_cash_date: Date balance would hit 0 (or None if stays positive)
        total_deficit_days: How many days scenario shows deficit
        max_deficit_amount: Largest negative amount (deficit depth)
        deficit_recovery_date: When deficit returns to positive (or None)
        risk_flags: Boolean flags for various risk conditions
        risk_severity: Overall severity assessment
        risk_summary: Human-readable risk explanation
    """
    scenario_type: str  # "best", "base", "worst"
    simulation_timeline: List[Dict[str, Any]]  # List of CashFlowEvent dicts
    first_shortfall_date: Optional[str]
    days_to_shortfall: Optional[int]
    minimum_cash_amount: float
    minimum_cash_date: str
    days_to_minimum: int
    zero_cash_date: Optional[str]
    total_deficit_days: int
    max_deficit_amount: float
    deficit_recovery_date: Optional[str]
    risk_flags: Dict[str, bool] = field(default_factory=dict)
    risk_severity: str = "safe"
    risk_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class ScenarioComparison:
    """
    Comparison metrics across the three scenarios.
    
    Attributes:
        best_to_base_days_difference: How many more days until shortfall in base vs best
        base_to_worst_days_difference: How many more days until shortfall in worst vs base
        best_to_worst_range: Total span of uncertainty (best vs worst shortfall days)
        uncertainty_level: Classification of uncertainty (low/medium/high)
        scenario_divergence_summary: Description of how scenarios differ
    """
    best_to_base_days_difference: Optional[int]
    base_to_worst_days_difference: Optional[int]
    best_to_worst_range: Optional[int]
    uncertainty_level: str
    scenario_divergence_summary: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class RiskDetectionResult:
    """
    Complete risk detection output combining all three scenarios.
    
    This is the main result object returned by the Risk Detection Engine,
    containing the full analysis across best, base, and worst cases.
    
    Attributes:
        best_case: RiskProjection for best-case scenario
        base_case: RiskProjection for base-case scenario
        worst_case: RiskProjection for worst-case scenario
        scenario_comparison: Metrics comparing across scenarios
        overall_risk_level: Risk level based on worst case
        primary_risk_date: Most urgent critical date to watch
        recommendation: Recommended action based on analysis
        analysis_summary: Executive summary of all findings
        snapshot_date: Date this analysis was generated
        analysis_horizon_days: Number of days forecasted
    """
    best_case: RiskProjection
    base_case: RiskProjection
    worst_case: RiskProjection
    scenario_comparison: ScenarioComparison
    overall_risk_level: str  # "safe", "caution", "warning", "critical
    primary_risk_date: Optional[str]
    recommendation: str
    analysis_summary: str
    snapshot_date: str
    analysis_horizon_days: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Ensure nested objects are converted
        data['best_case'] = self.best_case.to_dict()
        data['base_case'] = self.base_case.to_dict()
        data['worst_case'] = self.worst_case.to_dict()
        data['scenario_comparison'] = self.scenario_comparison.to_dict()
        return data

    def to_json_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return self.to_dict()


@dataclass
class ScenarioConfig:
    """
    Configuration for a scenario type.
    
    Specifies how to adapt FinancialState data for each scenario.
    
    Attributes:
        scenario_type: Type of scenario ("best", "base", "worst")
        use_full_confidence: Whether to use full confidence-weighted amounts
        apply_payment_delays: Whether to shift receivable dates forward
        min_confidence_threshold: Minimum confidence to include receivable (0.0-1.0)
        description: Human-readable description
    """
    scenario_type: str
    use_full_confidence: bool
    apply_payment_delays: bool
    min_confidence_threshold: float
    description: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


# Standard scenario configurations
BEST_CASE_CONFIG = ScenarioConfig(
    scenario_type="best",
    use_full_confidence=True,
    apply_payment_delays=False,
    min_confidence_threshold=0.0,
    description="Best case: All receivables on time at full amounts"
)

BASE_CASE_CONFIG = ScenarioConfig(
    scenario_type="base",
    use_full_confidence=False,
    apply_payment_delays=True,
    min_confidence_threshold=0.0,
    description="Base case: Expected delays applied, all receivables weighted by confidence"
)

WORST_CASE_CONFIG = ScenarioConfig(
    scenario_type="worst",
    use_full_confidence=False,
    apply_payment_delays=True,
    min_confidence_threshold=0.4,
    description="Worst case: Low-confidence receivables excluded, delays applied"
)
