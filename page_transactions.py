import streamlit as st

UNCATEGORIZED_LABELS = {'UNCATEGORIZED', 'Other Income'}


def render(tracker, income_loan):
    st.title("📝 Transactions")

    if tracker.transaction_db.empty:
        st.warning("No transactions yet — upload a CSV first.")
        st.stop()

    tab1, tab2 = st.tabs([
        "All Transactions",
        f"🔴 Uncategorized ({len(tracker.transaction_db[tracker.transaction_db['Category'].isin(UNCATEGORIZED_LABELS)])})",
    ])

    # ------------------------------------------------------------------ #
    #  TAB 1: All transactions with filters                                #
    # ------------------------------------------------------------------ #
    with tab1:
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
                ['All'] + sorted(
                    tracker.transaction_db['Date'].dt.to_period('M').astype(str).unique().tolist(),
                    reverse=True,
                )
            )

        df = tracker.transaction_db.copy()
        if selected_category != 'All':
            df = df[df['Category'] == selected_category]
        if selected_source != 'All':
            df = df[df['Source'] == selected_source]
        if month_filter != 'All':
            df = df[df['Date'].dt.to_period('M').astype(str) == month_filter]

        st.dataframe(
            df[['Date', 'Description', 'Normalized_Merchant', 'Category', 'Amount',
                'Source', 'Tax_Deductible']]
            .sort_values('Date', ascending=False),
            use_container_width=True,
            height=500,
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Transactions", len(df))
        with col2:
            st.metric("Income", f"${df[df['Amount'] > 0]['Amount'].sum():,.2f}")
        with col3:
            st.metric("Expenses", f"${abs(df[df['Amount'] < 0]['Amount'].sum()):,.2f}")

        st.divider()
        st.subheader("🔧 Quick Actions")

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Teach Categorization**")
            keyword = st.text_input("Keyword", key="learn_keyword")
            category = st.selectbox(
                "Category", sorted(tracker.category_rules.keys()), key="learn_category"
            )
            if st.button("Learn", key="learn_btn"):
                if keyword:
                    tracker.learn_category(keyword, category)
                    st.success(f"✓ '{keyword}' → {category}")
                    st.rerun()

        with col2:
            st.write("**Normalize Merchant**")
            raw_name = st.text_input("Raw Name", key="norm_raw")
            clean_name = st.text_input("Clean Name", key="norm_clean")
            if st.button("Normalize", key="norm_btn"):
                if raw_name and clean_name:
                    tracker.learn_merchant_normalization(raw_name, clean_name)
                    st.success(f"✓ '{raw_name}' → '{clean_name}'")
                    st.rerun()

        st.divider()
        st.subheader("🏷️ Tag Tax Deductible")
        st.caption("Row index from the table above (leftmost number)")
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            tax_txn_id = st.number_input("Row #", min_value=0, step=1, key="tax_txn_id")
        with col2:
            is_deductible = st.checkbox("Deductible", value=True, key="tax_deductible_check")
        with col3:
            tax_notes = st.text_input(
                "Notes", placeholder="e.g. Home office, business travel", key="tax_notes"
            )
        if st.button("Tag", key="tag_tax_btn"):
            if tax_txn_id < len(tracker.transaction_db):
                tracker.tag_tax_deductible(int(tax_txn_id), is_deductible, tax_notes)
                label = "deductible" if is_deductible else "not deductible"
                st.success(f"✓ Row {int(tax_txn_id)} marked {label}")
                st.rerun()
            else:
                st.error(f"Row {int(tax_txn_id)} not found")

        st.divider()
        st.subheader("✂️ Split Transaction")
        st.caption("Split one transaction across multiple categories")
        split_txn_id = st.number_input("Row # to split", min_value=0, step=1, key="split_txn_id")
        if split_txn_id < len(tracker.transaction_db):
            txn = tracker.transaction_db.iloc[int(split_txn_id)]
            st.info(
                f"**{txn['Normalized_Merchant']}** — "
                f"${abs(txn['Amount']):.2f} on {txn['Date'].strftime('%Y-%m-%d')}"
            )
        num_splits = st.number_input(
            "Number of splits", min_value=2, max_value=5, value=2, key="num_splits"
        )
        splits = []
        split_cols = st.columns(int(num_splits))
        all_categories = sorted(tracker.category_rules.keys())
        for i, col in enumerate(split_cols):
            with col:
                cat = st.selectbox(f"Category {i+1}", all_categories, key=f"split_cat_{i}")
                amt = st.number_input(
                    f"Amount {i+1}", min_value=0.01, value=1.0, step=0.01, key=f"split_amt_{i}"
                )
                splits.append({'category': cat, 'amount': amt, 'tax_deductible': False})
        if st.button("Apply Split", key="apply_split_btn"):
            if split_txn_id < len(tracker.transaction_db):
                split_id = tracker.split_transaction(int(split_txn_id), splits)
                st.success(f"✓ Split into {len(splits)} categories (ID: {split_id})")
                st.rerun()
            else:
                st.error(f"Row {int(split_txn_id)} not found")

    # ------------------------------------------------------------------ #
    #  TAB 2: Uncategorized / review queue                                 #
    # ------------------------------------------------------------------ #
    with tab2:
        unknown_df = tracker.transaction_db[
            tracker.transaction_db['Category'].isin(UNCATEGORIZED_LABELS)
        ].sort_values('Date', ascending=False).copy()

        if unknown_df.empty:
            st.success("✅ All transactions are categorized!")
            st.stop()

        st.info(
            f"**{len(unknown_df)} transactions** need a category. "
            "Teach a keyword below and they'll be re-categorized automatically."
        )

        # Show the uncategorized table
        st.dataframe(
            unknown_df[['Date', 'Description', 'Normalized_Merchant', 'Amount', 'Source',
                         'Category']]
            .reset_index(drop=True),
            use_container_width=True,
            height=350,
        )

        st.divider()
        st.subheader("Categorize by keyword")
        st.caption(
            "Type any part of the merchant/description, pick a category, "
            "then hit **Apply** — all matching transactions get re-categorized."
        )

        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            unk_keyword = st.text_input(
                "Keyword (case-insensitive)",
                placeholder="e.g. ALDI, Paragon, VENMO",
                key="unk_keyword",
            )
        with col2:
            unk_category = st.selectbox(
                "Assign category",
                sorted(tracker.category_rules.keys()),
                key="unk_category",
            )
        with col3:
            st.write("")
            st.write("")
            apply = st.button("Apply", type="primary", key="unk_apply")

        if apply and unk_keyword:
            tracker.learn_category(unk_keyword, unk_category)
            tracker.recategorize_all()
            remaining = tracker.transaction_db[
                tracker.transaction_db['Category'].isin(UNCATEGORIZED_LABELS)
            ]
            fixed = len(unknown_df) - len(remaining)
            st.success(
                f"✓ Taught '{unk_keyword}' → {unk_category} and re-categorized "
                f"{fixed} transaction(s)."
            )
            st.rerun()

        st.divider()
        st.subheader("Re-run categorization on all transactions")
        st.caption("Useful after teaching several new keywords at once.")
        if st.button("🔄 Recategorize All", key="recategorize_all_btn"):
            tracker.recategorize_all()
            st.success("✓ All transactions re-categorized with current rules.")
            st.rerun()
