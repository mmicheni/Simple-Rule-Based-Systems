// JavaScript logic for Personal Finance Advisor KBS

document.addEventListener("DOMContentLoaded", () => {
    // 1. Navigation Tabs
    const navButtons = document.querySelectorAll(".nav-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTabId = btn.getAttribute("data-target");

            // Toggle active class on buttons
            navButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            // Show/Hide tab content
            tabContents.forEach(tab => {
                if (tab.id === targetTabId) {
                    tab.classList.add("active");
                } else {
                    tab.classList.remove("active");
                }
            });
        });
    });

    // 2. Form Inputs and Sliders Synchronization
    const inputSliderPairs = [
        { input: "monthly_income", slider: "monthly_income_slider" },
        { input: "essential_expenses", slider: "essential_expenses_slider" },
        { input: "discretionary_expenses", slider: "discretionary_expenses_slider" },
        { input: "emergency_fund_balance", slider: "emergency_fund_balance_slider" },
        { input: "total_debt", slider: "total_debt_slider" },
        { input: "high_interest_debt", slider: "high_interest_debt_slider" },
        { input: "monthly_debt_payments", slider: "monthly_debt_payments_slider" },
        { input: "investment_horizon_years", slider: "investment_horizon_years_slider" }
    ];

    inputSliderPairs.forEach(pair => {
        const inputEl = document.getElementById(pair.input);
        const sliderEl = document.getElementById(pair.slider);

        if (inputEl && sliderEl) {
            // Update slider when input changes
            inputEl.addEventListener("input", () => {
                sliderEl.value = inputEl.value;
                evaluateFinancials();
            });

            // Update input when slider changes
            sliderEl.addEventListener("input", () => {
                inputEl.value = sliderEl.value;
                evaluateFinancials();
            });
        }
    });

    // Handle checkboxes and select changes
    const stableIncomeCheckbox = document.getElementById("has_stable_income");
    const riskSelect = document.getElementById("risk_tolerance");

    if (stableIncomeCheckbox) {
        stableIncomeCheckbox.addEventListener("change", evaluateFinancials);
    }
    if (riskSelect) {
        riskSelect.addEventListener("change", evaluateFinancials);
    }

    // 3. Explanation Trace Accordion Toggle
    const traceToggle = document.getElementById("trace-toggle");
    const traceContent = document.getElementById("trace-content");

    if (traceToggle && traceContent) {
        traceToggle.addEventListener("click", () => {
            traceToggle.classList.toggle("active");
            traceContent.classList.toggle("hidden");
        });
    }

    // 4. Rule Acquisition Form Logic (Radio Toggles)
    const actionRecommendRadio = document.querySelector('input[name="action_type"][value="recommend"]');
    const actionDeriveRadio = document.querySelector('input[name="action_type"][value="derive"]');
    const recommendFields = document.getElementById("recommend-fields");
    const deriveFields = document.getElementById("derive-fields");

    const toggleActionFields = () => {
        if (actionRecommendRadio && actionRecommendRadio.checked) {
            recommendFields.classList.remove("hidden");
            deriveFields.classList.add("hidden");
            // Set fields as required/not
            document.getElementById("rec_message").required = true;
            document.getElementById("derive_fact").required = false;
            document.getElementById("derive_value").required = false;
        } else if (actionDeriveRadio && actionDeriveRadio.checked) {
            recommendFields.classList.add("hidden");
            deriveFields.classList.remove("hidden");
            // Set fields as required/not
            document.getElementById("rec_message").required = false;
            document.getElementById("derive_fact").required = true;
            document.getElementById("derive_value").required = true;
        }
    };

    if (actionRecommendRadio && actionDeriveRadio) {
        actionRecommendRadio.addEventListener("change", toggleActionFields);
        actionDeriveRadio.addEventListener("change", toggleActionFields);
        toggleActionFields(); // Initial run
    }

    // 5. Submit New Rule (Knowledge Acquisition)
    const ruleForm = document.getElementById("rule-form");
    const validationAlert = document.getElementById("validation-alert");

    if (ruleForm) {
        ruleForm.addEventListener("submit", (e) => {
            e.preventDefault();
            
            // Build condition IF
            const rFact = document.getElementById("cond_fact").value.trim();
            const rOp = document.getElementById("cond_op").value;
            const rValRaw = document.getElementById("cond_val").value.trim();
            
            // Cast condition value appropriately
            let rVal;
            if (rValRaw.toLowerCase() === "true") rVal = true;
            else if (rValRaw.toLowerCase() === "false") rVal = false;
            else if (!isNaN(rValRaw)) rVal = parseFloat(rValRaw);
            else rVal = rValRaw;

            const ifCond = {
                fact: rFact,
                operator: rOp,
                value: rVal
            };

            // Build action THEN
            const actionType = document.querySelector('input[name="action_type"]:checked').value;
            let thenClause = {};

            if (actionType === "recommend") {
                thenClause = {
                    action: "recommend",
                    priority: document.getElementById("rec_priority").value,
                    message: document.getElementById("rec_message").value.trim()
                };
            } else {
                const dFact = document.getElementById("derive_fact").value.trim();
                const dValRaw = document.getElementById("derive_value").value.trim();
                
                let dVal;
                if (dValRaw.toLowerCase() === "true") dVal = true;
                else if (dValRaw.toLowerCase() === "false") dVal = false;
                else if (!isNaN(dValRaw)) dVal = parseFloat(dValRaw);
                else dVal = dValRaw;

                thenClause = {
                    action: "derive",
                    fact: dFact,
                    value: dVal
                };
            }

            // Full rule object
            const rulePayload = {
                id: document.getElementById("rule_id").value.trim(),
                category: document.getElementById("rule_category").value,
                description: document.getElementById("rule_desc").value.trim(),
                if: ifCond,
                then: thenClause
            };

            // Post rule payload to API
            fetch("/api/rules/add", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(rulePayload)
            })
            .then(res => res.json())
            .then(data => {
                validationAlert.classList.remove("hidden", "alert-success", "alert-error");
                
                if (data.success) {
                    validationAlert.classList.add("alert-success");
                    validationAlert.textContent = "🎉 Success: " + data.message;
                    ruleForm.reset();
                    toggleActionFields();
                    loadRules(); // Refresh rules table
                    evaluateFinancials(); // Re-run evaluation to see if new rule triggers
                } else {
                    validationAlert.classList.add("alert-error");
                    validationAlert.textContent = "❌ Error: " + data.error;
                }
            })
            .catch(err => {
                validationAlert.classList.remove("hidden", "alert-success", "alert-error");
                validationAlert.classList.add("alert-error");
                validationAlert.textContent = "❌ Network error: " + err.message;
            });
        });
    }

    // Chart.js global instance
    let budgetChartInstance = null;

    // Helper: format currency
    const formatCurrency = (val) => {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
    };

    // 6. Fetch Diagnostics (AJAX Evaluation)
    function evaluateFinancials() {
        const payload = {
            monthly_income: parseFloat(document.getElementById("monthly_income").value) || 0,
            essential_expenses: parseFloat(document.getElementById("essential_expenses").value) || 0,
            discretionary_expenses: parseFloat(document.getElementById("discretionary_expenses").value) || 0,
            emergency_fund_balance: parseFloat(document.getElementById("emergency_fund_balance").value) || 0,
            has_stable_income: document.getElementById("has_stable_income").checked,
            total_debt: parseFloat(document.getElementById("total_debt").value) || 0,
            high_interest_debt: parseFloat(document.getElementById("high_interest_debt").value) || 0,
            monthly_debt_payments: parseFloat(document.getElementById("monthly_debt_payments").value) || 0,
            risk_tolerance: document.getElementById("risk_tolerance").value,
            investment_horizon_years: parseFloat(document.getElementById("investment_horizon_years").value) || 0
        };

        if (payload.monthly_income <= 0) return;

        fetch("/api/evaluate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (!data.success) {
                console.error("Evaluation error:", data.error);
                return;
            }

            // Update KPI cards
            const m = data.metrics;
            
            // Monthly Savings Rate Card
            const savingsValEl = document.getElementById("metric-savings");
            const savingsRateEl = document.getElementById("metric-savings-rate");
            savingsValEl.textContent = formatCurrency(m.monthly_savings);
            savingsRateEl.textContent = `${m.savings_rate_pct.toFixed(1)}% Rate`;
            if (m.has_deficit) {
                savingsRateEl.className = "metric-sub text-red";
                savingsRateEl.textContent = "Deficit Running!";
            } else {
                savingsRateEl.className = m.savings_rate_pct >= 20 ? "metric-sub text-green" : "metric-sub text-amber";
            }

            // Emergency Fund Card
            const efMonthsEl = document.getElementById("metric-ef-months");
            const efTargetEl = document.getElementById("metric-ef-target");
            efMonthsEl.textContent = `${m.emergency_fund_months.toFixed(1)} Months`;
            efTargetEl.textContent = `Target: ${m.target_emergency_fund_months.toFixed(0)} Mo (${formatCurrency(m.target_emergency_fund)})`;
            if (m.emergency_fund_months >= m.target_emergency_fund_months) {
                efTargetEl.className = "metric-sub text-green";
            } else {
                efTargetEl.className = "metric-sub text-red";
            }

            // DTI Card
            const dtiValEl = document.getElementById("metric-dti");
            const dtiStatusEl = document.getElementById("metric-dti-status");
            dtiValEl.textContent = `${m.dti_pct.toFixed(1)}%`;
            if (m.dti_pct >= 40) {
                dtiStatusEl.textContent = "Critically High!";
                dtiStatusEl.className = "metric-sub text-red";
            } else {
                dtiStatusEl.textContent = "Healthy DTI";
                dtiStatusEl.className = "metric-sub text-green";
            }

            // High Interest Debt Card
            const hiValEl = document.getElementById("metric-hi-debt");
            const hiStatusEl = document.getElementById("metric-hi-debt-status");
            hiValEl.textContent = formatCurrency(payload.high_interest_debt);
            if (payload.high_interest_debt > 0) {
                hiStatusEl.textContent = "Action Required";
                hiStatusEl.className = "metric-sub text-red";
            } else {
                hiStatusEl.textContent = "Debt Free";
                hiStatusEl.className = "metric-sub text-green";
            }

            // Update Chart.js Donut Chart
            updateChart(payload.essential_expenses, payload.discretionary_expenses, m.monthly_savings);

            // Update Recommendations List
            const recsContainer = document.getElementById("recommendations-list");
            recsContainer.innerHTML = "";

            if (data.recommendations.length === 0) {
                recsContainer.innerHTML = `
                    <div class="alert alert-success">
                        ✅ The system found no critical warnings. You are meeting standard financial benchmarks!
                    </div>
                `;
            } else {
                data.recommendations.forEach(r => {
                    const card = document.createElement("div");
                    card.className = `rec-card rec-${r.priority}`;
                    
                    const title = document.createElement("div");
                    title.className = `rec-card-title ${r.priority}`;
                    title.textContent = `${r.category} • ${r.priority}`;
                    
                    const text = document.createElement("div");
                    text.textContent = r.message;

                    card.appendChild(title);
                    card.appendChild(text);
                    recsContainer.appendChild(card);
                });
            }

            // Update Explainer Trace Table
            const tbody = document.querySelector("#trace-table tbody");
            tbody.innerHTML = "";
            
            data.trace.forEach(t => {
                const tr = document.createElement("tr");
                
                let actionText = t.action.toUpperCase();
                if (t.action === "derive") {
                    actionText += ` (${t.details.fact} = ${t.details.value})`;
                }

                tr.innerHTML = `
                    <td>${t.cycle}</td>
                    <td><code>${t.rule_id}</code></td>
                    <td>${t.category}</td>
                    <td>${actionText}</td>
                    <td>${t.description}</td>
                `;
                tbody.appendChild(tr);
            });

            // Update Fact Base JSON display
            document.getElementById("fact-base-json").textContent = JSON.stringify(data.facts, null, 2);
        })
        .catch(err => console.error("Network error evaluating diagnostics:", err));
    }

    // Chart.js draw & update logic
    function updateChart(needs, wants, savings) {
        const ctx = document.getElementById("budgetChart");
        if (!ctx) return;

        let labels, sizes, colors;

        if (savings < 0) {
            labels = ["Needs (Essential)", "Wants (Discretionary)"];
            sizes = [needs, wants];
            colors = ["#ef4444", "#fb923c"]; // Red/Orange warning
        } else {
            labels = ["Needs (Essential)", "Wants (Discretionary)", "Savings / Debt Paydown"];
            sizes = [needs, wants, savings];
            colors = ["#6366f1", "#f59e0b", "#10b981"]; // Indigo/Amber/Emerald
        }

        if (budgetChartInstance) {
            // Update existing instance data
            budgetChartInstance.data.labels = labels;
            budgetChartInstance.data.datasets[0].data = sizes;
            budgetChartInstance.data.datasets[0].backgroundColor = colors;
            budgetChartInstance.update();
        } else {
            // Create new chart instance
            budgetChartInstance = new Chart(ctx, {
                type: "doughnut",
                data: {
                    labels: labels,
                    datasets: [{
                        data: sizes,
                        backgroundColor: colors,
                        borderWidth: 2,
                        borderColor: "#1e293b"
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: "bottom",
                            labels: {
                                color: "#f8fafc",
                                font: {
                                    family: "'Inter', sans-serif",
                                    size: 11
                                }
                            }
                        }
                    },
                    cutout: "60%"
                }
            });
        }
    }

    // 7. Load Rules List (Acquisition)
    function loadRules() {
        const tbody = document.querySelector("#rules-table tbody");
        if (!tbody) return;

        fetch("/api/rules")
        .then(res => res.json())
        .then(data => {
            if (!data.success) return;

            tbody.innerHTML = "";
            data.rules.forEach(r => {
                const tr = document.createElement("tr");

                // Format IF condition
                let condStr = "";
                const c = r.if;
                if (c.fact) {
                    condStr = `<code>${c.fact}</code> ${c.operator} ${c.value}`;
                } else if (c.and) {
                    condStr = c.and.map(sub => `(${sub.fact} ${sub.operator} ${sub.value})`).join(" AND ");
                } else if (c.or) {
                    condStr = c.or.map(sub => `(${sub.fact} ${sub.operator} ${sub.value})`).join(" OR ");
                } else if (c.not) {
                    condStr = `NOT (${c.not.fact} ${c.not.operator} ${c.not.value})`;
                } else {
                    condStr = JSON.stringify(c);
                }

                // Format THEN action
                let actionStr = "";
                const t = r.then;
                if (t.action === "recommend") {
                    actionStr = `Recommend <strong>[${t.priority}]</strong>: <span class="help-text">${t.message}</span>`;
                } else {
                    actionStr = `Derive Fact: <code>${t.fact}</code> = ${t.value}`;
                }

                tr.innerHTML = `
                    <td><code>${r.id}</code></td>
                    <td>${r.category}</td>
                    <td>${condStr}</td>
                    <td>${actionStr}</td>
                `;
                tbody.appendChild(tr);
            });
        })
        .catch(err => console.error("Error loading rules:", err));
    }

    // Initial Trigger on load
    evaluateFinancials();
    loadRules();
});
