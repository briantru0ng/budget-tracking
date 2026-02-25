import tempfile
import streamlit as st
from pathlib import Path

# Map friendly source names to the bank key the parser expects.
# Used only for display — the parser auto-detects from CSV headers.
BANK_LABELS = {
    'PNC (Checking / Debit)': 'PNC',
    'Capital One': 'Capital One',
    'Citi': 'Citi',
    'Discover': 'Discover',
    'Other / Unknown': None,
}


def render(tracker):
    st.title("📤 Upload Transactions")
    st.write("Export a CSV from your bank's website and drop it here.")

    uploaded_files = st.file_uploader(
        "Choose CSV files",
        type=['csv'],
        accept_multiple_files=True,
    )

    source_name = st.text_input(
        "Source label (appears in your transaction history)",
        placeholder="e.g. 'PNC Checking', 'Capital One Quicksilver'",
    )

    if uploaded_files and source_name and st.button("Import All Files", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        total_added = 0
        total_skipped = 0
        total_duplicates = 0

        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}…")

            temp_path = Path(tempfile.gettempdir()) / uploaded_file.name
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.getvalue())

            transactions, bank = tracker.extract_transactions_from_csv(
                str(temp_path), source_name
            )
            result = tracker.add_transactions(transactions, source_name)

            total_added += result['added']
            total_duplicates += result['duplicates']

            with st.expander(f"🔍 {uploaded_file.name} — {bank.upper()} format"):
                st.write(
                    f"**Detected bank:** `{bank}` | "
                    f"**Rows imported:** {len(transactions)} | "
                    f"**Added:** {result['added']} | "
                    f"**Duplicates skipped:** {result['duplicates']}"
                )
                if bank == 'unknown':
                    st.error(
                        "Could not detect bank format from headers. "
                        "Supported: PNC, Capital One, Citi, Discover."
                    )

            progress_bar.progress((i + 1) / len(uploaded_files))

        status_text.empty()
        progress_bar.empty()

        if total_added > 0:
            st.success(f"✓ Added {total_added} new transactions")
            st.balloons()
        else:
            st.warning("0 transactions added — check the diagnostics above.")

        if total_duplicates > 0:
            st.info(f"Skipped {total_duplicates} duplicates")

    st.divider()
    st.subheader("What gets filtered automatically")
    with st.expander("Filter rules by bank"):
        st.markdown("""
**PNC (Checking / Debit)**
- Skips credit card payments (Discover, Capital One) — already tracked on those cards
- Skips internal account transfers (`ONLINE TRANSFER TO/FROM XXXXX…`)
- Keeps Zelle to/from roommate (rent)
- Keeps all other Zelle, Venmo, and debit card purchases

**Capital One**
- Skips own payment credits (`CAPITAL ONE ONLINE/MOBILE PYMT`)
- All charges imported as expenses

**Citi**
- Skips payment credits (`ONLINE PAYMENT, THANK YOU`)
- All charges imported as expenses

**Discover**
- Skips `Payments and Credits` category rows
- All charges imported as expenses
        """)

    st.divider()
    st.subheader("Recent Uploads")

    if not tracker.transaction_db.empty:
        df = tracker.transaction_db.copy()
        source_stats = df.groupby('Source').agg(
            First=('Date', 'min'),
            Last=('Date', 'max'),
            Transactions=('Amount', 'count'),
        ).reset_index()
        source_stats.columns = ['Source', 'First Transaction', 'Last Transaction', 'Transactions']
        st.dataframe(source_stats, use_container_width=True)
    else:
        st.info("No transactions imported yet.")
