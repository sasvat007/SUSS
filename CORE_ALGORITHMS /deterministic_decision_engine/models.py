"""
Deterministic Decision Engine (DDE) Models

Core data structures for the payment decision optimization engine.
Represents penalties, vendor relationships, obligation scores, payment decisions,
and strategies across multiple scenarios (best/base/worst case).

Version: 0.0.1
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, TYPE_CHECKING
from enum import Enum
from datetime import datetime, timedelta

if TYPE_CHECKING:
    from deterministic_decision_engine.explanation_models import CompleteExplanation


class VendorRelationshipType(Enum):
    """Classification of vendor relationships based on tenure and reliability."""
    NEW = "NEW"  # < 1 year, building trust
    EXISTING = "EXISTING"  # 1-3 years, normal business relationship
    CORE = "CORE"  # > 3 years, proven loyal vendor


class StrategyType(Enum):
    """Payment strategy approach across scenarios."""
    AGGRESSIVE = "AGGRESSIVE"  # Maximize payment to reduce risk
    BALANCED = "BALANCED"  # Optimize payment vs survival
    CONSERVATIVE = "CONSERVATIVE"  # Minimize spending to ensure survival


class ScenarioType(Enum):
    """RDE cash flow scenarios replicated in DDE."""
    BEST = "BEST"  # Optimistic cash flow
    BASE = "BASE"  # Most likely cash flow
    WORST = "WORST"  # Pessimistic cash flow


class PaymentStatus(Enum):
    """Status of a payment decision."""
    PAY_IN_FULL = "PAY_IN_FULL"
    PARTIAL_PAY = "PARTIAL_PAY"
    DELAY = "DELAY"
    STRATEGIC_DEFAULT = "STRATEGIC_DEFAULT"  # Defer to improve survival


class PenaltyType(Enum):
    """How penalties accrue over time."""
    DAILY_PERCENTAGE = "DAILY_PERCENTAGE"  # % per day
    FIXED_FLAT = "FIXED_FLAT"  # One-time flat fee
    TIERED = "TIERED"  # Escalates with duration


@dataclass
class PenaltyModel:
    """
    Defines penalty structure for a category of obligations.
    
    Attributes:
        category: Obligation category (e.g., "Tax", "Loan", "Utilities")
        has_penalty: Whether penalties apply for late payment
        penalty_type: How penalties are calculated
        penalty_rate: Base rate (% for daily, $ for flat)
        escalation: Additional penalty for extreme lateness
        max_delay_days: Days after which penalty caps or max delay allowed
        description: Human-readable explanation
    """
    category: str
    has_penalty: bool
    penalty_type: PenaltyType
    penalty_rate: float  # Percentage (5 = 5% daily) or fixed amount
    escalation: float = 0.0  # Additional rate after escalation threshold
    max_delay_days: int = 999  # Practical maximum delay allowed
    description: str = ""


@dataclass
class VendorRelationship:
    """
    Represents the business relationship with a vendor.
    
    Attributes:
        vendor_id: Unique vendor identifier (maps to Payable.creditor_id)
        vendor_name: Human-readable vendor name
        relationship_type: Classification (NEW/EXISTING/CORE)
        years_with_business: How long we've worked with vendor
        payment_reliability: Historical on-time payment rate (0-100)
    """
    vendor_id: str
    vendor_name: str
    relationship_type: VendorRelationshipType
    years_with_business: float
    payment_reliability: float = 50.0  # Default 50% if unknown


@dataclass
class ObligationScore:
    """
    Weighted score for a single obligation (Payable).
    
    Computed as: (Legal×40% + Urgency×30% + Penalty×20% + Relationship×10% - Flexibility×5%) / 100
    Where each component is 0-100 and final score indicates payment priority (higher = pay first).
    
    Attributes:
        obligation_id: ID of the Payable
        legal_risk_score: 0-100, legal/regulatory importance
        urgency_score: 0-100, how soon due (100 = due today)
        penalty_score: 0-100, consequences of lateness
        relationship_score: 0-100, vendor relationship importance
        flexibility_score: 0-100, ability to pay partially or delay
        total_weighted_score: Final composite score (higher = higher priority)
        priority_rank: Rank among all obligations (1 = highest priority)
        category: Obligation category
        vendor_name: Vendor/creditor name
    """
    obligation_id: str
    legal_risk_score: float
    urgency_score: float
    penalty_score: float
    relationship_score: float
    flexibility_score: float
    total_weighted_score: float
    priority_rank: int
    category: str
    vendor_name: str = ""
    days_to_due: int = 0
    original_amount: float = 0.0


@dataclass
class PaymentDecision:
    """
    Decision for a single obligation in a strategy.
    
    Attributes:
        obligation_id: ID of the Payable
        status: Payment action (PAY_IN_FULL/PARTIAL_PAY/DELAY/STRATEGIC_DEFAULT)
        pay_amount: Amount to pay now (0 if DELAY/DEFAULT)
        delay_days: Days to delay payment (0 if paying now)
        potential_penalty: Estimated penalty cost if this decision taken
        rationale: Human-readable reason for decision
        vendor_id: Vendor/creditor ID
        vendor_name: Vendor name
        due_date: Original due date
        category: Obligation category
    """
    obligation_id: str
    status: PaymentStatus
    pay_amount: float
    delay_days: int
    potential_penalty: float
    rationale: str
    vendor_id: str = ""
    vendor_name: str = ""
    due_date: Optional[datetime] = None
    category: str = ""


@dataclass
class PaymentStrategy:
    """
    A complete payment plan (all decisions) for one scenario using one approach.
    
    Attributes:
        strategy_type: Approach (AGGRESSIVE/BALANCED/CONSERVATIVE)
        scenario_type: RDE cash flow scenario (BEST/BASE/WORST)
        decisions: List of PaymentDecisions for each obligation
        total_payment: Sum of all pay_amounts
        total_penalty_cost: Sum of all potential_penalties
        estimated_cash_after: Cash position after all payments
        survival_probability: % chance of staying above minimum buffer
        score: Ranking score (legal_risk + penalties - survival×50)
        timestamp: When strategy was generated
        metadata: Additional context (decision count, affected vendors, etc)
    """
    strategy_type: StrategyType
    scenario_type: ScenarioType
    decisions: List[PaymentDecision]
    total_payment: float
    total_penalty_cost: float
    estimated_cash_after: float
    survival_probability: float  # 0-100
    score: float  # Lower is better
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate strategy fields."""
        if not (0 <= self.total_penalty_cost <= 999_999_999):
            raise ValueError(f"Invalid total_penalty_cost: {self.total_penalty_cost}")
        if not (0 <= self.survival_probability <= 100):
            raise ValueError(f"survival_probability must be 0-100, got {self.survival_probability}")


