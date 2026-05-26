"""
MediExpert - A Rule-Based Medical Expert System
APT 3020B – Knowledge Representation Practical Lab
United States International University - Africa
"""

import json
import os
import sys


# ─────────────────────────────────────────────
# LOAD KNOWLEDGE BASE
# ─────────────────────────────────────────────

def load_knowledge_base(filepath: str = "knowledge_base.json") -> dict:
    """Load the knowledge base from a JSON file."""
    if not os.path.exists(filepath):
        print(f"[ERROR] Knowledge base file '{filepath}' not found.")
        sys.exit(1)
    with open(filepath, "r") as f:
        return json.load(f)


# ─────────────────────────────────────────────
# INPUT VALIDATION (BONUS)
# ─────────────────────────────────────────────

def validate_symptoms(user_input: list[str], valid_symptoms: list[str]) -> tuple[list[str], list[str]]:
    """
    Validate user-provided symptoms against the known symptom list.
    Returns (valid_list, invalid_list).
    """
    normalised = [s.strip().lower().replace(" ", "_") for s in user_input if s.strip()]
    valid   = [s for s in normalised if s in valid_symptoms]
    invalid = [s for s in normalised if s not in valid_symptoms]
    return valid, invalid


# ─────────────────────────────────────────────
# INFERENCE ENGINE  (Forward Chaining)
# ─────────────────────────────────────────────

def run_inference(symptoms: list[str], rules: list[dict]) -> list[dict]:
    """
    Apply IF-THEN rules to the given set of symptoms.
    Returns a list of matched diagnoses sorted by confidence (descending).
    """
    matches = []
    symptom_set = set(symptoms)

    for rule in rules:
        conditions = set(rule["conditions"])
        matched_conditions = conditions & symptom_set
        unmatched = conditions - symptom_set

        if conditions.issubset(symptom_set):          # ALL conditions met
            matches.append({
                "rule_id":    rule["id"],
                "diagnosis":  rule["diagnosis"],
                "confidence": rule["confidence"],
                "matched":    sorted(matched_conditions),
                "missing":    []
            })
        elif len(matched_conditions) / len(conditions) >= 0.67:   # ≥ 2/3 match (partial)
            matches.append({
                "rule_id":    rule["id"],
                "diagnosis":  rule["diagnosis"],
                "confidence": round(rule["confidence"] * (len(matched_conditions) / len(conditions)), 2),
                "matched":    sorted(matched_conditions),
                "missing":    sorted(unmatched),
                "partial":    True
            })

    matches.sort(key=lambda x: x["confidence"], reverse=True)
    return matches


# ─────────────────────────────────────────────
# DISPLAY HELPERS
# ─────────────────────────────────────────────

SEVERITY_COLOUR = {
    "low":      "\033[92m",   # green
    "moderate": "\033[93m",   # yellow
    "high":     "\033[91m",   # red
}
RESET = "\033[0m"
BOLD  = "\033[1m"
CYAN  = "\033[96m"
DIM   = "\033[2m"


def banner():
    print(f"""
{CYAN}{BOLD}
╔══════════════════════════════════════════════════════╗
║          MediExpert – Medical Expert System          ║
║    APT 3020B  |  Knowledge Representation Lab        ║
╚══════════════════════════════════════════════════════╝
{RESET}""")


def display_symptoms_menu(symptoms: list[str]):
    print(f"{BOLD}Available Symptoms:{RESET}")
    cols = 2
    items = [s.replace("_", " ").title() for s in symptoms]
    for i in range(0, len(items), cols):
        row = items[i:i + cols]
        left  = f"  {i+1:>2}. {row[0]:<25}"
        right = f"  {i+2:>2}. {row[1]}" if len(row) > 1 else ""
        print(left + right)
    print()


