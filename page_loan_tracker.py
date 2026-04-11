import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime


LOAN_TYPE_OPTIONS = ["personal", "student", "auto", "mortgage", "credit_card"]
STATUS_OPTIONS = ["Active", "Repayment", "In School", "Grace Period", "Deferment", "Forbearance", "Paid Off"]
INTEREST_TYPE_OPTIONS = ["Fixed", "Variable"]
REPAYMENT_PLAN_OPTIONS = [
    "", "Level", "Graduated", "Extended", "Income-Driven (IDR)",
    "Income-Based (IBR)", "Pay As You Earn (PAYE)",
    "Revised Pay As You Earn (REPAYE)", "Income-Contingent (ICR)",
]


def _detail_row(label, value, is_money=False, is_pct=False):
    """Render a single label: value row styled like a loan portal."""
    if value is None or value == '':
        return
    if is_money:
        display = f"${value:,.2f}" if isinstance(value, (int, float)) else value
    elif is_pct:
        display = f"{value * 100:.3f}%" if isinstance(value, float) and value < 1 else f"{value}%"
    else:
        display = str(value)
    st.markdown(
        f'<div style="display:flex;justify-content:space-between;padding:4px 0;'
        'border-bottom:1px solid rgba(128,128,128,0.15)">'
        f'<span style="color:gray">{label}</span>'
        f'<span style="font-weight:600">{display}</span></div>',
        unsafe_allow_html=True,
    )


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

    # ================================================================== #
    #  TAB 1: Active Loans (detailed portal-style view)                   #
    # ================================================================== #
    with tab1:
        if not income_loan.loans:
            st.info("No loans yet! Add one in the 'Add Loan' tab.")
        else:
            for loan_id, loan in income_loan.loans.items():
                payoff = income_loan.calculate_payoff_timeline(loan_id, 0)

                # Header bar with name and balance
                status = loan.get('status', 'Active')
                status_color = {
                    'Repayment': '#e67e22', 'Active': '#2ecc71',
                    'Paid Off': '#95a5a6', 'Deferment': '#3498db',
                    'Forbearance': '#9b59b6', 'Grace Period': '#1abc9c',
                    'In School': '#3498db',
                }.get(status, '#2ecc71')

                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">'
                    f'<span style="font-size:1.4rem;font-weight:700">💳 {loan["name"]}</span>'
                    f'<span style="background:{status_color};color:white;padding:2px 10px;'
                    f'border-radius:12px;font-size:0.85rem">{status}</span></div>',
                    unsafe_allow_html=True,
                )

                with st.expander("Loan Details", expanded=True):
                    left, right = st.columns(2)

                    # ---- Left column: Status & Repayment ---- #
                    with left:
                        st.markdown("#### Loan Status")
                        _detail_row("Loan Status", status)
                        if loan.get('repayment_plan'):
                            plan_label = loan['repayment_plan']
                            if loan.get('repayment_plan_end_date'):
                                plan_label += f" — Ends {loan['repayment_plan_end_date']}"
                            _detail_row("Repayment Plan", plan_label)
                        _detail_row("Repayment Start Date", loan.get('repayment_start_date') or loan.get('start_date'))
                        est_payoff = loan.get('estimated_payoff_date', '')
                        if not est_payoff and payoff and 'payoff_date' in payoff:
                            est_payoff = payoff['payoff_date']
                        _detail_row("Estimated Payoff Date", est_payoff)

                        if payoff and 'months_to_payoff' in payoff:
                            schedule_months = payoff['months_to_payoff']
                            _detail_row(
                                "Estimated Payment Schedule",
                                f"{schedule_months} months @ ${loan['monthly_payment']:,.2f}"
                            )
                            _detail_row("Total Amount to be Repaid", payoff['total_paid'], is_money=True)

                        st.markdown("")
                        st.markdown("**Ready to pay off this loan today?**")
                        current_bal = loan['current_balance']
                        monthly_rate = loan['interest_rate'] / 12
                        daily_interest = current_bal * (loan['interest_rate'] / 365)
                        payoff_online = current_bal + (current_bal * monthly_rate * 0)  # accrued
                        # Estimate mail payoff (+ ~3 days of interest)
                        payoff_mail = current_bal + daily_interest * 3
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Online", f"${current_bal:,.2f}")
                        with col_b:
                            st.metric("By U.S. Mail", f"${payoff_mail:,.2f}")

                    # ---- Right column: Balance & Loan Info ---- #
                    with right:
                        st.markdown("#### Balance Details")
                        unpaid_principal = loan.get('unpaid_principal', loan['current_balance'])
                        unpaid_interest = loan.get('unpaid_interest', 0)
                        _detail_row("Unpaid Principal", unpaid_principal, is_money=True)
                        _detail_row("Unpaid Interest", unpaid_interest, is_money=True)
                        _detail_row("Current Balance", loan['current_balance'], is_money=True)

                        st.markdown("")
                        st.markdown("#### Interest")
                        _detail_row("Interest Rate", loan['interest_rate'], is_pct=True)
                        _detail_row("Interest Type", loan.get('interest_type', 'Fixed'))

                        st.markdown("")
                        st.markdown("#### Loan Information")
                        _detail_row("Loan Type", loan['loan_type'].replace('_', ' ').title())
                        _detail_row("Original Principal", loan['principal'], is_money=True)
                        if loan.get('disbursement_date'):
                            _detail_row("Disbursement Date", loan['disbursement_date'])
                        if loan.get('school'):
                            _detail_row("School", loan['school'])
                        if loan.get('current_owner'):
                            _detail_row("Current Owner", loan['current_owner'])
                        if loan.get('guarantor'):
                            _detail_row("Guarantor", loan['guarantor'])
                        if loan.get('borrower_benefits'):
                            _detail_row("Borrower Benefits", loan['borrower_benefits'])

                    # ---- Progress bar ---- #
                    paid_pct = (
                        (loan['principal'] - loan['current_balance']) / loan['principal'] * 100
                        if loan['principal'] > 0 else 0
                    )
                    st.progress(min(paid_pct / 100, 1.0))
                    st.caption(f"{paid_pct:.1f}% paid off — ${loan['principal'] - loan['current_balance']:,.2f} of ${loan['principal']:,.2f}")

                    # ---- Actions row ---- #
                    act1, act2, act3 = st.columns(3)
                    with act1:
                        if st.button("What if I pay extra?", key=f"extra_toggle_{loan_id}"):
                            st.session_state[f'show_extra_{loan_id}'] = not st.session_state.get(f'show_extra_{loan_id}', False)
                    with act2:
                        if st.button("Record Payment", key=f"pay_{loan_id}"):
                            st.session_state[f'paying_{loan_id}'] = not st.session_state.get(f'paying_{loan_id}', False)
                    with act3:
                        if st.button("Edit Loan Details", key=f"edit_loan_{loan_id}"):
                            st.session_state[f'editing_loan_{loan_id}'] = not st.session_state.get(f'editing_loan_{loan_id}', False)

                    # Extra payment calculator
                    if st.session_state.get(f'show_extra_{loan_id}', False):
                        extra = st.number_input(
                            "Extra monthly payment", min_value=0, value=0, step=50,
                            key=f"extra_{loan_id}"
                        )
                        if extra > 0 and payoff and 'months_to_payoff' in payoff:
                            extra_payoff = income_loan.calculate_payoff_timeline(loan_id, extra)
                            if extra_payoff and 'months_to_payoff' in extra_payoff:
                                months_saved = payoff['months_to_payoff'] - extra_payoff['months_to_payoff']
                                interest_saved = payoff['total_interest'] - extra_payoff['total_interest']
                                c1, c2 = st.columns(2)
                                with c1:
                                    st.success(f"Save {months_saved} months")
                                with c2:
                                    st.success(f"Save ${interest_saved:,.2f} in interest")

                    # Record payment form
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

                    # Edit loan details form
                    if st.session_state.get(f'editing_loan_{loan_id}', False):
                        st.markdown("---")
                        st.markdown("**Edit Loan Details**")
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            new_status = st.selectbox(
                                "Status", STATUS_OPTIONS,
                                index=STATUS_OPTIONS.index(loan.get('status', 'Active'))
                                if loan.get('status', 'Active') in STATUS_OPTIONS else 0,
                                key=f"edit_status_{loan_id}",
                            )
                            new_plan = st.selectbox(
                                "Repayment Plan", REPAYMENT_PLAN_OPTIONS,
                                index=REPAYMENT_PLAN_OPTIONS.index(loan.get('repayment_plan', ''))
                                if loan.get('repayment_plan', '') in REPAYMENT_PLAN_OPTIONS else 0,
                                key=f"edit_plan_{loan_id}",
                            )
                            new_plan_end = st.text_input(
                                "Plan End Date", value=loan.get('repayment_plan_end_date', ''),
                                key=f"edit_plan_end_{loan_id}",
                            )
                            new_interest_type = st.selectbox(
                                "Interest Type", INTEREST_TYPE_OPTIONS,
                                index=INTEREST_TYPE_OPTIONS.index(loan.get('interest_type', 'Fixed'))
                                if loan.get('interest_type', 'Fixed') in INTEREST_TYPE_OPTIONS else 0,
                                key=f"edit_int_type_{loan_id}",
                            )
                            new_unpaid_principal = st.number_input(
                                "Unpaid Principal", value=float(loan.get('unpaid_principal', loan['current_balance'])),
                                key=f"edit_up_{loan_id}",
                            )
                            new_unpaid_interest = st.number_input(
                                "Unpaid Interest", value=float(loan.get('unpaid_interest', 0)),
                                key=f"edit_ui_{loan_id}",
                            )
                        with ec2:
                            new_school = st.text_input(
                                "School", value=loan.get('school', ''),
                                key=f"edit_school_{loan_id}",
                            )
                            new_owner = st.text_input(
                                "Current Owner", value=loan.get('current_owner', ''),
                                key=f"edit_owner_{loan_id}",
                            )
                            new_guarantor = st.text_input(
                                "Guarantor", value=loan.get('guarantor', ''),
                                key=f"edit_guarantor_{loan_id}",
                            )
                            new_disbursement = st.text_input(
                                "Disbursement Date", value=loan.get('disbursement_date', ''),
                                key=f"edit_disb_{loan_id}",
                            )
                            new_benefits = st.text_input(
                                "Borrower Benefits", value=loan.get('borrower_benefits', ''),
                                key=f"edit_benefits_{loan_id}",
                            )
                            new_est_payoff = st.text_input(
                                "Estimated Payoff Date", value=loan.get('estimated_payoff_date', ''),
                                key=f"edit_est_payoff_{loan_id}",
                            )
                        if st.button("Save Changes", key=f"save_edit_{loan_id}", type="primary"):
                            income_loan.update_loan(
                                loan_id,
                                status=new_status,
                                repayment_plan=new_plan,
                                repayment_plan_end_date=new_plan_end,
                                interest_type=new_interest_type,
                                unpaid_principal=new_unpaid_principal,
                                unpaid_interest=new_unpaid_interest,
                                current_balance=new_unpaid_principal + new_unpaid_interest,
                                school=new_school,
                                current_owner=new_owner,
                                guarantor=new_guarantor,
                                disbursement_date=new_disbursement,
                                borrower_benefits=new_benefits,
                                estimated_payoff_date=new_est_payoff,
                            )
                            st.session_state[f'editing_loan_{loan_id}'] = False
                            st.success("Loan details updated!")
                            st.rerun()

                st.divider()

    # ================================================================== #
    #  TAB 2: Add Loan                                                    #
    # ================================================================== #
    with tab2:
        st.subheader("Add New Loan")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Core Details**")
            loan_name = st.text_input("Loan Name", placeholder="e.g., Federal Direct Subsidized")
            principal = st.number_input("Original Principal ($)", min_value=1.0, value=10000.0)
            current_balance = st.number_input("Current Balance ($)", min_value=0.0, value=10000.0)
            interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=50.0, value=5.0, step=0.1)
            monthly_payment = st.number_input("Monthly Payment ($)", min_value=1.0, value=200.0)
            loan_type = st.selectbox("Loan Type", LOAN_TYPE_OPTIONS)
            interest_type = st.selectbox("Interest Type", INTEREST_TYPE_OPTIONS)

        with col2:
            st.markdown("**Dates & Status**")
            start_date = st.date_input("Repayment Start Date", value=datetime.now())
            status = st.selectbox("Loan Status", STATUS_OPTIONS)
            repayment_plan = st.selectbox("Repayment Plan", REPAYMENT_PLAN_OPTIONS)
            plan_end_date = st.text_input("Plan End Date", placeholder="MM/DD/YYYY")
            estimated_payoff = st.text_input("Estimated Payoff Date", placeholder="MM/DD/YYYY")

        st.divider()
        st.markdown("**Additional Details** (optional — for student loans, etc.)")
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            school = st.text_input("School", placeholder="e.g., Penn State University")
        with dc2:
            current_owner = st.text_input("Current Owner", placeholder="e.g., U.S. Dept of Education")
        with dc3:
            guarantor = st.text_input("Guarantor", placeholder="e.g., Dept of Ed")
        borrower_benefits = st.text_input("Borrower Benefits", placeholder="e.g., Interest Rate Reduction")

        if st.button("Add Loan", type="primary"):
            if loan_name:
                income_loan.add_loan(
                    loan_name, principal,
                    interest_rate / 100,
                    monthly_payment,
                    start_date.strftime('%Y-%m-%d'),
                    loan_type,
                    current_balance=current_balance,
                    unpaid_principal=current_balance,
                    status=status,
                    repayment_plan=repayment_plan,
                    repayment_plan_end_date=plan_end_date,
                    repayment_start_date=start_date.strftime('%Y-%m-%d'),
                    estimated_payoff_date=estimated_payoff,
                    interest_type=interest_type,
                    school=school,
                    current_owner=current_owner,
                    guarantor=guarantor,
                    borrower_benefits=borrower_benefits,
                )
                st.success(f"Added loan: {loan_name}")
                st.rerun()
            else:
                st.error("Please enter a loan name")

    # ================================================================== #
    #  TAB 3: Strategies                                                  #
    # ================================================================== #
    with tab3:
        st.subheader("Debt Payoff Strategies")

        if not income_loan.loans:
            st.info("Add loans first to see payoff strategies!")
        else:
            strategy_type = st.radio("Strategy", ["Avalanche (Save Most Money)", "Snowball (Quick Wins)"])

            if strategy_type.startswith("Avalanche"):
                strategy = income_loan.avalanche_strategy()
                st.write("### Debt Avalanche Strategy")
                st.write("Pay off highest interest rate first — mathematically optimal")
            else:
                strategy = income_loan.snowball_strategy()
                st.write("### Debt Snowball Strategy")
                st.write("Pay off smallest balance first — psychological wins")

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

    # ================================================================== #
    #  TAB 4: Compare Payoff                                              #
    # ================================================================== #
    with tab4:
        st.subheader("Compare Payoff Strategies")
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
                        width="stretch"
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
                    st.plotly_chart(fig, width="stretch")

                    best = comp_df[comp_df['Interest Saved'] == comp_df['Interest Saved'].max()].iloc[0]
                    st.success(
                        f"Paying ${best['Extra/Month']:.0f} extra/month saves "
                        f"**${best['Interest Saved']:,.2f}** in interest and pays off "
                        f"**{comparisons[0]['months_to_payoff'] - best['Months']} months earlier**"
                    )

        st.divider()
        st.subheader("Auto-Detect Loan Payments")
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
                    st.success("Scan complete — check Payment History tab for results")
                    st.rerun()
                else:
                    st.error("Enter at least one keyword")

    # ================================================================== #
    #  TAB 5: Payment History                                             #
    # ================================================================== #
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
                    width="stretch"
                )
            else:
                st.info("No payments recorded yet!")
