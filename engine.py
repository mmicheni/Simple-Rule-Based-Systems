#!/usr/bin/env python3
"""
Forward-chaining inference engine for the Personal Finance Advisor.
Supports conditions (and, or, not, comparisons) and handles two actions:
- 'derive': adds a new fact to the fact base (enabling subsequent rules to match)
- 'recommend': generates user recommendations with priority and string interpolation
"""

import json
import logging
from typing import Any, Dict, List, Tuple, Union

# Set up logging for rule activation tracking
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class FactBase:
    """Manages the current facts input by the user and derived during inference."""
    def __init__(self, initial_facts: Dict[str, Any] = None):
        self._facts = dict(initial_facts) if initial_facts else {}
        self._derived_in_cycle = {}  # Tracks fact -> cycle_number for explanation

    def set(self, name: str, value: Any, cycle: int = 0):
        """Sets a fact value. Returns True if the fact is new or value changed."""
        if name not in self._facts or self._facts[name] != value:
            self._facts[name] = value
            self._derived_in_cycle[name] = cycle
            return True
        return False

    def get(self, name: str, default: Any = None) -> Any:
        return self._facts.get(name, default)

    def has(self, name: str) -> bool:
        return name in self._facts

    def all_facts(self) -> Dict[str, Any]:
        return dict(self._facts)

    def get_derived_metadata(self) -> Dict[str, int]:
        return dict(self._derived_in_cycle)


class InferenceEngine:
    def __init__(self, kb_rules: List[Dict]):
        self.rules = kb_rules
        self.reset()

    def reset(self):
        self.fired_rules = []  # List of rule IDs that have fired
        self.recommendations = []  # List of triggered recommendations
        self.trace = []  # Execution log of rule firings for explanations

    def evaluate_condition(self, condition: Union[Dict, List], fact_base: FactBase) -> bool:
        """
        Evaluates a condition against the fact base.
        Conditions can be:
        - A single condition: {"fact": "name", "operator": "op", "value": val}
        - An 'and' logical block: {"and": [cond1, cond2, ...]}
        - An 'or' logical block: {"or": [cond1, cond2, ...]}
        - A 'not' logical block: {"not": cond}
        """
        if not isinstance(condition, dict):
            return False

        # Evaluate AND logical block
        if "and" in condition:
            sub_conds = condition["and"]
            if not isinstance(sub_conds, list) or len(sub_conds) == 0:
                return False
            return all(self.evaluate_condition(c, fact_base) for c in sub_conds)

        # Evaluate OR logical block
        if "or" in condition:
            sub_conds = condition["or"]
            if not isinstance(sub_conds, list) or len(sub_conds) == 0:
                return False
            return any(self.evaluate_condition(c, fact_base) for c in sub_conds)

        # Evaluate NOT logical block
        if "not" in condition:
            sub_cond = condition["not"]
            return not self.evaluate_condition(sub_cond, fact_base)

        # Evaluate single condition
        if "fact" in condition and "operator" in condition:
            fact_name = condition["fact"]
            op = condition["operator"]
            target_value = condition["value"]

            # If fact is not present in fact base, evaluate as False (unless checking for != or not existence)
            if not fact_base.has(fact_name):
                # If checking != to something, and we don't have it, it is indeed not equal (in standard logic)
                # But to avoid complications, we assume missing facts make comparison false unless specified.
                if op == "!=":
                    return True
                return False

            fact_value = fact_base.get(fact_name)

            try:
                if op == "==":
                    return fact_value == target_value
                elif op == "!=":
                    return fact_value != target_value
                elif op == ">":
                    return float(fact_value) > float(target_value)
                elif op == "<":
                    return float(fact_value) < float(target_value)
                elif op == ">=":
                    return float(fact_value) >= float(target_value)
                elif op == "<=":
                    return float(fact_value) <= float(target_value)
                else:
                    logging.warning(f"Unknown operator: {op} in rule condition")
                    return False
            except (ValueError, TypeError):
                # If numerical casting fails, fallback to string/direct comparison or return False
                return False

        return False

    def forward_chain(self, fact_base: FactBase) -> Tuple[List[Dict], List[Dict]]:
        """
        Runs the forward-chaining loop.
        Fires rules to derive facts and append recommendations until no new facts are derived.
        Returns:
            recommendations: List of recommend actions that fired
            trace: List of trace statements describing the inference steps
        """
        self.reset()
        cycle = 1
        max_cycles = 100  # Avoid infinite loops in case of circular rules

        while cycle <= max_cycles:
            fact_added_in_cycle = False
            rules_fired_in_cycle = 0

            for rule in self.rules:
                rule_id = rule["id"]
                if rule_id in self.fired_rules:
                    continue  # Skip rules that have already fired

                # Check if rule matches facts
                if self.evaluate_condition(rule["if"], fact_base):
                    self.fired_rules.append(rule_id)
                    rules_fired_in_cycle += 1
                    then_clause = rule["then"]
                    action_type = then_clause["action"]

                    # Log the activation details for tracing
                    self.trace.append({
                        "cycle": cycle,
                        "rule_id": rule_id,
                        "description": rule.get("description", ""),
                        "category": rule.get("category", "General"),
                        "action": action_type,
                        "details": then_clause
                    })

                    if action_type == "derive":
                        fact_name = then_clause["fact"]
                        fact_val = then_clause["value"]
                        # Set fact and check if it actually changed
                        if fact_base.set(fact_name, fact_val, cycle=cycle):
                            fact_added_in_cycle = True
                            logging.info(f"[Cycle {cycle}] Rule '{rule_id}' fired: derived fact '{fact_name}' = {fact_val}")

                    elif action_type == "recommend":
                        raw_msg = then_clause["message"]
                        priority = then_clause.get("priority", "medium")
                        
                        # Interpolate values from fact base into recommendation message
                        try:
                            msg = raw_msg.format(**fact_base.all_facts())
                        except Exception as e:
                            logging.warning(f"Interpolation failed for rule '{rule_id}': {e}. Using raw message.")
                            msg = raw_msg

                        rec = {
                            "rule_id": rule_id,
                            "category": rule.get("category", "General"),
                            "priority": priority,
                            "message": msg
                        }
                        self.recommendations.append(rec)
                        logging.info(f"[Cycle {cycle}] Rule '{rule_id}' fired: recommended '{priority}' priority advisory.")

            # If no new facts were derived in this cycle, we have reached a fixed point
            if not fact_added_in_cycle:
                break

            cycle += 1

        # Sort recommendations by priority (critical > high > medium > low)
        priority_map = {"critical": 1, "high": 2, "medium": 3, "low": 4}
        self.recommendations.sort(key=lambda r: priority_map.get(r["priority"], 9))

        return self.recommendations, self.trace


