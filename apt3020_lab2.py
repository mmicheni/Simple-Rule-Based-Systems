"""
APT 3020 – Knowledge-Based Systems
Lab 2: Reasoning and Inferencing Engine for a Student Academic Advisor
University: United States International University – Africa
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tasks covered:
  Task 1  – Knowledge Representation   (JSON embedded + Python dict)
  Task 2  – Reasoning Engine           (Forward Chaining)
  Task 3  – Forward Chaining Demo      (3 student profiles)
  Task 4  – Explanation Facility
  Bonus   – Backward Chaining + comparison
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import sys

# ════════════════════════════════════════════════════════
# TASK 1 – KNOWLEDGE REPRESENTATION
# ════════════════════════════════════════════════════════

# ── JSON representation (embedded) ──────────────────────
KNOWLEDGE_BASE_JSON = json.loads("""
{
  "facts_schema": {
    "description": "Possible attributes a student may have",
    "gpa_categories":        ["GPA Above 3.5", "GPA Between 3.0–3.49", "GPA Below 3.0"],
    "attendance_categories": ["Attendance Above 80%", "Attendance Below 80%"],
    "disciplinary_status":   ["No Disciplinary Cases", "Has Disciplinary Cases"],
    "academic_status":       ["Completed Prerequisite Courses", "Not Completed Prerequisites"],
    "financial_status":      ["Has Outstanding Fees", "No Outstanding Fees"]
  },
  "rules": [
    {
      "id": "R1", "name": "Scholarship Rule",
      "conditions":        {"gpa_above": 3.5, "attendance_above": 80, "no_disciplinary_cases": true},
      "condition_labels":  ["GPA > 3.5", "Attendance > 80%", "No disciplinary cases"],
      "conclusion":        "Eligible for Scholarship"
    },
    {
      "id": "R2", "name": "Graduation Rule",
      "conditions":        {"gpa_above": 3.0, "completed_prerequisites": true, "no_outstanding_fees": true},
      "condition_labels":  ["GPA > 3.0", "Completed Prerequisite Courses", "No outstanding fees"],
      "conclusion":        "Eligible for Graduation"
    },
    {
      "id": "R3", "name": "Probation Rule",
      "conditions":        {"gpa_below": 3.0},
      "condition_labels":  ["GPA < 3.0"],
      "conclusion":        "Academic Probation"
    },
    {
      "id": "R4", "name": "Registration Block Rule",
      "conditions":        {"has_outstanding_fees": true},
      "condition_labels":  ["Has outstanding fees"],
      "conclusion":        "Registration Blocked"
    },
    {
      "id": "R5", "name": "Dean's List Rule",
      "conditions":        {"gpa_above": 3.5, "attendance_above": 80},
      "condition_labels":  ["GPA > 3.5", "Attendance > 80%"],
      "conclusion":        "Dean's List Candidate"
    }
  ],
  "possible_conclusions": [
    "Eligible for Scholarship",
    "Eligible for Graduation",
    "Academic Probation",
    "Registration Blocked",
    "Dean's List Candidate"
  ]
}
""")

# ── Python dict representation ───────────────────────────
KNOWLEDGE_BASE = {
    "rules": [
        {
            "id":               "R1",
            "name":             "Scholarship Rule",
            "conditions":       lambda f: f["gpa"] > 3.5 and f["attendance"] > 80 and not f["disciplinary_cases"],
            "condition_labels": ["GPA > 3.5", "Attendance > 80%", "No disciplinary cases"],
            "conclusion":       "Eligible for Scholarship",
        },
        {
            "id":               "R2",
            "name":             "Graduation Rule",
            "conditions":       lambda f: f["gpa"] > 3.0 and f["completed_prerequisites"] and not f["outstanding_fees"],
            "condition_labels": ["GPA > 3.0", "Completed Prerequisite Courses", "No outstanding fees"],
            "conclusion":       "Eligible for Graduation",
        },
        {
            "id":               "R3",
            "name":             "Probation Rule",
            "conditions":       lambda f: f["gpa"] < 3.0,
            "condition_labels": ["GPA < 3.0"],
            "conclusion":       "Academic Probation",
        },
        {
            "id":               "R4",
            "name":             "Registration Block Rule",
            "conditions":       lambda f: f["outstanding_fees"],
            "condition_labels": ["Has outstanding fees"],
            "conclusion":       "Registration Blocked",
        },
        {
            "id":               "R5",
            "name":             "Dean's List Rule",
            "conditions":       lambda f: f["gpa"] > 3.5 and f["attendance"] > 80,
            "condition_labels": ["GPA > 3.5", "Attendance > 80%"],
            "conclusion":       "Dean's List Candidate",
        },
    ]
}

# ════════════════════════════════════════════════════════
# TERMINAL COLOURS
# ════════════════════════════════════════════════════════
RESET  = "\033[0m";  BOLD   = "\033[1m";  DIM  = "\033[2m"
GREEN  = "\033[92m"; RED    = "\033[91m"; CYAN = "\033[96m"
YELLOW = "\033[93m"; PURPLE = "\033[95m"; BLUE = "\033[94m"


# ════════════════════════════════════════════════════════
# TASK 2 – REASONING ENGINE: FORWARD CHAINING
# ════════════════════════════════════════════════════════

def forward_chaining(facts: dict) -> list[dict]:
    """
    Forward Chaining Inference Engine.
    Evaluates every rule against the working memory (facts).
    Fires all rules whose conditions are fully satisfied.
    Returns a list of triggered rule result dicts.
    """
    triggered = []
    for rule in KNOWLEDGE_BASE["rules"]:
        if rule["conditions"](facts):
            triggered.append({
                "rule_id":        rule["id"],
                "rule_name":      rule["name"],
                "conditions_met": rule["condition_labels"],
                "conclusion":     rule["conclusion"],
            })
    return triggered


# ════════════════════════════════════════════════════════
# BONUS – BACKWARD CHAINING
# ════════════════════════════════════════════════════════

def backward_chaining(goal: str, facts: dict) -> dict:
    """
    Backward Chaining Inference Engine.
    Starts from a goal conclusion, finds the matching rule,
    then checks whether the required conditions are satisfied.
    """
    for rule in KNOWLEDGE_BASE["rules"]:
        if rule["conclusion"] == goal:
            achieved = rule["conditions"](facts)
            return {
                "goal":               goal,
                "rule_id":            rule["id"],
                "rule_name":          rule["name"],
                "conditions_checked": rule["condition_labels"],
                "goal_achieved":      achieved,
                "verdict":            (f"{GREEN}✓ PROVED{RESET}:   {goal}"
                                       if achieved else
                                       f"{RED}✗ UNPROVED{RESET}: {goal}"),
            }
    return {
        "goal":          goal,
        "goal_achieved": False,
        "verdict":       f"{RED}✗ No rule found for goal:{RESET} {goal}",
    }


# ════════════════════════════════════════════════════════
# TASK 4 – EXPLANATION FACILITY
# ════════════════════════════════════════════════════════

def explain(student_name: str, facts: dict, results: list[dict]) -> None:
    """Prints a human-readable explanation of every triggered conclusion."""
    print(f"\n{CYAN}{'═'*62}{RESET}")
    print(f"{CYAN}{BOLD}  EXPLANATION REPORT  –  {student_name.upper()}{RESET}")
    print(f"{CYAN}{'═'*62}{RESET}")

    print(f"\n{BOLD}📋 STUDENT FACTS:{RESET}")
    print(f"   GPA                : {YELLOW}{facts['gpa']}{RESET}")
    print(f"   Attendance         : {YELLOW}{facts['attendance']}%{RESET}")
    print(f"   Disciplinary Cases : {'Yes' if facts['disciplinary_cases'] else 'No'}")
    print(f"   Completed Prereqs  : {'Yes' if facts['completed_prerequisites'] else 'No'}")
    print(f"   Outstanding Fees   : {'Yes' if facts['outstanding_fees'] else 'No'}")

    if not results:
        print(f"\n{DIM}  ⚠  No rules were triggered for this profile.{RESET}\n")
        return

    print(f"\n{BOLD}🔍 RULES TRIGGERED: {len(results)}{RESET}")
    for r in results:
        colour = RED if r["conclusion"] in ("Academic Probation", "Registration Blocked") else GREEN
        print(f"\n  {PURPLE}[{r['rule_id']}]{RESET} {BOLD}{r['rule_name']}{RESET}")
        print(f"  Conditions satisfied:")
        for cond in r["conditions_met"]:
            print(f"    {GREEN}✓{RESET} {cond}")
        print(f"  → Conclusion: {colour}{BOLD}{r['conclusion']}{RESET}")

    print(f"\n{BOLD}📌 FINAL CONCLUSIONS:{RESET}")
    for r in results:
        colour = RED if r["conclusion"] in ("Academic Probation", "Registration Blocked") else GREEN
        print(f"   {colour}✓ {r['conclusion']}{RESET}")
    print()


# ════════════════════════════════════════════════════════
# TASK 3 – FORWARD CHAINING DEMONSTRATION
# ════════════════════════════════════════════════════════

def run_profile(name: str, facts: dict, show_backward: bool = False) -> None:
    """Run full inference pipeline for one student and print results."""
    sep = f"{DIM}{'─'*62}{RESET}"
    print(f"\n{sep}")
    print(f"{BOLD}  PROCESSING: {name}{RESET}")
    print(sep)

    # ── Forward chaining ────────────────────────────────
    print(f"\n{BLUE}[FORWARD CHAINING]{RESET}")
    results = forward_chaining(facts)

    if results:
        for r in results:
            colour = RED if r["conclusion"] in ("Academic Probation", "Registration Blocked") else GREEN
            print(f"  Rule Triggered : {PURPLE}{r['rule_id']}{RESET} – {r['rule_name']}")
            print(f"  Conclusion     : {colour}✓ {r['conclusion']}{RESET}\n")
    else:
        print(f"  {DIM}No rules triggered.{RESET}\n")

    # ── Explanation ─────────────────────────────────────
    explain(name, facts, results)

    # ── Backward chaining (bonus) ───────────────────────
    if show_backward:
        print(f"{BLUE}[BACKWARD CHAINING – GOAL VERIFICATION]{RESET}")
        all_goals = [rule["conclusion"] for rule in KNOWLEDGE_BASE["rules"]]
        for goal in all_goals:
            bc = backward_chaining(goal, facts)
            print(f"  Goal      : {goal}")
            print(f"  Rule      : {bc.get('rule_name', 'N/A')}")
            print(f"  Checked   : {bc.get('conditions_checked', [])}")
            print(f"  Result    : {bc['verdict']}\n")

        # ── Comparison table ────────────────────────────
        print(f"\n{BOLD}{'─'*62}")
        print(f"  FORWARD vs BACKWARD CHAINING – COMPARISON")
        print(f"{'─'*62}{RESET}")
        rows = [
            ("Direction",    "Facts → Conclusions",    "Goal → Facts"),
            ("Approach",     "Data-driven",            "Goal-driven"),
            ("Use Case",     "Find all outcomes",      "Verify specific goal"),
            ("Efficiency",   "Evaluates all rules",    "Stops at first proof"),
            ("Best for",     "Unknown outcomes",       "Confirming a hypothesis"),
        ]
        print(f"  {'Aspect':<18} {'Forward Chaining':<26} {'Backward Chaining'}")
        print(f"  {'─'*18} {'─'*26} {'─'*22}")
        for aspect, fwd, bwd in rows:
            print(f"  {aspect:<18} {fwd:<26} {bwd}")
        print()


# ════════════════════════════════════════════════════════
# INTERACTIVE MODE
# ════════════════════════════════════════════════════════

def interactive_mode() -> None:
    """Allow user to enter a custom student profile."""
    print(f"\n{CYAN}{'═'*62}{RESET}")
    print(f"{CYAN}{BOLD}  INTERACTIVE MODE – Enter a Custom Student Profile{RESET}")
    print(f"{CYAN}{'═'*62}{RESET}\n")
    try:
        name      = input("Student Name              : ").strip() or "Unknown Student"
        gpa       = float(input("GPA (e.g. 3.7)            : "))
        att       = float(input("Attendance % (e.g. 85)    : "))
        disc      = input("Disciplinary Cases? (y/n) : ").strip().lower() == "y"
        prereqs   = input("Completed Prerequisites?  (y/n): ").strip().lower() == "y"
        fees      = input("Has Outstanding Fees? (y/n): ").strip().lower() == "y"

        facts = {
            "gpa":                    gpa,
            "attendance":             att,
            "disciplinary_cases":     disc,
            "completed_prerequisites": prereqs,
            "outstanding_fees":       fees,
        }
        run_profile(name, facts, show_backward=True)

    except (KeyboardInterrupt, EOFError):
        print(f"\n\n{DIM}Exited interactive mode.{RESET}\n")
    except ValueError:
        print(f"\n{RED}[ERROR] Invalid numeric input. Please enter numbers for GPA and attendance.{RESET}\n")


# ════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════

def main() -> None:
    print(f"\n{CYAN}{'█'*62}{RESET}")
    print(f"{CYAN}{BOLD}   APT 3020 – STUDENT ACADEMIC ADVISOR REASONING ENGINE{RESET}")
    print(f"{CYAN}{'█'*62}{RESET}")

    # ── Task 3: Three demonstration profiles ────────────

    # Profile 1 – High Achiever (triggers 3 rules; also shows backward chaining)
    run_profile(
        "Alice Wanjiru (High Achiever)",
        {"gpa": 3.8, "attendance": 90, "disciplinary_cases": False,
         "completed_prerequisites": True, "outstanding_fees": False},
        show_backward=True,
    )

    # Profile 2 – At-Risk Student (triggers warning rules)
    run_profile(
        "Brian Otieno (At-Risk Student)",
        {"gpa": 2.5, "attendance": 65, "disciplinary_cases": True,
         "completed_prerequisites": False, "outstanding_fees": True},
    )

    # Profile 3 – Near-Graduation (triggers graduation only)
    run_profile(
        "Carol Mwende (Near-Graduation)",
        {"gpa": 3.2, "attendance": 75, "disciplinary_cases": False,
         "completed_prerequisites": True, "outstanding_fees": False},
    )

    # ── Interactive session ──────────────────────────────
    print(f"\n{CYAN}{'█'*62}{RESET}")
    print(f"{CYAN}{BOLD}   INTERACTIVE MODE{RESET}")
    print(f"{CYAN}{'█'*62}{RESET}")
    interactive_mode()


if __name__ == "__main__":
    main()
