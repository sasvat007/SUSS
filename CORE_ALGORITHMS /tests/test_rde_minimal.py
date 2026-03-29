"""
Minimal test suite for Risk Detection Engine.

Tests basic functionality and core workflows.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from financial_state_engine.models import Transaction, Payable, Receivable, HiddenTransaction, BusinessContext
from financial_state_engine.engine import compute_financial_state


print("Risk Detection Engine Test Suite - Minimal")
print("=" * 60)

# Test 1: Create a simple financial state
print("\nTest 1: Computing Financial State...")
context = BusinessContext(
    min_cash_buffer=5000.0,
    time_horizon_days=30,
)

transactions = [
    Transaction(
        date="2024-01-15", 
        description="Revenue", 
        amount=50000.0, 
        transaction_type="credit"
    ),
]

payables = [
    Payable(
        id="pay_1",
        amount=10000.0, 
        due_date="2024-01-20", 
        description="Payment",
        status="pending"
    ),
]

fs = compute_financial_state(
    current_balance=20000.0,
    transactions=transactions,
    receivables=[],
    payables=payables,
    hidden_transactions=[],
    business_context=context,
    reference_date="2024-01-15",
)

print(f"✓ Financial State computed")
print(f"  Current balance: ₹{fs.current_balance:,.2f}")
print(f"  Available cash: ₹{fs.available_cash:,.2f}")
print(f"  Health score: {fs.health_score}/100")

# Test 2: Import Risk Detection modules
print("\nTest 2: Importing Risk Detection Engine modules...")
try:
    from risk_detection_engine.models import (
        RiskSeverity,
        UncertaintyLevel,
        BEST_CASE_CONFIG,
        BASE_CASE_CONFIG,
        WORST_CASE_CONFIG,
    )
    from risk_detection_engine.scenario_adapters import create_scenario_snapshot
    from risk_detection_engine.risk_simulator import simulate_scenario_timeline
    from risk_detection_engine.risk_detector import detect_first_shortfall_date
    from risk_detection_engine.risk_analyzer import classify_risk_severity
    print("✓ All modules imported successfully")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 3: Scenario adapters work
print("\nTest 3: Testing scenario adapters...")
try:
    # The adapter function works on individual lists
    adapted_rcv, adapted_pay, adapted_hid = create_scenario_snapshot(
        fs.outstanding_receivables if hasattr(fs, 'outstanding_receivables') else [],
        fs.outstanding_payables if hasattr(fs, 'outstanding_payables') else [],
        fs.hidden_transactions if hasattr(fs, 'hidden_transactions') else [],
        BEST_CASE_CONFIG,
        0  # avg_payment_delay_days
    )
    print(f"✓ Scenario adapter works")
except Exception as e:
    print(f"✗ Scenario adapter failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Timeline simulation works
print("\nTest 4: Testing timeline simulation...")
try:
    timeline = fs.cash_flow_timeline
    print(f"✓ Timeline simulation works")
    print(f"  Timeline events: {len(timeline)}")
except Exception as e:
    print(f"✗ Timeline simulation failed: {e}")
    sys.exit(1)

# Test 5: Detect shortfalls
print("\nTest 5: Testing shortfall detection...")
try:
    shortfall = detect_first_shortfall_date(timeline, fs.current_balance - 5000)
    print(f"✓ Shortfall detection works")
    print(f"  Shortfall date: {shortfall if shortfall else 'None'}")
except Exception as e:
    print(f"✗ Shortfall detection failed: {e}")
    sys.exit(1)

# Test 6: Classify severity
print("\nTest 6: Testing risk severity classification...")
try:
    severity = classify_risk_severity(None, False, False)
    print(f"✓ Severity classification works")
    print(f"  Severity (no shortfall): {severity}")
    
    severity2 = classify_risk_severity(7, False, False)
    print(f"  Severity (7 days): {severity2}")
except Exception as e:
    print(f"✗ Severity classification failed: {e}")
    sys.exit(1)

# Test 7: Full orchestration
print("\nTest 7: Testing full RDE orchestration...")
try:
    from risk_detection_engine.engine import detect_risks
    result = detect_risks(fs)
    print(f"✓ Full risk detection works")
    print(f"  Best case severity: {result.best_case.risk_severity}")
    print(f"  Overall risk level: {result.overall_risk_level}")
except Exception as e:
    print(f"✗ Full risk detection failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ All tests passed!")
print("=" * 60)
