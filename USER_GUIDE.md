# User Guide - Personal Finance Advisor KBS

Welcome to the **Personal Finance Advisor** user and developer manual. This guide explains how to use the interfaces, interpret the system's output, understand the reasoning process, and use the knowledge acquisition editor.

---

## 1. Operating the Advisor Interfaces

### Launching the System
Open your terminal inside the project directory and run:
```bash
python main.py
```
A menu will ask you to select a mode:
* **Option 1 (CLI)**: Guides you through terminal questions. Ideal for rapid consultation with zero installation overhead.
* **Option 2 (GUI)**: Starts a web dashboard. Best for simulating scenarios (using input boxes) and viewing visual charts.
* **Option 3 (Acquisition)**: Allows adding rules in the terminal.

---

## 2. Scenario Walkthroughs & Sample Cases

Here are three distinct sample test profiles that demonstrate the forward-chaining reasoning engine in action.

### Scenario A: The Debt Deficit (Budget Crisis & High Debt)
* **User Profile**: Net Income: **$4,000**, Needs (Rent, Utilities, etc.): **$2,800**, Wants (Dining, Shopping): **$1,500**, Emergency Savings: **$200**, High-Interest Debt: **$8,000**, Min monthly debt payment: **$400**, Risk Tolerance: **Medium**, Time Horizon: **5 Years**, Income: **Stable**.

#### 1. Inferred Facts (Computed automatically):
* `monthly_savings`: $4,000 - $2,800 - $1,500 = **-$300.00**
* `savings_rate_pct`: **-7.5%**
* `essential_expenses_pct`: **70.0%** (Needs > 50%)
* `discretionary_expenses_pct`: **37.5%** (Wants > 30%)
* `emergency_fund_months`: $200 / $2,800 = **0.07 months**
* `dti_pct`: ($400 / $4,000) * 100 = **10.0%**

#### 2. Engine Reasoning Trace (Rules Fired):
1. **Cycle 1 | `derive_deficit`**: Matches `savings_rate_pct < 0.0` $\rightarrow$ Derives `is_in_deficit = true`.
2. **Cycle 1 | `derive_has_high_interest_debt`**: Matches `high_interest_debt > 0.0` $\rightarrow$ Derives `has_high_interest_debt = true`.
3. **Cycle 2 | `rec_budget_deficit`**: Matches `is_in_deficit == true` $\rightarrow$ Triggers **CRITICAL** recommendation.
4. **Cycle 2 | `rec_housing_cost_high`**: Matches `essential_expenses_pct > 50.0` $\rightarrow$ Triggers **MEDIUM** recommendation.
5. **Cycle 2 | `rec_wants_cost_high`**: Matches `discretionary_expenses_pct > 30.0` $\rightarrow$ Triggers **MEDIUM** recommendation.
6. **Cycle 2 | `rec_pay_high_interest_debt`**: Matches `has_high_interest_debt == true` $\rightarrow$ Triggers **HIGH** recommendation.
7. **Cycle 2 | `rec_invest_not_ready_debt`**: Matches `has_high_interest_debt == true` $\rightarrow$ Triggers **MEDIUM** recommendation to halt investments.

#### 3. Output Recommendations:
1. 🚨 **[CRITICAL]** CRITICAL: You are running a monthly budget deficit of 300.00 (Savings Rate: -7.5%). Immediately review discretionary spending and cut down on non-essential items to balance your budget.
2. ⚠️ **[HIGH]** You have $8,000.00 in high-interest debt (e.g., credit card debt). Prioritize paying this off immediately using the Debt Avalanche or Snowball method.
3. 📌 **[MEDIUM]** Your essential expenses (Needs) account for 70.0% of your income, exceeding the recommended 50% threshold.
4. 📌 **[MEDIUM]** Your discretionary spending (Wants) accounts for 37.5% of your income, exceeding the recommended 30% limit.
5. 📌 **[MEDIUM]** Avoid putting extra funds into long-term investments right now. Paying off your credit card/high-interest debt yields a guaranteed return equal to the interest rate, outperforming the stock market.

---

### Scenario B: Ready to Invest (Strong Base, Moderate Risk)
* **User Profile**: Net Income: **$6,000**, Needs: **$2,500**, Wants: **$1,500**, Emergency Savings: **$15,000**, High-Interest Debt: **$0**, Min monthly debt payment: **$0**, Risk Tolerance: **Medium**, Time Horizon: **8 Years**, Income: **Stable**.

#### 1. Inferred Facts:
* `monthly_savings`: $6,000 - $2,500 - $1,500 = **$2,000.00**
* `savings_rate_pct`: **33.3%**
* `essential_expenses_pct`: **41.7%** (Healthy)
* `discretionary_expenses_pct`: **25.0%** (Healthy)
* `emergency_fund_months`: $15,000 / $2,500 = **6.0 months** (Stable target: 3 months)
* `dti_pct`: **0%**
* `target_emergency_fund`: 3.0 * $2,500 = **$7,500.00**

