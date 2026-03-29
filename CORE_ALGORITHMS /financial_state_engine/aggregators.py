"""
Aggregation module for Financial State Engine.

Consolidates inputs into computed quantities like available cash, payables buckets,
weighted receivables, and cash flow timelines.
"""

from typing import List, Tuple, Dict
from datetime import datetime
from .models import (
    Transaction, Payable, Receivable, HiddenTransaction, 
    BusinessContext, CashFlowEvent
)
from .utils import (
    parse_date, date_to_str, get_date_n_days_ahead, days_between,
    is_date_in_future, get_all_occurrences_of_recurring_transaction
)


def compute_available_cash(
    current_balance: float,
    min_cash_buffer: float
) -> float:
    """
    Calculate available cash after subtracting minimum buffer.
    
    Available cash = current balance - min buffer
    (Can be negative if business is in distress)
    
    Args:
        current_balance: Current account balance in INR
        min_cash_buffer: Minimum cash buffer to maintain in INR
        
    Returns:
        Available cash in INR
    """
    return current_balance - min_cash_buffer


def aggregate_payables_by_timeline(
    payables: List[Payable],
    time_horizon_days: int,
    reference_date: str = None
) -> Tuple[float, float, float]:
    """
    Aggregate payables into buckets: due now, due soon, due later.
    
    Args:
        payables: List of payables
        time_horizon_days: Days to look ahead for "due soon"
        reference_date: Reference date as YYYY-MM-DD (default: today)
        
    Returns:
        Tuple of (due_now, due_soon, due_later)
        - due_now: Payables due today or overdue
        - due_soon: Payables due within horizon (not including due_now)
        - due_later: Payables due after horizon
    """
    if reference_date is None:
        from .utils import get_today
        reference_date = get_today()
    
    due_now = 0.0
    due_soon = 0.0
    due_later = 0.0
    
    horizon_end_date = get_date_n_days_ahead(time_horizon_days, reference_date)
    
    for payable in payables:
        # Skip already paid payables
        if payable.status == "paid":
            continue
        
        due_date_dt = parse_date(payable.due_date)
        ref_dt = parse_date(reference_date)
        horizon_dt = parse_date(horizon_end_date)
        
        if due_date_dt <= ref_dt:
            # Due now or overdue
            due_now += payable.amount
        elif due_date_dt <= horizon_dt:
            # Due soon (within horizon)
            due_soon += payable.amount
        else:
            # Due later (after horizon)
            due_later += payable.amount
    
    return due_now, due_soon, due_later


def aggregate_payables_all(payables: List[Payable]) -> float:
    """
    Calculate total of all payables (excluding paid ones).
    
    Args:
        payables: List of payables
        
    Returns:
        Total in INR
    """
    total = 0.0
    for payable in payables:
        if payable.status != "paid":
            total += payable.amount
    return total


def compute_weighted_receivables(
    receivables: List[Receivable],
    time_horizon_days: int,
    reference_date: str = None
) -> Tuple[float, float]:
    """
    Calculate confidence-weighted sum of receivables within horizon.
    
    Weighted Receivables = Sum(Amount × Confidence) for receivables within horizon
    
    Args:
        receivables: List of receivables
        time_horizon_days: Days to look ahead
        reference_date: Reference date as YYYY-MM-DD (default: today)
        
    Returns:
        Tuple of (weighted_total, unweighted_total) within horizon
    """
    if reference_date is None:
        from .utils import get_today
        reference_date = get_today()
    
    weighted_total = 0.0
    unweighted_total = 0.0
    horizon_end_date = get_date_n_days_ahead(time_horizon_days, reference_date)
    
    for receivable in receivables:
        # Skip already received or cancelled receivables
        if receivable.status in ["received", "cancelled"]:
            continue
        
        # Only include receivables within horizon
        if is_date_in_future(receivable.expected_date, time_horizon_days, reference_date):
            unweighted_total += receivable.amount
            weighted_amount = receivable.amount * receivable.confidence
            weighted_total += weighted_amount
    
    return weighted_total, unweighted_total


def compute_receivable_quality_score(
    weighted_receivables: float,
    unweighted_receivables: float
) -> float:
    """
    Calculate quality score of receivables (confidence indicator).
    
    Quality Score = Weighted / Unweighted
    - 1.0 = all highly confident
    - 0.5 = moderate confidence
    - <0.5 = risky, many low-confidence receivables
    
    Args:
        weighted_receivables: Sum of amount × confidence
        unweighted_receivables: Total amount without confidence
        
    Returns:
        Quality score (0.0-1.0)
    """
    if unweighted_receivables == 0:
        return 0.0  # No receivables = no quality to assess
    
    quality = weighted_receivables / unweighted_receivables
    # Clamp to ensure valid range
    return max(0.0, min(quality, 1.0))


