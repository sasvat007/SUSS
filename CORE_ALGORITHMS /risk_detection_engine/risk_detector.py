"""
Risk detector for Risk Detection Engine.

Identifies critical risk dates and events from scenario timelines.
"""

from typing import Optional, List, Tuple
from datetime import datetime
from financial_state_engine.models import CashFlowEvent
from financial_state_engine.utils import (
    parse_date, days_between, get_today
)


def detect_first_shortfall_date(
    timeline: List[CashFlowEvent],
    min_cash_buffer: float
) -> Tuple[Optional[str], Optional[int]]:
    """
    Detect first date when available_cash (balance - min_buffer) falls below 0.
    
    Args:
        timeline: List of CashFlowEvent objects
        min_cash_buffer: Minimum buffer threshold
        
    Returns:
        Tuple of (shortfall_date: Optional[str], days_to_shortfall: Optional[int])
    """
    reference_date = get_today()
    
    for event in timeline:
        available_cash = event.balance - min_cash_buffer
        
        if available_cash < 0:
            # Found first shortfall
            days_to = days_between(reference_date, event.date)
            return event.date, days_to
    
    # No shortfall detected
    return None, None


def detect_minimum_cash_point(
    timeline: List[CashFlowEvent]
) -> Tuple[float, str, int]:
    """
    Detect the absolute minimum cash balance reached in timeline.
    
    Args:
        timeline: List of CashFlowEvent objects
        
    Returns:
        Tuple of (minimum_balance: float, minimum_date: str, days_to_minimum: int)
    """
    reference_date = get_today()
    
    if not timeline:
        return 0.0, reference_date, 0
    
    # Find minimum
    min_event = min(timeline, key=lambda e: e.balance)
    days_to = days_between(reference_date, min_event.date)
    
    return min_event.balance, min_event.date, days_to


def detect_zero_cash_date(
    timeline: List[CashFlowEvent]
) -> Optional[str]:
    """
    Detect first date when total cash balance reaches zero or goes negative.
    
    Args:
        timeline: List of CashFlowEvent objects
        
    Returns:
        Date string (or None if balance stays positive)
    """
    for event in timeline:
        if event.balance <= 0:
            return event.date
    
    return None


def count_deficit_days(
    timeline: List[CashFlowEvent],
    min_cash_buffer: float
) -> int:
    """
    Count total number of days with deficit (available_cash < 0).
    
    Args:
        timeline: List of CashFlowEvent objects
        min_cash_buffer: Minimum buffer threshold
        
    Returns:
        Number of deficit days
    """
    count = 0
    for event in timeline:
        available_cash = event.balance - min_cash_buffer
        if available_cash < 0:
            count += 1
    
    return count


def find_maximum_deficit(
    timeline: List[CashFlowEvent],
    min_cash_buffer: float
) -> float:
    """
    Find the maximum deficit amount (how deep the shortfall gets).
    
    Args:
        timeline: List of CashFlowEvent objects
        min_cash_buffer: Minimum buffer threshold
        
    Returns:
        Maximum deficit amount (absolute value)
    """
    max_deficit = 0.0
    
    for event in timeline:
        available_cash = event.balance - min_cash_buffer
        if available_cash < 0:
            deficit_amount = abs(available_cash)
            max_deficit = max(max_deficit, deficit_amount)
    
    return max_deficit


def find_recovery_date(
    timeline: List[CashFlowEvent],
    min_cash_buffer: float,
    reference_date: str = None
) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Find when (if ever) the cash position recovers to positive.
    
    Args:
        timeline: List of CashFlowEvent objects
        min_cash_buffer: Minimum buffer threshold
        reference_date: Reference date for calculating days
        
    Returns:
        Tuple of (recovered: bool, recovery_date: str or None, days_to_recovery: int or None)
    """
    if reference_date is None:
        reference_date = get_today()
    
    in_deficit = False
    
    for event in timeline:
        available_cash = event.balance - min_cash_buffer
        
        # Transition from surplus to deficit
        if available_cash < 0 and not in_deficit:
            in_deficit = True
        # Transition from deficit to surplus
        elif available_cash >= 0 and in_deficit:
            days_to = days_between(reference_date, event.date)
            return True, event.date, days_to
    
    # No recovery found
    return False, None, None


def identify_critical_risk_dates(
    timeline: List[CashFlowEvent],
    min_cash_buffer: float
) -> List[Tuple[str, str, str]]:
    """
    Identify all critical risk dates in timeline.
    
    Returns list of (date, event_type, description) tuples.
    
    Args:
        timeline: List of CashFlowEvent objects
        min_cash_buffer: Minimum buffer threshold
        
    Returns:
        List of (date, event_type, description)
    """
    critical_dates = []
    reference_date = get_today()
    
    # Find shortfall date
    shortfall_date, _ = detect_first_shortfall_date(timeline, min_cash_buffer)
    if shortfall_date:
        critical_dates.append((
            shortfall_date,
            "shortfall",
            f"Cash shortfall occurs (available cash falls below 0)"
        ))
    
    # Find minimum cash point
    min_balance, min_date, _ = detect_minimum_cash_point(timeline)
    if min_date and min_date not in [d[0] for d in critical_dates]:
        critical_dates.append((
            min_date,
            "minimum",
            f"Minimum cash point: ₹{min_balance:,.2f}"
        ))
    
    # Find zero cash date (if applicable)
    zero_date = detect_zero_cash_date(timeline)
    if zero_date and zero_date not in [d[0] for d in critical_dates]:
        critical_dates.append((
            zero_date,
            "zero_cash",
            "Total cash depletion (balance reaches 0)"
        ))
    
    # Find recovery date
    recovered, recovery_date, _ = find_recovery_date(timeline, min_cash_buffer)
    if recovered and recovery_date and recovery_date not in [d[0] for d in critical_dates]:
        critical_dates.append((
            recovery_date,
            "recovery",
            "Cash position recovers to positive"
        ))
    
    # Sort by date
    critical_dates.sort(key=lambda x: parse_date(x[0]))
    
    return critical_dates