#### 2. Engine Reasoning Trace (Rules Fired):
1. **Cycle 1 | `derive_adequate_emergency_fund_stable`**: Matches `has_stable_income == true` and `emergency_fund_months >= 3.0` $\rightarrow$ Derives `has_adequate_emergency_fund = true`.
2. **Cycle 2 | `derive_ready_to_invest`**: Matches `has_adequate_emergency_fund == true` and `has_high_interest_debt != true` $\rightarrow$ Derives `ready_to_invest = true`.
3. **Cycle 3 | `rec_savings_rate_good`**: Matches `savings_rate_pct >= 20.0` $\rightarrow$ Triggers **LOW** recommendation.
4. **Cycle 3 | `rec_invest_balanced`**: Matches `ready_to_invest == true`, `investment_horizon_years >= 3.0`, and `risk_tolerance == "medium"` $\rightarrow$ Triggers **MEDIUM** recommendation.

#### 3. Output Recommendations:
1. 📌 **[MEDIUM]** Based on your medium risk tolerance and medium-to-long horizon, we recommend a Balanced Portfolio: 60% Equities (diversified index funds) and 40% Fixed Income (bonds).
2. 💡 **[LOW]** Excellent job! Your savings rate of 33.3% meets or exceeds the 20% financial planning benchmark. Keep maintaining this level of discipline.

---

### Scenario C: The Short Horizon (Liquidity Focus)
* **User Profile**: Net Income: **$8,000**, Needs: **$3,000**, Wants: **$2,000**, Emergency Savings: **$18,000**, High-Interest Debt: **$0**, Min monthly debt payment: **$0**, Risk Tolerance: **High**, Time Horizon: **2 Years**, Income: **Stable**.

#### 1. Inferred Facts:
* `emergency_fund_months`: $18,000 / $3,000 = **6.0 months** (Stable target: 3 months)
* `ready_to_invest`: **true** (Emergency fund adequate, no high-interest debt)
* `investment_horizon_years`: **2.0 Years** (Short horizon < 3 years)

#### 2. Engine Reasoning Trace (Rules Fired):
1. **Cycle 1 | `derive_adequate_emergency_fund_stable`** $\rightarrow$ Derives `has_adequate_emergency_fund = true`.
2. **Cycle 2 | `derive_ready_to_invest`** $\rightarrow$ Derives `ready_to_invest = true`.
3. **Cycle 3 | `rec_invest_short_horizon`**: Matches `ready_to_invest == true` and `investment_horizon_years < 3.0` $\rightarrow$ Triggers **HIGH** recommendation.
*Note: Even though the user's risk tolerance is high, this short horizon rule overrides default allocation rules to prevent losses before the user needs capital.*

#### 3. Output Recommendations:
1. ⚠️ **[HIGH]** Your investment horizon is short (2.0 years). Avoid the stock market for these funds. Keep them in a High-Yield Savings Account (HYSA), Certificate of Deposit (CD), or Short-term Treasury Bills to protect your principal.
2. 💡 **[LOW]** Excellent job! Your savings rate of 37.5% meets or exceeds the 20% financial planning benchmark.

---

## 3. Guide to Adding Custom Rules (Expert Mode)

Financial advisors can customize the system using either the CLI rule builder (`python main.py --acquire`) or the Rule Acquisition Web tab.

### Writing a Valid Condition
When creating rules, write comparison expressions matching the keys in the Fact Base:

| Fact Base Variable | Data Type | Meaning |
| :--- | :--- | :--- |
| `monthly_income` | Float | Net take-home income per month |
| `essential_expenses_pct` | Float | Needs as a percentage of income |
| `discretionary_expenses_pct`| Float | Wants as a percentage of income |
| `savings_rate_pct` | Float | Savings as a percentage of income |
| `emergency_fund_months` | Float | Current emergency fund divided by Needs |
| `has_stable_income` | Boolean | True if income is stable |
| `dti_pct` | Float | Monthly debt payments divided by income |
| `high_interest_debt` | Float | Outstanding high-interest balance |
| `risk_tolerance` | String | `"low"`, `"medium"`, or `"high"` |
| `investment_horizon_years` | Float | Years until money is needed |
| `ready_to_invest` | Boolean | Derived fact indicating investment preparedness |

### Message Templates
You can inject actual user metrics directly into recommendation messages using standard Python curly braces:
* `Your savings rate is {savings_rate_pct:.1f}%` $\rightarrow$ "Your savings rate is 18.5%"
* `Aim for a target of ${target_emergency_fund:,.2f}` $\rightarrow$ "Aim for a target of $7,500.00"
