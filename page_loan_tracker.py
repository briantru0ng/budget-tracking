import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime


def render(income_loan):
    st.title("💳 Loan Tracker")

    loan_summary = income_loan.get_loan_summary()

    if loan_summary:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Debt", f"${loan_summary['total_debt']:,.2f}")
        with col2:
            st.metric("Monthly Payment", f"${loan_summary['total_monthly_payment']:,.2f}")
        with col3:
            st.metric("Interest Paid", f"${loan_summary['total_interest_paid']:,.2f}")
        st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Active Loans", "Add Loan", "Strategies", "Compare Payoff", "Payment History"
    ])

    # TAB 1: Active Loans
    with tab1:
        if not income_loan.loans:
            st.info("No loans yet! Add one in the 'Add Loan' tab.")
        else:
            for loan_id, loan in income_loan.loans.items():
                payoff = income_loan.calculate_payoff_timeline(loan_id, 0)

                with st.expander(f"💳 {loan['name']} - ${loan['current_balance']:,.2f}", expanded=True):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.write(f"**Balance:** ${loan['current_balance']:,.2f}")
                        st.write(f"**Original:** ${loan['principal']:,.2f}")
                        st.write(f"**Interest Rate:** {loan['interest_rate'] * 100:.2f}%")
                        st.write(f"**Monthly Payment:** ${loan['monthly_payment']:,.2f}")

                        if payoff and 'months_to_payoff' in payoff:
                            st.write(f"**Payoff Date:** {payoff['payoff_date']} ({payoff['months_to_payoff']} months)")
                            st.write(f"**Total Interest:** ${payoff['total_interest']:,.2f}")

                        paid_pct = (
                            (loan['principal'] - loan['current_balance']) / loan['principal'] * 100
                            if loan['principal'] > 0 else 0
                        )
                        st.progress(paid_pct / 100)
                        st.caption(f"{paid_pct:.1f}% paid off")

                    with col2:
                        st.write("**What if I pay extra?**")
                        extra = st.number_input(
                            "Extra monthly",
                            min_value=0, value=0, step=50,
                            key=f"extra_{loan_id}"
                        )

                        if extra > 0:
                            extra_payoff = income_loan.calculate_payoff_timeline(loan_id, extra)
                            if extra_payoff and 'months_to_payoff' in extra_payoff:
                                months_saved = payoff['months_to_payoff'] - extra_payoff['months_to_payoff']
                                interest_saved = payoff['total_interest'] - extra_payoff['total_interest']
                                st.success(f"Save {months_saved} months")
                                st.success(f"Save ${interest_saved:,.2f}")

                    if st.button("Record Payment", key=f"pay_{loan_id}"):
                        st.session_state[f'paying_{loan_id}'] = True

                    if st.session_state.get(f'paying_{loan_id}', False):
                        col1, col2 = st.columns(2)
                        with col1:
                            payment_amount = st.number_input("Amount", min_value=0.01, key=f"pay_amt_{loan_id}")
                        with col2:
                            payment_date = st.date_input("Date", value=datetime.now(), key=f"pay_date_{loan_id}")

                        extra_principal = st.number_input("Extra Principal", min_value=0.0, key=f"pay_extra_{loan_id}")

                        if st.button("Submit Payment", key=f"submit_{loan_id}"):
                            income_loan.record_payment(
                                loan_id, payment_amount,
                                payment_date.strftime('%Y-%m-%d'),
                                extra_principal
                            )
                            st.session_state[f'paying_{loan_id}'] = False
                            st.success("Payment recorded!")
                            st.rerun()

    # TAB 2: Add Loan
    with tab2:
        st.subheader("Add New Loan")

        col1, col2 = st.columns(2)
        with col1:
            loan_name = st.text_input("Loan Name", placeholder="e.g., Student Loan, Car Loan")
            principal = st.number_input("Original Amount ($)", min_value=1.0, value=10000.0)
            interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=50.0, value=5.0, step=0.1)
        with col2:
            monthly_payment = st.number_input("Monthly Payment ($)", min_value=1.0, value=200.0)
            start_date = st.date_input("Start Date", value=datetime.now())
            loan_type = st.selectbox("Loan Type", ["personal", "student", "auto", "mortgage", "credit_card"])

        if st.button("Add Loan", type="primary"):
            if loan_name:
                income_loan.add_loan(
                    loan_name, principal,
                    interest_rate / 100,
                    monthly_payment,
                    start_date.strftime('%Y-%m-%d'),
                    loan_type
                )
                st.success(f"✓ Added loan: {loan_name}")
                st.rerun()
            else:
                st.error("Please enter a loan name")

    # TAB 3: Strategies
    with tab3:
        st.subheader("Debt Payoff Strategies")

        if not income_loan.loans:
            st.info("Add loans first to see payoff strategies!")
        else:
            strategy_type = st.radio("Strategy", ["Avalanche (Save Most Money)", "Snowball (Quick Wins)"])

            if strategy_type.startswith("Avalanche"):
                strategy = income_loan.avalanche_strategy()
                st.write("### 🏔️ Debt Avalanche Strategy")
                st.write("Pay off highest interest rate first - mathematically optimal")
            else:
                strategy = income_loan.snowball_strategy()
                st.write("### ⛄ Debt Snowball Strategy")
                st.write("Pay off smallest balance first - psychological wins")

            for item in strategy:
                with st.container():
                    st.write(f"**{item['priority']}. {item['name']}**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Balance", f"${item['balance']:,.2f}")
                    with col2:
                        st.metric("Rate", f"{item['rate']:.2f}%")
                    with col3:
                        st.metric("Min Payment", f"${item['min_payment']:,.2f}")
                    st.info(item['recommendation'])
                    st.divider()

    # TAB 4: Compare Payoff
    with tab4:
        st.subheader("📊 Compare Payoff Strategies")
        st.write("See how much time and interest you save by paying extra each month.")

        if not income_loan.loans:
            st.info("Add loans first!")
        else:
            loan_options = {loan['name']: lid for lid, loan in income_loan.loans.items()}
            selected_loan_name = st.selectbox("Select Loan", list(loan_options.keys()), key="compare_loan")
            selected_loan_id = loan_options[selected_loan_name]

            if st.button("Run Comparison", type="primary"):
                comparisons = income_loan.compare_payoff_strategies(selected_loan_id)

                if comparisons:
                    comp_df = pd.DataFrame(comparisons)
                    comp_df.columns = [
                        'Extra/Month', 'Months', 'Payoff Date',
                        'Total Interest', 'Total Paid', 'Interest Saved'
                    ]

                    st.dataframe(
                        comp_df.style.format({
                            'Extra/Month': '${:,.0f}',
                            'Total Interest': '${:,.2f}',
                            'Total Paid': '${:,.2f}',
                            'Interest Saved': '${:,.2f}',
                        }),
                        use_container_width=True
                    )

                    fig = px.bar(
                        comp_df,
                        x='Extra/Month',
                        y='Interest Saved',
                        title="Interest Saved by Extra Monthly Payment",
                        labels={'Extra/Month': 'Extra Payment ($/month)', 'Interest Saved': 'Interest Saved ($)'},
                        text='Interest Saved'
                    )
                    fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
                    st.plotly_chart(fig, use_container_width=True)

                    best = comp_df[comp_df['Interest Saved'] == comp_df['Interest Saved'].max()].iloc[0]
                    st.success(
                        f"💡 Paying ${best['Extra/Month']:.0f} extra/month saves "
                        f"**${best['Interest Saved']:,.2f}** in interest and pays off "
                        f"**{comparisons[0]['months_to_payoff'] - best['Months']} months earlier**"
                    )

        st.divider()
        st.subheader("🔍 Auto-Detect Loan Payments")
        st.write("Scan your transaction history to automatically find and record past payments.")

        if not income_loan.loans:
            st.info("Add loans first!")
        else:
            loan_options2 = {loan['name']: lid for lid, loan in income_loan.loans.items()}
            auto_loan_name = st.selectbox("Select Loan", list(loan_options2.keys()), key="auto_loan")
            auto_loan_id = loan_options2[auto_loan_name]

            keywords_input = st.text_input(
                "Search keywords (comma-separated)",
                placeholder="e.g., navient, student loan, mohela",
                help="Transaction descriptions containing any of these words will be matched"
            )

            if st.button("Scan Transactions", key="auto_detect_btn"):
                if keywords_input:
                    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
                    with st.spinner("Scanning transactions..."):
                        income_loan.auto_detect_loan_payments(auto_loan_id, keywords)
                    st.success(f"✓ Scan complete — check Payment History tab for results")
                    st.rerun()
                else:
                    st.error("Enter at least one keyword")

    # TAB 5: Payment History
    with tab5:
        st.subheader("Payment History")

        if not income_loan.loans:
            st.info("No loans yet!")
        else:
            all_payments = []
            for loan_id, loan in income_loan.loans.items():
                for payment in loan['payments']:
                    all_payments.append({
                        'Loan': loan['name'],
                        'Date': payment['date'],
                        'Amount': payment['amount'],
                        'Principal': payment['principal'],
                        'Interest': payment['interest'],
                        'Balance After': payment['balance_after']
                    })

            if all_payments:
                df = pd.DataFrame(all_payments).sort_values('Date', ascending=False)
                st.dataframe(
                    df.style.format({
                        'Amount': '${:,.2f}',
                        'Principal': '${:,.2f}',
                        'Interest': '${:,.2f}',
                        'Balance After': '${:,.2f}'
                    }),
                    use_container_width=True
                )
            else:
                st.info("No payments recorded yet!")
