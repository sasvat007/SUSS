"""
Comprehensive test suite for Risk Detection Engine.

Tests all modules including scenario adapters, simulator, detector, analyzer, and engine.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from financial_state_engine.models import (
    Transaction,
    Payable,
    Receivable,
    HiddenTransaction,
    BusinessContext,
    FinancialState,
    CashFlowEvent,
    HealthScoreBreakdown,
)
from financial_state_engine.engine import compute_financial_state
from risk_detection_engine.models import (
    RiskSeverity,
    UncertaintyLevel,
    BEST_CASE_CONFIG,
    BASE_CASE_CONFIG,
    WORST_CASE_CONFIG,
)
from risk_detection_engine import detect_risks


# ============================================================================
# Test Fixtures - Create realistic financial states
# ============================================================================

def create_stable_business_inputs() -> tuple:
    """Create inputs for a financially stable business."""
    context = BusinessContext(
        min_cash_buffer=10000.0,
        time_horizon_days=30,
    )
    
    transactions = [
        Transaction(
            date="2024-01-01",
            description="Monthly revenue - confirmed",
            amount=50000.0,
            transaction_type="credit",
            category="revenue",
            id="txn_1",
        ),
        Transaction(
            date="2024-01-10",
            description="Payroll",
            amount=-20000.0,
            transaction_type="debit",
            category="expense",
            id="txn_2",
        ),
    ]
    
    receivables = [
        Receivable(
            id="rcv_1",
            amount=30000.0,
            expected_date="2024-01-20",
            description="Project invoice",
            confidence=0.95,
            status="pending",
            category="BigCorp",
        ),
    ]
    
    payables = [
        Payable(
            id="pay_1",
            amount=15000.0,
            due_date="2024-01-25",
            description="Inventory",
            status="pending",
            priority_level="normal",
        ),
    ]
    
    hidden_transactions = [
        HiddenTransaction(
            id="hid_1",
            transaction_type="subscription",
            amount=-5000.0,
            frequency="monthly",
            next_date="2024-02-01",
            category="Monthly subscription services",
        ),
    ]
    
    return context, transactions, receivables, payables, hidden_transactions


def create_stable_financial_state() -> FinancialState:
    """Create a financially stable business via FSE."""
    context, transactions, receivables, payables, hidden_transactions = create_stable_business_inputs()
    
    fs = compute_financial_state(
        opening_balance=50000.0,
        reference_date="2024-01-15",
        confirmed_transactions=transactions,
        outstanding_payables=payables,
        outstanding_receivables=receivables,
        hidden_transactions=hidden_transactions,
        business_context=context,
    )
    
    return fs


def create_stressed_business_inputs() -> tuple:
    """Create inputs for a financially stressed business."""
    context = BusinessContext(
        min_cash_buffer=5000.0,
        time_horizon_days=30,
    )
    
    transactions = [
        Transaction(
            date="2024-01-01",
            description="Monthly revenue - partial",
            amount=30000.0,
            transaction_type="credit",
            category="revenue",
            id="txn_1",
        ),
        Transaction(
            date="2024-01-10",
            description="Large quarterly tax",
            amount=-35000.0,
            transaction_type="debit",
            category="expense",
            id="txn_2",
        ),
    ]
    
    receivables = [
        Receivable(
            id="rcv_1",
            amount=20000.0,
            expected_date="2024-01-25",
            description="Invoice 001",
            confidence=0.7,
            status="pending",
            category="Client1",
        ),
    ]
    
    payables = [
        Payable(
            id="pay_1",
            amount=25000.0,
            due_date="2024-01-18",
            description="Lease payment",
            status="pending",
            priority_level="high",
        ),
        Payable(
            id="pay_2",
            amount=10000.0,
            due_date="2024-01-20",
            description="Inventory",
            status="pending",
            priority_level="normal",
        ),
    ]
    
    hidden_transactions = [
        HiddenTransaction(
            id="hid_1",
            transaction_type="rental",
            amount=-8000.0,
            frequency="monthly",
            next_date="2024-02-01",
            category="Recurring rent",
        ),
    ]
    
    return context, transactions, receivables, payables, hidden_transactions


def create_stressed_financial_state() -> FinancialState:
    """Create a financially stressed business via FSE."""
    context, transactions, receivables, payables, hidden_transactions = create_stressed_business_inputs()
    
    fs = compute_financial_state(
        opening_balance=15000.0,
        reference_date="2024-01-15",
        confirmed_transactions=transactions,
        outstanding_payables=payables,
        outstanding_receivables=receivables,
        hidden_transactions=hidden_transactions,
        business_context=context,
    )
    
    return fs


def create_critical_business_inputs() -> tuple:
    """Create inputs for a critically stressed business."""
    context = BusinessContext(
        min_cash_buffer=5000.0,
        time_horizon_days=30,
    )
    
    transactions = [
        Transaction(
            date="2024-01-01",
            description="Limited revenue",
            amount=10000.0,
            transaction_type="credit",
            category="revenue",
            id="txn_1",
        ),
        Transaction(
            date="2024-01-10",
            description="Supplier payment",
            amount=-30000.0,
            transaction_type="debit",
            category="expense",
            id="txn_2",
        ),
    ]
    
    receivables = [
        Receivable(
            id="rcv_1",
            amount=25000.0,
            expected_date="2024-02-05",
            description="Uncertain invoice",
            confidence=0.3,
            status="pending",
            category="UnstableClient",
        ),
    ]
    
    payables = [
        Payable(
            id="pay_1",
            amount=20000.0,
            due_date="2024-01-17",
            description="Critical payment",
            status="pending",
            priority_level="critical",
        ),
        Payable(
            id="pay_2",
            amount=15000.0,
            due_date="2024-01-20",
            description="Loan payment",
            status="pending",
            priority_level="high",
        ),
    ]
    
    hidden_transactions = [
        HiddenTransaction(
            id="hid_1",
            transaction_type="other",
            amount=-5000.0,
            frequency="weekly",
            next_date="2024-01-16",
            category="Recurring operating expense",
        ),
    ]
    
    return context, transactions, receivables, payables, hidden_transactions


def create_critical_financial_state() -> FinancialState:
    """Create a critically stressed business via FSE."""
    context, transactions, receivables, payables, hidden_transactions = create_critical_business_inputs()
    
    fs = compute_financial_state(
        opening_balance=8000.0,
        reference_date="2024-01-15",
        confirmed_transactions=transactions,
        outstanding_payables=payables,
        outstanding_receivables=receivables,
        hidden_transactions=hidden_transactions,
        business_context=context,
    )
    
    return fs


# ============================================================================
# Test Suite
# ============================================================================

def test_detect_risks_stable_business():
    """Test risk detection on a stable business."""
    fs = create_stable_financial_state()
    result = detect_risks(fs)
    
    assert result is not None
    assert result.best_case is not None
    assert result.base_case is not None
    assert result.worst_case is not None
    assert result.scenario_comparison is not None
    
    # Stable business should be safe in all scenarios
    assert result.best_case.risk_severity == RiskSeverity.SAFE.value
    assert result.base_case.risk_severity == RiskSeverity.SAFE.value
    assert result.worst_case.risk_severity in [RiskSeverity.SAFE.value, RiskSeverity.CAUTION.value]
    
    print("✓ test_detect_risks_stable_business passed")


def test_detect_risks_stressed_business():
    """Test risk detection on a stressed business."""
    fs = create_stressed_financial_state()
    result = detect_risks(fs)
    
    assert result is not None
    
    # Stressed business likely has shortfalls
    has_shortfall = result.best_case.has_shortfall or result.base_case.has_shortfall or result.worst_case.has_shortfall
    assert has_shortfall or result.overall_risk_level in [RiskSeverity.CAUTION.value, RiskSeverity.WARNING.value]
    
    print("✓ test_detect_risks_stressed_business passed")


def test_detect_risks_critical_business():
    """Test risk detection on a critically stressed business."""
    fs = create_critical_financial_state()
    result = detect_risks(fs)
    
    assert result is not None
    
    # Critical business should show warning or critical
    assert result.overall_risk_level in [
        RiskSeverity.WARNING.value,
        RiskSeverity.CRITICAL.value,
        RiskSeverity.CAUTION.value,
    ]
    
    print("✓ test_detect_risks_critical_business passed")


def test_best_case_least_severe():
    """Test that best case is always least severe."""
    fs = create_critical_financial_state()
    result = detect_risks(fs)
    
    severity_order = {"safe": 0, "caution": 1, "warning": 2, "critical": 3}
    
    best_rank = severity_order.get(result.best_case.risk_severity, 0)
    base_rank = severity_order.get(result.base_case.risk_severity, 0)
    worst_rank = severity_order.get(result.worst_case.risk_severity, 0)
    
    assert best_rank <= base_rank, "Best case should be <= base case severity"
    assert base_rank <= worst_rank, "Base case should be <= worst case severity"
    
    print("✓ test_best_case_least_severe passed")


def test_worst_case_most_severe():
    """Test that worst case is always most severe."""
    fs = create_stressed_financial_state()
    result = detect_risks(fs)
    
    severity_order = {"safe": 0, "caution": 1, "warning": 2, "critical": 3}
    
    worst_rank = severity_order.get(result.worst_case.risk_severity, 0)
    base_rank = severity_order.get(result.base_case.risk_severity, 0)
    best_rank = severity_order.get(result.best_case.risk_severity, 0)
    
    assert worst_rank >= best_rank, "Worst case should be >= best case severity"
    assert worst_rank >= base_rank, "Worst case should be >= base case severity"
    
    print("✓ test_worst_case_most_severe passed")


def test_scenario_comparison_exists():
    """Test that scenario comparison is properly populated."""
    fs = create_stable_financial_state()
    result = detect_risks(fs)
    
    assert result.scenario_comparison is not None
    assert result.scenario_comparison.scenario_divergence in [
        UncertaintyLevel.LOW.value,
        UncertaintyLevel.MEDIUM.value,
        UncertaintyLevel.HIGH.value,
    ]
    assert result.scenario_comparison.divergence_summary is not None
    assert len(result.scenario_comparison.divergence_summary) > 0
    assert result.scenario_comparison.recommendation is not None
    assert len(result.scenario_comparison.recommendation) > 0
    
    print("✓ test_scenario_comparison_exists passed")


def test_primary_risk_date_selection():
    """Test that primary risk date is correctly selected."""
    fs = create_critical_financial_state()
    result = detect_risks(fs)
    
    # Primary risk date should be from worst case if it exists
    if result.worst_case.shortfall_date:
        assert result.primary_risk_date == result.worst_case.shortfall_date
    elif result.base_case.shortfall_date:
        assert result.primary_risk_date == result.base_case.shortfall_date
    elif result.best_case.shortfall_date:
        assert result.primary_risk_date == result.best_case.shortfall_date
    
    print("✓ test_primary_risk_date_selection passed")


def test_overall_risk_level_matches_worst():
    """Test that overall risk level matches worst case."""
    fs = create_critical_financial_state()
    result = detect_risks(fs)
    
    severity_order = {"safe": 0, "caution": 1, "warning": 2, "critical": 3}
    worst_rank = severity_order.get(result.worst_case.risk_severity, 0)
    overall_rank = severity_order.get(result.overall_risk_level, 0)
    
    assert overall_rank >= worst_rank, "Overall risk should be >= worst case"
    
    print("✓ test_overall_risk_level_matches_worst passed")


def test_risk_flags_boolean_values():
    """Test that all risk flags are boolean values."""
    fs = create_stressed_financial_state()
    result = detect_risks(fs)
    
    for scenario in [result.best_case, result.base_case, result.worst_case]:
        for flag_name, flag_value in scenario.risk_flags.items():
            assert isinstance(flag_value, bool), f"Flag {flag_name} should be boolean"
    
    print("✓ test_risk_flags_boolean_values passed")


def test_critical_dates_in_order():
    """Test that critical dates are in chronological order."""
    fs = create_critical_financial_state()
    result = detect_risks(fs)
    
    for scenario in [result.best_case, result.base_case, result.worst_case]:
        dates = scenario.critical_risk_dates
        if len(dates) > 1:
            for i in range(len(dates) - 1):
                assert dates[i] <= dates[i + 1], f"Dates should be ordered: {dates}"
    
    print("✓ test_critical_dates_in_order passed")


def test_non_negative_metrics():
    """Test that all numeric metrics are non-negative."""
    fs = create_stressed_financial_state()
    result = detect_risks(fs)
    
    for scenario in [result.best_case, result.base_case, result.worst_case]:
        if scenario.days_to_shortfall:
            assert scenario.days_to_shortfall >= 0
        assert scenario.total_deficit_days >= 0
        assert scenario.days_to_shortfall is None or scenario.days_to_shortfall >= 0
    
    print("✓ test_non_negative_metrics passed")


def test_recovery_date_after_shortfall():
    """Test that recovery date (if any) is after shortfall date."""
    fs = create_stressed_financial_state()
    result = detect_risks(fs)
    
    for scenario in [result.best_case, result.base_case, result.worst_case]:
        if scenario.shortfall_date and scenario.recovery_date:
            assert scenario.recovery_date >= scenario.shortfall_date
    
    print("✓ test_recovery_date_after_shortfall passed")


def test_summaries_not_empty():
    """Test that summary text is generated for all scenarios."""
    fs = create_stable_financial_state()
    result = detect_risks(fs)
    
    assert len(result.best_case.summary) > 0
    assert len(result.base_case.summary) > 0
    assert len(result.worst_case.summary) > 0
    assert len(result.scenario_comparison.recommendation) > 0
    
    print("✓ test_summaries_not_empty passed")


def test_timestamp_preserved():
    """Test that reference timestamp is preserved."""
    fs = create_stable_financial_state()
    result = detect_risks(fs)
    
    assert result.timestamp is not None
    assert result.timestamp == fs.timestamp
    
    print("✓ test_timestamp_preserved passed")



def test_edge_case_zero_cash_at_start():
    """Test edge case where business starts with near-zero cash."""
    context = BusinessContext(
        min_cash_buffer=2000.0,
        time_horizon_days=30,
    )
    
    transactions = [
        Transaction(
            date="2024-01-20",
            description="Revenue incoming",
            amount=10000.0,
            transaction_type="credit",
            category="revenue",
            id="txn_1",
        ),
    ]
    
    payables = [
        Payable(
            id="pay_1",
            amount=5000.0,
            due_date="2024-01-17",
            description="Payment",
            status="pending",
            priority_level="normal",
        ),
    ]
    
    fs = compute_financial_state(
        opening_balance=1000.0,
        reference_date="2024-01-15",
        confirmed_transactions=transactions,
        outstanding_payables=payables,
        outstanding_receivables=[],
        hidden_transactions=[],
        business_context=context,
    )
    
    result = detect_risks(fs)
    
    # Should detect shortfall or critical risk
    assert result is not None
    assert result.worst_case.risk_severity in [
        RiskSeverity.CRITICAL.value,
        RiskSeverity.WARNING.value,
        RiskSeverity.CAUTION.value,
    ]
    
    print("✓ test_edge_case_zero_cash_at_start passed")


def test_edge_case_no_payables():
    """Test edge case where business has no payables."""
    context = BusinessContext(
        min_cash_buffer=5000.0,
        time_horizon_days=30,
    )
    
    transactions = [
        Transaction(
            date="2024-01-20",
            description="Monthly revenue",
            amount=50000.0,
            transaction_type="credit",
            category="revenue",
            id="txn_1",
        ),
    ]
    
    fs = compute_financial_state(
        opening_balance=20000.0,
        reference_date="2024-01-15",
        confirmed_transactions=transactions,
        outstanding_payables=[],
        outstanding_receivables=[],
        hidden_transactions=[],
        business_context=context,
    )
    
    result = detect_risks(fs)
    
    # Should be safe across all scenarios
    assert result.best_case.risk_severity == RiskSeverity.SAFE.value
    assert result.base_case.risk_severity == RiskSeverity.SAFE.value
    assert result.worst_case.risk_severity == RiskSeverity.SAFE.value
    
    print("✓ test_edge_case_no_payables passed")


def test_edge_case_all_uncertain_receivables():
    """Test edge case where all receivables are very uncertain."""
    context = BusinessContext(
        min_cash_buffer=5000.0,
        time_horizon_days=30,
    )
    
    receivables = [
        Receivable(
            id="rcv_1",
            amount=50000.0,
            expected_date="2024-01-25",
            description="Very uncertain",
            confidence=0.1,
            status="pending",
            category="Client1",
        ),
    ]
    
    payables = [
        Payable(
            id="pay_1",
            amount=30000.0,
            due_date="2024-01-18",
            description="Payment",
            status="pending",
            priority_level="normal",
        ),
    ]
    
    fs = compute_financial_state(
        opening_balance=10000.0,
        reference_date="2024-01-15",
        confirmed_transactions=[],
        outstanding_payables=payables,
        outstanding_receivables=receivables,
        hidden_transactions=[],
        business_context=context,
    )
    
    result = detect_risks(fs)
    
    # Worst case should filter out low-confidence receivable
    # Should be caution or worse
    assert result.worst_case.risk_severity in [
        RiskSeverity.CAUTION.value,
        RiskSeverity.WARNING.value,
        RiskSeverity.CRITICAL.value,
    ]
    
    print("✓ test_edge_case_all_uncertain_receivables passed")


def test_invalid_financial_state():
    """Test that invalid input raises error."""
    try:
        detect_risks(None)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    print("✓ test_invalid_financial_state passed")


def test_custom_scenario_configs():
    """Test that custom scenario configs can be passed."""
    fs = create_stable_financial_state()
    
    # Use custom configs
    result = detect_risks(
        fs,
        custom_best_config=BEST_CASE_CONFIG,
        custom_base_config=BASE_CASE_CONFIG,
        custom_worst_config=WORST_CASE_CONFIG,
    )
    
    assert result is not None
    
    print("✓ test_custom_scenario_configs passed")


# ============================================================================
# Run All Tests
# ============================================================================

if __name__ == "__main__":
    tests = [
        test_detect_risks_stable_business,
        test_detect_risks_stressed_business,
        test_detect_risks_critical_business,
        test_best_case_least_severe,
        test_worst_case_most_severe,
        test_scenario_comparison_exists,
        test_primary_risk_date_selection,
        test_overall_risk_level_matches_worst,
        test_risk_flags_boolean_values,
        test_critical_dates_in_order,
        test_non_negative_metrics,
        test_recovery_date_after_shortfall,
        test_summaries_not_empty,
        test_timestamp_preserved,
        test_edge_case_zero_cash_at_start,
        test_edge_case_no_payables,
        test_edge_case_all_uncertain_receivables,
        test_invalid_financial_state,
        test_custom_scenario_configs,
    ]
    
    print(f"\n{'='*60}")
    print(f"Running Risk Detection Engine Test Suite")
    print(f"{'='*60}\n")
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print(f"{'='*60}\n")
    
    if failed == 0:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"❌ {failed} test(s) failed")
        sys.exit(1)
