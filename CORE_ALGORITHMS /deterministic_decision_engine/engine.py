"""
Deterministic Decision Engine (DDE) - Main Entry Point

Public API for generating payment decisions across 3 RDE scenarios.

Orchestrates:
1. Obligation scoring (priority computation)
2. Strategy generation (3 approaches per scenario)
3. Strategy evaluation and ranking
4. Recommendation selection

Returns complete DecisionResult3Scenarios with 9 payment plans and cross-scenario guidance.

Version: 0.0.1
"""

from typing import Dict, List, Optional
from datetime import datetime
from financial_state_engine.models import FinancialState, Payable
from risk_detection_engine.models import RiskDetectionResult
from .models import (
    DecisionResult3Scenarios,
    VendorRelationship,
    VendorRelationshipType,
)
from .decision_generator import generate_payment_decisions
from .obligation_scorer import _extract_vendor_id
from .explainability_engine import ExplainabilityEngine
from .explanation_models import CompleteExplanation


def make_payment_decisions(
    financial_state: FinancialState,
    risk_detection_result: RiskDetectionResult,
    payables: List[Payable],
    vendor_relationships: Optional[Dict[str, VendorRelationship]] = None,
    reference_date: Optional[datetime] = None,
    risk_level: str = "MODERATE",
) -> DecisionResult3Scenarios:
    """
    Generate optimal payment decisions across 3 RDE scenarios.
    
    This is the main public API for the Deterministic Decision Engine.
    
    Input Requirements:
    ------------------
    - financial_state: Output from FinancialStateEngine
      Must include: current_cash, business_context, payables list
      Each payable must have: id, amount, due_date, category, creditor_id, description
    
    - risk_detection_result: Output from RiskDetectionEngine
      Must include: best_case, base_case, worst_case (RiskProjection objects)
      Each projection must have: first_shortfall_date, timeline
    
    - vendor_relationships (optional): Dict mapping vendor_id → VendorRelationship
      If not provided, defaults to EXISTING classification for all vendors
      Best practice: populate from questionnaire or CRM data
    
    - reference_date (optional): Current date for calculations
      Defaults to datetime.now()
    
    - risk_level (optional): Business risk tolerance
      Options: "AGGRESSIVE" (pay more), "MODERATE" (balanced), "CONSERVATIVE" (survive)
      Defaults to "MODERATE"
    
    Algorithm:
    ----------
    For each RDE scenario (BEST, BASE, WORST):
      1. Score all obligations (0-100) using weighted formula:
         Score = Legal×40% + Urgency×30% + Penalty×20% + Vendor×10% - Flexibility×5%
         Where:
         - Legal: Tax/Loan/Payroll = 90-100, Utilities = 65, Supplier = 40
         - Urgency: Scales from 0 (far future) to 100 (today)
         - Penalty: Based on category's daily penalty rate
         - Vendor: NEW (< 1yr) = 85, EXISTING (1-3yr) = 50, CORE (> 3yr) = 25
         - Flexibility: 80 if partial payments allowed, else 20
      
      2. Generate 3 strategies (different spending profiles):
         - AGGRESSIVE: Spend 90% of available cash, pay high-priority items
         - BALANCED: Spend 70% of available cash, balance payment vs survival
         - CONSERVATIVE: Spend 40% of available cash, maximize survival (only critical)
      
      3. Evaluate strategies:
         - Compute penalty costs, survival probability, cash remaining
         - Rank by composite score (lower is better)
      
      4. Select recommended strategy based on risk_level
    
    Output:
    -------
    DecisionResult3Scenarios: Complete decision package
      - best_case: DecisionResult (3 strategies + recommendation)
      - base_case: DecisionResult (3 strategies + recommendation)
      - worst_case: DecisionResult (3 strategies + recommendation)
      - overall_recommendation: Cross-scenario guidance
    
    Each DecisionResult contains:
      - aggressive_strategy: PaymentStrategy with 3 strategy_type
      - balanced_strategy: PaymentStrategy with decision details
      - conservative_strategy: PaymentStrategy with recommendations
      - PaymentDecision for each obligation: Pay/Partial/Delay + rationale
    
    Examples:
    ---------
    # Basic usage (all defaults)
    decisions = make_payment_decisions(fse_output, rde_output)
    
    # With vendor relationships from questionnaire
    vendor_rels = {
        "acme_corp": VendorRelationship(
            vendor_id="acme_corp",
            vendor_name="ACME Corporation",
            relationship_type=VendorRelationshipType.CORE,
            years_with_business=5.0,
            payment_reliability=95.0,
        ),
    }
    decisions = make_payment_decisions(fse_output, rde_output, vendor_relationships=vendor_rels)
    
    # Conservative approach (maximize survival)
    decisions = make_payment_decisions(fse_output, rde_output, risk_level="CONSERVATIVE")
    
    # Access results
    print(f"BASE case recommended: {decisions.base_case.recommended_strategy}")
    for decision in decisions.base_case.balanced_strategy.decisions:
        print(f"  {decision.obligation_id}: {decision.status.value} ${decision.pay_amount}")
    
    Returns:
        DecisionResult3Scenarios with 9 payment strategies (3 per scenario)
    
    Raises:
        ValueError: If financial_state or risk_detection_result invalid/incomplete
        TypeError: If vendor_relationships format incorrect
    """
    # Validate inputs
    if not financial_state:
        raise ValueError("financial_state is required")
    if not risk_detection_result:
        raise ValueError("risk_detection_result is required")
    if not payables:
        raise ValueError("payables is empty")
    if financial_state.current_balance is None:
        raise ValueError("financial_state.current_balance is required")
    
    # Validate risk_level
    valid_risk_levels = {"AGGRESSIVE", "MODERATE", "CONSERVATIVE"}
    if risk_level not in valid_risk_levels:
        raise ValueError(
            f"risk_level must be one of {valid_risk_levels}, got '{risk_level}'"
        )
    
    # Default vendor relationships if not provided
    if vendor_relationships is None:
        vendor_relationships = {}
        # Populate defaults for any vendors not provided
        for payable in payables:
            vendor_id = _extract_vendor_id(payable)
            if vendor_id not in vendor_relationships:
                vendor_relationships[vendor_id] = VendorRelationship(
                    vendor_id=vendor_id,
                    vendor_name=payable.description,
                    relationship_type=VendorRelationshipType.EXISTING,  # Default classification
                    years_with_business=2.0,  # Default 2 years
                    payment_reliability=50.0,  # Default 50%
                )
    
    # Default reference_date if not provided
    if reference_date is None:
        reference_date = datetime.now()
    
    # Generate decisions
    return generate_payment_decisions(
        financial_state=financial_state,
        risk_detection_result=risk_detection_result,
        payables=payables,
        vendor_relationships=vendor_relationships,
        reference_date=reference_date,
        risk_level=risk_level,
    )


