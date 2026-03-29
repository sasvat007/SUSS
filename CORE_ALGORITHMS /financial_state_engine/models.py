"""
Data models for the Financial State Engine.

Defines immutable, JSON-serializable data structures representing transactions,
obligations, receivables, business context, and computed financial state.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class TransactionType(Enum):
    """Types of transactions."""
    DEBIT = "debit"
    CREDIT = "credit"


class PayableStatus(Enum):
    """Status of a payable obligation."""
    DUE = "due"
    PENDING = "pending"
    OVERDUE = "overdue"
    PAID = "paid"


class ReceivableStatus(Enum):
    """Status of a receivable."""
    PENDING = "pending"
    RECEIVED = "received"
    CANCELLED = "cancelled"
    DELAYED = "delayed"


class PriorityLevel(Enum):
    """Priority levels for payables."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class HiddenTransactionType(Enum):
    """Types of hidden/recurring transactions."""
    SALARY = "salary"
    LOAN_PAYMENT = "loan_payment"
    SUBSCRIPTION = "subscription"
    TAX = "tax"
    RENTAL = "rental"
    UTILITY = "utility"
    OTHER = "other"


class FrequencyType(Enum):
    """Frequency of recurring transactions."""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class Transaction:
    """
    Represents a single bank transaction.
    
    Attributes:
        date: Transaction date (YYYY-MM-DD format)
        description: Description of the transaction
        amount: Amount in INR (signed: negative = debit, positive = credit)
        transaction_type: Type of transaction (debit or credit)
        category: Optional category for segmentation
        id: Unique identifier
    """
    date: str  # YYYY-MM-DD
    description: str
    amount: float
    transaction_type: str  # "debit" or "credit"
    category: Optional[str] = None
    id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class Payable:
    """
    Represents a payment obligation (invoice, vendor payment, etc.).
    
    Attributes:
        id: Unique identifier
        amount: Amount due in INR
        due_date: Due date (YYYY-MM-DD format)
        description: Description of the obligation
        status: Current status (due, pending, overdue, paid)
        priority_level: Priority for payment decisions
        category: Optional category (supplier name, etc.)
    """
    id: str
    amount: float
    due_date: str  # YYYY-MM-DD
    description: str
    status: str = "pending"
    priority_level: str = "normal"
    category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class Receivable:
    """
    Represents incoming payments/receivables.
    
    Attributes:
        id: Unique identifier
        amount: Amount expected in INR
        expected_date: Expected payment date (YYYY-MM-DD format)
        description: Description of the receivable (invoice #, client name, etc.)
        confidence: Confidence score (0.0-1.0) based on historical payment data
        status: Current status (pending, received, cancelled, delayed)
        category: Optional category (client name, project, etc.)
    """
    id: str
    amount: float
    expected_date: str  # YYYY-MM-DD
    description: str
    confidence: float  # 0.0 to 1.0
    status: str = "pending"
    category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def validate_confidence(self) -> bool:
        """Validate that confidence is in valid range."""
        return 0.0 <= self.confidence <= 1.0


@dataclass
class HiddenTransaction:
    """
    Represents recurring, scheduled transactions not yet in transaction history.
    
    Attributes:
        id: Unique identifier
        transaction_type: Type (salary, loan_payment, subscription, etc.)
        amount: Amount in INR (typically outflow, so can be negative or positive)
        frequency: Frequency of occurrence (monthly, weekly, etc.)
        next_date: Next occurrence date (YYYY-MM-DD format)
        category: Category/description (e.g., "Monthly Salary", "AWS Subscription")
        notes: Optional additional notes
    """
    id: str
    transaction_type: str
    amount: float
    frequency: str  # "weekly", "biweekly", "monthly", "quarterly", "yearly"
    next_date: str  # YYYY-MM-DD
    category: str
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class BusinessContext:
    """
    Business-specific configuration and constraints.
    
    Attributes:
        min_cash_buffer: Minimum cash to keep on hand (safety buffer) in INR
        time_horizon_days: Number of days to forecast (7-30 days typical)
        allow_partial_payments: Whether partial payments of obligations are allowed
        avg_payment_delay_days: Average delay in customer payments (days)
        currency: Currency code (INR for now)
        business_id: Optional identifier for the business
        config_date: Date this config was set (YYYY-MM-DD format)
    """
    min_cash_buffer: float  # INR
    time_horizon_days: int  # 7-30 typical
    allow_partial_payments: bool = True
    avg_payment_delay_days: int = 0
    currency: str = "INR"
    business_id: Optional[str] = None
    config_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def validate(self) -> bool:
        """Validate business context."""
        if self.min_cash_buffer < 0:
            return False
        if self.time_horizon_days <= 0 or self.time_horizon_days > 365:
            return False
        if self.avg_payment_delay_days < 0:
            return False
        return True


