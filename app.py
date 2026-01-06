"""
Midad Books - Enhanced Analytics with Beautiful UI
📚 كتب مداد
"""

import time
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from typing import Optional

from src.database import (
    add_sale,
    add_bundle_sale,
    delete_sale,
    get_books,
    get_sales,
    get_stats,
    init_db,
    save_books_bulk,
)

from src.calculations import calculate_sale_profit, calculate_profit_for_sale
from src.config import (
    LOW_STOCK_THRESHOLD,
    DEFAULT_PACKAGING_COST,
    MAX_SALES_HISTORY,
    LOW_MARGIN_THRESHOLD,
    HIGH_MARGIN_THRESHOLD,
    DISPLAY_DATE_FORMAT,
    PLATFORMS,
    GENRES,
    QUICK_MESSAGES,
)

from src.ui_components import (
    render_logo,
    render_title,
    render_stats_card,
    render_alerts,
    render_footer,
    render_page_header,
    render_info_banner,
    render_section_header,
    load_custom_css,
)

# Config
st.set_page_config(
    page_title="Midad Books - كتب مداد",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
load_custom_css()

# Init database
init_db()

# Session state
if "refresh_key" not in st.session_state:
    st.session_state.refresh_key = 0


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def show_success_toast(message: str):
    """Show success notification."""
    st.toast(f"✅ {message}", icon="✅")


def show_error_toast(message: str):
    """Show error notification."""
    st.toast(f"❌ {message}", icon="❌")


def get_low_stock_books(threshold: int = LOW_STOCK_THRESHOLD) -> list[dict]:
    """Get books with stock below threshold."""
    books = get_books("active")
    return [b for b in books if 0 < b["stock"] <= threshold]


def get_sales_by_date_range(days: int = 7) -> list[dict]:
    """Get sales from last N days."""
    sales = get_sales()
    cutoff = datetime.now() - timedelta(days=days)
    
    recent = []
    for s in sales:
        try:
            sale_date = datetime.strptime(s["date"], "%Y-%m-%d")
            if sale_date >= cutoff:
                recent.append(s)
        except:
            continue
    
    return recent


def group_sales_by_bundle(sales: list[dict]) -> list[dict]:
    """Group bundle sales together for better display."""
    grouped = []
    processed_bundles = set()
    all_books = get_books()
    
    for sale in sales:
        if sale['bundle_id'] and sale['bundle_id'] not in processed_bundles:
            # Find all sales in this bundle
            bundle_sales = [s for s in sales if s.get('bundle_id') == sale['bundle_id']]
            
            # Calculate bundle totals
            total_qty = sum(s['qty'] for s in bundle_sales)
            total_paid = sum(s['total'] for s in bundle_sales)
            bundle_profit = sum(calculate_profit_for_sale(s, all_books) for s in bundle_sales)
            
            # Create book list
            book_list = [f"{s['qty']}x {s['book_title']}" for s in bundle_sales]
            
            grouped.append({
                'id': f"B-{sale['bundle_id'][:6]}",
                'original_id': sale['id'],
                'date': sale['date'],
                'type': 'bundle',
                'book_title': f"📦 Bundle ({len(bundle_sales)} books)",
                'platform': sale['platform'],
                'qty': total_qty,
                'total': total_paid,
                'profit': bundle_profit,
                'customer': sale['customer'],
                'customer_username': sale['customer_username'],
                'bundle_details': book_list,
                'packaging_per_book': sale['packaging_per_book']
            })
            
            processed_bundles.add(sale['bundle_id'])
            
        elif not sale['bundle_id']:
            # Single sale
            profit = calculate_profit_for_sale(sale, all_books)
            
            grouped.append({
                'id': str(sale['id']),
                'original_id': sale['id'],
                'date': sale['date'],
                'type': 'single',
                'book_title': sale['book_title'],
                'platform': sale['platform'],
                'qty': sale['qty'],
                'total': sale['total'],
                'profit': profit,
                'customer': sale['customer'],
                'customer_username': sale['customer_username'],
                'bundle_details': None,
                'packaging_per_book': sale['packaging_per_book']
            })
    
    return grouped


# ============================================================================
# BEAUTIFUL SIDEBAR
# ============================================================================
with st.sidebar:
    # Logo
    render_logo()
    
    # Title
    render_title()
    
    # Navigation
    st.markdown("### 🧭 Navigation")
    page = st.radio(
        "Select Page",
        ["📚 Inventory", "💰 Sales", "📊 Analytics", "💬 Quick Messages"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Quick stats
    stats = get_stats()
    render_stats_card(stats)
    
    # Alerts
    low_stock = get_low_stock_books()
    recent_sales = get_sales_by_date_range(7)
    
    # Calculate week range
    today = datetime.now()
    week_start = today - timedelta(days=7)
    week_range = f"{week_start.strftime('%d/%m')} - {today.strftime('%d/%m/%Y')}"
    
    render_alerts(low_stock, recent_sales, week_range)
    
    # Footer
    render_footer()


# ============================================================================
# INVENTORY PAGE
# ============================================================================
if page == "📚 Inventory":
    render_page_header(
        "Inventory Management",
        "Manage your book collection - Track stock, prices, and sales history"
    )
    
    render_info_banner(
        "💡 Books with stock = 0 automatically move to 'Sold' tab",
        type="info"
    )
    
    # Only show Total Stock metric
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        st.metric("📦 Total Stock", stats["total_stock"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs([
        f"🟢 Active ({stats['active_count']})", 
        f"🔴 Sold ({stats['sold_count']})", 
        "📋 All"
    ])
    
    def render_inventory(status_filter: Optional[str], tab_key: str):
        """Render inventory table with edit capability."""
        
        books = get_books(status_filter)
        
        if books and status_filter == "active":
            books_without_targets = [b for b in books if b['target_price'] == 0]
            if books_without_targets:
                render_info_banner(
                    f"⚠️ {len(books_without_targets)} book(s) have no target price set",
                    type="warning"
                )

        if not books:
            st.info(f"No books found" + (f" with filter '{status_filter}'" if status_filter else ""))
            
            if status_filter == "active":
                st.info("💡 Add a new book by clicking '+ Add row' below")
            elif status_filter == "sold":
                st.caption("📦 Books appear here when stock reaches 0")
            
            df = pd.DataFrame(columns=[
                "id", "title", "author", "genre", "buy_price", 
                "target_price", "stock", "status", "notes"
            ])
        else:
            # Add stock alert icon
            for book in books:
                if book["stock"] > 0 and book["stock"] <= 2:
                    book["_stock_icon"] = "⚠️"
                elif book["stock"] > 2:
                    book["_stock_icon"] = "✅"
                else:
                    book["_stock_icon"] = "🔴"
            
            st.success(f"📊 Showing {len(books)} book(s)")
            df = pd.DataFrame(books)
        
        # Configure columns based on tab
        if status_filter == "active":
            column_config = {
                "id": None,
                "title": st.column_config.TextColumn("📖 Title", width="large", required=True),
                "author": st.column_config.TextColumn("✍️ Author", width="medium"),
                "genre": st.column_config.SelectboxColumn("📂 Genre", options=GENRES, width="small"),
                "buy_price": st.column_config.NumberColumn("💵 Buy €", format="%.2f", min_value=0, width="small"),
                "target_price": st.column_config.NumberColumn("🎯 Target €", format="%.2f", min_value=0, width="small"),
                "_stock_icon": st.column_config.TextColumn("", width="small"),
                "stock": st.column_config.NumberColumn("📦 Stock", min_value=0, step=1, width="small"),
                "status": None,
                "notes": st.column_config.TextColumn("📝 Notes", width="medium"),
                "created_at": None,
            }
            column_order = ["title", "author", "genre", "buy_price", "target_price", "_stock_icon", "stock", "notes"]
            
        elif status_filter == "sold":
            column_config = {
                "id": None,
                "title": st.column_config.TextColumn("📖 Title", width="large"),
                "author": st.column_config.TextColumn("✍️ Author", width="medium"),
                "genre": st.column_config.TextColumn("📂 Genre", width="small"),
                "buy_price": st.column_config.NumberColumn("💵 Buy €", format="%.2f", width="small"),
                "target_price": st.column_config.NumberColumn("🎯 Target €", format="%.2f", width="small"),
                "stock": None,
                "status": None,
                "notes": st.column_config.TextColumn("📝 Notes", width="medium"),
                "created_at": None,
                "_stock_icon": None,
            }
            column_order = ["title", "author", "genre", "buy_price", "target_price", "notes"]
            
        else:
            column_config = {
                "id": st.column_config.NumberColumn("🆔 ID", disabled=True, width="small"),
                "title": st.column_config.TextColumn("📖 Title", width="large", required=True),
                "author": st.column_config.TextColumn("✍️ Author", width="medium"),
                "genre": st.column_config.SelectboxColumn("📂 Genre", options=GENRES, width="small"),
                "buy_price": st.column_config.NumberColumn("💵 Buy €", format="%.2f", min_value=0, width="small"),
                "target_price": st.column_config.NumberColumn("🎯 Target €", format="%.2f", min_value=0, width="small"),
                "_stock_icon": st.column_config.TextColumn("", width="small"),
                "stock": st.column_config.NumberColumn("📦 Stock", min_value=0, step=1, width="small"),
                "status": st.column_config.TextColumn("📊 Status", width="small", disabled=True),
                "notes": st.column_config.TextColumn("📝 Notes", width="medium"),
                "created_at": None,
            }
            column_order = ["id", "title", "author", "genre", "buy_price", "target_price", "_stock_icon", "stock", "status", "notes"]
        
        # Data editor
        edited = st.data_editor(
            df,
            num_rows="dynamic",
            hide_index=True,
            key=f"editor_{tab_key}_{st.session_state.refresh_key}",
            column_config=column_config,
            column_order=column_order,
            width='stretch',
        )

        # Action buttons
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("💾 Save Changes", type="primary", key=f"save_{tab_key}", use_container_width=True):
                with st.spinner("Saving changes..."):
                    success, msg = save_books_bulk(edited.to_dict('records'), status_filter)
                    if success:
                        show_success_toast("Changes saved!")
                        st.success("✅ All changes saved")
                        st.session_state.refresh_key += 1
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        show_error_toast(msg)
                        st.error(f"❌ {msg}")
        
        with col2:
            if st.button("🔄 Refresh", key=f"refresh_{tab_key}", use_container_width=True):
                show_success_toast("Refreshed!")
                st.session_state.refresh_key += 1
                st.rerun()
        
        if books:
            st.caption("💡 Tip: Edit cells directly, add rows with '+', then click Save")

    with tab1:
        st.caption("📦 Books currently in stock")
        render_inventory("active", "active")
    
    with tab2:
        st.caption("🔴 Books sold out (stock = 0)")
        render_inventory("sold", "sold")
    
    with tab3:
        st.caption("📋 All books in inventory")
        render_inventory(None, "all")


# ============================================================================
# SALES PAGE
# ============================================================================
elif page == "💰 Sales":
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
        
        # SINGLE SALE TAB
        with sale_tab1:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                render_section_header("Sale Details", "📝")
                
                book_options = {f"{b['title']}": b for b in available_books}
                selected_title = st.selectbox(
                    "📖 Select Book", 
                    list(book_options.keys()),
                    key="book_selector"
                )
                selected_book = book_options[selected_title]
                
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
                
                # Date only (no time)
                sale_date = st.date_input("📅 Date", value=datetime.now(), key="sale_date")
                sale_datetime_str = sale_date.strftime('%Y-%m-%d')
                st.caption(f"📅 {sale_date.strftime('%d/%m/%Y')}")
                
                st.divider()
                
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
                
                # Total packaging
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
                
                if st.button("✅ Record Sale", type="primary", use_container_width=True, key="submit_sale"):
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
            
            with col2:
                render_section_header("Recent Sales", "📋")
                
                sales = get_sales()
                
                if sales:
                    date_filter = st.selectbox(
                        "📅 Show:",
                        ["All Time", "Last 7 Days", "Last 30 Days"],
                        key="date_filter_single"
                    )
                    
                    if date_filter == "Last 7 Days":
                        sales = get_sales_by_date_range(7)
                    elif date_filter == "Last 30 Days":
                        sales = get_sales_by_date_range(30)
                    
                    if not sales:
                        st.info(f"No sales for: {date_filter}")
                    else:
                        grouped_sales = group_sales_by_bundle(sales)
                        
                        sales_display = []
                        for s in grouped_sales[:MAX_SALES_HISTORY]:
                            profit_icon = "💚" if s['profit'] >= 0 else "💔"
                            
                            try:
                                date_obj = datetime.strptime(s["date"], "%Y-%m-%d")
                                date_display = date_obj.strftime(DISPLAY_DATE_FORMAT)
                            except:
                                date_display = s["date"]
                            
                            sales_display.append({
                                "ID": s["id"],
                                "📅 Date": date_display,
                                "📖 Book": s["book_title"][:30],
                                "Platform": s["platform"],
                                "Qty": s["qty"],
                                "💰 Total": f"€{s['total']:.2f}",
                                f"{profit_icon} Profit": f"€{s['profit']:.2f}",
                                "👤 Customer": s["customer"],
                            })
                        
                        st.dataframe(pd.DataFrame(sales_display), hide_index=True, width='stretch')
                        
                        for s in grouped_sales[:MAX_SALES_HISTORY]:
                            if s['type'] == 'bundle' and s['bundle_details']:
                                with st.expander(f"📦 Bundle {s['id']} Details"):
                                    for book in s['bundle_details']:
                                        st.caption(f"  • {book}")
                        
                        total_revenue = sum(s["total"] for s in grouped_sales)
                        total_items = sum(s["qty"] for s in grouped_sales)
                        total_profit = sum(s['profit'] for s in grouped_sales)
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("💰 Revenue", f"€{total_revenue:.2f}")
                        col2.metric("📦 Items", total_items)
                        col3.metric("💚 Profit", f"€{total_profit:.2f}")
                        
                        st.caption(f"Showing {len(sales_display)} sales")
                    
                    st.divider()
                    
                    with st.expander("🗑️ Undo Sale"):
                        st.warning("⚠️ This will delete the sale and restore stock")
                        
                        sale_id_input = st.text_input("Enter Sale ID or Bundle ID", 
                                                       placeholder="e.g., 4 or B-311b97",
                                                       key="delete_sale_id")
                        
                        if st.button("🗑️ Delete", type="secondary", key="delete_sale_btn"):
                            if sale_id_input:
                                if sale_id_input.startswith("B-"):
                                    bundle_hash = sale_id_input.split("B-")[1]
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
                                else:
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
                else:
                    st.info("🎉 No sales yet")
        
        # BUNDLE SALE TAB
        with sale_tab2:
            render_section_header("Create Bundle Sale", "🎁")
            st.caption("Sell multiple books in one transaction")
            
            selected_books = st.multiselect(
                "Select Books for Bundle (minimum 2)",
                options=[f"{b['id']}: {b['title']}" for b in available_books],
                key="bundle_books"
            )
            
            if len(selected_books) >= 2:
                book_ids = [int(s.split(":")[0]) for s in selected_books]
                selected_book_objs = [b for b in available_books if b['id'] in book_ids]
                
                st.divider()
                
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
                
                render_section_header("Customer", "👤")
                bundle_customer = st.text_input("Customer Name", key="bundle_customer")
                bundle_username = st.text_input("@️ Username", key="bundle_username")
                bundle_platform = st.selectbox("Platform", PLATFORMS, key="bundle_platform")
                
                bundle_date = st.date_input("Date", value=datetime.now(), key="bundle_date")
                bundle_datetime_str = bundle_date.strftime('%Y-%m-%d')
                
                st.divider()
                
                render_section_header("Bundle Preview", "📊")
                
                from src.calculations import calculate_bundle_profit
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
            
            elif len(selected_books) == 1:
                st.info("💡 Select at least one more book to create a bundle")
            else:
                st.info("💡 Select 2 or more books to create a bundle sale")


# ============================================================================
# ANALYTICS PAGE
# ============================================================================
elif page == "📊 Analytics":
    render_page_header(
        "Business Analytics",
        "Insights into your sales performance and inventory health"
    )
    
    # Force fresh data
    stats = get_stats()
    all_sales = get_sales()
    grouped_sales = group_sales_by_bundle(all_sales)
    
    # Calculate metrics
    total_revenue = sum(s["total"] for s in grouped_sales)
    total_items = sum(s["qty"] for s in grouped_sales)
    total_profit = sum(s['profit'] for s in grouped_sales)
    num_transactions = len(grouped_sales)
    
    # Count unique bundles vs single sales
    bundles_count = len([s for s in grouped_sales if s['type'] == 'bundle'])
    single_sales_count = len([s for s in grouped_sales if s['type'] == 'single'])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Beautiful gradient metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 25px; border-radius: 12px; text-align: center; color: white;
                        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);"
                        title="{total_items} books sold in {num_transactions} transactions">
                <h3 style="margin: 0; font-size: 32px;">💰</h3>
                <p style="margin: 8px 0; font-size: 13px; opacity: 0.95; font-weight: 600;">REVENUE</p>
                <h2 style="margin: 5px 0; font-size: 26px; font-weight: 700;">€{total_revenue:.2f}</h2>
                <p style="margin: 8px 0 0 0; font-size: 12px; opacity: 0.9;">📦 {total_items} books • {bundles_count} bundles</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        margin_pct = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
                        padding: 25px; border-radius: 12px; text-align: center; color: white;
                        box-shadow: 0 8px 16px rgba(67, 233, 123, 0.3);">
                <h3 style="margin: 0; font-size: 32px;">📈</h3>
                <p style="margin: 8px 0; font-size: 13px; opacity: 0.95; font-weight: 600;">PROFIT</p>
                <h2 style="margin: 5px 0; font-size: 26px; font-weight: 700;">€{total_profit:.2f}</h2>
                <p style="margin: 8px 0 0 0; font-size: 12px; opacity: 0.9;">Margin: {margin_pct:.1f}%</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        avg_books_per_order = total_items / num_transactions if num_transactions > 0 else 0
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                        padding: 25px; border-radius: 12px; text-align: center; color: white;
                        box-shadow: 0 8px 16px rgba(250, 112, 154, 0.3);">
                <h3 style="margin: 0; font-size: 32px;">📚</h3>
                <p style="margin: 8px 0; font-size: 13px; opacity: 0.95; font-weight: 600;">BOOKS SOLD</p>
                <h2 style="margin: 5px 0; font-size: 26px; font-weight: 700;">{total_items}</h2>
                <p style="margin: 8px 0 0 0; font-size: 12px; opacity: 0.9;">Avg: {avg_books_per_order:.1f} books/order</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        avg_order_value = total_revenue / num_transactions if num_transactions > 0 else 0
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                        padding: 25px; border-radius: 12px; text-align: center; color: white;
                        box-shadow: 0 8px 16px rgba(79, 172, 254, 0.3);">
                <h3 style="margin: 0; font-size: 32px;">🧾</h3>
                <p style="margin: 8px 0; font-size: 13px; opacity: 0.95; font-weight: 600;">AVG ORDER</p>
                <h2 style="margin: 5px 0; font-size: 26px; font-weight: 700;">€{avg_order_value:.2f}</h2>
                <p style="margin: 8px 0 0 0; font-size: 12px; opacity: 0.9;">Per transaction</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Inventory status
    render_section_header("Inventory Status", "📦")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📚 Active", stats['active_count'])
    with col2:
        st.metric("🔴 Sold Out", stats['sold_count'])
    with col3:
        st.metric("📦 Total Stock", stats['total_stock'])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        render_section_header("Sales by Platform", "🛒")
        if stats['platform_sales']:
            platform_df = pd.DataFrame([
                {"Platform": k, "Revenue (€)": v} 
                for k, v in sorted(stats['platform_sales'].items(), key=lambda x: x[1], reverse=True)
            ])
            st.bar_chart(platform_df.set_index("Platform"), height=300)
        else:
            st.info("No sales data")
    
    with col2:
        render_section_header("Sales Timeline", "📅")
        if all_sales:
            sales_by_date = {}
            for s in all_sales:
                date = s["date"]
                sales_by_date[date] = sales_by_date.get(date, 0) + s["total"]
            
            timeline_df = pd.DataFrame([
                {"Date": k, "Revenue (€)": v}
                for k, v in sorted(sales_by_date.items())
            ])
            st.line_chart(timeline_df.set_index("Date"), height=300)
        else:
            st.info("No sales data")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Insights
    col1, col2 = st.columns(2)
    
    with col1:
        render_section_header("Best Sellers", "🏆")
        if all_sales:
            book_sales = {}
            for s in all_sales:
                title = s["book_title"]
                book_sales[title] = book_sales.get(title, 0) + s["qty"]
            
            top_sellers = sorted(book_sales.items(), key=lambda x: x[1], reverse=True)[:5]
            
            for i, (title, qty) in enumerate(top_sellers, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📖"
                st.write(f"{medal} **{title[:30]}** - {qty} sold")
        else:
            st.info("No sales to analyze")
    
    with col2:
        render_section_header("Alerts", "⚠️")
        
        alerts_count = 0
        
        low_stock = get_low_stock_books()
        if low_stock:
            alerts_count += 1
            st.warning(f"📉 **{len(low_stock)} books** low stock")
            for book in low_stock[:3]:
                st.caption(f"  • {book['title'][:25]} - {book['stock']} left")
        
        if stats['low_margin_books']:
            alerts_count += 1
            st.error(f"💔 **{len(stats['low_margin_books'])} books** below cost")
            for b in stats['low_margin_books'][:3]:
                loss = b['buy'] - b['target']
                st.caption(f"  • {b['title'][:25]} - Loss: €{loss:.2f}")
        
        if alerts_count == 0:
            st.success("✅ All systems healthy!")


# ============================================================================
# QUICK MESSAGES PAGE
# ============================================================================
elif page == "💬 Quick Messages":
    render_page_header(
        "Quick Messages",
        "Copy-paste templates for customer communication"
    )
    
    render_info_banner(
        "💡 Click 'Copy' to copy any message template to your clipboard. Edit placeholders like [NAME], [AMOUNT], etc.",
        type="info"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Display all message templates
    for key, template in QUICK_MESSAGES.items():
        with st.expander(f"{template['title']}", expanded=False):
            st.text_area(
                "Message Template",
                value=template['message'],
                height=200,
                key=f"msg_{key}",
                label_visibility="collapsed"
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("📋 Copy", key=f"copy_{key}", use_container_width=True):
                    st.code(template['message'], language=None)
                    show_success_toast("Copied to display!")
                    st.info("👆 Select text above and copy (Ctrl+C / Cmd+C)")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Custom message creator
    render_section_header("Create Custom Message", "✍️")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        custom_title = st.text_input("Message Title", placeholder="e.g., Discount Offer")
    
    with col2:
        custom_category = st.selectbox("Category", ["General", "Promotion", "Follow-up", "Support"])
    
    custom_message = st.text_area(
        "Your Message",
        placeholder="Type your custom message here...\n\nTip: Use placeholders like [NAME], [BOOK], [PRICE]",
        height=150,
        key="custom_msg"
    )
    
    if st.button("💾 Save Custom Message", type="primary"):
        if custom_title and custom_message:
            st.success(f"✅ Message '{custom_title}' saved! (Note: Custom messages are session-only in this version)")
            st.code(custom_message, language=None)
        else:
            st.error("❌ Please enter both title and message")