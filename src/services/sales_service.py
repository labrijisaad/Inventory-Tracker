"""
Sales Service
Business logic for sales recording
"""

import time
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from src.config import (
    DEFAULT_PACKAGING_COST,
    HIGH_MARGIN_THRESHOLD,
    LOW_MARGIN_THRESHOLD,
    MAX_SALES_HISTORY,
    PLATFORMS,
)
from src.core.calculations import calculate_bundle_profit, calculate_sale_profit
from src.data.database import add_bundle_sale, add_sale, delete_sale, get_books, get_sales
from src.ui.components import render_info_banner, render_page_header, render_section_header
from src.utils.helpers import (
    get_sales_by_date_range,
    group_sales_by_bundle,
    show_error_toast,
    show_success_toast,
)


def render_sales_page():
    """Main sales page."""
    render_page_header(
        "Record New Sale",
        "Track single sales or create bundle transactions"
    )

    active_books = get_books("active")
    available_books = [b for b in active_books if b["stock"] > 0]

    if not available_books:
        render_info_banner(
            "⚠️ No books available for sale! Go to Inventory tab to add books.",
            type="warning"
        )
    else:
        sale_tab1, sale_tab2 = st.tabs(["📖 Single Sale", "🎁 Bundle Sale"])

        with sale_tab1:
            _render_single_sale_tab(available_books)

        with sale_tab2:
            _render_bundle_sale_tab(available_books)


def _render_single_sale_tab(available_books: list[dict]):
    """Render single sale tab."""
    col1, col2 = st.columns([1, 2])

    with col1:
        _render_sale_form(available_books)

    with col2:
        _render_sales_history()


