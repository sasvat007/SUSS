"""
Main Risk Detection Engine orchestrator.

Combines all modules to detect and analyze cash flow risks under 3 scenarios.
"""

from typing import Dict, Optional, List
from datetime import datetime
from financial_state_engine.models import FinancialState, CashFlowEvent

from .models import (
    RiskDetectionResult,
    RiskProjection,
    ScenarioComparison,
    BEST_CASE_CONFIG,
    BASE_CASE_CONFIG,
    WORST_CASE_CONFIG,
)
from .scenario_adapters import create_scenario_snapshot
from .risk_simulator import simulate_scenario_timeline, extract_timeline_metrics
from .risk_detector import (
    detect_first_shortfall_date,
    detect_minimum_cash_point,
    detect_zero_cash_date,
    count_deficit_days,
    find_maximum_deficit,
    find_recovery_date,
    identify_critical_risk_dates,
)
from .risk_analyzer import (
    generate_risk_flags,
    classify_risk_severity,
    generate_risk_summary,
    analyze_scenario_divergence,
    generate_scenario_divergence_summary,
    determine_primary_risk_date,
    generate_recommendation,
)


def detect_risks(
    financial_state: FinancialState,
    payables: List = None,
    receivables: List = None,
    custom_best_config: Optional[object] = None,
    custom_base_config: Optional[object] = None,
    custom_worst_config: Optional[object] = None,
) -> RiskDetectionResult:
    """
    Detect cash flow risks by simulating three scenarios.
    
    This is the main entry point for the Risk Detection Engine.
    
    Args:
        financial_state: Current financial state from Financial State Engine
        payables: List of Payable objects (optional, for better scenario modeling)
        receivables: List of Receivable objects (optional, for better scenario modeling)
        custom_best_config: Override best case config (optional)
        custom_base_config: Override base case config (optional)
        custom_worst_config: Override worst case config (optional)
        
    Returns:
        RiskDetectionResult with projections for all 3 scenarios, comparison, and recommendations
        
    Raises:
        ValueError: If financial_state is invalid
    """
    if not financial_state:
        raise ValueError("Financial state is required")
    
    # Use provided configs or defaults
    best_config = custom_best_config or BEST_CASE_CONFIG
    base_config = custom_base_config or BASE_CASE_CONFIG
    worst_config = custom_worst_config or WORST_CASE_CONFIG
    
    # Get context info (from business_context which is derived from FinancialState during compute)
    # For now, we'll use default values
    avg_payment_delay = getattr(financial_state, 'avg_payment_delay_days', 0)
    min_buffer = getattr(financial_state, 'min_buffer', 5000.0)
    forecast_days = getattr(financial_state, 'forecast_days', 30)
    
    # Use provided payables/receivables or empty lists for basic scenario modeling
    if payables is None:
        payables = []
    if receivables is None:
        receivables = []
    
    hidden_txns = []  # Would be populated if provided
    
    # Process each scenario
    best_projection = _analyze_scenario(
        financial_state, best_config, "best", receivables, payables, hidden_txns, avg_payment_delay, min_buffer
    )
    base_projection = _analyze_scenario(
        financial_state, base_config, "base", receivables, payables, hidden_txns, avg_payment_delay, min_buffer
    )
    worst_projection = _analyze_scenario(
        financial_state, worst_config, "worst", receivables, payables, hidden_txns, avg_payment_delay, min_buffer
    )
    
    # Analyze cross-scenario comparison
    comparison = _analyze_scenario_comparison(
        best_projection, base_projection, worst_projection
    )
    
    # Assemble final result
    result = RiskDetectionResult(
        best_case=best_projection,
        base_case=base_projection,
        worst_case=worst_projection,
        scenario_comparison=comparison,
        overall_risk_level=comparison.uncertainty_level,  # Using existing field
        primary_risk_date=determine_primary_risk_date(
            best_projection.first_shortfall_date,
            base_projection.first_shortfall_date,
            worst_projection.first_shortfall_date,
        ),
        recommendation=generate_recommendation(
            comparison.uncertainty_level,
            determine_primary_risk_date(
                best_projection.first_shortfall_date,
                base_projection.first_shortfall_date,
                worst_projection.first_shortfall_date,
            ),
            best_projection.risk_severity,
            worst_projection.risk_severity,
        ),
        analysis_summary="Risk detection analysis complete",
        snapshot_date=financial_state.snapshot_date,
        analysis_horizon_days=30,
    )
    
    return result


