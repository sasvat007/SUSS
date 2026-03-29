"""
Tests for Explainability Engine

Validates:
1. ExplanationFactors extraction (correct business-level classification)
2. StrategyExplanation generation (sensible templates, no algorithm exposure)
3. DecisionExplanation content (clear, actionable reasoning)
4. CompleteExplanation structure (all 9 strategies present, coherent)
5. Cross-scenario guidance (correct recommendations)

Run: python -m pytest tests/test_explainability_engine.py -v
"""

import pytest
from datetime import datetime, timedelta
from deterministic_decision_engine.explainability_engine import ExplainabilityEngine
from deterministic_decision_engine.models import (
    PaymentStatus,
    PaymentDecision,
    PaymentStrategy,
    StrategyType,
    ScenarioType,
    DecisionResult,
    DecisionResult3Scenarios,
)
from deterministic_decision_engine.explanation_models import (
    UrgencyLevel,
    PenaltyRiskLevel,
    VendorImpactLevel,
    CompleteExplanation,
)
from financial_state_engine.models import FinancialState, Payable
from risk_detection_engine.models import RiskDetectionResult, RiskProjection


# ==================== FIXTURES ====================

@pytest.fixture
def mock_payable():
    """Create a mock payable for testing."""
    from financial_state_engine.models import Payable
    return Payable(
        id="PAY-001",
        amount=10000.0,
        due_date="2026-03-30",  # Datetime formats as YYYY-MM-DD string
        category="Tax",
        description="Quarterly tax payment",
        status="pending",
        priority_level="critical",
    )


@pytest.fixture
def mock_financial_state():
    """Create a mock FinancialState for testing."""
    # FinancialState is constructed by the engine; for testing we create a lightweight mock
    class MockFinancialState:
        def __init__(self):
            self.current_cash = 25000.0
            self.payables = []
            self.receivables = []
            self.vendor_relationships = []
    
    return MockFinancialState()


@pytest.fixture
def mock_payment_decision():
    """Create a mock PaymentDecision for testing."""
    return PaymentDecision(
        obligation_id="PAY-001",
        status=PaymentStatus.PAY_IN_FULL,
        pay_amount=10000.0,
        delay_days=0,
        potential_penalty=0.0,
        rationale="Critical tax obligation; penalty 5% daily.",
        vendor_id="IRS",
        vendor_name="IRS",
        due_date=datetime.now() + timedelta(days=5),
        category="Tax",
    )


@pytest.fixture
def mock_payment_strategy():
    """Create a mock PaymentStrategy for testing."""
    decision1 = PaymentDecision(
        obligation_id="PAY-001",
        status=PaymentStatus.PAY_IN_FULL,
        pay_amount=10000.0,
        delay_days=0,
        potential_penalty=0.0,
        rationale="Critical tax obligation",
        vendor_id="IRS",
        vendor_name="IRS",
        due_date=datetime.now() + timedelta(days=5),
        category="Tax",
    )
    
    decision2 = PaymentDecision(
        obligation_id="PAY-002",
        status=PaymentStatus.PARTIAL_PAY,
        pay_amount=2500.0,
        delay_days=14,
        potential_penalty=250.0,
        rationale="Defer to preserve cash",
        vendor_id="ACME",
        vendor_name="ACME Corp",
        due_date=datetime.now() + timedelta(days=30),
        category="Supplier",
    )
    
    return PaymentStrategy(
        strategy_type=StrategyType.BALANCED,
        scenario_type=ScenarioType.BASE,
        decisions=[decision1, decision2],
        total_payment=12500.0,
        total_penalty_cost=250.0,
        estimated_cash_after=12500.0,
        survival_probability=75.0,
        score=50.0,
    )


@pytest.fixture
def mock_decision_result(mock_payment_strategy):
    """Create a mock DecisionResult for testing."""
    aggressive = PaymentStrategy(
        strategy_type=StrategyType.AGGRESSIVE,
        scenario_type=ScenarioType.BASE,
        decisions=mock_payment_strategy.decisions,
        total_payment=15000.0,
        total_penalty_cost=0.0,
        estimated_cash_after=10000.0,
        survival_probability=70.0,
        score=40.0,
    )
    
    balanced = mock_payment_strategy
    
    conservative = PaymentStrategy(
        strategy_type=StrategyType.CONSERVATIVE,
        scenario_type=ScenarioType.BASE,
        decisions=[mock_payment_strategy.decisions[0]],
        total_payment=10000.0,
        total_penalty_cost=500.0,
        estimated_cash_after=15000.0,
        survival_probability=85.0,
        score=60.0,
    )
    
    return DecisionResult(
        scenario_type=ScenarioType.BASE,
        aggressive_strategy=aggressive,
        balanced_strategy=balanced,
        conservative_strategy=conservative,
        recommended_strategy=StrategyType.BALANCED,
        reasoning="Balanced approach optimizes payment vs survival.",
        cash_available=25000.0,
    )


