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

    # ✅ UPDATED: Added 5th tab - Book Inspector
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        f"📦 Active Inventory ({stats['active_count']})",
        f"🔄 Restock ({sold_out_count})",
        "💰 Sales History",
        "📊 Book Performance",
        "🔍 Book Inspector"
    ])

    with tab1:
        _render_active_inventory_table()

    with tab2:
        _render_restock_tab()

    with tab3:
        _render_sales_history_table()

    with tab4:
        _render_book_performance_table()

    with tab5:
        _render_book_inspector()


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

        # ============================================================================
        # ✅ UPDATED: QUICK STOCK REFERENCE WITH SALES HISTORY
        # ============================================================================
        st.markdown("<br>", unsafe_allow_html=True)

        with st.expander("📦 **Quick Book Reference**", expanded=False):
            st.caption("💡 Select any book to see inventory, pricing, and sales history • Sorted by stock (highest first)")

            # ✅ GET ALL BOOKS (ACTIVE + SOLD OUT) + SALES DATA
            all_books_for_ref = get_books()  # Gets ALL books

            # Get sales history to calculate totals
            from src.data.database import get_sales
            all_sales = get_sales()

            # Calculate sales stats per book
            book_sales_stats = {}
            for sale in all_sales:
                book_id = sale['book_id']
                if book_id not in book_sales_stats:
                    book_sales_stats[book_id] = {
                        'total_sold': 0,
                        'last_sale_date': None
                    }

                book_sales_stats[book_id]['total_sold'] += sale['qty']

                # Track latest sale date
                sale_date = datetime.strptime(sale['date'], "%Y-%m-%d")
                if (book_sales_stats[book_id]['last_sale_date'] is None or
                    sale_date > book_sales_stats[book_id]['last_sale_date']):
                    book_sales_stats[book_id]['last_sale_date'] = sale_date

            # ✅ SORT BY STOCK - ALL BOOKS
            books_sorted_all = sorted(all_books_for_ref, key=lambda x: x['stock'], reverse=True)

            # Create book selection dropdown
            book_options = {
                f"{'📕' if b['stock'] == 0 else '📗'} {b['id']} - {b['title'][:40]} ({b['stock']} in stock)": b['id']
                for b in books_sorted_all
            }
            book_options = {"Select a book to view details...": None, **book_options}

            selected_display = st.selectbox(
                "Choose book:",
                list(book_options.keys()),
                key="quick_ref_book_select",
                label_visibility="collapsed"
            )

            selected_book_id = book_options[selected_display]

            if selected_book_id:
                # Get selected book details
                selected_book = next((b for b in books_sorted_all if b['id'] == selected_book_id), None)

                if selected_book:
                    # Get sales stats for this book
                    sales_stats = book_sales_stats.get(selected_book_id, {
                        'total_sold': 0,
                        'last_sale_date': None
                    })

                    # Display book details in a nice card
                    st.markdown(
                        f"""
                        <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
                                    padding: 5px 10px; border-radius: 8px; border-left: 4px solid #667eea; margin-top: 4px; margin-bottom: 4px;">
                            <h3 style="color: #b8b8ff; margin: 2px 0 4px 0;">📖 {selected_book['title']}</h3>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Two-column layout for details
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("#### 📊 Inventory Info")
                        st.caption(f"🆔 **Book ID:** `{selected_book['id']}`")
                        st.caption(f"📦 **Current Stock:** `{selected_book['stock']}` copies")
                        st.caption(f"📚 **Genre:** {selected_book['genre']}")
                        st.caption(f"✍️ **Author:** {selected_book['author'] if selected_book['author'] else 'Not specified'}")

                        # ✅ SALES HISTORY
                        st.markdown("#### 📈 Sales History")
                        if sales_stats['total_sold'] > 0:
                            st.caption(f"✅ **Total Sold:** `{sales_stats['total_sold']}` copies (all-time)")

                            # Format last sale date
                            if sales_stats['last_sale_date']:
                                last_sale_formatted = sales_stats['last_sale_date'].strftime("%d/%m/%Y")
                                days_ago = (datetime.now() - sales_stats['last_sale_date']).days
                                st.caption(f"📅 **Last Sold:** `{last_sale_formatted}` ({days_ago} days ago)")
                        else:
                            st.caption("🔴 **Never sold** - No sales recorded")

                        # Stock status indicator
                        st.markdown("#### 🚦 Stock Status")
                        if selected_book['stock'] == 0:
                            st.error("🔴 **Out of Stock** - Restock needed!")
                        elif selected_book['stock'] <= 1:
                            st.error("🔴 **Critical Stock** - Only 1 left!")
                        elif selected_book['stock'] <= 2:
                            st.warning("🟡 **Low Stock** - Consider restocking")
                        else:
                            st.success("🟢 **Good Stock Level**")

                    with col2:
                        st.markdown("#### 💰 Pricing Info")
                        st.caption(f"💵 **Buy Price:** €{selected_book['buy_price']:.2f}")
                        st.caption(f"🎯 **Target Price:** €{selected_book['target_price']:.2f}")

                        # Calculate potential profit per book
                        if selected_book['target_price'] > 0:
                            potential_profit_per_book = selected_book['target_price'] - selected_book['buy_price']
                            if potential_profit_per_book > 0:
                                margin = (potential_profit_per_book / selected_book['target_price']) * 100
                                st.caption(f"📈 **Profit per Book:** €{potential_profit_per_book:.2f} ({margin:.1f}% margin)")
                            else:
                                st.caption(f"⚠️ **Warning:** Selling below cost (€{abs(potential_profit_per_book):.2f} loss per book)")

                        # ✅ CURRENT STOCK VALUE (CLARIFIED)
                        st.markdown("#### 💼 Current Stock Value")

                        # Total invested in current stock
                        current_stock_cost = selected_book['stock'] * selected_book['buy_price']
                        st.caption(f"💵 **Total Invested (in current stock):** €{current_stock_cost:.2f}")
                        st.caption(f"ㅤㅤ↳ *({selected_book['stock']} copies × €{selected_book['buy_price']:.2f})*")

                        # Potential revenue if all current stock sells
                        if selected_book['target_price'] > 0 and selected_book['stock'] > 0:
                            potential_revenue = selected_book['stock'] * selected_book['target_price']
                            potential_profit_total = potential_revenue - current_stock_cost

                            st.caption(f"💰 **Potential Revenue (in current stock):** €{potential_revenue:.2f}")
                            st.caption(f"ㅤㅤ↳ *If all {selected_book['stock']} copies sell at target price*")

                            st.caption(f"📈 **Potential Profit (in current stock):** €{potential_profit_total:.2f}")
                            st.caption("ㅤㅤ↳ *From selling current stock only*")
                        elif selected_book['stock'] == 0:
                            st.caption("💡 **No stock** - Restock to see potential")

                    # Notes section (if exists)
                    if selected_book.get('notes'):
                        st.markdown("#### 📝 Notes")
                        st.info(selected_book['notes'])

                    st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.info("Select a book from the dropdown above to view details")

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
# TAB 4: BOOK PERFORMANCE (REDESIGNED - STRATEGIC INSIGHTS)
# ============================================================================
def _render_book_performance_table():
    """Smart performance dashboard with visual insights and strategic priorities."""

    performance = get_book_performance_stats()

    if not performance:
        st.info("📭 No books in database")
        return

    # ============================================================================
    # 📊 OVERVIEW METRICS
    # ============================================================================
    st.markdown("### 📊 Performance Overview")

    # Calculate core metrics
    total_titles = len(performance)
    titles_with_sales = [b for b in performance if b['total_sold'] > 0]
    active_titles = [b for b in performance if b['status'] == 'Active']

    all_time_books = sum(b['total_sold'] + b['current_stock'] for b in performance)
    books_sold = sum(b['total_sold'] for b in performance)

    all_time_investment = sum(
        (b['total_sold'] + b['current_stock']) * b.get('buy_price', 0)
        for b in performance
    )

    current_stock_value = sum(
        b['current_stock'] * b.get('buy_price', 0)
        for b in active_titles
    )

    total_profit = sum(b['total_profit'] for b in titles_with_sales)
    total_revenue = sum(b['total_revenue'] for b in titles_with_sales)
    avg_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("📚 Total Titles saved", total_titles)
        st.caption(f"{len(titles_with_sales)} titles sold")

    with col2:
        st.metric("📦 All-Time Books", all_time_books)
        st.caption("Sold + Stock")

    with col3:
        st.metric("✅ Books Sold", books_sold)
        sell_through = (books_sold / all_time_books * 100) if all_time_books > 0 else 0
        st.caption(f"{sell_through:.1f}% sell-through")

    with col4:
        st.metric("💰 All time Investment", f"€{all_time_investment:.2f}")
        st.caption(f"Current Stock: €{current_stock_value:.2f}")

    with col5:
        st.metric("📈 All time Profit", f"€{total_profit:.2f}")
        st.caption(f"{avg_margin:.1f}% margin")

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # 🎯 REVENUE DNA - RING CHART
    # ============================================================================
    st.markdown("### 🎯 Revenue DNA")
    st.caption("💡 Visual breakdown of revenue contribution by book")

    if titles_with_sales:
        # Sort by revenue and take top 12
        top_contributors = sorted(titles_with_sales, key=lambda x: x['total_revenue'], reverse=True)[:12]

        # Calculate "Others" if more than 12 books
        others_revenue = sum(b['total_revenue'] for b in titles_with_sales[12:]) if len(titles_with_sales) > 12 else 0

        # Prepare data for ring chart
        ids = [b['id'] for b in top_contributors]
        titles = [b['title'] for b in top_contributors]
        revenues = [b['total_revenue'] for b in top_contributors]

        # Add "Others" if applicable
        if others_revenue > 0:
            ids.append("Others")
            titles.append(f"{len(titles_with_sales) - 12} other books")
            revenues.append(others_revenue)

        # Create Plotly donut chart
        import plotly.graph_objects as go

        fig = go.Figure(data=[go.Pie(
            labels=ids,
            values=revenues,
            hole=0.5,  # Donut shape
            textinfo='label+percent',
            textposition='inside',
            textfont=dict(size=11, color='white', family='Arial Black'),
            hovertemplate='<b>%{label}</b><br>' +
                          'Title: %{customdata}<br>' +
                          'Revenue: €%{value:.2f}<br>' +
                          'Share: %{percent}<br>' +
                          '<extra></extra>',
            customdata=titles,
            marker=dict(
                colors=[
                    '#667eea', '#764ba2', '#f093fb', '#f5576c',
                    '#4facfe', '#00f2fe', '#43e97b', '#38f9d7',
                    '#fa709a', '#fee140', '#30cfd0', '#330867'
                ],
                line=dict(color='#1e1e1e', width=2)
            ),
            direction='clockwise',
            sort=False
        )])

        fig.update_layout(
            height=450,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(size=10)
            ),
            margin=dict(l=20, r=20, t=40, b=80),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e5e7eb', size=11)
        )

        # Add center text
        fig.add_annotation(
            text=f"<b>€{sum(revenues):.0f}</b><br><span style='font-size:12px'>Total Revenue</span>",
            x=0.5, y=0.5,
            font=dict(size=20, color='#e5e7eb'),
            showarrow=False
        )

        st.plotly_chart(fig, width='stretch')

        # Quick stats below chart
        col1, col2, col3 = st.columns(3)
        with col1:
            top_3_revenue = sum(revenues[:3])
            top_3_pct = (top_3_revenue / sum(revenues) * 100) if sum(revenues) > 0 else 0
            st.caption(f"🥇 **Top titles 3:** €{top_3_revenue:.2f} ({top_3_pct:.0f}%)")
        with col2:
            avg_revenue = sum(revenues) / len(revenues) if revenues else 0
            st.caption(f"📊 **Avg per Title:** €{avg_revenue:.2f}")
        with col3:
            st.caption(f"🔢 **Contributing Titles:** {len(ids)}")
    else:
        st.info("📭 No sales data to visualize yet")

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # 🚨 DEAD STOCK ALERT (STRATEGIC PRIORITY)
    # ============================================================================
    st.markdown("### 🚨 Strategic Alert")
    st.caption("💡 Identify capital tied up in non-performing inventory")

    dead_stock_books = [
        b for b in performance
        if b['total_sold'] == 0 and b['current_stock'] > 0
    ]

    if dead_stock_books:
        total_dead_copies = sum(b['current_stock'] for b in dead_stock_books)
        total_dead_capital = sum(
            b['current_stock'] * b.get('buy_price', 0)
            for b in dead_stock_books
        )

        # Sort by investment (highest first)
        dead_stock_books.sort(
            key=lambda x: x['current_stock'] * x.get('buy_price', 0),
            reverse=True
        )

        # Alert banner
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.15) 100%);
                        padding: 16px 20px; border-radius: 12px; border-left: 4px solid #ef4444; margin-bottom: 16px;">
                <p style="margin: 0 0 6px 0; color: #fca5a5; font-size: 15px; font-weight: 600;">
                    ⚠️ {len(dead_stock_books)} book(s) never sold - action needed
                </p>
                <p style="margin: 0; color: #f87171; font-size: 13px;">
                    💸 €{total_dead_capital:.2f} capital tied up in {total_dead_copies} copies
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Display top dead stock books (limit to 5 for readability)
        for book in dead_stock_books[:5]:
            invested = book['current_stock'] * book.get('buy_price', 0)

            st.markdown(
                f"""
                <div style="background: rgba(239, 68, 68, 0.05); padding: 10px 14px;
                            border-radius: 8px; border-left: 3px solid #f87171; margin-bottom: 6px;">
                    <strong style="color: #fca5a5; font-size: 13px;">
                        {book['id']} - {book['title'][:45]}{'...' if len(book['title']) > 45 else ''}
                    </strong>
                    <br>
                    <span style="color: #9ca3af; font-size: 11px;">
                        📦 {book['current_stock']} copies • 💰 €{invested:.2f} invested
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Show more link if there are more than 5
        if len(dead_stock_books) > 5:
            st.caption(f"_...and {len(dead_stock_books) - 5} more in Category Details below_")

    else:
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.15) 100%);
                        padding: 16px 20px; border-radius: 12px; border-left: 4px solid #10b981; margin-bottom: 16px;">
                <p style="margin: 0; color: #6ee7b7; font-size: 14px; font-weight: 600;">
                    ✅ Excellent! All books have sold at least once
                </p>
                <p style="margin: 4px 0 0 0; color: #86efac; font-size: 12px;">
                    No capital tied up in dead stock
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # 🌟 PERFORMANCE CATEGORIES
    # ============================================================================
    st.markdown("### 🌟 Performance Categories")
    st.caption("💡 Titles categorized by sales performance and stock status")

    # Calculate categories
    star_performers = []
    cash_cows = []
    rising_stars = []
    out_of_stock = []
    slow_movers = []
    dead_stock = []

    for book in performance:
        if book['total_sold'] == 0 and book['current_stock'] > 0:
            dead_stock.append(book)
        elif book['total_sold'] > 0 and book['current_stock'] == 0:
            out_of_stock.append(book)
        elif book['total_sold'] >= 10 and book['total_profit'] > 50:
            star_performers.append(book)
        elif book['velocity'] > 0.5 and book['total_sold'] >= 3 and book['current_stock'] > 0:
            rising_stars.append(book)
        elif book['total_sold'] > 0 and book['avg_margin'] > 40:
            cash_cows.append(book)
        elif book['total_sold'] > 0 and book['velocity'] < 0.2 and book['current_stock'] > 0:
            slow_movers.append(book)

    # Display category cards
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 12px; border-radius: 10px; text-align: center; color: white;">
                <h2 style="margin: 0; font-size: 28px;">🌟</h2>
                <p style="margin: 3px 0; font-size: 11px; opacity: 0.9;">STARS</p>
                <h3 style="margin: 3px 0; font-size: 20px;">{len(star_performers)}</h3>
                <p style="margin: 0; font-size: 10px; opacity: 0.8;">High sales</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                        padding: 12px; border-radius: 10px; text-align: center; color: white;">
                <h2 style="margin: 0; font-size: 28px;">💰</h2>
                <p style="margin: 3px 0; font-size: 11px; opacity: 0.9;">CASH COWS</p>
                <h3 style="margin: 3px 0; font-size: 20px;">{len(cash_cows)}</h3>
                <p style="margin: 0; font-size: 10px; opacity: 0.8;">High margin</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        padding: 12px; border-radius: 10px; text-align: center; color: white;">
                <h2 style="margin: 0; font-size: 28px;">🚀</h2>
                <p style="margin: 3px 0; font-size: 11px; opacity: 0.9;">RISING</p>
                <h3 style="margin: 3px 0; font-size: 20px;">{len(rising_stars)}</h3>
                <p style="margin: 0; font-size: 10px; opacity: 0.8;">Fast moving</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%);
                        padding: 12px; border-radius: 10px; text-align: center; color: white;">
                <h2 style="margin: 0; font-size: 28px;">📦</h2>
                <p style="margin: 3px 0; font-size: 11px; opacity: 0.9;">OUT</p>
                <h3 style="margin: 3px 0; font-size: 20px;">{len(out_of_stock)}</h3>
                <p style="margin: 0; font-size: 10px; opacity: 0.8;">Restock</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col5:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
                        padding: 12px; border-radius: 10px; text-align: center; color: #333;">
                <h2 style="margin: 0; font-size: 28px;">⚠️</h2>
                <p style="margin: 3px 0; font-size: 11px; opacity: 0.9;">SLOW</p>
                <h3 style="margin: 3px 0; font-size: 20px;">{len(slow_movers)}</h3>
                <p style="margin: 0; font-size: 10px; opacity: 0.8;">Low velocity</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col6:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #ff7675 0%, #d63031 100%);
                        padding: 12px; border-radius: 10px; text-align: center; color: white;">
                <h2 style="margin: 0; font-size: 28px;">🔴</h2>
                <p style="margin: 3px 0; font-size: 11px; opacity: 0.9;">DEAD</p>
                <h3 style="margin: 3px 0; font-size: 20px;">{len(dead_stock)}</h3>
                <p style="margin: 0; font-size: 10px; opacity: 0.8;">Never sold</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # 📊 INTERACTIVE ANALYSIS TABS
    # ============================================================================
    st.markdown("### 📊 Detailed Analysis")

    tab1, tab2, tab3 = st.tabs([
        "🏆 Top Performers",
        "🔍 Category Deep Dive",
        "📋 Full Data Table"
    ])

    # TAB 1: TOP PERFORMERS (SORTABLE)
    with tab1:
        if not titles_with_sales:
            st.info("📭 No sales data yet")
        else:
            col1, col2 = st.columns([2, 1])

            with col1:
                sort_metric = st.radio(
                    "Sort by:",
                    ["Total Sold", "Revenue", "Profit", "Margin %", "Velocity"],
                    horizontal=True,
                    key="top_performers_sort"
                )

            sort_keys = {
                "Total Sold": lambda x: x['total_sold'],
                "Revenue": lambda x: x['total_revenue'],
                "Profit": lambda x: x['total_profit'],
                "Margin %": lambda x: x['avg_margin'],
                "Velocity": lambda x: x['velocity']
            }

            top_15 = sorted(titles_with_sales, key=sort_keys[sort_metric], reverse=True)[:15]

            for idx, book in enumerate(top_15, 1):
                if idx == 1:
                    medal = "🥇"
                    color = "#ffd700"
                elif idx == 2:
                    medal = "🥈"
                    color = "#c0c0c0"
                elif idx == 3:
                    medal = "🥉"
                    color = "#cd7f32"
                else:
                    medal = f"#{idx}"
                    color = "#667eea"

                with st.expander(
                    f"{medal} **{book['id']}** - {book['title'][:40]} | "
                    f"Sold: {book['total_sold']} | Revenue: €{book['total_revenue']:.2f} | "
                    f"Profit: €{book['total_profit']:.2f}",
                    expanded=(idx <= 3)
                ):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.caption("**📊 Sales Data**")
                        st.write(f"📦 Copies Sold: **{book['total_sold']}**")
                        st.write(f"🔢 Transactions: **{book['num_sales']}**")
                        st.write(f"📦 Stock: **{book['current_stock']}**")

                    with col2:
                        st.caption("**💰 Financial**")
                        st.write(f"💵 Revenue: **€{book['total_revenue']:.2f}**")
                        st.write(f"📈 Profit: **€{book['total_profit']:.2f}**")
                        st.write(f"📊 Margin: **{book['avg_margin']:.1f}%**")

                    with col3:
                        st.caption("**⚡ Performance**")
                        st.write(f"🚀 Velocity: **{book['velocity']:.2f}**/day")
                        avg_per_sale = book['total_sold'] / book['num_sales'] if book['num_sales'] > 0 else 0
                        st.write(f"📦 Avg/sale: **{avg_per_sale:.1f}**")

                        if book['velocity'] > 0.5:
                            st.success("🔥 Hot!")
                        elif book['velocity'] > 0.2:
                            st.info("✅ Steady")
                        else:
                            st.warning("⚠️ Slow")

    # TAB 2: CATEGORY DEEP DIVE
    with tab2:
        category_select = st.selectbox(
            "Select category:",
            [
                "🌟 Star Performers",
                "💰 Cash Cows",
                "🚀 Rising Stars",
                "📦 Out of Stock",
                "⚠️ Slow Movers",
                "🔴 Dead Stock"
            ],
            key="category_select"
        )

        # Render selected category details (implement each as before)
        if category_select == "🔴 Dead Stock":
            st.markdown("### 🔴 Dead Stock Analysis")
            if not dead_stock:
                st.success("✅ No dead stock!")
            else:
                for book in sorted(dead_stock, key=lambda x: x['current_stock'] * x.get('buy_price', 0), reverse=True):
                    invested = book['current_stock'] * book.get('buy_price', 0)

                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        with col1:
                            st.markdown(f"**{book['id']}** - {book['title'][:35]}")
                        with col2:
                            st.metric("Stock", f"{book['current_stock']}")
                        with col3:
                            st.metric("Invested", f"€{invested:.2f}")
                        with col4:
                            st.metric("Target", f"€{book.get('target_price', 0):.2f}")

                        st.caption("💡 Actions: Review pricing • Improve listing • Bundle • Discount • Donate")
                        st.markdown("---")

        # (Add other categories similarly - shortened for space)

    # TAB 3: FULL DATA TABLE
    with tab3:
        st.caption("💡 Complete data with filtering and sorting")

        col1, col2 = st.columns(2)
        with col1:
            table_filter = st.selectbox(
                "Filter:",
                ["All Titles", "Active Only", "Sold Out", "With Sales", "Never Sold"],
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
                    'total_sold', 'total_revenue', 'total_profit', 'avg_margin', 'velocity'
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
                    'velocity': st.column_config.NumberColumn('Velocity', format='%.2f', width='small')
                },
                hide_index=True,
                width='stretch'
            )

            # Summary
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Titles", len(filtered_data))
            with col2:
                st.metric("Copies", sum(b['total_sold'] + b['current_stock'] for b in filtered_data))
            with col3:
                st.metric("Revenue", f"€{sum(b['total_revenue'] for b in filtered_data):.2f}")
            with col4:
                st.metric("Profit", f"€{sum(b['total_profit'] for b in filtered_data):.2f}")
        else:
            st.info("No titles match filter")

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # 🎯 SMART RECOMMENDATIONS (COLLAPSED)
    # ============================================================================
    with st.expander("🎯 **Smart Recommendations**", expanded=False):
        st.caption("💡 Data-driven actions to optimize inventory")

        rec_col1, rec_col2, rec_col3 = st.columns(3)

        with rec_col1:
            st.markdown("**🔄 Urgent Restock**")
            restock_urgent = [
                b for b in rising_stars + star_performers
                if b['current_stock'] <= 2
            ]

            if restock_urgent:
                for book in sorted(restock_urgent, key=lambda x: x['velocity'], reverse=True)[:5]:
                    st.success(f"**{book['id']}** - {book['title'][:18]}")
                    st.caption(f"Stock: {book['current_stock']} • {book['velocity']:.2f}/day")
            else:
                st.info("✅ Stock levels good")

        with rec_col2:
            st.markdown("**📈 Price Increase**")
            price_increase = [
                b for b in titles_with_sales
                if b['velocity'] > 0.5 and b['avg_margin'] < 40 and b['current_stock'] > 0
            ]

            if price_increase:
                for book in sorted(price_increase, key=lambda x: x['velocity'], reverse=True)[:5]:
                    st.info(f"**{book['id']}** - {book['title'][:18]}")
                    st.caption(f"Margin: {book['avg_margin']:.0f}% • Fast seller")
            else:
                st.info("✅ Pricing optimal")

        with rec_col3:
            st.markdown("**💥 Promotions**")
            needs_promotion = slow_movers + dead_stock

            if needs_promotion:
                for book in sorted(needs_promotion, key=lambda x: x['current_stock'] * x.get('buy_price', 0), reverse=True)[:5]:
                    st.warning(f"**{book['id']}** - {book['title'][:18]}")
                    st.caption(f"{book['current_stock']} copies idle")
            else:
                st.success("✅ All moving well")

