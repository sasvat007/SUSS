"""
Risk simulator for Risk Detection Engine.

Simulates day-by-day cash flow for each scenario, producing detailed timelines
with exact balance tracking.
"""

from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from financial_state_engine.models import (
    Receivable, Payable, HiddenTransaction, CashFlowEvent
)
from financial_state_engine.utils import (
    parse_date, date_to_str, get_date_n_days_ahead,
    is_date_in_future, get_all_occurrences_of_recurring_transaction
)


def simulate_scenario_timeline(
    starting_balance: float,
    min_cash_buffer: float,
    receivables: List[Receivable],
    payables: List[Payable],
    hidden_transactions: List[HiddenTransaction],
    time_horizon_days: int,
    reference_date: str = None
) -> List[CashFlowEvent]:
    """
    Simulate day-by-day cash flow for a scenario.
    
    Args:
        starting_balance: Current account balance
        min_cash_buffer: Minimum buffer to maintain
        receivables: Adapted receivables for scenario
        payables: Adapted payables for scenario
        hidden_transactions: Hidden transactions for scenario
        time_horizon_days: Forecast horizon in days
        reference_date: Reference date (YYYY-MM-DD, default: today)
        
    Returns:
        List of CashFlowEvent objects for each day with activity
    """
    if reference_date is None:
        from financial_state_engine.utils import get_today
        reference_date = get_today()
    
    timeline = []
    current_balance_sim = starting_balance
    
    # Build dictionary of all events by date
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
            # Use full amount (already confidence-weighted by adaptation)
            events_by_date[receivable.expected_date]["inflow"] += receivable.amount
            events_by_date[receivable.expected_date]["descriptions"].append(
                f"Receivable: {receivable.description}"
            )
    
    # Add hidden transactions
    for hidden_tx in hidden_transactions:
        occurrence_dates = get_all_occurrences_of_recurring_transaction(
            hidden_tx.next_date,
            hidden_tx.frequency,
            time_horizon_days,
            reference_date
        )
        
        for occ_date in occurrence_dates:
            if occ_date not in events_by_date:
                events_by_date[occ_date] = {
                    "inflow": 0.0,
                    "outflow": 0.0,
                    "descriptions": []
                }
            
            if hidden_tx.amount > 0:
                events_by_date[occ_date]["outflow"] += hidden_tx.amount
            else:
                events_by_date[occ_date]["inflow"] += abs(hidden_tx.amount)
            
            events_by_date[occ_date]["descriptions"].append(
                f"Hidden: {hidden_tx.category}"
            )
    
    # Build timeline in chronological order
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


def extract_timeline_metrics(
    timeline: List[CashFlowEvent],
    min_cash_buffer: float
) -> Tuple[float, str, float]:
    """
    Extract key metrics from a timeline.
    
    Args:
        timeline: List of CashFlowEvent objects
        min_cash_buffer: Minimum buffer threshold
        
    Returns:
        Tuple of (minimum_balance, minimum_balance_date, available_cash_at_minimum)
    """
    if not timeline:
        return 0.0, "", 0.0
    
    # Find minimum balance
    min_event = min(timeline, key=lambda e: e.balance)
    
    available_at_min = min_event.balance - min_cash_buffer
    
    return min_event.balance, min_event.date, available_at_min


def calculate_deficit_metrics(
    timeline: List[CashFlowEvent],
    min_cash_buffer: float
) -> Tuple[int, float, float]:
    """
    Calculate deficit-related metrics from timeline.
    
    Args:
        timeline: List of CashFlowEvent objects
        min_cash_buffer: Minimum cash threshold
        
    Returns:
        Tuple of (total_deficit_days, max_deficit_amount, deficit_depth)
    """
    deficit_days = 0
    max_deficit = 0.0
    
    for event in timeline:
        available_cash = event.balance - min_cash_buffer
        
        if available_cash < 0:
            deficit_days += 1
            deficit_amount = abs(available_cash)
            if deficit_amount > max_deficit:
                max_deficit = deficit_amount
    
    return deficit_days, max_deficit, max_deficit


def find_recovery_date(
    timeline: List[CashFlowEvent],
    min_cash_buffer: float
) -> Tuple[bool, str]:
    """
    Find when cash position recovers to positive (if at all).
    
    Args:
        timeline: List of CashFlowEvent objects
        min_cash_buffer: Minimum cash threshold
        
    Returns:
        Tuple of (recovered: bool, recovery_date: str or "")
    """
    in_deficit = False
    
    for event in timeline:
        available_cash = event.balance - min_cash_buffer
        
        if available_cash < 0 and not in_deficit:
            in_deficit = True
        elif available_cash >= 0 and in_deficit:
            # Recovery point found
            return True, event.date
    
    return False, ""


def get_timeline_events_dict(timeline: List[CashFlowEvent]) -> List[Dict]:
    """
    Convert timeline events to dictionary format for JSON serialization.
    
    Args:
        timeline: List of CashFlowEvent objects
        
    Returns:
        List of dictionaries
    """
    return [event.to_dict() for event in timeline]
