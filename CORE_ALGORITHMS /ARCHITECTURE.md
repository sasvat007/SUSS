# CapitalSense - Complete Financial Modeling System

A deterministic, three-engine financial decision platform that transforms fragmented financial data into clear, auditable payment strategies across multiple scenarios (BEST/BASE/WORST case).

**Status**: Fully implemented ✅ (Financial State Engine + Risk Detection Engine + Deterministic Decision Engine + Explainability Engine)

---

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [Engine 1: Financial State Engine](#engine-1-financial-state-engine)
3. [Engine 2: Risk Detection Engine](#engine-2-risk-detection-engine)
4. [Engine 3: Deterministic Decision Engine](#engine-3-deterministic-decision-engine)
5. [Engine 4: Explainability Engine](#engine-4-explainability-engine)
6. [End-to-End Usage](#end-to-end-usage)
7. [Testing](#testing)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CAPITALSENSE SYSTEM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Raw Financial Data                                             │
│  ├─ Bank Transactions                                           │
│  ├─ Payables (Invoices)                                         │
│  ├─ Receivables (Expected Income)                               │
│  └─ Business Context                                            │
│           ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ENGINE 1: FINANCIAL STATE ENGINE                        │   │
│  │ Computes: Health Score, Cash Runway, Obligation Pressure│   │
│  │ Output: FinancialState with comprehensive metrics        │   │
│  └──────────────────────────────────────────────────────────┘   │
│           ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ENGINE 2: RISK DETECTION ENGINE                         │   │
│  │ Projects: 3 scenarios (BEST/BASE/WORST)                 │   │
│  │ Output: RiskDetectionResult with shortfall dates        │   │
│  └──────────────────────────────────────────────────────────┘   │
│           ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ENGINE 3: DETERMINISTIC DECISION ENGINE                 │   │
│  │ Generates: 9 payment strategies (3 scenarios × 3 approaches)│
│  │ Output: DecisionResult3Scenarios with payment plans      │   │
│  └──────────────────────────────────────────────────────────┘   │
│           ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ENGINE 4: EXPLAINABILITY ENGINE (NEW!)                  │   │
│  │ Explains: All 9 strategies with business reasoning      │   │
│  │ Output: CompleteExplanation (no algorithm exposure)      │   │
│  └──────────────────────────────────────────────────────────┘   │
│           ↓                                                      │
│  Final Output: DecisionResult3Scenarios + Explanations      │   │
│  Ready for: API/Frontend/Reports                            │   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Engine 1: Financial State Engine

**Purpose**: Compute current financial health and cash flow metrics

**Location**: `financial_state_engine/`

### Main Function: `compute_financial_state()`

#### **Input Parameters**
```python
compute_financial_state(
    current_balance: float,                    # Current account balance (₹)
    transactions: List[Transaction],           # Bank transactions (for context)
    payables: List[Payable],                   # Invoices owed to vendors
    receivables: List[Receivable],             # Expected income from customers
    hidden_transactions: List[HiddenTransaction],  # Recurring transactions
    business_context: BusinessContext,         # Min buffer, time horizon
    reference_date: str = "YYYY-MM-DD",        # Today's date
    verbose: bool = False
)
```

#### **Input Models**

**Transaction** - Bank history record
```python
Transaction(
    date="2026-03-25",
    description="Client Payment",
    amount=50000,  # Positive=credit, Negative=debit
    transaction_type="credit"  # or "debit"
)
```

**Payable** - Amount owed
```python
Payable(
    id="PAY-001",
    amount=10000,
    due_date="2026-03-30",
    description="Invoice from Vendor",
    status="pending",  # "pending", "due", "overdue", "paid"
    priority_level="high",  # "critical", "high", "normal", "low"
    category=None  # Optional: "Supplier", "Tax", etc.
)
```

**Receivable** - Money expected
```python
Receivable(
    id="REC-001",
    amount=50000,
    expected_date="2026-03-28",
    description="Customer Invoice",
    status="pending",  # "pending", "received", "delayed", "cancelled"
    confidence_percentage=85,  # Likelihood of receipt (0-100)
    category=None
)
```

**HiddenTransaction** - Recurring/automatic payments
```python
HiddenTransaction(
    transaction_type="SALARY",  # "SALARY", "LOAN_PAYMENT", "SUBSCRIPTION", etc.
    amount=100000,
    frequency="MONTHLY",  # "DAILY", "WEEKLY", "MONTHLY", etc.
    start_date="2026-03-01",
    end_date="2026-12-31",
    description="Employee Salaries"
)
```

**BusinessContext** - Business constraints
```python
BusinessContext(
    min_cash_buffer=50000,  # Minimum cash to maintain (₹)
    allows_partial_payments=True,  # Can split payments?
    time_horizon_days=30  # Look-ahead period
)
```

#### **Output: FinancialState**

```python
FinancialState(
    current_balance=100000.0,           # Current account balance
    available_cash=50000.0,             # Balance minus min buffer
    total_payables_due_now=20000.0,     # Overdue + due today
    total_payables_due_soon=45000.0,    # Due within horizon
    total_payables_all=100000.0,        # All future payables
    weighted_receivables=35000.0,       # Expected income (confidence-adjusted)
    total_receivables_unweighted=40000.0,  # Total without confidence
    cash_runway_days=15,                # Days until buffer breach
    obligation_pressure_ratio=1.8,      # Payables / (Cash + Receivables)
    receivable_quality_score=78,        # Confidence in incoming cash (0-100)
    buffer_sufficiency_days=8,          # Days buffer lasts at burn rate
    health_score=65,                    # Overall health (0-100)
    health_score_breakdown=HealthScoreBreakdown(...),  # Component scores
    health_reasoning="...",             # Why this score
    cash_flow_timeline=[...],           # Day-by-day events
    snapshot_date="2026-03-25",
    status_flags={                      # Risk conditions
        "has_overdue": True,
        "high_pressure": True,
        "low_buffer": False
    }
)
```

### Sub-Functions (Internal)

| Function | Purpose | Input | Output |
|----------|---------|-------|--------|
| `compute_available_cash()` | Available cash after buffer | balance, min_buffer | float |
| `aggregate_payables_by_timeline()` | Group payables by timing | payables, horizon, date | (due_now, due_soon, due_later) |
| `compute_weighted_receivables()` | Adjust receivables by confidence | receivables, horizon, date | (weighted, unweighted) |
| `calculate_runway_days()` | Days until cash depletes | available_cash, daily_burn | int \| None |
| `calculate_obligation_pressure_ratio()` | Payables vs resources | payables, cash, receivables | float |
| `compute_health_score()` | Overall health 0-100 | runway, pressure, quality, buffer | int |
| `generate_health_reasoning()` | Explain the score | components, limiting_factor | str |

---

## Engine 2: Risk Detection Engine

**Purpose**: Project cash flows across 3 scenarios and detect shortfalls

**Location**: `risk_detection_engine/`

### Main Function: `detect_risks()`

#### **Input Parameters**
```python
detect_risks(
    financial_state: FinancialState,           # From Engine 1
    business_context: BusinessContext,         # Business constraints
    reference_date: str = "YYYY-MM-DD"         # Today's date
)
```

#### **Output: RiskDetectionResult**

```python
RiskDetectionResult(
    best_case=RiskProjection(...),   # Optimistic scenario
    base_case=RiskProjection(...),   # Most likely scenario
    worst_case=RiskProjection(...),  # Pessimistic scenario
)
```

### RiskProjection Model

```python
RiskProjection(
    scenario_type=ScenarioType.BASE,        # BEST, BASE, WORST
    first_shortfall_date=datetime(...),     # When cash turns negative
    days_to_shortfall=30,                   # Number of days until shortfall
    minimum_cash_amount=10000.0,            # Lowest cash point
    minimum_cash_date=datetime(...),        # When minimum occurs
    risk_severity="MODERATE"                # CRITICAL, HIGH, MODERATE, LOW
)
```

### Scenario Logic

| Scenario | Description | Cash Flow Assumption |
|----------|-------------|----------------------|
| **BEST** | Optimistic | All receivables arrive on time, zero delays |
| **BASE** | Most likely | Weighted by confidence score, some delays |
| **WORST** | Pessimistic | Receivables delayed 7 days, high burn rate |

### Sub-Functions

| Function | Purpose | Input | Output |
|----------|---------|-------|--------|
| `project_cash_position()` | Simulate daily cash | state, days, scenario | timeline |
| `find_shortfall_date()` | When does cash go negative? | timeline, buffer | datetime \| None |
| `compute_minimum_cash()` | Lowest cash point | timeline | (amount, date) |
| `assess_risk_severity()` | CRITICAL/HIGH/etc | days_to_shortfall, amount | str |

---

## Engine 3: Deterministic Decision Engine

**Purpose**: Generate optimal payment strategies across 3 scenarios

**Location**: `deterministic_decision_engine/`

### Main Function: `make_payment_decisions()`

#### **Input Parameters**
```python
make_payment_decisions(
    financial_state: FinancialState,        # From Engine 1
    risk_detection_result: RiskDetectionResult,  # From Engine 2
    payables: List[Payable],                # Obligations to evaluate
    vendor_relationships: Dict[str, VendorRelationship] = None,  # Vendor info
    reference_date: datetime = None,        # Current date
    risk_level: str = "MODERATE"            # AGGRESSIVE, MODERATE, CONSERVATIVE
)
```

#### **VendorRelationship Model**

```python
VendorRelationship(
    vendor_id="ACME-CORP",                  # Vendor identifier
    vendor_name="ACME Corporation",          # Display name
    relationship_type=VendorRelationshipType.CORE,  # NEW, EXISTING, CORE
    years_with_business=5.0,                # How long relationship
    payment_reliability=95.0                # Historical on-time % (0-100)
)
```

#### **Output: DecisionResult3Scenarios**

```python
DecisionResult3Scenarios(
    best_case=DecisionResult(...),      # 3 strategies for BEST scenario
    base_case=DecisionResult(...),      # 3 strategies for BASE scenario
    worst_case=DecisionResult(...),     # 3 strategies for WORST scenario
    overall_recommendation="Plan for BASE case...",  # Cross-scenario guidance
    explanation=CompleteExplanation(...)  # NEW! Explanations for all 9 strategies
)
```

### DecisionResult Model (per scenario)

```python
DecisionResult(
    scenario_type=ScenarioType.BASE,
    aggressive_strategy=PaymentStrategy(...),    # Spend 90% cash
    balanced_strategy=PaymentStrategy(...),      # Spend 70% cash
    conservative_strategy=PaymentStrategy(...),  # Spend 40% cash
    recommended_strategy=StrategyType.BALANCED,  # Which one to use
    reasoning="Balanced optimizes...",           # Why recommended
    cash_available=25000.0
)
```

### PaymentStrategy Model

```python
PaymentStrategy(
    strategy_type=StrategyType.BALANCED,     # AGGRESSIVE, BALANCED, CONSERVATIVE
    scenario_type=ScenarioType.BASE,         # BEST, BASE, WORST
    decisions=[PaymentDecision(...), ...],   # List of per-obligation decisions
    total_payment=15000.0,                   # Total cash to spend
    total_penalty_cost=500.0,                # Estimated penalties
    estimated_cash_after=10000.0,            # Cash remaining
    survival_probability=78.0,               # Chance of staying above buffer (%)
    score=45.0,                              # Ranking score (lower = better)
)
```

### PaymentDecision Model (per obligation)

```python
PaymentDecision(
    obligation_id="TAX-001",
    status=PaymentStatus.PAY_IN_FULL,       # PAY_IN_FULL, PARTIAL_PAY, DELAY, STRATEGIC_DEFAULT
    pay_amount=10000.0,                      # Amount to pay now
    delay_days=0,                            # Days to defer payment
    potential_penalty=0.0,                   # Estimated penalty cost
    rationale="Critical obligation; penalty 5% daily",
    vendor_id="IRS",
    vendor_name="IRS",
    due_date=datetime(...),
    category="Tax"
)
```

### Strategy Decision Logic

#### **Three Spending Approaches**

| Strategy | Spending | Focus | Best For |
|----------|----------|-------|----------|
| **AGGRESSIVE** | 90% available cash | Minimize penalties | Strong cash position, high-penalty items |
| **BALANCED** | 70% available cash | Optimize payment vs survival | Most situations (recommended) |
| **CONSERVATIVE** | 40% available cash | Maximize survival | Weak cash position, worst case |

#### **Scoring Formula** (Deterministic but NOT exposed in explanations)
```
Final Score = (Legal×40% + Urgency×30% + Penalty×20% + Vendor×10% - Flexibility×5%) / 100

Where:
- Legal: Tax/Loan/Payroll=90-100, Utilities=65, Supplier=40
- Urgency: Scales 0-100 based on days until due
- Penalty: Daily penalty rate × days
- Vendor: NEW=85, EXISTING=50, CORE=25 (relationship importance)
- Flexibility: 80 if partial allowed, else 20
```

### Sub-Functions

| Function | Purpose | Input | Output |
|----------|---------|-------|--------|
| `score_obligations()` | Compute priority scores | payables, vendor data | List[ObligationScore] |
| `generate_payment_strategies()` | Create 9 strategies | scores, cash, scenario | DecisionResult3Scenarios |
| `select_strategy()` | Pick best per scenario | 3 strategies, risk_level | (StrategyType, reasoning) |
| `evaluate_strategy()` | Compute metrics | decisions, cash, context | (cash_after, penalties, survival) |

---

## Engine 4: Explainability Engine (NEW!)

**Purpose**: Generate business-friendly explanations WITHOUT exposing algorithm internals

**Location**: `deterministic_decision_engine/`

### Main Function: `make_payment_decisions_with_explanations()`

#### **Input Parameters**
```python
make_payment_decisions_with_explanations(
    financial_state: FinancialState,        # From Engine 1
    risk_detection_result: RiskDetectionResult,  # From Engine 2
    payables: List[Payable],                # Obligations
    vendor_relationships: Dict = None,      # Vendor info
    reference_date: datetime = None,        # Today's date
    risk_level: str = "MODERATE",           # AGGRESSIVE, MODERATE, CONSERVATIVE
    enable_llm_refinement: bool = False     # Optional text polish
)
```

#### **Output: DecisionResult3Scenarios + Explanations**

```python
decisions = make_payment_decisions_with_explanations(...)

# Access decisions (same as Engine 3)
decisions.base_case.recommended_strategy  # BALANCED
decisions.base_case.balanced_strategy.total_payment  # $12,500

# NEW: Access complete explanations for all 9 strategies
explanation = decisions.explanation
```

### CompleteExplanation Model

```python
CompleteExplanation(
    # All 9 strategy explanations organized by scenario
    best_case_explanations={
        "aggressive": StrategyExplanation(...),
        "balanced": StrategyExplanation(...),
        "conservative": StrategyExplanation(...)
    },
    base_case_explanations={...},
    worst_case_explanations={...},
    
    # Recommended paths
    recommended_best_case="balanced",
    recommended_base_case="balanced",
    recommended_worst_case="conservative",
    
    # Cross-scenario guidance
    cross_scenario_summary="Plan for BASE case... Prepare WORST contingency...",
    scenario_context="BASE is most likely (70% probability)...",
    action_recommendation="1. PRIMARY: Execute BASE BALANCED strategy... 2. CONTINGENCY: Prepare WORST backup...",
    
    # Aggregated insights
    critical_obligations=["TAX-001"],      # Always paid
    flexible_obligations=["SUP-001"],      # Vary by strategy
    
    timestamp=datetime(...),
    generated_by="ExplainabilityEngine/1.0"
)
```

### StrategyExplanation Model

```python
StrategyExplanation(
    strategy_type="BALANCED",                # AGGRESSIVE, BALANCED, CONSERVATIVE
    scenario_type="Base",                    # BEST, BASE, WORST
    
    # Overview
    summary="BALANCED strategy spends 70% of available cash...",
    spending_profile="Total available: $25,000. Pay 2 obligations ($12,500)...",
    approach="Balances maintaining vendor relationships with survival...",
    
    # Detailed decisions
    obligation_explanations=[DecisionExplanation(...), ...],
    
    # Metrics
    total_payment=12500.0,
    total_penalty_cost=50.0,
    estimated_cash_after=12500.0,
    survival_probability=78.0,
    
    # Comparisons
    key_trade_offs="vs Aggressive: $2,500 less paid, $50 less penalty. vs Conservative: $2,500 more paid, $100 more penalty.",
    
    # Assessment
    strength="Optimizes both vendor relationships and operational survival",
    weakness="Higher penalty exposure than Aggressive",
    best_for="Recommended for most situations as it balances competing priorities",
    
    # Execution
    execution_guidance="1. Pay critical/legal obligations first... 2. Negotiate payment terms...",
    
    highest_priority_items=["IRS: $10,000", "ACME Corp: $2,500"],
    deferred_items=["ACME Corp: 14d delay"]
)
```

### DecisionExplanation Model (per obligation)

```python
DecisionExplanation(
    obligation_id="SUP-001",
    vendor_name="ACME Corp",
    category="Supplier",
    
    # Decision
    decision_status="Partial payment",
    pay_amount=2500.0,
    delay_days=14,
    
    # Business factors (NO algorithm exposure)
    factors=ExplanationFactors(
        urgency_level=UrgencyLevel.MEDIUM,         # CRITICAL/HIGH/MEDIUM/LOW
        penalty_risk_level=PenaltyRiskLevel.MEDIUM,
        vendor_impact_level=VendorImpactLevel.HIGH,
        flexibility_assessment=True,               # Can partial pay?
        estimated_penalty=50.0,                    # If delayed 1 week
        ...
    ),
    
    # Explanation
    summary="ACME Corp: Partial payment of $2,500. Delay remainder 14 days.",
    decision_rationale="Partial payment to preserve cash while maintaining relationship.",
    implications="Potential penalty: $50 if not paid within 14 days. Relationship risk: MEDIUM",
    
    # Alternatives
    comparison=StrategyComparison(...),            # What if chose different strategy?
    alternative_scenarios="If Aggressive: Pay in full ($5,000), penalty $0, but cash $15,000. If Conservative: Delay 30 days, penalty $150, but cash $17,500.",
    
    risk_to_decision="Vendor may impose stricter terms if delayed",
    mitigation="Communicate proactively; offer 50% upfront + 50% in 14 days"
)
```

### ExplanationFactors Model

```python
ExplanationFactors(
    obligation_id="SUP-001",
    vendor_name="ACME Corp",
    category="Supplier",
    amount=5000.0,
    
    # Business-level urgency (NOT internal score)
    urgency_level=UrgencyLevel.MEDIUM,      # CRITICAL/HIGH/MEDIUM/LOW
    days_to_due=30,
    days_overdue=0,
    
    # Penalty risk (human-readable)
    penalty_risk_level=PenaltyRiskLevel.MEDIUM,    # CRITICAL/HIGH/MEDIUM/LOW
    estimated_penalty=50.0,                        # If delayed 1 week
    penalty_accrual="Minimal or negotiable",       # Human-readable
    
    # Vendor relationship (levels, not scores)
    vendor_impact_level=VendorImpactLevel.HIGH,    # CRITICAL/HIGH/MEDIUM/LOW
    vendor_relationship="Established",              # Core/Established/New
    years_with_vendor=2.5,
    
    # Flexibility
    flexibility_assessment=True,                    # Can accept partial?
    partial_payment_allowed=True,
    minimum_partial="50% or $2,500 minimum"
)
```

### Key Features

✅ **NO Algorithm Exposure**: Business-level classifications only
- No scoring formula weights (40%, 30%, 20%, 10%, 5%)
- No internal numeric scores
- No algorithm components exposed

✅ **Deterministic Only**: 100% rule-based template generation
- All explanations from business logic
- Optional LLM for text polish (readability only)

✅ **Complete Transparency**: All 9 strategies explained
- 3 scenarios × 3 approaches = 9 total
- Each with rationale, trade-offs, pros/cons

✅ **Actionable Guidance**: Execution steps, trade-off analysis

### Sub-Functions

| Function | Purpose | Input | Output |
|----------|---------|-------|--------|
| `extract_explanation_factors()` | Map scores to business levels | decision, obligation_data | ExplanationFactors |
| `build_strategy_explanation()` | Create per-strategy explanation | strategy, scenario | StrategyExplanation |
| `generate_decision_summary()` | 1-2 sentence decision | decision, factors | str |
| `generate_trade_offs()` | Compare to other strategies | strategy, alternatives | str |
| `build_strategy_comparison()` | What if chose differently? | decision, all strategies | StrategyComparison |
| `generate_complete_explanation()` | All 9 strategies + guidance | decisions, financial_state, risk | CompleteExplanation |

---

## End-to-End Usage

### Quick Start
```python
from financial_state_engine import compute_financial_state
from risk_detection_engine import detect_risks
from deterministic_decision_engine.engine import make_payment_decisions_with_explanations

# Step 1: Compute current financial state
financial_state = compute_financial_state(
    current_balance=100000,
    transactions=[...],
    payables=[...],
    receivables=[...],
    hidden_transactions=[...],
    business_context=BusinessContext(min_cash_buffer=50000, time_horizon_days=30)
)
print(f"Health Score: {financial_state.health_score}")
print(f"Cash Runway: {financial_state.cash_runway_days} days")

# Step 2: Project risks across 3 scenarios
risk_detection = detect_risks(financial_state, business_context)
print(f"BASE shortfall in {risk_detection.base_case.days_to_shortfall} days")

# Step 3: Generate decisions WITH explanations
decisions = make_payment_decisions_with_explanations(
    financial_state=financial_state,
    risk_detection_result=risk_detection,
    payables=payables,
    risk_level="MODERATE"
)

# Step 4: Access results
print(f"\n--- BASE CASE (Most Likely) ---")
print(f"Recommended: {decisions.base_case.recommended_strategy}")
print(f"Pay: ${decisions.base_case.balanced_strategy.total_payment:,.2f}")
print(f"Penalties: ${decisions.base_case.balanced_strategy.total_penalty_cost:,.2f}")
print(f"Survival: {decisions.base_case.balanced_strategy.survival_probability:.0f}%")

# Step 5: Get full explanations (NEW!)
explanation = decisions.explanation
print(f"\n--- STRATEGY EXPLANATION ---")
balanced_exp = explanation.get_strategy_explanation("base", "balanced")
print(balanced_exp.summary)
print(f"\nKey Trade-offs: {balanced_exp.key_trade_offs}")
print(f"\nExecution: {balanced_exp.execution_guidance}")

# Step 6: Cross-scenario guidance
print(f"\n--- ACTION PLAN ---")
print(explanation.action_recommendation)
```

### Output Example
```
--- BASE CASE (Most Likely) ---
Recommended: BALANCED
Pay: $12,500.00
Penalties: $50.00
Survival: 78.0%

--- STRATEGY EXPLANATION ---
BALANCED strategy in Base case: Spend 70% of available cash across 2 obligations. 
Balances payment of critical items with survival cash preservation.

Key Trade-offs: vs Aggressive: $2,500 less paid, $50 less penalty. 
vs Conservative: $2,500 more paid, $100 more penalty.

Execution: 
1. Pay critical/legal obligations first. 
2. Negotiate payment terms for flexible obligations. 
3. Reserve remaining cash for working capital. 
4. Communicate proactively with key vendors.

--- ACTION PLAN ---
1. PRIMARY: Execute your BASE case BALANCED strategy. 
2. CONTINGENCY: Prepare triggers to switch to WORST case CONSERVATIVE strategy if cash drops below threshold. 
3. UPSIDE: Define actions if conditions move toward BEST case (increased spending for growth).
```

---

## Testing

### Run All Tests
```bash
cd /Users/ujjwalchoraria/Desktop/CapitalSense

# All engines
python3 -m pytest tests/ -v

# Individual engines
python3 -m pytest tests/test_financial_state_engine.py -v
python3 -m pytest tests/test_risk_detection_engine.py -v  
python3 -m pytest tests/test_deterministic_decision_engine.py -v
python3 -m pytest tests/test_explainability_engine.py -v  # NEW!
```

### Manual Testing (Explainability Engine)
```bash
python3 manual_test_explainability.py
```

Produces formatted output showing:
- All 9 strategies (3 scenarios × 3 approaches)
- Per-obligation decisions with rationale
- Trade-off analysis
- Execution guidance
- Cross-scenario recommendations

---

## Project Structure

```
CapitalSense/
├── README.md (this file)
├── manual_test_explainability.py              # Demo script
│
├── financial_state_engine/
│   ├── models.py                              # Transaction, Payable, etc.
│   ├── validators.py                          # Input validation
│   ├── aggregators.py                         # Sum/consolidate data
│   ├── metrics.py                             # Calculate runway, pressure, etc.
│   ├── health_scorer.py                       # Health score computation
│   ├── engine.py                              # Main orchestrator
│   ├── utils.py                               # Helpers
│   └── __init__.py
│
├── risk_detection_engine/
│   ├── models.py                              # RiskProjection, etc.
│   ├── projections.py                         # Scenario modeling
│   ├── engine.py                              # Main entry point
│   └── __init__.py
│
├── deterministic_decision_engine/
│   ├── models.py                              # Decision models
│   ├── explanation_models.py                  # Explainability models (NEW!)
│   ├── obligation_scorer.py                   # Priority scoring
│   ├── payment_optimizer.py                   # Strategy generation
│   ├── strategy_evaluator.py                  # Rank strategies
│   ├── explainability_engine.py               # Explanations (NEW!)
│   ├── engine.py                              # Main DDE + new API
│   ├── decision_generator.py                  # Generate decisions
│   ├── constants.py                           # Penalty models, etc.
│   └── __init__.py
│
└── tests/
    ├── test_financial_state_engine.py
    ├── test_risk_detection_engine.py
    ├── test_deterministic_decision_engine.py
    └── test_explainability_engine.py          # 20 tests (NEW!)
```

---

## Key Concepts

### Deterministic Approach
✅ No machine learning, no randomness
✅ Fully auditable decision logic
✅ Reproducible results
✅ Easy to explain to regulators/customers

### Three-Scenario Planning
✅ **BEST**: Optimistic cash flow (buffer = one time to act)
✅ **BASE**: Most likely (70% confidence = primary plan)
✅ **WORST**: Pessimistic (contingency for if things go wrong)

### Three-Approach Strategies
✅ **AGGRESSIVE**: Minimize penalties, spend 90% cash
✅ **BALANCED**: Optimize trade-offs, spend 70% cash (RECOMMENDED)
✅ **CONSERVATIVE**: Maximize survival, spend 40% cash

### Business Reasoning (NOT Algorithm Details)
✅ Explanations use business language
✅ No scoring weights exposed (40%, 30%, 20%, etc.)
✅ Focus on: urgency, penalties, vendor relationships, cash impact
✅ Complete transparency without revealing algorithm internals

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Mar 2026 | Financial State Engine (FSE) |
| 2.0 | Mar 2026 | Added Risk Detection Engine (RDE) |
| 3.0 | Mar 2026 | Added Deterministic Decision Engine (DDE) |
| 4.0 | Mar 2026 | **NEW!** Added Explainability Engine (complete transparency) |

---

## Support & Documentation

- **Inputs**: See data model sections for each engine
- **Outputs**: See output model sections
- **Examples**: Run `manual_test_explainability.py` for live demo
- **Tests**: See `tests/` directory for comprehensive examples
- **API**: See `make_payment_decisions_with_explanations()` for single entry point

---

**Status**: ✅ Production Ready | All 4 engines fully implemented | 20+ tests passing

