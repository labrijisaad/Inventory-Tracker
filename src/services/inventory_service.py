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
        "Books with stock = 0 goes to 🔄 Restock tab",
        type="info"
    )

    # Get sold-out count for tab label
    sold_out_books = get_books("sold")
    sold_out_count = len(sold_out_books)

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        f"📦 Active Inventory ({stats['active_count']})",
        f"🔄 Restock ({sold_out_count})",
        "💰 Sales History",
        "📊 Book Performance"
    ])

    with tab1:
        st.caption("📦 Books currently in stock")
        _render_active_inventory_table()

    with tab2:
        st.caption("🔄 Add stock to sold-out books or create new books")
        _render_restock_tab()

    with tab3:
        st.caption("💰 Complete sales transaction history")
        _render_sales_history_table()

    with tab4:
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
# TAB 2: RESTOCK (IMPROVED UI WITH 3 CLEAR OPTIONS)
# ============================================================================
def _render_restock_tab():
    """Render improved restock form with 3 clear options."""
    from src.data.database import restock_book

    # Get all books for reference
    all_books = get_books()
    sold_out_books = [b for b in all_books if b['stock'] == 0]
    active_books = [b for b in all_books if b['stock'] > 0]

    # ✅ MAIN INSTRUCTION
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
                    padding: 20px; border-radius: 12px; border-left: 4px solid #667eea; margin-bottom: 20px;">
            <h3 style="color: #b8b8ff; margin: 0 0 10px 0;">📦 What would you like to do?</h3>
            <p style="color: #9ca3af; margin: 0; font-size: 14px;">
                Choose one of the three options below to manage your inventory
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ✅ THREE CLEAR OPTIONS (RADIO BUTTONS)
    action_mode = st.radio(
        "Select action:",
        [
            "🔄 Restock a sold-out book",
            "📦 Add stock to existing book",
            "✨ Create a brand new book"
        ],
        key="restock_action_mode",
        help="Choose what you want to do"
    )

    st.markdown("---")

    # ============================================================================
    # OPTION 1: RESTOCK SOLD-OUT BOOK
    # ============================================================================
    if action_mode == "🔄 Restock a sold-out book":
        st.markdown("### 🔄 Restock Sold-Out Book")
        st.caption("💡 Select a book that's completely out of stock to replenish inventory")

        if not sold_out_books:
            st.success("✅ Great news! No books are sold out")
            st.info("💡 All your books are currently in stock")
            return

        # Show sold-out count
        st.info(f"📦 You have **{len(sold_out_books)} sold-out book(s)** ready to restock")

        # Dropdown to select book
        book_options = {
            f"📕 {b['id']} - {b['title'][:40]}": b['id']
            for b in sold_out_books
        }
        book_options = {"Select a book...": None, **book_options}

        selected_display = st.selectbox(
            "Choose book:",
            list(book_options.keys()),
            key="soldout_select"
        )

        selected_book_id = book_options[selected_display]

        if not selected_book_id:
            st.warning("👆 Please select a book from the list above")

            # Show preview of sold-out books
            with st.expander(f"📋 View all {len(sold_out_books)} sold-out books", expanded=False):
                for book in sold_out_books:
                    st.markdown(f"- **{book['id']}** - {book['title']} (€{book['buy_price']:.2f})")
            return

        # Get selected book
        existing_book = next((b for b in sold_out_books if b['id'] == selected_book_id), None)

        # Show book details
        st.success(f"✅ Selected: **{existing_book['title']}** by {existing_book['author']}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📖 Current Details:**")
            st.caption(f"🆔 ID: `{existing_book['id']}`")
            st.caption(f"✍️ Author: {existing_book['author']}")
            st.caption(f"📚 Genre: {existing_book['genre']}")
            st.caption(f"💰 Current buy price: €{existing_book['buy_price']:.2f}")

        with col2:
            st.markdown("**💵 Update Pricing (Optional):**")
            st.caption("💡 Leave unchanged if price hasn't changed")

            new_buy_price = st.number_input(
                "New buy price (€)",
                min_value=0.0,
                value=float(existing_book['buy_price']),
                step=0.25,
                key="soldout_buy_price",
                help="Update if your supplier changed prices"
            )

            new_target_price = st.number_input(
                "Target price (€)",
                min_value=0.0,
                value=float(existing_book['target_price']),
                step=0.25,
                key="soldout_target_price"
            )

        st.markdown("---")

        # Quantity input
        st.markdown("### 📦 How many copies to add?")
        quantity = st.number_input(
            "Quantity",
            min_value=1,
            value=10,
            step=1,
            key="soldout_qty",
            help="How many copies did you buy?"
        )

        st.caption(f"→ After restocking: **{existing_book['stock']} + {quantity} = {existing_book['stock'] + quantity}** copies")

        st.markdown("---")

        # Submit button
        if st.button("✅ Restock This Book", type="primary", width='stretch', key="submit_soldout"):
            book_data = {
                'id': existing_book['id'],
                'title': existing_book['title'],
                'author': existing_book['author'],
                'genre': existing_book['genre'],
                'buy_price': new_buy_price,
                'target_price': new_target_price,
                'notes': existing_book['notes']
            }

            with st.spinner("Restocking..."):
                success, msg, book_id = restock_book(book_data, quantity, is_existing=True)
                if success:
                    show_success_toast(f"Restocked {book_id}!")
                    st.success(msg)
                    st.balloons()
                    time.sleep(1.5)
                    st.rerun()
                else:
                    show_error_toast(msg)
                    st.error(msg)

    # ============================================================================
    # OPTION 2: ADD STOCK TO EXISTING BOOK
    # ============================================================================
    elif action_mode == "📦 Add stock to existing book":
        st.markdown("### 📦 Add Stock to Existing Book")
        st.caption("💡 Add more copies to any book in your inventory (even if already in stock)")

        if not all_books:
            st.info("📭 No books in database. Create your first book below!")
            return

        # Manual ID entry
        st.markdown("**🆔 Enter Book ID:**")
        manual_id = st.text_input(
            "Book ID",
            placeholder="e.g., BOOK-001",
            key="existing_book_id",
            help="Type the exact book ID"
        )

        if not manual_id:
            st.info("👆 Enter a book ID above (e.g., BOOK-001)")

            # Show all books as reference
            with st.expander(f"📋 View all {len(all_books)} books for reference", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Active Books:**")
                    for book in active_books[:10]:
                        st.caption(f"📗 {book['id']} - {book['title'][:30]} (Stock: {book['stock']})")
                with col2:
                    st.markdown("**Sold Out Books:**")
                    for book in sold_out_books[:10]:
                        st.caption(f"📕 {book['id']} - {book['title'][:30]} (Stock: 0)")
            return

        # Find book
        manual_id = manual_id.strip().upper()
        existing_book = next((b for b in all_books if b['id'] == manual_id), None)

        if not existing_book:
            st.error(f"❌ Book `{manual_id}` not found!")
            st.info("💡 Check the book list below to find the correct ID")

            with st.expander("📋 All Books", expanded=True):
                for book in all_books[:20]:
                    st.caption(f"**{book['id']}** - {book['title']}")
            return

        # Show current details
        st.success(f"✅ Found: **{existing_book['title']}**")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📊 Current Status:**")
            st.caption(f"📦 Current stock: **{existing_book['stock']}** copies")
            st.caption(f"💰 Buy price: €{existing_book['buy_price']:.2f}")
            st.caption(f"🎯 Target: €{existing_book['target_price']:.2f}")

        with col2:
            st.markdown("**💵 Update Pricing (Optional):**")
            new_buy_price = st.number_input(
                "New buy price (€)",
                min_value=0.0,
                value=float(existing_book['buy_price']),
                step=0.25,
                key="existing_buy_price"
            )

        st.markdown("---")

        # Quantity
        st.markdown("### 📦 How many copies to add?")
        quantity = st.number_input(
            "Quantity to add",
            min_value=1,
            value=5,
            step=1,
            key="existing_qty"
        )

        new_total = existing_book['stock'] + quantity
        st.caption(f"→ New total: **{existing_book['stock']} + {quantity} = {new_total}** copies")

        st.markdown("---")

        # Submit
        if st.button("✅ Add Stock", type="primary", width='stretch', key="submit_existing"):
            book_data = {
                'id': existing_book['id'],
                'title': existing_book['title'],
                'author': existing_book['author'],
                'genre': existing_book['genre'],
                'buy_price': new_buy_price,
                'target_price': existing_book['target_price'],
                'notes': existing_book['notes']
            }

            with st.spinner("Adding stock..."):
                success, msg, book_id = restock_book(book_data, quantity, is_existing=True)
                if success:
                    show_success_toast(f"Added stock to {book_id}!")
                    st.success(msg)
                    st.balloons()
                    time.sleep(1.5)
                    st.rerun()
                else:
                    show_error_toast(msg)
                    st.error(msg)

    # ============================================================================
    # OPTION 3: CREATE NEW BOOK
    # ============================================================================
    elif action_mode == "✨ Create a brand new book":
        st.markdown("### ✨ Create New Book")
        st.caption("💡 Add a completely new book to your inventory")

        # Optional: Custom ID
        with st.expander("🆔 Advanced: Set custom book ID (optional)", expanded=False):
            st.caption("💡 Leave empty to auto-generate next ID (recommended)")
            custom_id = st.text_input(
                "Custom ID",
                placeholder="e.g., BOOK-099",
                key="new_custom_id",
                help="Only use this if you need a specific ID format"
            )

        # Book details form
        st.markdown("**📝 Book Information:**")

        col1, col2 = st.columns(2)

        with col1:
            new_title = st.text_input(
                "Title *",
                placeholder="Enter book title",
                key="new_title",
                help="Required field"
            )

            new_author = st.text_input(
                "Author",
                placeholder="Enter author name",
                key="new_author"
            )

            new_genre = st.selectbox(
                "Genre",
                GENRES,
                key="new_genre"
            )

        with col2:
            new_buy_price = st.number_input(
                "Buy Price (€) *",
                min_value=0.0,
                value=0.0,
                step=0.25,
                key="new_buy_price",
                help="How much did you pay?"
            )

            new_target_price = st.number_input(
                "Target Selling Price (€)",
                min_value=0.0,
                value=0.0,
                step=0.25,
                key="new_target_price",
                help="How much do you want to sell it for?"
            )

            new_notes = st.text_area(
                "Notes",
                placeholder="ISBN, condition, publisher, etc.",
                key="new_notes",
                height=80
            )

        st.markdown("---")

        # Initial stock
        st.markdown("### 📦 Initial Stock Quantity")
        new_quantity = st.number_input(
            "How many copies?",
            min_value=1,
            value=1,
            step=1,
            key="new_qty",
            help="How many copies do you have?"
        )

        st.caption(f"→ New book will start with **{new_quantity}** copies")

        st.markdown("---")

        # Submit
        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button("✅ Create Book", type="primary", width='stretch', key="submit_new"):
                # Validation
                if not new_title.strip():
                    st.error("❌ Book title is required")
                    return

                if new_buy_price <= 0:
                    st.error("❌ Buy price must be greater than 0")
                    return

                book_data = {
                    'id': custom_id.strip().upper() if custom_id else None,
                    'title': new_title.strip(),
                    'author': new_author.strip(),
                    'genre': new_genre,
                    'buy_price': new_buy_price,
                    'target_price': new_target_price,
                    'notes': new_notes.strip()
                }

                with st.spinner("Creating book..."):
                    success, msg, book_id = restock_book(book_data, new_quantity, is_existing=False)
                    if success:
                        show_success_toast(f"Created {book_id}!")
                        st.success(msg)
                        st.balloons()
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        show_error_toast(msg)
                        st.error(msg)

        with col2:
            if st.button("🔄 Reset", width='stretch', key="reset_new"):
                st.rerun()



# ============================================================================
# TAB 3: SALES HISTORY (CHRONOLOGICAL VIEW) - FIXED DATE LOGIC
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
