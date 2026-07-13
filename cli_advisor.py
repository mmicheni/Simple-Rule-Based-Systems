#!/usr/bin/env python3
"""
CLI User Interface for the Personal Finance Advisor KBS.
Collects user parameters, calculates facts, invokes the engine, and formats outputs.
"""

import json
from engine import FactBase, InferenceEngine

def get_float_input(prompt: str, min_val: float = 0.0) -> float:
    while True:
        try:
            val = float(input(prompt).strip())
            if val < min_val:
                print(f"Value must be at least {min_val}. Please try again.")
                continue
            return val
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def get_bool_input(prompt: str) -> bool:
    while True:
        val = input(prompt).strip().lower()
        if val in ("y", "yes", "true", "t", "1"):
            return True
        if val in ("n", "no", "false", "f", "0"):
            return False
        print("Please enter Yes (y) or No (n).")

def get_choice_input(prompt: str, choices: list) -> str:
    while True:
        val = input(prompt).strip().lower()
        if val in choices:
            return val
        print(f"Invalid choice. Must be one of: {', '.join(choices)}")

def print_header(title: str):
    print("\n" + "=" * 50)
    print(f" {title.upper().center(48)} ")
    print("=" * 50 + "\n")

def run_cli_advisor(kb_path: str = "knowledge_base.json"):
    print_header("Personal Finance Advisor KBS")
    print("This expert system evaluates your budget, emergency fund, debt status,")
    print("and investment profile to provide priority financial recommendations.\n")

    # 1. Gather inputs
    income = get_float_input("Monthly net income ($): ")
    if income == 0:
        print("Income must be greater than zero to evaluate standard rules.")
        return

    essential = get_float_input("Monthly essential expenses (Needs: housing, utilities, groceries, minimum debt) ($): ")
    discretionary = get_float_input("Monthly discretionary expenses (Wants: dining, subscriptions, shopping) ($): ")
    savings_bal = get_float_input("Current emergency fund savings balance ($): ")
    stable_income = get_bool_input("Do you have a stable/predictable source of income? (y/n): ")
    
    total_debt = get_float_input("Total outstanding debt (mortgage, student loans, cards) ($): ")
    high_interest_debt = get_float_input("Of that, how much is high-interest debt (>7% interest, credit cards) ($): ")
    min_debt_payment = get_float_input("Total minimum monthly payments on all debts ($): ")
    
    risk = get_choice_input("What is your risk tolerance for long-term investments? (low/medium/high): ", ["low", "medium", "high"])
    horizon = get_float_input("What is your investment time horizon in years? (e.g., 2, 5, 10): ")

    # 2. Derive base facts
    monthly_savings = income - essential - discretionary
    savings_rate = (monthly_savings / income) * 100
    essential_pct = (essential / income) * 100
    discretionary_pct = (discretionary / income) * 100
    
    # Emergency fund coverage
    if essential > 0:
        ef_months = savings_bal / essential
    else:
        ef_months = 12.0 # default high coverage if expenses are zero
        
    dti = (min_debt_payment / income) * 100
    deficit = abs(monthly_savings) if monthly_savings < 0 else 0.0
    
    # Calculate target emergency fund based on stability
    target_ef_months = 3.0 if stable_income else 6.0
    target_ef = essential * target_ef_months

    facts_dict = {
        "monthly_income": income,
        "essential_expenses": essential,
        "discretionary_expenses": discretionary,
        "monthly_savings": monthly_savings,
        "savings_rate_pct": savings_rate,
        "essential_expenses_pct": essential_pct,
        "discretionary_expenses_pct": discretionary_pct,
        "emergency_fund_balance": savings_bal,
        "emergency_fund_months": ef_months,
        "has_stable_income": stable_income,
        "total_debt": total_debt,
        "high_interest_debt": high_interest_debt,
        "monthly_debt_payments": min_debt_payment,
        "dti_pct": dti,
        "risk_tolerance": risk,
        "investment_horizon_years": horizon,
        "monthly_deficit": deficit,
        "target_emergency_fund": target_ef
    }

    # 3. Load KB and run Inference Engine
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            kb = json.load(f)
    except FileNotFoundError:
        print(f"Error: Knowledge base file '{kb_path}' not found.")
        return

    fb = FactBase(facts_dict)
    engine = InferenceEngine(kb["rules"])
    recs, trace = engine.forward_chain(fb)

    # 4. Display Results
    print_header("Your Financial Analysis")
    
    print(f"📊 Savings Rate: {savings_rate:.1f}% ({'Deficit!' if monthly_savings < 0 else 'Positive cashflow'})")
    print(f"🏠 Budget Breakdown (Needs/Wants/Savings): {essential_pct:.1f}% / {discretionary_pct:.1f}% / {savings_rate:.1f}%")
    print(f"🛡️ Emergency Fund: {ef_months:.1f} months of essential expenses (Balance: ${savings_bal:,.2f})")
    print(f"   (Target for your profile: {target_ef_months:.1f} months = ${target_ef:,.2f})")
    print(f"💳 Debt-to-Income (DTI) Ratio: {dti:.1f}%")
    print(f"🔒 High-Interest Debt: ${high_interest_debt:,.2f}")
    
    print_header("Advisor Recommendations")
    
    if not recs:
        print("✅ The expert system evaluated your profile and found no critical action items. You are in excellent financial shape!")
    else:
        for i, r in enumerate(recs, 1):
            prio_color = {
                "critical": "🚨 [CRITICAL]",
                "high": "⚠️  [HIGH]",
                "medium": "📌 [MEDIUM]",
                "low": "💡 [LOW]"
            }.get(r["priority"], "[INFO]")
            print(f"{i}. {prio_color} {r['message']}")
            print("-" * 50)

    # 5. Optional Explanation Trace
    print()
    explain = get_bool_input("Would you like to view the inference reasoning trace? (y/n): ")
    if explain:
        print_header("Inference Engine Reasoning Path")
        print("Below is the cycle-by-cycle rule activation trace showing HOW the system reached its conclusions:")
        print(f"{'Cycle':<6} | {'Rule ID':<30} | {'Action':<10} | {'Description'}")
        print("-" * 80)
        for t in trace:
            desc = t["description"]
            action_desc = f"{t['action'].upper()}"
            if t["action"] == "derive":
                action_desc += f" ({t['details']['fact']})"
            print(f"{t['cycle']:<6} | {t['rule_id']:<30} | {action_desc:<10} | {desc}")
        print("-" * 80)
        print("\nDerived Facts added during inference:")
        # Find which facts were not in the initial set
        all_facts = fb.all_facts()
        derived_metadata = fb.get_derived_metadata()
        for f_name, cycle_num in derived_metadata.items():
            print(f" - Fact '{f_name}' set to {all_facts[f_name]} in Cycle {cycle_num}")
    
    print("\nThank you for using the Personal Finance Advisor!")

if __name__ == "__main__":
    run_cli_advisor()