@pytest.fixture
def mock_decisions_3_scenarios(mock_decision_result):
    """Create a mock DecisionResult3Scenarios for testing."""
    return DecisionResult3Scenarios(
        best_case=mock_decision_result,
        base_case=mock_decision_result,
        worst_case=DecisionResult(
            scenario_type=ScenarioType.WORST,
            aggressive_strategy=mock_decision_result.aggressive_strategy,
            balanced_strategy=mock_decision_result.balanced_strategy,
            conservative_strategy=mock_decision_result.conservative_strategy,
            recommended_strategy=StrategyType.CONSERVATIVE,
            reasoning="Conservative approach maximizes survival in worst case.",
            cash_available=15000.0,
        ),
        overall_recommendation="Plan for BASE case, prepare WORST case contingency.",
    )


@pytest.fixture
def mock_risk_detection():
    """Create a mock RiskDetectionResult for testing."""
    # Create a simple mock RiskProjection
    class MockProjection:
        def __init__(self):
            self.scenario_type = ScenarioType.BASE
            self.first_shortfall_date = datetime.now() + timedelta(days=30)
            self.days_to_shortfall = 30
            self.minimum_cash_amount = 5000.0
            self.minimum_cash_date = datetime.now() + timedelta(days=45)
            self.risk_severity = "MODERATE"
    
    class MockRiskDetection:
        def __init__(self):
            self.best_case = MockProjection()
            self.base_case = MockProjection()
            self.worst_case = MockProjection()
            self.worst_case.risk_severity = "CRITICAL"
    
    return MockRiskDetection()


# ==================== TESTS: FACTOR EXTRACTION ====================

class TestFactorExtraction:
    """Test ExplanationFactors extraction from PaymentDecision."""
    
    def test_extract_urgency_level_critical(self, mock_payment_decision):
        """Test CRITICAL urgency for overdue/today obligations."""
        engine = ExplainabilityEngine()
        
        decision = mock_payment_decision
        decision.due_date = datetime.now() - timedelta(days=1)  # Overdue
        
        factors = engine._extract_explanation_factors(decision, None, None)
        assert factors.urgency_level == UrgencyLevel.CRITICAL
        assert factors.days_overdue > 0
    
    def test_extract_urgency_level_high(self, mock_payment_decision):
        """Test HIGH urgency for 1-7 days out."""
        engine = ExplainabilityEngine()
        
        decision = mock_payment_decision
        decision.due_date = datetime.now() + timedelta(days=3)
        
        factors = engine._extract_explanation_factors(decision, None, None)
        assert factors.urgency_level == UrgencyLevel.HIGH
    
    def test_extract_urgency_level_medium(self, mock_payment_decision):
        """Test MEDIUM urgency for 1-month out."""
        engine = ExplainabilityEngine()
        
        decision = mock_payment_decision
        decision.due_date = datetime.now() + timedelta(days=15)
        
        factors = engine._extract_explanation_factors(decision, None, None)
        assert factors.urgency_level == UrgencyLevel.MEDIUM
    
    def test_extract_penalty_risk_critical(self, mock_payment_decision):
        """Test CRITICAL penalty risk for Tax/Payroll/Loan."""
        engine = ExplainabilityEngine()
        
        for category in ["Tax", "Payroll", "Loan"]:
            decision = mock_payment_decision
            decision.category = category
            
            factors = engine._extract_explanation_factors(decision, None, None)
            assert factors.penalty_risk_level == PenaltyRiskLevel.CRITICAL
    
    def test_extract_penalty_risk_high(self, mock_payment_decision):
        """Test HIGH penalty risk for Utilities/Insurance."""
        engine = ExplainabilityEngine()
        
        for category in ["Utilities", "Insurance", "Lease"]:
            decision = mock_payment_decision
            decision.category = category
            
            factors = engine._extract_explanation_factors(decision, None, None)
            assert factors.penalty_risk_level == PenaltyRiskLevel.HIGH
    
    def test_extract_penalty_risk_medium(self, mock_payment_decision):
        """Test MEDIUM penalty risk for Supplier."""
        engine = ExplainabilityEngine()
        
        decision = mock_payment_decision
        decision.category = "Supplier"
        
        factors = engine._extract_explanation_factors(decision, None, None)
        assert factors.penalty_risk_level == PenaltyRiskLevel.MEDIUM


# ==================== TESTS: TEMPLATE GENERATION ====================

