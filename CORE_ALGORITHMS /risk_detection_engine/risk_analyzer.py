"""
Risk analyzer for Risk Detection Engine.

Analyzes scenarios to generate risk flags, severity assessments, and recommendations.
"""

from typing import Dict, Optional
from .models import RiskSeverity, UncertaintyLevel


def generate_risk_flags(
    days_to_shortfall: Optional[int],
    total_deficit_days: int,
    max_deficit: float,
    recovered: bool,
    zero_cash_date: Optional[str]
) -> Dict[str, bool]:
    """
    Generate risk flags for a scenario.
    
    Args:
        days_to_shortfall: Days until first shortfall (or None)
        total_deficit_days: Total days in deficit
        max_deficit: Maximum deficit amount
        recovered: Whether scenario recovers from deficit
        zero_cash_date: Date of total cash depletion (or None)
        
    Returns:
        Dictionary of boolean flags
    """
    has_shortfall = days_to_shortfall is not None
    
    flags = {
        "has_shortfall": has_shortfall,
        "shortfall_within_7_days": has_shortfall and days_to_shortfall <= 7,
        "shortfall_within_14_days": has_shortfall and days_to_shortfall <= 14,
        "shortfall_within_30_days": has_shortfall and days_to_shortfall <= 30,
        "prolonged_deficit": total_deficit_days > 3,
        "zero_cash_risk": zero_cash_date is not None,
        "no_recovery_in_horizon": has_shortfall and not recovered,
        "deep_deficit": max_deficit > 50000,  # Arbitrary threshold; adjust as needed
        "moderate_deficit": 10000 <= max_deficit <= 50000,
    }
    
    return flags


def classify_risk_severity(
    days_to_shortfall: Optional[int],
    has_zero_cash_risk: bool,
    no_recovery: bool
) -> str:
    """
    Classify overall risk severity for a scenario.
    
    Args:
        days_to_shortfall: Days until shortfall (or None if no shortfall)
        has_zero_cash_risk: Whether total depletion is possible
        no_recovery: Whether scenario doesn't recover from deficit
        
    Returns:
        Severity level: "safe", "caution", "warning", or "critical"
    """
    # No shortfall = safe
    if days_to_shortfall is None:
        return RiskSeverity.SAFE.value
    
    # Immediate or very soon threats = critical
    if days_to_shortfall <= 7 or has_zero_cash_risk:
        return RiskSeverity.CRITICAL.value
    
    # Intermediate timeframe threats = warning
    if days_to_shortfall <= 14:
        return RiskSeverity.WARNING.value
    
    # Further out threats with recovery = caution
    if days_to_shortfall <= 30:
        return RiskSeverity.CAUTION.value
    
    # Distant threats or no recovery = caution
    if no_recovery:
        return RiskSeverity.CAUTION.value
    
    return RiskSeverity.SAFE.value


def generate_risk_summary(
    scenario_type: str,
    days_to_shortfall: Optional[int],
    minimum_cash: float,
    total_deficit_days: int,
    risk_severity: str,
    recovered: bool
) -> str:
    """
    Generate human-readable risk summary text.
    
    Args:
        scenario_type: "best", "base", or "worst"
        days_to_shortfall: Days until shortfall
        minimum_cash: Lowest cash balance in scenario
        total_deficit_days: Days in deficit
        risk_severity: "safe", "caution", "warning", "critical"
        recovered: Whether deficit recovers
        
    Returns:
        Summary text
    """
    scenario_label = scenario_type.upper()
    
    if risk_severity == "safe":
        status = "✓ SAFE"
        detail = f"No cash shortfall projected. Minimum balance: ₹{minimum_cash:,.2f}"
    elif risk_severity == "critical":
        status = "🔴 CRITICAL"
        if days_to_shortfall and days_to_shortfall <= 7:
            detail = f"Cash shortfall within {days_to_shortfall} days. Immediate action required."
        else:
            detail = f"Severe cash constraints detected. Planning required."
    elif risk_severity == "warning":
        status = "⚠ WARNING"
        detail = f"Cash shortfall within {days_to_shortfall} days. Consider action."
    else:  # caution
        status = "→ CAUTION"
        detail = f"Potential shortfall in {days_to_shortfall} days. Monitor closely."
    
    recovery_info = ""
    if total_deficit_days > 0:
        recovery_info = f" ({total_deficit_days} days in deficit"
        if recovered:
            recovery_info += ", then recovery"
        recovery_info += ")"
    
    return f"{scenario_label}: {status} — {detail}{recovery_info}"


