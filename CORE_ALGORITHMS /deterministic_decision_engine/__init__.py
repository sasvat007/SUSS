"""
Deterministic Decision Engine (DDE)

Payment decision optimization engine for managing cash flow across multiple scenarios.

Generates 9 payment strategies (3 per RDE scenario: BEST/BASE/WORST) based on:
- Obligation priority scoring (legal, urgency, penalty, vendor relationship, flexibility)
- Available cash in each scenario
- Business constraints (minimum buffer, partial payment policy)
- Vendor relationship strategy (NEW/EXISTING/CORE classification)

Key Components:
- models: Data structures for decisions, strategies, penalties
- obligation_scorer: Weighted scoring (40% legal, 30% urgency, 20% penalty, 10% vendor)
- penalty_calculator: Category-specific penalty models
- payment_optimizer: 3 strategy generators (aggressive/balanced/conservative)
- strategy_evaluator: Ranking and recommendation selection
- decision_generator: Multi-scenario orchestration
- engine: Main public API (make_payment_decisions)

Public API:
-----------
from deterministic_decision_engine import make_payment_decisions, explain_payment_decisions

decisions = make_payment_decisions(
    financial_state=fse_output,
    risk_detection_result=rde_output,
    vendor_relationships=vendor_dict,
    risk_level="MODERATE",
)

# Access results
print(decisions.base_case.recommended_strategy)  # AGGRESSIVE/BALANCED/CONSERVATIVE
for decision in decisions.base_case.balanced_strategy.decisions:
    print(f"  {decision.obligation_id}: {decision.status.value} ${decision.pay_amount}")

# Generate explanation
explanation = explain_payment_decisions(decisions, scenario="BASE", strategy="RECOMMENDED")
print(explanation)

Version: 0.0.1
"""

# Public API - Main functions
from .engine import (
    make_payment_decisions,
    explain_payment_decisions,
)

# Data models
from .models import (
    # Enums
    VendorRelationshipType,
    StrategyType,
    ScenarioType,
    PaymentStatus,
    PenaltyType,
    # Data classes
    PenaltyModel,
    VendorRelationship,
    ObligationScore,
    PaymentDecision,
    PaymentStrategy,
    DecisionResult,
    DecisionResult3Scenarios,
)

# Scoring and optimization
from .obligation_scorer import (
    score_obligation,
    score_all_obligations,
)

from .penalty_calculator import (
    get_penalty_model,
    calculate_delay_penalty,
    estimate_penalty_for_obligation,
    get_all_penalty_models,
)

from .payment_optimizer import PaymentOptimizer

from .strategy_evaluator import StrategyEvaluator

# Utilities
from .utils import (
    format_currency,
    format_strategy_summary,
    format_decision_summary,
    format_scenario_results,
    export_decisions_to_dict,
    create_sample_vendor_relationships,
    calculate_total_obligations,
    get_penalty_config,
    days_until_date,
    validate_decision_result,
)

__version__ = "0.0.1"

__all__ = [
    # Main API
    "make_payment_decisions",
    "explain_payment_decisions",
    # Enums
    "VendorRelationshipType",
    "StrategyType",
    "ScenarioType",
    "PaymentStatus",
    "PenaltyType",
    # Models
    "PenaltyModel",
    "VendorRelationship",
    "ObligationScore",
    "PaymentDecision",
    "PaymentStrategy",
    "DecisionResult",
    "DecisionResult3Scenarios",
    # Scoring
    "score_obligation",
    "score_all_obligations",
    # Penalties
    "get_penalty_model",
    "calculate_delay_penalty",
    "estimate_penalty_for_obligation",
    "get_all_penalty_models",
    # Optimizer
    "PaymentOptimizer",
    # Evaluator
    "StrategyEvaluator",
    # Utilities
    "format_currency",
    "format_strategy_summary",
    "format_decision_summary",
    "format_scenario_results",
    "export_decisions_to_dict",
    "create_sample_vendor_relationships",
    "calculate_total_obligations",
    "get_penalty_config",
    "days_until_date",
    "validate_decision_result",
]
