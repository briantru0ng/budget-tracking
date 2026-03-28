import streamlit as st
import pandas as pd
import json
from pathlib import Path

RECURRING_DB = 'recurring_transactions.json'


def render(tracker):
    st.title("🔄 Recurring Transactions")

    recurring = tracker.detect_recurring_transactions()

    # ------------------------------------------------------------------ #
    #  Confirmed recurring                                                #
    # ------------------------------------------------------------------ #
    if recurring:
        st.subheader(f"Confirmed Recurring ({len(recurring)})")
        recurring_df = pd.DataFrame.from_dict(recurring, orient='index')
        recurring_df = recurring_df.sort_values('amount', key=lambda x: x.abs(), ascending=False)
        st.dataframe(recurring_df, use_container_width=True)

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

    # ------------------------------------------------------------------ #
    #  Possibly recurring — 2+ occurrences with similar amounts           #
    # ------------------------------------------------------------------ #
    st.divider()
    st.subheader("🔍 Possibly Recurring")
    st.caption(
        "Transactions from the same merchant with similar amounts that appeared 2+ times "
        "but don't yet meet the 3-consecutive-month threshold. "
        "Promote them to track as recurring."
    )

    if tracker.transaction_db.empty:
        st.info("No transactions yet.")
        return

    df = tracker.transaction_db.copy()
    df = df[df['Category'] != 'SKIP']
    df['Month'] = df['Date'].dt.to_period('M')
    df['Amount_Rounded'] = df['Amount'].round(0)

    # Find merchant+amount combos that appear in 2+ different months
    # but aren't already in the confirmed recurring list
    candidates = []
    for merchant in df['Normalized_Merchant'].unique():
        merchant_txns = df[df['Normalized_Merchant'] == merchant]

        for amount in merchant_txns['Amount_Rounded'].unique():
            # Allow ~10% tolerance for "close enough" amounts
            tolerance = abs(amount) * 0.10 if amount != 0 else 1.0
            amount_txns = merchant_txns[
                (merchant_txns['Amount_Rounded'] >= amount - tolerance)
                & (merchant_txns['Amount_Rounded'] <= amount + tolerance)
            ]

            months = amount_txns['Month'].unique()
            if len(months) < 2:
                continue

            # Skip if already confirmed recurring
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

    # Deduplicate candidates by merchant (keep the one with most occurrences)
    seen = {}
    for c in candidates:
        key = c['merchant']
        if key not in seen or c['occurrences'] > seen[key]['occurrences']:
            seen[key] = c
    candidates = sorted(seen.values(), key=lambda x: x['occurrences'], reverse=True)

    if not candidates:
        st.info("No candidates found. More transaction history will help detect patterns.")
        return

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
