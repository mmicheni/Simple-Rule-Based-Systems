#!/usr/bin/env python3
"""
Knowledge Acquisition module for the Personal Finance Advisor.
Enables adding, validating, and managing rules stored in knowledge_base.json.
Features:
- Rule validation (syntax checks, checking operators)
- Circular dependency detection between derived facts
- Duplicate rule check
- Interactive CLI for rule acquisition
"""

import json
from typing import Dict, List, Set, Tuple

def load_kb(kb_path: str = "knowledge_base.json") -> Dict:
    with open(kb_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_kb(kb: Dict, kb_path: str = "knowledge_base.json"):
    with open(kb_path, "w", encoding="utf-8") as f:
        json.dump(kb, f, indent=2)

def extract_facts_from_condition(condition: Dict) -> Set[str]:
    """Recursively extracts all facts referenced in a condition."""
    facts = set()
    if not isinstance(condition, dict):
        return facts

    if "and" in condition:
        for cond in condition["and"]:
            facts.update(extract_facts_from_condition(cond))
    elif "or" in condition:
        for cond in condition["or"]:
            facts.update(extract_facts_from_condition(cond))
    elif "not" in condition:
        facts.update(extract_facts_from_condition(condition["not"]))
    elif "fact" in condition:
        facts.add(condition["fact"])

    return facts

def build_dependency_graph(rules: List[Dict]) -> Dict[str, Set[str]]:
    """
    Builds a directed dependency graph where:
    Key: Fact name
    Value: Set of facts that depend on this fact (i.e. Source Fact -> Target Fact)
    If Rule R has "if: A and B" and "then: derive C", then C depends on A and B (edges A->C and B->C).
    """
    graph = {}
    for rule in rules:
        then_clause = rule.get("then", {})
        if then_clause.get("action") == "derive":
            target_fact = then_clause.get("fact")
            if not target_fact:
                continue

            sources = extract_facts_from_condition(rule.get("if", {}))
            for source in sources:
                if source not in graph:
                    graph[source] = set()
                graph[source].add(target_fact)
    return graph

def has_cycle(graph: Dict[str, Set[str]]) -> bool:
    """Uses DFS to check for cycles in a directed graph."""
    visited = {}  # 0 = unvisited, 1 = visiting, 2 = fully visited

    def dfs(node: str) -> bool:
        visited[node] = 1  # visiting
        for neighbor in graph.get(node, []):
            if visited.get(neighbor, 0) == 1:
                return True  # Found a back edge / cycle!
            if visited.get(neighbor, 0) == 0:
                if dfs(neighbor):
                    return True
        visited[node] = 2  # fully visited
        return False

    # Perform DFS starting from each node
    all_nodes = set(graph.keys())
    for val in graph.values():
        all_nodes.update(val)

    for node in all_nodes:
        if visited.get(node, 0) == 0:
            if dfs(node):
                return True
    return False

def validate_rule(rule: Dict, existing_rules: List[Dict]) -> Tuple[bool, str]:
    """
    Validates a rule for syntax correctness, duplicate entries, and circular dependencies.
    """
    # 1. Basic Structure Validation
    required_keys = {"id", "category", "description", "if", "then"}
    if not all(k in rule for k in required_keys):
        return False, f"Rule is missing one or more required keys: {required_keys}"

    rule_id = rule["id"].strip()
    if not rule_id:
        return False, "Rule ID cannot be empty."

    # Check for duplicate ID
    if any(r["id"] == rule_id for r in existing_rules):
        return False, f"Rule ID '{rule_id}' already exists."

    # 2. Condition Validation
    if_cond = rule["if"]
    if not isinstance(if_cond, dict):
        return False, "'if' clause must be a dictionary."

    def validate_condition_syntax(cond: Dict) -> Tuple[bool, str]:
        if "and" in cond:
            if not isinstance(cond["and"], list):
                return False, "'and' clause must contain a list of conditions."
            for sub in cond["and"]:
                ok, err = validate_condition_syntax(sub)
                if not ok: return False, err
        elif "or" in cond:
            if not isinstance(cond["or"], list):
                return False, "'or' clause must contain a list of conditions."
            for sub in cond["or"]:
                ok, err = validate_condition_syntax(sub)
                if not ok: return False, err
        elif "not" in cond:
            if not isinstance(cond["not"], dict):
                return False, "'not' clause must contain a single condition dictionary."
            return validate_condition_syntax(cond["not"])
        elif "fact" in cond:
            if "operator" not in cond or "value" not in cond:
                return False, "Fact condition must contain 'operator' and 'value'."
            valid_ops = {"==", "!=", ">", "<", ">=", "<="}
            if cond["operator"] not in valid_ops:
                return False, f"Invalid operator '{cond['operator']}'. Must be one of {valid_ops}"
        else:
            return False, "Condition must contain 'and', 'or', 'not', or 'fact'."
        return True, ""

    ok, err = validate_condition_syntax(if_cond)
    if not ok:
        return False, f"Condition error: {err}"

    # 3. Action Validation
    then_clause = rule["then"]
    if not isinstance(then_clause, dict):
        return False, "'then' clause must be a dictionary."
    if "action" not in then_clause:
        return False, "'then' clause must contain an 'action'."

    action = then_clause["action"]
    if action == "derive":
        if "fact" not in then_clause or "value" not in then_clause:
            return False, "Derive action must contain 'fact' and 'value'."
    elif action == "recommend":
        if "message" not in then_clause:
            return False, "Recommend action must contain a 'message'."
    else:
        return False, f"Unknown action type '{action}'. Must be 'derive' or 'recommend'."

    # 4. Circular Dependency Validation (for derive actions)
    if action == "derive":
        temp_rules = existing_rules + [rule]
        graph = build_dependency_graph(temp_rules)
        if has_cycle(graph):
            return False, "Circular dependency detected! This rule would create a cycle in derived facts."

    return True, "Valid"

def acquire_rule_interactive() -> Dict:
    """Guided interactive terminal prompt to build a new financial rule."""
    print("\n==========================================")
    print("      KNOWLEDGE ACQUISITION INTERFACE     ")
    print("==========================================\n")
    
    rule_id = input("1. Enter a unique rule ID (e.g. rec_high_rent): ").strip()
    category = input("2. Enter category (Budgeting/Saving/Emergency Fund/Debt Management/Investment): ").strip()
    description = input("3. Enter a brief description: ").strip()

    print("\n--- Define Rule Condition (IF) ---")
    print("For simplicity, we will create a single condition: [Fact] [Operator] [Value]")
    fact = input("Enter fact name (e.g. savings_rate_pct, emergency_fund_months): ").strip()
    op = input("Enter operator (==, !=, >, <, >=, <=): ").strip()
    val_str = input("Enter threshold value (can be a number like 20.0 or a boolean like true/false): ").strip()
    
    # Try to cast value appropriately
    if val_str.lower() == "true":
        value = True
    elif val_str.lower() == "false":
        value = False
    else:
        try:
            value = float(val_str)
        except ValueError:
            value = val_str

    if_cond = {
        "fact": fact,
        "operator": op,
        "value": value
    }

    print("\n--- Define Rule Action (THEN) ---")
    print("Choose action type:")
    print("1. Derive a new fact (e.g., set 'is_ready_to_invest' = True)")
    print("2. Make a recommendation to the user")
    action_choice = input("Choice (1 or 2): ").strip()

    if action_choice == "1":
        derive_fact = input("Enter derived fact name: ").strip()
        derive_val_str = input("Enter value to set (e.g. true): ").strip()
        if derive_val_str.lower() == "true":
            derive_value = True
        elif derive_val_str.lower() == "false":
            derive_value = False
        else:
            try:
                derive_value = float(derive_val_str)
            except ValueError:
                derive_value = derive_val_str

        then_clause = {
            "action": "derive",
            "fact": derive_fact,
            "value": derive_value
        }
    else:
        priority = input("Enter priority (critical/high/medium/low): ").strip().lower()
        message = input("Enter recommendations text (you can include fact variables in braces, e.g. {savings_rate_pct:.1f}%): ").strip()
        then_clause = {
            "action": "recommend",
            "priority": priority,
            "message": message
        }

    return {
        "id": rule_id,
        "category": category,
        "description": description,
        "if": if_cond,
        "then": then_clause
    }

def run_acquisition_flow():
    kb_path = "knowledge_base.json"
    kb = load_kb(kb_path)
    
    new_rule = acquire_rule_interactive()
    
    ok, err = validate_rule(new_rule, kb["rules"])
    if not ok:
        print(f"\n❌ Rule Validation Failed: {err}")
        return

    print("\n✅ Rule validation passed successfully!")
    confirm = input("Save this rule to the knowledge base? (y/n): ").strip().lower()
    if confirm == "y":
        kb["rules"].append(new_rule)
        save_kb(kb, kb_path)
        print("🎉 Rule saved successfully to knowledge_base.json!")
    else:
        print("Save cancelled.")

if __name__ == "__main__":
    run_acquisition_flow()
