#!/usr/bin/env python3
"""
Test CapitalSense with real user data (Kuber Deco World)
"""

from datetime import datetime, timedelta
from financial_state_engine import (
    compute_financial_state,
    Transaction,
    Payable,
    Receivable,
    HiddenTransaction,
    BusinessContext
)
from risk_detection_engine import detect_risks
from deterministic_decision_engine.engine import make_payment_decisions_with_explanations

# ============================================================================
# USER DATA: Kuber Deco World
# ============================================================================

CURRENT_DATE = "2026-03-25"
CURRENT_BALANCE = 54_000.0
MIN_BUFFER = 7_000.0

# RECEIVABLES (Money Expected In)
receivables = [
    Receivable(
        id="REC-001",
        amount=1_850.0,
        expected_date="2026-03-30",
        description="Invoice from Kanan Interior Pvt Ltd",
        confidence=0.70,  # 70% confidence (0.0-1.0 scale)
    ),
    Receivable(
        id="REC-002",
        amount=820.0,
        expected_date="2026-03-30",
        description="Invoice from Arulmadha Traders",
        confidence=0.70,
    ),
    Receivable(
        id="REC-003",
        amount=350.0,
        expected_date="2026-03-30",
        description="Invoice from Sri Ganesh Glass and Plywoods",
        confidence=0.70,
    ),
]

# PAYABLES (Money Owed Out)
payables = [
    Payable(
        id="PAY-001",
        amount=20_000.0,
        due_date="2026-03-31",
        description="GST Payment",
        status="pending",
        priority_level="critical",  # Tax is critical
        category="Tax",
    ),
    Payable(
        id="PAY-002",
        amount=2_000.0,
        due_date="2026-03-30",
        description="Electricity Bill",
        status="pending",
        priority_level="high",  # Essential utility
        category="Utilities",
    ),
    Payable(
        id="PAY-003",
        amount=30_000.0,
        due_date="2026-03-31",
        description="Employee Salaries (3 people × ₹10,000 each)",
        status="pending",
        priority_level="critical",  # Payroll is critical
        category="Payroll",
    ),
    Payable(
        id="PAY-004",
        amount=5_000.0,
        due_date="2026-04-05",
        description="Vendor A Payment",
        status="pending",
        priority_level="high",
        category="Supplier",
    ),
    Payable(
        id="PAY-005",
        amount=5_000.0,
        due_date="2026-04-05",
        description="Vendor B Payment",
        status="pending",
        priority_level="high",
        category="Supplier",
    ),
]

# BUSINESS CONTEXT
business_context = BusinessContext(
    min_cash_buffer=MIN_BUFFER,
    time_horizon_days=14,
    allow_partial_payments=True,  # Fixed: was 'allows_partial_payments'
)

# ============================================================================
# STEP 1: FINANCIAL STATE ENGINE
# ============================================================================
print("\n" + "="*80)
print("STEP 1: FINANCIAL STATE ENGINE")
print("="*80)

financial_state = compute_financial_state(
    current_balance=CURRENT_BALANCE,
    transactions=[],
    payables=payables,
    receivables=receivables,
    hidden_transactions=[],
    business_context=business_context,
    reference_date=CURRENT_DATE,
    verbose=True
)

print(f"\n📊 CURRENT FINANCIAL POSITION")
print(f"   Current Balance:           ₹{financial_state.current_balance:>12,.2f}")
print(f"   Minimum Buffer:            ₹{MIN_BUFFER:>12,.2f}")
print(f"   Available Cash (after buffer): ₹{financial_state.available_cash:>12,.2f}")
print(f"\n📉 OBLIGATIONS")
print(f"   Due Now:                   ₹{financial_state.total_payables_due_now:>12,.2f}")
print(f"   Due Soon (14 days):        ₹{financial_state.total_payables_due_soon:>12,.2f}")
print(f"   Total Payables:            ₹{financial_state.total_payables_all:>12,.2f}")
print(f"\n📈 EXPECTED INCOME")
print(f"   Weighted Receivables:      ₹{financial_state.weighted_receivables:>12,.2f}")
print(f"   Total (unweighted):        ₹{financial_state.total_receivables_unweighted:>12,.2f}")
print(f"\n⏰ RUNWAY & PRESSURE")
print(f"   Cash Runway:               {financial_state.cash_runway_days} days")
print(f"   Obligation Pressure Ratio: {financial_state.obligation_pressure_ratio:.2f}x")
print(f"   Receivable Quality Score:  {financial_state.receivable_quality_score}%")
print(f"\n💯 HEALTH SCORE")
print(f"   Overall Health:            {financial_state.health_score}/100")
print(f"   Status:                    {financial_state.health_reasoning}")

