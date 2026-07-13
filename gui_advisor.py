import streamlit as st
import json
import matplotlib.pyplot as plt
import pandas as pd
from engine import FactBase, InferenceEngine
from acquisition import validate_rule, load_kb, save_kb

# Set page config
st.set_page_config(
    page_title="Smart Finance Advisor KBS",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styles for premium look
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    .metric-card {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #334155;
        text-align: center;
    }
    .metric-val {
        font-size: 2rem;
        font-weight: bold;
    }
    .metric-lbl {
        color: #94a3b8;
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

# Helper to load rules
def get_kb_data():
    try:
        return load_kb("knowledge_base.json")
    except FileNotFoundError:
        # Fallback default KB structure
        return {"rules": [], "default_constants": {}}

# Main application tabs
tab_advisor, tab_acquisition, tab_about = st.tabs([
    "📈 Personal Finance Advisor", 
    "✍️ Knowledge Acquisition (Expert Mode)", 
    "ℹ️ System Information"
])

# ----------------- TAB 1: ADVISOR -----------------
with tab_advisor:
    st.title("💰 Smart Personal Finance Advisor")
    st.subheader("A Knowledge-Based Expert System for Financial Diagnostics")
    st.write("Adjust your details in the sidebar to dynamically trigger rules and view advice.")

    # Sidebar inputs
    st.sidebar.header("💵 Financial Parameters")
    
    income = st.sidebar.number_input(
        "Monthly Net Take-Home Income ($)", 
        min_value=0.0, 
        value=5000.0, 
        step=100.0,
        help="Your net monthly income after taxes and payroll deductions."
    )
    
    essential = st.sidebar.number_input(
        "Essential Monthly Expenses (Needs) ($)", 
        min_value=0.0, 
        value=2500.0, 
        step=50.0,
        help="Rent/mortgage, utilities, groceries, insurance, and minimum debt payments."
    )
    
    discretionary = st.sidebar.number_input(
        "Discretionary Monthly Expenses (Wants) ($)", 
        min_value=0.0, 
        value=1200.0, 
        step=50.0,
        help="Dining out, entertainment, travel, and shopping."
    )
    
    savings_bal = st.sidebar.number_input(
        "Emergency Fund Savings ($)", 
        min_value=0.0, 
        value=3000.0, 
        step=100.0,
        help="Liquid cash reserves in savings accounts, HYSAs, or CDs."
    )
    
    stable_income = st.sidebar.checkbox(
        "Income is Stable & Predictable", 
        value=True,
        help="Uncheck if you are a freelancer, contractor, or have irregular commissions."
    )
    
    st.sidebar.markdown("---")
    st.sidebar.header("💳 Debt Profile")
    
    total_debt = st.sidebar.number_input(
        "Total Outstanding Debt ($)", 
        min_value=0.0, 
        value=15000.0, 
        step=500.0,
        help="Total balance of all mortgage, student loans, car loans, and credit cards."
    )
    
    high_interest_debt = st.sidebar.number_input(
        "High-Interest Debt (>7% APR) ($)", 
        min_value=0.0, 
        value=2000.0, 
        step=100.0,
        help="Credit cards, payday loans, or high-rate personal loans."
    )
    
    min_debt_payment = st.sidebar.number_input(
        "Total Minimum Monthly Debt Payment ($)", 
        min_value=0.0, 
        value=350.0, 
        step=10.0,
        help="The sum of all minimum monthly payments required by your lenders."
    )
    
    st.sidebar.markdown("---")
    st.sidebar.header("🎯 Investment Profile")
    
    risk = st.sidebar.selectbox(
        "Investment Risk Tolerance", 
        options=["low", "medium", "high"], 
        index=1,
        help="Low: Capital preservation. Medium: Balanced growth. High: Maximum growth/volatility."
    )
    
    horizon = st.sidebar.slider(
        "Investment Horizon (Years)", 
        min_value=1, 
        max_value=40, 
        value=8,
        help="When will you need to withdraw or use these investment funds?"
    )

    if income <= 0:
        st.error("Please enter a monthly income greater than $0 to calculate recommendations.")
    else:
        # Calculate derived facts
        monthly_savings = income - essential - discretionary
        savings_rate = (monthly_savings / income) * 100
        essential_pct = (essential / income) * 100
        discretionary_pct = (discretionary / income) * 100
        
        if essential > 0:
            ef_months = savings_bal / essential
        else:
            ef_months = 12.0
            
        dti = (min_debt_payment / income) * 100
        deficit = abs(monthly_savings) if monthly_savings < 0 else 0.0
        
        target_ef_months = 3.0 if stable_income else 6.0
        target_ef = essential * target_ef_months

        # Pack into FactBase
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

        # Run inference
        kb = get_kb_data()
        fb = FactBase(facts_dict)
        engine = InferenceEngine(kb["rules"])
        recs, trace = engine.forward_chain(fb)

        # Dashboard top metrics
        st.markdown("### 📊 Financial Dashboard Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            savings_color = "normal" if savings_rate >= 20 else "off"
            st.metric(
                label="Monthly Net Savings / Rate", 
                value=f"${monthly_savings:,.2f}", 
                delta=f"{savings_rate:.1f}% Savings Rate",
                delta_color=savings_color
            )
            
        with col2:
            ef_delta = f"{ef_months:.1f} / {target_ef_months:.0f} Mo Target"
            st.metric(
                label="Emergency Fund", 
                value=f"${savings_bal:,.2f}", 
                delta=ef_delta,
                delta_color="normal" if ef_months >= target_ef_months else "inverse"
            )
            
        with col3:
            st.metric(
                label="Debt-to-Income (DTI)", 
                value=f"{dti:.1f}%", 
                delta="Warning: High DTI!" if dti >= 40 else "Healthy DTI",
                delta_color="inverse" if dti >= 40 else "normal"
            )
            
        with col4:
            st.metric(
                label="High-Interest Debt Balance", 
                value=f"${high_interest_debt:,.2f}",
                delta="Action Required" if high_interest_debt > 0 else "Debt Free",
                delta_color="inverse" if high_interest_debt > 0 else "normal"
            )

        st.markdown("---")

        # Two columns layout: Charts on left, Recommendations on right
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.subheader("📦 Budget Allocation Breakdown")
            
            # Matplotlib Donut Chart
            # If savings rate is negative, handle gracefully
            if monthly_savings < 0:
                labels = ["Needs (Essential)", "Wants (Discretionary)"]
                sizes = [essential, discretionary]
                colors = ["#f87171", "#fb923c"]
                st.error("⚠️ Deficit Warning: Expenses exceed income! Savings portion cannot be plotted.")
            else:
                labels = ["Needs (Essential)", "Wants (Discretionary)", "Savings / Debt Paydown"]
                sizes = [essential, discretionary, monthly_savings]
                colors = ["#3b82f6", "#f59e0b", "#10b981"]

            fig, ax = plt.subplots(figsize=(5, 5))
            fig.patch.set_facecolor("#1e293b")
            ax.set_facecolor("#1e293b")
            
            wedges, texts, autotexts = ax.pie(
                sizes, 
                labels=labels, 
                colors=colors, 
                autopct="%1.1f%%",
                startangle=140, 
                pctdistance=0.75,
                textprops={'color': 'white', 'fontsize': 10}
            )
            # Make it a donut chart
            centre_circle = plt.Circle((0,0), 0.55, fc='#0e1117')
            fig.gca().add_artist(centre_circle)
            
            ax.axis('equal')  
            st.pyplot(fig)

        with col_right:
            st.subheader("💡 Personalized Recommendations")
            
            if not recs:
                st.success("✅ The system found no issues with your parameters. You are meeting all general financial best practices!")
            else:
                for r in recs:
                    category = r["category"]
                    prio = r["priority"].upper()
                    msg = r["message"]
                    
                    if r["priority"] == "critical":
                        st.error(f"🚨 **[{category} - {prio}]** {msg}")
                    elif r["priority"] == "high":
                        st.error(f"⚠️ **[{category} - {prio}]** {msg}")
                    elif r["priority"] == "medium":
                        st.warning(f"📌 **[{category} - {prio}]** {msg}")
                    else:
                        st.info(f"💡 **[{category} - {prio}]** {msg}")

        # Explainer Trace Expandable
        st.markdown("---")
        with st.expander("🕵️ Detailed Inference Engine Explainer Trace"):
            st.markdown("#### Firing Trace")
            st.write("This shows the sequence in which the inference engine fired rules, matching conditions, and deriving facts.")
            
            trace_data = []
            for t in trace:
                action_lbl = t["action"].upper()
                if t["action"] == "derive":
                    action_lbl += f" ({t['details']['fact']} = {t['details']['value']})"
                trace_data.append({
                    "Cycle": t["cycle"],
                    "Rule ID": t["rule_id"],
                    "Category": t["category"],
                    "Action Taken": action_lbl,
                    "Logic Description": t["description"]
                })
            
            if trace_data:
                st.table(pd.DataFrame(trace_data))
            else:
                st.write("No rules fired.")

            st.markdown("#### Fact Base Output")
            st.write("These are all the parameters (user-defined and inferred) present in the fact base:")
            st.json(fb.all_facts())


# ----------------- TAB 2: KNOWLEDGE ACQUISITION -----------------
with tab_acquisition:
    st.title("✍️ Knowledge Acquisition & Rule Manager")
    st.write("This interface allows financial analysts to add new rules to the expert system. Rules are automatically validated for logical consistency (syntax checks, duplicate check, and circular dependencies) before saving.")

    st.subheader("Add a New Recommendation Rule")
    
    with st.form("new_rule_form"):
        r_id = st.text_input("Rule ID (unique identifier, e.g. rec_credit_card_extreme)", placeholder="rec_...")
        r_cat = st.selectbox("Category", ["Budgeting", "Saving", "Emergency Fund", "Debt Management", "Investment"])
        r_desc = st.text_input("Rule Description (Human readable explanation)", placeholder="Fires when...")
        
        st.markdown("##### Condition (IF)")
        col_f, col_o, col_v = st.columns(3)
        with col_f:
            r_fact = st.text_input("Fact Name (e.g. savings_rate_pct, emergency_fund_months, high_interest_debt)", placeholder="Fact variable")
        with col_o:
            r_op = st.selectbox("Operator", ["==", "!=", ">", "<", ">=", "<="])
        with col_v:
            r_val = st.text_input("Value (Number like 20, or boolean like true / false)", placeholder="Value")

        st.markdown("##### Action (THEN)")
        r_action = st.radio("Action Type", ["recommend", "derive"])
        
        # Details for recommend
        r_prio = st.selectbox("Priority (If recommend)", ["low", "medium", "high", "critical"])
        r_msg = st.text_area("Recommendation Message (If recommend. You can interpolate variables, e.g. 'Your savings rate is {savings_rate_pct:.1f}%')", placeholder="Message text")
        
        # Details for derive
        r_dfact = st.text_input("Derived Fact Name (If derive)", placeholder="e.g. ready_to_invest")
        r_dval = st.text_input("Derived Fact Value (If derive)", placeholder="e.g. true")

        submit_btn = st.form_submit_button("Validate and Save Rule")

        if submit_btn:
            if not r_id.strip() or not r_fact.strip() or not r_desc.strip():
                st.error("❌ Rule ID, Fact, and Description cannot be empty.")
            else:
                # Structure condition
                try:
                    casted_val = float(r_val)
                except ValueError:
                    if r_val.lower() == "true":
                        casted_val = True
                    elif r_val.lower() == "false":
                        casted_val = False
                    else:
                        casted_val = r_val

                if_cond = {
                    "fact": r_fact.strip(),
                    "operator": r_op,
                    "value": casted_val
                }

                # Structure then clause
                if r_action == "recommend":
                    then_clause = {
                        "action": "recommend",
                        "priority": r_prio,
                        "message": r_msg.strip()
                    }
                else:
                    try:
                        casted_dval = float(r_dval)
                    except ValueError:
                        if r_dval.lower() == "true":
                            casted_dval = True
                        elif r_dval.lower() == "false":
                            casted_dval = False
                        else:
                            casted_dval = r_dval

                    then_clause = {
                        "action": "derive",
                        "fact": r_dfact.strip(),
                        "value": casted_dval
                    }

                new_rule = {
                    "id": r_id.strip(),
                    "category": r_cat,
                    "description": r_desc.strip(),
                    "if": if_cond,
                    "then": then_clause
                }

                # Validate
                current_kb = get_kb_data()
                is_valid, msg = validate_rule(new_rule, current_kb["rules"])
                
                if not is_valid:
                    st.error(f"❌ Rule Validation Failed: {msg}")
                else:
                    # Save
                    current_kb["rules"].append(new_rule)
                    save_kb(current_kb, "knowledge_base.json")
                    st.success("🎉 Success! The rule passed validation and has been saved to the Knowledge Base.")

    # View existing rules
    st.markdown("---")
    st.subheader("📚 Currently Loaded Rules")
    current_kb = get_kb_data()
    
    rules_df = []
    for r in current_kb["rules"]:
        cond = r["if"]
        cond_str = f"{cond.get('fact')} {cond.get('operator')} {cond.get('value')}" if "fact" in cond else str(cond)
        
        then = r["then"]
        if then["action"] == "recommend":
            action_str = f"Recommend: {then['message'][:60]}... [{then['priority']}]"
        else:
            action_str = f"Derive: {then['fact']} = {then['value']}"

        rules_df.append({
            "Rule ID": r["id"],
            "Category": r["category"],
            "Description": r["description"],
            "Condition (IF)": cond_str,
            "Action (THEN)": action_str
        })
    st.dataframe(pd.DataFrame(rules_df), use_container_width=True)


# ----------------- TAB 3: SYSTEM INFO -----------------
with tab_about:
    st.title("ℹ️ Knowledge-Based System Details")
    
    st.markdown("""
    ### System Architecture & Logic
    This Personal Finance Advisor KBS consists of three core components:
    
    1. **Knowledge Base (`knowledge_base.json`)**: 
       Stores domain guidelines and production rules formatted in JSON structure. Rules represent conditional financial expertise.
       
    2. **Inference Engine (`engine.py`)**: 
       Implements a forward-chaining algorithm (Modus Ponens) that matches facts against rules, derives new facts (cycle-by-cycle), and registers advice. It resolves conflicts using rule priority levels and logs an explanation trace.
       
    3. **Knowledge Acquisition Interface (`acquisition.py`)**: 
       Provides validators to prevent adding incorrect rules. Specifically:
       - **Syntax Verification**: Ensures rule structure matches expected templates.
       - **Duplicate Detection**: Flags identical rules.
       - **Circular Dependency Check**: Translates derivation facts into a directed graph and runs DFS to check for cycles, ensuring the inference engine never gets caught in an infinite logic loop.
       
    ### Suggested Development Workflow & Git Instructions
    For the group members, when contributing code, please run the following steps to ensure collaboration requirements are met:
    - **Step 1**: Create a feature branch: `git checkout -b feature-yourname-ui`
    - **Step 2**: Code your contributions.
    - **Step 3**: Make clean, descriptive commits:
      - `git commit -m "Added emergency fund check rule"`
      - `git commit -m "Improved Streamlit dashboard styling"`
    - **Step 4**: Push branch and submit a Pull Request on GitHub.
    """)