def _analyze_scenario(
    financial_state: FinancialState,
    scenario_config: object,
    scenario_type: str,
    receivables: List,
    payables: List,
    hidden_txns: List,
    avg_payment_delay: int,
    min_buffer: float,
) -> RiskProjection:
    """
    Analyze a single scenario (best, base, or worst case).
    
    Args:
        financial_state: Current financial state
        scenario_config: Scenario configuration
        scenario_type: "best", "base", or "worst"
        receivables: List of receivables
        payables: List of payables
        hidden_txns: List of hidden transactions
        avg_payment_delay: Average payment delay days
        min_buffer: Minimum cash buffer
        
    Returns:
        RiskProjection with analysis results
    """
    # Step 1: Create scenario-specific snapshot
    adapted_rcv, adapted_pay, adapted_hid = create_scenario_snapshot(
        receivables, payables, hidden_txns, scenario_config, avg_payment_delay
    )
    
    # Step 2: Simulate timeline using ADAPTED data (scenario-specific)
    timeline = simulate_scenario_timeline(
        starting_balance=financial_state.current_balance,
        min_cash_buffer=min_buffer,
        receivables=adapted_rcv,  # Use adapted receivables (scenario-filtered)
        payables=adapted_pay,      # Use adapted payables (scenario-filtered)
        hidden_transactions=adapted_hid,
        time_horizon_days=30,
        reference_date=financial_state.snapshot_date
    )
    
    # Step 3: Extract basic metrics
    metrics = extract_timeline_metrics(timeline, min_buffer)
    
    # Step 4: Detect critical dates (all return tuples or combinations)
    shortfall_date, days_to_shortfall = detect_first_shortfall_date(timeline, min_buffer)
    zero_cash_date = detect_zero_cash_date(timeline)
    minimum_cash, minimum_date, days_to_minimum = detect_minimum_cash_point(timeline)
    deficit_days = count_deficit_days(timeline, min_buffer)
    max_deficit = find_maximum_deficit(timeline, min_buffer)
    recovered, recovery_date, days_to_recovery = find_recovery_date(timeline, min_buffer, financial_state.snapshot_date)
    
    # Step 5: Generate risk flags
    risk_flags = generate_risk_flags(
        days_to_shortfall,
        deficit_days,
        max_deficit,
        recovered,
        zero_cash_date,
    )
    
    # Step 6: Classify severity
    risk_severity = classify_risk_severity(
        days_to_shortfall,
        zero_cash_date is not None,
        recovery_date is None and shortfall_date is not None,
    )
    
    # Step 7: Generate summary
    summary = generate_risk_summary(
        scenario_type,
        days_to_shortfall,
        minimum_cash,
        deficit_days,
        risk_severity,
        recovered,
    )
    
    # Assemble projection - match the existing RiskProjection fields
    projection = RiskProjection(
        scenario_type=scenario_type,
        simulation_timeline=[dict(date=e.date, balance=e.balance) for e in timeline],
        first_shortfall_date=shortfall_date,
        days_to_shortfall=days_to_shortfall,
        minimum_cash_amount=minimum_cash,
        minimum_cash_date=minimum_date,
        days_to_minimum=days_to_minimum,
        zero_cash_date=zero_cash_date,
        total_deficit_days=deficit_days,
        max_deficit_amount=max_deficit,
        deficit_recovery_date=recovery_date,
        risk_flags=risk_flags,
        risk_severity=risk_severity,
        risk_summary=summary,
    )
    
    return projection


def _analyze_scenario_comparison(
    best: RiskProjection,
    base: RiskProjection,
    worst: RiskProjection,
) -> ScenarioComparison:
    """
    Analyze comparison across the three scenarios.
    
    Args:
        best: Best case projection
        base: Base case projection
        worst: Worst case projection
        
    Returns:
        ScenarioComparison with cross-scenario analysis
    """
    # Analyze divergence
    uncertainty_level = analyze_scenario_divergence(
        best.days_to_shortfall,
        base.days_to_shortfall,
        worst.days_to_shortfall,
    )
    
    # Generate divergence summary
    divergence_summary = generate_scenario_divergence_summary(
        best.days_to_shortfall,
        base.days_to_shortfall,
        worst.days_to_shortfall,
        uncertainty_level,
    )
    
    # Calculate differences between scenarios
    best_to_base_diff = None
    if best.days_to_shortfall and base.days_to_shortfall:
        best_to_base_diff = base.days_to_shortfall - best.days_to_shortfall
    
    base_to_worst_diff = None
    if base.days_to_shortfall and worst.days_to_shortfall:
        base_to_worst_diff = worst.days_to_shortfall - base.days_to_shortfall
    
    best_to_worst_range = None
    if best.days_to_shortfall and worst.days_to_shortfall:
        best_to_worst_range = worst.days_to_shortfall - best.days_to_shortfall
    
    comparison = ScenarioComparison(
        best_to_base_days_difference=best_to_base_diff,
        base_to_worst_days_difference=base_to_worst_diff,
        best_to_worst_range=best_to_worst_range,
        uncertainty_level=uncertainty_level,
        scenario_divergence_summary=divergence_summary,
    )
    
    return comparison
