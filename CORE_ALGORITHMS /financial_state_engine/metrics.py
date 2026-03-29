"""
Metrics calculation module for Financial State Engine.

Computes intermediate metrics like runway, obligation pressure, buffer sufficiency
that feed into the health score calculation.
"""

from typing import List, Optional
from .models import CashFlowEvent
from .utils import get_today


def calculate_runway_days(
    cash_flow_timeline: List[CashFlowEvent],
    min_cash_buffer: float,
    time_horizon_days: int
) -> Optional[int]:
    """
    Calculate cash runway: days until balance falls below minimum buffer.
    
    Analyzes the cash flow timeline to find the first date where the cumulative
    balance drops below the minimum required buffer. This signals urgency.
    
    Args:
        cash_flow_timeline: List of CashFlowEvent objects (should be sorted by date)
        min_cash_buffer: Minimum cash buffer threshold
        time_horizon_days: Maximum horizon to consider
        
    Returns:
        Number of days until breach, or None if stable within horizon
        (Returns None if no breach will occur, or time_horizon_days if stable)
    """
    if not cash_flow_timeline:
        # No events = stable, no breach predicted
        return time_horizon_days
    
    for i, event in enumerate(cash_flow_timeline):
        if event.balance < min_cash_buffer:
            # Found the breach date - return days from start
            # Assuming first event is on day 1 or later
            return i + 1  # Day number in the timeline
    
    # No breach within horizon
    return None


def calculate_obligation_pressure_ratio(
    total_payables_within_horizon: float,
    available_cash: float,
    weighted_receivables: float
) -> float:
    """
    Calculate obligation pressure ratio.
    
    Measures how tight the cash situation is:
    Pressure Ratio = Total Payables / (Available Cash + Weighted Receivables)
    
    Interpretation:
    - ≤ 0.5: Comfortable (lots of room)
    - 0.5-1.0: Manageable
    - 1.0-2.0: Stretched (tight)
    - 2.0-3.0: Very tight
    - > 3.0: Critical/Unsustainable
    
    Args:
        total_payables_within_horizon: Total payables due within forecast horizon
        available_cash: Cash available after buffer
        weighted_receivables: Confidence-weighted incoming cash
        
    Returns:
        Ratio (0.0 to infinity)
    """
    denominator = available_cash + weighted_receivables
    
    # Handle edge cases
    if denominator <= 0:
        # No positive cash position - critical situation
        if total_payables_within_horizon > 0:
            return 3.0  # Signal as critical
        else:
            return 0.0  # No obligations either
    
    if total_payables_within_horizon <= 0:
        return 0.0  # No obligations
    
    ratio = total_payables_within_horizon / denominator
    return ratio


def calculate_buffer_sufficiency_days(
    min_cash_buffer: float,
    avg_daily_outflow: float
) -> float:
    """
    Calculate how many days the minimum buffer lasts at current burn rate.
    
    Estimates buffer longevity: Buffer Sufficiency = Min Buffer / Avg Daily Outflow
    
    Args:
        min_cash_buffer: Minimum buffer amount in INR
        avg_daily_outflow: Average daily outflow/burn rate in INR
        
    Returns:
        Number of days the buffer can sustain (0.0 to infinity)
    """
    if avg_daily_outflow <= 0:
        return float('inf')  # No outflow = buffer lasts infinitely
    
    if min_cash_buffer <= 0:
        return 0.0  # No buffer
    
    days = min_cash_buffer / avg_daily_outflow
    return days


def calculate_average_daily_outflow(
    cash_flow_timeline: List[CashFlowEvent],
    time_horizon_days: int
) -> float:
    """
    Calculate average daily outflow from cash flow timeline.
    
    Args:
        cash_flow_timeline: List of CashFlowEvent objects
        time_horizon_days: Total days in forecast horizon
        
    Returns:
        Average daily outflow in INR
    """
    if not cash_flow_timeline or time_horizon_days == 0:
        return 0.0
    
    total_outflow = sum(event.outflow for event in cash_flow_timeline)
    avg = total_outflow / time_horizon_days
    return avg


def calculate_average_daily_inflow(
    cash_flow_timeline: List[CashFlowEvent],
    time_horizon_days: int
) -> float:
    """
    Calculate average daily inflow from cash flow timeline.
    
    Args:
        cash_flow_timeline: List of CashFlowEvent objects
        time_horizon_days: Total days in forecast horizon
        
    Returns:
        Average daily inflow in INR
    """
    if not cash_flow_timeline or time_horizon_days == 0:
        return 0.0
    
    total_inflow = sum(event.inflow for event in cash_flow_timeline)
    avg = total_inflow / time_horizon_days
    return avg


