"""
Inventory Service
Business logic for inventory management
"""

import time
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from src.config import GENRES
from src.data.database import (
    get_book_performance_stats,
    get_books,
    get_sales_history_grouped,
    get_stats,
    save_books_bulk,
)
from src.ui.components import render_info_banner, render_page_header
from src.utils.helpers import show_error_toast, show_success_toast


def render_inventory_page():
    """Main inventory page."""
    stats = get_stats()

    render_page_header(
        "Inventory Management",
        "Manage inventory, track sales history, and analyze book performance"
    )

    render_info_banner(
        "💡 Books with stock = 0 automatically stop appearing in Active tab",
        type="info"
    )

    # Tabs
    tab1, tab2, tab3 = st.tabs([
        f"📦 Active Inventory ({stats['active_count']})",
        "💰 Sales History",
        "📊 Book Performance"
    ])

    with tab1:
        st.caption("📦 Books currently in stock - Add and manage your inventory")
        _render_active_inventory_table()

    with tab2:
        st.caption("💰 Complete sales transaction history")
        _render_sales_history_table()

    with tab3:
        st.caption("📊 Lifetime statistics for all books")
        _render_book_performance_table()


# ============================================================================
# TAB 1: ACTIVE INVENTORY (EDITABLE)
# ============================================================================
def _render_active_inventory_table():
    """Render active inventory with edit capability."""

    books = get_books("active")

    if books:
        books_without_targets = [b for b in books if b['target_price'] == 0]
        if books_without_targets:
            render_info_banner(
                f"⚠️ {len(books_without_targets)} book(s) have no target price set",
                type="warning"
            )

    if not books:
        st.info("📭 No active books in stock")
        st.info("💡 Add a new book by clicking '+ Add row' below")
        df = pd.DataFrame(columns=[
            "id", "title", "author", "genre", "buy_price",
            "target_price", "stock", "notes"
        ])
    else:
        st.success(f"📊 {len(books)} active book(s)")
        df = pd.DataFrame(books)

    # Column configuration
    column_config = {
        "id": st.column_config.TextColumn("🆔 ID", width="small", disabled=True),
        "title": st.column_config.TextColumn("📖 Title", width="large", required=True),
        "author": st.column_config.TextColumn("✍️ Author", width="medium"),
        "genre": st.column_config.SelectboxColumn("Genre", options=GENRES, width="small"),
        "buy_price": st.column_config.NumberColumn("Buy €", format="%.2f", min_value=0, width="small"),
        "target_price": st.column_config.NumberColumn("Target €", format="%.2f", min_value=0, width="small"),
        "stock": st.column_config.NumberColumn("📦 Stock", min_value=0, step=1, width="small"),
        "status": None,
        "notes": st.column_config.TextColumn("📝 Notes", width="medium"),
        "created_at": None,
    }

    column_order = ["id", "title", "author", "genre", "buy_price", "target_price", "stock", "notes"]

    # Data editor
    edited = st.data_editor(
        df,
        num_rows="dynamic",
        hide_index=True,
        key=f"editor_active_{st.session_state.refresh_key}",
        column_config=column_config,
        column_order=column_order,
        width='stretch',
    )

    # Action buttons
    col1, col2 = st.columns([3, 1])

    with col1:
        if st.button("💾 Save Changes", type="primary", key="save_active", width='stretch'):
            with st.spinner("Saving changes..."):
                success, msg = save_books_bulk(edited.to_dict('records'), "active")
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
        if st.button("🔄 Refresh", key="refresh_active", width='stretch'):
            show_success_toast("Refreshed!")
            st.session_state.refresh_key += 1
            st.rerun()

    if books:
        st.caption("💡 Tip: Edit cells directly, add rows with '+', then click Save")


