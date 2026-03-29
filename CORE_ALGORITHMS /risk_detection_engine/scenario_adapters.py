"""
Scenario adapters for Risk Detection Engine.

Adapts FinancialState data into different scenario configurations (best/base/worst)
without modifying the original data.
"""

from typing import List, Tuple
from financial_state_engine.models import (
    Receivable, Payable, HiddenTransaction, BusinessContext
)
from .models import ScenarioConfig


def adapt_receivables_for_scenario(
    receivables: List[Receivable],
    config: ScenarioConfig,
    avg_payment_delay_days: int
) -> List[Receivable]:
    """
    Adapt receivables list for a specific scenario.
    
    Creates a new list (non-destructive) with:
    - Filtered receivables based on confidence threshold
    - Shifted dates if delays apply
    - Amount adjusted by confidence if use_full_confidence=False
    
    Args:
        receivables: Original list of receivables
        config: Scenario configuration
        avg_payment_delay_days: Days to shift for delay scenarios
        
    Returns:
        Adapted list of receivables (non-destructive copy)
    """
    adapted = []
    
    for receivable in receivables:
        # Skip if confidence below threshold
        if receivable.confidence < config.min_confidence_threshold:
            continue
        
        # Skip if already received or cancelled
        if receivable.status in ["received", "cancelled"]:
            continue
        
        # Calculate adapted expected date
        expected_date = receivable.expected_date
        if config.apply_payment_delays and avg_payment_delay_days > 0:
            # Shift date forward by delay
            from financial_state_engine.utils import (
                parse_date, date_to_str
            )
            from datetime import timedelta
            
            orig_date = parse_date(expected_date)
            shifted_date = orig_date + timedelta(days=avg_payment_delay_days)
            expected_date = date_to_str(shifted_date)
        
        # Calculate adapted amount (apply confidence weighting if not using full confidence)
        adapted_amount = receivable.amount
        if not config.use_full_confidence:
            # In non-optimistic scenarios, reduce amount by confidence 
            # E.g., 70% confidence = expect 70% of the amount
            adapted_amount = receivable.amount * receivable.confidence
        
        # Create adapted receivable
        adapted_receivable = Receivable(
            id=receivable.id,
            amount=adapted_amount,
            expected_date=expected_date,
            description=receivable.description,
            confidence=receivable.confidence,
            status=receivable.status,
            category=receivable.category
        )
        adapted.append(adapted_receivable)
    
    return adapted


def adapt_payables_for_scenario(
    payables: List[Payable],
    config: ScenarioConfig
) -> List[Payable]:
    """
    Adapt payables list for a specific scenario.
    
    For now, payables are the same across scenarios (we assume supplier
    payment terms don't change). Creates a non-destructive copy.
    
    Args:
        payables: Original list of payables
        config: Scenario configuration (included for consistency)
        
    Returns:
        Adapted list of payables (copy)
    """
    # Skip paid payables
    adapted = [
        Payable(
            id=p.id,
            amount=p.amount,
            due_date=p.due_date,
            description=p.description,
            status=p.status,
            priority_level=p.priority_level,
            category=p.category
        )
        for p in payables
        if p.status != "paid"
    ]
    
    return adapted


def adapt_hidden_transactions_for_scenario(
    hidden_transactions: List[HiddenTransaction],
    config: ScenarioConfig
) -> List[HiddenTransaction]:
    """
    Adapt hidden transactions for a specific scenario.
    
    Hidden transactions (salary, subscriptions) are generally more certain
    than customer receivables, so they're included in all scenarios.
    
    Args:
        hidden_transactions: Original list of hidden transactions
        config: Scenario configuration (included for consistency)
        
    Returns:
        Adapted list (copy) of hidden transactions
    """
    adapted = [
        HiddenTransaction(
            id=ht.id,
            transaction_type=ht.transaction_type,
            amount=ht.amount,
            frequency=ht.frequency,
            next_date=ht.next_date,
            category=ht.category,
            notes=ht.notes
        )
        for ht in hidden_transactions
    ]
    
    return adapted


def create_scenario_snapshot(
    receivables: List[Receivable],
    payables: List[Payable],
    hidden_transactions: List[HiddenTransaction],
    config: ScenarioConfig,
    avg_payment_delay_days: int
) -> Tuple[List[Receivable], List[Payable], List[HiddenTransaction]]:
    """
    Create a complete adapted data snapshot for a scenario.
    
    Combines all adapters into one non-destructive operation.
    
    Args:
        receivables: Original receivables
        payables: Original payables
        hidden_transactions: Original hidden transactions
        config: Scenario configuration
        avg_payment_delay_days: Payment delay setting
        
    Returns:
        Tuple of (adapted_receivables, adapted_payables, adapted_hidden_transactions)
    """
    adapted_receivables = adapt_receivables_for_scenario(
        receivables, config, avg_payment_delay_days
    )
    
    adapted_payables = adapt_payables_for_scenario(payables, config)
    
    adapted_hidden_transactions = adapt_hidden_transactions_for_scenario(
        hidden_transactions, config
    )
    
    return adapted_receivables, adapted_payables, adapted_hidden_transactions


def get_scenario_description(scenario_type: str) -> str:
    """
    Get human-readable description of a scenario type.
    
    Args:
        scenario_type: "best", "base", or "worst"
        
    Returns:
        Description string
    """
    descriptions = {
        "best": "Best case: All receivables on time at full amounts",
        "base": "Base case: Expected payment delays, all receivables weighted by confidence",
        "worst": "Worst case: Low-confidence receivables excluded, delays applied"
    }
    return descriptions.get(scenario_type, "Unknown scenario")
