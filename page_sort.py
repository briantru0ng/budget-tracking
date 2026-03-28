import streamlit as st
import pandas as pd


def render(tracker):
    st.title("🗂️ Sort Transactions")

    if tracker.transaction_db.empty:
        st.info("No transactions yet. Upload some statements first.")
        st.stop()

    uncategorized_labels = {'UNCATEGORIZED', 'Other Income'}
    unk = tracker.transaction_db[
        tracker.transaction_db['Category'].isin(uncategorized_labels)
    ]
    skipped = tracker.transaction_db[
        tracker.transaction_db['Category'] == 'SKIP'
    ]

    if unk.empty and skipped.empty:
        st.success("All transactions are categorized!")
        st.stop()

    basket_names = list(tracker.baskets.keys())

    # ================================================================== #
    #  Uncategorized transactions                                         #
    # ================================================================== #
    if not unk.empty:
        # Split into merchant-groupable vs case-by-case (Zelle/Venmo)
        case_by_case_patterns = ['ZELLE', 'VENMO']
        is_case_by_case = unk['Description'].str.upper().str.contains(
            '|'.join(case_by_case_patterns), na=False
        )
        unk_grouped = unk[~is_case_by_case]
        unk_individual = unk[is_case_by_case]

        st.caption(
            f"{len(unk)} uncategorized transaction(s). "
            "Pick a basket and sub-category, or skip to come back later."
        )

        # -------------------------------------------------------------- #
        #  Merchant-grouped sorting                                       #
        # -------------------------------------------------------------- #
        if not unk_grouped.empty:
            st.subheader(f"By Merchant ({len(unk_grouped)} transactions)")

            merchant_groups = (
                unk_grouped.groupby('Normalized_Merchant')
                .agg(Count=('Amount', 'size'), Total=('Amount', 'sum'),
                     Sample=('Description', 'first'),
                     DateMin=('Date', 'min'), DateMax=('Date', 'max'),
                     Sources=('Source', lambda x: ', '.join(sorted(x.unique()))))
                .sort_values('Count', ascending=False)
                .reset_index()
            )

            for idx, row in merchant_groups.iterrows():
                merchant = row['Normalized_Merchant']
                count = row['Count']
                total = row['Total']
                sample = row['Sample']
                date_min = pd.to_datetime(row['DateMin']).strftime('%m/%d/%Y')
                date_max = pd.to_datetime(row['DateMax']).strftime('%m/%d/%Y')
                sources = row['Sources']
                date_str = date_min if date_min == date_max else f"{date_min} – {date_max}"

                if total < 0:
                    box_color = "rgba(255, 60, 60, 0.12)"
                    border_color = "rgba(255, 60, 60, 0.4)"
                else:
                    box_color = "rgba(60, 200, 60, 0.12)"
                    border_color = "rgba(60, 200, 60, 0.4)"

                with st.container():
                    cols = st.columns([3, 2, 2, 0.5, 0.5])

                    with cols[0]:
                        st.markdown(
                            f'<div style="background:{box_color};border:1px solid {border_color};'
                            f'border-radius:8px;padding:8px 12px;margin-bottom:4px">'
                            f'<strong>{merchant}</strong><br>'
                            f'<code style="font-size:0.85em">{sample[:60]}</code><br>'
                            f'{count} txn(s) &mdash; <strong>${abs(total):,.2f}</strong> &middot; '
                            f'{date_str} &middot; {sources}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                    with cols[1]:
                        basket = st.selectbox(
                            "Basket",
                            ['— pick —'] + basket_names,
                            key=f"bsk_{idx}",
                            label_visibility="collapsed",
                        )

                    with cols[2]:
                        if basket != '— pick —' and basket in tracker.baskets:
                            subs = tracker.baskets[basket]
                            sub = st.selectbox(
                                "Sub",
                                subs if subs else ['(none)'],
                                key=f"sub_{idx}",
                                label_visibility="collapsed",
                            )
                        else:
                            sub = st.selectbox(
                                "Sub",
                                ['— pick basket first —'],
                                key=f"sub_{idx}",
                                label_visibility="collapsed",
                                disabled=True,
                            )

                    with cols[3]:
                        if st.button("✓", key=f"sort_{idx}"):
                            if basket != '— pick —' and sub not in (
                                '(none)', '— pick basket first —'
                            ):
                                keyword = merchant.lower()
                                tracker.learn_category(keyword, sub)
                                tracker.recategorize_all()
                                st.success(f"'{merchant}' → {basket} > {sub}")
                                st.rerun()
                            else:
                                st.error("Pick a basket and sub-category first")

                    with cols[4]:
                        if st.button("⏭", key=f"skip_{idx}", help="Skip — won't count in totals"):
                            mask = tracker.transaction_db['Normalized_Merchant'] == merchant
                            mask &= tracker.transaction_db['Category'].isin(uncategorized_labels)
                            tracker.transaction_db.loc[mask, 'Category'] = 'SKIP'
                            tracker.save_transaction_db()
                            st.rerun()

                st.divider()

        # -------------------------------------------------------------- #
        #  Case-by-case (Zelle / Venmo)                                   #
        # -------------------------------------------------------------- #
        if not unk_individual.empty:
            st.subheader(f"Zelle / Venmo ({len(unk_individual)} transactions)")
            st.caption("These vary by person and amount — categorize each one individually.")

            for i, (df_idx, txn) in enumerate(unk_individual.sort_values('Date', ascending=False).iterrows()):
                amount = txn['Amount']
                desc = txn['Description']
                date = pd.to_datetime(txn['Date']).strftime('%m/%d/%Y')
                source = txn['Source']

                if amount < 0:
                    box_color = "rgba(255, 60, 60, 0.12)"
                    border_color = "rgba(255, 60, 60, 0.4)"
                    direction = "Sent"
                else:
                    box_color = "rgba(60, 200, 60, 0.12)"
                    border_color = "rgba(60, 200, 60, 0.4)"
                    direction = "Received"

                with st.container():
                    cols = st.columns([3, 2, 2, 0.5, 0.5])

                    with cols[0]:
                        st.markdown(
                            f'<div style="background:{box_color};border:1px solid {border_color};'
                            f'border-radius:8px;padding:8px 12px;margin-bottom:4px">'
                            f'<strong>{direction}</strong> &mdash; '
                            f'<strong>${abs(amount):,.2f}</strong><br>'
                            f'<code style="font-size:0.85em">{desc[:80]}</code><br>'
                            f'{date} &middot; {source}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                    with cols[1]:
                        basket = st.selectbox(
                            "Basket",
                            ['— pick —'] + basket_names,
                            key=f"ind_bsk_{i}",
                            label_visibility="collapsed",
                        )

                    with cols[2]:
                        if basket != '— pick —' and basket in tracker.baskets:
                            subs = tracker.baskets[basket]
                            sub = st.selectbox(
                                "Sub",
                                subs if subs else ['(none)'],
                                key=f"ind_sub_{i}",
                                label_visibility="collapsed",
                            )
                        else:
                            sub = st.selectbox(
                                "Sub",
                                ['— pick basket first —'],
                                key=f"ind_sub_{i}",
                                label_visibility="collapsed",
                                disabled=True,
                            )

                    with cols[3]:
                        if st.button("✓", key=f"ind_sort_{i}"):
                            if basket != '— pick —' and sub not in (
                                '(none)', '— pick basket first —'
                            ):
                                tracker.transaction_db.loc[df_idx, 'Category'] = sub
                                tracker.save_transaction_db()
                                st.success(f"Categorized → {basket} > {sub}")
                                st.rerun()
                            else:
                                st.error("Pick a basket and sub-category first")

                    with cols[4]:
                        if st.button("⏭", key=f"ind_skip_{i}", help="Skip — won't count in totals"):
                            tracker.transaction_db.loc[df_idx, 'Category'] = 'SKIP'
                            tracker.save_transaction_db()
                            st.rerun()

                st.divider()

        # Quick-add a new sub-category
        st.caption("Need a new sub-category?")
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            new_basket = st.selectbox(
                "Parent basket", basket_names, key="new_sub_basket"
            )
        with c2:
            new_sub = st.text_input(
                "New sub-category name", key="new_sub_name",
                placeholder="e.g. Coffee, Subscriptions"
            )
        with c3:
            st.write("")
            st.write("")
            if st.button("Add", key="add_new_sub"):
                if new_sub:
                    tracker.add_subcategory(new_basket, new_sub)
                    st.success(f"✓ Added '{new_sub}' under {new_basket}")
                    st.rerun()

    elif unk.empty:
        st.success("All transactions are categorized (or skipped)!")

    # ================================================================== #
    #  Skipped transactions — recategorize later                          #
    # ================================================================== #
    if not skipped.empty:
        st.divider()
        st.subheader(f"⏭ Skipped ({len(skipped)})")
        st.caption(
            "These are excluded from spending/income totals. "
            "Recategorize them anytime, or leave as-is."
        )

        for i, (df_idx, txn) in enumerate(skipped.sort_values('Date', ascending=False).iterrows()):
            amount = txn['Amount']
            desc = txn['Description']
            merchant = txn['Normalized_Merchant']
            date = pd.to_datetime(txn['Date']).strftime('%m/%d/%Y')
            source = txn['Source']

            box_color = "rgba(150, 150, 150, 0.12)"
            border_color = "rgba(150, 150, 150, 0.4)"

            with st.container():
                cols = st.columns([3, 2, 2, 0.5, 0.5])

                with cols[0]:
                    st.markdown(
                        f'<div style="background:{box_color};border:1px solid {border_color};'
                        f'border-radius:8px;padding:8px 12px;margin-bottom:4px">'
                        f'<strong>{merchant}</strong> &mdash; '
                        f'<strong>${abs(amount):,.2f}</strong><br>'
                        f'<code style="font-size:0.85em">{desc[:80]}</code><br>'
                        f'{date} &middot; {source}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                with cols[1]:
                    basket = st.selectbox(
                        "Basket",
                        ['— pick —'] + basket_names,
                        key=f"skp_bsk_{i}",
                        label_visibility="collapsed",
                    )

                with cols[2]:
                    if basket != '— pick —' and basket in tracker.baskets:
                        subs = tracker.baskets[basket]
                        sub = st.selectbox(
                            "Sub",
                            subs if subs else ['(none)'],
                            key=f"skp_sub_{i}",
                            label_visibility="collapsed",
                        )
                    else:
                        sub = st.selectbox(
                            "Sub",
                            ['— pick basket first —'],
                            key=f"skp_sub_{i}",
                            label_visibility="collapsed",
                            disabled=True,
                        )

                with cols[3]:
                    if st.button("✓", key=f"skp_sort_{i}"):
                        if basket != '— pick —' and sub not in (
                            '(none)', '— pick basket first —'
                        ):
                            tracker.transaction_db.loc[df_idx, 'Category'] = sub
                            tracker.save_transaction_db()
                            st.success(f"Recategorized → {basket} > {sub}")
                            st.rerun()
                        else:
                            st.error("Pick a basket and sub-category first")

                with cols[4]:
                    if st.button("↩", key=f"skp_undo_{i}", help="Move back to uncategorized"):
                        tracker.transaction_db.loc[df_idx, 'Category'] = 'UNCATEGORIZED'
                        tracker.save_transaction_db()
                        st.rerun()

            st.divider()
