"""
Obligation Scorer for DDE

Computes weighted priority scores for each obligation based on:
- Legal/regulatory risk (40%)
- Urgency / days to due (30%)
- Penalty cost (20%)
- Vendor relationship importance (10%)
- Flexibility to delay/partially pay (-5%)

Score formula: (Legal×0.40 + Urgency×0.30 + Penalty×0.20 + Relationship×0.10 - Flexibility×0.05)
Higher score = higher payment priority.

Version: 0.0.1
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from financial_state_engine.models import Payable, BusinessContext
from .models import (
    ObligationScore,
    VendorRelationship,
    VendorRelationshipType,
    PenaltyModel,
)
from .penalty_calculator import get_penalty_model, calculate_delay_penalty


# Legal risk scores by category (0-100)
LEGAL_RISK_SCORES = {
    "Tax": 100,  # Highest: legal obligation, CRA enforcement
    "Payroll": 90,  # Very high: labor laws, employee rights
    "Loan": 95,  # Very high: contract breach, default clauses
    "Rent": 85,  # High: can trigger eviction
    "Insurance": 70,  # High: coverage gaps if missed
    "Utilities": 65,  # Moderate: service disconnection
    "Supplier": 40,  # Lower: business relationship but non-legal
    "Other": 30,  # Default: treat as low risk
}

# Vendor relationship importance scores (0-100)
# Based on classification: NEW vendors need trust-building, CORE vendors proven loyal
RELATIONSHIP_SCORES = {
    VendorRelationshipType.NEW: 85,  # NEW: Must prioritize to build relationship
    VendorRelationshipType.EXISTING: 50,  # EXISTING: Standard business relationship
    VendorRelationshipType.CORE: 25,  # CORE: Proven loyal, can tolerate delays
}


def _extract_vendor_id(payable: Payable) -> str:
    """
    Extract vendor ID from payable.
    
    Looks for "vendor_XXX" pattern in description, or uses payable ID as fallback.
    
    Args:
        payable: Payable to extract from
    
    Returns:
        Vendor ID string
    """
    import re
    description = payable.description or ""
    
    # Try to find vendor_XXX pattern
    match = re.search(r'vendor_\w+', description)
    if match:
        return match.group(0)
    
    # Fallback to payable ID
    return payable.id


def _parse_due_date(due_date) -> datetime:
    """
    Parse due_date field (can be string or datetime).
    
    Args:
        due_date: String (YYYY-MM-DD) or datetime object
    
    Returns:
        datetime object
    
    Raises:
        ValueError: If format invalid
    """
    if isinstance(due_date, str):
        try:
            return datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid due_date format: {due_date}")
    elif isinstance(due_date, datetime):
        return due_date
    else:
        raise ValueError(f"Invalid due_date type: {type(due_date)}")


def _parse_category(category: Optional[str]) -> str:
    """
    Normalize category field.
    
    Args:
        category: Category string or None
    
    Returns:
        Non-empty category string
    """
    return (category or "").strip() or "Other"


def score_obligation(
    payable: Payable,
    vendor_relationships: Dict[str, VendorRelationship],
    reference_date: datetime,
    business_context: BusinessContext,
    time_horizon_days: int = 90,
) -> ObligationScore:
    """
    Compute weighted priority score for a single obligation.
    
    Weights:
    - Legal risk: 40% (highest priority for taxes, payroll, loans)
    - Urgency: 30% (how soon due)
    - Penalty: 20% (cost of lateness)
    - Relationship: 10% (vendor importance)
    - Flexibility: -5% (ability to delay/partially pay)
    
    Args:
        payable: Obligation to score
        vendor_relationships: Dict of vendor_id → VendorRelationship for lookups
        reference_date: Current date (for urgency calculation)
        business_context: BusinessContext (allow_partial_payments, etc)
        time_horizon_days: Max days in planning horizon (for urgency scaling)
    
    Returns:
        ObligationScore with all component scores and final ranking
    
    Raises:
        ValueError: If payable amount or due_date invalid
    """
    if payable.amount <= 0:
        raise ValueError(f"Payable {payable.id} has invalid amount: {payable.amount}")
    
    if payable.due_date is None:
        raise ValueError(f"Payable {payable.id} missing due_date")
    
    # Calculate each component score
    legal_score = _compute_legal_score(_parse_category(payable.category))
    urgency_score = _compute_urgency_score(_parse_due_date(payable.due_date), reference_date, time_horizon_days)
    penalty_score = _compute_penalty_score(payable)
    relationship_score = _compute_relationship_score(
        _extract_vendor_id(payable), vendor_relationships
    )
    flexibility_score = _compute_flexibility_score(business_context, payable)
    
    # Apply legal overrides (ensure critical obligations never score too low)
    legal_score = _apply_legal_overrides(legal_score, _parse_category(payable.category))
    
    # Compute weighted score
    weighted_score = (
        legal_score * 0.40 +
        urgency_score * 0.30 +
        penalty_score * 0.20 +
        relationship_score * 0.10 -
        flexibility_score * 0.05
    )
    
    # Create ObligationScore (priority_rank set later when batch-scored)
    due_date_parsed = _parse_due_date(payable.due_date)
    days_to_due = (due_date_parsed - reference_date).days
    
    return ObligationScore(
        obligation_id=payable.id,
        legal_risk_score=legal_score,
        urgency_score=urgency_score,
        penalty_score=penalty_score,
        relationship_score=relationship_score,
        flexibility_score=flexibility_score,
        total_weighted_score=weighted_score,
        priority_rank=0,  # Set by score_all_obligations()
        category=_parse_category(payable.category),
        vendor_name=payable.description or "Unknown",  # Use description as vendor name fallback
        days_to_due=days_to_due,
        original_amount=payable.amount,
    )


def score_all_obligations(
    payables: List[Payable],
    vendor_relationships: Dict[str, VendorRelationship],
    reference_date: datetime,
    business_context: BusinessContext,
    time_horizon_days: int = 90,
) -> List[ObligationScore]:
    """
    Score all obligations and assign priority ranks.
    
    Args:
        payables: List of Payables to score
        vendor_relationships: Dict of vendor_id → VendorRelationship
        reference_date: Current date
        business_context: Business constraints
        time_horizon_days: Planning horizon in days
    
    Returns:
        List of ObligationScores sorted by priority_rank (1 = highest priority)
    """
    scores = []
    for payable in payables:
        try:
            score = score_obligation(
                payable,
                vendor_relationships,
                reference_date,
                business_context,
                time_horizon_days,
            )
            scores.append(score)
        except ValueError as e:
            # Log warning but continue scoring others
            print(f"Warning: Skipping payable {payable.id}: {e}")
            continue
    
    # Sort by weighted score (descending) and assign ranks
    scores.sort(key=lambda s: s.total_weighted_score, reverse=True)
    
    for rank, score in enumerate(scores, start=1):
        score.priority_rank = rank
    
    return scores


def _compute_legal_score(category: str) -> float:
    """
    Compute legal/regulatory risk score for category.
    
    Args:
        category: Obligation category
    
    Returns:
        Score 0-100 (higher = more legally risky)
    """
    normalized = category.strip().lower()
    
    # Try exact match
    for key, score in LEGAL_RISK_SCORES.items():
        if key.lower() == normalized:
            return float(score)
    
    # Try partial match
    for key, score in LEGAL_RISK_SCORES.items():
        if normalized in key.lower() or key.lower() in normalized:
            return float(score)
    
    return float(LEGAL_RISK_SCORES["Other"])


def _compute_urgency_score(
    due_date: datetime,
    reference_date: datetime,
    time_horizon_days: int,
) -> float:
    """
    Compute urgency score based on days to due.
    
    Formula: max(0, 100 - (days_to_due / time_horizon × 100))
    - 0 days to due → score = 100 (urgent)
    - Equal to horizon → score = 0 (not urgent)
    - Beyond horizon → score = 0 (future obligation)
    
    Args:
        due_date: When obligation is due
        reference_date: Current date
        time_horizon_days: Planning horizon (e.g., 90 days)
    
    Returns:
        Score 0-100 (higher = more urgent)
    """
    days_to_due = (due_date - reference_date).days
    
    if days_to_due <= 0:
        # Already due or overdue
        return 100.0
    
    if days_to_due >= time_horizon_days:
        # Beyond planning horizon
        return 0.0
    
    # Linear scaling: days_to_due / horizon maps to urgency
    return max(0.0, 100.0 - (days_to_due / time_horizon_days * 100.0))


def _compute_penalty_score(payable: Payable) -> float:
    """
    Compute penalty/consequence score.
    
    Formula: IF has_penalty: 50 + (rate × 50), ELSE 0
    - No penalty categories (Payroll): 0 (financial, but still critical)
    - Low rate (Supplier 1%): 50
    - High rate (Tax 5%): 50 + (5 × 5) = 75
    
    Args:
        payable: Obligation to evaluate
    
    Returns:
        Score 0-100 (higher = more costly penalties)
    """
    penalty_model = get_penalty_model(payable.category)
    
    if not penalty_model.has_penalty:
        # No financial penalty (but category might be legally important)
        return 0.0
    
    # Score based on daily percentage rate
    base = 50.0
    rate_bonus = penalty_model.penalty_rate * 5.0  # Scale rate to 0-50 range
    
    return min(100.0, base + rate_bonus)


def _compute_relationship_score(
    creditor_id: str,
    vendor_relationships: Dict[str, VendorRelationship],
) -> float:
    """
    Compute vendor relationship importance score.
    
    NEW vendors (< 1yr): 85 (must prioritize to build trust)
    EXISTING vendors (1-3yr): 50 (normal business)
    CORE vendors (> 3yr): 25 (proven loyal, can delay)
    Unknown vendors: 50 (treat as EXISTING)
    
    Args:
        creditor_id: Vendor/creditor ID
        vendor_relationships: Dict of known relationships
    
    Returns:
        Score 0-100 (higher = more important vendor to maintain)
    """
    if creditor_id not in vendor_relationships:
        # Unknown vendor: default to EXISTING treatment
        return float(RELATIONSHIP_SCORES[VendorRelationshipType.EXISTING])
    
    vendor_rel = vendor_relationships[creditor_id]
    return float(RELATIONSHIP_SCORES[vendor_rel.relationship_type])


def _compute_flexibility_score(
    business_context: BusinessContext,
    payable: Payable,
) -> float:
    """
    Compute flexibility score (ability to delay or partially pay).
    
    Higher flexibility = lower priority to pay in full now.
    
    Formula:
    - If allow_partial_payments: 80 (can split payments)
    - Else: 20 (must pay in full)
    - Adjusted by category (some categories have less flexibility)
    
    Args:
        business_context: Business policy on payments
        payable: Obligation to evaluate
    
    Returns:
        Score 0-100 (higher = more flexible)
    """
    base_flexibility = 80.0 if business_context.allow_partial_payments else 20.0
    
    # Some categories have less flexibility (can't partially pay taxes)
    inflexible_categories = {"Tax", "Payroll", "Loan", "Rent"}
    normalized_cat = payable.category.lower()
    
    if any(cat.lower() in normalized_cat for cat in inflexible_categories):
        # Reduce flexibility for rigid categories
        base_flexibility = max(5.0, base_flexibility - 30.0)
    
    return base_flexibility


def _apply_legal_overrides(legal_score: float, category: str) -> float:
    """
    Apply legal overrides to ensure critical obligations never score too low.
    
    Ensures Tax, Payroll, Loan payables always score >= 85 for legal component.
    
    Args:
        legal_score: Computed legal score
        category: Obligation category
    
    Returns:
        Potentially adjusted legal score with minimums applied
    """
    critical_categories = {"Tax", "Payroll", "Loan"}
    normalized = category.strip().lower()
    
    if any(cat.lower() == normalized for cat in critical_categories):
        return max(85.0, legal_score)
    
    return legal_score
