# CapitalSense

**Transform fragmented financial data into clear payment strategies**

A deterministic financial decision engine that analyzes your cash position and generates auditable payment plans across three scenarios (BEST/BASE/WORST).

## ✨ What CapitalSense Does

```
💰 Your Financial Data  →  [4 Decision Engines]  →  📋 Clear Payment Strategy
```

**Input**: Bank transactions, invoices, expected income, payroll, recurring expenses  
**Output**: Prioritized payment plans with full explanations & trade-offs

### Key Features

- **4 Specialized Engines**: Financial state → Risk detection → Decision making → Explanations
- **Deterministic & Auditable**: No ML, no randomness, 100% rule-based
- **Three-Scenario Planning**: BEST/BASE/WORST futures so you can prepare
- **Complete Transparency**: All 9 strategies explained with business reasoning (no algorithm details)
- **Action-Ready Output**: Step-by-step guidance on what to do today
- **Full Modular Design**: Clean separation, testable, extensible


---

## 🏗️ The 4 Engines

| Engine | Purpose | Input | Output |
|--------|---------|-------|--------|
| **1️⃣ Financial State** | Analyze current health | Transactions, invoices, income | Health score (0-100), runway, pressure |
| **2️⃣ Risk Detection** | Project 3 possible futures | Financial state | Shortfall timelines (BEST/BASE/WORST) |
| **3️⃣ Decision Maker** | Generate payment strategies | Risk projection & obligations | 9 plans (3 scenarios × 3 approaches) |
| **4️⃣ Explainability** | ⭐ NEW! Explain all strategies | Strategies + business context | Complete explanations (zero algorithm exposure) |

---

## 🚀 Quick Start

```python
from financial_state_engine import compute_financial_state
from risk_detection_engine import detect_risks
from deterministic_decision_engine.engine import make_payment_decisions_with_explanations

# 1. Analyze current financial position
state = compute_financial_state(
    current_balance=100_000,
    payables=[...],
    receivables=[...],
    business_context=BusinessContext(min_cash_buffer=50_000)
)
print(f"Health: {state.health_score}/100")

# 2. Project risks across 3 scenarios
risks = detect_risks(state, business_context)
print(f"BASE case shortfall in {risks.base_case.days_to_shortfall} days")

# 3. Get decisions WITH full explanations
decisions = make_payment_decisions_with_explanations(
    financial_state=state,
    risk_detection_result=risks,
    payables=payables
)

# 4. Recommended strategy
print(f"Pay: ${decisions.base_case.balanced_strategy.total_payment:,}")
print(f"Survival: {decisions.base_case.balanced_strategy.survival_probability:.0f}%")

# 5. Complete explanation (NEW!)
explanation = decisions.explanation
print(explanation.action_recommendation)
```

---

## 📊 Understanding the Output

### Engine 1: Financial State
```
Health Score: 65/100
Cash Runway: 15 days (before minimum buffer breach)
Pressure Ratio: 1.8x (payables vs available resources)
→ Status: MODERATE (stable with manageable constraints)
```

### Engine 2: Risk Detection
```
BEST case:    No shortfall (optimistic cash flow)
BASE case:    Shortfall in 30 days (most likely)
WORST case:   Shortfall in 15 days (if things go wrong)
→ Plan for BASE, prepare WORST contingency
```

### Engine 3: Decision Engine
```
9 Strategies Generated (3 scenarios × 3 spending approaches):

BEST case:
  Aggressive: Pay $18k (90% cash) → $2k remaining
  Balanced:   Pay $14k (70% cash) → $6k remaining ← RECOMMENDED
  Conservative: Pay $10k (40% cash) → $10k remaining

BASE case:
  Aggressive: Pay $16k (90% cash) → $9k remaining
  Balanced:   Pay $12.5k (70% cash) → $12.5k remaining ← RECOMMENDED
  Conservative: Pay $8k (40% cash) → $17k remaining

WORST case:
  Aggressive: Pay $14k (90% cash) → $6k remaining
  Balanced:   Pay $10k (70% cash) → $10k remaining
  Conservative: Pay $6k (40% cash) → $14k remaining ← RECOMMENDED
```

### Engine 4: Explainability (NEW!)
```
✓ Why pay $12.5k (not $16k or $8k)?
✓ Which vendors to prioritize?
✓ What are the risks?
✓ Step-by-step action plan
✓ What if conditions change?

→ Complete business reasoning (ZERO algorithm details exposed)
```

---

## 🎯 The Three Scenarios

Plan for three possible futures, not just one:

| Scenario | When? | Cash Flow Assumption | Probability |
|----------|-------|---------------------|-------------|
| 🟢 **BEST** | Best day | Customers pay on time, no delays | 20% |
| 🟡 **BASE** | Most likely | ~70% of income arrives, standard delays | 70% |
| 🔴 **WORST** | If things go wrong | Income delayed, aggressive burn rate | 10% |

---

## 💡 The Three Spending Strategies

For **each scenario**, CapitalSense generates **three approaches**:

| Strategy | Style | Spend | How Much? | Best When |
|----------|-------|-------|----------|-----------|
| **🔥 Aggressive** | Maximize payments | 90% available | Pay more, preserve less | Strong cash position |
| **⚖️ Balanced** | Optimize tradeoff | 70% available | **RECOMMENDED** | Most situations |
| **🛡️ Conservative** | Maximize survival | 40% available | Pay less, hoard cash | Survival is critical |

---

## 📚 Data Inputs & Models

### Input: Payable (What You Owe)
```python
Payable(
    id="INV-2026-001",
    amount=10_000,                    # Amount owed
    due_date="2026-03-30",            # When due
    category="Supplier",              # Type: Supplier, Tax, Payroll, Utilities, etc.
    priority_level="high",            # critical, high, normal, low
    status="pending",                 # pending, due, overdue, paid
    description="Vendor Invoice ABC"
)
```

### Input: Receivable (Expected Income)
```python
Receivable(
    id="REC-2026-001",
    amount=50_000,                    # Amount expected
    expected_date="2026-03-28",       # When expected
    confidence_percentage=85,         # Likelihood 0-100 (based on history)
    description="Client Project Alpha"
)
```

### Input: BusinessContext (Your Constraints)
```python
BusinessContext(
    min_cash_buffer=50_000,           # Minimum to keep in bank
    allows_partial_payments=True,     # Can you split payments?
    time_horizon_days=30              # How far to look ahead
)
```

---

## 🎁 What's New: Explainability Engine (Engine 4)

### Before (Opaque Decision)
```
Decision: PAY $5,000 to Vendor ABC
Score: 45 ❌ What does 45 mean?
```

### Now (Complete Transparency)
```
Decision: PARTIAL payment to Vendor ABC: $2,500 (Delay remainder 14 days)

WHY? ✓ Established vendor (low relationship risk)
    ✓ Terms allow delay with minimal penalty
    ✓ Preserves critical cash for payroll
    
TRADE-OFFS:
  If AGGRESSIVE: Pay full $5,000 but only $15k left for other needs
  If CONSERVATIVE: Delay 30 days but keep $17.5k cash
  
EXECUTE:
  1. Call vendor, explain cash flow timing
  2. Offer 50% now, 50% in 14 days
  3. Get written confirmation
  4. Update records
  
RISKS: Potential penalty $50 if delayed beyond 14 days (MEDIUM risk)
       Vendor may tighten payment terms
MITIGATION: Communicate proactively; offer interest on delayed portion
```

✅ **Why this is powerful**:
- All 9 strategies explained (9 = 3 scenarios × 3 spending levels)
- Each obligation has rationale + trade-offs + action steps
- Business reasoning only (no scoring formulas, no algorithm guts)
- Per-vendor guidance: who to pay first, who to delay
- Cross-scenario recommendations: primary plan + backup triggers

---

## 📖 Complete Documentation

**For complete technical detail**, see [ARCHITECTURE.md](ARCHITECTURE.md) with:

- Full API documentation (all 4 engines)
- All models & data structures
- Detailed algorithms & scoring logic
- Sub-functions & internal workflows
- Complete test examples

**For live working example**, run:
```bash
python3 manual_test_explainability.py
```

Shows real payables, receivables, and all 9 strategies with full explanations

---

## 🧪 Testing

### Quick Test
```bash
cd /Users/ujjwalchoraria/Desktop/CapitalSense
python3 -m pytest tests/ -v
```

Running tests from all 4 engines (80+ tests, all passing):

| Engine | Tests | Status |
|--------|-------|--------|
| Financial State Engine | 15 | ✅ |
| Risk Detection Engine | 20 | ✅ |
| Decision Engine | 25 | ✅ |
| Explainability Engine | 20 | ✅ NEW! |
| **TOTAL** | **80+** | **✅ ALL PASS** |

### Manual Demo
```bash
python3 manual_test_explainability.py
```

Outputs:
- Live company scenario
- All 9 strategies compared
- Per-obligation explanations
- Trade-off analysis  
- Execution steps

---

## 📁 Project Structure