def aggregate_hidden_transactions_in_horizon(
    hidden_transactions: List[HiddenTransaction],
    time_horizon_days: int,
    reference_date: str = None
) -> Tuple[float, List[Tuple[str, float, str]]]:
    """
    Aggregate hidden (recurring) transactions within horizon.
    
    Returns total outflow from hidden transactions and list of occurrences.
    
    Args:
        hidden_transactions: List of hidden transactions
        time_horizon_days: Days to look ahead
        reference_date: Reference date as YYYY-MM-DD (default: today)
        
    Returns:
        Tuple of (total_outflow, list_of_occurrences)
        Each occurrence is (date_str, amount, category)
    """
    if reference_date is None:
        from .utils import get_today
        reference_date = get_today()
    
    total_outflow = 0.0
    occurrences = []
    
    for hidden_tx in hidden_transactions:
        # Get all occurrences within horizon
        occurrence_dates = get_all_occurrences_of_recurring_transaction(
            hidden_tx.next_date,
            hidden_tx.frequency,
            time_horizon_days,
            reference_date
        )
        
        for occ_date in occurrence_dates:
            amount = hidden_tx.amount
            if amount > 0:
                # Treat positive amount as outflow
                pass
            else:
                # Negative amount is inflow
                amount = abs(amount)
            
            total_outflow += hidden_tx.amount  # Add signed amount
            occurrences.append((occ_date, hidden_tx.amount, hidden_tx.category))
    
    return total_outflow, occurrences


def build_cash_flow_timeline(
    current_balance: float,
    payables: List[Payable],
    receivables: List[Receivable],
    hidden_transactions: List[HiddenTransaction],
    time_horizon_days: int,
    reference_date: str = None
) -> List[CashFlowEvent]:
    """
    Build a day-by-day cash flow timeline for the forecast horizon.
    
    Simulates cash position by aggregating inflows (receivables, income) and
    outflows (payables, expenses) for each day within the horizon.
    
    Args:
        current_balance: Starting balance in INR
        payables: List of payables
        receivables: List of receivables
        hidden_transactions: List of recurring transactions
        time_horizon_days: Number of days to forecast
        reference_date: Reference date as YYYY-MM-DD (default: today)
        
    Returns:
        List of CashFlowEvent objects for each day with activity
    """
    if reference_date is None:
        from .utils import get_today
        reference_date = get_today()
    
    timeline = []
    current_balance_sim = current_balance
    ref_dt = parse_date(reference_date)
    horizon_end = get_date_n_days_ahead(time_horizon_days, reference_date)
    
    # Build a dictionary of all events by date
    events_by_date: Dict[str, Dict] = {}
    
    # Add payables
    for payable in payables:
        if payable.status == "paid":
            continue
        if is_date_in_future(payable.due_date, time_horizon_days, reference_date):
            if payable.due_date not in events_by_date:
                events_by_date[payable.due_date] = {
                    "inflow": 0.0,
                    "outflow": 0.0,
                    "descriptions": []
                }
            events_by_date[payable.due_date]["outflow"] += payable.amount
            events_by_date[payable.due_date]["descriptions"].append(
                f"Payable: {payable.description}"
            )
    
    # Add receivables
    for receivable in receivables:
        if receivable.status in ["received", "cancelled"]:
            continue
        if is_date_in_future(receivable.expected_date, time_horizon_days, reference_date):
            if receivable.expected_date not in events_by_date:
                events_by_date[receivable.expected_date] = {
                    "inflow": 0.0,
                    "outflow": 0.0,
                    "descriptions": []
                }
            # Only count weighted amount (confidence-adjusted)
            weighted_amount = receivable.amount * receivable.confidence
            events_by_date[receivable.expected_date]["inflow"] += weighted_amount
            events_by_date[receivable.expected_date]["descriptions"].append(
                f"Receivable: {receivable.description} (confidence: {receivable.confidence})"
            )
    
    # Add hidden transactions
    _, hidden_occurrences = aggregate_hidden_transactions_in_horizon(
        hidden_transactions,
        time_horizon_days,
        reference_date
    )
    
    for occ_date, amount, category in hidden_occurrences:
        if occ_date not in events_by_date:
            events_by_date[occ_date] = {
                "inflow": 0.0,
                "outflow": 0.0,
                "descriptions": []
            }
        
        if amount > 0:
            events_by_date[occ_date]["outflow"] += amount
        else:
            events_by_date[occ_date]["inflow"] += abs(amount)
        
        events_by_date[occ_date]["descriptions"].append(
            f"Recurring: {category}"
        )
    
    # Build timeline events in chronological order
    sorted_dates = sorted(events_by_date.keys())
    
    for date_str in sorted_dates:
        event_data = events_by_date[date_str]
        inflow = event_data["inflow"]
        outflow = event_data["outflow"]
        
        current_balance_sim = current_balance_sim + inflow - outflow
        
        event = CashFlowEvent(
            date=date_str,
            inflow=inflow,
            outflow=outflow,
            balance=current_balance_sim,
            events=event_data["descriptions"]
        )
        timeline.append(event)
    
    return timeline


def calculate_total_payables_within_horizon(
    payables: List[Payable],
    time_horizon_days: int,
    reference_date: str = None
) -> float:
    """
    Calculate total payables due within horizon (includes due now + due soon).
    
    Args:
        payables: List of payables
        time_horizon_days: Days to look ahead
        reference_date: Reference date as YYYY-MM-DD (default: today)
        
    Returns:
        Total in INR
    """
    due_now, due_soon, _ = aggregate_payables_by_timeline(
        payables, time_horizon_days, reference_date
    )
    return due_now + due_soon
