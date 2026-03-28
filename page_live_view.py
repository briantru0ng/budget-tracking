import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from advanced_tracker import AdvancedBudgetTracker

# Main Expenses: essential/fixed cost categories
# Maps display label -> list of transaction categories that roll up into it
MAIN_EXPENSE_ITEMS = {
    "Rent": ["Housing"],
    "Electric": [],
    "Natural Gas": [],
    "Internet": ["Internet"],
    "Water": ["Water"],
    "Groceries": ["Groceries"],
    "Car Gas": ["Gas"],
    "Insurance": ["Insurance"],
}

# All categories considered "main expenses"
_MAIN_CATS = set()
for _cats in MAIN_EXPENSE_ITEMS.values():
    _MAIN_CATS.update(_cats)

# Categories to exclude from personal expenses (income, transfers, skips)
_EXCLUDED_FROM_PERSONAL = {"Income", "Other Income", "Transfers", "SKIP"} | _MAIN_CATS


def _build_period_filter(df_all):
    """Build the period selector and return (selected_data, period_label, mode, value)."""
    now = datetime.now()
    current_year = now.year
    all_periods = sorted(df_all['_period'].unique())

    cy_periods = [p for p in all_periods if p.year == current_year]
    prev_periods = [p for p in all_periods if p.year < current_year]

    options = []
    option_map = {}

    for p in cy_periods:
        label = p.strftime('%B %Y')
        options.append(label)
        option_map[label] = ('month', p)

    if cy_periods:
        options.append(f"YTD {current_year}")
        option_map[f"YTD {current_year}"] = ('ytd', current_year)

    one_year_ago = pd.Period(now, freq='M') - 12
    if one_year_ago in all_periods:
        label_1ya = f"1 Year Ago ({one_year_ago.strftime('%B %Y')})"
        options.append(label_1ya)
        option_map[label_1ya] = ('month', one_year_ago)

    options.append("All Time")
    option_map["All Time"] = ('all', None)

    for p in reversed(prev_periods):
        label = p.strftime('%B %Y')
        options.append(label)
        option_map[label] = ('month', p)

    current_period = pd.Period(now, freq='M')
    default_label = current_period.strftime('%B %Y')
    default_idx = options.index(default_label) if default_label in options else 0

    selected = st.selectbox("Period", options, index=default_idx)
    mode, value = option_map[selected]

    if mode == 'month':
        current_data = df_all[df_all['_period'] == value]
        period_label = value.strftime('%B %Y')
    elif mode == 'ytd':
        current_data = df_all[df_all['Budget_Date'].dt.year == value]
        period_label = f"YTD {value}"
    else:
        current_data = df_all
        period_label = "All Time"

    return current_data, period_label, mode, value


