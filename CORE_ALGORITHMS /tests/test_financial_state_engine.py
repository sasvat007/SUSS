"""
Comprehensive tests for the Financial State Engine.

Tests all modules with unit tests for individual components and integration
tests for end-to-end scenarios.
"""

import unittest
from datetime import datetime, timedelta
from financial_state_engine import (
    compute_financial_state, FinancialStateEngine,
    Transaction, Payable, Receivable, HiddenTransaction,
    BusinessContext, ValidationError
)
from financial_state_engine.validators import (
    validate_transaction, validate_payable, validate_receivable,
    TransactionValidationError, PayableValidationError, ReceivableValidationError
)
from financial_state_engine.utils import (
    get_today, get_date_n_days_ahead, days_between, is_date_in_future,
    get_all_occurrences_of_recurring_transaction
)
from financial_state_engine.aggregators import (
    compute_available_cash, aggregate_payables_by_timeline,
    compute_weighted_receivables, compute_receivable_quality_score
)
from financial_state_engine.metrics import (
    calculate_runway_days, calculate_obligation_pressure_ratio,
    calculate_buffer_sufficiency_days, score_runway_component,
    score_obligation_pressure_component
)
from financial_state_engine.health_scorer import compute_health_score


class TestUtilities(unittest.TestCase):
    """Test utility functions."""
    
    def test_get_today(self):
        """Test that get_today returns valid date string."""
        today = get_today()
        self.assertIsInstance(today, str)
        self.assertEqual(len(today), 10)  # YYYY-MM-DD
        self.assertEqual(today[4], '-')
        self.assertEqual(today[7], '-')
    
    def test_get_date_n_days_ahead(self):
        """Test date arithmetic."""
        today = get_today()
        tomorrow = get_date_n_days_ahead(1, today)
        diff = days_between(today, tomorrow)
        self.assertEqual(diff, 1)
    
    def test_is_date_in_future(self):
        """Test date comparison."""
        today = get_today()
        tomorrow = get_date_n_days_ahead(1, today)
        # Tomorrow is within 1 day ahead of today (inclusive range)
        self.assertTrue(is_date_in_future(tomorrow, 1, today))
        # Today itself is on day 0, which is within range [0, 1]
        self.assertTrue(is_date_in_future(today, 1, today))
        # Day after tomorrow is outside 1-day horizon
        day_after = get_date_n_days_ahead(2, today)
        self.assertFalse(is_date_in_future(day_after, 1, today))
    
    def test_get_all_occurrences_of_recurring_transaction(self):
        """Test recurring transaction date generation."""
        today = get_today()
        next_date = today
        occurrences = get_all_occurrences_of_recurring_transaction(
            next_date, "weekly", 30, today
        )
        # Should have ~4 occurrences in 30 days for weekly
        self.assertGreaterEqual(len(occurrences), 3)
        self.assertLessEqual(len(occurrences), 5)


class TestValidators(unittest.TestCase):
    """Test validation functions."""
    
    def test_validate_transaction_valid(self):
        """Test valid transaction passes validation."""
        tx = Transaction(
            date=get_today(),
            description="Payment",
            amount=-1000,
            transaction_type="debit"
        )
        # Should not raise
        validate_transaction(tx, 10000)
    
    def test_validate_transaction_invalid_date(self):
        """Test invalid date raises error."""
        tx = Transaction(
            date="2026/03/25",  # Wrong format
            description="Payment",
            amount=-1000,
            transaction_type="debit"
        )
        with self.assertRaises(TransactionValidationError):
            validate_transaction(tx, 10000)
    
    def test_validate_payable_valid(self):
        """Test valid payable passes validation."""
        payable = Payable(
            id="p001",
            amount=5000,
            due_date=get_date_n_days_ahead(5),
            description="Invoice",
            status="pending",
            priority_level="normal"
        )
        # Should not raise
        validate_payable(payable)
    
    def test_validate_payable_invalid_confidence(self):
        """Test receivable with invalid confidence raises error."""
        receivable = Receivable(
            id="r001",
            amount=1000,
            expected_date=get_date_n_days_ahead(3),
            description="Invoice",
            confidence=1.5  # Invalid: > 1.0
        )
        with self.assertRaises(ReceivableValidationError):
            validate_receivable(receivable)


