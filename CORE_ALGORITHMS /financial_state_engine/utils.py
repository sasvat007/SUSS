"""
Utility functions for the Financial State Engine.

Helpers for date arithmetic, calculations, and common operations.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import json


def parse_date(date_str: str) -> datetime:
    """
    Parse date string in YYYY-MM-DD format.
    
    Args:
        date_str: Date string
        
    Returns:
        datetime object
    """
    return datetime.strptime(date_str, "%Y-%m-%d")


def date_to_str(date_obj: datetime) -> str:
    """
    Convert datetime to YYYY-MM-DD string.
    
    Args:
        date_obj: datetime object
        
    Returns:
        Date string in YYYY-MM-DD format
    """
    return date_obj.strftime("%Y-%m-%d")


def get_today() -> str:
    """Get today's date as YYYY-MM-DD string."""
    return date_to_str(datetime.now())


def get_date_n_days_ahead(days: int, reference_date: str = None) -> str:
    """
    Get a date N days ahead of reference date.
    
    Args:
        days: Number of days ahead
        reference_date: Reference date as YYYY-MM-DD (default: today)
        
    Returns:
        Date string in YYYY-MM-DD format
    """
    if reference_date is None:
        reference_date = get_today()
    
    ref_datetime = parse_date(reference_date)
    future_datetime = ref_datetime + timedelta(days=days)
    return date_to_str(future_datetime)


def days_between(date1_str: str, date2_str: str) -> int:
    """
    Calculate days between two dates.
    
    Args:
        date1_str: First date as YYYY-MM-DD
        date2_str: Second date as YYYY-MM-DD
        
    Returns:
        Number of days (can be negative if date1 > date2)
    """
    date1 = parse_date(date1_str)
    date2 = parse_date(date2_str)
    return (date2 - date1).days


def is_date_past(date_str: str, reference_date: str = None) -> bool:
    """
    Check if a date is in the past relative to reference date.
    
    Args:
        date_str: Date to check as YYYY-MM-DD
        reference_date: Reference date as YYYY-MM-DD (default: today)
        
    Returns:
        True if date is in the past
    """
    if reference_date is None:
        reference_date = get_today()
    
    return days_between(date_str, reference_date) > 0


def is_date_today(date_str: str, reference_date: str = None) -> bool:
    """
    Check if a date is today (relative to reference date).
    
    Args:
        date_str: Date to check as YYYY-MM-DD
        reference_date: Reference date as YYYY-MM-DD (default: today)
        
    Returns:
        True if date is today
    """
    if reference_date is None:
        reference_date = get_today()
    
    return days_between(date_str, reference_date) == 0


def is_date_in_future(date_str: str, days_ahead: int, reference_date: str = None) -> bool:
    """
    Check if a date is within N days in the future.
    
    Args:
        date_str: Date to check as YYYY-MM-DD
        days_ahead: Number of days to look ahead
        reference_date: Reference date as YYYY-MM-DD (default: today)
        
    Returns:
        True if date is between today and today + days_ahead (inclusive)
    """
    if reference_date is None:
        reference_date = get_today()
    
    days_diff = days_between(reference_date, date_str)
    return 0 <= days_diff <= days_ahead


def get_next_occurrence_of_recurring_transaction(
    next_date_str: str,
    frequency: str,
    reference_date: str = None
) -> str:
    """
    Get the next occurrence date(s) of a recurring transaction within time horizon.
    
    Args:
        next_date_str: Current next occurrence date as YYYY-MM-DD
        frequency: Frequency ("weekly", "biweekly", "monthly", "quarterly", "yearly")
        reference_date: Reference date (default: today)
        
    Returns:
        Date string of next occurrence that falls on or after reference_date
    """
    if reference_date is None:
        reference_date = get_today()
    
    next_dt = parse_date(next_date_str)
    ref_dt = parse_date(reference_date)
    
    # Map frequency to days
    frequency_map = {
        "weekly": 7,
        "biweekly": 14,
        "monthly": 30,  # Not precise, but reasonable for short horizons
        "quarterly": 90,
        "yearly": 365
    }
    
    days_to_add = frequency_map.get(frequency, 30)
    
    # If next_date is already in the future of reference date, return it
    if next_dt >= ref_dt:
        return date_to_str(next_dt)
    
    # Otherwise, increment until we're past reference date
    while next_dt < ref_dt:
        next_dt += timedelta(days=days_to_add)
    
    return date_to_str(next_dt)


def get_all_occurrences_of_recurring_transaction(
    next_date_str: str,
    frequency: str,
    time_horizon_days: int,
    reference_date: str = None
) -> List[str]:
    """
    Get all occurrences of a recurring transaction within time horizon.
    
    Args:
        next_date_str: First occurrence date as YYYY-MM-DD
        frequency: Frequency string
        time_horizon_days: Number of days to look ahead
        reference_date: Reference date (default: today)
        
    Returns:
        List of occurrence dates as YYYY-MM-DD strings
    """
    if reference_date is None:
        reference_date = get_today()
    
    occurrences = []
    frequency_map = {
        "weekly": 7,
        "biweekly": 14,
        "monthly": 30,
        "quarterly": 90,
        "yearly": 365
    }
    
    days_to_add = frequency_map.get(frequency, 30)
    horizon_end = get_date_n_days_ahead(time_horizon_days, reference_date)
    
    current_date = parse_date(next_date_str)
    ref_dt = parse_date(reference_date)
    horizon_dt = parse_date(horizon_end)
    
    # Start from the reference date or later
    if current_date < ref_dt:
        days_past = (ref_dt - current_date).days
        # Calculate how many cycles have passed
        cycles = (days_past // days_to_add) + 1
        current_date = parse_date(next_date_str) + timedelta(days=cycles * days_to_add)
    
    # Collect all occurrences within horizon
    while current_date <= horizon_dt:
        occurrences.append(date_to_str(current_date))
        current_date += timedelta(days=days_to_add)
    
    return occurrences


def round_to_cents(amount: float) -> float:
    """
    Round amount to nearest cent (for INR, 2 decimal places).
    
    Args:
        amount: Amount in INR
        
    Returns:
        Rounded amount
    """
    return round(amount, 2)


def to_json_serializable(obj: Any) -> Any:
    """
    Convert object to JSON-serializable format.
    
    Handles common types and dataclasses.
    
    Args:
        obj: Object to convert
        
    Returns:
        JSON-serializable object
    """
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif isinstance(obj, (list, tuple)):
        return [to_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: to_json_serializable(val) for key, val in obj.items()}
    elif isinstance(obj, (datetime, )):
        return obj.isoformat()
    else:
        return obj


def pretty_json(obj: Any, indent: int = 2) -> str:
    """
    Convert object to pretty-printed JSON string.
    
    Args:
        obj: Object to convert
        indent: Indentation level
        
    Returns:
        JSON string
    """
    return json.dumps(to_json_serializable(obj), indent=indent, default=str)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp value between min and max.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(value, max_val))
