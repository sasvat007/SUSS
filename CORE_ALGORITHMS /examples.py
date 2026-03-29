"""
Example usage of the Financial State Engine.

Demonstrates how to use the engine with realistic scenarios.
"""

import json
from financial_state_engine import (
    compute_financial_state, FinancialStateEngine,
    Transaction, Payable, Receivable, HiddenTransaction, BusinessContext
)
from financial_state_engine.utils import get_today, get_date_n_days_ahead


def example_stable_business():
    """Example: Stable, well-managed business."""
    print("=" * 70)
    print("EXAMPLE 1: Stable Business")
    print("=" * 70)
    
    today = get_today()
    
    # Typical stable business scenario
    state = compute_financial_state(
        current_balance=150000,
        transactions=[
            Transaction(
                date=today,
                description="Sales Revenue",
                amount=50000,
                transaction_type="credit"
            )
        ],
        payables=[
            Payable(
                id="p1",
                amount=8000,
                due_date=get_date_n_days_ahead(5, today),
                description="Raw Materials Purchase",
                status="pending",
                priority_level="high"
            ),
            Payable(
                id="p2",
                amount=12000,
                due_date=get_date_n_days_ahead(15, today),
                description="Rent",
                status="pending",
                priority_level="normal"
            )
        ],
        receivables=[
            Receivable(
                id="r1",
                amount=40000,
                expected_date=get_date_n_days_ahead(7, today),
                description="Project ABC - Client XYZ",
                confidence=0.95
            ),
            Receivable(
                id="r2",
                amount=25000,
                expected_date=get_date_n_days_ahead(12, today),
                description="Retainer - Client 123",
                confidence=0.85
            )
        ],
        hidden_transactions=[
            HiddenTransaction(
                id="h1",
                transaction_type="salary",
                amount=-50000,
                frequency="monthly",
                next_date=get_date_n_days_ahead(5, today),
                category="Team Salaries (5 employees)"
            ),
            HiddenTransaction(
                id="h2",
                transaction_type="subscription",
                amount=-2000,
                frequency="monthly",
                next_date=get_date_n_days_ahead(28, today),
                category="SaaS Tools & Software"
            )
        ],
        business_context=BusinessContext(
            min_cash_buffer=30000,
            time_horizon_days=30,
            allow_partial_payments=True,
            avg_payment_delay_days=2
        ),
        reference_date=today,
        verbose=True
    )
    
    print("\n" + "-" * 70)
    print("RESULTS:")
    print("-" * 70)
    print(f"Health Score: {state.health_score}/100")
    print(f"Current Balance: ₹{state.current_balance:,.2f}")
    print(f"Available Cash: ₹{state.available_cash:,.2f}")
    print(f"Cash Runway: {state.cash_runway_days if state.cash_runway_days else 'Stable'} days")
    print(f"Obligation Pressure Ratio: {state.obligation_pressure_ratio:.2f}")
    print(f"Receivable Quality: {state.receivable_quality_score:.2f}")
    print(f"\nStatus Flags:")
    for flag, value in state.status_flags.items():
        if value:
            print(f"  ⚠ {flag}: {value}")
    
    print("\n" + "-" * 70)
    print("REASONING:")
    print("-" * 70)
    print(state.health_reasoning)
    
    return state


def example_distressed_business():
    """Example: Business under cash constraints."""
    print("\n\n" + "=" * 70)
    print("EXAMPLE 2: Distressed Business (Cash Constraints)")
    print("=" * 70)
    
    today = get_today()
    
    # Tight cash scenario
    state = compute_financial_state(
        current_balance=8000,
        transactions=[
            Transaction(
                date=today,
                description="Emergency loan drawdown",
                amount=5000,
                transaction_type="credit"
            )
        ],
        payables=[
            Payable(
                id="p1",
                amount=5000,
                due_date=today,
                description="Overdue Vendor Invoice",
                status="overdue",
                priority_level="critical"
            ),
            Payable(
                id="p2",
                amount=8000,
                due_date=get_date_n_days_ahead(2, today),
                description="Payroll (due in 2 days)",
                status="pending",
                priority_level="critical"
            ),
            Payable(
                id="p3",
                amount=12000,
                due_date=get_date_n_days_ahead(10, today),
                description="Supplier Payment",
                status="pending",
                priority_level="high"
            )
        ],
        receivables=[
            Receivable(
                id="r1",
                amount=30000,
                expected_date=get_date_n_days_ahead(15, today),
                description="Major Client Invoice (uncertain)",
                confidence=0.4  # Low confidence due to past delays
            )
        ],
        hidden_transactions=[
            HiddenTransaction(
                id="h1",
                transaction_type="subscription",
                amount=-1500,
                frequency="monthly",
                next_date=get_date_n_days_ahead(5, today),
                category="AWS Infrastructure"
            )
        ],
        business_context=BusinessContext(
            min_cash_buffer=3000,
            time_horizon_days=30,
            allow_partial_payments=True,  # Partial payments allowed
            avg_payment_delay_days=7
        ),
        reference_date=today,
        verbose=True
    )
    
    print("\n" + "-" * 70)
    print("RESULTS:")
    print("-" * 70)
    print(f"Health Score: {state.health_score}/100")
    print(f"Current Balance: ₹{state.current_balance:,.2f}")
    print(f"Available Cash: ₹{state.available_cash:,.2f}")
    print(f"Cash Runway: {state.cash_runway_days if state.cash_runway_days else 'Stable'} days")
    print(f"Obligation Pressure Ratio: {state.obligation_pressure_ratio:.2f}")
    print(f"Receivable Quality: {state.receivable_quality_score:.2f}")
    print(f"\nPayables Due Now: ₹{state.total_payables_due_now:,.2f}")
    print(f"Payables Due Soon (within {state.cash_flow_timeline[-1].date if state.cash_flow_timeline else 'N/A'}): ₹{state.total_payables_due_soon:,.2f}")
    
    print(f"\nCritical Status Flags:")
    for flag, value in state.status_flags.items():
        if value:
            print(f"  🔴 {flag}")
    
    print("\n" + "-" * 70)
    print("REASONING:")
    print("-" * 70)
    print(state.health_reasoning)
    
    return state


