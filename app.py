"""
Midad Books - Enhanced Analytics & UX
📚 كتب مداد
"""

import time
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from typing import Optional

from src.database import (
    Genre,
    Platform,
    add_sale,
    delete_sale,
    get_books,
    get_sales,
    get_stats,
    init_db,
    save_books_bulk,
)

# Config
st.set_page_config(
    page_title="Midad Books",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Init database
init_db()

# Session state for forcing refresh
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


def show_warning_toast(message: str):
    """Show warning notification."""
    st.toast(f"⚠️ {message}", icon="⚠️")


def get_low_stock_books(threshold: int = 3) -> list[dict]:
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
            sale_date = datetime.strptime(s["date"], "%Y-%m-%d %H:%M")
            if sale_date >= cutoff:
                recent.append(s)
        except:
            continue
    
    return recent


def calculate_profit_for_sale(sale: dict, books: list[dict]) -> float:
    """Calculate profit for a single sale."""
    book = next((b for b in books if b["id"] == sale["book_id"]), None)
    if not book:
        return 0
    
    revenue = sale["total"] - (sale["packaging_per_book"] * sale["qty"])
    cost = book["buy_price"] * sale["qty"]
    return revenue - cost


# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    st.title("📚 Midad Books")
    st.caption("كتب مداد")
    st.divider()
    
    page = st.radio(
        "Navigate",
        ["📚 Inventory", "💰 Sales", "📊 Analytics"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # Quick stats
    stats = get_stats()
    
    # Stats cards with better visuals
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📚 Active", stats["active_count"])
        st.metric("💰 Revenue", f"€{stats['revenue']:.0f}")
    with col2:
        st.metric("✅ Sold", stats["sold_count"])
        st.metric("📈 Profit", f"€{stats['profit']:.0f}")
    
    st.caption(f"📦 Stock: {stats['total_stock']} books")
    
    # Low stock warnings
    low_stock = get_low_stock_books(threshold=2)
    if low_stock:
        st.divider()
        st.warning(f"⚠️ {len(low_stock)} book(s) low stock!")
        with st.expander("View Low Stock"):
            for book in low_stock[:3]:
                st.caption(f"📕 {book['title'][:20]} - Stock: {book['stock']}")
    
    # Recent activity
    recent_sales = get_sales_by_date_range(7)
    if recent_sales:
        st.divider()
        st.success(f"🔥 {len(recent_sales)} sales this week!")
    
    # Debug mode
    st.divider()
    if st.checkbox("🐛 Debug Mode"):
        st.caption("**📊 Status Breakdown:**")
        all_books_debug = get_books()
        for b in all_books_debug[:10]:
            status_icon = "🟢" if b["status"] == "Active" else "🔴"
            st.caption(f"{status_icon} {b['title'][:20]} | Stock: {b['stock']}")


# ============================================================================
# INVENTORY PAGE
# ============================================================================
if page == "📚 Inventory":
    st.header("📚 Inventory Management")
    
    # Quick actions row
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.caption("💡 Stock = 0 → automatically moves to 'Sold' tab")
    with col2:
        st.metric("Total Stock", stats["total_stock"], label_visibility="collapsed")
    with col3:
        st.metric("Stock Value", f"€{stats['stock_value']:.0f}", label_visibility="collapsed")
    
    st.divider()
    
    # Filter tabs
    tab1, tab2, tab3 = st.tabs([
        f"🟢 Active ({stats['active_count']})", 
        f"🔴 Sold ({stats['sold_count']})", 
        "📋 All"
    ])
    
    def render_inventory(status_filter: Optional[str], tab_key: str):
        """Render inventory table with edit capability."""
        
        books = get_books(status_filter)

        if not books:
            st.info(f"No books found" + (f" with filter '{status_filter}'" if status_filter else ""))
            
            if status_filter == "active":
                st.info("💡 Add a new book by clicking '+ Add row' below")
                st.caption("📝 Fill in: Title (required), Author, Buy Price, Target Price, Stock")
            elif status_filter == "sold":
                st.caption("📦 Books appear here when stock reaches 0")
                st.caption("💡 To restock: Go to 'All Books' tab and increase stock")
            
            df = pd.DataFrame(columns=[
                "id", "title", "author", "genre", "buy_price", 
                "target_price", "stock", "status", "notes"
            ])
        else:
            # Add visual indicators
            for book in books:
                if book["stock"] > 0 and book["stock"] <= 2:
                    book["_alert"] = "⚠️"
                elif book["stock"] > 2:
                    book["_alert"] = "✅"
                else:
                    book["_alert"] = "🔴"
            
            st.success(f"📊 Showing {len(books)} book(s)")
            df = pd.DataFrame(books)
        
        # Data editor
        edited = st.data_editor(
            df,
            num_rows="dynamic",
            hide_index=True,
            key=f"editor_{tab_key}_{st.session_state.refresh_key}",
            column_config={
                "id": st.column_config.NumberColumn("🆔 ID", disabled=True, width="small"),
                "title": st.column_config.TextColumn("📖 Title", width="large", required=True, help="Book title (required)"),
                "author": st.column_config.TextColumn("✍️ Author", width="medium", help="Author name"),
                "genre": st.column_config.SelectboxColumn("📂 Genre", options=[g.value for g in Genre], width="small"),
                "buy_price": st.column_config.NumberColumn("💵 Buy €", format="%.2f", min_value=0, width="small", help="What YOU paid"),
                "target_price": st.column_config.NumberColumn("🎯 Target €", format="%.2f", min_value=0, width="small", help="Your goal selling price"),
                "stock": st.column_config.NumberColumn("📦 Stock", min_value=0, step=1, width="small", help="Quantity available"),
                "status": st.column_config.TextColumn("📊 Status", width="small", disabled=True, help="Auto-computed from stock"),
                "notes": st.column_config.TextColumn("📝 Notes", width="medium", help="Any additional notes"),
                "created_at": None,
                "_alert": None,
            },
            column_order=["id", "title", "author", "genre", "buy_price", "target_price", "stock", "status", "notes"],
            width=1400,
        )

        # Action buttons
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("💾 Save Changes", type="primary", key=f"save_{tab_key}", use_container_width=True):
                with st.spinner("Saving changes..."):
                    success, msg = save_books_bulk(edited.to_dict('records'), status_filter)
                    if success:
                        show_success_toast("Changes saved successfully!")
                        st.success("✅ All changes saved to database")
                        st.session_state.refresh_key += 1
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        show_error_toast(f"Save failed: {msg}")
                        st.error(f"❌ {msg}")
        
        with col2:
            if st.button("🔄 Refresh", key=f"refresh_{tab_key}", use_container_width=True):
                show_success_toast("Data refreshed!")
                st.session_state.refresh_key += 1
                st.rerun()
        
        # Help text
        if books:
            st.caption("💡 Tip: Edit cells directly, add rows with '+', delete rows with '🗑️', then click Save")

    with tab1:
        st.caption("📦 Books currently in stock and available to sell")
        render_inventory("active", "active")
    
    with tab2:
        st.caption("🔴 Books that are completely sold out (stock = 0)")
        render_inventory("sold", "sold")
    
    with tab3:
        st.caption("📋 All books in your inventory regardless of status")
        render_inventory(None, "all")


# ============================================================================
# SALES PAGE (WITH REAL-TIME SUMMARY + DATE PICKER)
# ============================================================================
elif page == "💰 Sales":
    st.header("💰 Record New Sale")
    
    active_books = get_books("active")
    available_books = [b for b in active_books if b["stock"] > 0]
    
    if not available_books:
        st.warning("⚠️ No books available for sale!")
        st.info("👉 Go to **Inventory** tab to add books or restock")
        st.caption("💡 Tip: Add books in the Active Books tab, then come back here to sell them")
    else:
        col1, col2 = st.columns([1, 2])
        
        # LEFT: Sale form with REAL-TIME summary
        with col1:
            st.subheader("📝 Sale Details")
            
            # Book selector (OUTSIDE form for reactivity)
            book_options = {f"{b['title']}": b for b in available_books}
            
            selected_title = st.selectbox(
                "📖 Select Book", 
                list(book_options.keys()),
                help="Only books with stock > 0 appear here",
                key="book_selector"
            )
            selected_book = book_options[selected_title]
            
            # Visual stock indicator
            if selected_book['stock'] > 3:
                stock_color = "🟢"
                stock_msg = "Good stock"
            elif selected_book['stock'] > 1:
                stock_color = "🟡"
                stock_msg = "Low stock"
            else:
                stock_color = "🔴"
                stock_msg = "Last one!"
            
            # Book info card
            target_info = f"🎯 Target: €{selected_book['target_price']:.2f}" if selected_book['target_price'] > 0 else "🎯 No target set"
            st.info(
                f"{stock_color} **Stock: {selected_book['stock']} available** ({stock_msg})\n\n"
                f"💵 You paid: €{selected_book['buy_price']:.2f}\n\n"
                f"{target_info}"
            )
            
            st.divider()
            
            # DATE PICKER (NEW!)
            col_date, col_time = st.columns([2, 1])
            with col_date:
                sale_date = st.date_input(
                    "📅 Sale Date",
                    value=datetime.now(),
                    help="When did this sale happen?",
                    key="sale_date_input"
                )
            with col_time:
                sale_time = st.time_input(
                    "🕐 Time",
                    value=datetime.now().time(),
                    help="Time of sale",
                    key="sale_time_input"
                )
            
            # Combine date and time
            sale_datetime_str = f"{sale_date.strftime('%Y-%m-%d')} {sale_time.strftime('%H:%M')}"
            st.caption(f"📅 Will be recorded as: {sale_datetime_str}")
            
            st.divider()
            
            # Platform (OUTSIDE form)
            platform = st.selectbox(
                "🛒 Platform", 
                [p.value for p in Platform],
                help="Where are you selling this book?",
                key="platform_selector"
            )
            
            # Quantity (OUTSIDE form for real-time update)
            qty = st.number_input(
                "📦 Quantity", 
                min_value=1, 
                max_value=selected_book["stock"], 
                value=1,
                help=f"How many to sell (max: {selected_book['stock']})",
                key="qty_input"
            )
            
            # Suggest total based on target or buy price
            suggested_total = qty * (selected_book["target_price"] if selected_book["target_price"] > 0 else selected_book["buy_price"] * 1.5)
            
            # Total paid (OUTSIDE form for real-time update)
            total_paid = st.number_input(
                "💰 Total Customer Paid (€)", 
                min_value=0.0, 
                value=float(suggested_total),
                step=0.50,
                help="Total amount customer paid for all books",
                key="total_paid_input"
            )
            
            # Packaging (OUTSIDE form for real-time update)
            packaging_per_book = st.number_input(
                "📦 Packaging per Book (€)", 
                min_value=0.0, 
                value=1.0,
                step=0.10,
                help="Cost of packaging materials per book",
                key="packaging_input"
            )
            
            # Customer name (OUTSIDE form)
            customer = st.text_input(
                "👤 Customer Name",
                placeholder="e.g., Ahmed M.",
                help="Customer's name for records",
                key="customer_input"
            )
            
            # ✨ REAL-TIME CALCULATION (updates as you type!)
            price_per_book = total_paid / qty if qty > 0 else 0
            total_packaging = packaging_per_book * qty
            revenue = total_paid - total_packaging
            cost = selected_book["buy_price"] * qty
            profit = revenue - cost
            profit_margin = (profit / revenue * 100) if revenue > 0 else 0
            
            st.divider()
            
            # REAL-TIME SUMMARY (updates instantly!)
            st.markdown("### 📊 Live Summary")
            st.caption("💡 Updates as you change values above")
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("💰 Total", f"€{total_paid:.2f}")
                st.caption(f"📖 Per book: €{price_per_book:.2f}")
                st.caption(f"📦 Packaging: €{total_packaging:.2f}")
            with col_b:
                st.metric("💵 Revenue", f"€{revenue:.2f}")
                st.caption(f"💸 Cost: €{cost:.2f}")
            
            # Profit display with colors and warnings
            if profit >= 0:
                st.success(f"### 💚 Profit: €{profit:.2f}")
                st.caption(f"📊 Margin: {profit_margin:.1f}%")
                
                if profit_margin > 50:
                    st.info("🎉 Great deal! Over 50% margin")
                elif profit_margin < 10:
                    st.warning("⚠️ Low margin (under 10%)")
            else:
                st.error(f"### 💔 Loss: €{abs(profit):.2f}")
                st.warning("⚠️ Warning: You're selling below cost!")
                st.caption(f"💡 You need at least €{cost + total_packaging:.2f} to break even")
            
            st.divider()
            
            # Submit button (NOW with validation)
            if st.button("✅ Record Sale", type="primary", use_container_width=True, key="submit_sale"):
                # Validation
                if not customer.strip():
                    show_error_toast("Please enter customer name")
                    st.error("❌ Customer name is required!")
                elif total_paid <= 0:
                    show_error_toast("Total must be greater than 0")
                    st.error("❌ Total paid must be greater than €0!")
                else:
                    # Confirmation for losses
                    if profit < 0:
                        st.warning(f"⚠️ Recording a LOSS of €{abs(profit):.2f}")
                        st.caption("The sale will be recorded anyway")
                    
                    with st.spinner("Recording sale..."):
                        success, msg = add_sale(
                            selected_book["id"], qty, total_paid, 
                            packaging_per_book, customer, platform,
                            sale_datetime_str  # Pass custom date
                        )
                        
                        if success:
                            # Show detailed success message
                            show_success_toast(f"Sale recorded! Profit: €{profit:.2f}")
                            st.success(f"✅ {msg}")
                            st.caption(f"📅 Recorded for: {sale_datetime_str}")
                            st.balloons()
                            
                            # Check for milestones
                            all_sales = get_sales()
                            if len(all_sales) % 10 == 0:  # Every 10 sales
                                st.toast(f"🎉 Milestone: {len(all_sales)} sales!", icon="🎉")
                            
                            # Check if last item
                            if selected_book["stock"] - qty == 0:
                                st.info(f"📦 '{selected_book['title']}' is now sold out and moved to Sold tab!")
                            
                            st.session_state.refresh_key += 1
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            show_error_toast(msg)
                            st.error(f"❌ {msg}")
        
        # RIGHT: Recent sales with better display
        with col2:
            st.subheader("📋 Recent Sales History")
            
            sales = get_sales()
            
            if sales:
                # Date filter with better labels
                date_filter = st.selectbox(
                    "📅 Show sales from:",
                    ["All Time", "Last 7 Days", "Last 30 Days", "Today"],
                    help="Filter sales by date range"
                )
                
                # Filter sales
                if date_filter == "Last 7 Days":
                    sales = get_sales_by_date_range(7)
                elif date_filter == "Last 30 Days":
                    sales = get_sales_by_date_range(30)
                elif date_filter == "Today":
                    today = datetime.now().strftime("%Y-%m-%d")
                    sales = [s for s in sales if s["date"].startswith(today)]
                
                if not sales:
                    st.info(f"No sales found for: {date_filter}")
                    st.caption("💡 Try selecting a different time range")
                else:
                    # Display sales with profit indicators and FULL DATE
                    sales_display = []
                    all_books = get_books()
                    
                    for s in sales[:20]:
                        profit = calculate_profit_for_sale(s, all_books)
                        profit_icon = "💚" if profit >= 0 else "💔"
                        
                        # Parse and format date nicely
                        try:
                            date_obj = datetime.strptime(s["date"], "%Y-%m-%d %H:%M")
                            date_display = date_obj.strftime("%d/%m/%Y %H:%M")
                        except:
                            date_display = s["date"]
                        
                        sales_display.append({
                            "ID": s["id"],
                            "📅 Date & Time": date_display,
                            "📖 Book": s["book_title"][:25] + "..." if len(s["book_title"]) > 25 else s["book_title"],
                            "🛒": s["platform"],
                            "Qty": s["qty"],
                            "💰 Total": f"€{s['total']:.2f}",
                            "📦": f"€{s['packaging_per_book']:.2f}",
                            f"{profit_icon} Profit": f"€{profit:.2f}",
                            "👤 Customer": s["customer"],
                        })
                    
                    # FIXED: Changed use_container_width to width='stretch'
                    st.dataframe(pd.DataFrame(sales_display), hide_index=True, width='stretch')
                    
                    # Summary stats
                    total_revenue = sum(s["total"] for s in sales)
                    total_items = sum(s["qty"] for s in sales)
                    total_profit = sum(calculate_profit_for_sale(s, all_books) for s in sales)
                    
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("💰 Revenue", f"€{total_revenue:.2f}")
                    with col_stat2:
                        st.metric("📦 Items", total_items)
                    with col_stat3:
                        profit_color = "normal" if total_profit >= 0 else "inverse"
                        st.metric("💚 Profit", f"€{total_profit:.2f}", delta_color=profit_color)
                    
                    st.caption(f"Showing {len(sales_display)} of {len(get_sales())} total sales")
                
                st.divider()
                
                # Delete sale with better UX
                with st.expander("🗑️ Undo Sale (Restore Stock)"):
                    st.warning("⚠️ This will:")
                    st.caption("• Delete the sale record permanently")
                    st.caption("• Restore the book's stock")
                    st.caption("• Update all statistics")
                    
                    sale_id = st.number_input(
                        "Enter Sale ID to delete", 
                        min_value=1, 
                        step=1,
                        help="Find the ID in the leftmost column above"
                    )
                    
                    col_del1, col_del2 = st.columns([1, 1])
                    with col_del1:
                        if st.button("🗑️ Delete & Restore", type="secondary", use_container_width=True):
                            with st.spinner("Deleting sale..."):
                                success, msg = delete_sale(sale_id)
                                if success:
                                    show_success_toast("Sale deleted successfully")
                                    st.success(msg)
                                    st.session_state.refresh_key += 1
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    show_error_toast(msg)
                                    st.error(msg)
                    with col_del2:
                        st.caption("⚠️ Cannot be undone!")
            else:
                st.info("🎉 No sales yet - make your first sale!")
                st.caption("💡 Select a book above, enter the details, and click 'Record Sale'")


# ============================================================================
# ANALYTICS PAGE (ENHANCED)
# ============================================================================
elif page == "📊 Analytics":
    st.header("📊 Business Analytics")
    
    stats = get_stats()
    
    # Date filter for analytics
    col_filter, col_refresh = st.columns([3, 1])
    with col_filter:
        time_range = st.selectbox(
            "Time Range",
            ["All Time", "Last 7 Days", "Last 30 Days"],
            help="Filter analytics by date range"
        )
    with col_refresh:
        if st.button("🔄 Refresh Data", use_container_width=True):
            show_success_toast("Analytics refreshed!")
            st.rerun()
    
    # Get filtered sales
    if time_range == "Last 7 Days":
        filtered_sales = get_sales_by_date_range(7)
    elif time_range == "Last 30 Days":
        filtered_sales = get_sales_by_date_range(30)
    else:
        filtered_sales = get_sales()
    
    # Calculate filtered stats
    filtered_revenue = sum(s["total"] for s in filtered_sales)
    filtered_items = sum(s["qty"] for s in filtered_sales)
    
    all_books = get_books()
    filtered_profit = sum(calculate_profit_for_sale(s, all_books) for s in filtered_sales)
    
    st.caption(f"📊 Showing data for: {time_range}")
    st.divider()
    
    # Top metrics row with better visuals
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Revenue", f"€{filtered_revenue:.2f}")
        st.caption(f"📦 Packaging: -€{stats['total_packaging']:.2f}")
    with col2:
        margin = (filtered_profit / filtered_revenue * 100) if filtered_revenue > 0 else 0
        profit_color = "normal" if filtered_profit >= 0 else "inverse"
        st.metric("📈 Profit", f"€{filtered_profit:.2f}", delta=f"{margin:.1f}%", delta_color=profit_color)
    with col3:
        st.metric("📦 Items Sold", filtered_items)
        avg_sale = filtered_revenue / filtered_items if filtered_items > 0 else 0
        st.caption(f"Avg: €{avg_sale:.2f}")
    with col4:
        sales_count = len(filtered_sales)
        st.metric("🧾 Transactions", sales_count)
    
    st.divider()
    
    # Inventory metrics
    st.subheader("📦 Inventory Status")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📚 Active Books", stats['active_count'])
    with col2:
        st.metric("🔴 Sold Out", stats['sold_count'])
    with col3:
        st.metric("🏦 Stock Value", f"€{stats['stock_value']:.2f}")
    with col4:
        if stats['potential_revenue'] > 0:
            potential_profit = stats['potential_revenue'] - stats['stock_value']
            st.metric("💎 Potential Profit", f"€{potential_profit:.2f}")
        else:
            st.metric("💎 Potential", "Set targets")
    
    st.divider()
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛒 Sales by Platform")
        if stats['platform_sales']:
            platform_df = pd.DataFrame([
                {"Platform": k, "Revenue (€)": v} 
                for k, v in sorted(stats['platform_sales'].items(), key=lambda x: x[1], reverse=True)
            ])
            st.bar_chart(platform_df.set_index("Platform"), height=300)
            st.caption("💡 Total sales grouped by selling platform")
        else:
            st.info("No sales data yet")
            st.caption("Make your first sale to see platform breakdown")
    
    with col2:
        st.subheader("📅 Sales Timeline")
        if filtered_sales:
            # Group by date
            sales_by_date = {}
            for s in filtered_sales:
                date = s["date"].split()[0]
                sales_by_date[date] = sales_by_date.get(date, 0) + s["total"]
            
            timeline_df = pd.DataFrame([
                {"Date": k, "Revenue (€)": v}
                for k, v in sorted(sales_by_date.items())
            ])
            st.line_chart(timeline_df.set_index("Date"), height=300)
            st.caption(f"💡 Revenue trend over {time_range.lower()}")
        else:
            st.info("No sales in this period")
            st.caption("Try selecting a different time range")
    
    st.divider()
    
    # Insights row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Best Sellers")
        if filtered_sales:
            # Count sales per book
            book_sales = {}
            for s in filtered_sales:
                title = s["book_title"]
                book_sales[title] = book_sales.get(title, 0) + s["qty"]
            
            top_sellers = sorted(book_sales.items(), key=lambda x: x[1], reverse=True)[:5]
            
            for i, (title, qty) in enumerate(top_sellers, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📖"
                st.write(f"{medal} **{title[:30]}** - {qty} sold")
            
            st.caption(f"💡 Top 5 books sold in {time_range.lower()}")
        else:
            st.info("No sales to analyze")
            st.caption("Make some sales to see best sellers")
    
    with col2:
        st.subheader("⚠️ Alerts & Insights")
        
        alerts_count = 0
        
        # Low stock alert
        low_stock = get_low_stock_books(threshold=2)
        if low_stock:
            alerts_count += 1
            st.warning(f"📉 **{len(low_stock)} books** have low stock")
            for book in low_stock[:3]:
                st.caption(f"  • {book['title'][:25]} - Only {book['stock']} left")
        
        # Negative margin books
        if stats['low_margin_books']:
            alerts_count += 1
            st.error(f"💔 **{len(stats['low_margin_books'])} books** have target below cost")
            for b in stats['low_margin_books'][:3]:
                loss = b['buy'] - b['target']
                st.caption(f"  • {b['title'][:25]} - Loss: €{loss:.2f}")
        
        # Positive feedback
        if alerts_count == 0:
            st.success("✅ All systems healthy!")
            st.caption("• Good stock levels")
            st.caption("• Healthy profit margins")
            st.caption("• No issues detected")