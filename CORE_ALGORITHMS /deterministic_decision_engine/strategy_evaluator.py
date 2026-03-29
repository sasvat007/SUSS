"""
Strategy Evaluator for DDE

Analyzes and ranks payment strategies based on multiple dimensions:
- Penalty cost (lower is better)
- Survival probability (higher is better)
- Payment coverage (% of obligations paid)
- Vendor impact (relationship preservation)
- Risk profile (legal/financial exposure)

Recommends best strategy for each scenario.

Version: 0.0.1
"""

from typing import List, Tuple, Dict
from .models import (
    PaymentStrategy,
    StrategyType,
    PaymentStatus,
    DecisionResult,
    ScenarioType,
)


class StrategyEvaluator:
    """Analyzes and ranks payment strategies."""
    
    @staticmethod
    def evaluate_strategy(
        strategy: PaymentStrategy,
        total_obligations: int,
        total_obligation_amount: float,
    ) -> Dict[str, float]:
        """
        Compute evaluation metrics for a strategy.
        
        Metrics:
        - payment_coverage: % of obligations with non-zero payment
        - amount_coverage: % of total amount paid
        - penalty_rate: Penalties as % of obligations
        - survival_score: Weighted survival probability
        - overall_score: Composite ranking score
        
        Args:
            strategy: PaymentStrategy to evaluate
            total_obligations: Total number of obligations
            total_obligation_amount: Sum of all obligation amounts
        
        Returns:
            Dict of metric_name → value
        """
        # Coverage metrics
        paid_obligations = sum(
            1 for d in strategy.decisions if d.pay_amount > 0
        )
        payment_coverage = (paid_obligations / total_obligations * 100.0) if total_obligations > 0 else 0.0
        
        amount_coverage = (
            (strategy.total_payment / total_obligation_amount * 100.0)
            if total_obligation_amount > 0
            else 0.0
        )
        
        # Penalty metrics
        penalty_rate = (
            (strategy.total_penalty_cost / strategy.total_payment * 100.0)
            if strategy.total_payment > 0
            else 0.0
        )
        
        # Strategic metrics
        fully_paid = sum(1 for d in strategy.decisions if d.status == PaymentStatus.PAY_IN_FULL)
        partially_paid = sum(1 for d in strategy.decisions if d.status == PaymentStatus.PARTIAL_PAY)
        delayed = sum(1 for d in strategy.decisions if d.status in (PaymentStatus.DELAY, PaymentStatus.STRATEGIC_DEFAULT))
        
        # Survival score (already 0-100)
        survival_score = strategy.survival_probability
        
        # Overall composite score
        # Lower penalty rate is better, higher survival is better, higher coverage is better
        composite_score = StrategyEvaluator._compute_composite_score(
            penalty_rate, survival_score, amount_coverage
        )
        
        return {
            "payment_coverage": payment_coverage,  # % obligations paid
            "amount_coverage": amount_coverage,  # % amount paid
            "penalty_rate": penalty_rate,  # Penalties as % of payment
            "fully_paid_count": fully_paid,
            "partially_paid_count": partially_paid,
            "delayed_count": delayed,
            "survival_score": survival_score,
            "total_penalty_cost": strategy.total_penalty_cost,
            "total_payment": strategy.total_payment,
            "cash_after": strategy.estimated_cash_after,
            "composite_score": composite_score,  # Lower is better
        }
    
    @staticmethod
    def rank_strategies(
        aggressive: PaymentStrategy,
        balanced: PaymentStrategy,
        conservative: PaymentStrategy,
        total_obligations: int,
        total_obligation_amount: float,
    ) -> Tuple[List[PaymentStrategy], List[Dict]]:
        """
        Evaluate and rank 3 strategies.
        
        Args:
            aggressive: AGGRESSIVE strategy
            balanced: BALANCED strategy
            conservative: CONSERVATIVE strategy
            total_obligations: Total obligations count
            total_obligation_amount: Total obligations amount
        
        Returns:
            Tuple of (ranked_strategies_list, metrics_list)
            Where ranked_strategies_list[0] is recommended (best)
        """
        strategies = [aggressive, balanced, conservative]
        
        metrics_list = []
        for strategy in strategies:
            metrics = StrategyEvaluator.evaluate_strategy(
                strategy, total_obligations, total_obligation_amount
            )
            metrics_list.append(metrics)
        
        # Rank by composite score (lower is better)
        ranked = sorted(
            zip(strategies, metrics_list),
            key=lambda x: x[1]["composite_score"],
        )
        
        ranked_strategies = [s for s, _ in ranked]
        ranked_metrics = [m for _, m in ranked]
        
        return ranked_strategies, ranked_metrics
    
    @staticmethod
    def select_recommended_strategy(
        aggressive: PaymentStrategy,
        balanced: PaymentStrategy,
        conservative: PaymentStrategy,
        total_obligations: int,
        total_obligation_amount: float,
        risk_level: str = "MODERATE",  # AGGRESSIVE, MODERATE, CONSERVATIVE
    ) -> Tuple[StrategyType, str]:
        """
        Select recommended strategy based on risk preference.
        
        Args:
            aggressive: AGGRESSIVE strategy
            balanced: BALANCED strategy
            conservative: CONSERVATIVE strategy
            total_obligations: Total obligations count
            total_obligation_amount: Total obligations amount
            risk_level: Business risk tolerance (AGGRESSIVE/MODERATE/CONSERVATIVE)
        
        Returns:
            Tuple of (recommended_strategy_type, reasoning)
        """
        ranked, metrics = StrategyEvaluator.rank_strategies(
            aggressive, balanced, conservative, total_obligations, total_obligation_amount
        )
        
        ranked_types = [s.strategy_type for s in ranked]
        
        # Select based on risk preference
        if risk_level == "AGGRESSIVE":
            # Prefer aggressive (pay more, penalties okay)
            rec_type = ranked_types[0]  # Best overall
            reasoning = f"Business risk tolerance: AGGRESSIVE. Recommending {rec_type.value} approach (rank 1 of 3)."
        elif risk_level == "CONSERVATIVE":
            # Prefer conservative (survival paramount)
            rec_type = StrategyType.CONSERVATIVE
            reasoning = "Business risk tolerance: CONSERVATIVE. Recommending CONSERVATIVE approach (survival priority)."
        else:
            # MODERATE: default to balanced if available, else best ranked
            if StrategyType.BALANCED in ranked_types:
                rec_type = StrategyType.BALANCED
                reasoning = "Business risk tolerance: MODERATE. Recommending BALANCED approach (optimize payment vs survival)."
            else:
                rec_type = ranked_types[0]
                reasoning = f"Business risk tolerance: MODERATE. Recommending {rec_type.value} (BALANCED not optimal)."
        
        return rec_type, reasoning
    
    @staticmethod
    def create_scenario_result(
        scenario_type: ScenarioType,
        aggressive: PaymentStrategy,
        balanced: PaymentStrategy,
        conservative: PaymentStrategy,
        total_obligations: int,
        total_obligation_amount: float,
        risk_level: str = "MODERATE",
        cash_available: float = 0.0,
    ) -> DecisionResult:
        """
        Create DecisionResult for a scenario.
        
        Args:
            scenario_type: BEST/BASE/WORST
            aggressive: AGGRESSIVE strategy
            balanced: BALANCED strategy
            conservative: CONSERVATIVE strategy
            total_obligations: Count of obligations
            total_obligation_amount: Sum of obligations
            risk_level: Business risk tolerance
            cash_available: Available cash in scenario
        
        Returns:
            DecisionResult with all strategies and recommendation
        """
        rec_type, reasoning = StrategyEvaluator.select_recommended_strategy(
            aggressive, balanced, conservative,
            total_obligations, total_obligation_amount,
            risk_level
        )
        
        return DecisionResult(
            scenario_type=scenario_type,
            aggressive_strategy=aggressive,
            balanced_strategy=balanced,
            conservative_strategy=conservative,
            recommended_strategy=rec_type,
            reasoning=reasoning,
            cash_available=cash_available,
        )
    
    @staticmethod
    def _compute_composite_score(
        penalty_rate: float,
        survival_score: float,
        amount_coverage: float,
    ) -> float:
        """
        Compute composite score for strategy ranking.
        
        Lower score is better.
        
        Balances:
        - Penalty avoidance (minimize penalty_rate)
        - Survival (maximize survival_score)
        - Payment coverage (maximize amount_coverage)
        
        Formula:
        score = penalty_rate + (100 - survival_score) × 0.5 - amount_coverage × 0.25
        
        Args:
            penalty_rate: Penalties as % of payment (0-100+)
            survival_score: Survival probability (0-100)
            amount_coverage: % of amount paid (0-100)
        
        Returns:
            Composite score (lower is better)
        """
        survival_risk = (100.0 - survival_score) * 0.5
        coverage_bonus = amount_coverage * 0.25
        
        score = penalty_rate + survival_risk - coverage_bonus
        return max(-100.0, score)  # Floor at -100
    
    @staticmethod
    def analyze_strategy_tradeoffs(
        aggressive: PaymentStrategy,
        balanced: PaymentStrategy,
        conservative: PaymentStrategy,
    ) -> str:
        """
        Generate human-readable analysis of strategy tradeoffs.
        
        Args:
            aggressive: AGGRESSIVE strategy
            balanced: BALANCED strategy
            conservative: CONSERVATIVE strategy
        
        Returns:
            Multi-line analysis text
        """
        lines = []
        lines.append("=== Payment Strategy Tradeoff Analysis ===\n")
        
        lines.append(f"AGGRESSIVE Strategy:")
        lines.append(f"  Payment: ${aggressive.total_payment:,.2f}")
        lines.append(f"  Penalties: ${aggressive.total_penalty_cost:,.2f}")
        lines.append(f"  Survival: {aggressive.survival_probability:.1f}%")
        lines.append(f"  Cash After: ${aggressive.estimated_cash_after:,.2f}")
        lines.append("")
        
        lines.append(f"BALANCED Strategy:")
        lines.append(f"  Payment: ${balanced.total_payment:,.2f}")
        lines.append(f"  Penalties: ${balanced.total_penalty_cost:,.2f}")
        lines.append(f"  Survival: {balanced.survival_probability:.1f}%")
        lines.append(f"  Cash After: ${balanced.estimated_cash_after:,.2f}")
        lines.append("")
        
        lines.append(f"CONSERVATIVE Strategy:")
        lines.append(f"  Payment: ${conservative.total_payment:,.2f}")
        lines.append(f"  Penalties: ${conservative.total_penalty_cost:,.2f}")
        lines.append(f"  Survival: {conservative.survival_probability:.1f}%")
        lines.append(f"  Cash After: ${conservative.estimated_cash_after:,.2f}")
        lines.append("")
        
        # Key tradeoffs
        lines.append("Key Tradeoffs:")
        pay_diff = aggressive.total_payment - conservative.total_payment
        penalty_diff = aggressive.total_penalty_cost - conservative.total_penalty_cost
        
        if pay_diff > 0:
            lines.append(f"  Aggressive pays ${abs(pay_diff):,.2f} MORE than Conservative")
        else:
            lines.append(f"  Aggressive pays ${abs(pay_diff):,.2f} LESS than Conservative")
        
        if penalty_diff > 0:
            lines.append(f"  Aggressive incurs ${abs(penalty_diff):,.2f} MORE in penalties")
        else:
            lines.append(f"  Aggressive incurs ${abs(penalty_diff):,.2f} LESS in penalties")
        
        survival_diff = aggressive.survival_probability - conservative.survival_probability
        if survival_diff > 0:
            lines.append(f"  Aggressive has {survival_diff:.1f}% HIGHER survival risk")
        else:
            lines.append(f"  Aggressive has {abs(survival_diff):.1f}% LOWER survival risk")
        
        return "\n".join(lines)