def _render_sale_form(available_books: list[dict]):
    """Render sale input form."""
    render_section_header("Sale Details", "📝")

    # ✅ IMPROVED: Add stock status to dropdown
    book_options = {}
    for b in available_books:
        stock_icon = "🟢" if b['stock'] > 3 else "🟡" if b['stock'] > 1 else "🔴"
        display = f"{stock_icon} {b['id'][5:]} - {b['title']} ({b['stock']} left)"
        book_options[display] = b

    selected_display = st.selectbox(
        "📖 Select Book",
        list(book_options.keys()),
        key="book_selector"
    )
    selected_book = book_options[selected_display]

    # ✅ NEW: Warning if no buy price set
    if selected_book['buy_price'] == 0:
        st.warning(
            "⚠️ **Warning**: This book has no buy price set!\n\n"
            "Profit calculation will be inaccurate. Please update in Inventory tab."
        )

    # Stock status details
    if selected_book['stock'] > 3:
        stock_color, stock_msg = "🟢", "Good stock"
    elif selected_book['stock'] > 1:
        stock_color, stock_msg = "🟡", "Low stock"
    else:
        stock_color, stock_msg = "🔴", "Last one!"

    st.info(
        f"{stock_color} **Stock: {selected_book['stock']}** ({stock_msg})\n\n"
        f"💵 You paid: €{selected_book['buy_price']:.2f}\n\n"
        f"🎯 Target: €{selected_book['target_price']:.2f}" if selected_book['target_price'] > 0 else "🎯 No target"
    )
    st.divider()

    # Date
    sale_date = st.date_input("📅 Date", value=datetime.now(), key="sale_date")
    sale_datetime_str = sale_date.strftime('%Y-%m-%d')
    st.caption(f"📅 {sale_date.strftime('%d/%m/%Y')}")

    st.divider()

    # Sale details
    platform = st.selectbox("🛒 Platform", PLATFORMS, key="platform")

    qty = st.number_input(
        "📦 Quantity",
        min_value=1,
        max_value=selected_book["stock"],
        value=1,
        key="qty"
    )

    suggested_total = qty * (selected_book["target_price"] if selected_book["target_price"] > 0 else selected_book["buy_price"] * 1.5)
    total_paid = st.number_input(
        "💰 Total Paid (€)",
        min_value=0.0,
        value=float(suggested_total),
        step=0.25,
        key="total_paid"
    )

    total_packaging = st.number_input(
        "📦 Packaging Total for order (€)",
        min_value=0.0,
        value=DEFAULT_PACKAGING_COST * qty,
        step=0.10,
        key="packaging_total"
    )

    packaging_per_book = total_packaging / qty if qty > 0 else 0

    customer_name = st.text_input("👤 Customer Name", placeholder="e.g., Ahmed M.", key="customer_name")
    customer_username = st.text_input("@️ Username", placeholder="e.g., ahmed_m", key="customer_username")

    # Calculate profit
    calc = calculate_sale_profit(qty, total_paid, packaging_per_book, selected_book["buy_price"])

    st.divider()
    render_section_header("Live Summary", "📊")

    # ✅ ALTERNATIVE: Pure Streamlit (No HTML)
    if calc['profit'] >= 0:
        with st.container():
            st.success("💚 **PROFITABLE SALE**")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**CUSTOMER PAYS**")
                st.markdown(f"### €{total_paid:.2f}")
                st.caption(f"€{calc['price_per_book']:.2f} per book × {qty}")

            with col2:
                st.markdown("**YOUR EXPENSES**")
                st.markdown(f"### €{calc['cost'] + calc['total_packaging']:.2f}")
                st.caption(f"Book €{calc['cost']:.2f} + Pkg €{calc['total_packaging']:.2f}")

            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**NET PROFIT**")
                st.markdown(f"## €{calc['profit']:.2f}")

            with col2:
                st.markdown("**MARGIN**")
                st.markdown(f"## {calc['margin_percent']:.1f}%")

            if calc['margin_percent'] > HIGH_MARGIN_THRESHOLD:
                st.success("🎉 Excellent margin!")
            elif 0 <= calc['margin_percent'] < LOW_MARGIN_THRESHOLD:
                st.warning("⚠️ Consider raising price")
    else:
        st.error("💔 **SELLING AT A LOSS**")
        st.markdown(f"## €{calc['profit']:.2f}")
        st.warning(f"⚠️ Total expenses (€{calc['cost'] + calc['total_packaging']:.2f}) exceed customer payment (€{total_paid:.2f})")

    st.divider()

    # ✅ NEW: Pre-validation checks
    validation_issues = []

    if not customer_name.strip():
        validation_issues.append("Customer name is required")
    if not customer_username.strip():
        validation_issues.append("Username is required")
    if total_paid <= 0:
        validation_issues.append("Total paid must be greater than 0")
    if qty > selected_book["stock"]:
        validation_issues.append(f"Only {selected_book['stock']} in stock")

    if validation_issues:
        for issue in validation_issues:
            st.error(f"❌ {issue}")

    # Submit button
    submit_disabled = len(validation_issues) > 0
    if st.button("✅ Record Sale", type="primary", use_container_width=True,
                 key="submit_sale", disabled=submit_disabled):
        with st.spinner("Recording sale..."):
            success, msg = add_sale(
                selected_book["id"], qty, total_paid,
                packaging_per_book, customer_name, customer_username,
                platform, sale_datetime_str
            )

            if success:
                # ✅ IMPROVED: More informative success message
                margin_emoji = "🎉" if calc['margin_percent'] > HIGH_MARGIN_THRESHOLD else "💚"
                show_success_toast(f"{margin_emoji} Profit: €{calc['profit']:.2f} ({calc['margin_percent']:.1f}%)")

                st.success(f"✅ {msg}")

                # Show what happened to the book
                new_stock = selected_book["stock"] - qty
                if new_stock == 0:
                    st.info(f"📦 '{selected_book['title']}' is now sold out and moved to 'Sold' inventory")
                elif new_stock <= 2:
                    st.warning(f"⚠️ Only {new_stock} copy/copies of '{selected_book['title']}' remaining!")

                st.balloons()
                st.session_state.refresh_key += 1
                time.sleep(1.5)
                st.rerun()
            else:
                show_error_toast(msg)
                st.error(f"❌ {msg}")


