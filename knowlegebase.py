FACTS = {
    "net_income": 120000,
    "expenses": 95000,
    "savings": 15000,
    "emergency_fund": 25000,
    "surplus_funds": 75000,
    "debt_to_income_ratio": 0.35,
    "salary_hits_account": True,
    "dividends_paid": False
}

RULES = {
    "Budgetting Rule" : {
        "IF" : ["expenses > net_income"],
        "THEN": "recommend reducing discretionary spending"

        "IF": ["salary hits account"],
        "THEN": "20% to be automatically debited AND credited to savings account"
    },

    "Saving Rule" : {
        "IF" : ["savings < 20% of income"],
        "THEN": "recommend increasing monthly savings contributions"
    },

    "Emergency Fund Rule" : {
        "IF" : ["emergency fund < 3 months of expenses"],
        "THEN": "recommend prioritizing emergency fund contributions"
    },

    "Investment Rule": {
        "IF": ["emergency fund is sufficient AND savings rate ≥ 20%"],
        "THEN": "recommend investing surplus funds"

        "IF": ["surplus funds = 50,000"],
        "THEN": "invest in treasury bills/bonds"

        "IF": ["surplus funds is 50,000 < x <= 100,000"],
        "THEN": "invest 50,000 in treasury bills/bonds AND remainder in the stock market"

        "IF": ["dividends are paid from stocks",
        "THEN"]: "reinvest dividends"
    },

     "Debt Management Rule": {
         "IF": ["debt-to-income ratio > 40%"],
         "THEN": "recommend debt repayment strategies before new investments"
     }
}

RELATIONS = {
    "income -> expenses": "expenses should not exceed income",
    "income -> savings": "savings are a percentage of income",
    "income -> debt_to_income_ratio": "ratio is debt divided by income",
    "expenses -> emergency_fund": "emergency fund should cover 3 months of expenses",
    "surplus_funds -> investment": "surplus funds determine investment strategy",
    "dividends -> reinvestment": "dividends can be reinvested into portfolio"
}
