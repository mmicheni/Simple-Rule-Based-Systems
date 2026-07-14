#!/usr/bin/env python3
"""
Unit tests for the Personal Finance Advisor KBS Engine and Acquisition modules.
Runs logic tests to verify correct forward-chaining and graph cycle detection.
"""

import sys
import os
import unittest

# Append workspace directory to system path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import FactBase, InferenceEngine
from acquisition import validate_rule, build_dependency_graph, has_cycle

class TestFactBase(unittest.TestCase):
    def test_set_and_get(self):
        fb = FactBase({"a": 1})
        self.assertEqual(fb.get("a"), 1)
        self.assertFalse(fb.has("b"))
        
        # Setting a new fact returns True
        self.assertTrue(fb.set("b", 2, cycle=1))
        self.assertEqual(fb.get("b"), 2)
        
        # Setting same value returns False
        self.assertFalse(fb.set("b", 2, cycle=1))
        
        # Setting different value returns True
        self.assertTrue(fb.set("b", 3, cycle=2))
        self.assertEqual(fb.get("b"), 3)


class TestInferenceEngine(unittest.TestCase):
    def setUp(self):
        self.rules = [
            {
                "id": "rule_1",
                "category": "Test",
                "description": "Derive fact_b if fact_a is true",
                "if": {"fact": "fact_a", "operator": "==", "value": True},
                "then": {"action": "derive", "fact": "fact_b", "value": True}
            },
            {
                "id": "rule_2",
                "category": "Test",
                "description": "Recommend target if fact_b is true",
                "if": {"fact": "fact_b", "operator": "==", "value": True},
                "then": {"action": "recommend", "priority": "high", "message": "Recommendation success!"}
            }
        ]
        self.engine = InferenceEngine(self.rules)

    def test_evaluate_condition_comparisons(self):
        fb = FactBase({"x": 10, "y": 5, "name": "Alice"})
        
        # Numeric comparisons
        self.assertTrue(self.engine.evaluate_condition({"fact": "x", "operator": ">", "value": 5}, fb))
        self.assertFalse(self.engine.evaluate_condition({"fact": "x", "operator": "<", "value": 5}, fb))
        self.assertTrue(self.engine.evaluate_condition({"fact": "y", "operator": "<=", "value": 5}, fb))
        self.assertTrue(self.engine.evaluate_condition({"fact": "x", "operator": "!=", "value": 5}, fb))
        self.assertTrue(self.engine.evaluate_condition({"fact": "name", "operator": "==", "value": "Alice"}, fb))
        
        # Missing fact evaluations
        self.assertFalse(self.engine.evaluate_condition({"fact": "z", "operator": "==", "value": 1}, fb))
        self.assertTrue(self.engine.evaluate_condition({"fact": "z", "operator": "!=", "value": 1}, fb))

    def test_evaluate_condition_logical(self):
        fb = FactBase({"a": True, "b": False})
        
        # AND evaluation
        self.assertTrue(self.engine.evaluate_condition({"and": [{"fact": "a", "operator": "==", "value": True}]}, fb))
        self.assertFalse(self.engine.evaluate_condition({"and": [
            {"fact": "a", "operator": "==", "value": True},
            {"fact": "b", "operator": "==", "value": True}
        ]}, fb))
        
        # OR evaluation
        self.assertTrue(self.engine.evaluate_condition({"or": [
            {"fact": "a", "operator": "==", "value": True},
            {"fact": "b", "operator": "==", "value": True}
        ]}, fb))
        
        # NOT evaluation
        self.assertTrue(self.engine.evaluate_condition({"not": {"fact": "b", "operator": "==", "value": True}}, fb))

    def test_forward_chaining(self):
        # Initial fact: only fact_a is True
        fb = FactBase({"fact_a": True})
        
        recs, trace = self.engine.forward_chain(fb)
        
        # Check that fact_b was derived (Cycle 1) and recommendation triggered (Cycle 2)
        self.assertTrue(fb.get("fact_b"))
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["rule_id"], "rule_2")
        self.assertEqual(recs[0]["message"], "Recommendation success!")
        
        self.assertEqual(len(trace), 2)
        self.assertEqual(trace[0]["rule_id"], "rule_1")
        self.assertEqual(trace[1]["rule_id"], "rule_2")


