#!/usr/bin/env python3
"""
Manual Testing Script for Explainability Engine

Run this to see real explanations for all 9 payment strategies.

Usage:
    python3 manual_test_explainability.py
"""

from datetime import datetime, timedelta
from deterministic_decision_engine.engine import make_payment_decisions_with_explanations
from deterministic_decision_engine.models import (
    PaymentStrategy, StrategyType, ScenarioType, DecisionResult,
    DecisionResult3Scenarios, PaymentStatus, PaymentDecision,
)
from deterministic_decision_engine.explanation_models import CompleteExplanation


def create_mock_strategies():
    """Create mock payment strategies for demonstration."""
    
    # Create decision 1: Tax payment (critical, due soon)
    decision1 = PaymentDecision(
        obligation_id="TAX-001",
        status=PaymentStatus.PAY_IN_FULL,
        pay_amount=10000.0,
        delay_days=0,
        potential_penalty=0.0,
        rationale="Critical tax obligation; must pay to avoid 5% daily penalty.",
        vendor_id="IRS",
        vendor_name="IRS - Quarterly Tax",
        due_date=datetime.now() + timedelta(days=3),
        category="Tax",
    )
    
    # Create decision 2: Supplier invoice (flexible)
    decision2_aggressive = PaymentDecision(
        obligation_id="SUP-001",
        status=PaymentStatus.PAY_IN_FULL,
        pay_amount=5000.0,
        delay_days=0,
        potential_penalty=0.0,
        rationale="Pay supplier to maintain relationship.",
        vendor_id="ACME-CORP",
        vendor_name="ACME Corp - Core Supplier",
        due_date=datetime.now() + timedelta(days=30),
        category="Supplier",
    )
    
    decision2_balanced = PaymentDecision(
        obligation_id="SUP-001",
        status=PaymentStatus.PARTIAL_PAY,
        pay_amount=2500.0,
        delay_days=14,
        potential_penalty=50.0,
        rationale="Partial payment to preserve cash while maintaining relationship.",
        vendor_id="ACME-CORP",
        vendor_name="ACME Corp - Core Supplier",
        due_date=datetime.now() + timedelta(days=30),
        category="Supplier",
    )
    
    decision2_conservative = PaymentDecision(
        obligation_id="SUP-001",
        status=PaymentStatus.DELAY,
        pay_amount=0.0,
        delay_days=30,
        potential_penalty=150.0,
        rationale="Defer entirely to maximize survival cash.",
        vendor_id="ACME-CORP",
        vendor_name="ACME Corp - Core Supplier",
        due_date=datetime.now() + timedelta(days=30),
        category="Supplier",
    )
    
    # Build 3 strategies for BASE scenario
    aggressive_strategy = PaymentStrategy(
        strategy_type=StrategyType.AGGRESSIVE,
        scenario_type=ScenarioType.BASE,
        decisions=[decision1, decision2_aggressive],
        total_payment=15000.0,
        total_penalty_cost=0.0,
        estimated_cash_after=10000.0,
        survival_probability=72.0,
        score=35.0,
    )
    
    balanced_strategy = PaymentStrategy(
        strategy_type=StrategyType.BALANCED,
        scenario_type=ScenarioType.BASE,
        decisions=[decision1, decision2_balanced],
        total_payment=12500.0,
        total_penalty_cost=50.0,
        estimated_cash_after=12500.0,
        survival_probability=78.0,
        score=40.0,
    )
    
    conservative_strategy = PaymentStrategy(
        strategy_type=StrategyType.CONSERVATIVE,
        scenario_type=ScenarioType.BASE,
        decisions=[decision1, decision2_conservative],
        total_payment=10000.0,
        total_penalty_cost=150.0,
        estimated_cash_after=15000.0,
        survival_probability=88.0,
        score=50.0,
    )
    
    # Build DecisionResult for BASE scenario
    base_case = DecisionResult(
        scenario_type=ScenarioType.BASE,
        aggressive_strategy=aggressive_strategy,
        balanced_strategy=balanced_strategy,
        conservative_strategy=conservative_strategy,
        recommended_strategy=StrategyType.BALANCED,
        reasoning="Balanced strategy optimizes payment vs survival in likely scenario.",
        cash_available=25000.0,
    )
    
    # Return DecisionResult3Scenarios (mock - normally from DDE)
    return DecisionResult3Scenarios(
        best_case=base_case,
        base_case=base_case,
        worst_case=DecisionResult(
            scenario_type=ScenarioType.WORST,
            aggressive_strategy=aggressive_strategy,
            balanced_strategy=balanced_strategy,
            conservative_strategy=conservative_strategy,
            recommended_strategy=StrategyType.CONSERVATIVE,
            reasoning="Conservative strategy maximizes survival in worst case.",
            cash_available=15000.0,
        ),
        overall_recommendation="Plan for BASE case; prepare WORST case contingency.",
    )


def create_mock_financial_state():
    """Create mock financial state."""
    class MockFinancialState:
        def __init__(self):
            self.current_cash = 25000.0
            self.payables = []
            self.vendor_relationships = []
    
    return MockFinancialState()


def create_mock_risk_detection():
    """Create mock risk detection."""
    class MockProjection:
        def __init__(self):
            self.first_shortfall_date = datetime.now() + timedelta(days=45)
            self.days_to_shortfall = 45
    
    class MockRiskDetection:
        def __init__(self):
            self.best_case = MockProjection()
            self.base_case = MockProjection()
            self.worst_case = MockProjection()
    
    return MockRiskDetection()


