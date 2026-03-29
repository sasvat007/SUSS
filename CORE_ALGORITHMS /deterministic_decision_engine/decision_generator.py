"""
Decision Generator for DDE

Orchestrates the decision process across all 3 RDE scenarios (BEST/BASE/WORST).

For each scenario:
1. Extract cash available and time horizon
2. Score all obligations (legal, urgency, penalty, relationship, flexibility)
3. Generate 3 payment strategies (aggressive, balanced, conservative)
4. Evaluate and rank strategies
5. Select recommended strategy

Combines results into DecisionResult3Scenarios (9 total strategies).

Version: 0.0.1
"""

from typing import Dict, List
from datetime import datetime
from financial_state_engine.models import FinancialState, Payable, BusinessContext
from risk_detection_engine.models import RiskDetectionResult, RiskProjection
from .models import (
    DecisionResult,
    DecisionResult3Scenarios,
    VendorRelationship,
    ScenarioType,
)
from .obligation_scorer import score_all_obligations
from .payment_optimizer import PaymentOptimizer
from .strategy_evaluator import StrategyEvaluator


class DecisionGenerator:
    """Orchestrates decision generation across scenarios."""
    
    def __init__(
        self,
        financial_state: FinancialState,
        risk_detection_result: RiskDetectionResult,
        vendor_relationships: Dict[str, VendorRelationship],
        payables: List[Payable] = None,
        reference_date: datetime = None,
        risk_level: str = "MODERATE",
    ):
        """
        Initialize decision generator.
        
        Args:
            financial_state: FSE output
            risk_detection_result: RDE output (risk projections, scenarios)
            vendor_relationships: Dict of vendor_id → VendorRelationship
            payables: List of payables to evaluate (required)
            reference_date: Current date (default: now)
            risk_level: Business risk tolerance (AGGRESSIVE/MODERATE/CONSERVATIVE)
        """
        self.financial_state = financial_state
        self.risk_detection_result = risk_detection_result
        self.vendor_relationships = vendor_relationships
        self.reference_date = reference_date or datetime.now()
        self.risk_level = risk_level
        self.payables = payables or []
        
        # Create or extract business context
        if hasattr(financial_state, 'business_context') and financial_state.business_context:
            self.business_context = financial_state.business_context
        else:
            # Create default business context if not present
            from financial_state_engine import BusinessContext
            self.business_context = BusinessContext(
                min_cash_buffer=7000,
                time_horizon_days=14,
                allow_partial_payments=True
            )
        
        # Extract risk projections (best/base/worst)
        self.projections = {
            ScenarioType.BEST: risk_detection_result.best_case,
            ScenarioType.BASE: risk_detection_result.base_case,
            ScenarioType.WORST: risk_detection_result.worst_case,
        }
    
    def generate_decisions(self) -> DecisionResult3Scenarios:
        """
        Generate decisions across all 3 scenarios.
        
        Returns:
            DecisionResult3Scenarios with 9 total strategies (3 per scenario)
        
        Raises:
            ValueError: If financial_state or risk_detection_result invalid
        """
        if not self.payables:
            raise ValueError("No payables to process")
        
        if self.financial_state.current_balance is None:
            raise ValueError("Current balance not available")
        
        # Score all obligations once (same scores for all scenarios)
        obligation_scores = score_all_obligations(
            self.payables,
            self.vendor_relationships,
            self.reference_date,
            self.business_context,
            time_horizon_days=90,
        )
        
        # Generate decisions for each scenario
        best_result = self._generate_scenario_decisions(
            ScenarioType.BEST, obligation_scores
        )
        base_result = self._generate_scenario_decisions(
            ScenarioType.BASE, obligation_scores
        )
        worst_result = self._generate_scenario_decisions(
            ScenarioType.WORST, obligation_scores
        )
        
        # Generate overall recommendation (cross-scenario guidance)
        overall_recommendation = self._generate_overall_recommendation(
            best_result, base_result, worst_result
        )
        
        # Create final result
        return DecisionResult3Scenarios(
            best_case=best_result,
            base_case=base_result,
            worst_case=worst_result,
            overall_recommendation=overall_recommendation,
            financial_state_id=getattr(self.financial_state, "id", ""),
            risk_detection_id=getattr(self.risk_detection_result, "id", ""),
        )
    
    def _generate_scenario_decisions(
        self,
        scenario_type: ScenarioType,
        obligation_scores: List,
    ) -> DecisionResult:
        """
        Generate decisions for a specific RDE scenario.
        
        Args:
            scenario_type: BEST/BASE/WORST
            obligation_scores: Pre-computed obligation scores
        
        Returns:
            DecisionResult with 3 strategies and recommendation
        """
        projection = self.projections[scenario_type]
        
        # Calculate available cash for this scenario
        cash_available = self._calculate_available_cash(projection)
        
        # Generate 3 strategies for this scenario
        optimizer = PaymentOptimizer(
            payables=self.payables,
            obligation_scores=obligation_scores,
            business_context=self.business_context,
            available_cash=cash_available,
            scenario_type=scenario_type,
            reference_date=self.reference_date,
        )
        
        aggressive, balanced, conservative = optimizer.generate_all_strategies()
        
        # Evaluate and create result
        result = StrategyEvaluator.create_scenario_result(
            scenario_type=scenario_type,
            aggressive=aggressive,
            balanced=balanced,
            conservative=conservative,
            total_obligations=len(self.payables),
            total_obligation_amount=sum(p.amount for p in self.payables),
            risk_level=self.risk_level,
            cash_available=cash_available,
        )
        
        return result
    
    def _calculate_available_cash(self, projection: RiskProjection) -> float:
        """
        Calculate available cash for a scenario.
        
        Uses the RiskProjection's cash timeline to determine worst-case cash
        in the planning period.
        
        Args:
            projection: RiskProjection for this scenario
        
        Returns:
            Estimated available cash (current - min buffer from upcoming period)
        """
        from datetime import datetime
        
        # Start with available cash (after buffer)
        available = self.financial_state.available_cash
        
        # Adjust for worst-case shortfall in projection
        # (conservative: assume we'll need to handle any shortfalls)
        if projection.first_shortfall_date:
            # Parse date if string
            if isinstance(projection.first_shortfall_date, str):
                shortfall_date = datetime.strptime(projection.first_shortfall_date, "%Y-%m-%d")
            else:
                shortfall_date = projection.first_shortfall_date
            
            # Apply conservative discount if shortfall expected soon
            days_to_shortfall = (shortfall_date - self.reference_date).days
            if 0 < days_to_shortfall <= 30:
                # Shortfall within 30 days: reserve more cash
                available *= 0.8  # Conservative reduction
            elif days_to_shortfall <= 0:
                # Shortfall already here
                available *= 0.6
        
        # Ensure we don't go below min buffer
        min_buffer = self.business_context.min_cash_buffer
        return max(min_buffer, available)
    
    def _generate_overall_recommendation(
        self,
        best_result,
        base_result,
        worst_result,
    ) -> str:
        """
        Generate cross-scenario guidance.
        
        Recommends which scenarios to plan for and key strategies.
        
        Args:
            best_result: DecisionResult for BEST case
            base_result: DecisionResult for BASE case
            worst_result: DecisionResult for WORST case
        
        Returns:
            Human-readable recommendation
        """
        lines = []
        lines.append("=== Overall Recommendation ===\n")
        
        # Recommend planning scenarios
        lines.append("Planning Scenarios:")
        lines.append(f"  1. BASE Case (Most Likely): Use {base_result.recommended_strategy.value} strategy")
        lines.append(f"     Rationale: {base_result.reasoning}")
        lines.append("")
        
        lines.append(f"  2. WORST Case (Contingency): Use {worst_result.recommended_strategy.value} strategy")
        lines.append(f"     Rationale: {worst_result.reasoning}")
        lines.append("")
        
        if best_result.recommended_strategy != base_result.recommended_strategy:
            lines.append(f"  3. BEST Case (Opportunity): Use {best_result.recommended_strategy.value} strategy")
            lines.append(f"     Rationale: {best_result.reasoning}")
        else:
            lines.append(f"  3. BEST Case (Opportunity): Use {best_result.recommended_strategy.value} strategy (consistent with BASE)")
        
        lines.append("\nKey Observations:")
        
        # Compare scenarios
        base_payment = base_result.aggressive_strategy.total_payment + best_result.aggressive_strategy.total_payment + worst_result.aggressive_strategy.total_payment
        
        # Survival analysis
        if worst_result.conservative_strategy.survival_probability < 50:
            lines.append("  • CRITICAL: Conservative strategy inadequate for worst case; explore alternatives")
        if best_result.aggressive_strategy.total_penalty_cost > base_result.balanced_strategy.total_penalty_cost * 2:
            lines.append("  • Aggressive penalties significant; balanced approach recommended")
        
        lines.append("")
        lines.append("Action Items:")
        lines.append("  1. Implement BASE case strategy immediately")
        lines.append("  2. Monitor cash flow; be ready to switch to WORST case plan if needed")
        lines.append("  3. Review vendor relationships (prioritize NEW vendors)")
        lines.append("  4. Consider alternative funding if worst-case cash insufficient")
        
        return "\n".join(lines)


def generate_payment_decisions(
    financial_state: FinancialState,
    risk_detection_result: RiskDetectionResult,
    vendor_relationships: Dict[str, VendorRelationship],
    payables: List[Payable] = None,
    reference_date: datetime = None,
    risk_level: str = "MODERATE",
) -> DecisionResult3Scenarios:
    """
    Convenience function: generate decisions in one call.
    
    Args:
        financial_state: FSE output
        risk_detection_result: RDE output
        vendor_relationships: Dict of vendor relationships
        payables: List of payables to evaluate (required)
        reference_date: Current date (optional)
        risk_level: Business risk tolerance (optional)
    
    Returns:
        DecisionResult3Scenarios with all 9 strategies
    """
    generator = DecisionGenerator(
        financial_state,
        risk_detection_result,
        vendor_relationships,
        payables=payables,
        reference_date=reference_date,
        risk_level=risk_level,
    )
    return generator.generate_decisions()