if __name__ == "__main__":
    # Quick sanity check
    with open("knowledge_base.json", "r") as f:
        kb = json.load(f)

    # Mock user input
    # Needs: 3500, Wants: 1200, Income: 5000, Savings: 300, Stable Income, No emergency fund, High interest debt
    # income: 5000
    # essential: 3500 (70% of income - high needs!)
    # discretionary: 1200 (24% of income)
    # monthly_savings: 300 (savings rate: 6% - low!)
    # emergency fund balance: 500 (emergency_fund_months: 500 / 3500 = 0.14 - very low!)
    # high interest debt: 4000
    # dti: (300 minimum payments / 5000) = 6%
    facts_data = {
        "monthly_income": 5000.0,
        "essential_expenses": 3500.0,
        "discretionary_expenses": 1200.0,
        "monthly_savings": 300.0,
        "savings_rate_pct": 6.0,
        "essential_expenses_pct": 70.0,
        "discretionary_expenses_pct": 24.0,
        "emergency_fund_balance": 500.0,
        "emergency_fund_months": 0.14,
        "has_stable_income": True,
        "monthly_debt_payments": 300.0,
        "dti_pct": 6.0,
        "total_debt": 10000.0,
        "high_interest_debt": 4000.0,
        "risk_tolerance": "medium",
        "investment_horizon_years": 5.0,
        "monthly_deficit": 0.0,
        "target_emergency_fund": 10500.0 # 3 * 3500
    }

    fb = FactBase(facts_data)
    engine = InferenceEngine(kb["rules"])
    recs, trace = engine.forward_chain(fb)

    print("\n--- RECOMMENDED ACTIONS ---")
    for r in recs:
        print(f"[{r['category']} - {r['priority'].upper()}] {r['message']}")

    print("\n--- EXPLANATION TRACE ---")
    for t in trace:
        print(f"Cycle {t['cycle']} | Rule '{t['rule_id']}' fired. Category: {t['category']} | Action: {t['action']}")