def analyze_scenario_divergence(
    best_days_to_shortfall: Optional[int],
    base_days_to_shortfall: Optional[int],
    worst_days_to_shortfall: Optional[int]
) -> str:
    """
    Analyze divergence between scenarios and classify uncertainty level.
    
    Args:
        best_days_to_shortfall: Days to shortfall in best case
        base_days_to_shortfall: Days to shortfall in base case
        worst_days_to_shortfall: Days to shortfall in worst case
        
    Returns:
        Uncertainty level: "low", "medium", or "high"
    """
    # Convert None to large number for comparison
    best = best_days_to_shortfall if best_days_to_shortfall else 365
    base = base_days_to_shortfall if base_days_to_shortfall else 365
    worst = worst_days_to_shortfall if worst_days_to_shortfall else 365
    
    # Calculate divergence
    max_range = best - worst
    
    # If all are the same, low uncertainty
    if max_range == 0:
        return UncertaintyLevel.LOW.value
    
    # If range > 21 days or one is safe and others aren't
    if max_range > 21 or (365 in [best, base, worst] and 365 not in [best, base, worst]):
        return UncertaintyLevel.HIGH.value
    
    # Medium uncertainty
    return UncertaintyLevel.MEDIUM.value


def generate_scenario_divergence_summary(
    best_days: Optional[int],
    base_days: Optional[int],
    worst_days: Optional[int],
    uncertainty_level: str
) -> str:
    """
    Generate human-readable summary of scenario divergence.
    
    Args:
        best_days: Days to shortfall in best case
        base_days: Days to shortfall in base case
        worst_days: Days to shortfall in worst case
        uncertainty_level: "low", "medium", or "high"
        
    Returns:
        Summary text
    """
    # Format shortfall info
    def fmt(days):
        return f"{days} days" if days else "stable"
    
    summary = f"Best: {fmt(best_days)} | Base: {fmt(base_days)} | Worst: {fmt(worst_days)}"
    
    if uncertainty_level == "low":
        interpretation = "Scenarios align; receivables/delays have minimal impact"
    elif uncertainty_level == "high":
        interpretation = "High divergence between scenarios; significant uncertainty about timing"
    else:
        interpretation = "Moderate divergence; scenario variations are meaningful"
    
    return f"{summary} — {interpretation}"


def determine_primary_risk_date(
    best_shortfall: Optional[str],
    base_shortfall: Optional[str],
    worst_shortfall: Optional[str]
) -> Optional[str]:
    """
    Determine the most urgent critical date to watch.
    
    Priority: worst case shortfall > base case > best case
    
    Args:
        best_shortfall: Shortfall date in best case
        base_shortfall: Shortfall date in base case
        worst_shortfall: Shortfall date in worst case
        
    Returns:
        Most urgent date to watch (or None if all safe)
    """
    if worst_shortfall:
        return worst_shortfall
    elif base_shortfall:
        return base_shortfall
    elif best_shortfall:
        return best_shortfall
    
    return None


def generate_recommendation(
    overall_risk_level: str,
    primary_risk_date: Optional[str],
    best_severity: str,
    worst_severity: str
) -> str:
    """
    Generate recommended action based on risk analysis.
    
    Args:
        overall_risk_level: Overall risk classification
        primary_risk_date: Most urgent date to watch
        best_severity: Best case severity
        worst_severity: Worst case severity
        
    Returns:
        Recommendation text
    """
    if overall_risk_level == "critical":
        if primary_risk_date:
            return f"URGENT: Cash crisis projected by {primary_risk_date}. Take immediate action: accelerate receivables, defer expenses, or secure credit."
        else:
            return "URGENT: Severe cash constraints. Immediate action required."
    
    elif overall_risk_level == "warning":
        if primary_risk_date:
            return f"HIGH PRIORITY: Shortfall expected by {primary_risk_date}. Develop contingency plan—accelerate collections, defer non-critical expenses, or arrange financing."
        else:
            return "HIGH PRIORITY: Shortfall likely in near term. Develop mitigation plan."
    
    elif overall_risk_level == "caution":
        if primary_risk_date:
            return f"MONITOR: Potential shortfall around {primary_risk_date}. Prepare contingency plan. Monitor actual payments closely."
        else:
            return "MONITOR: Watch cash position. Contingency plan recommended."
    
    else:  # safe
        if best_severity == worst_severity:
            return "SAFE: Strong cash position across all scenarios. Continue normal operations."
        else:
            return "STABLE: Safe under current projections, but prepare for downside scenarios."