def display_result(match: dict, diseases: dict):
    diagnosis = match["diagnosis"]
    info      = diseases.get(diagnosis, {})
    severity  = info.get("severity", "unknown")
    colour    = SEVERITY_COLOUR.get(severity, "")

    partial_tag = f"  {DIM}[Partial Match]{RESET}" if match.get("partial") else ""

    print(f"\n  {BOLD}Diagnosis   :{RESET} {colour}{BOLD}{diagnosis}{RESET}{partial_tag}")
    print(f"  {BOLD}Confidence  :{RESET} {match['confidence'] * 100:.0f}%")
    print(f"  {BOLD}Severity    :{RESET} {colour}{severity.upper()}{RESET}")
    print(f"  {BOLD}Description :{RESET} {info.get('description', 'N/A')}")
    print(f"  {BOLD}Matched     :{RESET} {', '.join(s.replace('_',' ').title() for s in match['matched'])}")
    if match.get("missing"):
        print(f"  {BOLD}Also check  :{RESET} {DIM}{', '.join(s.replace('_',' ').title() for s in match['missing'])}{RESET}")
    print(f"  {BOLD}Action      :{RESET} {info.get('recommendation', 'Consult a healthcare professional.')}")


# ─────────────────────────────────────────────
# MAIN PROGRAM
# ─────────────────────────────────────────────

def get_user_symptoms(valid_symptoms: list[str]) -> list[str]:
    """Prompt user for symptoms with full input validation."""
    while True:
        print(f"{BOLD}Enter your symptoms separated by commas{RESET}")
        print(f"{DIM}(e.g.  fever, headache, fatigue   or   1, 7, 2 for numbered entries){RESET}")
        raw = input("  >> ").strip()

        if not raw:
            print(f"\n{CYAN}[INFO] No input provided. Please enter at least one symptom.{RESET}\n")
            continue

        # Allow numeric input (index-based selection)
        parts = [p.strip() for p in raw.split(",")]
        resolved = []
        for p in parts:
            if p.isdigit():
                idx = int(p) - 1
                if 0 <= idx < len(valid_symptoms):
                    resolved.append(valid_symptoms[idx])
                else:
                    print(f"\n{CYAN}[WARN] Number {p} is out of range. Skipping.{RESET}")
            else:
                resolved.append(p)

        valid, invalid = validate_symptoms(resolved, valid_symptoms)

        if invalid:
            print(f"\n{CYAN}[WARN] Unrecognised symptoms skipped: {', '.join(invalid)}{RESET}")

        if not valid:
            print(f"\n{CYAN}[ERROR] None of the entered symptoms are recognised. Try again.{RESET}\n")
            continue

        print(f"\n{DIM}Symptoms accepted: {', '.join(s.replace('_',' ').title() for s in valid)}{RESET}\n")
        return valid


def main():
    banner()

    kb       = load_knowledge_base("knowledge_base.json")
    symptoms = kb["symptoms"]
    rules    = kb["rules"]
    diseases = kb["diseases"]

    while True:
        display_symptoms_menu(symptoms)
        patient_symptoms = get_user_symptoms(symptoms)

        print(f"{BOLD}{'─'*56}")
        print(f"  Running inference engine…")
        print(f"{'─'*56}{RESET}")

        results = run_inference(patient_symptoms, rules)

        if not results:
            print(f"\n{CYAN}  No matching diagnosis found based on entered symptoms.")
            print(f"  Please consult a qualified medical professional.{RESET}")
        else:
            full    = [r for r in results if not r.get("partial")]
            partial = [r for r in results if r.get("partial")]

            if full:
                print(f"\n{BOLD}  ✔  Confirmed Diagnoses ({len(full)} found):{RESET}")
                for r in full:
                    display_result(r, diseases)

            if partial:
                print(f"\n{BOLD}  ⚠  Possible Diagnoses – Partial Match ({len(partial)} found):{RESET}")
                for r in partial:
                    display_result(r, diseases)

        print(f"\n{BOLD}{'─'*56}{RESET}")
        again = input("  Check another patient? (yes/no): ").strip().lower()
        if again not in ("yes", "y"):
            print(f"\n{CYAN}Thank you for using MediExpert. Stay healthy!{RESET}\n")
            break
        print()


if __name__ == "__main__":
    main()
