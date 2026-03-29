"""
Explainability Engine Models

Data structures for generating human-readable explanations of payment decisions.
Exposes business-level insights without revealing algorithm internals.

These models are designed to:
- Provide transparency for all 9 payment strategies
- Explain decision rationale in business terms
- Show trade-offs between alternative approaches
- Maintain deterministic generation (no AI randomness)

Version: 0.0.1
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime


class UrgencyLevel(Enum):
    """Business-level urgency classification."""
    CRITICAL = "CRITICAL"  # Due today or overdue
    HIGH = "HIGH"  # Due within 1 week
    MEDIUM = "MEDIUM"  # Due within 1 month
    LOW = "LOW"  # Due > 1 month away


class PenaltyRiskLevel(Enum):
    """Business-level penalty risk classification."""
    CRITICAL = "CRITICAL"  # Penalties accrue daily, high rate (Tax, Payroll, Loans)
    HIGH = "HIGH"  # Significant penalties, moderate rate (Utilities, Insurance)
    MEDIUM = "MEDIUM"  # Modest penalties (Suppliers with contracts)
    LOW = "LOW"  # Minimal or no penalties (Flexible suppliers)


class VendorImpactLevel(Enum):
    """Relationship impact of payment decision."""
    CRITICAL = "CRITICAL"  # Core vendor, long-term relationship (>3 years)
    HIGH = "HIGH"  # Important vendor, established (1-3 years)
    MEDIUM = "MEDIUM"  # New or moderate vendor (<1 year)
    LOW = "LOW"  # One-time or minimal relationship


@dataclass
class ExplanationFactors:
    """
    Business-level factors for a single obligation decision.
    
    This model extracts key business considerations WITHOUT exposing the
    underlying scoring algorithm (weights, formula components, etc).
    
    Attributes:
        obligation_id: ID of the obligation
        vendor_name: Vendor/creditor name
        category: Obligation category (Tax, Loan, Payroll, etc)
        amount: Original obligation amount
        
        urgency_level: CRITICAL/HIGH/MEDIUM/LOW (days to due)
        days_to_due: Number of days until due
        days_overdue: If negative days_to_due, how many days overdue
        
        penalty_risk_level: CRITICAL/HIGH/MEDIUM/LOW (penalty accrual rate)
        estimated_penalty: Estimated penalty if delayed one week/month
        penalty_accrual: "Daily", "Fixed", "Tiered" (human-readable)
        
        vendor_impact_level: CRITICAL/HIGH/MEDIUM/LOW (relationship importance)
        vendor_relationship: "Core" / "Established" / "New" (human-readable)
        years_with_vendor: How long business relationship
        
        flexibility_assessment: Can partial payment be made? Yes/No
        partial_payment_allowed: Boolean
        minimum_partial: Minimum amount if partial ({percentage}% or $amount)
        
        cash_impact_summary: String describing cash impact of decision
        survival_risk: String describing risk to survival if delayed
    """
    obligation_id: str
    vendor_name: str
    category: str
    amount: float
    
    urgency_level: UrgencyLevel
    days_to_due: int
    
    penalty_risk_level: PenaltyRiskLevel
    estimated_penalty: float  # Penalty if delayed one week
    penalty_accrual: str  # "Daily 5%", "Fixed $100", "Tiered"
    
    vendor_impact_level: VendorImpactLevel
    vendor_relationship: str  # "Core", "Established", "New"
    
    flexibility_assessment: bool  # Can accept partial payment?
    
    # Fields with defaults
    days_overdue: int = 0
    years_with_vendor: Optional[float] = None
    partial_payment_allowed: bool = False
    minimum_partial: str = ""  # "50% or $X minimum"
    cash_impact_summary: str = ""
    survival_risk: str = ""


@dataclass
class StrategyComparisonRow:
    """
    Trade-off comparison between two strategies for same obligation.
    
    Shows what happens with AGGRESSIVE vs BALANCED vs CONSERVATIVE.
    """
    strategy_name: str  # "Aggressive", "Balanced", "Conservative"
    decision: str  # "Pay $X", "Partial $X", "Delay N days"
    penalty_cost: float  # Estimated additional penalty
    survival_impact: float  # Change in survival probability (%)
    cash_impact: float  # Change in cash after payments
    rationale: str  # Brief explanation of trade-off


@dataclass
class StrategyComparison:
    """
    Comparison of all 3 strategies for a single obligation.
    
    Helps users understand: What if I chose differently?
    """
    obligation_id: str
    vendor_name: str
    comparison_rows: List[StrategyComparisonRow]
    
    def get_trade_off_summary(self, from_strategy: str, to_strategy: str) -> str:
        """Generate natural language summary of trade-off."""
        from_row = next((r for r in self.comparison_rows if r.strategy_name == from_strategy), None)
        to_row = next((r for r in self.comparison_rows if r.strategy_name == to_strategy), None)
        
        if not from_row or not to_row:
            return ""
        
        penalty_diff = to_row.penalty_cost - from_row.penalty_cost
        survival_diff = to_row.survival_impact - from_row.survival_impact
        cash_diff = to_row.cash_impact - from_row.cash_impact
        
        return (
            f"vs {from_strategy}: "
            f"penalty {'+' if penalty_diff > 0 else ''}{penalty_diff:.0f}, "
            f"survival {'+' if survival_diff > 0 else ''}{survival_diff:.1f}%, "
            f"cash {'+' if cash_diff > 0 else ''}{cash_diff:.0f}"
        )


@dataclass
class DecisionExplanation:
    """
    Complete explanation for a single obligation decision.
    
    Answers:
    - WHAT decision was made?
    - WHY was it chosen?
    - What are key business factors?
    - What if alternative strategies chosen?
    """
    obligation_id: str
    vendor_name: str
    category: str
    
    # The decision itself
    decision_status: str  # "Pay in full", "Partial payment", "Delay", "Strategic default"
    pay_amount: float
    
    # Business factors driving decision
    factors: ExplanationFactors
    
    # Narrative explanations
    summary: str  # 1-2 sentence explanation
    decision_rationale: str  # Why this decision was chosen
    implications: str  # What this means for cash, penalties, relationships
    
    # Fields with defaults
    delay_days: int = 0
    comparison: Optional[StrategyComparison] = None
    alternative_scenarios: str = ""  # "If Aggressive: Pay in full ($X), penalty $0 but cash $Y"
    risk_to_decision: str = ""  # Downside risks
    mitigation: str = ""  # Possible mitigations


@dataclass
class StrategyExplanation:
    """
    Complete explanation for one strategy (across all obligations).
    
    Answers:
    - What approach is this strategy?
    - How does it work?
    - What are the trade-offs?
    - How does it compare to alternatives?
    """
    strategy_type: str  # "Aggressive", "Balanced", "Conservative"
    scenario_type: str  # "Best", "Base", "Worst"
    
    # Strategy overview
    summary: str  # 1-2 sentence description
    spending_profile: str  # "Spend 70% of available cash on N obligations"
    approach: str  # How it prioritizes obligations
    
    # Detailed explanations
    obligation_explanations: List[DecisionExplanation]
    
    # Strategy-level metrics & trade-offs
    total_payment: float
    total_penalty_cost: float
    estimated_cash_after: float
    survival_probability: float  # 0-100
    
    # Comparisons to other approaches in same scenario
    key_trade_offs: str  # "vs Aggressive: $X less in payments, +$Y penalty risk, -Z% survival"
    
    # Risk assessment
    strength: str  # What this strategy excels at
    weakness: str  # Where it struggles
    best_for: str  # "Best if you prioritize survival" or "Best if you minimize penalties"
    
    # Decision examples
    highest_priority_items: List[str] = field(default_factory=list)  # Top N obligations paid
    deferred_items: List[str] = field(default_factory=list)  # What's delayed
    
    # Execution guidance
    execution_guidance: str = ""  # Practical steps to implement


@dataclass
class CompleteExplanation:
    """
    Complete explainability output for all 9 strategies.
    
    Top-level explanation model, parallel to DecisionResult3Scenarios.
    Provides full transparency across:
    - All 3 RDE scenarios (Best, Base, Worst)
    - All 3 approaches per scenario (Aggressive, Balanced, Conservative)
    """
    
    # All 9 strategy explanations organized hierarchically
    best_case_explanations: Dict[str, StrategyExplanation]  # {"aggressive": ..., "balanced": ..., "conservative": ...}
    base_case_explanations: Dict[str, StrategyExplanation]
    worst_case_explanations: Dict[str, StrategyExplanation]
    
    # Recommended strategies (from parent DecisionResult)
    recommended_best_case: str  # "Balanced", "Conservative", etc
    recommended_base_case: str
    recommended_worst_case: str
    
    # Cross-scenario guidance
    cross_scenario_summary: str  # Why BASE case is primary recommendation
    scenario_context: str  # "Base case (75% probability) should be primary plan"
    action_recommendation: str  # "Plan for Base case, prepare for Worst case"
    
    # High-level insights (aggregated across all strategies)
    critical_obligations: List[str] = field(default_factory=list)  # Always paid across all strategies
    flexible_obligations: List[str] = field(default_factory=list)  # Vary between strategies
    vendor_critical_relationships: List[str] = field(default_factory=list)  # Must maintain
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    generated_by: str = "ExplainabilityEngine/1.0"
    
    def get_strategy_explanation(self, scenario: str, strategy: str) -> Optional[StrategyExplanation]:
        """Retrieve explanation for specific strategy in scenario."""
        scenario_map = {
            "best": self.best_case_explanations,
            "base": self.base_case_explanations,
            "worst": self.worst_case_explanations,
        }
        
        scenario_dict = scenario_map.get(scenario.lower())
        if not scenario_dict:
            return None
        
        return scenario_dict.get(strategy.lower())
    
    def all_strategy_explanations(self) -> List[StrategyExplanation]:
        """Return all 9 explanations flattened."""
        return (
            list(self.best_case_explanations.values())
            + list(self.base_case_explanations.values())
            + list(self.worst_case_explanations.values())
        )
