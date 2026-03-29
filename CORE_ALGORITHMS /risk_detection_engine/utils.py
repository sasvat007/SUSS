"""
Utility functions for Risk Detection Engine.

Provides severity mappings, format helpers, and recommendations.
"""

from typing import Dict, Optional, Tuple


# Severity level color codes (for terminal/HTML output)
SEVERITY_COLORS = {
    "safe": "\x1b[92m",      # Green
    "caution": "\x1b[93m",   # Yellow
    "warning": "\x1b[91m",   # Red
    "critical": "\x1b[91m",  # Red (bright)
}

SEVERITY_SYMBOLS = {
    "safe": "✓",
    "caution": "→",
    "warning": "⚠",
    "critical": "🔴",
}

# Severity numeric scores (for ML/aggregation)
SEVERITY_SCORES = {
    "safe": 0,
    "caution": 1,
    "warning": 2,
    "critical": 3,
}


def format_currency(amount: float, currency: str = "INR") -> str:
    """
    Format currency amount for display.
    
    Args:
        amount: Numeric amount
        currency: Currency code (default: INR)
        
    Returns:
        Formatted string (e.g., "₹1,00,000.00")
    """
    if currency == "INR":
        symbol = "₹"
        # Indian format: commas at 10^3, 10^5, 10^7, etc.
        # But simpler: use standard comma with 2 decimals
        return f"{symbol}{amount:,.2f}"
    elif currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def format_date_range(start_date: Optional[str], end_date: Optional[str]) -> str:
    """
    Format a date range for display.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        Formatted range
    """
    if not start_date and not end_date:
        return "No data"
    elif start_date and not end_date:
        return f"From {start_date}"
    elif end_date and not start_date:
        return f"Until {end_date}"
    else:
        return f"{start_date} to {end_date}"


def format_risk_summary_table(
    best_severity: str,
    base_severity: str,
    worst_severity: str,
    best_shortfall: Optional[int],
    base_shortfall: Optional[int],
    worst_shortfall: Optional[int],
) -> str:
    """
    Format risk metrics as a readable table.
    
    Args:
        best_severity: Best case severity
        base_severity: Base case severity
        worst_severity: Worst case severity
        best_shortfall: Days to shortfall (best)
        base_shortfall: Days to shortfall (base)
        worst_shortfall: Days to shortfall (worst)
        
    Returns:
        Formatted table string
    """
    def format_days(days):
        return f"{days} days" if days else "Stable"
    
    lines = [
        "╔════════════╦════════════════╦═════════════════╗",
        "║  Scenario  ║      Risk      ║ Shortfall Date  ║",
        "╠════════════╬════════════════╬═════════════════╣",
        f"║ Best Case  ║ {best_severity:12} ║ {format_days(best_shortfall):15} ║",
        f"║ Base Case  ║ {base_severity:12} ║ {format_days(base_shortfall):15} ║",
        f"║ Worst Case ║ {worst_severity:12} ║ {format_days(worst_shortfall):15} ║",
        "╚════════════╩════════════════╩═════════════════╝",
    ]
    
    return "\n".join(lines)


def get_action_priority(risk_level: str) -> int:
    """
    Get priority level for action (0=lowest, 3=highest).
    
    Args:
        risk_level: "safe", "caution", "warning", or "critical"
        
    Returns:
        Priority (0-3)
    """
    return SEVERITY_SCORES.get(risk_level, 0)


def should_trigger_alert(risk_level: str) -> bool:
    """
    Determine if risk level warrants triggering an alert.
    
    Args:
        risk_level: "safe", "caution", "warning", or "critical"
        
    Returns:
        True if warning or critical
    """
    return risk_level in ["warning", "critical"]