class TestKnowledgeAcquisition(unittest.TestCase):
    def setUp(self):
        """A minimal set of existing rules to test validation against."""
        self.existing_rules = [
            {
                "id": "existing_rule_1",
                "category": "Budgeting",
                "description": "An existing rule",
                "if": {"fact": "savings_rate_pct", "operator": "<", "value": 0.0},
                "then": {"action": "derive", "fact": "is_in_deficit", "value": True}
            }
        ]

    def _make_valid_rec_rule(self, rule_id="new_rec_rule"):
        """Helper to create a syntactically valid recommend rule."""
        return {
            "id": rule_id,
            "category": "Budgeting",
            "description": "A valid recommendation rule",
            "if": {"fact": "savings_rate_pct", "operator": ">=", "value": 20.0},
            "then": {
                "action": "recommend",
                "priority": "low",
                "message": "Great savings rate of {savings_rate_pct:.1f}%!"
            }
        }

    def _make_valid_derive_rule(self, rule_id="new_derive_rule"):
        """Helper to create a syntactically valid derive rule."""
        return {
            "id": rule_id,
            "category": "Investment",
            "description": "A valid derive rule",
            "if": {"fact": "dti_pct", "operator": "<", "value": 36.0},
            "then": {"action": "derive", "fact": "has_healthy_dti", "value": True}
        }

    # --- 1. Circular Dependency Tests ---

    def test_circular_dependency_detection(self):
        """Adding a rule that creates a dependency loop (A->B, B->A) should fail."""
        rules = [
            {
                "id": "rule_a_to_b",
                "if": {"fact": "fact_a", "operator": "==", "value": True},
                "then": {"action": "derive", "fact": "fact_b", "value": True}
            }
        ]
        new_rule = {
            "id": "rule_b_to_a",
            "category": "Test",
            "description": "Circularity test",
            "if": {"fact": "fact_b", "operator": "==", "value": True},
            "then": {"action": "derive", "fact": "fact_a", "value": True}
        }

        graph = build_dependency_graph(rules + [new_rule])
        self.assertTrue(has_cycle(graph))

        is_valid, msg = validate_rule(new_rule, rules)
        self.assertFalse(is_valid)
        self.assertIn("Circular dependency detected", msg)

    def test_no_cycle_in_valid_chain(self):
        """A linear chain A->B->C should NOT be flagged as circular."""
        rules = [
            {
                "id": "r1",
                "if": {"fact": "fact_a", "operator": "==", "value": True},
                "then": {"action": "derive", "fact": "fact_b", "value": True}
            },
            {
                "id": "r2",
                "if": {"fact": "fact_b", "operator": "==", "value": True},
                "then": {"action": "derive", "fact": "fact_c", "value": True}
            }
        ]
        graph = build_dependency_graph(rules)
        self.assertFalse(has_cycle(graph))

    # --- 2. Missing Required Keys Tests ---

    def test_missing_required_key_id(self):
        """A rule without 'id' should fail validation."""
        rule = self._make_valid_rec_rule()
        del rule["id"]
        is_valid, msg = validate_rule(rule, self.existing_rules)
        self.assertFalse(is_valid)
        self.assertIn("missing", msg.lower())

    def test_missing_required_key_category(self):
        """A rule without 'category' should fail validation."""
        rule = self._make_valid_rec_rule()
        del rule["category"]
        is_valid, msg = validate_rule(rule, self.existing_rules)
        self.assertFalse(is_valid)

    def test_missing_required_key_description(self):
        """A rule without 'description' should fail validation."""
        rule = self._make_valid_rec_rule()
        del rule["description"]
        is_valid, msg = validate_rule(rule, self.existing_rules)
        self.assertFalse(is_valid)

    def test_missing_required_key_if(self):
        """A rule without 'if' should fail validation."""
        rule = self._make_valid_rec_rule()
        del rule["if"]
        is_valid, msg = validate_rule(rule, self.existing_rules)
        self.assertFalse(is_valid)

    def test_missing_required_key_then(self):
        """A rule without 'then' should fail validation."""
        rule = self._make_valid_rec_rule()
        del rule["then"]
        is_valid, msg = validate_rule(rule, self.existing_rules)
        self.assertFalse(is_valid)

    # --- 3. Duplicate Rule ID Tests ---

    def test_duplicate_rule_id_rejected(self):
        """A rule whose ID already exists in the KB should be rejected."""
        rule = self._make_valid_rec_rule(rule_id="existing_rule_1")
        is_valid, msg = validate_rule(rule, self.existing_rules)
        self.assertFalse(is_valid)
        self.assertIn("already exists", msg)

    def test_unique_rule_id_accepted(self):
        """A rule with a brand-new unique ID should pass the duplicate check."""
        rule = self._make_valid_rec_rule(rule_id="brand_new_unique_rule")
        is_valid, msg = validate_rule(rule, self.existing_rules)
        self.assertTrue(is_valid, f"Expected valid, got: {msg}")

    def test_empty_rule_id_rejected(self):
        """A rule with an empty string as its ID should be rejected."""
        rule = self._make_valid_rec_rule(rule_id="   ")
        is_valid, msg = validate_rule(rule, self.existing_rules)
        self.assertFalse(is_valid)
        self.assertIn("empty", msg.lower())

    # --- 4. Invalid Operator Tests ---

    def test_invalid_operator_rejected(self):
        """A condition using an unsupported operator (e.g. '=>') should fail."""
        rule = self._make_valid_rec_rule()
        rule["if"]["operator"] = "=>"
        is_valid, msg = validate_rule(rule, self.existing_rules)
        self.assertFalse(is_valid)
        self.assertIn("Invalid operator", msg)

    def test_all_valid_operators_accepted(self):
        """Each of the six supported comparison operators should pass validation."""
        valid_ops = ["==", "!=", ">", "<", ">=", "<="]
        for i, op in enumerate(valid_ops):
            rule = self._make_valid_rec_rule(rule_id=f"op_test_rule_{i}")
            rule["if"]["operator"] = op
            is_valid, msg = validate_rule(rule, self.existing_rules)
            self.assertTrue(is_valid, f"Operator '{op}' should be valid, got: {msg}")

    # --- 5. Malformed Action Structure Tests ---

    def test_recommend_action_missing_message_rejected(self):
        """A 'recommend' action without a 'message' key should be rejected."""
        rule = self._make_valid_rec_rule()
        del rule["then"]["message"]
        is_valid, msg = validate_rule(rule, self.existing_rules)
        self.assertFalse(is_valid)
        self.assertIn("message", msg.lower())

    def test_derive_action_missing_fact_rejected(self):
        """A 'derive' action without a 'fact' key should be rejected."""
        rule = self._make_valid_derive_rule()
        del rule["then"]["fact"]
        is_valid, msg = validate_rule(rule, self.existing_rules)
        self.assertFalse(is_valid)

    def test_derive_action_missing_value_rejected(self):
        """A 'derive' action without a 'value' key should be rejected."""
        rule = self._make_valid_derive_rule()
        del rule["then"]["value"]
        is_valid, msg = validate_rule(rule, self.existing_rules)
        self.assertFalse(is_valid)

    def test_unknown_action_type_rejected(self):
        """A 'then' clause with an unsupported action type should be rejected."""
        rule = self._make_valid_rec_rule()
        rule["then"]["action"] = "alert"
        is_valid, msg = validate_rule(rule, self.existing_rules)
        self.assertFalse(is_valid)
        self.assertIn("Unknown action type", msg)

    # --- 6. Valid Full Rules (Positive Checks) ---

    def test_fully_valid_recommend_rule_accepted(self):
        """A fully correct recommend rule should pass all validation checks."""
        rule = self._make_valid_rec_rule()
        is_valid, msg = validate_rule(rule, self.existing_rules)
        self.assertTrue(is_valid, f"Expected valid rule, got: {msg}")

    def test_fully_valid_derive_rule_accepted(self):
        """A fully correct derive rule should pass all validation checks."""
        rule = self._make_valid_derive_rule()
        is_valid, msg = validate_rule(rule, self.existing_rules)
        self.assertTrue(is_valid, f"Expected valid rule, got: {msg}")

if __name__ == "__main__":
    unittest.main()
