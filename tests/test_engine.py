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
    def test_circular_dependency_detection(self):
        # Setup rules that create circular references: A -> B, B -> A
        rules = [
            {
                "id": "rule_a_to_b",
                "if": {"fact": "fact_a", "operator": "==", "value": True},
                "then": {"action": "derive", "fact": "fact_b", "value": True}
            }
        ]
        
        # Validate that adding a rule deriving A from B is flagged as circular
        new_rule = {
            "id": "rule_b_to_a",
            "category": "Test",
            "description": "Circularity test",
            "if": {"fact": "fact_b", "operator": "==", "value": True},
            "then": {"action": "derive", "fact": "fact_a", "value": True}
        }
        
        # 1. Build graph
        graph = build_dependency_graph(rules + [new_rule])
        # Expected graph: {'fact_a': {'fact_b'}, 'fact_b': {'fact_a'}}
        self.assertTrue(has_cycle(graph))
        
        # 2. Check validate_rule returns False for circularity
        is_valid, msg = validate_rule(new_rule, rules)
        self.assertFalse(is_valid)
        self.assertIn("Circular dependency detected", msg)

if __name__ == "__main__":
    unittest.main()
