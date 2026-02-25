#!/usr/bin/env python3
"""
Streamlit Dashboard for Advanced Budget Tracker
Run with: streamlit run dashboard.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from pathlib import Path

# Import our tracker
from advanced_tracker import AdvancedBudgetTracker
from income_loan_tracker import IncomeAndLoanTracker
from savings_goals import SavingsGoalsTracker

# Page config
st.set_page_config(
    page_title="Budget Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize tracker
@st.cache_resource
def get_tracker():
    return AdvancedBudgetTracker()

@st.cache_resource
def get_income_loan_tracker():
    return IncomeAndLoanTracker(get_tracker())

@st.cache_resource
def get_savings_tracker():
    return SavingsGoalsTracker()

tracker = get_tracker()
income_loan = get_income_loan_tracker()
savings_goals = get_savings_tracker()

# Sidebar navigation
st.sidebar.title("💰 Budget Tracker")
page = st.sidebar.radio(
    "Navigate",
    [
        "📊 Live View", 
        "💰 Savings Goals", 
        "📤 Upload Documents", 
        "💳 Loan Tracker",
        "📝 All Transactions",
        "🔄 Recurring",
        "📈 Trends",
        "⚙️ Settings & Tools"
    ]
)

# Helper functions
def load_budgets():
    """Load budget targets"""
    if Path('budgets.json').exists():
        with open('budgets.json', 'r') as f:
            return json.load(f)
    return {}

def save_budgets(budgets):
    """Save budget targets"""
    with open('budgets.json', 'w') as f:
        json.dump(budgets, f, indent=2)

# ============================================================
# LIVE VIEW PAGE
# ============================================================
if page == "📊 Live View":
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
        merchant_spending = current_data[current_data['Amount'] < 0].groupby('Normalized_Merchant')['Amount'].sum().abs().sort_values(ascending=False).head(10)
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

# ============================================================
# SAVINGS GOALS PAGE
# ============================================================
elif page == "💰 Savings Goals":
    st.title("💰 Savings Goals")
    
    # Summary metrics at top
    all_goals = savings_goals.get_all_goals()
    
    if all_goals:
        col1, col2, col3, col4 = st.columns(4)
        
        total_target = savings_goals.get_total_savings_target()
        total_saved = savings_goals.get_total_saved()
        progress = (total_saved / total_target * 100) if total_target > 0 else 0
        
        with col1:
            st.metric("Total Goals", len(all_goals))
        with col2:
            st.metric("Total Target", f"${total_target:,.2f}")
        with col3:
            st.metric("Total Saved", f"${total_saved:,.2f}")
        with col4:
            st.metric("Overall Progress", f"{progress:.1f}%")
        
        st.divider()
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Active Goals", "Add New Goal", "Contribute", "Allocation Suggestion"])
    
    # TAB 1: Active Goals
    with tab1:
        if not all_goals:
            st.info("No savings goals yet! Create one in the 'Add New Goal' tab.")
        else:
            # Display each goal
            for goal in sorted(all_goals, key=lambda x: x['progress_pct'], reverse=True):
                with st.expander(f"{'✅' if goal['status'] == 'completed' else '📊'} {goal['name']} - {goal['progress_pct']:.1f}%", expanded=(goal['status'] != 'completed')):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Progress bar
                        st.progress(min(goal['progress_pct'] / 100, 1.0))
                        
                        # Details
                        st.write(f"**Target:** ${goal['target_amount']:,.2f}")
                        st.write(f"**Current:** ${goal['current_amount']:,.2f}")
                        st.write(f"**Remaining:** ${goal['remaining']:,.2f}")
                        st.write(f"**Deadline:** {goal['target_date']} ({goal['days_remaining']} days)")
                        
                        # Interest rate if set
                        if goal.get('interest_rate', 0) > 0:
                            st.write(f"**Interest Rate:** {goal['interest_rate'] * 100:.2f}% APY 💰")
                            if goal.get('interest_earned', 0) > 0:
                                st.write(f"**Interest Earned:** ${goal['interest_earned']:,.2f}")
                        
                        # Status indicator
                        status_colors = {
                            'completed': '🎉 Completed!',
                            'overdue': '⚠️ Overdue',
                            'urgent': '🔥 Urgent (< 30 days)',
                            'active': '✅ On Track' if goal['on_track'] else '⚠️ Behind Schedule'
                        }
                        st.write(f"**Status:** {status_colors[goal['status']]}")
                    
                    with col2:
                        # Pie chart
                        fig = go.Figure(data=[go.Pie(
                            values=[goal['current_amount'], goal['remaining']],
                            labels=['Saved', 'Remaining'],
                            hole=0.5,
                            marker_colors=['#00D9FF', '#E0E0E0']
                        )])
                        fig.update_layout(
                            showlegend=False,
                            height=200,
                            margin=dict(l=0, r=0, t=0, b=0)
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Monthly contribution needed
                    if goal['status'] != 'completed':
                        if goal.get('interest_rate', 0) > 0:
                            st.info(f"💡 Save ${goal['monthly_needed']:.2f}/month to reach your goal (with {goal['interest_rate']*100:.1f}% interest helping!)")
                            
                            # Show projection
                            if st.button(f"📊 See Projection", key=f"proj_{goal['goal_id']}"):
                                projection = savings_goals.project_with_interest(goal['goal_id'])
                                if projection:
                                    st.write(f"**With {goal['interest_rate']*100:.1f}% APY:**")
                                    st.write(f"- You'll contribute: ${projection['total_contributed']:,.2f}")
                                    st.write(f"- Interest will add: ${projection['total_interest']:,.2f} 💰")
                                    st.write(f"- Total saved: ${projection['final_balance']:,.2f}")
                                    st.success(f"Interest earns you ${projection['total_interest']:,.2f} for free!")
                        else:
                            st.info(f"💡 Save ${goal['monthly_needed']:.2f}/month to reach your goal")
                    
                    # Edit/Delete options
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"Edit", key=f"edit_{goal['goal_id']}"):
                            st.session_state[f'editing_{goal["goal_id"]}'] = True
                    
                    with col2:
                        if st.button(f"Add Contribution", key=f"contrib_{goal['goal_id']}"):
                            st.session_state[f'contributing_{goal["goal_id"]}'] = True
                    
                    with col3:
                        if st.button(f"🗑️ Delete", key=f"delete_{goal['goal_id']}"):
                            savings_goals.delete_goal(goal['goal_id'])
                            st.success(f"Deleted {goal['name']}")
                            st.rerun()
                    
                    # Edit form
                    if st.session_state.get(f'editing_{goal["goal_id"]}', False):
                        st.write("**Edit Goal**")
                        new_target = st.number_input("Target Amount", value=float(goal['target_amount']), key=f"edit_target_{goal['goal_id']}")
                        new_date = st.date_input("Target Date", value=datetime.strptime(goal['target_date'], '%Y-%m-%d'), key=f"edit_date_{goal['goal_id']}")
                        
                        if st.button("Save Changes", key=f"save_{goal['goal_id']}"):
                            savings_goals.update_goal(
                                goal['goal_id'],
                                target_amount=new_target,
                                target_date=new_date.strftime('%Y-%m-%d')
                            )
                            st.session_state[f'editing_{goal["goal_id"]}'] = False
                            st.success("Goal updated!")
                            st.rerun()
                    
                    # Contribute form
                    if st.session_state.get(f'contributing_{goal["goal_id"]}', False):
                        st.write("**Add Contribution**")
                        contrib_amount = st.number_input("Amount", min_value=0.01, key=f"contrib_amt_{goal['goal_id']}")
                        contrib_notes = st.text_input("Notes (optional)", key=f"contrib_notes_{goal['goal_id']}")
                        
                        if st.button("Add", key=f"add_contrib_{goal['goal_id']}"):
                            milestone = savings_goals.add_contribution(
                                goal['goal_id'],
                                contrib_amount,
                                notes=contrib_notes
                            )
                            st.session_state[f'contributing_{goal["goal_id"]}'] = False
                            
                            if milestone:
                                st.balloons()
                                st.success(f"🎉 Milestone reached: {milestone}!")
                            else:
                                st.success(f"Added ${contrib_amount:.2f}!")
                            st.rerun()
    
    # TAB 2: Add New Goal
    with tab2:
        st.subheader("Create New Savings Goal")
        
        col1, col2 = st.columns(2)
        
        with col1:
            goal_name = st.text_input("Goal Name", placeholder="e.g., Emergency Fund, Europe Trip")
            target_amount = st.number_input("Target Amount ($)", min_value=1.0, value=1000.0, step=100.0)
            target_date = st.date_input("Target Date", value=datetime.now() + timedelta(days=365))
        
        with col2:
            category = st.selectbox(
                "Category",
                ["emergency", "vacation", "house", "car", "education", "wedding", "general"]
            )
            priority = st.selectbox("Priority", ["high", "medium", "low"])
            current_amount = st.number_input("Current Amount (if any)", min_value=0.0, value=0.0)
            interest_rate = st.number_input(
                "Interest Rate (% APY)",
                min_value=0.0,
                max_value=20.0,
                value=0.0,
                step=0.1,
                help="Enter interest rate for HYSA, savings accounts, or investment accounts"
            )
        
        notes = st.text_area("Notes (optional)")
        
        if st.button("Create Goal", type="primary"):
            if goal_name:
                goal_id = savings_goals.add_goal(
                    goal_name,
                    target_amount,
                    target_date.strftime('%Y-%m-%d'),
                    category,
                    current_amount,
                    priority,
                    notes,
                    interest_rate / 100  # Convert percentage to decimal
                )
                st.success(f"✓ Created goal: {goal_name}")
                
                summary = savings_goals.get_goal_summary(goal_id)
                if interest_rate > 0:
                    st.info(f"💡 With {interest_rate:.1f}% APY, you'll need to save ${summary['monthly_needed']:.2f}/month (interest helps!)")
                else:
                    st.info(f"💡 You'll need to save ${summary['monthly_needed']:.2f}/month to reach your goal")
                st.rerun()
            else:
                st.error("Please enter a goal name")
    
    # TAB 3: Quick Contribute
    with tab3:
        st.subheader("Add Contribution")
        
        if not all_goals:
            st.info("Create a goal first!")
        else:
            goal_options = {goal['name']: goal['goal_id'] for goal in all_goals if goal['status'] != 'completed'}
            
            if not goal_options:
                st.success("🎉 All goals completed!")
            else:
                selected_goal_name = st.selectbox("Select Goal", list(goal_options.keys()))
                selected_goal_id = goal_options[selected_goal_name]
                
                amount = st.number_input("Contribution Amount ($)", min_value=0.01, value=50.0, step=10.0)
                contrib_date = st.date_input("Date", value=datetime.now())
                contrib_notes = st.text_input("Notes (optional)")
                
                if st.button("Add Contribution", type="primary"):
                    milestone = savings_goals.add_contribution(
                        selected_goal_id,
                        amount,
                        contrib_date.strftime('%Y-%m-%d'),
                        contrib_notes
                    )
                    
                    if milestone:
                        st.balloons()
                        st.success(f"🎉 Milestone reached: {milestone}!")
                    else:
                        st.success(f"✓ Added ${amount:.2f} to {selected_goal_name}")
                    
                    # Show updated progress
                    summary = savings_goals.get_goal_summary(selected_goal_id)
                    st.info(f"Progress: {summary['progress_pct']:.1f}% - ${summary['current_amount']:,.2f} / ${summary['target_amount']:,.2f}")
                    st.rerun()
    
    # TAB 4: Allocation Suggestion
    with tab4:
        st.subheader("Smart Allocation Suggestion")
        
        if not all_goals:
            st.info("Create goals first to get allocation suggestions!")
        else:
            st.write("Enter how much you can save monthly, and we'll suggest how to allocate it across your goals based on priority and urgency.")
            
            monthly_budget = st.number_input("Monthly Savings Budget ($)", min_value=0.0, value=500.0, step=50.0)
            
            if st.button("Get Suggestion"):
                allocations = savings_goals.suggest_allocation(monthly_budget)
                
                st.write("### 💡 Suggested Allocation")
                
                # Create visualization
                data = []
                for goal_id, amount in allocations.items():
                    goal = savings_goals.goals[goal_id]
                    data.append({
                        'Goal': goal['name'],
                        'Suggested': amount,
                        'Needed': goal['monthly_contribution_needed'],
                        'Priority': goal['priority']
                    })
                
                df = pd.DataFrame(data)
                
                # Bar chart
                fig = px.bar(
                    df,
                    x='Goal',
                    y=['Suggested', 'Needed'],
                    barmode='group',
                    title="Suggested vs Needed Monthly Contributions"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Table
                st.dataframe(
                    df.style.format({
                        'Suggested': '${:,.2f}',
                        'Needed': '${:,.2f}'
                    }),
                    use_container_width=True
                )
                
                total_allocated = df['Suggested'].sum()
                if total_allocated < monthly_budget:
                    st.success(f"💰 Surplus: ${monthly_budget - total_allocated:.2f} available for additional savings or other goals")
                elif total_allocated == monthly_budget:
                    st.info(f"✅ Perfect! Full budget allocated: ${total_allocated:.2f}")
                else:
                    st.warning(f"⚠️ Goals need ${total_allocated:.2f}/month but budget is ${monthly_budget:.2f}")

# ============================================================
# UPLOAD DOCUMENTS PAGE
# ============================================================
elif page == "📤 Upload Documents":
    st.title("📤 Upload Documents")
    
    st.write("Upload your bank statements, credit card statements, or other financial documents.")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=['pdf'],
        accept_multiple_files=True
    )
    
    source_name = st.text_input(
        "Source Name",
        placeholder="e.g., 'Chase Sapphire', 'Bank of America Checking'",
        help="Give this source a recognizable name"
    )
    
    if uploaded_files and source_name and st.button("Process All Files", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_added = 0
        total_duplicates = 0
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}...")
            
            # Save temp file
            temp_path = Path(f"/tmp/{uploaded_file.name}")
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
            
            # Process
            transactions = tracker.extract_transactions_from_pdf(str(temp_path), source_name)
            result = tracker.add_transactions(transactions, source_name)
            
            total_added += result['added']
            total_duplicates += result['duplicates']
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        status_text.empty()
        progress_bar.empty()
        
        st.success(f"✓ Processed {len(uploaded_files)} files")
        st.info(f"Added {total_added} new transactions")
        
        if total_duplicates > 0:
            st.warning(f"Skipped {total_duplicates} duplicates")
        
        st.balloons()
    
    st.divider()
    
    # Recent uploads
    st.subheader("Recent Activity")
    
    if not tracker.transaction_db.empty:
        df = tracker.transaction_db.copy()
        
        # Group by source and show stats
        source_stats = df.groupby('Source').agg({
            'Date': ['min', 'max'],
            'Amount': 'count'
        }).reset_index()
        
        source_stats.columns = ['Source', 'First Transaction', 'Last Transaction', 'Total Transactions']
        
        st.dataframe(source_stats, use_container_width=True)

# ============================================================
# LOAN TRACKER PAGE
# ============================================================
elif page == "💳 Loan Tracker":
    st.title("💳 Loan Tracker")
    
    # Summary at top
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
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Active Loans", "Add Loan", "Strategies", "Payment History"])
    
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
                        # Loan details
                        st.write(f"**Balance:** ${loan['current_balance']:,.2f}")
                        st.write(f"**Original:** ${loan['principal']:,.2f}")
                        st.write(f"**Interest Rate:** {loan['interest_rate'] * 100:.2f}%")
                        st.write(f"**Monthly Payment:** ${loan['monthly_payment']:,.2f}")
                        
                        if payoff and 'months_to_payoff' in payoff:
                            st.write(f"**Payoff Date:** {payoff['payoff_date']} ({payoff['months_to_payoff']} months)")
                            st.write(f"**Total Interest:** ${payoff['total_interest']:,.2f}")
                        
                        # Progress bar
                        paid_pct = ((loan['principal'] - loan['current_balance']) / loan['principal']) * 100 if loan['principal'] > 0 else 0
                        st.progress(paid_pct / 100)
                        st.caption(f"{paid_pct:.1f}% paid off")
                    
                    with col2:
                        # What-if calculator
                        st.write("**What if I pay extra?**")
                        extra = st.number_input(
                            "Extra monthly",
                            min_value=0,
                            value=0,
                            step=50,
                            key=f"extra_{loan_id}"
                        )
                        
                        if extra > 0:
                            extra_payoff = income_loan.calculate_payoff_timeline(loan_id, extra)
                            if extra_payoff and 'months_to_payoff' in extra_payoff:
                                months_saved = payoff['months_to_payoff'] - extra_payoff['months_to_payoff']
                                interest_saved = payoff['total_interest'] - extra_payoff['total_interest']
                                
                                st.success(f"Save {months_saved} months")
                                st.success(f"Save ${interest_saved:,.2f}")
                    
                    # Record payment
                    if st.button(f"Record Payment", key=f"pay_{loan_id}"):
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
                                loan_id,
                                payment_amount,
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
                loan_id = income_loan.add_loan(
                    loan_name,
                    principal,
                    interest_rate / 100,  # Convert to decimal
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
            strategy_type = st.radio(
                "Strategy",
                ["Avalanche (Save Most Money)", "Snowball (Quick Wins)"]
            )
            
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
    
    # TAB 4: Payment History
    with tab4:
        st.subheader("Payment History")
        
        if not income_loan.loans:
            st.info("No loans yet!")
        else:
            # Aggregate all payments
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
                df = pd.DataFrame(all_payments)
                df = df.sort_values('Date', ascending=False)
                
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

# ============================================================
# TRANSACTIONS PAGE
# ============================================================
elif page == "📝 All Transactions":
    st.title("📝 All Transactions")
    
    if tracker.transaction_db.empty:
        st.warning("No transactions yet!")
        st.stop()
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        categories = ['All'] + sorted(tracker.transaction_db['Category'].unique().tolist())
        selected_category = st.selectbox("Category", categories)
    
    with col2:
        sources = ['All'] + sorted(tracker.transaction_db['Source'].unique().tolist())
        selected_source = st.selectbox("Source", sources)
    
    with col3:
        month_filter = st.selectbox(
            "Month",
            ['All'] + sorted(tracker.transaction_db['Date'].dt.to_period('M').astype(str).unique().tolist(), reverse=True)
        )
    
    # Apply filters
    df = tracker.transaction_db.copy()
    
    if selected_category != 'All':
        df = df[df['Category'] == selected_category]
    
    if selected_source != 'All':
        df = df[df['Source'] == selected_source]
    
    if month_filter != 'All':
        df = df[df['Date'].dt.to_period('M').astype(str) == month_filter]
    
    # Display
    st.dataframe(
        df[['Date', 'Normalized_Merchant', 'Category', 'Amount', 'Source', 'Tax_Deductible']].sort_values('Date', ascending=False),
        use_container_width=True,
        height=600
    )
    
    # Summary
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Transactions", len(df))
    with col2:
        st.metric("Total Income", f"${df[df['Amount'] > 0]['Amount'].sum():,.2f}")
    with col3:
        st.metric("Total Expenses", f"${abs(df[df['Amount'] < 0]['Amount'].sum()):,.2f}")
    
    # Quick actions
    st.divider()
    st.subheader("🔧 Quick Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Teach Categorization**")
        keyword = st.text_input("Keyword", key="learn_keyword")
        category = st.selectbox("Category", sorted(tracker.category_rules.keys()), key="learn_category")
        if st.button("Learn"):
            if keyword:
                tracker.learn_category(keyword, category)
                st.success(f"✓ Learned: '{keyword}' → {category}")
                st.rerun()
    
    with col2:
        st.write("**Normalize Merchant**")
        raw_name = st.text_input("Raw Name", key="norm_raw")
        clean_name = st.text_input("Clean Name", key="norm_clean")
        if st.button("Normalize"):
            if raw_name and clean_name:
                tracker.learn_merchant_normalization(raw_name, clean_name)
                st.success(f"✓ Normalized: '{raw_name}' → '{clean_name}'")
                st.rerun()

# ============================================================
# RECURRING PAGE
# ============================================================
elif page == "🔄 Recurring":
    st.title("🔄 Recurring Transactions")
    
    recurring = tracker.detect_recurring_transactions()
    
    if not recurring:
        st.info("No recurring transactions detected yet. Add more months of data!")
        st.stop()
    
    st.write(f"Found **{len(recurring)}** recurring transactions:")
    
    # Display as table
    recurring_df = pd.DataFrame.from_dict(recurring, orient='index')
    recurring_df = recurring_df.sort_values('amount', key=lambda x: x.abs(), ascending=False)
    
    st.dataframe(recurring_df, use_container_width=True)
    
    # Missing this month
    st.divider()
    st.subheader("⚠️ Missing This Month")
    
    missing = tracker.check_missing_recurring()
    if missing:
        for m in missing:
            st.warning(f"**{m['merchant']}** - ${m['amount']:.2f} - Expected: {m['expected_date']}")
    else:
        st.success("✓ All recurring transactions present this month!")

# ============================================================
# TRENDS PAGE
# ============================================================
elif page == "📈 Trends":
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
    
    fig = px.line(
        savings_df,
        x='Month',
        y='Savings_Rate',
        title="Savings Rate Trend",
        markers=True
    )
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

# ============================================================
# SETTINGS & TOOLS PAGE
# ============================================================
elif page == "⚙️ Settings & Tools":
    st.title("⚙️ Settings & Tools")
    
    # Tabs for different tools
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💰 Apply Interest", 
        "🔍 Income Breakdown",
        "🧹 Duplicates", 
        "🏷️ Categorization",
        "💾 Budgets"
    ])
    
    # TAB 1: Apply Interest
    with tab1:
        st.subheader("💰 Apply Interest to Savings Goals")
        st.write("Manually compound interest on your savings goals (use for monthly interest payments)")
        
        all_goals = savings_goals.get_all_goals()
        interest_goals = [g for g in all_goals if g.get('interest_rate', 0) > 0]
        
        if not interest_goals:
            st.info("No goals with interest rates set. Add interest rates to your goals in the Savings Goals tab!")
        else:
            selected_goal_name = st.selectbox(
                "Select Goal",
                [g['name'] for g in interest_goals],
                key="interest_goal"
            )
            
            selected_goal = next(g for g in interest_goals if g['name'] == selected_goal_name)
            
            st.info(f"**{selected_goal['name']}**\n"
                   f"- Current Balance: ${selected_goal['current_amount']:,.2f}\n"
                   f"- Interest Rate: {selected_goal['interest_rate'] * 100:.2f}% APY")
            
            months = st.number_input(
                "Number of Months to Compound",
                min_value=1,
                max_value=12,
                value=1,
                help="Typically 1 month for monthly interest payments"
            )
            
            # Preview calculation
            monthly_rate = selected_goal['interest_rate'] / 12
            preview_interest = selected_goal['current_amount'] * monthly_rate * months
            preview_new_balance = selected_goal['current_amount'] + preview_interest
            
            st.write("**Preview:**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Interest to Add", f"${preview_interest:.2f}")
            with col2:
                st.metric("New Balance", f"${preview_new_balance:.2f}")
            
            if st.button("Apply Interest", type="primary", key="apply_interest_btn"):
                interest_earned = savings_goals.apply_interest(selected_goal['goal_id'], months)
                if interest_earned:
                    st.success(f"✓ Applied {months} month(s) of interest")
                    st.success(f"💰 Interest earned: ${interest_earned:.2f}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Failed to apply interest")
        
        st.divider()
        
        # Batch apply to all
        if interest_goals:
            st.subheader("Apply to All Goals")
            st.write("Apply 1 month of interest to all interest-bearing goals at once")
            
            if st.button("Apply to All Goals", key="apply_all_interest"):
                total_interest = 0
                for goal in interest_goals:
                    interest = savings_goals.apply_interest(goal['goal_id'], 1)
                    if interest:
                        total_interest += interest
                
                st.success(f"✓ Applied interest to {len(interest_goals)} goals")
                st.success(f"💰 Total interest earned: ${total_interest:.2f}")
                st.balloons()
                st.rerun()
    
    # TAB 2: Income Breakdown
    with tab2:
        st.subheader("🔍 Income Stream Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=90))
        with col2:
            end_date = st.date_input("End Date", value=datetime.now())
        
        if st.button("Analyze Income", type="primary"):
            income_loan.recategorize_income()
            breakdown = income_loan.get_income_breakdown(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if breakdown:
                st.write(f"### Income Breakdown ({start_date} to {end_date})")
                
                # Create dataframe
                data = []
                total = 0
                for stream, stats in breakdown.items():
                    data.append({
                        'Stream': stream,
                        'Total': stats['sum'],
                        'Count': stats['count'],
                        'Average': stats['mean']
                    })
                    total += stats['sum']
                
                df = pd.DataFrame(data).sort_values('Total', ascending=False)
                
                # Pie chart
                fig = px.pie(
                    df,
                    values='Total',
                    names='Stream',
                    title=f"Total Income: ${total:,.2f}"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Table
                st.dataframe(
                    df.style.format({
                        'Total': '${:,.2f}',
                        'Average': '${:,.2f}'
                    }),
                    use_container_width=True
                )
            else:
                st.info("No income transactions found in this date range")
        
        st.divider()
        
        # Teach income categorization
        st.subheader("Teach Income Categorization")
        
        col1, col2 = st.columns(2)
        with col1:
            keyword = st.text_input("Keyword (e.g., 'mom', 'dad', 'venmo from john')")
        with col2:
            stream = st.selectbox(
                "Income Stream",
                ["Salary", "Side_Income", "Investments", "Gifts", "Refunds", "Government", "Rental", "Business"]
            )
        
        if st.button("Teach", key="teach_income"):
            if keyword:
                income_loan.income_streams[stream].append(keyword.lower())
                income_loan.save_income_streams()
                st.success(f"✓ Learned: '{keyword}' → {stream}")
                st.info("Tip: Go to All Transactions and use 'Recategorize All' to apply this rule")
            else:
                st.error("Please enter a keyword")
    
    # TAB 3: Duplicates
    with tab3:
        st.subheader("🧹 Duplicate Detection & Cleanup")
        
        if tracker.transaction_db.empty:
            st.info("No transactions to scan")
        else:
            if st.button("🔍 Scan for Duplicates", type="primary"):
                df = tracker.transaction_db.copy()
                
                # Method 1: Exact duplicates
                exact_dups = df[df.duplicated(subset=['Date', 'Description', 'Amount'], keep=False)]
                exact_dups = exact_dups.sort_values(['Date', 'Description', 'Amount'])
                
                # Method 2: Same day + amount + merchant
                likely_dups = []
                df_sorted = df.sort_values(['Date', 'Amount'])
                for i in range(len(df_sorted) - 1):
                    curr = df_sorted.iloc[i]
                    next_txn = df_sorted.iloc[i + 1]
                    
                    if (curr['Date'] == next_txn['Date'] and 
                        curr['Amount'] == next_txn['Amount'] and
                        curr.get('Normalized_Merchant', '').lower() == next_txn.get('Normalized_Merchant', '').lower() and
                        curr['Description'] != next_txn['Description']):
                        
                        likely_dups.append({
                            'Date': curr['Date'].strftime('%Y-%m-%d'),
                            'Merchant': curr.get('Normalized_Merchant', 'Unknown'),
                            'Amount': curr['Amount'],
                            'Desc1': curr['Description'],
                            'Desc2': next_txn['Description']
                        })
                
                # Display results
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Exact Duplicates", len(exact_dups))
                with col2:
                    st.metric("Likely Duplicates", len(likely_dups))
                
                if not exact_dups.empty:
                    st.warning(f"⚠️ Found {len(exact_dups)} exact duplicate transactions")
                    with st.expander("View Exact Duplicates"):
                        st.dataframe(
                            exact_dups[['Date', 'Description', 'Amount', 'Source']],
                            use_container_width=True
                        )
                else:
                    st.success("✓ No exact duplicates found")
                
                if likely_dups:
                    st.warning(f"🤔 Found {len(likely_dups)} likely duplicate pairs")
                    with st.expander("View Likely Duplicates"):
                        for dup in likely_dups[:10]:
                            st.write(f"**{dup['Date']} - {dup['Merchant']} - ${dup['Amount']:.2f}**")
                            st.text(f"1: {dup['Desc1']}")
                            st.text(f"2: {dup['Desc2']}")
                            st.divider()
                else:
                    st.success("✓ No likely duplicates found")
        
        st.divider()
        
        # Auto-remove duplicates
        st.subheader("Auto-Remove Duplicates")
        st.warning("⚠️ This will remove ALL exact duplicate transactions (keeps first occurrence)")
        
        if st.button("🗑️ Remove All Duplicates", key="remove_dups"):
            before = len(tracker.transaction_db)
            tracker.transaction_db = tracker.transaction_db.drop_duplicates(
                subset=['Date', 'Description', 'Amount'],
                keep='first'
            ).reset_index(drop=True)
            tracker.save_transaction_db()
            after = len(tracker.transaction_db)
            removed = before - after
            
            if removed > 0:
                st.success(f"✓ Removed {removed} duplicate transactions")
                st.info(f"Database now has {after} transactions")
                st.rerun()
            else:
                st.info("No duplicates to remove")
    
    # TAB 4: Categorization
    with tab4:
        st.subheader("🏷️ Categorization Management")
        
        # Quick teach
        st.write("**Quick Teach**")
        col1, col2 = st.columns(2)
        with col1:
            keyword = st.text_input("Merchant Keyword", placeholder="e.g., wegmans, starbucks")
        with col2:
            category = st.selectbox(
                "Category",
                sorted(tracker.category_rules.keys())
            )
        
        if st.button("Add Keyword", type="primary", key="add_keyword"):
            if keyword:
                if tracker.learn_category(keyword, category):
                    st.success(f"✓ Learned: '{keyword}' → {category}")
                else:
                    st.info(f"'{keyword}' already in {category}")
            else:
                st.error("Please enter a keyword")
        
        st.divider()
        
        # Merchant normalization
        st.write("**Merchant Normalization**")
        st.caption("Clean up messy transaction names")
        
        col1, col2 = st.columns(2)
        with col1:
            raw_name = st.text_input("Raw Name", placeholder="e.g., AMZN MKTP US*2X4H8")
        with col2:
            clean_name = st.text_input("Clean Name", placeholder="e.g., Amazon")
        
        if st.button("Add Normalization", key="add_norm"):
            if raw_name and clean_name:
                tracker.learn_merchant_normalization(raw_name, clean_name)
                st.success(f"✓ Normalized: '{raw_name}' → '{clean_name}'")
            else:
                st.error("Please fill both fields")
        
        st.divider()
        
        # Recategorize all
        st.write("**Apply All Rules**")
        st.info("Re-run categorization on ALL transactions with updated rules")
        
        if st.button("🔄 Recategorize All Transactions", key="recat_all"):
            with st.spinner("Recategorizing..."):
                tracker.recategorize_all()
                income_loan.recategorize_income()
                st.success("✓ Recategorized all transactions!")
                st.rerun()
        
        st.divider()
        
        # View uncategorized
        st.write("**Uncategorized Transactions**")
        if not tracker.transaction_db.empty:
            uncategorized = tracker.transaction_db[tracker.transaction_db['Category'] == 'UNCATEGORIZED']
            
            st.metric("Uncategorized Count", len(uncategorized))
            
            if not uncategorized.empty:
                st.warning("These transactions need categorization:")
                st.dataframe(
                    uncategorized[['Date', 'Description', 'Amount', 'Source']].head(20),
                    use_container_width=True
                )
                
                if len(uncategorized) > 20:
                    st.caption(f"Showing first 20 of {len(uncategorized)} uncategorized transactions")
            else:
                st.success("✓ All transactions categorized!")
    
    # TAB 5: Budgets
    with tab5:
        st.subheader("💾 Budget Targets")
        st.write("Set monthly budget limits for each spending category")
        
        budgets = load_budgets()
        
        if not tracker.transaction_db.empty:
            categories = [cat for cat in tracker.transaction_db['Category'].unique() 
                         if cat not in ['Income', 'Other Income', 'UNCATEGORIZED']]
            
            st.write("Enter your monthly budget for each category:")
            
            updated_budgets = {}
            
            # Create columns for better layout
            cols = st.columns(2)
            for i, category in enumerate(sorted(categories)):
                with cols[i % 2]:
                    current_budget = budgets.get(category, 0)
                    new_budget = st.number_input(
                        category,
                        min_value=0.0,
                        value=float(current_budget),
                        step=50.0,
                        key=f"budget_{category}"
                    )
                    if new_budget > 0:
                        updated_budgets[category] = new_budget
            
            if st.button("💾 Save Budgets", type="primary", key="save_budgets"):
                save_budgets(updated_budgets)
                st.success("✓ Budgets saved!")
                st.info("Budget alerts will now appear in Live View")
                st.rerun()
        else:
            st.info("Add transactions first to set budgets")
        
        st.divider()
        
        # Budget summary
        if budgets:
            st.write("**Current Budgets**")
            total_budget = sum(budgets.values())
            st.metric("Total Monthly Budget", f"${total_budget:,.2f}")
            
            budget_df = pd.DataFrame([
                {'Category': cat, 'Budget': amt}
                for cat, amt in sorted(budgets.items(), key=lambda x: x[1], reverse=True)
            ])
            
            st.dataframe(
                budget_df.style.format({'Budget': '${:,.2f}'}),
                use_container_width=True,
                hide_index=True
            )

# Sidebar info
st.sidebar.divider()
st.sidebar.info(
    "💡 **Quick Tips**\n\n"
    "• Upload statements in Upload tab\n"
    "• Set savings goals\n"
    "• Track loan payoff\n"
    "• Monitor spending trends"
)
