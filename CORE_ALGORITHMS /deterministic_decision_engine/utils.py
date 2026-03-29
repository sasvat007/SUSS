"""
DDE Utilities

Helper functions, formatting, and default configurations.

Version: 0.0.1
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .models import (
    DecisionResult3Scenarios,
    PaymentStrategy,
    PaymentDecision,
    VendorRelationship,
    VendorRelationshipType,
    PenaltyModel,
    PenaltyType,
)


# Default penalty models by category (reference/constants)
DEFAULT_PENALTY_CONFIGS = {
    "Tax": {"rate": 5.0, "escalation": 0.5, "description": "Tax penalties: severe and escalate quickly"},
    "Loan": {"rate": 2.0, "escalation": 0.25, "description": "Loan penalties: moderate compound"},
    "Utilities": {"rate": 1.5, "escalation": 0.0, "description": "Utility penalties: service disconnect risk"},
    "Payroll": {"rate": 0.0, "escalation": 0.0, "description": "Payroll: no financial penalty (legal/HR risk)"},
    "Supplier": {"rate": 1.0, "escalation": 0.0, "description": "Supplier penalties: moderate"},
    "Rent": {"rate": 3.0, "escalation": 0.5, "description": "Rent penalties: high (eviction risk)"},
    "Insurance": {"rate": 2.5, "escalation": 0.0, "description": "Insurance penalties: policy cancellation risk"},
}


def format_currency(amount: float) -> str:
    """
    Format amount as currency string.
    
    Args:
        amount: Numeric amount
    
    Returns:
        Formatted string (e.g., "$1,234.56")
    """
    return f"${amount:,.2f}"


def format_strategy_summary(strategy: PaymentStrategy) -> str:
    """
    Format payment strategy as human-readable summary.
    
    Args:
        strategy: PaymentStrategy to format
    
    Returns:
        Multi-line summary text
    """
    lines = []
    lines.append(f"{strategy.strategy_type.value} Strategy ({strategy.scenario_type.value}):")
    lines.append(f"  Total Payment:     {format_currency(strategy.total_payment)}")
    lines.append(f"  Penalty Cost:      {format_currency(strategy.total_penalty_cost)}")
    lines.append(f"  Cash After:        {format_currency(strategy.estimated_cash_after)}")
    lines.append(f"  Survival Prob:     {strategy.survival_probability:.1f}%")
    lines.append(f"  Decisions:         {len(strategy.decisions)} obligations")
    return "\n".join(lines)


def format_decision_summary(decision: PaymentDecision) -> str:
    """
    Format single payment decision as human-readable summary.
    
    Args:
        decision: PaymentDecision to format
    
    Returns:
        Single-line summary (e.g., "Tax: PAY_IN_FULL $1,000.00")
    """
    return (
        f"{decision.category}: {decision.status.value} "
        f"{format_currency(decision.pay_amount)}"
    )


def format_scenario_results(results: DecisionResult3Scenarios) -> str:
    """
    Format complete scenario results as human-readable text.
    
    Args:
        results: DecisionResult3Scenarios
    
    Returns:
        Multi-line formatted output
    """
    lines = []
    lines.append("=" * 60)
    lines.append("PAYMENT DECISION RESULTS (All 3 Scenarios)")
    lines.append("=" * 60)
    lines.append("")
    
    # Best case
    lines.append("BEST CASE SCENARIO:")
    lines.append(f"  Recommended: {results.best_case.recommended_strategy.value}")
    lines.append(f"  {format_strategy_summary(results.best_case.aggressive_strategy)}")
    lines.append("")
    
    # Base case
    lines.append("BASE CASE SCENARIO (Most Likely):")
    lines.append(f"  Recommended: {results.base_case.recommended_strategy.value}")
    lines.append(f"  {format_strategy_summary(results.base_case.balanced_strategy)}")
    lines.append("")
    
    # Worst case
    lines.append("WORST CASE SCENARIO:")
    lines.append(f"  Recommended: {results.worst_case.recommended_strategy.value}")
    lines.append(f"  {format_strategy_summary(results.worst_case.conservative_strategy)}")
    lines.append("")
    
    lines.append("=" * 60)
    lines.append("OVERALL RECOMMENDATION:")
    lines.append("=" * 60)
    lines.append(results.overall_recommendation)
    
    return "\n".join(lines)


def export_decisions_to_dict(results: DecisionResult3Scenarios) -> Dict:
    """
    Export DecisionResult3Scenarios as nested dictionary (JSON-serializable).
    
    Args:
        results: DecisionResult3Scenarios
    
    Returns:
        Dict with all decision data
    """
    def strategy_to_dict(strat: PaymentStrategy) -> Dict:
        return {
            "strategy_type": strat.strategy_type.value,
            "scenario_type": strat.scenario_type.value,
            "total_payment": strat.total_payment,
            "total_penalty_cost": strat.total_penalty_cost,
            "estimated_cash_after": strat.estimated_cash_after,
            "survival_probability": strat.survival_probability,
            "score": strat.score,
            "decisions": [
                {
                    "obligation_id": d.obligation_id,
                    "status": d.status.value,
                    "pay_amount": d.pay_amount,
                    "delay_days": d.delay_days,
                    "potential_penalty": d.potential_penalty,
                    "rationale": d.rationale,
                    "category": d.category,
                    "vendor_name": d.vendor_name,
                }
                for d in strat.decisions
            ],
        }
    
    def result_to_dict(result) -> Dict:
        return {
            "scenario_type": result.scenario_type.value,
            "cash_available": result.cash_available,
            "recommended_strategy": result.recommended_strategy.value,
            "reasoning": result.reasoning,
            "strategies": {
                "aggressive": strategy_to_dict(result.aggressive_strategy),
                "balanced": strategy_to_dict(result.balanced_strategy),
                "conservative": strategy_to_dict(result.conservative_strategy),
            },
        }
    
    return {
        "timestamp": results.timestamp.isoformat(),
        "financial_state_id": results.financial_state_id,
        "risk_detection_id": results.risk_detection_id,
        "scenarios": {
            "best": result_to_dict(results.best_case),
            "base": result_to_dict(results.base_case),
            "worst": result_to_dict(results.worst_case),
        },
        "overall_recommendation": results.overall_recommendation,
    }


def create_sample_vendor_relationships() -> Dict[str, VendorRelationship]:
    """
    Create sample vendor relationships for testing.
    
    Returns:
        Dict of vendor_id → VendorRelationship
    """
    return {
        "vendor_001": VendorRelationship(
            vendor_id="vendor_001",
            vendor_name="Tax Authority",
            relationship_type=VendorRelationshipType.CORE,
            years_with_business=10.0,
            payment_reliability=100.0,
        ),
        "vendor_002": VendorRelationship(
            vendor_id="vendor_002",
            vendor_name="Bank Loan Provider",
            relationship_type=VendorRelationshipType.CORE,
            years_with_business=5.0,
            payment_reliability=95.0,
        ),
        "vendor_003": VendorRelationship(
            vendor_id="vendor_003",
            vendor_name="Utilities Corp",
            relationship_type=VendorRelationshipType.EXISTING,
            years_with_business=2.5,
            payment_reliability=80.0,
        ),
        "vendor_004": VendorRelationship(
            vendor_id="vendor_004",
            vendor_name="New Supplier",
            relationship_type=VendorRelationshipType.NEW,
            years_with_business=0.3,
            payment_reliability=50.0,
        ),
    }


def calculate_total_obligations(
    decisions: DecisionResult3Scenarios,
) -> Dict[str, float]:
    """
    Calculate aggregate metrics across all 9 strategies.
    
    Args:
        decisions: DecisionResult3Scenarios
    
    Returns:
        Dict with aggregate metrics
    """
    total_payment = 0.0
    total_penalties = 0.0
    total_delayed = 0
    total_paid = 0
    
    for strategy in decisions.all_strategies:
        total_payment += strategy.total_payment
        total_penalties += strategy.total_penalty_cost
        total_paid += sum(1 for d in strategy.decisions if d.pay_amount > 0)
        total_delayed += sum(1 for d in strategy.decisions if d.delay_days > 0)
    
    avg_payment = total_payment / 9 if total_payment > 0 else 0.0
    avg_penalties = total_penalties / 9 if total_penalties > 0 else 0.0
    
    return {
        "total_strategies": 9,
        "avg_payment_per_strategy": avg_payment,
        "total_penalties_all_strategies": total_penalties,
        "avg_penalties_per_strategy": avg_penalties,
        "total_paid_decisions": total_paid,
        "total_delayed_decisions": total_delayed,
    }


def get_penalty_config(category: str) -> Dict[str, any]:
    """
    Get penalty configuration for a category.
    
    Args:
        category: Obligation category
    
    Returns:
        Dict with penalty rate, escalation, description
    """
    normalized = category.strip().lower()
    
    # Try exact match
    for key, config in DEFAULT_PENALTY_CONFIGS.items():
        if key.lower() == normalized:
            return config
    
    # Try partial match
    for key, config in DEFAULT_PENALTY_CONFIGS.items():
        if normalized in key.lower() or key.lower() in normalized:
            return config
    
    # Default
    return {"rate": 0.5, "escalation": 0.0, "description": "Unknown category"}


def days_until_date(reference_date: datetime, target_date: datetime) -> int:
    """
    Calculate days between two dates.
    
    Args:
        reference_date: Start date
        target_date: End date
    
    Returns:
        Number of days (negative if target is in past)
    """
    delta = target_date - reference_date
    return delta.days


def validate_decision_result(results: DecisionResult3Scenarios) -> List[str]:
    """
    Validate DecisionResult3Scenarios for consistency.
    
    Args:
        results: DecisionResult3Scenarios to validate
    
    Returns:
        List of validation issues (empty if valid)
    """
    issues = []
    
    # Check all scenarios present
    if not results.best_case:
        issues.append("Missing best_case")
    if not results.base_case:
        issues.append("Missing base_case")
    if not results.worst_case:
        issues.append("Missing worst_case")
    
    # Check all strategies present in each scenario
    for scenario_name, scenario_result in [
        ("best_case", results.best_case),
        ("base_case", results.base_case),
        ("worst_case", results.worst_case),
    ]:
        if scenario_result:
            if not scenario_result.aggressive_strategy:
                issues.append(f"{scenario_name}: missing aggressive_strategy")
            if not scenario_result.balanced_strategy:
                issues.append(f"{scenario_name}: missing balanced_strategy")
            if not scenario_result.conservative_strategy:
                issues.append(f"{scenario_name}: missing conservative_strategy")
            
            # Check strategy content
            for strat in [
                scenario_result.aggressive_strategy,
                scenario_result.balanced_strategy,
                scenario_result.conservative_strategy,
            ]:
                if strat and not strat.decisions:
                    issues.append(f"{scenario_name}/{strat.strategy_type}: no decisions")
    
    return issues