def render(tracker, load_budgets, savings_tracker=None, income_loan=None):
    st.title("📊 Live View Dashboard")

    # Reload from disk so edits on other pages are reflected immediately
    tracker.transaction_db = tracker.load_transaction_db()

    if tracker.transaction_db.empty:
        st.warning("No transactions yet! Add some statements to get started.")
        st.stop()

    # ---- Prepare data -------------------------------------------------- #
    df_all = tracker.transaction_db.copy()
    # Budget_Date is computed at load time; recompute if missing (cache edge case)
    if 'Budget_Date' not in df_all.columns:
        df_all = AdvancedBudgetTracker._apply_budget_dates(df_all)
    df_all = df_all[df_all['Category'] != 'SKIP']
    df_all['_period'] = df_all['Budget_Date'].dt.to_period('M')
    now = datetime.now()

    current_data, period_label, mode, value = _build_period_filter(df_all)

    # ---- Compute totals ------------------------------------------------ #
    # Income = transactions in income categories (not just any positive amount)
    _INCOME_CATS = set(tracker.baskets.get('Income', ['Income', 'Other Income']))
    income_mask = current_data['Category'].isin(_INCOME_CATS) & (current_data['Amount'] > 0)
    income_total = current_data.loc[income_mask, 'Amount'].sum()
    expense_data = current_data[current_data['Amount'] < 0].copy()
    expense_by_cat = expense_data.groupby('Category')['Amount'].sum().abs()

    main_expense_total = sum(expense_by_cat.get(c, 0) for c in _MAIN_CATS)
    all_expenses = expense_by_cat.sum()
    personal_expense_total = sum(
        amt for cat, amt in expense_by_cat.items()
        if cat not in _MAIN_CATS and cat not in _EXCLUDED_FROM_PERSONAL
    )
    working_with = income_total - main_expense_total - personal_expense_total

    # ---- Top-level summary metrics ------------------------------------- #
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💵 Income", f"${income_total:,.2f}")
    with col2:
        st.metric("💸 Expenses", f"${all_expenses:,.2f}")
    with col3:
        net = income_total - all_expenses
        st.metric("💰 Net", f"${net:,.2f}", delta=f"${net:,.2f}")
    with col4:
        # Savings rate = total in Savings group categories / income
        _SAVINGS_CATS = set(tracker.baskets.get('Savings', []))
        savings_total = sum(expense_by_cat.get(c, 0) for c in _SAVINGS_CATS)
        savings_rate = (savings_total / income_total * 100) if income_total > 0 else 0.0
        st.metric("📊 Savings Rate", f"{savings_rate:.1f}%")

    # ---- Alerts (only for single-month views) -------------------------- #
    if mode == 'month':
        budgets = load_budgets()
        if budgets:
            alerts = tracker.budget_forecast_alert(budgets)
            if alerts:
                st.error("⚠️ Budget Alerts")
                for alert in alerts:
                    st.warning(
                        f"**{alert['category']}**: On track to spend ${alert['projected_total']:,.2f} "
                        f"(${alert['projected_overage']:,.2f} over budget of ${alert['budget']:,.2f})"
                    )

    if mode == 'month' and value == pd.Period(now, freq='M'):
        missing = tracker.check_missing_recurring()
        if missing:
            st.warning(f"⚠️ {len(missing)} recurring transactions missing this month")
            for m in missing:
                st.info(f"Expected: {m['merchant']} - ${m['amount']:.2f} on {m['expected_date']}")

    st.divider()

    # ==================================================================== #
    #                              TABS                                     #
    # ==================================================================== #
    tab_income, tab_main, tab_personal, tab_working, tab_savings = st.tabs([
        "💵 Income",
        "🏠 Main Expenses",
        "🛍️ Personal Expenses",
        "📊 Working With Costs",
        "💰 Expected Savings",
    ])

    # ---- Income Tab ---------------------------------------------------- #
    with tab_income:
        st.subheader(f"Income — {period_label}")

        income_data = current_data[income_mask].copy()

        if income_data.empty:
            st.info("No income recorded for this period.")
        else:
            # Group by normalized merchant (income source)
            source_col = 'Normalized_Merchant' if 'Normalized_Merchant' in income_data.columns else 'Description'
            by_source = income_data.groupby(source_col)['Amount'].sum().sort_values(ascending=False)

            rows = []
            for source, amt in by_source.items():
                rows.append({"Source": source, "Amount": amt})
            rows.append({"Source": "**Total**", "Amount": income_total})

            income_df = pd.DataFrame(rows)
            income_df['Amount'] = income_df['Amount'].map(lambda x: f"$ {x:,.2f}")
            st.table(income_df.set_index("Source"))

            # Pie chart
            fig = px.pie(
                values=by_source.values,
                names=by_source.index,
                title="Income Sources",
            )
            st.plotly_chart(fig, use_container_width=True)

    # ---- Main Expenses Tab --------------------------------------------- #
    with tab_main:
        st.subheader(f"Main Expenses — {period_label}")

        rows = []
        for label, cats in MAIN_EXPENSE_ITEMS.items():
            total = sum(expense_by_cat.get(c, 0) for c in cats)
            rows.append({"Category": label, "Amount": total})

        # "Other" main expenses: main categories not explicitly listed
        listed_cats = set()
        for cats in MAIN_EXPENSE_ITEMS.values():
            listed_cats.update(cats)
        other_main = sum(
            amt for cat, amt in expense_by_cat.items()
            if cat in _MAIN_CATS and cat not in listed_cats
        )
        if other_main > 0:
            rows.append({"Category": "Other", "Amount": other_main})

        rows.append({"Category": "**Total**", "Amount": main_expense_total})

        main_df = pd.DataFrame(rows)
        main_df['Amount'] = main_df['Amount'].map(lambda x: f"$ {x:,.2f}" if x > 0 else "$ -")
        st.table(main_df.set_index("Category"))

        # Bar chart of non-zero items
        chart_rows = [r for r in rows[:-1] if not isinstance(r['Amount'], str)]
        if chart_rows:
            chart_data = pd.DataFrame([r for r in rows[:-1]])
            # Re-extract numeric amounts for chart
            chart_data2 = []
            for label, cats in MAIN_EXPENSE_ITEMS.items():
                total = sum(expense_by_cat.get(c, 0) for c in cats)
                if total > 0:
                    chart_data2.append({"Category": label, "Amount": total})
            if chart_data2:
                cdf = pd.DataFrame(chart_data2)
                fig = px.bar(cdf, x="Category", y="Amount", title="Main Expenses Breakdown")
                st.plotly_chart(fig, use_container_width=True)

    # ---- Personal Expenses Tab ----------------------------------------- #
    with tab_personal:
        st.subheader(f"Personal Expenses — {period_label}")

        personal_cats = {
            cat: amt for cat, amt in expense_by_cat.items()
            if cat not in _MAIN_CATS and cat not in _EXCLUDED_FROM_PERSONAL
        }

        if not personal_cats:
            st.info("No personal expenses for this period.")
        else:
            rows = []
            for cat in sorted(personal_cats, key=personal_cats.get, reverse=True):
                rows.append({"Category": cat, "Amount": personal_cats[cat]})
            rows.append({"Category": "**Total**", "Amount": personal_expense_total})

            pers_df = pd.DataFrame(rows)
            pers_df['Amount'] = pers_df['Amount'].map(lambda x: f"$ {x:,.2f}")
            st.table(pers_df.set_index("Category"))

            # Pie chart
            fig = px.pie(
                values=list(personal_cats.values()),
                names=list(personal_cats.keys()),
                title="Personal Spending Breakdown",
            )
            st.plotly_chart(fig, use_container_width=True)

    # ---- Working With Costs Tab ---------------------------------------- #
    with tab_working:
        st.subheader(f"Working With Costs — {period_label}")

        st.markdown("How much you have left after essential and personal spending:")

        summary_rows = [
            {"": "Income", "Amount": f"$ {income_total:,.2f}"},
            {"": "− Main Expenses", "Amount": f"$ {main_expense_total:,.2f}"},
            {"": "− Personal Expenses", "Amount": f"$ {personal_expense_total:,.2f}"},
            {"": "**= Working With**", "Amount": f"**$ {working_with:,.2f}**"},
        ]
        st.table(pd.DataFrame(summary_rows).set_index(""))

        if working_with > 0:
            st.success(f"You have **${working_with:,.2f}** available for savings & investments.")
        elif working_with == 0:
            st.warning("You're breaking even — no surplus for savings this period.")
        else:
            st.error(f"You're **${abs(working_with):,.2f}** over budget this period.")

        # Waterfall-style breakdown
        fig = px.bar(
            x=["Income", "Main Expenses", "Personal Expenses", "Working With"],
            y=[income_total, -main_expense_total, -personal_expense_total, working_with],
            title="Cash Flow Waterfall",
            labels={"x": "", "y": "Amount ($)"},
            color=["Income", "Main Expenses", "Personal Expenses", "Working With"],
            color_discrete_map={
                "Income": "#2ecc71",
                "Main Expenses": "#e74c3c",
                "Personal Expenses": "#e67e22",
                "Working With": "#3498db",
            },
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # Monthly spending trend
        st.subheader("📅 Monthly Spending Trend")
        df = tracker.transaction_db[tracker.transaction_db['Category'] != 'SKIP'].copy()
        if 'Budget_Date' not in df.columns:
            df['Budget_Date'] = pd.to_datetime(df['Date'])
        df['Month'] = df['Budget_Date'].dt.to_period('M').astype(str)
        monthly = df.groupby(['Month', 'Category'])['Amount'].sum().reset_index()
        monthly_expenses = monthly[monthly['Amount'] < 0].copy()
        monthly_expenses['Amount'] = monthly_expenses['Amount'].abs()

        fig = px.line(
            monthly_expenses,
            x='Month',
            y='Amount',
            color='Category',
            title="Spending by Category Over Time",
        )
        st.plotly_chart(fig, use_container_width=True)

    # ---- Expected Savings Tab ------------------------------------------ #
    with tab_savings:
        st.subheader(f"Expected Savings — {period_label}")

        if savings_tracker and savings_tracker.goals:
            goals = savings_tracker.get_all_goals()

            # Calculate allocation percentages relative to working_with
            rows = []
            total_monthly = 0
            for goal in sorted(goals, key=lambda g: g.get('monthly_needed', 0), reverse=True):
                monthly = goal.get('monthly_needed', 0)
                pct = (monthly / working_with * 100) if working_with > 0 else 0
                total_monthly += monthly
                rows.append({
                    "Goal": goal['name'],
                    "%": f"{pct:.0f}%",
                    "Amount": monthly,
                })

            total_pct = (total_monthly / working_with * 100) if working_with > 0 else 0
            rows.append({
                "Goal": "**Total**",
                "%": f"{total_pct:.0f}%",
                "Amount": total_monthly,
            })

            sav_df = pd.DataFrame(rows)
            sav_df['Amount'] = sav_df['Amount'].map(lambda x: f"$ {x:,.2f}")
            st.table(sav_df.set_index("Goal"))

            remaining = working_with - total_monthly
            if remaining > 0:
                st.info(f"**${remaining:,.2f}** unallocated from Working With Costs.")
            elif remaining < 0:
                st.warning(f"Savings goals exceed available funds by **${abs(remaining):,.2f}**.")
            else:
                st.success("Savings goals fully utilize your available funds!")

            # Progress bars
            st.subheader("Goal Progress")
            for goal in goals:
                pct = min(goal.get('progress_pct', 0), 100)
                st.markdown(f"**{goal['name']}** — ${goal['current_amount']:,.2f} / ${goal['target_amount']:,.2f}")
                st.progress(pct / 100)
        else:
            st.info(
                "No savings goals configured yet. "
                "Head to **💰 Savings Goals** in the sidebar to set up your goals — "
                "they'll show up here with allocation percentages."
            )