@dataclass
class CashFlowEvent:
    """
    Represents a cash inflow or outflow event on a specific date.
    
    Attributes:
        date: Event date (YYYY-MM-DD format)
        inflow: Total inflow on this date (INR)
        outflow: Total outflow on this date (INR)
        balance: Cumulative balance after this event (INR)
        events: List of descriptions of what happened on this date
    """
    date: str
    inflow: float = 0.0
    outflow: float = 0.0
    balance: float = 0.0
    events: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class HealthScoreBreakdown:
    """
    Detailed breakdown of health score calculation.
    
    Attributes:
        runway_score: Score based on runway (0-100)
        obligation_pressure_score: Score based on obligation pressure (0-100)
        receivable_quality_score: Score based on receivable quality (0-100)
        buffer_sufficiency_score: Score based on buffer sufficiency (0-100)
        runway_weight: Weight of runway component (default 0.40)
        pressure_weight: Weight of pressure component (default 0.35)
        quality_weight: Weight of quality component (default 0.15)
        buffer_weight: Weight of buffer component (default 0.10)
    """
    runway_score: float
    obligation_pressure_score: float
    receivable_quality_score: float
    buffer_sufficiency_score: float
    runway_weight: float = 0.40
    pressure_weight: float = 0.35
    quality_weight: float = 0.15
    buffer_weight: float = 0.10

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class FinancialState:
    """
    Computed financial state snapshot for a business.
    
    This is the primary output of the Financial State Engine.
    
    Attributes:
        current_balance: Current account balance in INR
        available_cash: Current balance minus min buffer
        total_payables_due_now: Payables due today or overdue
        total_payables_due_soon: Payables due within time horizon
        total_payables_all: All payables regardless of timing
        weighted_receivables: Sum of (amount × confidence) for all receivables within horizon
        total_receivables_unweighted: Total receivables without confidence adjustment
        cash_runway_days: Days until cash falls below buffer (or None if stable)
        obligation_pressure_ratio: (Payables within horizon) / (Available cash + Weighted receivables)
        receivable_quality_score: Measure of confidence in incoming cash
        buffer_sufficiency_days: Estimated days the buffer lasts at current burn rate
        health_score: Overall financial health (0-100)
        health_score_breakdown: Detailed component scores
        health_reasoning: Human-readable explanation of health score
        cash_flow_timeline: Day-by-day cash flow events within horizon
        snapshot_date: Date this state was computed (YYYY-MM-DD format)
        status_flags: Dict of boolean flags for risk conditions (e.g., "has_overdue": True)
    """
    current_balance: float
    available_cash: float
    total_payables_due_now: float
    total_payables_due_soon: float
    total_payables_all: float
    weighted_receivables: float
    total_receivables_unweighted: float
    cash_runway_days: Optional[int]
    obligation_pressure_ratio: float
    receivable_quality_score: float
    buffer_sufficiency_days: float
    health_score: int  # 0-100
    health_score_breakdown: HealthScoreBreakdown
    health_reasoning: str
    cash_flow_timeline: List[CashFlowEvent]
    snapshot_date: str
    status_flags: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Ensure nested objects are also converted
        data['health_score_breakdown'] = self.health_score_breakdown.to_dict()
        data['cash_flow_timeline'] = [event.to_dict() for event in self.cash_flow_timeline]
        return data

    def to_json_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary with proper formatting."""
        return self.to_dict()
