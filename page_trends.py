import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def render(tracker):
    st.title("📈 Trends & Insights")

    if tracker.transaction_db.empty:
        st.warning("No transactions yet!")
        st.stop()

    # Year-over-year comparison
    st.subheader("📊 Year-over-Year Comparison")
    yoy = tracker.calculate_yoy_comparison()

    if yoy:
        yoy_df = pd.DataFrame.from_dict(yoy, orient='index')
        yoy_df = yoy_df.sort_values('pct_change', ascending=False)

        fig = px.bar(
            yoy_df,
            x=yoy_df.index,
            y='pct_change',
            title="YoY Spending Change by Category",
            labels={'pct_change': 'Change (%)', 'index': 'Category'},
            color='pct_change',
            color_continuous_scale=['green', 'yellow', 'red']
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(yoy_df, use_container_width=True)
    else:
        st.info("Need at least 2 years of data for YoY comparison")

    st.divider()

    # Savings rate over time
    st.subheader("💰 Savings Rate Over Time")
    df = tracker.transaction_db.copy()
    df['Month'] = df['Date'].dt.to_period('M')

    savings_rates = []
    for month in sorted(df['Month'].unique()):
        rate = tracker.calculate_savings_rate(month)
        savings_rates.append({'Month': str(month), 'Savings_Rate': rate})

    savings_df = pd.DataFrame(savings_rates)

    fig = px.line(savings_df, x='Month', y='Savings_Rate', title="Savings Rate Trend", markers=True)
    fig.add_hline(y=20, line_dash="dash", line_color="green", annotation_text="20% Target")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Cash flow projection
    st.subheader("💵 Cash Flow Projection")
    projections = tracker.project_cash_flow(6)
    proj_df = pd.DataFrame(projections)

    fig = go.Figure()
    fig.add_trace(go.Bar(name='Income', x=proj_df['month'], y=proj_df['projected_income'], marker_color='green'))
    fig.add_trace(go.Bar(name='Expenses', x=proj_df['month'], y=proj_df['projected_expenses'], marker_color='red'))
    fig.add_trace(go.Scatter(name='Net', x=proj_df['month'], y=proj_df['projected_net'], mode='lines+markers', line=dict(color='blue', width=3)))

    fig.update_layout(title="6-Month Projection (Based on Recurring Transactions)", barmode='group')
    st.plotly_chart(fig, use_container_width=True)