def print_section(title):
    """Print formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_strategy_explanation(scenario, strategy_name, explanation):
    """Print a strategy explanation."""
    if not explanation:
        return
    
    print(f"\n{'─'*80}")
    print(f"📊 {scenario.upper()} Case → {strategy_name.upper()} Strategy")
    print(f"{'─'*80}")
    
    print(f"\n📝 Summary:")
    print(f"   {explanation.summary}")
    
    print(f"\n💡 Approach:")
    print(f"   {explanation.approach}")
    
    print(f"\n💰 Spending Profile:")
    print(f"   {explanation.spending_profile}")
    
    print(f"\n📈 Key Trade-offs:")
    print(f"   {explanation.key_trade_offs}")
    
    print(f"\n✓ Strengths:")
    print(f"   {explanation.strength}")
    
    print(f"\n✗ Weaknesses:")
    print(f"   {explanation.weakness}")
    
    print(f"\n🎯 Best For:")
    print(f"   {explanation.best_for}")
    
    print(f"\n📋 Metrics:")
    print(f"   • Total Payment: ${explanation.total_payment:,.2f}")
    print(f"   • Penalty Cost: ${explanation.total_penalty_cost:,.2f}")
    print(f"   • Cash After: ${explanation.estimated_cash_after:,.2f}")
    print(f"   • Survival Probability: {explanation.survival_probability:.1f}%")
    
    if explanation.highest_priority_items:
        print(f"\n🔴 Highest Priority (Paid):")
        for item in explanation.highest_priority_items:
            print(f"   • {item}")
    
    if explanation.deferred_items:
        print(f"\n⏸️  Deferred Items:")
        for item in explanation.deferred_items:
            print(f"   • {item}")
    
    print(f"\n🚀 Execution Guidance:")
    for line in explanation.execution_guidance.split('\n'):
        if line.strip():
            print(f"   {line}")
    
    # Print individual obligation explanations
    if explanation.obligation_explanations:
        print(f"\n{'─'*80}")
        print(f"📋 Decision Breakdown:")
        print(f"{'─'*80}")
        
        for i, obs_exp in enumerate(explanation.obligation_explanations, 1):
            print(f"\n   {i}. {obs_exp.vendor_name}")
            print(f"      Decision: {obs_exp.decision_status}")
            print(f"      Amount: ${obs_exp.pay_amount:,.2f}")
            print(f"      Rationale: {obs_exp.decision_rationale}")
            print(f"      Implications: {obs_exp.implications}")


def main():
    """Run manual testing."""
    print_section("🎯 EXPLAINABILITY ENGINE - MANUAL TEST")
    
    print("Generating mock payment decisions...")
    decisions = create_mock_strategies()
    financial_state = create_mock_financial_state()
    risk_detection = create_mock_risk_detection()
    
    # Generate explanations
    from deterministic_decision_engine.explainability_engine import ExplainabilityEngine
    
    print("✓ Mock data created")
    print("Generating complete explanations for all 9 strategies...")
    
    engine = ExplainabilityEngine(enable_llm_refinement=False)
    explanation = engine.generate_complete_explanation(
        decisions=decisions,
        financial_state=financial_state,
        risk_detection=risk_detection,
    )
    
    print("✓ Explanations generated!\n")
    
    # Print cross-scenario guidance
    print_section("📊 CROSS-SCENARIO GUIDANCE")
    print(f"Summary:\n{explanation.cross_scenario_summary}")
    print(f"\nContext:\n{explanation.scenario_context}")
    print(f"\nAction Plan:\n{explanation.action_recommendation}")
    
    # Print BASE case explanations (most common)
    print_section("💼 BASE CASE EXPLANATIONS (Most Likely Scenario)")
    print(f"Recommended Strategy: {explanation.recommended_base_case.upper()}\n")
    
    for strategy_type in ["aggressive", "balanced", "conservative"]:
        strategy_exp = explanation.get_strategy_explanation("base", strategy_type)
        print_strategy_explanation("base", strategy_type, strategy_exp)
    
    # Print WORST case for comparison
    print_section("⚠️  WORST CASE EXPLANATIONS (Contingency Planning)")
    print(f"Recommended Strategy: {explanation.recommended_worst_case.upper()}\n")
    
    balanced_worst = explanation.get_strategy_explanation("worst", "balanced")
    print_strategy_explanation("worst", "balanced", balanced_worst)
    
    # Print BEST case for upside
    print_section("🚀 BEST CASE EXPLANATIONS (Upside Scenario)")
    print(f"Recommended Strategy: {explanation.recommended_best_case.upper()}\n")
    
    aggressive_best = explanation.get_strategy_explanation("best", "aggressive")
    print_strategy_explanation("best", "aggressive", aggressive_best)
    
    # Summary statistics
    print_section("📈 SUMMARY STATISTICS")
    
    all_strategies = explanation.all_strategy_explanations()
    print(f"Total Strategies Explained: {len(all_strategies)}")
    print(f"Scenarios: BEST, BASE, WORST")
    print(f"Approaches per Scenario: AGGRESSIVE, BALANCED, CONSERVATIVE")
    
    print(f"\nCritical Obligations (always paid): {explanation.critical_obligations}")
    print(f"Flexible Obligations (vary by strategy): {explanation.flexible_obligations}")
    
    print("\n✅ Manual test complete! All explanations generated successfully.")
    print("\nTo use in production:")
    print("  decisions = make_payment_decisions_with_explanations(fse_output, rde_output, payables)")
    print("  print(decisions.explanation.cross_scenario_summary)")
    print("  balanced_exp = decisions.explanation.get_strategy_explanation('base', 'balanced')")


if __name__ == "__main__":
    main()