def _render_sales_history():
    """Render recent sales history."""
    render_section_header("Recent Sales", "📋")

    sales = get_sales()

    if not sales:
        st.info("🎉 No sales yet")
        return

    date_filter = st.selectbox(
        "📅 Show:",
        ["All Time", "Last 7 Days", "Last 30 Days"],
        key="date_filter_single"
    )

    # ✅ IMPROVED: Add period info and better formatting
    st.markdown(f"**Period:** {date_filter}")

    # Filter by date range
    if date_filter == "Last 7 Days":
        sales = get_sales_by_date_range(7)
        today = datetime.now()
        start = (today - timedelta(days=7)).strftime("%d/%m/%Y")
        st.caption(f"📅 {start} → {today.strftime('%d/%m/%Y')}")
    elif date_filter == "Last 30 Days":
        sales = get_sales_by_date_range(30)
        today = datetime.now()
        start = (today - timedelta(days=30)).strftime("%d/%m/%Y")
        st.caption(f"📅 {start} → {today.strftime('%d/%m/%Y')}")

    if not sales:
        st.info(f"📭 No sales for: {date_filter}")
        return

    grouped_sales = group_sales_by_bundle(sales)

    # ✅ IMPROVED: Better column widths and formatting
    sales_display = []
    for s in grouped_sales[:MAX_SALES_HISTORY]:
        profit_icon = "💚" if s['profit'] >= 0 else "💔"

        # Parse date
        try:
            date_str = s["date"]
            if '/' in date_str:
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            elif ' ' in date_str:
                date_obj = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
            else:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            date_display = date_obj.strftime("%d/%m/%Y")
        except Exception:
            date_display = date_str

        # Format sale ID
        if s['type'] == 'bundle':
            sale_id = s['id']
            book_display = f"📦 {s['qty']} books"
        else:
            sale_id = f"SE{s['id']:03d}"
            book_display = s.get("book_title", "Unknown")[:25]

        # Calculate margin for display
        margin = (s['profit'] / s['total'] * 100) if s['total'] > 0 else 0

        sales_display.append({
            "ID": sale_id,
            "Date": date_display,
            "Book/Bundle": book_display,
            "Platform": s["platform"],
            "Qty": s["qty"],
            "Total": f"€{s['total']:.2f}",
            "Profit": f"{profit_icon} €{s['profit']:.2f}",
            "Margin": f"{margin:.0f}%",
            "Customer": s["customer"][:20],
        })

    # Display dataframe
    df = pd.DataFrame(sales_display)

    st.dataframe(
        df,
        column_config={
            "ID": st.column_config.TextColumn("ID", width="small"),
            "Date": st.column_config.TextColumn("Date", width="small"),
            "Book/Bundle": st.column_config.TextColumn("Book/Bundle", width="medium"),
            "Platform": st.column_config.TextColumn("Platform", width="small"),
            "Qty": st.column_config.NumberColumn("Qty", width="small"),
            "Total": st.column_config.TextColumn("Total", width="small"),
            "Profit": st.column_config.TextColumn("Profit", width="small"),
            "Margin": st.column_config.TextColumn("Margin %", width="small"),
            "Customer": st.column_config.TextColumn("Customer", width="medium"),
        },
        hide_index=True,
        use_container_width=True
    )

    # Bundle details
    for s in grouped_sales[:MAX_SALES_HISTORY]:
        if s['type'] == 'bundle' and s['bundle_details']:
            with st.expander(f"📦 Bundle `{s['id']}` Details"):
                for book in s['bundle_details']:
                    st.caption(f"  • {book}")

    # Summary metrics
    total_revenue = sum(s["total"] for s in grouped_sales)
    total_items = sum(s["qty"] for s in grouped_sales)
    total_profit = sum(s['profit'] for s in grouped_sales)

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Revenue", f"€{total_revenue:.2f}")
    col2.metric("📦 Items", total_items)
    col3.metric("💚 Profit", f"€{total_profit:.2f}")

    st.caption(f"Showing {len(sales_display)} sales")

    st.divider()

    # Delete sale section
    _render_delete_sale_section()


def _render_delete_sale_section():
    """Render delete sale interface."""
    with st.expander("🗑️ Undo Sale"):
        st.warning("⚠️ This will delete the sale and restore stock")

        sale_id_input = st.text_input(
            "Enter Sale ID or Bundle ID",
            placeholder="e.g., SE001 or B-311b97",
            key="delete_sale_id"
        )

        if st.button("🗑️ Delete", type="secondary", key="delete_sale_btn"):
            if not sale_id_input:
                st.error("❌ Please enter a sale ID")
                return

            if sale_id_input.startswith("B-"):
                _delete_bundle(sale_id_input)
            elif sale_id_input.startswith("SE"):
                _delete_single_sale_with_prefix(sale_id_input)
            else:
                _delete_single_sale(sale_id_input)