class TestAggregators(unittest.TestCase):
    """Test aggregation functions."""
    
    def test_compute_available_cash(self):
        """Test available cash calculation."""
        balance = 100000
        buffer = 20000
        available = compute_available_cash(balance, buffer)
        self.assertEqual(available, 80000)
    
    def test_compute_available_cash_negative(self):
        """Test available cash can be negative (distress)."""
        balance = 10000
        buffer = 20000
        available = compute_available_cash(balance, buffer)
        self.assertEqual(available, -10000)
    
    def test_compute_weighted_receivables(self):
        """Test weighted receivables calculation."""
        today = get_today()
        receivables = [
            Receivable(
                id="r1",
                amount=1000,
                expected_date=get_date_n_days_ahead(5, today),
                description="Invoice 1",
                confidence=1.0  # 100% confident
            ),
            Receivable(
                id="r2",
                amount=1000,
                expected_date=get_date_n_days_ahead(10, today),
                description="Invoice 2",
                confidence=0.5  # 50% confident
            )
        ]
        
        weighted, unweighted = compute_weighted_receivables(
            receivables, 30, today
        )
        
        # Both within horizon: 1000*1.0 + 1000*0.5 = 1500 weighted
        self.assertEqual(weighted, 1500)
        self.assertEqual(unweighted, 2000)
    
    def test_compute_receivable_quality_score(self):
        """Test quality score calculation."""
        # High confidence
        quality = compute_receivable_quality_score(1500, 2000)
        self.assertEqual(quality, 0.75)
        
        # No receivables
        quality = compute_receivable_quality_score(0, 0)
        self.assertEqual(quality, 0.0)


class TestMetrics(unittest.TestCase):
    """Test metric calculations."""
    
    def test_score_runway_component(self):
        """Test runway component scoring."""
        self.assertEqual(score_runway_component(35), 100)
        self.assertEqual(score_runway_component(20), 75)
        self.assertEqual(score_runway_component(10), 50)
        self.assertEqual(score_runway_component(3), 25)
        self.assertEqual(score_runway_component(1), 0)
        self.assertEqual(score_runway_component(None), 100)  # Stable
    
    def test_score_obligation_pressure_component(self):
        """Test obligation pressure component scoring."""
        self.assertEqual(score_obligation_pressure_component(0.3), 100)
        self.assertEqual(score_obligation_pressure_component(0.8), 75)
        self.assertEqual(score_obligation_pressure_component(1.5), 50)
        self.assertEqual(score_obligation_pressure_component(2.5), 25)
        self.assertEqual(score_obligation_pressure_component(3.5), 0)
    
    def test_calculate_obligation_pressure_ratio(self):
        """Test obligation pressure ratio calculation."""
        # No pressure
        ratio = calculate_obligation_pressure_ratio(
            total_payables_within_horizon=1000,
            available_cash=5000,
            weighted_receivables=5000
        )
        self.assertAlmostEqual(ratio, 0.1, places=2)
        
        # High pressure
        ratio = calculate_obligation_pressure_ratio(
            total_payables_within_horizon=5000,
            available_cash=1000,
            weighted_receivables=1000
        )
        self.assertAlmostEqual(ratio, 2.5, places=2)


class TestHealthScorer(unittest.TestCase):
    """Test health scoring functions."""
    
    def test_compute_health_score_excellent(self):
        """Test health score for excellent position."""
        score, breakdown = compute_health_score(
            runway_days=40,
            pressure_ratio=0.3,
            quality_score=0.9,
            buffer_days=15
        )
        self.assertGreaterEqual(score, 80)
    
    def test_compute_health_score_critical(self):
        """Test health score for critical position."""
        score, breakdown = compute_health_score(
            runway_days=1,
            pressure_ratio=4.0,
            quality_score=0.2,
            buffer_days=0.5
        )
        self.assertLessEqual(score, 20)
    
    def test_health_score_weights_validation(self):
        """Test that weight validation works."""
        with self.assertRaises(ValueError):
            # Weights don't sum to 1.0
            compute_health_score(
                runway_days=10,
                pressure_ratio=1.0,
                quality_score=0.5,
                buffer_days=5,
                runway_weight=0.5,
                pressure_weight=0.5,
                quality_weight=0.5,  # Sums to 1.5
                buffer_weight=0.0
            )