```
CapitalSense/
├── README.md                              ← Quick start & overview
├── ARCHITECTURE.md                        ← Deep technical docs
├── manual_test_explainability.py          ← Live demo script
│
├── financial_state_engine/                ← Engine 1: Current health
│   ├── models.py                          # Data models
│   ├── validators.py                      # Input validation
│   ├── aggregators.py                     # Consolidation
│   ├── metrics.py                         # Runway, pressure
│   ├── health_scorer.py                   # Score calculation
│   ├── engine.py                          # Main entry point
│   └── utils.py                           # Helpers
│
├── risk_detection_engine/                 ← Engine 2: Future threats
│   ├── models.py                          # RiskProjection
│   ├── projections.py                     # 3-scenario modeling
│   └── engine.py                          # Main entry point
│
├── deterministic_decision_engine/         ← Engines 3 & 4
│   ├── models.py                          # Decision models
│   ├── explanation_models.py              # Explainability models
│   ├── obligation_scorer.py               # Priority scoring
│   ├── payment_optimizer.py               # Strategy generation
│   ├── strategy_evaluator.py              # Ranking
│   ├── explainability_engine.py           # NEW! Explanations
│   ├── engine.py                          # Main orchestrator
│   └── constants.py                       # Penalty models
│
└── tests/                                 ← 80+ tests
    ├── test_financial_state_engine.py
    ├── test_risk_detection_engine.py
    ├── test_deterministic_decision_engine.py
    └── test_explainability_engine.py      # NEW!
```

---

## 🔄 How It Works

```
STEP 1: OBSERVE
├─ Bank balance: $100k
├─ Owe: $50k (invoices)
├─ Expect: $35k (incoming)
└─ Burn: $10k/month

          ↓

STEP 2: ASSESS (Engine 1)
├─ Health: 65/100
├─ Runway: 15 days
└─ Pressure: 1.8x

          ↓

STEP 3: PREDICT (Engine 2)
├─ BEST: No shortfall
├─ BASE: Day 30
└─ WORST: Day 15

          ↓

STEP 4: PLAN (Engine 3)
├─ 9 strategies generated
└─ BASE-Balanced recommended

          ↓

STEP 5: EXPLAIN (Engine 4 - NEW!)
├─ Why this strategy?
├─ Per-vendor decisions
├─ Trade-offs vs alternatives
└─ Action steps to execute

          ↓

RESULT: Auditable, executable plan
```

---

## ✅ Key Principles

✅ **Deterministic**: No ML, same inputs = same outputs  
✅ **Auditable**: Full reasoning trail, regulatory-ready  
✅ **Three Scenarios**: Prepare for BEST/BASE/WORST, not just one future  
✅ **Business Language**: Zero algorithm internals exposed  
✅ **Action-Ready**: Step-by-step guidance, not just analysis

---

## 🧁 FAQ

**Q: Why three scenarios?**  
A: Uncertain future. BEST/BASE/WORST let you prepare for any outcome.

**Q: Why BALANCED always recommended?**  
A: Optimizes obligation payment vs cash survival. Best mathematical trade-off.

**Q: Can I override?**  
A: Yes! AGGRESSIVE if strong position, CONSERVATIVE if critical. You decide.

**Q: How accurate?**  
A: As accurate as your input data. System flags confidence scores.

**Q: Why not pay everything?**  
A: You might not have enough cash for essential expenses. Strategic partial payments are often more efficient.

---

## 📞 API Quick Reference

### Engine 1: Financial State
```python
state = compute_financial_state(
    current_balance=100_000,
    payables=[...],
    receivables=[...],
    business_context=BusinessContext(min_cash_buffer=50_000)
)
print(state.health_score)  # 0-100
```

### Engine 2: Risk Detection  
```python
risks = detect_risks(state, business_context)
print(risks.base_case.days_to_shortfall)  # Days until cash runs out
```

### Engines 3 & 4: Decision + Explanations
```python
decisions = make_payment_decisions_with_explanations(
    financial_state=state,
    risk_detection_result=risks,
    payables=payables
)
# Engine 3
print(decisions.base_case.balanced_strategy.total_payment)
# Engine 4 (NEW!)
print(decisions.explanation.action_recommendation)
```

---

## 🎓 System Status

**Version**: 4.0 (Explainability Engine)  
**Status**: ✅ Production Ready  

| Component | Tests | Status |
|-----------|-------|--------|
| Financial State | 15 | ✅ |
| Risk Detection | 20 | ✅ |
| Decision | 25 | ✅ |
| Explainability | 20 | ✅ NEW! |
| **TOTAL** | **80+** | **✅ ALL PASS** |

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Quick start (you are here) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Technical deep-dive |
| [manual_test_explainability.py](manual_test_explainability.py) | Live demo |
| [tests/](tests/) | 80+ test examples |

---

**Made for clear, confident financial decisions**

March 2026 | CapitalSense Team