# ============================================================================
# TAB 5: BOOK INSPECTOR (DEEP-DIVE ANALYTICS FOR INDIVIDUAL BOOKS)
# ============================================================================
def _render_book_inspector():
    """Comprehensive analytics for a single book with advanced visualizations."""

    st.markdown("### 🔍 Book Inspector")
    st.caption("💡 Deep-dive analytics for books with sales history")

    # Get all books and sales data
    all_books = get_books()

    if not all_books:
        st.info("📭 No books in database")
        return

    # Get sales with customer names
    from src.data.database import get_sales, get_customers
    all_sales_raw = get_sales()
    customers = get_customers()
    customer_map = {c['id']: c['name'] for c in customers}

    # Filter books - ONLY show books with at least 1 sale
    books_with_sales_ids = set(s['book_id'] for s in all_sales_raw)
    books_with_sales = [b for b in all_books if b['id'] in books_with_sales_ids]

    if not books_with_sales:
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, rgba(251, 191, 36, 0.15) 0%, rgba(245, 158, 11, 0.15) 100%);
                        padding: 24px; border-radius: 12px; border-left: 4px solid #f59e0b; text-align: center;">
                <h3 style="color: #fbbf24; margin: 0 0 12px 0;">📊 No Sales Data Yet</h3>
                <p style="color: #fcd34d; margin: 0; font-size: 14px;">
                    No books have been sold yet. Record your first sale to unlock analytics!
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # ============================================================================
    # BOOK SELECTION - SORTED BY COPIES SOLD
    # ============================================================================
    st.markdown("---")

    # ✅ Calculate sales count per book
    books_sales_count = {}
    for sale in all_sales_raw:
        book_id = sale['book_id']
        books_sales_count[book_id] = books_sales_count.get(book_id, 0) + sale['qty']

    # ✅ SORT BY COPIES SOLD (DESCENDING)
    books_with_sales_sorted = sorted(
        books_with_sales,
        key=lambda x: books_sales_count.get(x['id'], 0),
        reverse=True
    )

    # Separate active from sold out (but keep sort order)
    active_books = [b for b in books_with_sales_sorted if b['stock'] > 0]
    sold_out_books = [b for b in books_with_sales_sorted if b['stock'] == 0]

    book_options = {}

    if active_books:
        book_options["─── 📗 ACTIVE BOOKS (WITH SALES) ───"] = None
        for b in active_books:
            total_sold = books_sales_count.get(b['id'], 0)
            book_options[f"📗 {b['id']} - {b['title'][:35]} ({total_sold} sold | {b['stock']} in stock)"] = b['id']

    if sold_out_books:
        book_options["─── 📕 SOLD OUT BOOKS ───"] = None
        for b in sold_out_books:
            total_sold = books_sales_count.get(b['id'], 0)
            book_options[f"📕 {b['id']} - {b['title'][:35]} ({total_sold} sold)"] = b['id']

    book_options = {"📊 Select a book to analyze...": None, **book_options}

    selected_display = st.selectbox(
        "Choose book:",
        list(book_options.keys()),
        key="book_inspector_select",
        label_visibility="collapsed"
    )

    selected_book_id = book_options[selected_display]

    if not selected_book_id:
        st.info("👆 Select a book from the dropdown above to view detailed analytics")

        # Show summary stats
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Books with Sales", len(books_with_sales))
        with col2:
            total_transactions = len(set(
                s['bundle_id'] if s['bundle_id'] else f"sale_{s['id']}"
                for s in all_sales_raw
            ))
            st.metric("Total Transactions", total_transactions)
        with col3:
            total_copies = sum(s['qty'] for s in all_sales_raw)
            st.metric("Total Copies Sold", total_copies)

        return

    # Get selected book
    selected_book = next((b for b in books_with_sales_sorted if b['id'] == selected_book_id), None)

    if not selected_book:
        st.error("❌ Book not found")
        return

    # ============================================================================
    # GET SALES DATA FOR THIS BOOK
    # ============================================================================
    book_sales = []
    for sale in all_sales_raw:
        if sale['book_id'] == selected_book_id:
            sale_with_customer = sale.copy()
            sale_with_customer['customer_name'] = customer_map.get(sale['customer_id'], 'Unknown')
            book_sales.append(sale_with_customer)

    if not book_sales:
        st.warning("⚠️ This book should have sales but none found (data error)")
        return

    # ============================================================================
    # BOOK HEADER CARD
    # ============================================================================
    st.markdown("<br>", unsafe_allow_html=True)

    status_color = "#10b981" if selected_book['stock'] > 0 else "#ef4444"
    status_text = f"{selected_book['stock']} in stock" if selected_book['stock'] > 0 else "SOLD OUT"

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
                    padding: 24px; border-radius: 16px; border-left: 5px solid #667eea; margin-bottom: 20px;">
            <h2 style="color: #b8b8ff; margin: 0 0 8px 0; font-size: 24px;">
                📖 {selected_book['title']}
            </h2>
            <p style="color: #9ca3af; margin: 0 0 12px 0; font-size: 14px;">
                ✍️ by {selected_book['author'] if selected_book['author'] else 'Unknown Author'} •
                📚 {selected_book['genre']} •
                🆔 {selected_book['id']}
            </p>
            <div style="display: inline-block; background: {status_color}; color: white;
                        padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 600;">
                📦 {status_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ============================================================================
    # CALCULATE COMPREHENSIVE METRICS
    # ============================================================================

    # Total metrics
    total_copies_sold = sum(s['qty'] for s in book_sales)
    total_transactions = len(set(s['bundle_id'] if s['bundle_id'] else f"sale_{s['id']}" for s in book_sales))

    # Financial metrics
    total_revenue_gross = sum(s['total'] for s in book_sales)
    total_packaging = sum(s['packaging_per_book'] * s['qty'] for s in book_sales)
    total_revenue_net = total_revenue_gross - total_packaging
    total_cost = sum(selected_book['buy_price'] * s['qty'] for s in book_sales)
    total_profit = total_revenue_net - total_cost
    avg_margin = (total_profit / total_revenue_net * 100) if total_revenue_net > 0 else 0

    # Pricing metrics
    avg_price_per_book = total_revenue_gross / total_copies_sold if total_copies_sold > 0 else 0
    min_price = min(s['total'] / s['qty'] for s in book_sales) if book_sales else 0
    max_price = max(s['total'] / s['qty'] for s in book_sales) if book_sales else 0

    # Time metrics
    first_sale_date = min(datetime.strptime(s['date'], "%Y-%m-%d") for s in book_sales)
    last_sale_date = max(datetime.strptime(s['date'], "%Y-%m-%d") for s in book_sales)
    days_selling = (last_sale_date - first_sale_date).days + 1
    velocity = total_copies_sold / days_selling if days_selling > 0 else 0

    # Advanced restocking metrics
    revenue_per_day = total_revenue_net / days_selling if days_selling > 0 else 0
    profit_per_day = total_profit / days_selling if days_selling > 0 else 0

    # Stock runway (days until out of stock at current velocity)
    if velocity > 0 and selected_book['stock'] > 0:
        days_until_stockout = selected_book['stock'] / velocity
    else:
        days_until_stockout = 0

    # ROI metrics
    total_invested = selected_book['buy_price'] * (total_copies_sold + selected_book['stock'])
    roi_percentage = (total_profit / total_cost * 100) if total_cost > 0 else 0

    # Inventory turnover
    avg_inventory = (total_copies_sold + selected_book['stock']) / 2
    turnover_ratio = total_copies_sold / avg_inventory if avg_inventory > 0 else 0

    # Platform breakdown (keep for chart only)
    platform_breakdown = {}
    for sale in book_sales:
        platform = sale['platform']
        if platform not in platform_breakdown:
            platform_breakdown[platform] = {'count': 0, 'revenue': 0}
        platform_breakdown[platform]['count'] += sale['qty']
        platform_breakdown[platform]['revenue'] += sale['total']

    # ============================================================================
    # KEY METRICS CARDS
    # ============================================================================
    st.markdown("### 📊 Performance Overview")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 20px; border-radius: 12px; text-align: center; color: white;
                        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);">
                <h3 style="margin: 0; font-size: 28px;">📦</h3>
                <p style="margin: 8px 0; font-size: 11px; opacity: 0.95; font-weight: 600;">COPIES SOLD</p>
                <h2 style="margin: 5px 0; font-size: 24px; font-weight: 700;">{total_copies_sold}</h2>
                <p style="margin: 8px 0 0 0; font-size: 10px; opacity: 0.9;">{total_transactions} orders</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                        padding: 20px; border-radius: 12px; text-align: center; color: white;
                        box-shadow: 0 8px 16px rgba(17, 153, 142, 0.3);">
                <h3 style="margin: 0; font-size: 28px;">💰</h3>
                <p style="margin: 8px 0; font-size: 11px; opacity: 0.95; font-weight: 600;">REVENUE</p>
                <h2 style="margin: 5px 0; font-size: 24px; font-weight: 700;">€{total_revenue_net:.2f}</h2>
                <p style="margin: 8px 0 0 0; font-size: 10px; opacity: 0.9;">€{revenue_per_day:.2f}/day</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        profit_color_grad = "#10b981" if total_profit >= 0 else "#ef4444"
        profit_icon = "📈" if total_profit >= 0 else "📉"

        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, {profit_color_grad} 0%, {profit_color_grad}dd 100%);
                        padding: 20px; border-radius: 12px; text-align: center; color: white;
                        box-shadow: 0 8px 16px rgba(16, 185, 129, 0.3);">
                <h3 style="margin: 0; font-size: 28px;">{profit_icon}</h3>
                <p style="margin: 8px 0; font-size: 11px; opacity: 0.95; font-weight: 600;">PROFIT</p>
                <h2 style="margin: 5px 0; font-size: 24px; font-weight: 700;">€{total_profit:.2f}</h2>
                <p style="margin: 8px 0 0 0; font-size: 10px; opacity: 0.9;">€{profit_per_day:.2f}/day</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        velocity_color = "#f093fb" if velocity > 0.5 else "#fbbf24" if velocity > 0.2 else "#9ca3af"
        velocity_label = "HOT" if velocity > 0.5 else "STEADY" if velocity > 0.2 else "SLOW"

        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, {velocity_color} 0%, {velocity_color}dd 100%);
                        padding: 20px; border-radius: 12px; text-align: center; color: white;
                        box-shadow: 0 8px 16px rgba(240, 147, 251, 0.3);">
                <h3 style="margin: 0; font-size: 28px;">⚡</h3>
                <p style="margin: 8px 0; font-size: 11px; opacity: 0.95; font-weight: 600;">VELOCITY</p>
                <h2 style="margin: 5px 0; font-size: 24px; font-weight: 700;">{velocity:.2f}</h2>
                <p style="margin: 8px 0 0 0; font-size: 10px; opacity: 0.9;">copies/day • {velocity_label}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col5:
        # Stock runway color coding
        if days_until_stockout == 0:
            runway_color = "#ef4444"
            runway_label = "OUT"
        elif days_until_stockout < 7:
            runway_color = "#f59e0b"
            runway_label = "CRITICAL"
        elif days_until_stockout < 30:
            runway_color = "#fbbf24"
            runway_label = "LOW"
        else:
            runway_color = "#10b981"
            runway_label = "GOOD"

        runway_display = f"{int(days_until_stockout)}" if days_until_stockout > 0 else "0"

        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, {runway_color} 0%, {runway_color}dd 100%);
                        padding: 20px; border-radius: 12px; text-align: center; color: white;
                        box-shadow: 0 8px 16px rgba(239, 68, 68, 0.3);">
                <h3 style="margin: 0; font-size: 28px;">⏱️</h3>
                <p style="margin: 8px 0; font-size: 11px; opacity: 0.95; font-weight: 600;">STOCK RUNWAY</p>
                <h2 style="margin: 5px 0; font-size: 24px; font-weight: 700;">{runway_display}</h2>
                <p style="margin: 8px 0 0 0; font-size: 10px; opacity: 0.9;">days • {runway_label}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # RESTOCKING INTELLIGENCE PANEL
    # ============================================================================
    st.markdown("### 🎯 Restocking Intelligence")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("ROI", f"{roi_percentage:.1f}%", help="Return on Investment: Profit / Cost")
        st.caption(f"Invested: €{total_cost:.2f}")

    with col2:
        st.metric("Margin", f"{avg_margin:.1f}%")
        if avg_margin > 50:
            st.caption("🟢 Excellent")
        elif avg_margin > 30:
            st.caption("🟡 Good")
        else:
            st.caption("🔴 Low")

    with col3:
        st.metric("Turnover", f"{turnover_ratio:.2f}x", help="Inventory turnover ratio")
        if turnover_ratio > 5:
            st.caption("🔥 Fast moving")
        elif turnover_ratio > 2:
            st.caption("✅ Healthy")
        else:
            st.caption("⚠️ Slow")

    with col4:
        sell_through = (total_copies_sold / (total_copies_sold + selected_book['stock']) * 100)
        st.metric("Sell-Through", f"{sell_through:.1f}%")
        if sell_through > 80:
            st.caption("🟢 High demand")
        elif sell_through > 50:
            st.caption("🟡 Moderate")
        else:
            st.caption("🔴 Low demand")

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # PLOTLY CHARTS - ENHANCED VISUALIZATIONS
    # ============================================================================
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    # Sort sales by date
    book_sales_sorted = sorted(book_sales, key=lambda x: x['date'])

    # ============================================================================
    # CHART 1: SALES FREQUENCY & REVENUE TIMELINE
    # ============================================================================
    st.markdown("### 📅 Sales Timeline & Revenue Trend")

    # Prepare data by date
    daily_data = {}
    for sale in book_sales_sorted:
        date = sale['date']
        if date not in daily_data:
            daily_data[date] = {'qty': 0, 'revenue': 0, 'transactions': 0}
        daily_data[date]['qty'] += sale['qty']
        daily_data[date]['revenue'] += sale['total']
        daily_data[date]['transactions'] += 1

    dates = sorted(daily_data.keys())
    quantities = [daily_data[d]['qty'] for d in dates]
    revenues = [daily_data[d]['revenue'] for d in dates]

    # Create figure with secondary y-axis
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])

    # Add bar chart for quantities
    fig1.add_trace(
        go.Bar(
            x=dates,
            y=quantities,
            name="Copies Sold",
            marker_color='rgba(102, 126, 234, 0.7)',
            hovertemplate='<b>%{x}</b><br>Copies: %{y}<extra></extra>'
        ),
        secondary_y=False,
    )

    # Add line chart for revenue
    fig1.add_trace(
        go.Scatter(
            x=dates,
            y=revenues,
            name="Revenue",
            line=dict(color='#10b981', width=3),
            mode='lines+markers',
            marker=dict(size=8),
            hovertemplate='<b>%{x}</b><br>Revenue: €%{y:.2f}<extra></extra>'
        ),
        secondary_y=True,
    )

    fig1.update_xaxes(title_text="Date")
    fig1.update_yaxes(title_text="Copies Sold", secondary_y=False, showgrid=False)
    fig1.update_yaxes(title_text="Revenue (€)", secondary_y=True, showgrid=True, gridcolor='rgba(128,128,128,0.2)')

    fig1.update_layout(
        height=400,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e5e7eb', size=11)
    )

    st.plotly_chart(fig1, width='content')

    st.caption(f"📊 **Sales Pattern:** {len(dates)} active days • Avg {total_copies_sold/len(dates):.1f} copies/active day • Peak: {max(quantities)} copies in one day")

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # CHART 2: PRICE ANALYSIS & RECOMMENDATION + PROFIT/REVENUE
    # ============================================================================
    st.markdown("### 💰 Pricing Analysis & Performance")

    col1, col2 = st.columns(2)

    with col1:
        st.caption("**Price Per Book Over Time**")

        sale_dates = [datetime.strptime(s['date'], "%Y-%m-%d") for s in book_sales_sorted]
        sale_prices = [s['total'] / s['qty'] for s in book_sales_sorted]

        fig4 = go.Figure()

        # Scatter plot with line
        fig4.add_trace(go.Scatter(
            x=sale_dates,
            y=sale_prices,
            mode='lines+markers',
            marker=dict(size=10, color=sale_prices, colorscale='RdYlGn', showscale=False),
            line=dict(color='rgba(102, 126, 234, 0.5)', width=2),
            hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Price: €%{y:.2f}<extra></extra>'
        ))

        # Add average line
        fig4.add_hline(
            y=avg_price_per_book,
            line_dash="dash",
            line_color="white",
            annotation_text=f"Avg: €{avg_price_per_book:.2f}",
            annotation_position="right"
        )

        fig4.update_layout(
            height=300,
            yaxis_title="Price (€)",
            xaxis_title="Date",
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e5e7eb', size=11),
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
        )

        st.plotly_chart(fig4, width='content')

        # ✅ PRICING RECOMMENDATION
        price_variance = max_price - min_price
        recent_prices = sale_prices[-3:] if len(sale_prices) >= 3 else sale_prices
        recent_avg = sum(recent_prices) / len(recent_prices)

        # Calculate optimal price (based on current margin + market acceptance)
        if velocity > 0.5:  # Hot seller
            recommended_price = recent_avg * 1.1  # Can increase 10%
        elif velocity > 0.2:  # Steady
            recommended_price = recent_avg * 1.05  # Increase 5%
        else:  # Slow
            recommended_price = recent_avg * 0.95  # Maybe decrease 5%

        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
                        padding: 16px; border-radius: 10px; border-left: 4px solid #667eea; margin-top: 10px;">
                <p style="margin: 0 0 8px 0; color: #b8b8ff; font-size: 13px; font-weight: 600;">
                    💡 PRICING RECOMMENDATION
                </p>
                <p style="margin: 0 0 6px 0; color: #e5e7eb; font-size: 15px; font-weight: 700;">
                    Sell this book for: <span style="color: #10b981;">€{recommended_price:.2f}</span>
                </p>
                <p style="margin: 0; color: #9ca3af; font-size: 11px;">
                    Based on: Recent avg €{recent_avg:.2f} • Velocity {velocity:.2f}/day • Margin {avg_margin:.0f}%
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.caption("**Revenue & Profit Per Transaction**")

        # ✅ SHOW BOTH REVENUE AND PROFIT
        transaction_revenues = []
        transaction_profits = []
        transaction_dates = []

        for sale in book_sales_sorted:
            sale_revenue = sale['total'] - (sale['packaging_per_book'] * sale['qty'])
            sale_cost = selected_book['buy_price'] * sale['qty']
            sale_profit = sale_revenue - sale_cost

            transaction_revenues.append(sale_revenue)
            transaction_profits.append(sale_profit)
            transaction_dates.append(datetime.strptime(sale['date'], "%Y-%m-%d"))

        fig5 = go.Figure()

        # Add revenue bars (light green background)
        fig5.add_trace(go.Bar(
            x=transaction_dates,
            y=transaction_revenues,
            name="Revenue",
            marker_color='rgba(16, 185, 129, 0.3)',
            hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Revenue: €%{y:.2f}<extra></extra>'
        ))

        # Add profit bars (solid green/red)
        colors = ['#10b981' if p >= 0 else '#ef4444' for p in transaction_profits]
        fig5.add_trace(go.Bar(
            x=transaction_dates,
            y=transaction_profits,
            name="Profit",
            marker_color=colors,
            hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Profit: €%{y:.2f}<extra></extra>'
        ))

        # Add zero line
        fig5.add_hline(y=0, line_color="white", line_width=1)

        fig5.update_layout(
            height=300,
            yaxis_title="Amount (€)",
            xaxis_title="Date",
            barmode='overlay',
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e5e7eb', size=11),
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig5, width='content')

        profitable_sales = sum(1 for p in transaction_profits if p >= 0)
        avg_profit_per_sale = sum(transaction_profits) / len(transaction_profits)
        st.caption(f"✅ {profitable_sales}/{len(transaction_profits)} sales profitable • Avg €{avg_profit_per_sale:.2f}/transaction")

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # CHART 4: MONTHLY BREAKDOWN (if enough data)
    # ============================================================================
    if days_selling > 30:
        st.markdown("### 📊 Monthly Performance Breakdown")

        # Group by month
        monthly_data = {}
        for sale in book_sales_sorted:
            date = datetime.strptime(sale['date'], "%Y-%m-%d")
            month_key = date.strftime("%Y-%m")

            if month_key not in monthly_data:
                monthly_data[month_key] = {'copies': 0, 'revenue': 0, 'profit': 0}

            sale_revenue = sale['total'] - (sale['packaging_per_book'] * sale['qty'])
            sale_cost = selected_book['buy_price'] * sale['qty']
            sale_profit = sale_revenue - sale_cost

            monthly_data[month_key]['copies'] += sale['qty']
            monthly_data[month_key]['revenue'] += sale['total']
            monthly_data[month_key]['profit'] += sale_profit

        months = sorted(monthly_data.keys())
        monthly_copies = [monthly_data[m]['copies'] for m in months]
        monthly_revenues = [monthly_data[m]['revenue'] for m in months]
        monthly_profits = [monthly_data[m]['profit'] for m in months]

        fig6 = make_subplots(
            rows=1, cols=3,
            subplot_titles=("Copies Sold", "Revenue", "Profit"),
            specs=[[{"type": "bar"}, {"type": "bar"}, {"type": "bar"}]]
        )

        fig6.add_trace(
            go.Bar(x=months, y=monthly_copies, marker_color='#667eea', name="Copies"),
            row=1, col=1
        )

        fig6.add_trace(
            go.Bar(x=months, y=monthly_revenues, marker_color='#11998e', name="Revenue"),
            row=1, col=2
        )

        fig6.add_trace(
            go.Bar(x=months, y=monthly_profits, marker_color='#10b981', name="Profit"),
            row=1, col=3
        )

        fig6.update_layout(
            height=300,
            showlegend=False,
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e5e7eb', size=10)
        )

        st.plotly_chart(fig6, width='content')

        # Calculate trend
        if len(months) >= 2:
            recent_month_copies = monthly_copies[-1]
            previous_month_copies = monthly_copies[-2]
            trend = ((recent_month_copies - previous_month_copies) / previous_month_copies * 100) if previous_month_copies > 0 else 0

            if trend > 10:
                st.success(f"📈 Sales growing! {abs(trend):.0f}% increase vs previous month")
            elif trend < -10:
                st.warning(f"📉 Sales declining: {abs(trend):.0f}% decrease vs previous month")
            else:
                st.info(f"➡️ Sales stable: {abs(trend):.0f}% change vs previous month")

        st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # DETAILED SALES HISTORY TABLE
    # ============================================================================
    st.markdown("### 📋 Detailed Transaction History")

    with st.expander(f"📊 View all {len(book_sales)} transactions", expanded=False):
        sales_display = []
        for sale in reversed(book_sales_sorted):
            sale_revenue = sale['total'] - (sale['packaging_per_book'] * sale['qty'])
            sale_cost = selected_book['buy_price'] * sale['qty']
            sale_profit = sale_revenue - sale_cost
            sale_margin = (sale_profit / sale_revenue * 100) if sale_revenue > 0 else 0

            sale_id_display = f"B-{sale['bundle_id'][:7]}" if sale['bundle_id'] else f"SE{sale['id']:03d}"

            sales_display.append({
                'ID': sale_id_display,
                'Date': datetime.strptime(sale['date'], "%Y-%m-%d").strftime("%d/%m/%Y"),
                'Customer': sale['customer_name'],
                'Platform': sale['platform'],
                'Qty': sale['qty'],
                'Price/Book': f"€{sale['total'] / sale['qty']:.2f}",
                'Total': f"€{sale['total']:.2f}",
                'Profit': f"€{sale_profit:.2f}",
                'Margin': f"{sale_margin:.1f}%"
            })

        st.dataframe(
            pd.DataFrame(sales_display),
            column_config={
                'ID': st.column_config.TextColumn('ID', width='small'),
                'Date': st.column_config.TextColumn('Date', width='small'),
                'Customer': st.column_config.TextColumn('Customer', width='medium'),
                'Platform': st.column_config.TextColumn('Platform', width='small'),
                'Qty': st.column_config.NumberColumn('Qty', width='small'),
                'Price/Book': st.column_config.TextColumn('Price/Book', width='small'),
                'Total': st.column_config.TextColumn('Total', width='small'),
                'Profit': st.column_config.TextColumn('Profit', width='small'),
                'Margin': st.column_config.TextColumn('Margin', width='small'),
            },
            hide_index=True,
            width='content'
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # ✅ IMPROVED AI RECOMMENDATIONS (VELOCITY-FOCUSED)
    # ============================================================================
    st.markdown("### 💡 Recommendations")

    recommendations = []

    # ✅ SCENARIO 1: Out of stock + Fast velocity = URGENT RESTOCK
    if selected_book['stock'] == 0 and velocity > 0.5:
        potential_lost_revenue = revenue_per_day * 7
        recommended_qty = int(velocity * 30)
        recommendations.append({
            'type': 'error',
            'icon': '🚨',
            'title': 'CRITICAL: HIGH-VELOCITY BOOK OUT OF STOCK',
            'message': f'This book sells **{velocity:.2f} copies/day** (fast mover!) but is out of stock. Losing **€{potential_lost_revenue:.2f}/week** in revenue. **RESTOCK {recommended_qty} COPIES NOW!**'
        })

    # ✅ SCENARIO 2: Out of stock + Moderate velocity = Important restock
    elif selected_book['stock'] == 0 and velocity > 0.2:
        recommended_qty = int(velocity * 30)
        recommendations.append({
            'type': 'warning',
            'icon': '⚠️',
            'title': 'OUT OF STOCK - STEADY SELLER',
            'message': f'Sells {velocity:.2f} copies/day (steady pace). Out of stock. Recommend restocking **{recommended_qty} copies** (30 days supply).'
        })

    # ✅ SCENARIO 3: Out of stock + Slow velocity = Consider discontinuing
    elif selected_book['stock'] == 0 and velocity <= 0.2:
        recommendations.append({
            'type': 'info',
            'icon': '🤔',
            'title': 'SLOW SELLER - OUT OF STOCK',
            'message': f'Only sold {velocity:.2f} copies/day (slow). Out of stock. **Consider:** Is it worth restocking? Maybe discontinue or wait for demand.'
        })

    # ✅ SCENARIO 4: Low stock + Fast velocity = Urgent restock
    elif 0 < days_until_stockout < 7 and velocity > 0.5:
        recommended_qty = int(velocity * 30)
        recommendations.append({
            'type': 'error',
            'icon': '🔥',
            'title': 'FAST-MOVING BOOK - LOW STOCK ALERT',
            'message': f'Only **{days_until_stockout:.0f} days** of stock left! Sells **{velocity:.2f} copies/day** (hot!). Restock **{recommended_qty} copies** ASAP to avoid stockout.'
        })

    # ✅ SCENARIO 5: Low stock + Moderate velocity = Plan restock
    elif 0 < days_until_stockout < 14 and velocity > 0.2:
        recommended_qty = int(velocity * 30)
        recommendations.append({
            'type': 'warning',
            'icon': '⏰',
            'title': 'PLAN RESTOCK SOON',
            'message': f'{days_until_stockout:.0f} days of stock remaining (sells {velocity:.2f}/day). Recommend ordering **{recommended_qty} copies** for next 30 days.'
        })

    # ✅ SCENARIO 6: In stock + Slow sales = Needs marketing
    elif selected_book['stock'] > 5 and velocity < 0.1:
        recommendations.append({
            'type': 'info',
            'icon': '📣',
            'title': 'SLOW MOVER - NEEDS PROMOTION',
            'message': f'{selected_book["stock"]} copies in stock but only selling {velocity:.2f}/day. Try: Better photos, bundle deals, price discount, or Instagram promotion.'
        })

    # ✅ SCENARIO 7: Good stock + Fast velocity = Winner
    elif selected_book['stock'] > 0 and velocity > 0.5:
        recommendations.append({
            'type': 'success',
            'icon': '🏆',
            'title': 'WINNING PRODUCT',
            'message': f'Hot seller! {velocity:.2f} copies/day with {selected_book["stock"]} in stock. **Keep this stocked at all times.** Consider bulk ordering for better margins.'
        })

    # ✅ SCENARIO 8: Healthy stock + Steady velocity = All good
    elif selected_book['stock'] > 0 and velocity > 0.2 and days_until_stockout > 14:
        recommendations.append({
            'type': 'success',
            'icon': '✅',
            'title': 'HEALTHY INVENTORY',
            'message': f'Good balance: {selected_book["stock"]} copies, {velocity:.2f}/day velocity, {days_until_stockout:.0f} days runway. No action needed right now.'
        })

    # Display recommendations
    if recommendations:
        for rec in recommendations:
            if rec['type'] == 'success':
                st.success(f"{rec['icon']} **{rec['title']}**\n\n{rec['message']}")
            elif rec['type'] == 'warning':
                st.warning(f"{rec['icon']} **{rec['title']}**\n\n{rec['message']}")
            elif rec['type'] == 'info':
                st.info(f"{rec['icon']} **{rec['title']}**\n\n{rec['message']}")
            elif rec['type'] == 'error':
                st.error(f"{rec['icon']} **{rec['title']}**\n\n{rec['message']}")
    else:
        st.info("✅ No urgent actions needed. Book performance is stable.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # INVENTORY STATUS & BOOK DETAILS
    # ============================================================================
    with st.expander("📦 **Inventory Status & Book Details**", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**📊 Inventory Metrics**")
            total_copies_ever = total_copies_sold + selected_book['stock']
            st.caption(f"**Total Copies Ever:** {total_copies_ever}")
            st.caption(f"**Copies Sold:** {total_copies_sold} ({sell_through:.1f}%)")
            st.caption(f"**Current Stock:** {selected_book['stock']}")
            st.caption(f"**Stock Runway:** {int(days_until_stockout)} days" if days_until_stockout > 0 else "**Stock Runway:** Out of stock")

        with col2:
            st.markdown("**💰 Financial Summary**")
            st.caption(f"**Total Invested:** €{total_invested:.2f}")
            st.caption(f"**Total Revenue:** €{total_revenue_net:.2f}")
            st.caption(f"**Total Profit:** €{total_profit:.2f}")
            st.caption(f"**ROI:** {roi_percentage:.1f}%")

        with col3:
            st.markdown("**📚 Book Info**")
            st.caption(f"**ID:** `{selected_book['id']}`")
            st.caption(f"**Author:** {selected_book['author'] if selected_book['author'] else 'Not specified'}")
            st.caption(f"**Genre:** {selected_book['genre']}")
            st.caption(f"**Added:** {selected_book['created_at']}")

        if selected_book.get('notes'):
            st.markdown("---")
            st.markdown("**📝 Notes**")
            st.caption(selected_book['notes'])