# ============================================================================
# STEP 2: RISK DETECTION ENGINE
# ============================================================================
print("\n" + "="*80)
print("STEP 2: RISK DETECTION ENGINE (3 Scenarios)")
print("="*80)

risk_detection = detect_risks(
    financial_state=financial_state,
    payables=payables,        # Pass the actual payables
    receivables=receivables   # Pass the actual receivables
)

print(f"\n🟢 BEST CASE (Optimistic)")
print(f"   Days to Shortfall:         {risk_detection.best_case.days_to_shortfall}")
print(f"   Minimum Cash:              ₹{risk_detection.best_case.minimum_cash_amount:,.2f}")
print(f"   Severity:                  {risk_detection.best_case.risk_severity}")

print(f"\n🟡 BASE CASE (Most Likely)")
print(f"   Days to Shortfall:         {risk_detection.base_case.days_to_shortfall}")
print(f"   Minimum Cash:              ₹{risk_detection.base_case.minimum_cash_amount:,.2f}")
print(f"   Severity:                  {risk_detection.base_case.risk_severity}")

print(f"\n🔴 WORST CASE (Pessimistic)")
print(f"   Days to Shortfall:         {risk_detection.worst_case.days_to_shortfall}")
print(f"   Minimum Cash:              ₹{risk_detection.worst_case.minimum_cash_amount:,.2f}")
print(f"   Severity:                  {risk_detection.worst_case.risk_severity}")

# ============================================================================
# STEP 3 & 4: DECISION ENGINE + EXPLAINABILITY ENGINE
# ============================================================================
print("\n" + "="*80)
print("STEP 3 & 4: DECISION ENGINE + EXPLAINABILITY ENGINE")
print("="*80)

decisions = make_payment_decisions_with_explanations(
    financial_state=financial_state,
    risk_detection_result=risk_detection,
    payables=payables,  # Pass payables separately, not inside financial_state
    vendor_relationships=None,
    reference_date=datetime.strptime(CURRENT_DATE, "%Y-%m-%d"),
    risk_level="MODERATE",
)

# ============================================================================
# ANALYZE BASE CASE (Most Likely)
# ============================================================================
print("\n" + "="*80)
print("🎯 BASE CASE ANALYSIS (70% Likely Scenario)")
print("="*80)

base_decision = decisions.base_case

print(f"\n📋 THREE STRATEGIES AVAILABLE:")
print(f"\n  1️⃣ AGGRESSIVE (Spend 90% of available cash)")
print(f"     Total to Pay:             ₹{base_decision.aggressive_strategy.total_payment:>10,.2f}")
print(f"     Penalties:                ₹{base_decision.aggressive_strategy.total_penalty_cost:>10,.2f}")
print(f"     Cash After:               ₹{base_decision.aggressive_strategy.estimated_cash_after:>10,.2f}")
print(f"     Survival Probability:     {base_decision.aggressive_strategy.survival_probability:>10.0f}%")

print(f"\n  2️⃣ BALANCED (Spend 70% of available cash) ⭐ RECOMMENDED")
print(f"     Total to Pay:             ₹{base_decision.balanced_strategy.total_payment:>10,.2f}")
print(f"     Penalties:                ₹{base_decision.balanced_strategy.total_penalty_cost:>10,.2f}")
print(f"     Cash After:               ₹{base_decision.balanced_strategy.estimated_cash_after:>10,.2f}")
print(f"     Survival Probability:     {base_decision.balanced_strategy.survival_probability:>10.0f}%")

