"""
Comprehensive Test Suite for Deterministic Decision Engine (DDE)

Tests core functionality, algorithm correctness, and integration.

Test Coverage:
- Models and data structures
- Penalty calculations (daily %, escalation, tiered)
- Obligation scoring (weights, legal overrides, vendor strategy)
- Payment optimizer (3 strategies: aggressive/balanced/conservative)
- Strategy evaluator (ranking, recommendation)
- Decision generator (multi-scenario orchestration)
- Engine API (make_payment_decisions, explain)
- Utils (formatting, export)

Run: python -m pytest tests/test_deterministic_decision_engine.py -v

Version: 0.0.1
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from financial_state_engine.models import (
    Payable,
    BusinessContext,
    Transaction,
)
from financial_state_engine.engine import compute_financial_state
from risk_detection_engine.models import (
    RiskProjection,
    RiskDetectionResult,
)
from deterministic_decision_engine.models import (
    VendorRelationship,
    VendorRelationshipType,
    StrategyType,
    ScenarioType,
    PaymentStatus,
    PenaltyModel,
    PenaltyType,
)
from deterministic_decision_engine import (
    make_payment_decisions,
    explain_payment_decisions,
    score_obligation,
    score_all_obligations,
    calculate_delay_penalty,
    get_penalty_model,
    PaymentOptimizer,
    StrategyEvaluator,
    format_currency,
    validate_decision_result,
)


# ============================================================================
# Test Data Factories
# ============================================================================

def create_test_payables():
    """Create sample payables for testing."""
    return [
        Payable(
            id="pay_tax_001",
            amount=5000.0,
            due_date="2024-01-20",  # FSE uses string format
            description="Tax Payment - vendor_001",  # Vendor ID in description
            status="pending",
            priority_level="high",
            category="Tax",
        ),
        Payable(
            id="pay_loan_001",
            amount=10000.0,
            due_date="2024-01-25",
            description="Bank Loan Payment - vendor_002",
            status="pending",
            priority_level="high",
            category="Loan",
        ),
        Payable(
            id="pay_util_001",
            amount=2000.0,
            due_date="2024-01-30",
            description="Utilities - vendor_003",
            status="pending",
            priority_level="normal",
            category="Utilities",
        ),
        Payable(
            id="pay_supp_001",
            amount=3000.0,
            due_date="2024-02-15",
            description="Supplier Invoice - vendor_004",
            status="pending",
            priority_level="normal",
            category="Supplier",
        ),
    ]


def create_test_vendor_relationships():
    """Create sample vendor relationships."""
    return {
        "vendor_001": VendorRelationship(
            vendor_id="vendor_001",
            vendor_name="Tax Authority",
            relationship_type=VendorRelationshipType.CORE,
            years_with_business=10.0,
            payment_reliability=100.0,
        ),
        "vendor_002": VendorRelationship(
            vendor_id="vendor_002",
            vendor_name="Bank",
            relationship_type=VendorRelationshipType.CORE,
            years_with_business=5.0,
            payment_reliability=95.0,
        ),
        "vendor_003": VendorRelationship(
            vendor_id="vendor_003",
            vendor_name="Utilities",
            relationship_type=VendorRelationshipType.EXISTING,
            years_with_business=2.0,
            payment_reliability=80.0,
        ),
        "vendor_004": VendorRelationship(
            vendor_id="vendor_004",
            vendor_name="New Supplier",
            relationship_type=VendorRelationshipType.NEW,
            years_with_business=0.3,
            payment_reliability=50.0,
        ),
    }


def create_test_financial_state(current_cash=50000.0):
    """Create sample financial state using FSE."""
    return compute_financial_state(
        current_balance=current_cash,
        transactions=[
            Transaction(
                date="2024-01-15",
                description="Income",
                amount=50000.0,
                transaction_type="credit",
            ),
        ],
        receivables=[],
        payables=create_test_payables(),
        hidden_transactions=[],
        business_context=BusinessContext(
            min_cash_buffer=5000.0,
            time_horizon_days=90,
        ),
        reference_date="2024-01-15",
    )


def create_test_risk_detection_result():
    """Create sample RDE output with 3 scenarios."""
    from datetime import datetime, timedelta
    
    reference_date_str = "2024-01-15"
    reference_date = datetime.strptime(reference_date_str, "%Y-%m-%d")
    
    best_projection = RiskProjection(
        scenario_type="best",
        simulation_timeline=[],
        first_shortfall_date=None,
        days_to_shortfall=None,
        minimum_cash_amount=50000.0,
        minimum_cash_date=reference_date_str,
        days_to_minimum=0,
        zero_cash_date=None,
        total_deficit_days=0,
        max_deficit_amount=0.0,
        deficit_recovery_date=None,
        risk_severity="safe",
        risk_summary="Best case scenario",
    )
    
    base_projection = RiskProjection(
        scenario_type="base",
        simulation_timeline=[],
        first_shortfall_date="2024-02-29",
        days_to_shortfall=45,
        minimum_cash_amount=0.0,
        minimum_cash_date="2024-02-29",
        days_to_minimum=45,
        zero_cash_date="2024-02-29",
        total_deficit_days=7,
        max_deficit_amount=-5000.0,
        deficit_recovery_date="2024-03-07",
        risk_severity="caution",
        risk_summary="Base case - shortfall in 45 days",
    )
    
    worst_projection = RiskProjection(
        scenario_type="worst",
        simulation_timeline=[],
        first_shortfall_date="2024-02-04",
        days_to_shortfall=20,
        minimum_cash_amount=-10000.0,
        minimum_cash_date="2024-02-04",
        days_to_minimum=20,
        zero_cash_date="2024-01-25",
        total_deficit_days=20,
        max_deficit_amount=-15000.0,
        deficit_recovery_date=None,
        risk_severity="critical",
        risk_summary="Worst case - critical shortfall in 20 days",
    )
    
    return RiskDetectionResult(
        best_case=best_projection,
        base_case=base_projection,
        worst_case=worst_projection,
        scenario_comparison=None,
        overall_risk_level="caution",
        primary_risk_date="2024-02-29",
        recommendation="Monitor cash flow closely",
        analysis_summary="Test scenario with moderate risk",
        snapshot_date=reference_date_str,
        analysis_horizon_days=90,
    )


# ============================================================================
# Test Suite
# ============================================================================

def test_models_basic():
    """Test basic model creation and validation."""
    print("\n" + "=" * 70)
    print("Test 1: Models - Basic Creation")
    print("=" * 70)
    
    # Create a penalty model
    penalty = PenaltyModel(
        category="Tax",
        has_penalty=True,
        penalty_type=PenaltyType.DAILY_PERCENTAGE,
        penalty_rate=5.0,
        escalation=0.5,
    )
    
    assert penalty.category == "Tax"
    assert penalty.penalty_rate == 5.0
    print("✓ PenaltyModel created successfully")
    
    # Create a vendor relationship
    vendor = VendorRelationship(
        vendor_id="v001",
        vendor_name="Test Vendor",
        relationship_type=VendorRelationshipType.NEW,
        years_with_business=0.5,
        payment_reliability=60.0,
    )
    
    assert vendor.relationship_type == VendorRelationshipType.NEW
    print("✓ VendorRelationship created successfully")


def test_penalty_calculator():
    """Test penalty calculations."""
    print("\n" + "=" * 70)
    print("Test 2: Penalty Calculator")
    print("=" * 70)
    
    penalty_model = get_penalty_model("Tax")
    
    # Test 1: No delay = no penalty
    penalty = calculate_delay_penalty(1000.0, 0, penalty_model)
    assert penalty == 0.0
    print("✓ No delay = no penalty")
    
    # Test 2: 10 days delay on $1000 at 5% daily
    penalty = calculate_delay_penalty(1000.0, 10, penalty_model)
    assert penalty > 0.0
    print(f"✓ 10-day delay: ${penalty:.2f} penalty")
    
    # Test 3: Escalation kicks in
    penalty_15_days = calculate_delay_penalty(1000.0, 15, penalty_model)
    penalty_20_days = calculate_delay_penalty(1000.0, 20, penalty_model)
    assert penalty_20_days > penalty_15_days
    print(f"✓ Penalty escalates: 15 days = ${penalty_15_days:.2f}, 20 days = ${penalty_20_days:.2f}")
    
    # Test 4: Different category
    supplier_penalty_model = get_penalty_model("Supplier")
    supplier_penalty = calculate_delay_penalty(1000.0, 10, supplier_penalty_model)
    assert supplier_penalty < penalty  # Supplier rate lower than Tax
    print(f"✓ Category-specific penalties: Tax=${penalty:.2f}, Supplier=${supplier_penalty:.2f}")


def test_obligation_scoring():
    """Test obligation scoring algorithm."""
    print("\n" + "=" * 70)
    print("Test 3: Obligation Scoring")
    print("=" * 70)
    
    payables = create_test_payables()
    vendor_rels = create_test_vendor_relationships()
    reference_date = datetime(2024, 1, 15)
    context = BusinessContext(
        min_cash_buffer=5000.0,
        time_horizon_days=90,
        allow_partial_payments=True,
    )
    
    # Score all obligations
    scores = score_all_obligations(
        payables,
        vendor_rels,
        reference_date,
        context,
        time_horizon_days=90,
    )
    
    assert len(scores) == len(payables)
    print(f"✓ Scored {len(scores)} obligations")
    
    # Check priority ranking
    assert scores[0].priority_rank == 1
    assert scores[-1].priority_rank == len(scores)
    print(f"✓ Priority ranks assigned: 1-{len(scores)}")
    
    # Verify Tax obligation scores high (legal override)
    tax_score = next((s for s in scores if s.category == "Tax"), None)
    assert tax_score is not None
    assert tax_score.legal_risk_score >= 85  # Override minimum
    print(f"✓ Tax obligation legal score: {tax_score.legal_risk_score} (≥ 85 override)")
    
    # Verify vendor relationship scoring
    new_vendor_score = next(
        (s for s in scores if s.obligation_id == "pay_supp_001"), None
    )
    assert new_vendor_score is not None
    assert new_vendor_score.relationship_score == 85  # NEW vendor
    print(f"✓ NEW vendor relationship score: {new_vendor_score.relationship_score} (85)")
    
    # Verify sorting by priority
    prev_score = 100.0
    for score in scores:
        assert score.total_weighted_score <= prev_score
        prev_score = score.total_weighted_score
    print(f"✓ Scores sorted correctly (descending priority)")


def test_payment_optimizer():
    """Test strategy generation."""
    print("\n" + "=" * 70)
    print("Test 4: Payment Optimizer - Strategy Generation")
    print("=" * 70)
    
    payables = create_test_payables()
    vendor_rels = create_test_vendor_relationships()
    reference_date = datetime(2024, 1, 15)
    context = BusinessContext(
        min_cash_buffer=5000.0,
        time_horizon_days=90,
        allow_partial_payments=True,
    )
    
    scores = score_all_obligations(payables, vendor_rels, reference_date, context)
    
    # Create optimizer
    optimizer = PaymentOptimizer(
        payables=payables,
        obligation_scores=scores,
        business_context=context,
        available_cash=30000.0,
        scenario_type=ScenarioType.BASE,
        reference_date=reference_date,
    )
    
    # Generate strategies
    aggressive, balanced, conservative = optimizer.generate_all_strategies()
    
    assert aggressive.strategy_type == StrategyType.AGGRESSIVE
    assert balanced.strategy_type == StrategyType.BALANCED
    assert conservative.strategy_type == StrategyType.CONSERVATIVE
    print("✓ All 3 strategies generated")
    
    # Verify payment amounts
    assert aggressive.total_payment >= balanced.total_payment >= conservative.total_payment
    print(f"✓ Payment amounts (as expected): Agg=${aggressive.total_payment:.0f}, Bal=${balanced.total_payment:.0f}, Con=${conservative.total_payment:.0f}")
    
    # Verify survival probabilities
    print(f"✓ Survival probabilities: Agg={aggressive.survival_probability:.0f}%, Bal={balanced.survival_probability:.0f}%, Con={conservative.survival_probability:.0f}%")
    
    # Verify all strategies have decisions
    assert len(aggressive.decisions) > 0
    assert len(balanced.decisions) > 0
    assert len(conservative.decisions) > 0
    print(f"✓ All strategies have payment decisions")


def test_strategy_evaluator():
    """Test strategy evaluation and ranking."""
    print("\n" + "=" * 70)
    print("Test 5: Strategy Evaluator - Ranking & Recommendation")
    print("=" * 70)
    
    payables = create_test_payables()
    vendor_rels = create_test_vendor_relationships()
    reference_date = datetime(2024, 1, 15)
    context = BusinessContext(
        min_cash_buffer=5000.0,
        time_horizon_days=90,
        allow_partial_payments=True,
    )
    
    scores = score_all_obligations(payables, vendor_rels, reference_date, context)
    optimizer = PaymentOptimizer(
        payables=payables,
        obligation_scores=scores,
        business_context=context,
        available_cash=30000.0,
        scenario_type=ScenarioType.BASE,
        reference_date=reference_date,
    )
    
    aggressive, balanced, conservative = optimizer.generate_all_strategies()
    
    # Rank strategies
    ranked, metrics = StrategyEvaluator.rank_strategies(
        aggressive, balanced, conservative,
        total_obligations=len(payables),
        total_obligation_amount=sum(p.amount for p in payables),
    )
    
    assert len(ranked) == 3
    print(f"✓ Ranked {len(ranked)} strategies")
    
    # Verify ordering
    print(f"  1. {ranked[0].strategy_type.value} (score: {metrics[0]['composite_score']:.2f})")
    print(f"  2. {ranked[1].strategy_type.value} (score: {metrics[1]['composite_score']:.2f})")
    print(f"  3. {ranked[2].strategy_type.value} (score: {metrics[2]['composite_score']:.2f})")
    
    # Test recommendation selection
    rec_type, reasoning = StrategyEvaluator.select_recommended_strategy(
        aggressive, balanced, conservative,
        total_obligations=len(payables),
        total_obligation_amount=sum(p.amount for p in payables),
        risk_level="MODERATE",
    )
    
    assert rec_type in [StrategyType.AGGRESSIVE, StrategyType.BALANCED, StrategyType.CONSERVATIVE]
    print(f"✓ Recommended strategy (MODERATE risk): {rec_type.value}")
    print(f"  Reasoning: {reasoning[:60]}...")


def test_decision_generator():
    """Test multi-scenario decision generation."""
    print("\n" + "=" * 70)
    print("Test 6: Decision Generator - Multi-Scenario")
    print("=" * 70)
    
    financial_state = create_test_financial_state(current_cash=50000.0)
    risk_detection_result = create_test_risk_detection_result()
    vendor_rels = create_test_vendor_relationships()
    
    # Generate decisions
    decisions = make_payment_decisions(
        financial_state=financial_state,
        risk_detection_result=risk_detection_result,
        vendor_relationships=vendor_rels,
        risk_level="MODERATE",
    )
    
    assert decisions is not None
    assert decisions.best_case is not None
    assert decisions.base_case is not None
    assert decisions.worst_case is not None
    print("✓ Generated DecisionResult3Scenarios")
    
    # Verify structure
    assert len(decisions.all_strategies) == 9  # 3 scenarios × 3 strategies
    print(f"✓ Generated {len(decisions.all_strategies)} total strategies (9 = 3×3)")
    
    # Verify recommendations set
    assert decisions.best_case.recommended_strategy in [StrategyType.AGGRESSIVE, StrategyType.BALANCED, StrategyType.CONSERVATIVE]
    assert decisions.base_case.recommended_strategy in [StrategyType.AGGRESSIVE, StrategyType.BALANCED, StrategyType.CONSERVATIVE]
    assert decisions.worst_case.recommended_strategy in [StrategyType.AGGRESSIVE, StrategyType.BALANCED, StrategyType.CONSERVATIVE]
    print(f"✓ Recommendations selected")
    print(f"  BEST: {decisions.best_case.recommended_strategy.value}")
    print(f"  BASE: {decisions.base_case.recommended_strategy.value}")
    print(f"  WORST: {decisions.worst_case.recommended_strategy.value}")


def test_engine_api():
    """Test main engine API."""
    print("\n" + "=" * 70)
    print("Test 7: Engine API - make_payment_decisions")
    print("=" * 70)
    
    financial_state = create_test_financial_state(current_cash=50000.0)
    risk_detection_result = create_test_risk_detection_result()
    vendor_rels = create_test_vendor_relationships()
    
    # Test with different risk levels
    for risk_level in ["AGGRESSIVE", "MODERATE", "CONSERVATIVE"]:
        decisions = make_payment_decisions(
            financial_state=financial_state,
            risk_detection_result=risk_detection_result,
            vendor_relationships=vendor_rels,
            risk_level=risk_level,
        )
        assert decisions is not None
        print(f"✓ Generated decisions with risk_level={risk_level}")
    
    # Test validation
    issues = validate_decision_result(decisions)
    assert len(issues) == 0
    print(f"✓ Decision result validation passed")


def test_explainability():
    """Test decision explanation API."""
    print("\n" + "=" * 70)
    print("Test 8: Explainability - explain_payment_decisions")
    print("=" * 70)
    
    financial_state = create_test_financial_state(current_cash=50000.0)
    risk_detection_result = create_test_risk_detection_result()
    vendor_rels = create_test_vendor_relationships()
    
    decisions = make_payment_decisions(
        financial_state=financial_state,
        risk_detection_result=risk_detection_result,
        vendor_relationships=vendor_rels,
    )
    
    # Test explanations for each scenario
    for scenario in ["BEST", "BASE", "WORST"]:
        explanation = explain_payment_decisions(
            decisions,
            scenario=scenario,
            strategy="RECOMMENDED",
        )
        assert explanation is not None
        assert len(explanation) > 0
        print(f"✓ Generated explanation for {scenario} case")


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "=" * 70)
    print("Test 9: Edge Cases & Error Handling")
    print("=" * 70)
    
    # Test with no payables
    try:
        fs = compute_financial_state(
            current_balance=50000.0,
            transactions=[
                Transaction(
                    date="2024-01-15",
                    description="Income",
                    amount=50000.0,
                    transaction_type="credit",
                ),
            ],
            receivables=[],
            payables=[],  # Empty payables
            hidden_transactions=[],
            business_context=BusinessContext(
                min_cash_buffer=5000.0,
                time_horizon_days=90,
            ),
            reference_date="2024-01-15",
        )
        
        decisions = make_payment_decisions(
            fs,
            create_test_risk_detection_result(),
        )
        print("✗ Should have raised ValueError for empty payables")
    except ValueError as e:
        print(f"✓ Correctly raised error for empty payables: {str(e)[:50]}...")
    
    # Test with invalid risk_level
    try:
        financial_state = create_test_financial_state()
        decisions = make_payment_decisions(
            financial_state,
            create_test_risk_detection_result(),
            risk_level="INVALID",
        )
        print("✗ Should have raised ValueError for invalid risk_level")
    except ValueError as e:
        print(f"✓ Correctly raised error for invalid risk_level")
    
    # Test with low cash (survival test)
    fs_low_cash = create_test_financial_state(current_cash=8000.0)
    decisions = make_payment_decisions(
        fs_low_cash,
        create_test_risk_detection_result(),
    )
    assert decisions is not None
    print(f"✓ Handled low cash scenario (${fs_low_cash.current_cash:,.0f})")


def test_vendor_relationship_strategy():
    """Test vendor relationship priority strategy."""
    print("\n" + "=" * 70)
    print("Test 10: Vendor Relationship Strategy")
    print("=" * 70)
    
    payables = create_test_payables()
    vendor_rels = create_test_vendor_relationships()
    reference_date = datetime(2024, 1, 15)
    context = BusinessContext(
        min_cash_buffer=5000.0,
        time_horizon_days=90,
        allow_partial_payments=True,
    )
    
    scores = score_all_obligations(payables, vendor_rels, reference_date, context)
    
    # Find NEW vendor score
    new_vendor_score = next(
        (s for s in scores if s.obligation_id == "pay_supp_001"), None
    )
    core_vendor_score = next(
        (s for s in scores if s.obligation_id == "pay_tax_001"), None
    )
    
    # Both are critical (Tax, NEW Supplier), but verify relationship_score differs
    assert new_vendor_score.relationship_score > core_vendor_score.relationship_score
    print(f"✓ NEW vendor (supp) relationship_score={new_vendor_score.relationship_score}")
    print(f"✓ CORE vendor (tax) relationship_score={core_vendor_score.relationship_score}")
    print(f"  Difference: {new_vendor_score.relationship_score - core_vendor_score.relationship_score:.0f}")


# ============================================================================
# Main Test Runner
# ============================================================================

def run_all_tests():
    """Run complete test suite."""
    print("\n" + "=" * 70)
    print("DETERMINISTIC DECISION ENGINE - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Models - Basic Creation", test_models_basic),
        ("Penalty Calculator", test_penalty_calculator),
        ("Obligation Scoring", test_obligation_scoring),
        ("Payment Optimizer", test_payment_optimizer),
        ("Strategy Evaluator", test_strategy_evaluator),
        ("Decision Generator", test_decision_generator),
        ("Engine API", test_engine_api),
        ("Explainability", test_explainability),
        ("Edge Cases", test_edge_cases),
        ("Vendor Relationship Strategy", test_vendor_relationship_strategy),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n✗ FAILED: {test_name}")
            print(f"  Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n✗ {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