def calculate_net_cash_flow(cash_flow_timeline: List[CashFlowEvent]) -> float:
    """
    Calculate total net cash flow over the timeline period.
    
    Args:
        cash_flow_timeline: List of CashFlowEvent objects
        
    Returns:
        Net flow (inflows - outflows) in INR
    """
    total_inflow = sum(event.inflow for event in cash_flow_timeline)
    total_outflow = sum(event.outflow for event in cash_flow_timeline)
    return total_inflow - total_outflow


def score_runway_component(runway_days: Optional[int]) -> float:
    """
    Score the runway component (0-100).
    
    Thresholds:
    - ≥ 30 days → 100 (excellent)
    - ≥ 14 days → 75 (good)
    - ≥ 7 days → 50 (caution)
    - ≥ 2 days → 25 (warning)
    - < 2 days → 0 (critical)
    
    Args:
        runway_days: Days until buffer breach, or None if stable
        
    Returns:
        Score (0-100)
    """
    if runway_days is None:
        return 100  # Stable
    
    if runway_days >= 30:
        return 100
    elif runway_days >= 14:
        return 75
    elif runway_days >= 7:
        return 50
    elif runway_days >= 2:
        return 25
    else:
        return 0


def score_obligation_pressure_component(pressure_ratio: float) -> float:
    """
    Score the obligation pressure component (0-100).
    
    Thresholds:
    - ≤ 0.5 → 100 (comfortable)
    - ≤ 1.0 → 75 (manageable)
    - ≤ 2.0 → 50 (stretched)
    - ≤ 3.0 → 25 (tight)
    - > 3.0 → 0 (unsustainable)
    
    Args:
        pressure_ratio: Obligation pressure ratio
        
    Returns:
        Score (0-100)
    """
    if pressure_ratio <= 0.5:
        return 100
    elif pressure_ratio <= 1.0:
        return 75
    elif pressure_ratio <= 2.0:
        return 50
    elif pressure_ratio <= 3.0:
        return 25
    else:
        return 0


def score_receivable_quality_component(quality_score: float) -> float:
    """
    Score the receivable quality component (0-100).
    
    Thresholds:
    - ≥ 0.8 → 100 (highly reliable)
    - ≥ 0.6 → 75 (mostly reliable)
    - ≥ 0.4 → 50 (moderately risky)
    - < 0.4 → 25 (very risky)
    
    Note: If no receivables (quality = 0), score 0 (risky due to no incoming cash).
    
    Args:
        quality_score: Receivable quality score (0.0-1.0)
        
    Returns:
        Score (0-100)
    """
    if quality_score >= 0.8:
        return 100
    elif quality_score >= 0.6:
        return 75
    elif quality_score >= 0.4:
        return 50
    elif quality_score > 0.0:
        return 25
    else:
        # No receivables at all = zero quality
        return 0


def score_buffer_sufficiency_component(buffer_days: float) -> float:
    """
    Score the buffer sufficiency component (0-100).
    
    Thresholds:
    - ≥ 10 days → 100 (solid buffer)
    - ≥ 5 days → 75
    - ≥ 2 days → 50
    - < 2 days → 0 (insufficient)
    
    Note: Infinite buffer treated as 100.
    
    Args:
        buffer_days: Days the buffer can sustain current burn
        
    Returns:
        Score (0-100)
    """
    if buffer_days == float('inf'):
        return 100
    
    if buffer_days >= 10:
        return 100
    elif buffer_days >= 5:
        return 75
    elif buffer_days >= 2:
        return 50
    else:
        return 0


def get_limiting_factor(
    runway_days: Optional[int],
    pressure_ratio: float,
    quality_score: float,
    buffer_days: float
) -> str:
    """
    Identify which metric is most problematic (limiting factor).
    
    Args:
        runway_days: Days until buffer breach
        pressure_ratio: Obligation pressure ratio
        quality_score: Receivable quality (0.0-1.0)
        buffer_days: Buffer sufficiency in days
        
    Returns:
        String identifying the limiting factor
    """
    scores = {
        "runway": score_runway_component(runway_days),
        "pressure": score_obligation_pressure_component(pressure_ratio),
        "quality": score_receivable_quality_component(quality_score),
        "buffer": score_buffer_sufficiency_component(buffer_days)
    }
    
    # Find the component with the lowest score
    limiting = min(scores.items(), key=lambda x: x[1])
    return limiting[0]
