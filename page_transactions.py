import streamlit as st
import pandas as pd
from advanced_tracker import AdvancedBudgetTracker


def render(tracker, income_loan):
    st.title("📝 Transactions")

    if tracker.transaction_db.empty:
        st.warning("No transactions yet — upload a statement first.")
        st.stop()

    df_full = tracker.transaction_db.copy()
    # Ensure Budget_Date exists (used for month/year filtering)
    if 'Budget_Date' not in df_full.columns:
        df_full = AdvancedBudgetTracker._apply_budget_dates(df_full)

    # ---- Filters: Year, Month, Group, Category, Source ------------------- #
    month_names = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December",
    }
    basket_names = list(tracker.baskets.keys())

    col_y, col_m, col_grp, col_cat, col_src = st.columns(5)

    years = sorted(df_full['Budget_Date'].dt.year.unique(), reverse=True)
    with col_y:
        selected_year = st.selectbox("Year", ["All"] + [str(y) for y in years])

    # Build month list based on selected year
    if selected_year != "All":
        months_in_year = (
            df_full[df_full['Budget_Date'].dt.year == int(selected_year)]['Budget_Date']
            .dt.month.unique()
        )
        month_options = ["All"] + [
            month_names[m] for m in sorted(months_in_year, reverse=True)
        ]
    else:
        month_options = ["All"]

    with col_m:
        selected_month = st.selectbox("Month", month_options)

    with col_grp:
        selected_group = st.selectbox("Group", ["All"] + basket_names)

    # Category options cascade from selected group
    with col_cat:
        if selected_group != "All":
            cat_options = ["All"] + sorted(tracker.baskets.get(selected_group, []))
        else:
            cat_options = ["All"] + sorted(df_full['Category'].unique().tolist())
        selected_category = st.selectbox("Category", cat_options)

    with col_src:
        sources = ["All"] + sorted(df_full['Source'].unique().tolist())
        selected_source = st.selectbox("Source", sources)

    # ---- Apply filters ------------------------------------------------- #
    df = df_full.copy()
    if selected_year != "All":
        df = df[df['Budget_Date'].dt.year == int(selected_year)]
    if selected_month != "All":
        month_num = {v: k for k, v in month_names.items()}[selected_month]
        df = df[df['Budget_Date'].dt.month == month_num]
    if selected_group != "All":
        group_cats = tracker.baskets.get(selected_group, [])
        df = df[df['Category'].isin(group_cats)]
    if selected_category != "All":
        df = df[df['Category'] == selected_category]
    if selected_source != "All":
        df = df[df['Source'] == selected_source]

    df = df.sort_values('Date', ascending=False)

    # ---- Summary metrics ----------------------------------------------- #
    df_active = df[df['Category'] != 'SKIP']
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Transactions", len(df_active))
    with col2:
        st.metric("Income", f"${df_active[df_active['Amount'] > 0]['Amount'].sum():,.2f}")
    with col3:
        st.metric("Expenses", f"${abs(df_active[df_active['Amount'] < 0]['Amount'].sum()):,.2f}")

    st.divider()

    # ---- Transaction table (read-only, selectable) ---------------------- #
    all_categories = sorted(tracker.category_rules.keys())

    if df.empty:
        st.info("No transactions match the current filters.")
        st.stop()

    # Build display dataframe with original index preserved
    display_df = df[['Date', 'Description', 'Normalized_Merchant', 'Category',
                     'Amount', 'Source', 'Tax_Deductible']].copy()
    display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')

    # Add parent basket (group) column before Category
    display_df.insert(
        display_df.columns.get_loc('Category'),
        'Group',
        display_df['Category'].map(
            lambda c: tracker.get_basket_for_category(c) or ''
        ),
    )

    event = st.dataframe(
        display_df,
        column_config={
            "Date": st.column_config.TextColumn("Date"),
            "Description": st.column_config.TextColumn("Description", width="large"),
            "Normalized_Merchant": st.column_config.TextColumn("Merchant"),
            "Group": st.column_config.TextColumn("Group"),
            "Category": st.column_config.TextColumn("Category"),
            "Amount": st.column_config.NumberColumn("Amount", format="$ %.2f"),
            "Source": st.column_config.TextColumn("Source"),
            "Tax_Deductible": st.column_config.CheckboxColumn("Tax Ded."),
        },
        use_container_width=True,
        height=500,
        on_select="rerun",
        selection_mode="multi-row",
        key="txn_table",
    )

    # ---- Recategorize selected rows ------------------------------------ #
    selected_rows = event.selection.rows if event.selection else []
    selected_indices = [display_df.index[r] for r in selected_rows] if selected_rows else []

    st.subheader("🏷️ Recategorize")
    if selected_indices:
        sel_df = tracker.transaction_db.loc[selected_indices]
        st.caption(f"{len(selected_indices)} transaction(s) selected")
        for idx in selected_indices:
            row = tracker.transaction_db.loc[idx]
            st.text(f"  Row {idx}: {row['Normalized_Merchant']} — ${abs(row['Amount']):,.2f}")
    else:
        st.caption("Select rows in the table above, then pick Group → Category to recategorize.")

    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        recat_group = st.selectbox(
            "Group", ["— pick —"] + basket_names + ["Skip / Exclude"], key="recat_group"
        )
    with rc2:
        if recat_group == "Skip / Exclude":
            recat_cat = st.selectbox(
                "Category", ["SKIP"], key="recat_cat", disabled=True
            )
            recat_cat = "SKIP"
        elif recat_group != "— pick —" and recat_group in tracker.baskets:
            sub_options = tracker.baskets[recat_group]
            recat_cat = st.selectbox(
                "Category", sub_options if sub_options else ["(none)"], key="recat_cat"
            )
        else:
            recat_cat = st.selectbox(
                "Category", ["— pick group first —"], key="recat_cat", disabled=True
            )
    with rc3:
        st.write("")
        st.write("")
        apply_disabled = (
            not selected_indices
            or recat_group == "— pick —"
            or recat_cat in ("(none)", "— pick group first —")
        )
        if st.button("Apply", key="recat_apply", type="primary", disabled=apply_disabled):
            for idx in selected_indices:
                tracker.transaction_db.at[idx, 'Category'] = recat_cat
            tracker.save_transaction_db()
            st.success(
                f"Updated {len(selected_indices)} transaction(s) → {recat_group} > {recat_cat}"
            )
            # Clear table selection before rerun
            del st.session_state["txn_table"]
            st.rerun()

    st.divider()

    # ---- Quick Actions ------------------------------------------------- #
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
                st.success(f"Learned: '{keyword}' → {category}")
                st.rerun()

    with col2:
        st.write("**Normalize Merchant**")
        raw_name = st.text_input("Raw Name", key="norm_raw")
        clean_name = st.text_input("Clean Name", key="norm_clean")
        if st.button("Normalize", key="norm_btn"):
            if raw_name and clean_name:
                tracker.learn_merchant_normalization(raw_name, clean_name)
                st.success(f"Normalized: '{raw_name}' → '{clean_name}'")
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
            st.success(f"Row {int(tax_txn_id)} marked {label}")
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
            st.success(f"Split into {len(splits)} categories (ID: {split_id})")
            st.rerun()
        else:
            st.error(f"Row {int(split_txn_id)} not found")
