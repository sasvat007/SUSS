"""
Main Financial State Engine orchestrator.

Coordinates data validation, aggregation, metrics calculation, and health scoring
to produce comprehensive financial state snapshots.
"""

from typing import List, Tuple, Dict, Any
from datetime import datetime

from .models import (
    Transaction, Payable, Receivable, HiddenTransaction,
    BusinessContext, FinancialState
)
from .validators import (
    validate_all_inputs, validate_transaction, validate_payable,
    validate_receivable, validate_hidden_transaction, validate_business_context,
    ValidationError
)
from .aggregators import (
    compute_available_cash,
    aggregate_payables_by_timeline,
    aggregate_payables_all,
    compute_weighted_receivables,
    compute_receivable_quality_score,
    aggregate_hidden_transactions_in_horizon,
    build_cash_flow_timeline,
    calculate_total_payables_within_horizon
)
from .metrics import (
    calculate_runway_days,
    calculate_obligation_pressure_ratio,
    calculate_buffer_sufficiency_days,
    calculate_average_daily_outflow,
    get_limiting_factor
)
from .health_scorer import (
    compute_health_score,
    generate_health_reasoning,
    generate_health_status_flags
)
from .utils import get_today, round_to_cents


class FinancialStateEngine:
    """
    Main engine for computing financial state.
    
    This class orchestrates all sub-modules to produce a comprehensive
    financial state snapshot from raw inputs.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the engine.
        
        Args:
            verbose: If True, log intermediate calculations
        """
        self.verbose = verbose
    
    def _log(self, message: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(f"[FinancialStateEngine] {message}")
    
    def compute_financial_state(
        self,
        current_balance: float,
        transactions: List[Transaction],
        payables: List[Payable],
        receivables: List[Receivable],
        hidden_transactions: List[HiddenTransaction],
        business_context: BusinessContext,
        reference_date: str = None
    ) -> FinancialState:
        """
        Compute complete financial state snapshot.
        
        This is the main entry point for the engine. It validates all inputs,
        performs aggregations, calculates metrics, scores health, and returns
        a comprehensive FinancialState object.
        
        Args:
            current_balance: Current account balance in INR
            transactions: List of transaction objects
            payables: List of payable objects
            receivables: List of receivable objects
            hidden_transactions: List of hidden transaction objects (recurring)
            business_context: Business context and configuration
            reference_date: Reference date for computations (YYYY-MM-DD, default: today)
            
        Returns:
            FinancialState object
            
        Raises:
            ValidationError: If any inputs are invalid
        """
        if reference_date is None:
            reference_date = get_today()
        
        self._log(f"Computing financial state as of {reference_date}")
        
        # ===== PHASE 1: VALIDATION =====
        self._log("Phase 1: Validating inputs...")
        
        is_valid, errors = validate_all_inputs(
            current_balance,
            transactions,
            payables,
            receivables,
            hidden_transactions,
            business_context,
            reference_date
        )
        
        if not is_valid:
            error_msg = "Input validation failed:\n" + "\n".join(errors)
            raise ValidationError(error_msg)
        
        self._log(f"  ✓ All inputs valid")
        
        # ===== PHASE 2: AGGREGATION =====
        self._log("Phase 2: Aggregating inputs...")
        
        # Available cash
        available_cash = compute_available_cash(
            current_balance,
            business_context.min_cash_buffer
        )
        self._log(f"  • Available cash: ₹{available_cash:,.2f}")
        
        # Payables aggregation
        due_now, due_soon, due_later = aggregate_payables_by_timeline(
            payables,
            business_context.time_horizon_days,
            reference_date
        )
        total_payables_all = aggregate_payables_all(payables)
        total_payables_within_horizon = calculate_total_payables_within_horizon(
            payables,
            business_context.time_horizon_days,
            reference_date
        )
        self._log(f"  • Payables: due_now=₹{due_now:,.2f}, due_soon=₹{due_soon:,.2f}, total=₹{total_payables_all:,.2f}")
        
        # Receivables aggregation
        weighted_receivables, unweighted_receivables = compute_weighted_receivables(
            receivables,
            business_context.time_horizon_days,
            reference_date
        )
        self._log(f"  • Receivables: weighted=₹{weighted_receivables:,.2f}, unweighted=₹{unweighted_receivables:,.2f}")
        
        # Receivable quality
        quality_score = compute_receivable_quality_score(
            weighted_receivables,
            unweighted_receivables
        )
        self._log(f"  • Receivable quality score: {quality_score:.2f}")
        
        # Hidden transactions
        hidden_outflow, hidden_occurrences = aggregate_hidden_transactions_in_horizon(
            hidden_transactions,
            business_context.time_horizon_days,
            reference_date
        )
        self._log(f"  • Hidden transactions: {len(hidden_occurrences)} occurrences, net=₹{hidden_outflow:,.2f}")
        
        # ===== PHASE 3: CASH FLOW TIMELINE =====
        self._log("Phase 3: Building cash flow timeline...")
        
        cash_flow_timeline = build_cash_flow_timeline(
            current_balance,
            payables,
            receivables,
            hidden_transactions,
            business_context.time_horizon_days,
            reference_date
        )
        
        self._log(f"  • Timeline events: {len(cash_flow_timeline)} days with activity")
        
        # ===== PHASE 4: METRICS CALCULATION =====
        self._log("Phase 4: Calculating metrics...")
        
        # Runway
        runway_days = calculate_runway_days(
            cash_flow_timeline,
            business_context.min_cash_buffer,
            business_context.time_horizon_days
        )
        self._log(f"  • Cash runway: {runway_days if runway_days else 'stable'} days")
        
        # Obligation pressure
        obligation_pressure = calculate_obligation_pressure_ratio(
            total_payables_within_horizon,
            available_cash,
            weighted_receivables
        )
        self._log(f"  • Obligation pressure ratio: {obligation_pressure:.2f}")
        
        # Buffer sufficiency
        avg_daily_outflow = calculate_average_daily_outflow(
            cash_flow_timeline,
            business_context.time_horizon_days
        )
        buffer_sufficiency = calculate_buffer_sufficiency_days(
            business_context.min_cash_buffer,
            avg_daily_outflow
        )
        self._log(f"  • Buffer sufficiency: {buffer_sufficiency:.1f} days (avg outflow: ₹{avg_daily_outflow:,.2f}/day)")
        
        # ===== PHASE 5: HEALTH SCORING =====
        self._log("Phase 5: Computing health score...")
        
        health_score, breakdown = compute_health_score(
            runway_days,
            obligation_pressure,
            quality_score,
            buffer_sufficiency
        )
        
        self._log(f"  • Health score: {health_score}/100")
        self._log(f"    - Runway component: {breakdown.runway_score}/100 (weight: {breakdown.runway_weight})")
        self._log(f"    - Pressure component: {breakdown.obligation_pressure_score}/100 (weight: {breakdown.pressure_weight})")
        self._log(f"    - Quality component: {breakdown.receivable_quality_score}/100 (weight: {breakdown.quality_weight})")
        self._log(f"    - Buffer component: {breakdown.buffer_sufficiency_score}/100 (weight: {breakdown.buffer_weight})")
        
        # ===== PHASE 6: REASONING & STATUS FLAGS =====
        self._log("Phase 6: Generating reasoning and status flags...")
        
        reasoning = generate_health_reasoning(
            health_score,
            runway_days,
            obligation_pressure,
            quality_score,
            buffer_sufficiency,
            total_payables_within_horizon,
            available_cash,
            weighted_receivables
        )
        
        status_flags = {
            "critical_runway": runway_days is not None and runway_days < 2,
            "limited_runway": runway_days is not None and runway_days < 7,
            "high_pressure": obligation_pressure > 2.0,
            "low_receivable_quality": quality_score < 0.5,
            "insufficient_buffer": buffer_sufficiency < 2.0,
            "has_overdue": due_now > 0,
            "critical_status": health_score < 20
        }
        
        self._log(f"  • Status flags: {sum(1 for v in status_flags.values() if v)} raised")
        
        # ===== PHASE 7: ASSEMBLE RESULT =====
        self._log("Phase 7: Assembling result...")
        
        financial_state = FinancialState(
            current_balance=round_to_cents(current_balance),
            available_cash=round_to_cents(available_cash),
            total_payables_due_now=round_to_cents(due_now),
            total_payables_due_soon=round_to_cents(due_soon),
            total_payables_all=round_to_cents(total_payables_all),
            weighted_receivables=round_to_cents(weighted_receivables),
            total_receivables_unweighted=round_to_cents(unweighted_receivables),
            cash_runway_days=runway_days,
            obligation_pressure_ratio=round_to_cents(obligation_pressure),
            receivable_quality_score=round_to_cents(quality_score),
            buffer_sufficiency_days=round_to_cents(buffer_sufficiency),
            health_score=health_score,
            health_score_breakdown=breakdown,
            health_reasoning=reasoning,
            cash_flow_timeline=cash_flow_timeline,
            snapshot_date=reference_date,
            status_flags=status_flags
        )
        
        self._log("✓ Financial state computation complete")
        
        return financial_state


def compute_financial_state(
    current_balance: float,
    transactions: List[Transaction],
    payables: List[Payable],
    receivables: List[Receivable],
    hidden_transactions: List[HiddenTransaction],
    business_context: BusinessContext,
    reference_date: str = None,
    verbose: bool = False
) -> FinancialState:
    """
    Convenience function to compute financial state with a single call.
    
    Args:
        current_balance: Current account balance in INR
        transactions: List of transaction objects
        payables: List of payable objects
        receivables: List of receivable objects
        hidden_transactions: List of hidden transaction objects
        business_context: Business context and configuration
        reference_date: Reference date for computations (YYYY-MM-DD, default: today)
        verbose: If True, print intermediate log messages
        
    Returns:
        FinancialState object
        
    Raises:
        ValidationError: If any inputs are invalid
    """
    engine = FinancialStateEngine(verbose=verbose)
    return engine.compute_financial_state(
        current_balance=current_balance,
        transactions=transactions,
        payables=payables,
        receivables=receivables,
        hidden_transactions=hidden_transactions,
        business_context=business_context,
        reference_date=reference_date
    )