# ============================================================================
# TAB 2: SALES HISTORY (CHRONOLOGICAL VIEW) - FIXED DATE LOGIC
# ============================================================================
def _render_sales_history_table():
    """Render chronological sales history with expandable book details."""

    sales_history = get_sales_history_grouped()

    if not sales_history:
        st.info("📭 No sales recorded yet")
        st.caption("Sales will appear here after you record your first transaction")
        return

    # Date period filter
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
    with col1:
        period_filter = st.selectbox(
            "📅 Period",
            ["All Time", "Last 7 Days", "Last 30 Days", "This Week (Mon-Sun)", "This Month"],
            key="sales_period_filter"
        )

    # ✅ FIXED: Apply date filter correctly
    today = datetime.now().date()

    if period_filter == "Last 7 Days":
        # Last 7 days from today (rolling)
        cutoff_date = today - timedelta(days=7)
        sales_history = [
            s for s in sales_history
            if datetime.strptime(s['date'], "%Y-%m-%d").date() >= cutoff_date
        ]

    elif period_filter == "Last 30 Days":
        # Last 30 days from today (rolling)
        cutoff_date = today - timedelta(days=30)
        sales_history = [
            s for s in sales_history
            if datetime.strptime(s['date'], "%Y-%m-%d").date() >= cutoff_date
        ]

    elif period_filter == "This Week (Mon-Sun)":
        # Current Monday-Sunday week
        days_since_monday = today.weekday()  # 0 = Monday
        monday = today - timedelta(days=days_since_monday)
        sunday = monday + timedelta(days=6)

        sales_history = [
            s for s in sales_history
            if monday <= datetime.strptime(s['date'], "%Y-%m-%d").date() <= sunday
        ]

    elif period_filter == "This Month":
        # Current calendar month
        first_of_month = today.replace(day=1)
        sales_history = [
            s for s in sales_history
            if datetime.strptime(s['date'], "%Y-%m-%d").date() >= first_of_month
        ]

    if not sales_history:
        st.info(f"📭 No sales in {period_filter.lower()}")
        return

    # ✅ Summary metrics for selected period with clear date range
    total_transactions = len(sales_history)
    total_books_sold = sum(s['num_books'] for s in sales_history)
    total_revenue = sum(s['total'] for s in sales_history)
    total_profit = sum(s['profit'] for s in sales_history)

    # Show exact date range for selected period
    if period_filter == "Last 7 Days":
        cutoff = today - timedelta(days=7)
        date_range = f"{cutoff.strftime('%d/%m/%Y')} → {today.strftime('%d/%m/%Y')}"
    elif period_filter == "Last 30 Days":
        cutoff = today - timedelta(days=30)
        date_range = f"{cutoff.strftime('%d/%m/%Y')} → {today.strftime('%d/%m/%Y')}"
    elif period_filter == "This Week (Mon-Sun)":
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        sunday = monday + timedelta(days=6)
        date_range = f"Mon {monday.strftime('%d/%m')} - Sun {sunday.strftime('%d/%m/%Y')}"
    elif period_filter == "This Month":
        date_range = today.strftime("%B %Y")
    else:
        date_range = "All dates"

    st.markdown(f"**Period: {period_filter}** • {date_range}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🛒 Transactions", total_transactions)
    with col2:
        st.metric("📚 Books Sold", total_books_sold)
    with col3:
        st.metric("💰 Revenue", f"€{total_revenue:.2f}")
    with col4:
        st.metric("📈 Profit", f"€{total_profit:.2f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Display each transaction (rest of the function stays the same)
    for sale in sales_history:
        # Format date
        try:
            date_obj = datetime.strptime(sale['date'], "%Y-%m-%d")
            display_date = date_obj.strftime("%d/%m/%Y")
        except:
            display_date = sale['date']

        # Transaction type icon
        type_icon = "📦" if sale['type'] == 'bundle' else "📖"

        # Profit color
        profit_color = "🟢" if sale['profit'] >= 0 else "🔴"

        with st.expander(
            f"{type_icon} **`{sale['sale_id']}`** | "
            f"{display_date} | "
            f"👤 {sale['customer']} | "
            f"{sale['platform']} | "
            f"💰 `€{sale['total']:.2f}` | "
            f"Profit {profit_color} `€{sale['profit']:.2f}`",
            expanded=False
        ):
            # Books sold in this transaction
            st.markdown("**📚 Books Sold:**")

            books_df = pd.DataFrame(sale['books'])
            books_df['total'] = books_df['total'].apply(lambda x: f"€{x:.2f}")
            books_df['profit'] = books_df['profit'].apply(lambda x: f"€{x:.2f}")
            books_df['price_per_book'] = books_df['price_per_book'].apply(lambda x: f"€{x:.2f}")

            st.dataframe(
                books_df,
                column_config={
                    'book_id': st.column_config.TextColumn('Book ID', width='small'),
                    'title': st.column_config.TextColumn('Title', width='large'),
                    'qty': st.column_config.NumberColumn('Qty', width='small'),
                    'price_per_book': st.column_config.TextColumn('Price/Book', width='small'),
                    'total': st.column_config.TextColumn('Total', width='small'),
                    'profit': st.column_config.TextColumn('Profit', width='small'),
                },
                hide_index=True,
                width='stretch'
            )

            # Transaction summary
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.caption("📦 Total Books")
                st.write(f"**{sale['num_books']}**")
            with col2:
                st.caption("💰 Total Paid")
                st.write(f"**€{sale['total']:.2f}**")
            with col3:
                st.caption("📈 Total Profit")
                profit_icon = "💚" if sale['profit'] >= 0 else "💔"
                st.write(f"**{profit_icon} €{sale['profit']:.2f}**")
            with col4:
                margin = (sale['profit'] / sale['total'] * 100) if sale['total'] > 0 else 0
                st.caption("📊 Margin")
                st.write(f"**{margin:.1f}%**")


# ============================================================================
# TAB 3: BOOK PERFORMANCE (ANALYTICS)
# ============================================================================
def _render_book_performance_table():
    """Render lifetime performance statistics for all books."""

    performance = get_book_performance_stats()

    if not performance:
        st.info("📭 No books in database")
        return

    # Filter controls
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        status_filter = st.selectbox(
            "Status Filter",
            ["All", "Active", "Sold Out", "Never Sold"],
            key="perf_status_filter"
        )
    with col2:
        sort_by = st.selectbox(
            "Sort By",
            ["Total Sold", "Revenue", "Profit", "Margin %", "Book ID"],
            key="perf_sort"
        )

    # Apply filters
    filtered = performance
    if status_filter == "Active":
        filtered = [b for b in filtered if b['status'] == 'Active']
    elif status_filter == "Sold Out":
        filtered = [b for b in filtered if b['status'] == 'Sold Out']
    elif status_filter == "Never Sold":
        filtered = [b for b in filtered if b['total_sold'] == 0]

    # Apply sorting
    sort_keys = {
        "Total Sold": lambda x: x['total_sold'],
        "Revenue": lambda x: x['total_revenue'],
        "Profit": lambda x: x['total_profit'],
        "Margin %": lambda x: x['avg_margin'],
        "Book ID": lambda x: x['id']
    }
    filtered.sort(key=sort_keys[sort_by], reverse=(sort_by != "Book ID"))

    if not filtered:
        st.info(f"📭 No books match filter: {status_filter}")
        return

    st.success(f"📊 Analyzing {len(filtered)} book(s)")

    # Summary metrics
    total_books = len(filtered)
    books_with_sales = len([b for b in filtered if b['total_sold'] > 0])
    total_sold_qty = sum(b['total_sold'] for b in filtered)
    total_rev = sum(b['total_revenue'] for b in filtered)
    total_prof = sum(b['total_profit'] for b in filtered)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("📚 Total Books", total_books)
    with col2:
        st.metric("✅ With Sales", books_with_sales)
    with col3:
        st.metric("📦 Units Sold", total_sold_qty)
    with col4:
        st.metric("💰 Revenue", f"€{total_rev:.2f}")
    with col5:
        st.metric("📈 Profit", f"€{total_prof:.2f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Performance table
    df = pd.DataFrame(filtered)

    display_df = df[[
        'id', 'title', 'author', 'status', 'current_stock',
        'total_sold', 'total_revenue', 'total_profit', 'avg_margin',
        'num_sales', 'velocity'
    ]].copy()

    st.dataframe(
        display_df,
        column_config={
            'id': st.column_config.TextColumn('Book ID', width='small'),
            'title': st.column_config.TextColumn('Title', width='large'),
            'author': st.column_config.TextColumn('Author', width='medium'),
            'status': st.column_config.TextColumn('Status', width='small'),
            'current_stock': st.column_config.NumberColumn('Stock', width='small'),
            'total_sold': st.column_config.NumberColumn('Sold', width='small'),
            'total_revenue': st.column_config.NumberColumn('Revenue', format='€%.2f', width='small'),
            'total_profit': st.column_config.NumberColumn('Profit', format='€%.2f', width='small'),
            'avg_margin': st.column_config.NumberColumn('Margin %', format='%.1f%%', width='small'),
            'num_sales': st.column_config.NumberColumn('# Sales', width='small'),
            'velocity': st.column_config.NumberColumn('Velocity', format='%.2f', width='small', help='Books sold per day')
        },
        hide_index=True,
        width='stretch'
    )

    st.caption("💡 **Velocity** = Books sold per day since first sale")

    # Insights
    st.markdown("---")
    st.markdown("**📊 Quick Insights:**")

    # Best seller
    if books_with_sales > 0:
        best_seller = max(filtered, key=lambda x: x['total_sold'])
        st.success(f"🥇 **Best Seller**: {best_seller['title']} ({best_seller['total_sold']} sold)")

    # Most profitable
    if books_with_sales > 0:
        most_profitable = max(filtered, key=lambda x: x['total_profit'])
        st.success(f"💰 **Most Profitable**: {most_profitable['title']} (€{most_profitable['total_profit']:.2f} profit)")

    # Never sold
    never_sold = [b for b in filtered if b['total_sold'] == 0 and b['status'] == 'Active']
    if never_sold:
        st.warning(f"⚠️ **{len(never_sold)} book(s)** have never sold (consider pricing/marketing)")