@dataclass
class DecisionResult:
    """
    All 3 strategies for a single RDE scenario.
    
    Attributes:
        scenario_type: Which scenario (BEST/BASE/WORST)
        aggressive_strategy: AGGRESSIVE approach (maximize payment)
        balanced_strategy: BALANCED approach (optimize payment vs survival)
        conservative_strategy: CONSERVATIVE approach (minimize spending)
        recommended_strategy: Which strategy is recommended for this scenario
        reasoning: Why that strategy is recommended
        cash_available: Available cash for this scenario
    """
    scenario_type: ScenarioType
    aggressive_strategy: PaymentStrategy
    balanced_strategy: PaymentStrategy
    conservative_strategy: PaymentStrategy
    recommended_strategy: StrategyType
    reasoning: str
    cash_available: float


@dataclass
class DecisionResult3Scenarios:
    """
    Complete decision output: 3 scenarios × 3 strategies = 9 total payment plans.
    
    Top-level output from DDE engine.
    
    Attributes:
        best_case: DecisionResult for BEST scenario
        base_case: DecisionResult for BASE scenario
        worst_case: DecisionResult for WORST scenario
        overall_recommendation: Cross-scenario guidance (which scenarios to plan for)
        timestamp: When decisions were generated
        financial_state_id: Reference to input FinancialState
        risk_detection_id: Reference to input RiskDetectionResult
        explanation: Optional detailed explanations for all 9 strategies (populated by ExplainabilityEngine)
    """
    best_case: DecisionResult
    base_case: DecisionResult
    worst_case: DecisionResult
    overall_recommendation: str
    timestamp: datetime = field(default_factory=datetime.now)
    financial_state_id: str = ""
    risk_detection_id: str = ""
    explanation: Optional["CompleteExplanation"] = None
    
    @property
    def all_strategies(self) -> List[PaymentStrategy]:
        """Return all 9 strategies flattened for analysis."""
        return [
            self.best_case.aggressive_strategy,
            self.best_case.balanced_strategy,
            self.best_case.conservative_strategy,
            self.base_case.aggressive_strategy,
            self.base_case.balanced_strategy,
            self.base_case.conservative_strategy,
            self.worst_case.aggressive_strategy,
            self.worst_case.balanced_strategy,
            self.worst_case.conservative_strategy,
        ]
