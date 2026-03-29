"""
Payment Optimizer for DDE

Generates 3 payment strategies (AGGRESSIVE/BALANCED/CONSERVATIVE) for a given scenario.

Each strategy makes decisions for every obligation considering:
- Available cash in the scenario
- Obligation priority scores
- Penalty models
- Minimum cash buffer requirement

Strategies differ in optimization goals:
- AGGRESSIVE: Maximize payment, minimize penalty risk (pay what we can)
- BALANCED: Optimize between paying obligations and maintaining cash buffer
- CONSERVATIVE: Minimize spending to ensure survival (only pay critical items)

Version: 0.0.1
"""

from typing import List, Tuple, Dict
from datetime import datetime
from financial_state_engine.models import Payable, BusinessContext
from .models import (
    ObligationScore,
    PaymentDecision,
    PaymentStrategy,
    PaymentStatus,
    StrategyType,
    ScenarioType,
)
from .penalty_calculator import get_penalty_model, calculate_delay_penalty
from .obligation_scorer import _extract_vendor_id
from .obligation_scorer import _extract_vendor_id


class PaymentOptimizer:
    """Generates payment strategies for a cash scenario."""
    
    def __init__(
        self,
        payables: List[Payable],
        obligation_scores: List[ObligationScore],
        business_context: BusinessContext,
        available_cash: float,
        scenario_type: ScenarioType,
        reference_date: datetime,
    ):
        """
        Initialize optimizer for a scenario.
        
        Args:
            payables: All obligations to consider
            obligation_scores: Pre-computed priority scores
            business_context: Business constraints (min buffer, partial payments)
            available_cash: Cash available in this scenario
            scenario_type: RDE scenario (BEST/BASE/WORST)
            reference_date: Current date (for penalty calculations)
        """
        self.payables = payables
        self.scores = obligation_scores
        self.context = business_context
        self.cash = available_cash
        self.scenario = scenario_type
        self.reference_date = reference_date
        
        # Cache payables by ID for lookup
        self.payables_by_id = {p.id: p for p in payables}
    
    def generate_all_strategies(self) -> Tuple[PaymentStrategy, PaymentStrategy, PaymentStrategy]:
        """
        Generate 3 strategies for this scenario.
        
        Returns:
            Tuple of (aggressive_strategy, balanced_strategy, conservative_strategy)
        """
        aggressive = self._generate_aggressive_strategy()
        balanced = self._generate_balanced_strategy()
        conservative = self._generate_conservative_strategy()
        
        return aggressive, balanced, conservative
    
    def _generate_aggressive_strategy(self) -> PaymentStrategy:
        """
        AGGRESSIVE: Pay as much as possible within available cash.
        
        Algorithm:
        1. Use high spending allocation (~90% of available cash)
        2. Sort obligations by priority score (highest first)
        3. Pay in full where possible, skip lowest-priority items if needed
        4. Only delay if absolutely must to stay above minimum buffer
        
        Returns:
            PaymentStrategy with aggressive payment decisions
        """
        # Can spend up to 90% of available cash, keep 10% buffer
        spending_target = self.cash * 0.90
        min_buffer = self.context.min_cash_buffer
        
        decisions = []
        total_spent = 0.0
        
        # Sort by priority (highest first)
        sorted_scores = sorted(
            self.scores,
            key=lambda s: s.total_weighted_score,
            reverse=True,
        )
        
        for score in sorted_scores:
            payable = self.payables_by_id.get(score.obligation_id)
            if not payable:
                continue
            
            remaining_budget = spending_target - total_spent
            
            if remaining_budget <= 0:
                # Out of budget: must delay
                decision = PaymentDecision(
                    obligation_id=payable.id,
                    status=PaymentStatus.DELAY,
                    pay_amount=0.0,
                    delay_days=30,  # Default 30-day delay
                    potential_penalty=calculate_delay_penalty(
                        payable.amount, 30, get_penalty_model(payable.category)
                    ),
                    rationale=f"Aggressive: Budget exhausted; deferring {payable.description}",
                    vendor_id=_extract_vendor_id(payable),
                    vendor_name=payable.description,
                    due_date=payable.due_date,
                    category=payable.category,
                )
            elif payable.amount <= remaining_budget:
                # Can pay in full
                decision = PaymentDecision(
                    obligation_id=payable.id,
                    status=PaymentStatus.PAY_IN_FULL,
                    pay_amount=payable.amount,
                    delay_days=0,
                    potential_penalty=0.0,
                    rationale=f"Aggressive: Paying in full (high priority: {score.priority_rank})",
                    vendor_id=_extract_vendor_id(payable),
                    vendor_name=payable.description,
                    due_date=payable.due_date,
                    category=payable.category,
                )
                total_spent += payable.amount
            else:
                # Can only partially pay or must delay
                if self.context.allow_partial_payments:
                    pay_amount = remaining_budget
                    decision = PaymentDecision(
                        obligation_id=payable.id,
                        status=PaymentStatus.PARTIAL_PAY,
                        pay_amount=pay_amount,
                        delay_days=0,
                        potential_penalty=0.0,
                        rationale=f"Aggressive: Partial payment (${pay_amount:.2f} of ${payable.amount:.2f})",
                        vendor_id=_extract_vendor_id(payable),
                        vendor_name=payable.description,
                        due_date=payable.due_date,
                        category=payable.category,
                    )
                    total_spent += pay_amount
                else:
                    # Can't partial pay: skip this and lower priority items
                    decision = PaymentDecision(
                        obligation_id=payable.id,
                        status=PaymentStatus.DELAY,
                        pay_amount=0.0,
                        delay_days=15,
                        potential_penalty=calculate_delay_penalty(
                            payable.amount, 15, get_penalty_model(payable.category)
                        ),
                        rationale="Aggressive: Insufficient budget and partial pay not allowed",
                        vendor_id=_extract_vendor_id(payable),
                        vendor_name=payable.description,
                        due_date=payable.due_date,
                        category=payable.category,
                    )
            
            decisions.append(decision)
        
        # Calculate metrics
        total_payment = sum(d.pay_amount for d in decisions)
        total_penalties = sum(d.potential_penalty for d in decisions)
        cash_after = self.cash - total_payment
        survival = 100.0 if cash_after >= min_buffer else 0.0
        
        return PaymentStrategy(
            strategy_type=StrategyType.AGGRESSIVE,
            scenario_type=self.scenario,
            decisions=decisions,
            total_payment=total_payment,
            total_penalty_cost=total_penalties,
            estimated_cash_after=cash_after,
            survival_probability=survival,
            score=self._compute_strategy_score(total_penalties, survival),
            metadata={"spending_target": spending_target, "decisions_count": len(decisions)},
        )
    
    def _generate_balanced_strategy(self) -> PaymentStrategy:
        """
        BALANCED: Optimize between paying obligations and maintaining survival cash.
        
        Algorithm:
        1. Use moderate spending allocation (~70% of available cash, keep 30% buffer)
        2. Sort by priority, pay critical items (score > 50) in full
        3. For lower-priority items: decide case-by-case
        4. Goal: Minimize risk while maintaining operational cash
        
        Returns:
            PaymentStrategy with balanced payment decisions
        """
        # Can spend up to 70% of available cash, keep 30% safe
        spending_target = self.cash * 0.70
        min_buffer = self.context.min_cash_buffer
        
        decisions = []
        total_spent = 0.0
        
        # Sort by priority
        sorted_scores = sorted(
            self.scores,
            key=lambda s: s.total_weighted_score,
            reverse=True,
        )
        
        for score in sorted_scores:
            payable = self.payables_by_id.get(score.obligation_id)
            if not payable:
                continue
            
            remaining_budget = spending_target - total_spent
            is_critical = score.total_weighted_score > 50  # Critical threshold
            
            if remaining_budget <= 0:
                # Out of budget
                if is_critical:
                    # Critical items: pay anyway (adjust buffer)
                    decision = PaymentDecision(
                        obligation_id=payable.id,
                        status=PaymentStatus.PAY_IN_FULL,
                        pay_amount=payable.amount,
                        delay_days=0,
                        potential_penalty=0.0,
                        rationale=f"Balanced: Critical item (score {score.total_weighted_score:.1f}) paid despite budget",
                        vendor_id=_extract_vendor_id(payable),
                        vendor_name=payable.description,
                        due_date=payable.due_date,
                        category=payable.category,
                    )
                    total_spent += payable.amount
                else:
                    # Non-critical: delay
                    penalty_model = get_penalty_model(payable.category)
                    delay = 20  # Moderate delay for non-critical
                    decision = PaymentDecision(
                        obligation_id=payable.id,
                        status=PaymentStatus.DELAY,
                        pay_amount=0.0,
                        delay_days=delay,
                        potential_penalty=calculate_delay_penalty(
                            payable.amount, delay, penalty_model
                        ),
                        rationale=f"Balanced: Non-critical (score {score.total_weighted_score:.1f}); delaying {delay} days",
                        vendor_id=_extract_vendor_id(payable),
                        vendor_name=payable.description,
                        due_date=payable.due_date,
                        category=payable.category,
                    )
            elif payable.amount <= remaining_budget:
                # Pay in full
                decision = PaymentDecision(
                    obligation_id=payable.id,
                    status=PaymentStatus.PAY_IN_FULL,
                    pay_amount=payable.amount,
                    delay_days=0,
                    potential_penalty=0.0,
                    rationale=f"Balanced: Paying in full (priority {score.priority_rank})",
                    vendor_id=_extract_vendor_id(payable),
                    vendor_name=payable.description,
                    due_date=payable.due_date,
                    category=payable.category,
                )
                total_spent += payable.amount
            else:
                # Partial budget available
                if is_critical:
                    # Pay what we can for critical
                    if self.context.allow_partial_payments:
                        pay_amount = remaining_budget
                        decision = PaymentDecision(
                            obligation_id=payable.id,
                            status=PaymentStatus.PARTIAL_PAY,
                            pay_amount=pay_amount,
                            delay_days=0,
                            potential_penalty=0.0,
                            rationale=f"Balanced: Critical item partial pay (${pay_amount:.2f})",
                            vendor_id=_extract_vendor_id(payable),
                            vendor_name=payable.description,
                            due_date=payable.due_date,
                            category=payable.category,
                        )
                        total_spent += pay_amount
                    else:
                        # Can't partial: pay in full anyway (critical)
                        decision = PaymentDecision(
                            obligation_id=payable.id,
                            status=PaymentStatus.PAY_IN_FULL,
                            pay_amount=payable.amount,
                            delay_days=0,
                            potential_penalty=0.0,
                            rationale="Balanced: Critical item; paying in full despite budget",
                            vendor_id=_extract_vendor_id(payable),
                            vendor_name=payable.description,
                            due_date=payable.due_date,
                            category=payable.category,
                        )
                        total_spent += payable.amount
                else:
                    # Non-critical: delay instead
                    delay = 25
                    decision = PaymentDecision(
                        obligation_id=payable.id,
                        status=PaymentStatus.DELAY,
                        pay_amount=0.0,
                        delay_days=delay,
                        potential_penalty=calculate_delay_penalty(
                            payable.amount, delay, get_penalty_model(payable.category)
                        ),
                        rationale=f"Balanced: Non-critical; delaying {delay} days to preserve cash",
                        vendor_id=_extract_vendor_id(payable),
                        vendor_name=payable.description,
                        due_date=payable.due_date,
                        category=payable.category,
                    )
            
            decisions.append(decision)
        
        total_payment = sum(d.pay_amount for d in decisions)
        total_penalties = sum(d.potential_penalty for d in decisions)
        cash_after = self.cash - total_payment
        survival = 100.0 if cash_after >= min_buffer else 50.0 if cash_after > 0 else 0.0
        
        return PaymentStrategy(
            strategy_type=StrategyType.BALANCED,
            scenario_type=self.scenario,
            decisions=decisions,
            total_payment=total_payment,
            total_penalty_cost=total_penalties,
            estimated_cash_after=cash_after,
            survival_probability=survival,
            score=self._compute_strategy_score(total_penalties, survival),
            metadata={"spending_target": spending_target, "critical_threshold": 50},
        )
    
    def _generate_conservative_strategy(self) -> PaymentStrategy:
        """
        CONSERVATIVE: Minimize spending to ensure survival.
        
        Algorithm:
        1. Use low spending allocation (~40% of available cash, keep 60% safe)
        2. Only pay items with score > 70 (critical only)
        3. For everything else: delay as long as acceptable
        4. Goal: Maximize survival probability at all costs
        
        Returns:
            PaymentStrategy with conservative payment decisions
        """
        # Can spend up to 40% of available cash, keep 60% safe
        spending_target = self.cash * 0.40
        min_buffer = self.context.min_cash_buffer
        
        decisions = []
        total_spent = 0.0
        
        # Sort by priority
        sorted_scores = sorted(
            self.scores,
            key=lambda s: s.total_weighted_score,
            reverse=True,
        )
        
        for score in sorted_scores:
            payable = self.payables_by_id.get(score.obligation_id)
            if not payable:
                continue
            
            remaining_budget = spending_target - total_spent
            is_critical = score.total_weighted_score > 70  # High threshold for conservative
            
            if is_critical:
                # Must pay critical items
                if payable.amount <= remaining_budget:
                    decision = PaymentDecision(
                        obligation_id=payable.id,
                        status=PaymentStatus.PAY_IN_FULL,
                        pay_amount=payable.amount,
                        delay_days=0,
                        potential_penalty=0.0,
                        rationale=f"Conservative: Must pay critical item (score {score.total_weighted_score:.1f})",
                        vendor_id=_extract_vendor_id(payable),
                        vendor_name=payable.description,
                        due_date=payable.due_date,
                        category=payable.category,
                    )
                    total_spent += payable.amount
                else:
                    # Budget constraint: partial pay if allowed
                    if self.context.allow_partial_payments and remaining_budget > 0:
                        pay_amount = remaining_budget
                        decision = PaymentDecision(
                            obligation_id=payable.id,
                            status=PaymentStatus.PARTIAL_PAY,
                            pay_amount=pay_amount,
                            delay_days=0,
                            potential_penalty=0.0,
                            rationale=f"Conservative: Critical partial (${pay_amount:.2f})",
                            vendor_id=_extract_vendor_id(payable),
                            vendor_name=payable.description,
                            due_date=payable.due_date,
                            category=payable.category,
                        )
                        total_spent += pay_amount
                    else:
                        # Can't pay more: delay critical item
                        decision = PaymentDecision(
                            obligation_id=payable.id,
                            status=PaymentStatus.STRATEGIC_DEFAULT,
                            pay_amount=0.0,
                            delay_days=45,
                            potential_penalty=calculate_delay_penalty(
                                payable.amount, 45, get_penalty_model(payable.category)
                            ),
                            rationale="Conservative: Critical item deferred to ensure survival",
                            vendor_id=_extract_vendor_id(payable),
                            vendor_name=payable.description,
                            due_date=payable.due_date,
                            category=payable.category,
                        )
            else:
                # Non-critical: aggressive delay
                delay = 60  # 2 months
                penalty_model = get_penalty_model(payable.category)
                decision = PaymentDecision(
                    obligation_id=payable.id,
                    status=PaymentStatus.STRATEGIC_DEFAULT,
                    pay_amount=0.0,
                    delay_days=delay,
                    potential_penalty=calculate_delay_penalty(
                        payable.amount, delay, penalty_model
                    ),
                    rationale=f"Conservative: Deferring for {delay} days to preserve cash (score {score.total_weighted_score:.1f})",
                    vendor_id=_extract_vendor_id(payable),
                    vendor_name=payable.description,
                    due_date=payable.due_date,
                    category=payable.category,
                )
            
            decisions.append(decision)
        
        total_payment = sum(d.pay_amount for d in decisions)
        total_penalties = sum(d.potential_penalty for d in decisions)
        cash_after = self.cash - total_payment
        survival = 100.0 if cash_after >= min_buffer else 75.0 if cash_after > 0 else 50.0
        
        return PaymentStrategy(
            strategy_type=StrategyType.CONSERVATIVE,
            scenario_type=self.scenario,
            decisions=decisions,
            total_payment=total_payment,
            total_penalty_cost=total_penalties,
            estimated_cash_after=cash_after,
            survival_probability=survival,
            score=self._compute_strategy_score(total_penalties, survival),
            metadata={"spending_target": spending_target, "critical_threshold": 70},
        )
    
    @staticmethod
    def _compute_strategy_score(total_penalties: float, survival: float) -> float:
        """
        Compute overall score for strategy ranking.
        
        Lower score is better.
        Formula: total_penalties + (100 - survival_probability) × 0.5
        
        Balances penalty cost against survival risk.
        
        Args:
            total_penalties: Sum of all penalty costs
            survival: Survival probability (0-100)
        
        Returns:
            Strategy score (lower is better)
        """
        survival_risk = (100.0 - survival) * 0.5
        return total_penalties + survival_risk