class TestIntegrationScenarioA(unittest.TestCase):
    """Integration test: Stable Business scenario."""
    
    def test_scenario_stable_business(self):
        """
        Scenario A: Stable Business
        - High balance (100k)
        - Predictable receivables (high confidence)
        - Low obligations (20k)
        - Good buffer (20k)
        
        Expected: Health score ~85+
        """
        today = get_today()
        
        state = compute_financial_state(
            current_balance=100000,
            transactions=[
                Transaction(
                    date=today,
                    description="Sales",
                    amount=50000,
                    transaction_type="credit"
                )
            ],
            payables=[
                Payable(
                    id="p1",
                    amount=5000,
                    due_date=get_date_n_days_ahead(5, today),
                    description="Vendor payment",
                    status="pending"
                ),
                Payable(
                    id="p2",
                    amount=8000,
                    due_date=get_date_n_days_ahead(15, today),
                    description="Expense",
                    status="pending"
                )
            ],
            receivables=[
                Receivable(
                    id="r1",
                    amount=30000,
                    expected_date=get_date_n_days_ahead(7, today),
                    description="Client Invoice",
                    confidence=0.95  # Very confident
                )
            ],
            hidden_transactions=[],
            business_context=BusinessContext(
                min_cash_buffer=20000,
                time_horizon_days=30,
                allow_partial_payments=True,
                avg_payment_delay_days=0
            ),
            reference_date=today
        )
        
        # Assertions
        self.assertGreater(state.health_score, 75)
        self.assertIsNone(state.cash_runway_days)  # Stable
        self.assertLess(state.obligation_pressure_ratio, 0.5)
        self.assertFalse(state.status_flags.get("critical_status", False))
        self.assertFalse(state.status_flags.get("limited_runway", False))


class TestIntegrationScenarioB(unittest.TestCase):
    """Integration test: Distressed Business scenario."""
    
    def test_scenario_distressed_business(self):
        """
        Scenario B: Distressed Business
        - Low balance (15k)
        - Uncertain receivables (low confidence)
        - High obligations (40k)
        - Low buffer (05k)
        
        Expected: Health score ~20-40, signals distress
        """
        today = get_today()
        
        state = compute_financial_state(
            current_balance=8000,  # Very low balance
            transactions=[
                Transaction(
                    date=today,
                    description="Withdrawal",
                    amount=-5000,
                    transaction_type="debit"
                )
            ],
            payables=[
                Payable(
                    id="p1",
                    amount=10000,
                    due_date=today,  # Due now
                    description="Urgent payment",
                    status="due"
                ),
                Payable(
                    id="p2",
                    amount=15000,
                    due_date=get_date_n_days_ahead(3, today),
                    description="Vendor",
                    status="pending"
                ),
                Payable(
                    id="p3",
                    amount=15000,
                    due_date=get_date_n_days_ahead(5, today),
                    description="Expense",
                    status="pending"
                )
            ],
            receivables=[
                Receivable(
                    id="r1",
                    amount=25000,
                    expected_date=get_date_n_days_ahead(20, today),
                    description="Client invoice",
                    confidence=0.2  # Very low confidence
                )
            ],
            hidden_transactions=[
                HiddenTransaction(
                    id="h1",
                    transaction_type="salary",
                    amount=-3000,  # Outflow
                    frequency="monthly",
                    next_date=get_date_n_days_ahead(10, today),
                    category="Employee salary"
                )
            ],
            business_context=BusinessContext(
                min_cash_buffer=3000,
                time_horizon_days=30,
                allow_partial_payments=False,
                avg_payment_delay_days=5
            ),
            reference_date=today
        )
        
        # Assertions
        self.assertLess(state.health_score, 50)
        self.assertIsNotNone(state.cash_runway_days)
        self.assertLess(state.cash_runway_days, 5)  # Very limited runway
        self.assertGreater(state.obligation_pressure_ratio, 1.5)
        # Status flags - at least some warning flags should be raised
        has_status_flags = (
            state.status_flags.get("critical_runway", False) or
            state.status_flags.get("limited_runway", False) or
            state.status_flags.get("high_pressure", False)
        )
        self.assertTrue(has_status_flags)