def explain_payment_decisions(
    decisions: DecisionResult3Scenarios,
    scenario: str = "BASE",
    strategy: str = "RECOMMENDED",
) -> str:
    """
    Generate human-readable explanation of payment decisions.
    
    Args:
        decisions: DecisionResult3Scenarios from make_payment_decisions()
        scenario: "BEST", "BASE", or "WORST"
        strategy: "RECOMMENDED", "AGGRESSIVE", "BALANCED", or "CONSERVATIVE"
    
    Returns:
        Multi-line explanation text
    """
    if scenario.upper() == "BEST":
        result = decisions.best_case
    elif scenario.upper() == "WORST":
        result = decisions.worst_case
    else:
        result = decisions.base_case
    
    scenario_name = scenario.upper()
    
    if strategy.upper() == "RECOMMENDED":
        strategy_name = result.recommended_strategy.value
        strat = getattr(result, f"{strategy_name.lower()}_strategy")
        rec_note = " (RECOMMENDED)"
    else:
        strategy_name = strategy.upper()
        strat = getattr(result, f"{strategy_name.lower()}_strategy")
        rec_note = ""
    
    lines = []
    lines.append(f"=== {scenario_name} Case Payment Plan ({strategy_name}){rec_note} ===\n")
    lines.append(f"Cash Available: ${result.cash_available:,.2f}")
    lines.append(f"Total Payment: ${strat.total_payment:,.2f}")
    lines.append(f"Penalties: ${strat.total_penalty_cost:,.2f}")
    lines.append(f"Cash After: ${strat.estimated_cash_after:,.2f}")
    lines.append(f"Survival Probability: {strat.survival_probability:.1f}%")
    lines.append("")
    
    lines.append("Payment Decisions:")
    for i, decision in enumerate(strat.decisions, start=1):
        lines.append(f"  {i}. {decision.vendor_name} ({decision.obligation_id})")
        lines.append(f"     Amount: ${decision.pay_amount:,.2f} (of ${decision.original_amount:,.2f})")
        lines.append(f"     Status: {decision.status.value}")
        if decision.delay_days > 0:
            lines.append(f"     Delay: {decision.delay_days} days")
        if decision.potential_penalty > 0:
            lines.append(f"     Penalty Cost: ${decision.potential_penalty:,.2f}")
        lines.append(f"     Reason: {decision.rationale}")
        lines.append("")
    
    return "\n".join(lines)