def example_json_output():
    """Example: JSON output for API/integration."""
    print("\n\n" + "=" * 70)
    print("EXAMPLE 3: JSON Output for API Integration")
    print("=" * 70)
    
    today = get_today()
    
    state = compute_financial_state(
        current_balance=75000,
        transactions=[],
        payables=[
            Payable(
                id="p1",
                amount=10000,
                due_date=get_date_n_days_ahead(8, today),
                description="Q1 Rent",
                status="pending"
            )
        ],
        receivables=[
            Receivable(
                id="r1",
                amount=50000,
                expected_date=get_date_n_days_ahead(10, today),
                description="Contract Completion",
                confidence=0.9
            )
        ],
        hidden_transactions=[],
        business_context=BusinessContext(
            min_cash_buffer=20000,
            time_horizon_days=30
        ),
        reference_date=today,
        verbose=False
    )
    
    # Convert to JSON
    json_output = json.dumps(state.to_json_dict(), indent=2)
    
    print("\nJSON Output (First 50 lines):")
    print("-" * 70)
    lines = json_output.split('\n')
    for line in lines[:50]:
        print(line)
    
    # Also show structure
    print("\n... (output truncated)")
    print("\nKey Fields in JSON:")
    state_dict = state.to_json_dict()
    print(f"  • health_score: {state_dict['health_score']}")
    print(f"  • cash_runway_days: {state_dict['cash_runway_days']}")
    print(f"  • obligation_pressure_ratio: {state_dict['obligation_pressure_ratio']}")
    print(f"  • cash_flow_timeline entries: {len(state_dict['cash_flow_timeline'])}")
    print(f"  • status_flags count: {sum(1 for v in state_dict['status_flags'].values() if v)}")
    
    return state


def example_cash_flow_analysis():
    """Example: Detailed cash flow timeline analysis."""
    print("\n\n" + "=" * 70)
    print("EXAMPLE 4: Cash Flow Timeline Analysis")
    print("=" * 70)
    
    today = get_today()
    
    state = compute_financial_state(
        current_balance=50000,
        transactions=[],
        payables=[
            Payable(
                id="p1",
                amount=10000,
                due_date=get_date_n_days_ahead(3, today),
                description="Vendor A",
                status="pending"
            ),
            Payable(
                id="p2",
                amount=8000,
                due_date=get_date_n_days_ahead(8, today),
                description="Vendor B",
                status="pending"
            )
        ],
        receivables=[
            Receivable(
                id="r1",
                amount=20000,
                expected_date=get_date_n_days_ahead(5, today),
                description="Client Invoice",
                confidence=0.9
            )
        ],
        hidden_transactions=[
            HiddenTransaction(
                id="h1",
                transaction_type="salary",
                amount=-15000,
                frequency="monthly",
                next_date=get_date_n_days_ahead(1, today),
                category="Payroll"
            )
        ],
        business_context=BusinessContext(
            min_cash_buffer=15000,
            time_horizon_days=30
        ),
        reference_date=today,
        verbose=False
    )
    
    print("\nCash Flow Timeline (Day-by-Day):")
    print("-" * 70)
    print(f"Starting Balance: ₹{state.current_balance:,.2f}")
    print(f"Min Buffer: ₹{state.current_balance - state.available_cash:,.2f}\n")
    
    print(f"{'Date':<12} {'Inflow':<12} {'Outflow':<12} {'Balance':<15} {'Events':<30}")
    print("-" * 70)
    
    for event in state.cash_flow_timeline:
        events_str = "; ".join(event.events)[:28] if event.events else ""
        print(f"{event.date:<12} ₹{event.inflow:<11,.2f} ₹{event.outflow:<11,.2f} ₹{event.balance:<14,.2f} {events_str:<30}")
    
    print("\n" + "-" * 70)
    print(f"Final Balance (Day {len(state.cash_flow_timeline)}): ₹{state.cash_flow_timeline[-1].balance:,.2f}" if state.cash_flow_timeline else "No events")
    print(f"Cash Runway: {state.cash_runway_days if state.cash_runway_days else 'Stable'} days")
    
    return state


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║ " + "Financial State Engine - Usage Examples".center(66) + " ║")
    print("╚" + "=" * 68 + "╝")
    
    # Run examples
    stable_state = example_stable_business()
    distressed_state = example_distressed_business()
    json_state = example_json_output()
    timeline_state = example_cash_flow_analysis()
    
    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Scenario 1 (Stable):     Health Score {stable_state.health_score}/100")
    print(f"Scenario 2 (Distressed): Health Score {distressed_state.health_score}/100")
    print(f"Scenario 3 (API):        Health Score {json_state.health_score}/100")
    print(f"Scenario 4 (Timeline):   Health Score {timeline_state.health_score}/100")
    print("\n✓ All examples completed successfully!")


if __name__ == '__main__':
    main()