def get_risk_mitigation_steps(
    risk_level: str,
    days_to_shortfall: Optional[int],
) -> list:
    """
    Get recommended mitigation steps based on risk level and timing.
    
    Args:
        risk_level: "safe", "caution", "warning", or "critical"
        days_to_shortfall: Days until shortfall (or None)
        
    Returns:
        List of recommended actions
    """
    if risk_level == "safe":
        return [
            "Monitor cash position",
            "Continue normal operations",
            "Review quarterly with team",
        ]
    
    elif risk_level == "critical":
        urgent_steps = [
            "IMMEDIATE: Contact key customers for early payment",
            "IMMEDIATE: Defer non-critical expenses",
            "IMMEDIATE: Arrange emergency credit line",
        ]
        
        if days_to_shortfall and days_to_shortfall <= 3:
            urgent_steps.insert(3, "IMMEDIATE: Contact suppliers about extended terms")
        elif days_to_shortfall and days_to_shortfall <= 7:
            urgent_steps.append("Contact suppliers about extended payment terms")
        
        urgent_steps.extend([
            "Daily cash position tracking",
            "Escalate to finance leadership",
        ])
        
        return urgent_steps
    
    elif risk_level == "warning":
        return [
            "HIGH PRIORITY: Start customer collections campaign",
            "HIGH PRIORITY: Identify expenses to defer",
            "Prepare credit line application",
            "Communicate with suppliers about timing flexibility",
            "Weekly cash tracking and projections",
            "Prepare board/stakeholder communication",
        ]
    
    else:  # caution
        return [
            "Monitor cash position closely",
            "Prepare contingency plan for expense reduction",
            "Maintain credit line access",
            "Bi-weekly cash flow updates",
            "Brief leadership on downside scenario",
        ]


def estimate_cash_runway(available_cash: float, daily_burn: float) -> Optional[float]:
    """
    Estimate runway in days based on available cash and daily burn rate.
    
    Args:
        available_cash: Cash available (after minimum buffer)
        daily_burn: Average daily cash outlay
        
    Returns:
        Days of runway (or None if burn <= 0)
    """
    if daily_burn <= 0:
        return None
    
    return available_cash / daily_burn


def classify_business_health_risk(
    cash_runway_days: Optional[float],
    current_health_score: float,
) -> str:
    """
    Classify overall business health and risk.
    
    Args:
        cash_runway_days: Projected runway in days (or None)
        current_health_score: Health score from Financial State Engine (0-100)
        
    Returns:
        Classification: "excellent", "good", "fair", "poor", "critical"
    """
    if current_health_score >= 80:
        return "excellent"
    elif current_health_score >= 60:
        return "good"
    elif current_health_score >= 40:
        return "fair"
    elif current_health_score >= 20:
        return "poor"
    else:
        return "critical"


def explain_severity_change(
    previous_worst_severity: str,
    current_worst_severity: str,
    previous_shortfall_date: Optional[str],
    current_shortfall_date: Optional[str],
) -> str:
    """
    Explain what changed in risk severity from previous to current analysis.
    
    Args:
        previous_worst_severity: Worst case severity from last analysis
        current_worst_severity: Worst case severity from current analysis
        previous_shortfall_date: Shortfall date from last analysis
        current_shortfall_date: Shortfall date from current analysis
        
    Returns:
        Explanation text
    """
    severity_order = {"safe": 0, "caution": 1, "warning": 2, "critical": 3}
    prev_rank = severity_order.get(previous_worst_severity, 0)
    curr_rank = severity_order.get(current_worst_severity, 0)
    
    if curr_rank > prev_rank:
        return f"⚠ Risk deteriorated: {previous_worst_severity} → {current_worst_severity}"
    elif curr_rank < prev_rank:
        return f"✓ Risk improved: {previous_worst_severity} → {current_worst_severity}"
    elif previous_shortfall_date != current_shortfall_date:
        if previous_shortfall_date and current_shortfall_date:
            return f"Shortfall timing shifted: {previous_shortfall_date} → {current_shortfall_date}"
        elif previous_shortfall_date:
            return "Shortfall risk removed"
        else:
            return "New shortfall risk detected"
    else:
        return "Risk profile unchanged"


# Severity message templates
SEVERITY_MESSAGES = {
    "safe": {
        "title": "Green Light",
        "description": "Cash position is strong and stable.",
        "action": "Maintain current trajectory.",
    },
    "caution": {
        "title": "Yellow Flag",
        "description": "Cash position shows potential stress points.",
        "action": "Prepare contingency plans. Monitor closely.",
    },
    "warning": {
        "title": "Red Alert",
        "description": "Cash constraints likely within timeline.",
        "action": "Implement mitigation measures. Escalate to leadership.",
    },
    "critical": {
        "title": "Emergency",
        "description": "Immediate cash crisis likely.",
        "action": "Take action NOW. All options on table.",
    },
}


def get_severity_message(severity: str) -> Dict[str, str]:
    """
    Get structured message for a severity level.
    
    Args:
        severity: Severity level
        
    Returns:
        Dict with title, description, action
    """
    return SEVERITY_MESSAGES.get(severity, SEVERITY_MESSAGES["safe"])
