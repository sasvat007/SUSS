"""
Financial State Engine - Core financial modeling and analysis system.

Transforms fragmented financial data into clear, actionable insights about
short-term financial health and cash runway.

Main exports:
- compute_financial_state: Main entry point for financial state computation
- FinancialStateEngine: Low-level engine class for advanced usage
- Models: Data structure classes for inputs/outputs
"""

from .models import (
    Transaction, Payable, Receivable, HiddenTransaction,
    BusinessContext, FinancialState, HealthScoreBreakdown,
    CashFlowEvent
)
from .engine import compute_financial_state, FinancialStateEngine
from .validators import ValidationError

__all__ = [
    'compute_financial_state',
    'FinancialStateEngine',
    'Transaction',
    'Payable',
    'Receivable',
    'HiddenTransaction',
    'BusinessContext',
    'FinancialState',
    'HealthScoreBreakdown',
    'CashFlowEvent',
    'ValidationError'
]

__version__ = '0.1.0'
