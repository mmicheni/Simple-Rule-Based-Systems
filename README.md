# MediExpert – Medical Expert System

> **APT 3020B – Knowledge Representation Practical Lab**  
> United States International University – Africa

---

## Project Description

MediExpert is a rule-based medical expert system that identifies possible illnesses from a patient's reported symptoms. It applies **forward-chaining inference** over a structured knowledge base of IF–THEN rules to produce diagnoses with confidence scores, severity ratings, and recommended actions.

---

## Objectives

- Represent medical knowledge using facts and rules
- Design and implement a rule-based expert system
- Apply logical inference (forward chaining) to diagnose illnesses
- Demonstrate semantic relationships via a network diagram
- Document and organise the project using GitHub best practices

---

## Symptoms Used

| # | Symptom       | # | Symptom           |
|---|---------------|---|-------------------|
| 1 | Fever         | 6  | Runny Nose       |
| 2 | Headache      | 7  | Fatigue          |
| 3 | Cough         | 8  | Sore Throat      |
| 4 | Chest Pain    | 9  | Vomiting         |
| 5 | Sneezing      | 10 | Diarrhea         |

*(Plus extended symptoms: Rash, Joint Pain, Shortness of Breath, Loss of Appetite, Chills)*

---

## Diseases Detected

| Disease        | Severity |
|----------------|----------|
| Malaria        | High     |
| Pneumonia      | High     |
| Flu            | Moderate |
| Food Poisoning | Moderate |
| Typhoid        | High     |
| Common Cold    | Low      |

---

## Rules Applied

```
R1: IF Fever       AND Headache   AND Fatigue       → Malaria        (85%)
R2: IF Cough       AND Chest Pain AND Fatigue       → Pneumonia      (88%)
R3: IF Sneezing    AND Runny Nose AND Sore Throat   → Flu            (80%)
R4: IF Vomiting    AND Diarrhea   AND Fatigue       → Food Poisoning (82%)
R5: IF Fever       AND Headache   AND Loss of Appetite AND Fatigue → Typhoid (78%)
R6: IF Sneezing    AND Runny Nose AND Cough         → Common Cold    (75%)
```

Partial matches (≥ 2/3 rule conditions met) are also surfaced as possible diagnoses at reduced confidence.

---

## Technologies Used

| Technology | Purpose |
|------------|---------|
| Python 3.10+ | Core programming language |
| JSON | Knowledge base storage |
| Standard Library (`json`, `os`, `sys`) | File I/O and system utilities |
| ANSI escape codes | Coloured terminal output |

---

## How to Run the Program

### Prerequisites
- Python 3.10 or higher installed

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/APT3020-Knowledge-Representation-Lab.git
cd APT3020-Knowledge-Representation-Lab

# 2. Run the expert system
python main.py
```

### Input Options
- Type symptom names separated by commas: `fever, headache, fatigue`
- Or use the displayed numbers: `1, 2, 7`
- Mixed input is supported: `1, headache, 7`

---

## Sample Output

```
╔══════════════════════════════════════════════════════╗
║          MediExpert – Medical Expert System          ║
║    APT 3020B  |  Knowledge Representation Lab        ║
╚══════════════════════════════════════════════════════╝

Available Symptoms:
   1. Fever                      2. Headache
   3. Cough                      4. Chest Pain
   5. Sneezing                   6. Runny Nose
   7. Fatigue                    8. Sore Throat
   9. Vomiting                  10. Diarrhea
  ...

Enter your symptoms separated by commas
  >> fever, headache, fatigue

────────────────────────────────────────────────────────
  Running inference engine…
────────────────────────────────────────────────────────

  ✔  Confirmed Diagnoses (1 found):

  Diagnosis   : Malaria
  Confidence  : 85%
  Severity    : HIGH
  Description : A mosquito-borne infectious disease caused by Plasmodium parasites.
  Matched     : Fatigue, Fever, Headache
  Action      : Seek immediate medical attention. Antimalarial medication required.
```

*(See `/screenshots/` folder for full output screenshots)*

---

## Repository Structure

```
APT3020-Knowledge-Representation-Lab/
│
├── README.md                  ← This file
├── main.py                    ← Expert system source code
├── knowledge_base.json        ← Knowledge base (facts, symptoms, rules)
├── semantic_network.png       ← Semantic network diagram
├── screenshots/
│   └── output.png             ← Sample program output
└── docs/
    └── report.pdf             ← Lab report (if required)
```

---

## Bonus Features Implemented

- ✅ Input validation (unrecognised symptoms are flagged and skipped)
- ✅ Numeric input support (select symptoms by number)
- ✅ Partial match inference (diagnoses at ≥ 67% rule match)
- ✅ Extended knowledge base (6 diseases, 15 symptoms)
- ✅ Confidence scores and severity ratings per diagnosis
- ✅ Colour-coded terminal output (severity highlighted)

---

## Group Members

| Name | Student ID |
|------|------------|
|      |            |
|      |            |

---

*This project is submitted in partial fulfilment of APT 3020B – Knowledge Representation.*