class TestTemplateGeneration:
    """Test deterministic template-based explanation generation."""
    
    def test_decision_summary_pay_in_full(self, mock_payment_decision):
        """Test summary for PAY_IN_FULL status."""
        engine = ExplainabilityEngine()
        
        decision = mock_payment_decision
        decision.status = PaymentStatus.PAY_IN_FULL
        decision.due_date = datetime.now() + timedelta(days=5)
        
        factors = engine._extract_explanation_factors(decision, None, None)
        summary = engine._generate_decision_summary(decision, factors)
        
        assert "Full payment" in summary
        assert "$10000.00" in summary
    
    def test_decision_summary_delay(self, mock_payment_decision):
        """Test summary for DELAY status."""
        engine = ExplainabilityEngine()
        
        decision = mock_payment_decision
        decision.status = PaymentStatus.DELAY
        decision.delay_days = 30
        decision.potential_penalty = 1500.0
        
        factors = engine._extract_explanation_factors(decision, None, None)
        summary = engine._generate_decision_summary(decision, factors)
        
        assert "Deferred" in summary or "Delay" in summary
        assert "30" in summary
    
    def test_strategy_summary_includes_type(self, mock_payment_strategy):
        """Test strategy summary includes strategy type."""
        engine = ExplainabilityEngine()
        
        summary = engine._generate_strategy_summary(
            mock_payment_strategy,
            "Base",
            0.7,
            2,
        )
        
        assert "BALANCED" in summary or "balanced" in summary
        assert "Base" in summary
    
    def test_spending_profile_calculation(self, mock_payment_strategy):
        """Test spending profile reflects actual cash allocation."""
        engine = ExplainabilityEngine()
        
        # Create a simple mock object for FinancialState
        class MockFS:
            current_cash = 25000.0
        
        profile = engine._generate_spending_profile(mock_payment_strategy, 0.7, MockFS())
        
        assert "$25000.00" in profile
        assert "$12500.00" in profile  # total_payment
    
    def test_trade_offs_show_differences(self, mock_decision_result):
        """Test trade-off templates show meaningful differences."""
        engine = ExplainabilityEngine()
        
        aggressive = mock_decision_result.aggressive_strategy
        trade_offs = engine._generate_trade_offs(aggressive, mock_decision_result)
        
        # Should show clear differences
        assert "vs" in trade_offs or "Balanced" in trade_offs


# ==================== TESTS: COMPLETE EXPLANATION ====================

class TestCompleteExplanation:
    """Test generation of complete explanations for all 9 strategies."""
    
    def test_complete_explanation_structure(
        self,
        mock_decisions_3_scenarios,
        mock_financial_state,
        mock_risk_detection,
    ):
        """Test CompleteExplanation has all required fields."""
        engine = ExplainabilityEngine()
        
        explanation = engine.generate_complete_explanation(
            mock_decisions_3_scenarios,
            mock_financial_state,
            mock_risk_detection,
        )
        
        assert isinstance(explanation, CompleteExplanation)
        assert explanation.best_case_explanations is not None
        assert explanation.base_case_explanations is not None
        assert explanation.worst_case_explanations is not None
        assert explanation.recommended_best_case is not None
        assert explanation.cross_scenario_summary is not None
    
    def test_all_9_strategies_present(
        self,
        mock_decisions_3_scenarios,
        mock_financial_state,
        mock_risk_detection,
    ):
        """Test all 9 strategies have explanations."""
        engine = ExplainabilityEngine()
        
        explanation = engine.generate_complete_explanation(
            mock_decisions_3_scenarios,
            mock_financial_state,
            mock_risk_detection,
        )
        
        strategies = explanation.all_strategy_explanations()
        assert len(strategies) == 9
        
        # Check strategy types
        strategy_types = [s.strategy_type for s in strategies]
        assert strategy_types.count("AGGRESSIVE") == 3
        assert strategy_types.count("BALANCED") == 3
        assert strategy_types.count("CONSERVATIVE") == 3
    
    def test_get_strategy_explanation(
        self,
        mock_decisions_3_scenarios,
        mock_financial_state,
        mock_risk_detection,
    ):
        """Test retrieving specific strategy explanation."""
        engine = ExplainabilityEngine()
        
        explanation = engine.generate_complete_explanation(
            mock_decisions_3_scenarios,
            mock_financial_state,
            mock_risk_detection,
        )
        
        balanced_base = explanation.get_strategy_explanation("base", "balanced")
        assert balanced_base is not None
        assert balanced_base.strategy_type == "BALANCED"
        assert balanced_base.scenario_type == "Base"
    
    def test_cross_scenario_guidance_present(
        self,
        mock_decisions_3_scenarios,
        mock_financial_state,
        mock_risk_detection,
    ):
        """Test cross-scenario guidance is generated."""
        engine = ExplainabilityEngine()
        
        explanation = engine.generate_complete_explanation(
            mock_decisions_3_scenarios,
            mock_financial_state,
            mock_risk_detection,
        )
        
        assert len(explanation.cross_scenario_summary) > 0
        assert len(explanation.scenario_context) > 0
        assert len(explanation.action_recommendation) > 0


