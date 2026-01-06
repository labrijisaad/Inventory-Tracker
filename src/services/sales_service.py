"""
Sales Service
Business logic for sales recording
"""

import time
from datetime import datetime
import pandas as pd
import streamlit as st

from src.data.database import get_books, get_sales, add_sale, add_bundle_sale, delete_sale
from src.core.calculations import calculate_sale_profit, calculate_bundle_profit
from src.ui.components import (
    render_page_header, render_info_banner, render_section_header
)
from src.config import (
    DEFAULT_PACKAGING_COST, PLATFORMS, MAX_SALES_HISTORY, 
    DISPLAY_DATE_FORMAT, LOW_MARGIN_THRESHOLD, HIGH_MARGIN_THRESHOLD
)
from src.utils.helpers import (
    show_success_toast, show_error_toast, 
    get_sales_by_date_range, group_sales_by_bundle
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
    
    book_options = {f"{b['title']}": b for b in available_books}
    selected_title = st.selectbox(
        "📖 Select Book", 
        list(book_options.keys()),
        key="book_selector"
    )
    selected_book = book_options[selected_title]
    
    # Stock status
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
        step=0.50,
        key="total_paid"
    )
    
    total_packaging = st.number_input(
        "📦 Packaging Total (€)", 
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
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("💰 Total", f"€{total_paid:.2f}")
        st.caption(f"📖 Per book: €{calc['price_per_book']:.2f}")
        st.caption(f"📦 Packaging: €{calc['total_packaging']:.2f}")
    with col_b:
        st.metric("💵 Revenue", f"€{calc['revenue']:.2f}")
        st.caption(f"💸 Cost: €{calc['cost']:.2f}")
    
    if calc['profit'] >= 0:
        st.success(f"### 💚 Profit: €{calc['profit']:.2f}")
        st.caption(f"📊 Margin: {calc['margin_percent']:.1f}%")
        
        if calc['margin_percent'] > HIGH_MARGIN_THRESHOLD:
            st.info("🎉 Great deal!")
        elif calc['margin_percent'] < LOW_MARGIN_THRESHOLD:
            st.warning("⚠️ Low margin")
    else:
        st.error(f"### 💔 Loss: €{abs(calc['profit']):.2f}")
        st.warning("⚠️ Selling below cost!")
    
    st.divider()
    
    # Submit button
    if st.button("✅ Record Sale", type="primary", width='stretch', key="submit_sale"):
        if not customer_name.strip() or not customer_username.strip():
            show_error_toast("Customer info required")
            st.error("❌ Please enter customer name and username")
        else:
            with st.spinner("Recording sale..."):
                success, msg = add_sale(
                    selected_book["id"], qty, total_paid, 
                    packaging_per_book, customer_name, customer_username,
                    platform, sale_datetime_str
                )
                
                if success:
                    show_success_toast(f"Sale recorded! Profit: €{calc['profit']:.2f}")
                    st.success(f"✅ {msg}")
                    st.balloons()
                    
                    if selected_book["stock"] - qty == 0:
                        st.info(f"📦 '{selected_book['title']}' moved to Sold tab!")
                    
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
    
    # ✅ Filter by date range
    if date_filter == "Last 7 Days":
        sales = get_sales_by_date_range(7)
    elif date_filter == "Last 30 Days":
        sales = get_sales_by_date_range(30)
    
    if not sales:
        st.info(f"No sales for: {date_filter}")
        return
    
    grouped_sales = group_sales_by_bundle(sales)
    
    # Display sales table
    sales_display = []
    for s in grouped_sales[:MAX_SALES_HISTORY]:
        profit_icon = "💚" if s['profit'] >= 0 else "💔"
        
        # ✅ Parse and display date consistently
        try:
            date_str = s["date"]
            
            if '/' in date_str:
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            elif ' ' in date_str:
                date_obj = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
            else:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            
            date_display = date_obj.strftime("%d/%m/%Y")
        except Exception as e:
            print(f"⚠️ Date display error: {date_str} - {e}")
            date_display = date_str
        
        # ✅ FIXED: Keep ID as string to avoid Arrow error
        sales_display.append({
            "ID": str(s["id"]),  # ✅ Convert to string
            "📅 Date": date_display,
            "📖 Book": s.get("book_title", "Bundle")[:30] if s['type'] == 'single' else "📦 Bundle",
            "Platform": s["platform"],
            "Qty": s["qty"],
            "💰 Total": f"€{s['total']:.2f}",
            f"{profit_icon} Profit": f"€{s['profit']:.2f}",
            "👤 Customer": s["customer"],
        })
    
    st.dataframe(pd.DataFrame(sales_display), hide_index=True, use_container_width=True)
    
    # Bundle details
    for s in grouped_sales[:MAX_SALES_HISTORY]:
        if s['type'] == 'bundle' and s['bundle_details']:
            with st.expander(f"📦 Bundle {s['id']} Details"):
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
        
        sale_id_input = st.text_input("Enter Sale ID or Bundle ID", 
                                       placeholder="e.g., 4 or B-311b97",
                                       key="delete_sale_id")
        
        if st.button("🗑️ Delete", type="secondary", key="delete_sale_btn"):
            if not sale_id_input:
                st.error("❌ Please enter a sale ID")
                return
            
            if sale_id_input.startswith("B-"):
                _delete_bundle(sale_id_input)
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


def _render_bundle_sale_tab(available_books: list[dict]):
    """Render bundle sale tab."""
    render_section_header("Create Bundle Sale", "🎁")
    st.caption("Sell multiple books in one transaction")
    
    selected_books = st.multiselect(
        "Select Books for Bundle (minimum 2)",
        options=[f"{b['id']}: {b['title']}" for b in available_books],
        key="bundle_books"
    )
    
    if len(selected_books) < 2:
        if len(selected_books) == 1:
            st.info("💡 Select at least one more book to create a bundle")
        else:
            st.info("💡 Select 2 or more books to create a bundle sale")
        return
    
    book_ids = [int(s.split(":")[0]) for s in selected_books]
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
        "Packaging Total (€)",
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
    
    # Preview
    render_section_header("Bundle Preview", "📊")
    
    buy_prices = [b['buy_price'] for b in selected_book_objs]
    bundle_calc = calculate_bundle_profit(quantities, buy_prices, bundle_total, bundle_packaging)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📚 Total Books", bundle_calc['total_books'])
    col2.metric("💰 Per Book", f"€{bundle_calc['price_per_book']:.2f}")
    col3.metric("📦 Packaging", f"€{bundle_calc['total_packaging']:.2f}")
    
    col1, col2 = st.columns(2)
    col1.metric("💵 Revenue", f"€{bundle_calc['revenue']:.2f}")
    col2.metric("💸 Cost", f"€{bundle_calc['cost']:.2f}")
    
    if bundle_calc['profit'] >= 0:
        st.success(f"### 💚 Bundle Profit: €{bundle_calc['profit']:.2f}")
        st.caption(f"📊 Margin: {bundle_calc['margin_percent']:.1f}%")
    else:
        st.error(f"### 💔 Bundle Loss: €{abs(bundle_calc['profit']):.2f}")
    
    st.divider()
    
    # Submit
    if st.button("✅ Record Bundle Sale", type="primary", width='stretch', key="submit_bundle"):
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