def _delete_bundle(bundle_id_input: str):
    """Delete a bundle sale."""
    bundle_hash = bundle_id_input.split("B-")[1]
    all_sales = get_sales()
    matching_sale = None
    for s in all_sales:
        if s.get('bundle_id') and s['bundle_id'].startswith(bundle_hash):
            matching_sale = s
            break

    if matching_sale:
        with st.spinner("Deleting bundle..."):
            success, msg = delete_sale(matching_sale['id'])
            if success:
                show_success_toast("Bundle deleted")
                st.success(msg)
                st.session_state.refresh_key += 1
                time.sleep(1)
                st.rerun()
            else:
                show_error_toast(msg)
                st.error(msg)
    else:
        st.error("❌ Bundle ID not found")


def _delete_single_sale(sale_id_input: str):
    """Delete a single sale."""
    try:
        sale_id = int(sale_id_input)
        with st.spinner("Deleting..."):
            success, msg = delete_sale(sale_id)
            if success:
                show_success_toast("Sale deleted")
                st.success(msg)
                st.session_state.refresh_key += 1
                time.sleep(1)
                st.rerun()
            else:
                show_error_toast(msg)
                st.error(msg)
    except ValueError:
        st.error("❌ Invalid ID format")


def _delete_single_sale_with_prefix(sale_id_input: str):
    """Delete a single sale using SE prefix format."""
    try:
        # Extract numeric part from SE001 → 1
        numeric_id = int(sale_id_input.replace("SE", "").lstrip("0") or "0")
        with st.spinner("Deleting..."):
            success, msg = delete_sale(numeric_id)
            if success:
                show_success_toast("Sale deleted")
                st.success(msg)
                st.session_state.refresh_key += 1
                time.sleep(1)
                st.rerun()
            else:
                show_error_toast(msg)
                st.error(msg)
    except ValueError:
        st.error("❌ Invalid sale ID format. Use SE001, SE002, etc.")


