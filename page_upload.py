import shutil
import tempfile
import pandas as pd
import streamlit as st
from pathlib import Path

STATEMENTS_DIR = Path(__file__).parent / "statements"
COMPLETED_DIR = Path(__file__).parent / "completed_statements"

BANK_LABELS = {
    'pnc': 'PNC Checking',
    'capital_one': 'Capital One',
    'citi': 'Citi',
    'discover': 'Discover',
    'unknown': 'Unknown',
}


def render(tracker):
    st.title("📤 Upload Transactions")

    # ------------------------------------------------------------------ #
    #  Batch import from statements/ folder                               #
    # ------------------------------------------------------------------ #
    csv_files = sorted(STATEMENTS_DIR.glob("*.csv")) + sorted(STATEMENTS_DIR.glob("*.CSV"))
    if csv_files:
        st.subheader(f"📁 Statements Folder ({len(csv_files)} file{'s' if len(csv_files) != 1 else ''})")
        with st.expander("Files to import", expanded=True):
            for f in csv_files:
                st.text(f"  • {f.name}")

        if st.button("Import All from Statements Folder", type="primary"):
            COMPLETED_DIR.mkdir(exist_ok=True)
            progress_bar = st.progress(0)
            status_text = st.empty()

            total_added = 0
            total_duplicates = 0
            errors = []

            for i, csv_file in enumerate(csv_files):
                status_text.text(f"Processing {csv_file.name}…")
                try:
                    headers = pd.read_csv(str(csv_file), nrows=0, dtype=str).columns.tolist()
                    bank = tracker._detect_csv_bank(headers)
                    source_label = BANK_LABELS.get(bank, bank)
                    transactions, bank = tracker.extract_transactions_from_csv(
                        str(csv_file), source_label
                    )
                    result = tracker.add_transactions(transactions, source_label)

                    total_added += result['added']
                    total_duplicates += result['duplicates']

                    with st.expander(f"🔍 {csv_file.name} — {bank.upper()} format"):
                        st.write(
                            f"**Detected bank:** `{bank}` | "
                            f"**Rows parsed:** {len(transactions)} | "
                            f"**Added:** {result['added']} | "
                            f"**Duplicates skipped:** {result['duplicates']}"
                        )

                    # Move to completed folder
                    dest = COMPLETED_DIR / csv_file.name
                    if dest.exists():
                        dest = COMPLETED_DIR / f"{csv_file.stem}_{i}{csv_file.suffix}"
                    shutil.move(str(csv_file), str(dest))

                except Exception as e:
                    errors.append((csv_file.name, str(e)))
                    with st.expander(f"❌ {csv_file.name} — ERROR"):
                        st.error(str(e))

                progress_bar.progress((i + 1) / len(csv_files))

            status_text.empty()
            progress_bar.empty()

            if total_added > 0:
                st.success(f"✓ Added {total_added} new transactions")
                st.balloons()
            elif not errors:
                st.warning("0 transactions added — all duplicates or empty files.")

            if total_duplicates > 0:
                st.info(f"Skipped {total_duplicates} duplicates")

            if errors:
                st.error(f"{len(errors)} file(s) failed — see details above")

            st.rerun()
    else:
        st.info("No CSV files in the `statements/` folder.")

    st.divider()

    # ------------------------------------------------------------------ #
    #  Manual drag-and-drop upload                                        #
    # ------------------------------------------------------------------ #
    st.subheader("Manual Upload")
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

    # ------------------------------------------------------------------ #
    #  Filter rules reference                                              #
    # ------------------------------------------------------------------ #
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
        source_stats.columns = [
            'Source', 'First Transaction', 'Last Transaction', 'Transactions'
        ]
        st.dataframe(source_stats, width="stretch")
    else:
        st.info("No transactions imported yet.")
