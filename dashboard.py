#!/usr/bin/env python3
"""
Streamlit Dashboard for Advanced Budget Tracker
Run with: streamlit run dashboard.py
"""
import json
import streamlit as st
from pathlib import Path

from advanced_tracker import AdvancedBudgetTracker
from income_loan_tracker import IncomeAndLoanTracker
from savings_goals import SavingsGoalsTracker

import page_live_view
import page_sort
import page_savings_goals
import page_upload
import page_loan_tracker
import page_transactions
import page_recurring
import page_trends
import page_settings

# Page config
st.set_page_config(
    page_title="Budget Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)


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


def load_budgets():
    if Path('budgets.json').exists():
        with open('budgets.json', 'r') as f:
            return json.load(f)
    return {}


def save_budgets(budgets):
    with open('budgets.json', 'w') as f:
        json.dump(budgets, f, indent=2)


# Sidebar navigation — grouped with sub-items indented via ideographic spaces
st.sidebar.markdown(
    """<style>
    /* Make indented sub-items slightly smaller / muted */
    div[data-testid="stSidebar"] label[data-baseweb="radio"] > div:first-child + div {
        font-size: 0.95rem;
    }
    </style>""",
    unsafe_allow_html=True,
)
st.sidebar.title("💰 Budget Tracker")

# Build grouped navigation with visual hierarchy
NAV_ITEMS = [
    "📊 Live View",
    "　　📈 Trends",
    "📝 All Transactions",
    "　　🗂️ Sort Transactions",
    "　　🔄 Recurring",
    "💰 Savings Goals",
    "💳 Loan Tracker",
    "📤 Upload Documents",
    "⚙️ Settings & Tools",
]

# Map indented labels back to clean names for routing
LABEL_MAP = {item: item.lstrip("　") for item in NAV_ITEMS}

page_raw = st.sidebar.radio("Navigate", NAV_ITEMS, label_visibility="collapsed")
page = LABEL_MAP[page_raw]

# Route to page modules
if page == "📊 Live View":
    page_live_view.render(tracker, load_budgets, savings_goals, income_loan)

elif page == "🗂️ Sort Transactions":
    page_sort.render(tracker)

elif page == "💰 Savings Goals":
    page_savings_goals.render(savings_goals)

elif page == "📤 Upload Documents":
    page_upload.render(tracker)

elif page == "💳 Loan Tracker":
    page_loan_tracker.render(income_loan)

elif page == "📝 All Transactions":
    page_transactions.render(tracker, income_loan)

elif page == "🔄 Recurring":
    page_recurring.render(tracker)

elif page == "📈 Trends":
    page_trends.render(tracker)

elif page == "⚙️ Settings & Tools":
    page_settings.render(tracker, income_loan, savings_goals, load_budgets, save_budgets)

# Sidebar footer
st.sidebar.divider()
st.sidebar.info("""💡 **Quick Tips**

• Upload statements in Upload tab
• Set savings goals
• Track loan payoff
• Monitor spending trends""")

