"""
Penalty Calculator for DDE

Handles penalty model lookup and penalty cost calculations.
Supports category-specific default penalties and delay-based penalty accrual.

Version: 0.0.1
"""

from typing import Dict, Optional
from datetime import datetime
from .models import PenaltyModel, PenaltyType


# Default penalty models by obligation category
DEFAULT_PENALTIES: Dict[str, PenaltyModel] = {
    "Tax": PenaltyModel(
        category="Tax",
        has_penalty=True,
        penalty_type=PenaltyType.DAILY_PERCENTAGE,
        penalty_rate=5.0,  # 5% per day
        escalation=0.5,  # Additional 0.5% after 30 days
        max_delay_days=90,  # Most tax penalties cap at 90 days
        description="Tax and GST penalties are severe and escalate quickly. Legal requirement.",
    ),
    "Loan": PenaltyModel(
        category="Loan",
        has_penalty=True,
        penalty_type=PenaltyType.DAILY_PERCENTAGE,
        penalty_rate=2.0,  # 2% per day
        escalation=0.25,  # Additional 0.25% after 15 days
        max_delay_days=180,
        description="Loan penalties are moderate but compound. Can trigger default clauses.",
    ),
    "Utilities": PenaltyModel(
        category="Utilities",
        has_penalty=True,
        penalty_type=PenaltyType.DAILY_PERCENTAGE,
        penalty_rate=1.5,  # 1.5% per day
        escalation=0.0,
        max_delay_days=120,
        description="Utilities may disconnect service if penalties accumulate.",
    ),
    "Payroll": PenaltyModel(
        category="Payroll",
        has_penalty=False,  # No financial penalty, but legal/HR consequence
        penalty_type=PenaltyType.FIXED_FLAT,
        penalty_rate=0.0,
        escalation=0.0,
        max_delay_days=14,  # Payroll defaults are critical - max 2 weeks
        description="Payroll penalties are non-financial but severe (legal, morale, HR).",
    ),
    "Supplier": PenaltyModel(
        category="Supplier",
        has_penalty=True,
        penalty_type=PenaltyType.DAILY_PERCENTAGE,
        penalty_rate=1.0,  # 1% per day
        escalation=0.0,
        max_delay_days=60,
        description="Supplier penalties are moderate; vendors may pause service.",
    ),
    "Rent": PenaltyModel(
        category="Rent",
        has_penalty=True,
        penalty_type=PenaltyType.DAILY_PERCENTAGE,
        penalty_rate=3.0,  # 3% per day
        escalation=0.5,  # Additional 0.5% after 5 days
        max_delay_days=30,
        description="Rent penalties are high and can trigger eviction.",
    ),
    "Insurance": PenaltyModel(
        category="Insurance",
        has_penalty=True,
        penalty_type=PenaltyType.DAILY_PERCENTAGE,
        penalty_rate=2.5,  # 2.5% per day
        escalation=0.0,
        max_delay_days=60,
        description="Insurance penalties can lead to policy cancellation.",
    ),
}

# Default fallback for unknown categories
DEFAULT_OTHER = PenaltyModel(
    category="Other",
    has_penalty=True,
    penalty_type=PenaltyType.DAILY_PERCENTAGE,
    penalty_rate=0.5,  # 0.5% per day (conservative)
    escalation=0.0,
    max_delay_days=180,
    description="Generic penalty model for unclassified obligations.",
)


def get_penalty_model(category: str) -> PenaltyModel:
    """
    Retrieve penalty model for a category.
    
    Falls back to DEFAULT_OTHER if category not found.
    
    Args:
        category: Obligation category (e.g., "Tax", "Loan")
    
    Returns:
        PenaltyModel with penalty structure for this category
    """
    normalized = category.strip().lower()
    
    # Try exact match (case-insensitive)
    for key, penalty in DEFAULT_PENALTIES.items():
        if key.lower() == normalized:
            return penalty
    
    # Try partial match
    for key, penalty in DEFAULT_PENALTIES.items():
        if normalized in key.lower() or key.lower() in normalized:
            return penalty
    
    # Fallback
    return DEFAULT_OTHER