def _render_bundle_sale_tab(available_books: list[dict]):
    """Render bundle sale tab."""
    render_section_header("Create Bundle Sale", "🎁")
    st.caption("Sell multiple books in one transaction")

    # ✅ IMPROVED: Cleaner bundle book display
    book_display_options = []
    for b in available_books:
        stock_icon = "🟢" if b['stock'] > 3 else "🟡" if b['stock'] > 1 else "🔴"
        display = f"{stock_icon} {b['id'][5:]} - {b['title'][:35]} (Stock: {b['stock']})"
        book_display_options.append((display, b['id']))

    selected_books = st.multiselect(
        "Select Books for Bundle (minimum 2)",
        options=[disp for disp, _ in book_display_options],
        key="bundle_books",
        help="💡 Tip: Bundles often sell better than individual books"
    )

    if len(selected_books) < 2:
        if len(selected_books) == 1:
            st.info("💡 Select at least one more book to create a bundle")
        else:
            st.info("💡 Select 2 or more books to create a bundle sale")
        return

    # ✅ Extract book IDs from selections
    book_id_map = {disp: book_id for disp, book_id in book_display_options}
    book_ids = [book_id_map[sel] for sel in selected_books]
    selected_book_objs = [b for b in available_books if b['id'] in book_ids]

    st.divider()

    # Quantities
    render_section_header("Quantities", "📦")
    quantities = []
    for book in selected_book_objs:
        qty = st.number_input(
            f"{book['title'][:40]} (Stock: {book['stock']})",
            min_value=1,
            max_value=book['stock'],
            value=1,
            key=f"bundle_qty_{book['id']}"
        )
        quantities.append(qty)

    st.divider()

    # Pricing
    total_books = sum(quantities)
    suggested_bundle_total = sum(
        book['target_price'] * qty if book['target_price'] > 0 else book['buy_price'] * 1.5 * qty
        for book, qty in zip(selected_book_objs, quantities)
    )

    render_section_header("Pricing", "💰")
    bundle_total = st.number_input(
        f"Total Bundle Price (€) - {total_books} books",
        min_value=0.0,
        value=float(suggested_bundle_total),
        step=0.50,
        key="bundle_total"
    )

    bundle_packaging_total = st.number_input(
        "Packaging Total for order (€)",
        min_value=0.0,
        value=DEFAULT_PACKAGING_COST * total_books,
        step=0.10,
        key="bundle_packaging_total"
    )

    bundle_packaging = bundle_packaging_total / total_books if total_books > 0 else 0

    st.divider()

    # Customer
    render_section_header("Customer", "👤")
    bundle_customer = st.text_input("Customer Name", key="bundle_customer")
    bundle_username = st.text_input("@️ Username", key="bundle_username")
    bundle_platform = st.selectbox("Platform", PLATFORMS, key="bundle_platform")

    bundle_date = st.date_input("Date", value=datetime.now(), key="bundle_date")
    bundle_datetime_str = bundle_date.strftime('%Y-%m-%d')

    st.divider()

    # ✅ IMPROVED: Better bundle preview with book list
    render_section_header("Bundle Preview", "📊")

    # Show books in bundle
    st.markdown("**📚 Books in This Bundle:**")
    for book, qty in zip(selected_book_objs, quantities):
        st.markdown(
            f"- **{qty}x** {book['title'][:40]} (€{book['buy_price']:.2f} cost each)"
        )

    st.divider()

    buy_prices = [b['buy_price'] for b in selected_book_objs]
    bundle_calc = calculate_bundle_profit(quantities, buy_prices, bundle_total, bundle_packaging)

    # Display calculation
    col1, col2, col3 = st.columns(3)
    col1.metric("📚 Total Books", bundle_calc['total_books'])
    col2.metric("💰 Per Book", f"€{bundle_calc['price_per_book']:.2f}")
    col3.metric("📦 Total Packaging", f"€{bundle_calc['total_packaging']:.2f}")

    st.markdown("---")

    if bundle_calc['profit'] >= 0:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, rgba(67, 233, 123, 0.15) 0%, rgba(56, 249, 215, 0.15) 100%);
                        padding: 16px; border-radius: 12px; border-left: 4px solid #43e97b; text-align: center;">
                <div style="color: #43e97b; font-size: 14px; font-weight: 700; margin-bottom: 8px;">
                    💚 BUNDLE PROFIT
                </div>
                <div style="color: #e5e7eb; font-size: 32px; font-weight: 900;">
                    €{bundle_calc['profit']:.2f}
                </div>
                <div style="color: #9ca3af; font-size: 12px; margin-top: 8px;">
                    Margin: {bundle_calc['margin_percent']:.1f}% • Revenue: €{bundle_calc['revenue']:.2f}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, rgba(255, 107, 107, 0.15) 0%, rgba(238, 90, 111, 0.15) 100%);
                        padding: 16px; border-radius: 12px; border-left: 4px solid #ff6b6b; text-align: center;">
                <div style="color: #ff6b6b; font-size: 14px; font-weight: 700; margin-bottom: 8px;">
                    💔 BUNDLE LOSS
                </div>
                <div style="color: #e5e7eb; font-size: 32px; font-weight: 900;">
                    €{bundle_calc['profit']:.2f}
                </div>
                <div style="color: #9ca3af; font-size: 12px; margin-top: 8px;">
                    ⚠️ Consider adjusting bundle price
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    # Submit
    if st.button("✅ Record Bundle Sale", type="primary", use_container_width=True, key="submit_bundle"):
        if not bundle_customer.strip() or not bundle_username.strip():
            show_error_toast("Customer info required")
            st.error("❌ Please enter customer name and username")
        else:
            with st.spinner("Recording bundle sale..."):
                success, msg = add_bundle_sale(
                    book_ids, quantities, bundle_total, bundle_packaging,
                    bundle_customer, bundle_username, bundle_platform,
                    bundle_datetime_str
                )

                if success:
                    show_success_toast(f"Bundle recorded! Profit: €{bundle_calc['profit']:.2f}")
                    st.success(f"✅ {msg}")
                    st.balloons()
                    st.session_state.refresh_key += 1
                    time.sleep(1.5)
                    st.rerun()
                else:
                    show_error_toast(msg)
                    st.error(f"❌ {msg}")
