import streamlit as st
import pandas as pd


def render(tracker):
    st.title("🔄 Recurring Transactions")

    recurring = tracker.detect_recurring_transactions()

    if not recurring:
        st.info("No recurring transactions detected yet. Add more months of data!")
        st.stop()

    st.write(f"Found **{len(recurring)}** recurring transactions:")

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