def calculate_delay_penalty(
    amount: float,
    delay_days: int,
    penalty_model: PenaltyModel,
) -> float:
    """
    Calculate penalty cost for delayed payment.
    
    Args:
        amount: Original obligation amount
        delay_days: How many days payment is delayed
        penalty_model: PenaltyModel governing this category
    
    Returns:
        Estimated penalty cost (0 if no penalties or amount=0)
    """
    if not penalty_model.has_penalty or amount <= 0 or delay_days <= 0:
        return 0.0
    
    # Cap delay at max_delay_days
    actual_delay = min(delay_days, penalty_model.max_delay_days)
    
    if penalty_model.penalty_type == PenaltyType.DAILY_PERCENTAGE:
        return _calculate_daily_percentage_penalty(
            amount, actual_delay, penalty_model
        )
    elif penalty_model.penalty_type == PenaltyType.FIXED_FLAT:
        return amount * (penalty_model.penalty_rate / 100.0)  # One-time flat
    elif penalty_model.penalty_type == PenaltyType.TIERED:
        return _calculate_tiered_penalty(amount, actual_delay, penalty_model)
    
    return 0.0


def _calculate_daily_percentage_penalty(
    amount: float,
    delay_days: int,
    penalty_model: PenaltyModel,
) -> float:
    """
    Calculate daily percentage penalty with optional escalation.
    
    Formula: amount × (base_rate × days / 100) + escalation_penalty
    Escalation applies after 15-30 days depending on category.
    
    Args:
        amount: Original obligation amount
        delay_days: Days of delay
        penalty_model: PenaltyModel with rate and escalation
    
    Returns:
        Total penalty cost
    """
    escalation_threshold = 15  # Default: escalate after 15 days
    
    if delay_days <= escalation_threshold:
        # Simple linear accrual
        penalty = amount * (penalty_model.penalty_rate * delay_days / 100.0)
    else:
        # Phase 1: Base rate for first 15 days
        phase1 = amount * (penalty_model.penalty_rate * escalation_threshold / 100.0)
        
        # Phase 2: Base rate + escalation for remaining days
        remaining_days = delay_days - escalation_threshold
        phase2 = amount * (
            (penalty_model.penalty_rate + penalty_model.escalation)
            * remaining_days
            / 100.0
        )
        
        penalty = phase1 + phase2
    
    return max(0.0, penalty)


def _calculate_tiered_penalty(
    amount: float,
    delay_days: int,
    penalty_model: PenaltyModel,
) -> float:
    """
    Calculate tiered penalty (escalates in chunks).
    
    Tier 1: 0-7 days → base_rate
    Tier 2: 8-30 days → base_rate + escalation
    Tier 3: 31+ days → base_rate + escalation×2
    
    Args:
        amount: Original obligation amount
        delay_days: Days of delay
        penalty_model: PenaltyModel with rate and escalation
    
    Returns:
        Total penalty cost
    """
    if delay_days <= 7:
        rate = penalty_model.penalty_rate
    elif delay_days <= 30:
        rate = penalty_model.penalty_rate + penalty_model.escalation
    else:
        rate = penalty_model.penalty_rate + (penalty_model.escalation * 2)
    
    return amount * (rate * delay_days / 100.0)


def estimate_penalty_for_obligation(
    obligation_id: str,
    amount: float,
    category: str,
    potential_delay_days: int,
) -> float:
    """
    Convenience function: get penalty model and calculate penalty in one call.
    
    Args:
        obligation_id: ID of obligation (unused, for logging)
        amount: Original amount owed
        category: Obligation category
        potential_delay_days: Proposed delay in days
    
    Returns:
        Estimated penalty cost
    """
    penalty_model = get_penalty_model(category)
    return calculate_delay_penalty(amount, potential_delay_days, penalty_model)


def get_all_penalty_models() -> Dict[str, PenaltyModel]:
    """Return copy of all default penalty models (for reference/testing)."""
    return dict(DEFAULT_PENALTIES)