class TestIntegrationScenarioC(unittest.TestCase):
    """Integration test: Edge case scenario."""
    
    def test_scenario_zero_balance_no_receivables(self):
        """
        Scenario C: Edge Case
        - Zero balance
        - No receivables  
        - High obligations
        
        Expected: Health score very low (< 20), critical status
        """
        today = get_today()
        
        state = compute_financial_state(
            current_balance=0,
            transactions=[],
            payables=[
                Payable(
                    id="p1",
                    amount=50000,
                    due_date=get_date_n_days_ahead(5, today),
                    description="Debt",
                    status="pending"
                )
            ],
            receivables=[],
            hidden_transactions=[],
            business_context=BusinessContext(
                min_cash_buffer=10000,
                time_horizon_days=30
            ),
            reference_date=today
        )
        
        # Assertions
        self.assertLess(state.health_score, 20)  # Very low score
        self.assertTrue(state.status_flags.get("critical_status"))
        self.assertEqual(state.available_cash, -10000)  # Negative available cash


class TestJSONSerialization(unittest.TestCase):
    """Test JSON serialization of outputs."""
    
    def test_financial_state_to_json(self):
        """Test that FinancialState can be converted to JSON."""
        today = get_today()
        
        state = compute_financial_state(
            current_balance=50000,
            transactions=[],
            payables=[
                Payable(
                    id="p1",
                    amount=5000,
                    due_date=get_date_n_days_ahead(10, today),
                    description="Payment",
                    status="pending"
                )
            ],
            receivables=[
                Receivable(
                    id="r1",
                    amount=10000,
                    expected_date=get_date_n_days_ahead(5, today),
                    description="Invoice",
                    confidence=0.8
                )
            ],
            hidden_transactions=[],
            business_context=BusinessContext(
                min_cash_buffer=10000,
                time_horizon_days=30
            ),
            reference_date=today
        )
        
        # Convert to dict
        state_dict = state.to_json_dict()
        
        # Verify structure
        self.assertIn("health_score", state_dict)
        self.assertIn("health_score_breakdown", state_dict)
        self.assertIn("cash_flow_timeline", state_dict)
        self.assertIn("status_flags", state_dict)
        
        # Verify it's JSON-serializable
        import json
        json_str = json.dumps(state_dict)
        self.assertIsInstance(json_str, str)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""
    
    def test_invalid_business_context_raises_error(self):
        """Test that invalid business context raises error."""
        today = get_today()
        
        with self.assertRaises(ValidationError):
            compute_financial_state(
                current_balance=50000,
                transactions=[],
                payables=[],
                receivables=[],
                hidden_transactions=[],
                business_context=BusinessContext(
                    min_cash_buffer=10000,
                    time_horizon_days=-1  # Invalid: negative
                ),
                reference_date=today
            )
    
    def test_invalid_receivable_confidence_raises_error(self):
        """Test that invalid receivable confidence raises error."""
        today = get_today()
        
        with self.assertRaises(ValidationError):
            compute_financial_state(
                current_balance=50000,
                transactions=[],
                payables=[],
                receivables=[
                    Receivable(
                        id="r1",
                        amount=1000,
                        expected_date=get_date_n_days_ahead(5, today),
                        description="Invoice",
                        confidence=1.5  # Invalid: > 1.0
                    )
                ],
                hidden_transactions=[],
                business_context=BusinessContext(
                    min_cash_buffer=10000,
                    time_horizon_days=30
                ),
                reference_date=today
            )


if __name__ == '__main__':
    unittest.main()
