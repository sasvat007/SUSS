"""
Explainability Engine

Generates deterministic, business-friendly explanations for payment decisions
across all 9 strategies (3 scenarios × 3 approaches).

All explanations are template-driven and deterministic. No AI generation of logic—
only optional LLM polish for readability.

Version: 0.0.1
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from deterministic_decision_engine.models import (
    DecisionResult3Scenarios,
    PaymentStrategy,
    PaymentDecision,
    StrategyType,
    ScenarioType,
    PaymentStatus,
)
from deterministic_decision_engine.explanation_models import (
    CompleteExplanation,
    StrategyExplanation,
    DecisionExplanation,
    ExplanationFactors,
    StrategyComparison,
    StrategyComparisonRow,
    UrgencyLevel,
    PenaltyRiskLevel,
    VendorImpactLevel,
)
from financial_state_engine.models import FinancialState
from risk_detection_engine.models import RiskDetectionResult


class ExplainabilityEngine:
    """
    Generates deterministic explanations for payment decisions.
    
    Main API: generate_complete_explanation(decisions, financial_state, risk_detection)
    
    Process:
    1. Extract business-level factors for each obligation
    2. Generate decision explanations using deterministic templates
    3. Build strategy-level summaries with comparisons
    4. Aggregate into cross-scenario guidance
    5. Optionally refine text via LLM (readability only)
    """
    
    def __init__(self, enable_llm_refinement: bool = False):
        """
        Initialize the Explainability Engine.
        
        Args:
            enable_llm_refinement: Whether to refine text via LLM for better readability.
                                   When False, uses deterministic templates only.
        """
        self.enable_llm_refinement = enable_llm_refinement
    
    def generate_complete_explanation(
        self,
        decisions: DecisionResult3Scenarios,
        financial_state: FinancialState,
        risk_detection: RiskDetectionResult,
    ) -> CompleteExplanation:
        """
        Generate complete explanations for all 9 payment strategies.
        
        Args:
            decisions: Output from DDE engine (DecisionResult3Scenarios)
            financial_state: Current financial state
            risk_detection: Risk detection projections (best/base/worst)
        
        Returns:
            CompleteExplanation with nested strategy explanations for all 9 strategies
        
        Raises:
            ValueError: If inputs are invalid or incomplete
        """
        if not decisions or not decisions.best_case:
            raise ValueError("decisions must contain valid best_case, base_case, worst_case")
        
        # Generate explanations for all 9 strategies (3 scenarios × 3 strategies)
        best_explanations = self._build_scenario_explanations(
            decisions.best_case,
            financial_state,
            risk_detection.best_case,
            "Best",
        )
        
        base_explanations = self._build_scenario_explanations(
            decisions.base_case,
            financial_state,
            risk_detection.base_case,
            "Base",
        )
        
        worst_explanations = self._build_scenario_explanations(
            decisions.worst_case,
            financial_state,
            risk_detection.worst_case,
            "Worst",
        )
        
        # Aggregate critical/flexible obligations
        critical, flexible = self._identify_critical_vs_flexible(decisions)
        
        # Build cross-scenario guidance
        cross_scenario_summary, scenario_context, action_rec = self._generate_cross_scenario_guidance(
            financial_state,
            risk_detection,
            decisions,
        )
        
        return CompleteExplanation(
            best_case_explanations=best_explanations,
            base_case_explanations=base_explanations,
            worst_case_explanations=worst_explanations,
            recommended_best_case=decisions.best_case.recommended_strategy.value.lower(),
            recommended_base_case=decisions.base_case.recommended_strategy.value.lower(),
            recommended_worst_case=decisions.worst_case.recommended_strategy.value.lower(),
            cross_scenario_summary=cross_scenario_summary,
            scenario_context=scenario_context,
            action_recommendation=action_rec,
            critical_obligations=critical,
            flexible_obligations=flexible,
        )
    
    def _build_scenario_explanations(
        self,
        decision_result,
        financial_state: FinancialState,
        risk_projection,
        scenario_name: str,
    ) -> Dict[str, StrategyExplanation]:
        """
        Build explanations for all 3 strategies in one scenario.
        
        Returns dict with keys: "aggressive", "balanced", "conservative"
        """
        return {
            "aggressive": self._build_strategy_explanation(
                decision_result.aggressive_strategy,
                decision_result,
                financial_state,
                scenario_name,
            ),
            "balanced": self._build_strategy_explanation(
                decision_result.balanced_strategy,
                decision_result,
                financial_state,
                scenario_name,
            ),
            "conservative": self._build_strategy_explanation(
                decision_result.conservative_strategy,
                decision_result,
                financial_state,
                scenario_name,
            ),
        }
    
    def _build_strategy_explanation(
        self,
        strategy: PaymentStrategy,
        decision_result,
        financial_state: FinancialState,
        scenario_name: str,
    ) -> StrategyExplanation:
        """
        Build complete explanation for one strategy.
        """
        # Extract factor info for each decision
        decision_explanations = []
        for decision in strategy.decisions:
            obs_data = self._find_obligation_data(decision.obligation_id, financial_state)
            vendor_data = self._find_vendor_data(decision.vendor_id, financial_state)
            
            factors = self._extract_explanation_factors(decision, obs_data, vendor_data)
            
            # Build comparison (what if chose different strategy)
            comparison = self._build_strategy_comparison(
                decision,
                strategy,
                decision_result,
                factors,
            )
            
            decision_exp = DecisionExplanation(
                obligation_id=decision.obligation_id,
                vendor_name=decision.vendor_name,
                category=decision.category,
                decision_status=self._format_payment_status(decision.status),
                pay_amount=decision.pay_amount,
                delay_days=decision.delay_days,
                factors=factors,
                summary=self._generate_decision_summary(decision, factors),
                decision_rationale=decision.rationale,  # Already good from engine
                implications=self._generate_implications(decision, factors, financial_state),
                comparison=comparison,
                alternative_scenarios=self._generate_alternatives(decision, decision_result),
            )
            decision_explanations.append(decision_exp)
        
        # Identify highest/deferred items
        paid_items = [
            f"{d.vendor_name} ({d.category}): ${d.pay_amount:.2f}"
            for d in decision_explanations
            if d.pay_amount > 0
        ][:5]  # Top 5
        
        deferred_items = [
            f"{d.vendor_name} ({d.category}): {d.delay_days}d delay"
            for d in decision_explanations
            if d.delay_days > 0
        ][:5]  # Top 5
        
        # Build strategy explanation
        strategy_type_name = strategy.strategy_type.value.lower()
        spending_pct = self._get_spending_fraction(strategy.strategy_type)
        
        return StrategyExplanation(
            strategy_type=strategy.strategy_type.value,
            scenario_type=scenario_name,
            summary=self._generate_strategy_summary(
                strategy,
                scenario_name,
                spending_pct,
                len(strategy.decisions),
            ),
            spending_profile=self._generate_spending_profile(
                strategy,
                spending_pct,
                financial_state,
            ),
            approach=self._generate_approach_explanation(strategy.strategy_type),
            obligation_explanations=decision_explanations,
            total_payment=strategy.total_payment,
            total_penalty_cost=strategy.total_penalty_cost,
            estimated_cash_after=strategy.estimated_cash_after,
            survival_probability=strategy.survival_probability,
            key_trade_offs=self._generate_trade_offs(strategy, decision_result),
            strength=self._get_strategy_strength(strategy.strategy_type),
            weakness=self._get_strategy_weakness(strategy.strategy_type),
            best_for=self._get_best_for_description(strategy.strategy_type),
            highest_priority_items=paid_items,
            deferred_items=deferred_items,
            execution_guidance=self._generate_execution_guidance(strategy.strategy_type),
        )
    
    def _extract_explanation_factors(
        self,
        decision: PaymentDecision,
        obligation_data: Optional[Dict],
        vendor_data: Optional[Dict],
    ) -> ExplanationFactors:
        """
        Extract business-level factors without exposing algorithm.
        
        Maps scoring components to business terminology:
        - urgency_score → UrgencyLevel (Critical/High/Medium/Low)
        - penalty_score → PenaltyRiskLevel
        - relationship_score → VendorImpactLevel
        """
        from datetime import datetime
        
        # Calculate days to due
        if decision.due_date:
            # Parse due_date if it's a string
            if isinstance(decision.due_date, str):
                due_date = datetime.strptime(decision.due_date, "%Y-%m-%d")
            else:
                due_date = decision.due_date
            
            delta = due_date - datetime.now()
            days_to_due = delta.days
        else:
            days_to_due = 0
        
        days_overdue = max(0, -days_to_due) if days_to_due < 0 else 0
        
        # Determine urgency level
        if days_to_due <= 0:
            urgency = UrgencyLevel.CRITICAL
        elif days_to_due <= 7:
            urgency = UrgencyLevel.HIGH
        elif days_to_due <= 30:
            urgency = UrgencyLevel.MEDIUM
        else:
            urgency = UrgencyLevel.LOW
        
        # Determine penalty risk level (from category & penalty score)
        penalty_risk = self._assess_penalty_risk(decision.category)
        
        # Determine vendor impact level
        vendor_impact = self._assess_vendor_impact(vendor_data, decision.vendor_name)
        
        # Check flexibility
        can_partial = self._can_make_partial_payment(obligation_data, decision.category)
        
        # Estimate penalty if delayed 1 week
        estimated_penalty = self._estimate_penalty_for_delay(
            decision.category,
            decision.original_amount if hasattr(decision, 'original_amount') else decision.pay_amount,
            7,  # 1 week
        )
        
        return ExplanationFactors(
            obligation_id=decision.obligation_id,
            vendor_name=decision.vendor_name,
            category=decision.category,
            amount=decision.pay_amount if decision.status == PaymentStatus.PAY_IN_FULL else decision.pay_amount,
            urgency_level=urgency,
            days_to_due=days_to_due,
            days_overdue=days_overdue,
            penalty_risk_level=penalty_risk,
            estimated_penalty=estimated_penalty,
            penalty_accrual=self._get_penalty_accrual_description(decision.category),
            vendor_impact_level=vendor_impact,
            vendor_relationship=self._get_vendor_relationship_description(vendor_data),
            years_with_vendor=vendor_data.get("years_with_business") if vendor_data else None,
            flexibility_assessment=can_partial,
            partial_payment_allowed=can_partial,
        )
    
    def _build_strategy_comparison(
        self,
        decision: PaymentDecision,
        current_strategy: PaymentStrategy,
        decision_result,
        factors: ExplanationFactors,
    ) -> Optional[StrategyComparison]:
        """
        Build comparison showing what happens with each strategy for this obligation.
        """
        # Find the same obligation decision in aggressive/balanced/conservative
        strategies_map = {
            "aggressive": decision_result.aggressive_strategy,
            "balanced": decision_result.balanced_strategy,
            "conservative": decision_result.conservative_strategy,
        }
        
        rows = []
        for strat_name, strategy in strategies_map.items():
            obs_decision = next(
                (d for d in strategy.decisions if d.obligation_id == decision.obligation_id),
                None,
            )
            
            if obs_decision:
                row = StrategyComparisonRow(
                    strategy_name=strat_name.capitalize(),
                    decision=self._format_payment_status(obs_decision.status),
                    penalty_cost=obs_decision.potential_penalty,
                    survival_impact=strategy.survival_probability,  # Overall strategy survival
                    cash_impact=strategy.estimated_cash_after,
                    rationale="",  # Will be populated by template
                )
                rows.append(row)
        
        return StrategyComparison(
            obligation_id=decision.obligation_id,
            vendor_name=decision.vendor_name,
            comparison_rows=rows,
        ) if rows else None
    
    # ==================== TEMPLATE GENERATORS (DETERMINISTIC) ====================
    
    def _generate_decision_summary(self, decision: PaymentDecision, factors: ExplanationFactors) -> str:
        """1-2 sentence summary of what decision was made."""
        status_str = self._format_payment_status(decision.status)
        
        if decision.status == PaymentStatus.PAY_IN_FULL:
            return f"{factors.vendor_name} ({factors.category}): Full payment of ${decision.pay_amount:.2f}. Due in {factors.days_to_due} days."
        elif decision.status == PaymentStatus.PARTIAL_PAY:
            return f"{factors.vendor_name} ({factors.category}): Partial payment of ${decision.pay_amount:.2f}. Delay remainder {decision.delay_days} days."
        elif decision.status == PaymentStatus.DELAY:
            return f"{factors.vendor_name} ({factors.category}): Deferred {decision.delay_days} days. Penalty risk: ${decision.potential_penalty:.2f}."
        else:  # STRATEGIC_DEFAULT
            return f"{factors.vendor_name} ({factors.category}): Strategic deferral. Estimated penalty: ${decision.potential_penalty:.2f}."
    
    def _generate_implications(
        self,
        decision: PaymentDecision,
        factors: ExplanationFactors,
        financial_state: FinancialState,
    ) -> str:
        """What does this decision mean for cash, penalties, relationships?"""
        implications = []
        
        if decision.status == PaymentStatus.PAY_IN_FULL:
            implications.append(f"✓ Pays obligation in full. No penalties. Preserves vendor relationship.")
            if decision.potential_penalty == 0:
                implications.append(f"✓ No financial penalty for timely payment.")
        
        elif decision.status == PaymentStatus.PARTIAL_PAY:
            implications.append(f"⚠ Partial payment (${ decision.pay_amount:.2f}). Remaining balance deferred.")
            implications.append(f"⚠ Potential penalty: ${decision.potential_penalty:.2f} if not paid within {decision.delay_days} days.")
        
        elif decision.status == PaymentStatus.DELAY:
            implications.append(f"⚠ Payment deferred {decision.delay_days} days.")
            implications.append(f"⚠ Penalty risk: ${decision.potential_penalty:.2f}.")
            implications.append(f"ℹ Relationship risk: {factors.vendor_impact_level.value} (may affect future terms).")
        
        else:  # STRATEGIC_DEFAULT
            implications.append(f"⚠ Strategic default. Deferred payment prioritizes survival.")
            implications.append(f"⚠ Penalty: ~${decision.potential_penalty:.2f}.")
            implications.append(f"⚠ Vendor may restrict credit or require deposits.")
        
        return " ".join(implications)
    
    def _generate_alternatives(self, decision: PaymentDecision, decision_result) -> str:
        """Show what alternatives look like (if chose different strategy)."""
        alternatives = []
        
        # Check same obligation in other strategies
        for strat in [decision_result.aggressive_strategy, decision_result.balanced_strategy, decision_result.conservative_strategy]:
            other_decision = next(
                (d for d in strat.decisions if d.obligation_id == decision.obligation_id),
                None,
            )
            if other_decision and other_decision.status != decision.status:
                alt_desc = f"{strat.strategy_type.value}: {self._format_payment_status(other_decision.status)} (penalty ${other_decision.potential_penalty:.2f})"
                alternatives.append(alt_desc)
        
        return " | ".join(alternatives) if alternatives else "Same decision in all strategies."
    
    def _generate_strategy_summary(
        self,
        strategy: PaymentStrategy,
        scenario_name: str,
        spending_pct: float,
        num_obligations: int,
    ) -> str:
        """1-2 sentence description of strategy approach."""
        strategy_type = strategy.strategy_type.value
        action = {
            "AGGRESSIVE": f"prioritizes paying high-priority obligations to minimize penalties",
            "BALANCED": f"balances payment of critical items with survival cash preservation",
            "CONSERVATIVE": f"focuses on survival by paying only essential obligations",
        }.get(strategy_type, "")
        
        return f"{strategy_type} strategy in {scenario_name} case: Spend {spending_pct:.0%} available cash across {num_obligations} obligations. {action}."
    
    def _generate_spending_profile(
        self,
        strategy: PaymentStrategy,
        spending_pct: float,
        financial_state: FinancialState,
    ) -> str:
        """Describe how cash is allocated."""
        paid_count = len([d for d in strategy.decisions if d.pay_amount > 0])
        delayed_count = len([d for d in strategy.decisions if d.delay_days > 0])
        
        return (
            f"Total cash available: ₹{financial_state.available_cash:.2f}. "
            f"Allocation: Pay {paid_count} obligations (₹{strategy.total_payment:.2f}), "
            f"defer {delayed_count} obligations (penalties: ₹{strategy.total_penalty_cost:.2f}), "
            f"preserve ₹{strategy.estimated_cash_after:.2f} for emergencies."
        )
    
    def _generate_approach_explanation(self, strategy_type: StrategyType) -> str:
        """Explain the philosophical approach of this strategy."""
        explanations = {
            StrategyType.AGGRESSIVE: "This approach prioritizes minimizing penalties and legal risks by paying high-priority obligations in full, even if it reduces available cash.",
            StrategyType.BALANCED: "This approach balances maintaining vendor relationships and minimizing penalties while preserving enough cash to handle unexpected shortfalls.",
            StrategyType.CONSERVATIVE: "This approach prioritizes business survival by deferring non-critical obligations and maximizing available cash for essential operations.",
        }
        return explanations.get(strategy_type, "")
    
    def _generate_trade_offs(self, strategy: PaymentStrategy, decision_result) -> str:
        """Compare this strategy to others in same scenario."""
        strategy_type = strategy.strategy_type.value
        
        if strategy_type == "AGGRESSIVE":
            balanced = decision_result.balanced_strategy
            return (
                f"vs Balanced: ${strategy.total_payment - balanced.total_payment:+.2f} more in payments, "
                f"${balanced.total_penalty_cost - strategy.total_penalty_cost:+.2f} more penalty risk, "
                f"{strategy.survival_probability - balanced.survival_probability:+.1f}% survival margin"
            )
        elif strategy_type == "BALANCED":
            aggressive = decision_result.aggressive_strategy
            conservative = decision_result.conservative_strategy
            return (
                f"vs Aggressive: ${aggressive.total_payment - strategy.total_payment:.2f} less paid, ${strategy.total_penalty_cost - aggressive.total_penalty_cost:.2f} less penalty. "
                f"vs Conservative: ${strategy.total_payment - conservative.total_payment:.2f} more paid, ${conservative.total_penalty_cost - strategy.total_penalty_cost:.2f} more penalty."
            )
        else:  # CONSERVATIVE
            balanced = decision_result.balanced_strategy
            aggressive = decision_result.aggressive_strategy
            return (
                f"vs Balanced: ${balanced.total_payment - strategy.total_payment:.2f} less in payments, "
                f"${strategy.total_penalty_cost - balanced.total_penalty_cost:+.2f} more penalty risk, "
                f"{strategy.survival_probability - balanced.survival_probability:+.1f}% survival margin"
            )
    
    def _generate_execution_guidance(self, strategy_type: StrategyType) -> str:
        """Practical steps to implement this strategy."""
        guidance = {
            StrategyType.AGGRESSIVE: "1. Pay all obligations marked PAY_IN_FULL immediately. 2. Contact vendors marked PARTIAL_PAY to arrange residual payment terms. 3. Monitor penalties carefully.",
            StrategyType.BALANCED: "1. Pay critical/legal obligations first. 2. Negotiate payment terms for flexible obligations. 3. Reserve remaining cash for working capital. 4. Communicate proactively with key vendors.",
            StrategyType.CONSERVATIVE: "1. Pay only critical obligations (Tax, Payroll, Loans). 2. Contact other vendors to negotiate extended terms or defer. 3. Preserve all possible cash. 4. Prioritize revenue generation.",
        }
        return guidance.get(strategy_type, "")
    
    # ==================== HELPER METHODS ====================
    
    def _get_spending_fraction(self, strategy_type: StrategyType) -> float:
        """Get spending % for strategy type."""
        return {
            StrategyType.AGGRESSIVE: 0.90,
            StrategyType.BALANCED: 0.70,
            StrategyType.CONSERVATIVE: 0.40,
        }.get(strategy_type, 0.7)
    
    def _format_payment_status(self, status: PaymentStatus) -> str:
        """Convert PaymentStatus enum to readable text."""
        descriptions = {
            PaymentStatus.PAY_IN_FULL: "Pay in full",
            PaymentStatus.PARTIAL_PAY: "Partial payment",
            PaymentStatus.DELAY: "Delay payment",
            PaymentStatus.STRATEGIC_DEFAULT: "Strategic deferral",
        }
        return descriptions.get(status, status.value if hasattr(status, 'value') else str(status))
    
    def _assess_penalty_risk(self, category: str) -> PenaltyRiskLevel:
        """Map category to penalty risk level (without exposing scores)."""
        critical = {"Tax", "Payroll", "Loan"}
        high = {"Utilities", "Insurance", "Lease"}
        
        if category in critical:
            return PenaltyRiskLevel.CRITICAL
        elif category in high:
            return PenaltyRiskLevel.HIGH
        elif category in {"Supplier", "Contractor"}:
            return PenaltyRiskLevel.MEDIUM
        else:
            return PenaltyRiskLevel.LOW
    
    def _assess_vendor_impact(self, vendor_data: Optional[Dict], vendor_name: str) -> VendorImpactLevel:
        """Classify vendor relationship impact."""
        if not vendor_data:
            return VendorImpactLevel.MEDIUM
        
        years = vendor_data.get("years_with_business", 0)
        if years > 3:
            return VendorImpactLevel.CRITICAL
        elif years > 1:
            return VendorImpactLevel.HIGH
        elif years > 0:
            return VendorImpactLevel.MEDIUM
        else:
            return VendorImpactLevel.LOW
    
    def _get_strategy_strength(self, strategy_type: StrategyType) -> str:
        """What does this strategy excel at?"""
        strengths = {
            StrategyType.AGGRESSIVE: "Minimizes penalty risk and legal complications. Best for maintaining good vendor relationships.",
            StrategyType.BALANCED: "Optimizes both vendor relationships and operational survival. Most flexible approach.",
            StrategyType.CONSERVATIVE: "Maximizes cash preservation and business survival. Best if expecting further deterioration.",
        }
        return strengths.get(strategy_type, "")
    
    def _get_strategy_weakness(self, strategy_type: StrategyType) -> str:
        """Where does this strategy struggle?"""
        weaknesses = {
            StrategyType.AGGRESSIVE: "Depletes cash quickly. High risk if cash projections worsen. May not support ongoing operations.",
            StrategyType.BALANCED: "Higher penalty exposure than Aggressive. Lower survival margin than Conservative.",
            StrategyType.CONSERVATIVE: "Significant penalty accumulation. Risks vendor relationship deterioration and future credit restrictions.",
        }
        return weaknesses.get(strategy_type, "")
    
    def _get_best_for_description(self, strategy_type: StrategyType) -> str:
        """When is this strategy best?"""
        best_for = {
            StrategyType.AGGRESSIVE: "Best if cash flow is strong and penalties are very high (taxes, loans, payroll focus).",
            StrategyType.BALANCED: "Best in Base case scenario. Recommended for most situations as it balances competing priorities.",
            StrategyType.CONSERVATIVE: "Best if in Worst case or expecting severe cash constraints. Prioritizes staying in business.",
        }
        return best_for.get(strategy_type, "")
    
    def _can_make_partial_payment(self, obligation_data: Optional[Dict], category: str) -> bool:
        """Can this obligation accept partial payment?"""
        if not obligation_data:
            return category not in {"Tax", "Payroll", "Loan"}  # Estimate
        return obligation_data.get("partial_payment_allowed", True)
    
    def _get_penalty_accrual_description(self, category: str) -> str:
        """Human-readable penalty accrual description."""
        accrual_map = {
            "Tax": "5% daily accrual",
            "Payroll": "10% daily + legal liability",
            "Loan": "Interest + penalties",
            "Utilities": "Fixed late fee + escalation",
            "Insurance": "Policy cancellation risk",
            "Lease": "1-2% monthly + default risk",
            "Supplier": "Minimal or negotiable",
        }
        return accrual_map.get(category, "Varies by contract")
    
    def _get_vendor_relationship_description(self, vendor_data: Optional[Dict]) -> str:
        """Human-readable vendor relationship classification."""
        if not vendor_data:
            return "Established"
        
        years = vendor_data.get("years_with_business", 1)
        if years > 3:
            return "Core partner"
        elif years > 1:
            return "Established"
        else:
            return "New"
    
    def _estimate_penalty_for_delay(self, category: str, amount: float, delay_days: int) -> float:
        """Estimate penalty if payment delayed N days."""
        penalty_rates = {
            "Tax": 0.05 * delay_days,  # 5% daily
            "Payroll": 0.10 * delay_days,  # 10% daily
            "Loan": 0.02 * delay_days,  # 2% daily
            "Utilities": 50 + (10 * (delay_days // 7)),  # Flat $50 + escalation
            "Insurance": 35,  # Flat fee
            "Lease": 0.015 * delay_days,  # 1.5% daily
            "Supplier": 0.005 * delay_days,  # 0.5% daily (minimal)
        }
        
        rate = penalty_rates.get(category, 0.01 * delay_days)  # Default 1% daily
        return amount * rate if rate < 1 else rate  # Cap large percentages
    
    def _find_obligation_data(self, obligation_id: str, financial_state: FinancialState) -> Optional[Dict]:
        """Find obligation in FinancialState."""
        if not hasattr(financial_state, 'payables'):
            return None
        
        for payable in financial_state.payables:
            if payable.id == obligation_id or getattr(payable, 'obligation_id', None) == obligation_id:
                return {
                    "amount": payable.amount,
                    "due_date": payable.due_date,
                    "category": payable.category,
                    "partial_payment_allowed": True,  # Default assumption
                }
        
        return None
    
    def _find_vendor_data(self, vendor_id: str, financial_state: FinancialState) -> Optional[Dict]:
        """Find vendor data in FinancialState."""
        if not hasattr(financial_state, 'vendor_relationships'):
            return None
        
        for vendor in financial_state.vendor_relationships:
            if vendor.vendor_id == vendor_id:
                return {
                    "vendor_name": vendor.vendor_name,
                    "relationship_type": vendor.relationship_type,
                    "years_with_business": vendor.years_with_business,
                    "payment_reliability": vendor.payment_reliability,
                }
        
        return None
    
    def _identify_critical_vs_flexible(self, decisions: DecisionResult3Scenarios) -> Tuple[List[str], List[str]]:
        """Identify which obligations are always paid (critical) vs vary (flexible)."""
        # Count how many strategies pay each obligation in full
        payment_counts = {}
        total_strategies = 9
        
        for strategy in decisions.all_strategies:
            for decision in strategy.decisions:
                if decision.obligation_id not in payment_counts:
                    payment_counts[decision.obligation_id] = 0
                
                if decision.status == PaymentStatus.PAY_IN_FULL:
                    payment_counts[decision.obligation_id] += 1
        
        critical = [
            obs_id
            for obs_id, count in payment_counts.items()
            if count >= 8  # Paid in 8+ out of 9 strategies
        ]
        
        flexible = [
            obs_id
            for obs_id, count in payment_counts.items()
            if count >= 3 and count < 8  # Varies significantly
        ]
        
        return critical, flexible
    
    def _generate_cross_scenario_guidance(
        self,
        financial_state: FinancialState,
        risk_detection: RiskDetectionResult,
        decisions: DecisionResult3Scenarios,
    ) -> Tuple[str, str, str]:
        """
        Generate guidance on how to use all 3 scenarios.
        
        Returns: (summary, scenario_context, action_recommendation)
        """
        # BASE should be primary plan; WORST is contingency; BEST is upside
        summary = (
            "Plan for the BASE case (most likely scenario) as your primary approach. "
            "Prepare contingency plans for the WORST case. Monitor for upside (BEST case). "
            f"Survival probability: BASE {decisions.base_case.aggressive_strategy.survival_probability:.0f}%, "
            f"WORST {decisions.worst_case.aggressive_strategy.survival_probability:.0f}%."
        )
        
        context = (
            f"The BASE case represents the most likely cash flow projection. "
            f"The WORST case represents severe constraints; the BEST case represents favorable conditions. "
            f"Use BASE for operational planning, WORST for contingency readiness, BEST for upside scenarios."
        )
        
        action = (
            f"1. PRIMARY: Execute your BASE case {decisions.base_case.recommended_strategy.value} strategy. "
            f"2. CONTINGENCY: Prepare triggers to switch to WORST case {decisions.worst_case.recommended_strategy.value} strategy if cash drops below threshold. "
            f"3. UPSIDE: Define actions if conditions move toward BEST case (increased spending for growth)."
        )
        
        return summary, context, action
