import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from advanced_tracker import AdvancedBudgetTracker

RECURRING_DB = 'recurring_transactions.json'


def render(tracker):
    st.title("🔄 Recurring Transactions")

    tracker.transaction_db = tracker.load_transaction_db()

    if tracker.transaction_db.empty:
        st.warning("No transactions yet — upload a statement first.")
        st.stop()

    tab_subs, tab_detected, tab_candidates = st.tabs([
        "📋 Subscriptions",
        "✅ Confirmed Recurring",
        "🔍 Possibly Recurring",
    ])

    # ================================================================== #
    #  TAB 1: Subscriptions (Services > Monthly / Yearly)                 #
    # ================================================================== #
    with tab_subs:
        df = tracker.transaction_db.copy()
        if 'Budget_Date' not in df.columns:
            df = AdvancedBudgetTracker._apply_budget_dates(df)
        df = df[df['Category'] != 'SKIP']
        df['_period'] = df['Budget_Date'].dt.to_period('M')

        # Period selector
        now = datetime.now()
        all_periods = sorted(df['_period'].unique(), reverse=True)
        period_labels = [p.strftime('%B %Y') for p in all_periods]
        current_period = pd.Period(now, freq='M')
        default_label = current_period.strftime('%B %Y')
        default_idx = period_labels.index(default_label) if default_label in period_labels else 0

        selected_label = st.selectbox("Period", period_labels, index=default_idx)
        selected_period = all_periods[period_labels.index(selected_label)]
        period_data = df[df['_period'] == selected_period]

        # Filter to Services basket
        services_cats = tracker.baskets.get('Services', [])
        if not services_cats:
            st.warning(
                "No categories in the **Services** basket. "
                "Go to **Settings & Tools > Baskets** to add sub-categories like "
                "'Monthly Subscriptions' and 'Yearly Subscriptions'."
            )
        else:
            monthly_cats = [c for c in services_cats if 'monthly' in c.lower()]
            yearly_cats = [c for c in services_cats if 'yearly' in c.lower() or 'annual' in c.lower()]
            other_cats = [c for c in services_cats if c not in monthly_cats and c not in yearly_cats]

            svc_data = period_data[
                (period_data['Category'].isin(services_cats)) & (period_data['Amount'] < 0)
            ].copy()
            svc_data['Amount'] = svc_data['Amount'].abs()
            merchant_col = 'Normalized_Merchant' if 'Normalized_Merchant' in svc_data.columns else 'Description'

            if svc_data.empty:
                st.info(f"No subscription/service charges for {selected_label}.")
            else:
                # Summary metrics
                total_recurring = svc_data['Amount'].sum()
                income_cats = set(tracker.baskets.get('Income', ['Income', 'Other Income']))
                income_total = period_data.loc[
                    period_data['Category'].isin(income_cats) & (period_data['Amount'] > 0), 'Amount'
                ].sum()

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Subscriptions", f"${total_recurring:,.2f}")
                with col2:
                    pct = (total_recurring / income_total * 100) if income_total > 0 else 0
                    st.metric("% of Income", f"{pct:.1f}%")
                with col3:
                    st.metric("Services", str(svc_data[merchant_col].nunique()))

                st.divider()

                # Monthly Subscriptions
                monthly_txns = svc_data[svc_data['Category'].isin(monthly_cats)]
                if not monthly_txns.empty:
                    st.subheader("Monthly Subscriptions")
                    by_merchant = monthly_txns.groupby(merchant_col)['Amount'].sum().sort_values(ascending=False)
                    rows = [{"Service": m, "Amount": a} for m, a in by_merchant.items()]
                    subtotal = by_merchant.sum()
                    rows.append({"Service": "**Subtotal**", "Amount": subtotal})

                    mdf = pd.DataFrame(rows)
                    mdf['Amount'] = mdf['Amount'].map(lambda x: f"$ {x:,.2f}")
                    st.table(mdf.set_index("Service"))

                # Yearly Subscriptions
                yearly_txns = svc_data[svc_data['Category'].isin(yearly_cats)]
                if not yearly_txns.empty:
                    st.subheader("Yearly Subscriptions")
                    by_merchant = yearly_txns.groupby(merchant_col)['Amount'].sum().sort_values(ascending=False)
                    rows = []
                    for m, a in by_merchant.items():
                        rows.append({"Service": m, "Amount": a, "Monthly Equiv.": f"$ {a / 12:,.2f}"})
                    subtotal = by_merchant.sum()
                    rows.append({"Service": "**Subtotal**", "Amount": subtotal, "Monthly Equiv.": f"$ {subtotal / 12:,.2f}"})

                    ydf = pd.DataFrame(rows)
                    ydf['Amount'] = ydf['Amount'].map(lambda x: f"$ {x:,.2f}" if isinstance(x, float) else x)
                    st.table(ydf.set_index("Service"))

                # Other Services
                other_txns = svc_data[svc_data['Category'].isin(other_cats)]
                if not other_txns.empty:
                    st.subheader("Other Services")
                    by_merchant = other_txns.groupby(merchant_col)['Amount'].sum().sort_values(ascending=False)
                    rows = [{"Service": m, "Amount": a} for m, a in by_merchant.items()]
                    subtotal = by_merchant.sum()
                    rows.append({"Service": "**Subtotal**", "Amount": subtotal})

                    odf = pd.DataFrame(rows)
                    odf['Amount'] = odf['Amount'].map(lambda x: f"$ {x:,.2f}")
                    st.table(odf.set_index("Service"))

    # ================================================================== #
    #  TAB 2: Confirmed Recurring                                         #
    # ================================================================== #
    with tab_detected:
        recurring = tracker.detect_recurring_transactions()

        if recurring:
            st.subheader(f"Confirmed Recurring ({len(recurring)})")
            recurring_df = pd.DataFrame.from_dict(recurring, orient='index')
            recurring_df = recurring_df.sort_values('amount', key=lambda x: x.abs(), ascending=False)
            st.dataframe(recurring_df, width="stretch")

            st.divider()
            st.subheader("⚠️ Missing This Month")

            missing = tracker.check_missing_recurring()
            if missing:
                for m in missing:
                    st.warning(f"**{m['merchant']}** - ${m['amount']:.2f} - Expected: {m['expected_date']}")
            else:
                st.success("✓ All recurring transactions present this month!")
        else:
            st.info("No recurring transactions detected yet (needs 3+ consecutive months).")

    # ================================================================== #
    #  TAB 3: Possibly Recurring                                          #
    # ================================================================== #
    with tab_candidates:
        st.caption(
            "Transactions from the same merchant with similar amounts that appeared 2+ times "
            "but don't yet meet the 3-consecutive-month threshold. "
            "Promote them to track as recurring."
        )

        recurring = tracker.detect_recurring_transactions()

        df = tracker.transaction_db.copy()
        df = df[df['Category'] != 'SKIP']
        df['Month'] = df['Date'].dt.to_period('M')
        df['Amount_Rounded'] = df['Amount'].round(0)

        candidates = []
        for merchant in df['Normalized_Merchant'].unique():
            merchant_txns = df[df['Normalized_Merchant'] == merchant]

            for amount in merchant_txns['Amount_Rounded'].unique():
                tolerance = abs(amount) * 0.10 if amount != 0 else 1.0
                amount_txns = merchant_txns[
                    (merchant_txns['Amount_Rounded'] >= amount - tolerance)
                    & (merchant_txns['Amount_Rounded'] <= amount + tolerance)
                ]

                months = amount_txns['Month'].unique()
                if len(months) < 2:
                    continue

                key = f"{merchant}|{amount}"
                if key in recurring:
                    continue

                avg_amount = amount_txns['Amount'].mean()
                candidates.append({
                    'merchant': merchant,
                    'avg_amount': avg_amount,
                    'occurrences': len(months),
                    'months': sorted([str(m) for m in months]),
                    'category': amount_txns.iloc[0]['Category'],
                    'last_seen': amount_txns['Date'].max().strftime('%Y-%m-%d'),
                    'avg_day': int(amount_txns['Date'].dt.day.mean()),
                    'sample_desc': amount_txns.iloc[0]['Description'][:60],
                })

        seen = {}
        for c in candidates:
            key = c['merchant']
            if key not in seen or c['occurrences'] > seen[key]['occurrences']:
                seen[key] = c
        candidates = sorted(seen.values(), key=lambda x: x['occurrences'], reverse=True)

        if not candidates:
            st.info("No candidates found. More transaction history will help detect patterns.")
        else:
            for i, c in enumerate(candidates):
                amount = c['avg_amount']
                if amount < 0:
                    box_color = "rgba(255, 60, 60, 0.12)"
                    border_color = "rgba(255, 60, 60, 0.4)"
                else:
                    box_color = "rgba(60, 200, 60, 0.12)"
                    border_color = "rgba(60, 200, 60, 0.4)"

                cols = st.columns([4, 1])

                with cols[0]:
                    months_str = ', '.join(c['months'])
                    st.markdown(
                        f'<div style="background:{box_color};border:1px solid {border_color};'
                        f'border-radius:8px;padding:8px 12px;margin-bottom:4px">'
                        f'<strong>{c["merchant"]}</strong> &mdash; '
                        f'<strong>${abs(amount):,.2f}</strong><br>'
                        f'<code style="font-size:0.85em">{c["sample_desc"]}</code><br>'
                        f'{c["occurrences"]} months: {months_str} &middot; '
                        f'avg day: {c["avg_day"]} &middot; {c["category"]}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                with cols[1]:
                    if st.button("Add to Recurring", key=f"promote_{i}"):
                        new_key = f"{c['merchant']}|{c['avg_amount']:.2f}"
                        tracker.recurring_db[new_key] = {
                            'merchant': c['merchant'],
                            'amount': round(c['avg_amount'], 2),
                            'category': c['category'],
                            'frequency': 'monthly',
                            'occurrences': c['occurrences'],
                            'last_seen': c['last_seen'],
                            'avg_day_of_month': c['avg_day'],
                        }
                        tracker.save_recurring_db()
                        st.success(f"✓ Added {c['merchant']} as recurring")
                        st.rerun()

                st.divider()