def make_payment_decisions_with_explanations(
    financial_state: FinancialState,
    risk_detection_result: RiskDetectionResult,
    payables: List[Payable],
    vendor_relationships: Optional[Dict[str, VendorRelationship]] = None,
    reference_date: Optional[datetime] = None,
    risk_level: str = "MODERATE",
    enable_llm_refinement: bool = False,
) -> DecisionResult3Scenarios:
    """
    Generate payment decisions AND complete explanations for all 9 strategies.
    
    This is the recommended API when you need full transparency and explanations.
    It calls make_payment_decisions() and then generates a CompleteExplanation.
    
    Args:
        financial_state: FinancialState from FinancialStateEngine
        risk_detection_result: RiskDetectionResult from RiskDetectionEngine
        payables: List of obligations to evaluate
        vendor_relationships: Optional vendor relationship data
        reference_date: Current date (defaults to now)
        risk_level: "AGGRESSIVE", "MODERATE", or "CONSERVATIVE"
        enable_llm_refinement: Optionally refine explanation text via LLM for readability.
                               When False (default), uses deterministic templates only.
    
    Returns:
        DecisionResult3Scenarios with populated explanation field
    
    Raises:
        ValueError: If inputs are invalid
        RuntimeError: If explanation generation fails
    
    Examples:
        # Generate decisions with full explanations
        decisions = make_payment_decisions_with_explanations(fse_output, rde_output, payables)
        
        # Access all 9 strategy explanations
        for scenario in ["best", "base", "worst"]:
            for strategy in ["aggressive", "balanced", "conservative"]:
                explanation = decisions.explanation.get_strategy_explanation(scenario, strategy)
                print(f"{scenario.upper()} {strategy.upper()}: {explanation.summary}")
        
        # Access recommendations
        print(f"Base case recommended: {decisions.explanation.recommended_base_case}")
        print(f"Overall: {decisions.explanation.action_recommendation}")
    """
    # First, generate decisions
    decisions = make_payment_decisions(
        financial_state=financial_state,
        risk_detection_result=risk_detection_result,
        payables=payables,
        vendor_relationships=vendor_relationships,
        reference_date=reference_date,
        risk_level=risk_level,
    )
    
    # Then, generate complete explanations
    try:
        engine = ExplainabilityEngine(enable_llm_refinement=enable_llm_refinement)
        explanation = engine.generate_complete_explanation(
            decisions=decisions,
            financial_state=financial_state,
            risk_detection=risk_detection_result,
        )
        
        # Attach explanation to decisions
        decisions.explanation = explanation
        
    except Exception as e:
        raise RuntimeError(f"Failed to generate explanations: {str(e)}") from e
    
    return decisions