print(f"\n  3️⃣ CONSERVATIVE (Spend 40% of available cash)")
print(f"     Total to Pay:             ₹{base_decision.conservative_strategy.total_payment:>10,.2f}")
print(f"     Penalties:                ₹{base_decision.conservative_strategy.total_penalty_cost:>10,.2f}")
print(f"     Cash After:               ₹{base_decision.conservative_strategy.estimated_cash_after:>10,.2f}")
print(f"     Survival Probability:     {base_decision.conservative_strategy.survival_probability:>10.0f}%")

print(f"\n🎯 RECOMMENDED FOR BASE CASE: {base_decision.recommended_strategy}")
print(f"   Reason: {base_decision.reasoning}")

# ============================================================================
# DETAILED BREAKDOWN: BALANCED STRATEGY
# ============================================================================
print("\n" + "="*80)
print("📊 DETAILED BREAKDOWN: BALANCED STRATEGY (RECOMMENDED)")
print("="*80)

balanced = base_decision.balanced_strategy

# Create lookup for payable amounts
payable_lookup = {p.id: p for p in payables}

print(f"\nTotal Available Cash:       ₹{financial_state.available_cash:>12,.2f}")
print(f"Spending 70%:               ₹{balanced.total_payment:>12,.2f}")
print(f"Penalties (estimated):      ₹{balanced.total_penalty_cost:>12,.2f}")
print(f"Cash Remaining:             ₹{balanced.estimated_cash_after:>12,.2f}")

print(f"\n💳 PER-OBLIGATION DECISIONS:")
for i, decision in enumerate(balanced.decisions, 1):
    # Get original payable amount
    payable = payable_lookup.get(decision.obligation_id)
    amount_due = payable.amount if payable else decision.pay_amount
    
    print(f"\n  {i}. {decision.vendor_name} ({decision.category})")
    print(f"     Obligation ID:         {decision.obligation_id}")
    print(f"     Amount Due:            ₹{amount_due:>10,.2f}")
    print(f"     Decision:              {decision.status}")
    print(f"     Pay Amount:            ₹{decision.pay_amount:>10,.2f}")
    print(f"     Delay Days:            {decision.delay_days} days")
    print(f"     Potential Penalty:     ₹{decision.potential_penalty:>10,.2f}")
    print(f"     Rationale:             {decision.rationale}")

# ============================================================================
# CROSS-SCENARIO GUIDANCE
# ============================================================================
print("\n" + "="*80)
print("🗺️  CROSS-SCENARIO GUIDANCE & ACTION PLAN")
print("="*80)

explanation = decisions.explanation
print(f"\n{explanation.cross_scenario_summary}")
print(f"\n{explanation.action_recommendation}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("✅ SUMMARY FOR KUBER DECO WORLD")
print("="*80)
print(f"""
YOUR SITUATION:
  • Current Balance: ₹{CURRENT_BALANCE:,.0f}
  • Min Buffer: ₹{MIN_BUFFER:,.0f}
  • Available for Payments: ₹{financial_state.available_cash:,.0f}
  • Total Obligations (14 days): ₹{financial_state.total_payables_due_soon:,.0f}
  • Expected Income (14 days): ₹{financial_state.weighted_receivables:,.0f}
  • Health Score: {financial_state.health_score}/100

RISK ASSESSMENT:
  • BASE Case Shortfall: {risk_detection.base_case.days_to_shortfall} days
  • Severity: {risk_detection.base_case.risk_severity}

RECOMMENDED ACTION:
  Execute BALANCED Strategy in BASE Case
  → Pay ₹{balanced.total_payment:,.0f} now (to {len([d for d in balanced.decisions if d.pay_amount > 0])} vendors)
  → Keep ₹{balanced.estimated_cash_after:,.0f} as working capital
  → Survival Probability: {balanced.survival_probability:.0f}%

CRITICAL OBLIGATIONS (Pay in Full):
  • GST: ₹20,000 (tax penalty is severe)
  • Payroll: ₹10,000 (keep team motivated)
  • Electricity: ₹2,000 (essential utility)

FLEXIBLE OBLIGATIONS (Can Delay):
  • Vendor A: Can delay or partial pay
  • Vendor B: Can delay or partial pay
""")

print("="*80)
print("For detailed per-vendor explanations, see above 'PER-OBLIGATION DECISIONS'")
print("="*80)
