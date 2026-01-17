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
        _render_active_inventory_table()

    with tab2:
        _render_restock_tab()

    with tab3:
        _render_sales_history_table()

    with tab4:
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

        # ✅ SORT BY STOCK (ASCENDING - LOW STOCK FIRST)
        books_sorted = sorted(books, key=lambda x: x['stock'], reverse=True)
        df = pd.DataFrame(books_sorted)

    # Column configuration
    column_config = {
        "id": st.column_config.TextColumn("🆔 ID", width="small", disabled=True),
        "title": st.column_config.TextColumn("📖 Title", width="medium", required=True),
        "stock": st.column_config.NumberColumn("📦 Stock", min_value=0, step=1, width="small"),
        "author": st.column_config.TextColumn("✍️ Author", width="small"),
        "genre": st.column_config.SelectboxColumn("Genre", options=GENRES, width="small"),
        "buy_price": st.column_config.NumberColumn("Buy €", format="%.2f", min_value=0, width="small"),
        "target_price": st.column_config.NumberColumn("Target €", format="%.2f", min_value=0, width="small"),
        "status": None,
        "notes": st.column_config.TextColumn("📝 Notes", width="medium"),
        "created_at": None,
    }

    column_order = ["id", "title", "stock", "genre", "buy_price", "target_price", "author","notes"]

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
        # ✅ NEW: QUICK STOCK REFERENCE (COLLAPSIBLE)
        # ============================================================================
        st.markdown("<br>", unsafe_allow_html=True)

        with st.expander("📦 **Quick Stock Reference** - View book details", expanded=False):
            st.caption("💡 Select a book to see full details • Sorted by stock (lowest first)")

            # Create book selection dropdown
            book_options = {
                f"📚 {b['id']} - {b['title'][:40]} ({b['stock']} in stock)": b['id']
                for b in books_sorted
            }
            book_options = {"Select a book...": None, **book_options}

            selected_display = st.selectbox(
                "Choose book:",
                list(book_options.keys()),
                key="quick_ref_book_select",
                label_visibility="collapsed"
            )

            selected_book_id = book_options[selected_display]

            if selected_book_id:
                # Get selected book details
                selected_book = next((b for b in books_sorted if b['id'] == selected_book_id), None)

                if selected_book:
                    # Display book details in a nice card
                    st.markdown(
                        f"""
                        <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
                                    padding: 20px; border-radius: 12px; border-left: 4px solid #667eea; margin-top: 15px;">
                            <h3 style="color: #b8b8ff; margin: 0 0 15px 0;">📖 {selected_book['title']}</h3>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Two-column layout for details
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**📊 Inventory Info:**")
                        st.caption(f"🆔 **Book ID:** `{selected_book['id']}`")
                        st.caption(f"📦 **Current Stock:** `{selected_book['stock']}` copies")
                        st.caption(f"📚 **Genre:** {selected_book['genre']}")
                        st.caption(f"✍️ **Author:** {selected_book['author'] if selected_book['author'] else 'Not specified'}")

                        # Stock status indicator
                        if selected_book['stock'] <= 1:
                            st.error("🔴 **Critical Stock** - Restock needed!")
                        elif selected_book['stock'] <= 2:
                            st.warning("🟡 **Low Stock** - Consider restocking")
                        else:
                            st.success("🟢 **Good Stock Level**")

                    with col2:
                        st.markdown("**💰 Pricing Info:**")
                        st.caption(f"💵 **Buy Price:** €{selected_book['buy_price']:.2f}")
                        st.caption(f"🎯 **Target Price:** €{selected_book['target_price']:.2f}")

                        # Calculate potential profit per book
                        if selected_book['target_price'] > 0:
                            potential_profit = selected_book['target_price'] - selected_book['buy_price']
                            if potential_profit > 0:
                                margin = (potential_profit / selected_book['target_price']) * 100
                                st.caption(f"📈 **Potential Profit:** €{potential_profit:.2f} ({margin:.1f}% margin)")
                            else:
                                st.caption(f"⚠️ **Warning:** Selling below cost (€{abs(potential_profit):.2f} loss)")

                        # Total inventory value
                        inventory_value = selected_book['stock'] * selected_book['buy_price']
                        potential_revenue = selected_book['stock'] * selected_book['target_price']
                        st.caption(f"💼 **Total Invested:** €{inventory_value:.2f}")
                        if selected_book['target_price'] > 0:
                            st.caption(f"💰 **Potential Revenue:** €{potential_revenue:.2f}")

                    # Notes section (if exists)
                    if selected_book.get('notes'):
                        st.markdown("**📝 Notes:**")
                        st.info(selected_book['notes'])

                    st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.info("👆 Select a book from the dropdown above to view details")

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
        </div>
        """,
        unsafe_allow_html=True
    )

    # ============================================================================
    # ✅ NEW: SHOW SOLD-OUT BOOKS LIST FIRST (BEFORE ACTION SELECTION)
    # ============================================================================
    if sold_out_books:

        with st.expander(f"📋 View all {len(sold_out_books)} sold-out books", expanded=False):
            st.caption("💡 Books with 0 stock that need restocking")

            # Display in 2 columns for better readability
            col1, col2 = st.columns(2)

            mid_point = len(sold_out_books) // 2

            with col1:
                for book in sold_out_books[:mid_point]:
                    st.markdown(
                        f"📕 **{book['id']}** - {book['title'][:35]}"
                        f"{'...' if len(book['title']) > 35 else ''}"
                    )

            with col2:
                for book in sold_out_books[mid_point:]:
                    st.markdown(
                        f"📕 **{book['id']}** - {book['title'][:35]}"
                        f"{'...' if len(book['title']) > 35 else ''}"
                    )
    else:
        st.success("✅ Great news! No books are sold out")
        st.caption("💡 All your books are currently in stock")

    st.markdown("---")

    # ✅ THREE CLEAR OPTIONS (RADIO BUTTONS) - NOW AFTER THE LIST
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
            st.info("💡 All your books are currently in stock")
            return

        # Dropdown to select book (removed redundant count message)
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
# TAB 4: BOOK PERFORMANCE (ADVANCED ANALYTICS)
# ============================================================================
def _render_book_performance_table():
    """Render advanced performance analytics with actionable insights."""

    performance = get_book_performance_stats()

    if not performance:
        st.info("📭 No books in database")
        return

    # ============================================================================
    # 📊 OVERVIEW METRICS
    # ============================================================================
    st.markdown("### 📊 Performance Overview")

    total_books = len(performance)
    books_with_sales = [b for b in performance if b['total_sold'] > 0]
    active_books = [b for b in performance if b['status'] == 'Active']

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("📚 Total Books", total_books)
        st.caption("All time inventory")

    with col2:
        st.metric("✅ With Sales", len(books_with_sales))
        sell_through = (len(books_with_sales) / total_books * 100) if total_books > 0 else 0
        st.caption(f"{sell_through:.0f}% sell-through rate")

    with col3:
        total_invested = sum(b['current_stock'] * b.get('buy_price', 0) for b in active_books)
        st.metric("💰 Capital Invested", f"€{total_invested:.2f}")
        st.caption("In current stock")

    with col4:
        total_profit = sum(b['total_profit'] for b in books_with_sales)
        st.metric("📈 Total Profit", f"€{total_profit:.2f}")
        avg_profit = total_profit / len(books_with_sales) if books_with_sales else 0
        st.caption(f"€{avg_profit:.2f} avg per book")

    with col5:
        total_revenue = sum(b['total_revenue'] for b in books_with_sales)
        avg_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        st.metric("📊 Avg Margin", f"{avg_margin:.1f}%")
        st.caption("Across all sales")

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # 🌟 PERFORMANCE CATEGORIES (SMART SEGMENTATION)
    # ============================================================================
    st.markdown("### 🌟 Performance Categories")
    st.caption("💡 Books automatically categorized by sales data and profitability")

    # Calculate performance categories
    star_performers = []
    cash_cows = []
    rising_stars = []
    slow_movers = []
    dead_stock = []

    for book in performance:
        if book['total_sold'] == 0 and book['status'] == 'Active':
            dead_stock.append(book)
        elif book['total_sold'] >= 10 and book['total_profit'] > 50:
            star_performers.append(book)
        elif book['velocity'] > 0.5 and book['total_sold'] >= 3:
            rising_stars.append(book)
        elif book['total_sold'] > 0 and book['avg_margin'] > 40:
            cash_cows.append(book)
        elif book['total_sold'] > 0 and book['velocity'] < 0.2:
            slow_movers.append(book)

    # Display categories in colored cards
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 15px; border-radius: 10px; text-align: center; color: white;">
                <h2 style="margin: 0; font-size: 32px;">🌟</h2>
                <p style="margin: 5px 0; font-size: 12px; opacity: 0.9;">STAR PERFORMERS</p>
                <h3 style="margin: 5px 0; font-size: 24px;">{len(star_performers)}</h3>
                <p style="margin: 0; font-size: 11px; opacity: 0.8;">High sales + profit</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                        padding: 15px; border-radius: 10px; text-align: center; color: white;">
                <h2 style="margin: 0; font-size: 32px;">💰</h2>
                <p style="margin: 5px 0; font-size: 12px; opacity: 0.9;">CASH COWS</p>
                <h3 style="margin: 5px 0; font-size: 24px;">{len(cash_cows)}</h3>
                <p style="margin: 0; font-size: 11px; opacity: 0.8;">High margins</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        padding: 15px; border-radius: 10px; text-align: center; color: white;">
                <h2 style="margin: 0; font-size: 32px;">🚀</h2>
                <p style="margin: 5px 0; font-size: 12px; opacity: 0.9;">RISING STARS</p>
                <h3 style="margin: 5px 0; font-size: 24px;">{len(rising_stars)}</h3>
                <p style="margin: 0; font-size: 11px; opacity: 0.8;">Fast moving</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%);
                        padding: 15px; border-radius: 10px; text-align: center; color: white;">
                <h2 style="margin: 0; font-size: 32px;">⚠️</h2>
                <p style="margin: 5px 0; font-size: 12px; opacity: 0.9;">SLOW MOVERS</p>
                <h3 style="margin: 5px 0; font-size: 24px;">{len(slow_movers)}</h3>
                <p style="margin: 0; font-size: 11px; opacity: 0.8;">Low velocity</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col5:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
                        padding: 15px; border-radius: 10px; text-align: center; color: #333;">
                <h2 style="margin: 0; font-size: 32px;">🔴</h2>
                <p style="margin: 5px 0; font-size: 12px; opacity: 0.9;">DEAD STOCK</p>
                <h3 style="margin: 5px 0; font-size: 24px;">{len(dead_stock)}</h3>
                <p style="margin: 0; font-size: 11px; opacity: 0.8;">Never sold</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # 📈 VISUAL ANALYTICS
    # ============================================================================
    st.markdown("### 📈 Visual Insights")

    tab_charts, tab_top10, tab_categories = st.tabs([
        "📊 Revenue & Profit",
        "🏆 Top 10 Performers",
        "🔍 Category Details"
    ])

    # TAB 1: Revenue & Profit Charts
    with tab_charts:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**💰 Revenue Contribution**")
            if books_with_sales:
                # Top 10 by revenue
                top_revenue = sorted(books_with_sales, key=lambda x: x['total_revenue'], reverse=True)[:10]
                revenue_data = pd.DataFrame([
                    {'Book': b['title'][:30], 'Revenue': b['total_revenue']}
                    for b in top_revenue
                ])
                st.bar_chart(revenue_data.set_index('Book'))
            else:
                st.info("No sales data yet")

        with col2:
            st.markdown("**📈 Profit Contribution**")
            if books_with_sales:
                # Top 10 by profit
                top_profit = sorted(books_with_sales, key=lambda x: x['total_profit'], reverse=True)[:10]
                profit_data = pd.DataFrame([
                    {'Book': b['title'][:30], 'Profit': b['total_profit']}
                    for b in top_profit
                ])
                st.bar_chart(profit_data.set_index('Book'))
            else:
                st.info("No sales data yet")

        st.markdown("<br>", unsafe_allow_html=True)

        # Margin distribution
        st.markdown("**📊 Profit Margin Distribution**")
        if books_with_sales:
            margin_ranges = {
                '0-20%': len([b for b in books_with_sales if 0 <= b['avg_margin'] < 20]),
                '20-40%': len([b for b in books_with_sales if 20 <= b['avg_margin'] < 40]),
                '40-60%': len([b for b in books_with_sales if 40 <= b['avg_margin'] < 60]),
                '60-80%': len([b for b in books_with_sales if 60 <= b['avg_margin'] < 80]),
                '80-100%': len([b for b in books_with_sales if b['avg_margin'] >= 80]),
            }
            margin_df = pd.DataFrame(list(margin_ranges.items()), columns=['Margin Range', 'Books'])
            st.bar_chart(margin_df.set_index('Margin Range'))
        else:
            st.info("No sales data yet")

    # TAB 2: Top 10 Performers
    with tab_top10:
        if not books_with_sales:
            st.info("No sales data yet")
        else:
            col1, col2 = st.columns([2, 1])

            with col1:
                sort_metric = st.radio(
                    "Sort by:",
                    ["Total Sold", "Revenue", "Profit", "Margin %"],
                    horizontal=True
                )

            sort_keys = {
                "Total Sold": lambda x: x['total_sold'],
                "Revenue": lambda x: x['total_revenue'],
                "Profit": lambda x: x['total_profit'],
                "Margin %": lambda x: x['avg_margin']
            }

            top_10 = sorted(books_with_sales, key=sort_keys[sort_metric], reverse=True)[:10]

            for idx, book in enumerate(top_10, 1):
                medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"#{idx}"

                with st.expander(
                    f"{medal} **{book['title']}** | "
                    f"Sold: {book['total_sold']} | "
                    f"Revenue: €{book['total_revenue']:.2f} | "
                    f"Profit: €{book['total_profit']:.2f}",
                    expanded=(idx <= 3)
                ):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.caption("**📊 Sales Data**")
                        st.write(f"🆔 ID: `{book['id']}`")
                        st.write(f"📦 Sold: **{book['total_sold']}** units")
                        st.write(f"🔢 Transactions: **{book['num_sales']}**")
                        st.write(f"📦 Stock Left: **{book['current_stock']}**")

                    with col2:
                        st.caption("**💰 Financial**")
                        st.write(f"💵 Revenue: **€{book['total_revenue']:.2f}**")
                        st.write(f"📈 Profit: **€{book['total_profit']:.2f}**")
                        st.write(f"📊 Margin: **{book['avg_margin']:.1f}%**")
                        roi = (book['total_profit'] / (book['total_sold'] * book.get('buy_price', 1)) * 100) if book.get('buy_price', 0) > 0 else 0
                        st.write(f"💎 ROI: **{roi:.0f}%**")

                    with col3:
                        st.caption("**⚡ Performance**")
                        st.write(f"🚀 Velocity: **{book['velocity']:.2f}** books/day")
                        avg_per_sale = book['total_sold'] / book['num_sales'] if book['num_sales'] > 0 else 0
                        st.write(f"📦 Avg per sale: **{avg_per_sale:.1f}**")

                        # Status indicator
                        if book['velocity'] > 0.5:
                            st.success("🔥 **Hot seller!**")
                        elif book['velocity'] > 0.2:
                            st.info("✅ **Steady sales**")
                        else:
                            st.warning("⚠️ **Slow mover**")

    # TAB 3: Category Details
    with tab_categories:
        category_select = st.selectbox(
            "Select category to view details:",
            ["🌟 Star Performers", "💰 Cash Cows", "🚀 Rising Stars", "⚠️ Slow Movers", "🔴 Dead Stock"]
        )

        if category_select == "🌟 Star Performers":
            st.markdown("### 🌟 Star Performers")
            st.caption("💡 Books with high sales volume (≥10 sold) and significant profit (>€50)")

            if not star_performers:
                st.info("No star performers yet. Keep selling!")
            else:
                for book in sorted(star_performers, key=lambda x: x['total_profit'], reverse=True):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        with col1:
                            st.markdown(f"**📖 {book['title']}**")
                            st.caption(f"🆔 {book['id']} • ✍️ {book.get('author', 'Unknown')}")
                        with col2:
                            st.metric("Sold", book['total_sold'])
                        with col3:
                            st.metric("Profit", f"€{book['total_profit']:.2f}")
                        with col4:
                            st.metric("Margin", f"{book['avg_margin']:.0f}%")
                        st.markdown("---")

        elif category_select == "💰 Cash Cows":
            st.markdown("### 💰 Cash Cows")
            st.caption("💡 Books with excellent profit margins (>40%) - high-value items")

            if not cash_cows:
                st.info("No cash cows yet")
            else:
                for book in sorted(cash_cows, key=lambda x: x['avg_margin'], reverse=True):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        with col1:
                            st.markdown(f"**📖 {book['title']}**")
                            st.caption(f"🆔 {book['id']} • Stock: {book['current_stock']}")
                        with col2:
                            st.metric("Margin", f"{book['avg_margin']:.1f}%")
                        with col3:
                            st.metric("Profit", f"€{book['total_profit']:.2f}")
                        with col4:
                            st.metric("Sold", book['total_sold'])
                        st.markdown("---")

        elif category_select == "🚀 Rising Stars":
            st.markdown("### 🚀 Rising Stars")
            st.caption("💡 Books with high velocity (>0.5 books/day) - trending items")

            if not rising_stars:
                st.info("No rising stars yet")
            else:
                for book in sorted(rising_stars, key=lambda x: x['velocity'], reverse=True):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        with col1:
                            st.markdown(f"**📖 {book['title']}**")
                            st.caption(f"🆔 {book['id']} • Added: {book.get('first_sale', 'Recently')}")
                        with col2:
                            st.metric("Velocity", f"{book['velocity']:.2f}/day")
                        with col3:
                            st.metric("Sold", book['total_sold'])
                        with col4:
                            st.metric("Stock", book['current_stock'])

                        if book['current_stock'] <= 2:
                            st.warning("⚠️ **Urgent:** Low stock! Consider restocking soon")
                        st.markdown("---")

        elif category_select == "⚠️ Slow Movers":
            st.markdown("### ⚠️ Slow Movers")
            st.caption("💡 Books with low sales velocity (<0.2 books/day) - need attention")

            if not slow_movers:
                st.success("✅ No slow movers - all books selling well!")
            else:
                st.warning(f"📉 {len(slow_movers)} book(s) need attention")

                for book in sorted(slow_movers, key=lambda x: x['velocity']):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        with col1:
                            st.markdown(f"**📖 {book['title']}**")
                            st.caption(f"🆔 {book['id']} • Stock: {book['current_stock']}")
                        with col2:
                            st.metric("Velocity", f"{book['velocity']:.3f}/day")
                        with col3:
                            st.metric("Total Sold", book['total_sold'])
                        with col4:
                            days_since = book.get('days_since_last_sale', 999)
                            st.metric("Days Idle", days_since if days_since < 999 else "N/A")

                        # Recommendations
                        st.caption("💡 **Recommendations:**")
                        recommendations = []
                        if book['avg_margin'] < 30:
                            recommendations.append("• Consider lowering price (low margin)")
                        if book['current_stock'] > 5:
                            recommendations.append("• High stock + slow sales = Run promotion")
                        if days_since > 60:
                            recommendations.append("• No sales in 2+ months - Bundle with popular book")

                        if recommendations:
                            for rec in recommendations:
                                st.caption(rec)
                        st.markdown("---")

        elif category_select == "🔴 Dead Stock":
            st.markdown("### 🔴 Dead Stock")
            st.caption("💡 Books that have NEVER sold - critical action needed")

            if not dead_stock:
                st.success("✅ Excellent! No dead stock - all books have sold at least once")
            else:
                st.error(f"🚨 {len(dead_stock)} book(s) have never sold")

                # Calculate capital tied up
                dead_capital = sum(b['current_stock'] * b.get('buy_price', 0) for b in dead_stock)
                st.warning(f"💰 **€{dead_capital:.2f}** capital tied up in unsold inventory")

                for book in sorted(dead_stock, key=lambda x: x['current_stock'] * x.get('buy_price', 0), reverse=True):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        with col1:
                            st.markdown(f"**📖 {book['title']}**")
                            st.caption(f"🆔 {book['id']} • ✍️ {book.get('author', 'Unknown')}")
                        with col2:
                            st.metric("Stock", book['current_stock'])
                        with col3:
                            invested = book['current_stock'] * book.get('buy_price', 0)
                            st.metric("Invested", f"€{invested:.2f}")
                        with col4:
                            target = book.get('target_price', 0)
                            st.metric("Target", f"€{target:.2f}")

                        # Urgent actions
                        st.error("**⚠️ Urgent Actions Needed:**")
                        st.caption("1️⃣ Check pricing - is it too high?")
                        st.caption("2️⃣ Improve listing - better photo/description?")
                        st.caption("3️⃣ Bundle with popular books")
                        st.caption("4️⃣ Run flash sale (20-30% off)")
                        st.caption("5️⃣ Last resort: Donate or discount heavily")
                        st.markdown("---")

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # 🎯 ACTIONABLE RECOMMENDATIONS
    # ============================================================================
    st.markdown("### 🎯 Smart Recommendations")

    rec_col1, rec_col2, rec_col3 = st.columns(3)

    with rec_col1:
        st.markdown("**🔄 Restock Urgently**")
        restock_urgent = [
            b for b in rising_stars + star_performers
            if b['current_stock'] <= 2
        ]

        if restock_urgent:
            for book in restock_urgent[:5]:
                st.success(f"📕 {book['id']} - {book['title'][:25]}")
                st.caption(f"   Stock: {book['current_stock']} • Velocity: {book['velocity']:.2f}/day")
        else:
            st.info("✅ All hot sellers have good stock")

    with rec_col2:
        st.markdown("**📈 Consider Price Increase**")
        price_increase = [
            b for b in books_with_sales
            if b['velocity'] > 0.5 and b['avg_margin'] < 40
        ]

        if price_increase:
            for book in sorted(price_increase, key=lambda x: x['velocity'], reverse=True)[:5]:
                st.info(f"📗 {book['id']} - {book['title'][:25]}")
                st.caption(f"   Velocity: {book['velocity']:.2f}/day • Margin: {book['avg_margin']:.0f}%")
        else:
            st.info("✅ Pricing looks optimal")

    with rec_col3:
        st.markdown("**💥 Run Promotion**")
        needs_promotion = slow_movers + dead_stock

        if needs_promotion:
            for book in needs_promotion[:5]:
                st.warning(f"📙 {book['id']} - {book['title'][:25]}")
                idle_days = book.get('days_since_last_sale', 0)
                st.caption(f"   Idle: {idle_days if idle_days < 999 else 'Never sold'} days")
        else:
            st.success("✅ All books moving well!")

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # 📋 DETAILED DATA TABLE (COLLAPSIBLE)
    # ============================================================================
    with st.expander("📋 **View Full Performance Table**", expanded=False):
        st.caption("💡 Complete data for all books")

        col1, col2 = st.columns(2)
        with col1:
            table_filter = st.selectbox(
                "Filter:",
                ["All Books", "Active Only", "Sold Out", "With Sales", "Never Sold"],
                key="table_filter"
            )
        with col2:
            table_sort = st.selectbox(
                "Sort By:",
                ["Total Sold", "Revenue", "Profit", "Margin %", "Velocity", "Stock"],
                key="table_sort"
            )

        # Apply filter
        filtered_data = performance
        if table_filter == "Active Only":
            filtered_data = [b for b in performance if b['status'] == 'Active']
        elif table_filter == "Sold Out":
            filtered_data = [b for b in performance if b['status'] == 'Sold Out']
        elif table_filter == "With Sales":
            filtered_data = [b for b in performance if b['total_sold'] > 0]
        elif table_filter == "Never Sold":
            filtered_data = [b for b in performance if b['total_sold'] == 0]

        # Apply sort
        sort_keys_table = {
            "Total Sold": lambda x: x['total_sold'],
            "Revenue": lambda x: x['total_revenue'],
            "Profit": lambda x: x['total_profit'],
            "Margin %": lambda x: x['avg_margin'],
            "Velocity": lambda x: x['velocity'],
            "Stock": lambda x: x['current_stock']
        }
        filtered_data = sorted(filtered_data, key=sort_keys_table[table_sort], reverse=True)

        if filtered_data:
            df = pd.DataFrame(filtered_data)
            st.dataframe(
                df[[
                    'id', 'title', 'author', 'status', 'current_stock',
                    'total_sold', 'total_revenue', 'total_profit', 'avg_margin',
                    'num_sales', 'velocity'
                ]],
                column_config={
                    'id': st.column_config.TextColumn('ID', width='small'),
                    'title': st.column_config.TextColumn('Title', width='large'),
                    'author': st.column_config.TextColumn('Author', width='medium'),
                    'status': st.column_config.TextColumn('Status', width='small'),
                    'current_stock': st.column_config.NumberColumn('Stock', width='small'),
                    'total_sold': st.column_config.NumberColumn('Sold', width='small'),
                    'total_revenue': st.column_config.NumberColumn('Revenue', format='€%.2f', width='small'),
                    'total_profit': st.column_config.NumberColumn('Profit', format='€%.2f', width='small'),
                    'avg_margin': st.column_config.NumberColumn('Margin %', format='%.1f%%', width='small'),
                    'num_sales': st.column_config.NumberColumn('# Sales', width='small'),
                    'velocity': st.column_config.NumberColumn('Velocity', format='%.2f', width='small')
                },
                hide_index=True,
                width='stretch'
            )
        else:
            st.info("No books match the selected filter")
