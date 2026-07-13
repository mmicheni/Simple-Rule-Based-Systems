#!/usr/bin/env python3
"""
Flask web server for the Personal Finance Advisor.
Exposes pages and REST API endpoints for evaluation and knowledge acquisition.
"""

import os
import json
import logging
from flask import Flask, jsonify, render_template, request
from engine import FactBase, InferenceEngine
from acquisition import load_kb, save_kb, validate_rule

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

KB_PATH = "knowledge_base.json"

@app.route("/")
def index():
    """Renders the main SPA dashboard."""
    return render_template("index.html")

@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    """
    Evaluates user financial profile.
    Accepts JSON input, computes facts, runs the rules engine,
    and returns recommendations, metrics, and trace explanation.
    """
    try:
        data = request.json or {}
        
        # Extract inputs with defaults
        income = float(data.get("monthly_income", 0.0))
        essential = float(data.get("essential_expenses", 0.0))
        discretionary = float(data.get("discretionary_expenses", 0.0))
        savings_bal = float(data.get("emergency_fund_balance", 0.0))
        stable_income = bool(data.get("has_stable_income", True))
        
        total_debt = float(data.get("total_debt", 0.0))
        high_interest_debt = float(data.get("high_interest_debt", 0.0))
        min_debt_payment = float(data.get("monthly_debt_payments", 0.0))
        
        risk = str(data.get("risk_tolerance", "medium")).lower()
        if risk not in ("low", "medium", "high"):
            risk = "medium"
        horizon = float(data.get("investment_horizon_years", 5.0))

        # Handle zero income edge case
        if income <= 0:
            return jsonify({
                "success": False,
                "error": "Monthly income must be greater than zero."
            }), 400

        # Compute intermediate facts
        monthly_savings = income - essential - discretionary
        savings_rate = (monthly_savings / income) * 100
        essential_pct = (essential / income) * 100
        discretionary_pct = (discretionary / income) * 100
        
        ef_months = savings_bal / essential if essential > 0 else 12.0
        dti = (min_debt_payment / income) * 100
        deficit = abs(monthly_savings) if monthly_savings < 0 else 0.0
        
        target_ef_months = 3.0 if stable_income else 6.0
        target_ef = essential * target_ef_months

        # Pack facts into fact base
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

        # Load KB
        kb = load_kb(KB_PATH)
        fb = FactBase(facts_dict)
        engine = InferenceEngine(kb["rules"])
        recs, trace = engine.forward_chain(fb)

        # Build response payload
        payload = {
            "success": True,
            "metrics": {
                "monthly_savings": monthly_savings,
                "savings_rate_pct": savings_rate,
                "essential_expenses_pct": essential_pct,
                "discretionary_expenses_pct": discretionary_pct,
                "emergency_fund_months": ef_months,
                "dti_pct": dti,
                "target_emergency_fund_months": target_ef_months,
                "target_emergency_fund": target_ef,
                "has_deficit": monthly_savings < 0
            },
            "recommendations": recs,
            "trace": trace,
            "facts": fb.all_facts()
        }
        return jsonify(payload)

    except Exception as e:
        logging.error(f"Error during financial evaluation: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route("/api/rules", methods=["GET"])
def get_rules():
    """Serves the active list of rules in the KB."""
    try:
        kb = load_kb(KB_PATH)
        return jsonify({
            "success": True,
            "rules": kb.get("rules", [])
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/rules/add", methods=["POST"])
def add_rule():
    """
    Validates and appends a new rule to the knowledge base.
    """
    try:
        new_rule = request.json or {}
        
        # Load active KB
        kb = load_kb(KB_PATH)
        
        # Validate rule structure and constraints (syntax, duplicates, cycle checks)
        is_valid, msg = validate_rule(new_rule, kb.get("rules", []))
        
        if not is_valid:
            return jsonify({
                "success": False,
                "error": msg
            }), 400

        # Save back to JSON
        kb["rules"].append(new_rule)
        save_kb(kb, KB_PATH)
        
        logging.info(f"Successfully added rule '{new_rule['id']}' to KB.")
        return jsonify({
            "success": True,
            "message": "Rule successfully validated and saved."
        })

    except Exception as e:
        logging.error(f"Error while adding rule: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