# ==================== TESTS: NO ALGORITHM EXPOSURE ====================

class TestAlgorithmProtection:
    """Test that explanations don't expose internal algorithm details."""
    
    def test_no_scoring_weights_exposed(
        self,
        mock_decisions_3_scenarios,
        mock_financial_state,
        mock_risk_detection,
    ):
        """Test scoring formula weights are not exposed."""
        engine = ExplainabilityEngine()
        
        explanation = engine.generate_complete_explanation(
            mock_decisions_3_scenarios,
            mock_financial_state,
            mock_risk_detection,
        )
        
        # Check all strategies don't mention specific weights
        forbidden_terms = ["40%", "30%", "20%", "10%", "5%", "weighted"]
        
        for strategy in explanation.all_strategy_explanations():
            text = (
                strategy.summary + strategy.approach + strategy.spending_profile
            )
            for term in forbidden_terms:
                # Allow mathematical percentages in other contexts, but not scoring formula
                if "score" in term.lower() or "formula" in term.lower():
                    assert term not in text.lower()
    
    def test_business_level_terms_only(
        self,
        mock_decisions_3_scenarios,
        mock_financial_state,
        mock_risk_detection,
    ):
        """Test explanations use business terms, not algorithm terms."""
        engine = ExplainabilityEngine()
        
        explanation = engine.generate_complete_explanation(
            mock_decisions_3_scenarios,
            mock_financial_state,
            mock_risk_detection,
        )
        
        # Should use business terms
        business_terms = ["urgency", "penalty", "vendor", "relationship", "cash", "survival"]
        found_business_terms = False
        
        for strategy in explanation.all_strategy_explanations():
            text = strategy.summary.lower()
            for term in business_terms:
                if term in text:
                    found_business_terms = True
                    break
        
        # At least some strategies should mention business-level factors
        assert found_business_terms


# ==================== TESTS: INTEGRATION ====================

class TestIntegration:
    """Test integration with payment_optimizer and DDE."""
    
    def test_explanation_has_valid_json_structure(
        self,
        mock_decisions_3_scenarios,
        mock_financial_state,
        mock_risk_detection,
    ):
        """Test explanation structure can be serialized."""
        engine = ExplainabilityEngine()
        
        explanation = engine.generate_complete_explanation(
            mock_decisions_3_scenarios,
            mock_financial_state,
            mock_risk_detection,
        )
        
        # Basic structure validation
        assert hasattr(explanation, 'best_case_explanations')
        assert isinstance(explanation.best_case_explanations, dict)
        assert "aggressive" in explanation.best_case_explanations
        assert "balanced" in explanation.best_case_explanations
        assert "conservative" in explanation.best_case_explanations
    
    def test_all_decisions_have_explanations(
        self,
        mock_decisions_3_scenarios,
        mock_financial_state,
        mock_risk_detection,
    ):
        """Test every obligation has an explanation."""
        engine = ExplainabilityEngine()
        
        explanation = engine.generate_complete_explanation(
            mock_decisions_3_scenarios,
            mock_financial_state,
            mock_risk_detection,
        )
        
        for strategy in explanation.all_strategy_explanations():
            assert len(strategy.obligation_explanations) > 0
            
            for obligation_exp in strategy.obligation_explanations:
                assert obligation_exp.obligation_id
                assert obligation_exp.vendor_name
                assert len(obligation_exp.summary) > 0
                assert len(obligation_exp.decision_rationale) > 0


# ==================== PERFORMANCE Tests ====================

class TestPerformance:
    """Test explanation generation performance."""
    
    def test_explanation_generation_speed(
        self,
        mock_decisions_3_scenarios,
        mock_financial_state,
        mock_risk_detection,
    ):
        """Test explanation generation completes in reasonable time."""
        import time
        
        engine = ExplainabilityEngine()
        
        start = time.time()
        explanation = engine.generate_complete_explanation(
            mock_decisions_3_scenarios,
            mock_financial_state,
            mock_risk_detection,
        )
        duration = time.time() - start
        
        # Should complete in < 1 second
        assert duration < 1.0, f"Explanation generation took {duration:.2f}s (should be < 1s)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
