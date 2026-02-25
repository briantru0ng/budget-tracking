import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime


def render(tracker, load_budgets):
    st.title("📊 Live View Dashboard")

    if tracker.transaction_db.empty:
        st.warning("No transactions yet! Add some statements to get started.")
        st.stop()

    # Current month stats
    current_month = pd.Period(datetime.now(), freq='M')
    current_data = tracker.transaction_db[
        tracker.transaction_db['Date'].dt.to_period('M') == current_month
    ]

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        income = current_data[current_data['Amount'] > 0]['Amount'].sum()
        st.metric("💵 Income", f"${income:,.2f}")

    with col2:
        expenses = abs(current_data[current_data['Amount'] < 0]['Amount'].sum())
        st.metric("💸 Expenses", f"${expenses:,.2f}")

    with col3:
        net = income - expenses
        st.metric("💰 Net", f"${net:,.2f}", delta=f"${net:,.2f}")

    with col4:
        savings_rate = tracker.calculate_savings_rate(current_month)
        st.metric("📊 Savings Rate", f"{savings_rate:.1f}%")

    st.divider()

    # Alerts section
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

    # Missing recurring transactions
    missing = tracker.check_missing_recurring()
    if missing:
        st.warning(f"⚠️ {len(missing)} recurring transactions missing this month")
        for m in missing:
            st.info(f"Expected: {m['merchant']} - ${m['amount']:.2f} on {m['expected_date']}")

    st.divider()

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Spending by Category")
        category_spending = current_data[current_data['Amount'] < 0].groupby('Category')['Amount'].sum().abs()
        fig = px.pie(
            values=category_spending.values,
            names=category_spending.index,
            title="Current Month"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Top Merchants")
        merchant_spending = (
            current_data[current_data['Amount'] < 0]
            .groupby('Normalized_Merchant')['Amount'].sum().abs()
            .sort_values(ascending=False).head(10)
        )
        fig = px.bar(
            x=merchant_spending.values,
            y=merchant_spending.index,
            orientation='h',
            title="Top 10 Merchants"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Monthly trend
    st.subheader("📅 Monthly Spending Trend")
    df = tracker.transaction_db.copy()
    df['Month'] = df['Date'].dt.to_period('M').astype(str)
    monthly = df.groupby(['Month', 'Category'])['Amount'].sum().reset_index()
    monthly_expenses = monthly[monthly['Amount'] < 0].copy()
    monthly_expenses['Amount'] = monthly_expenses['Amount'].abs()

    fig = px.line(
        monthly_expenses,
        x='Month',
        y='Amount',
        color='Category',
        title="Spending by Category Over Time"
    )
    st.plotly_chart(fig, use_container_width=True)
