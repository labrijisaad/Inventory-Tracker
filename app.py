"""
Midad Books - Simple Inventory & Sales
📚 كتب مداد
"""

import time

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

# Sidebar navigation
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
    
    # Quick stats (always fresh)
    stats = get_stats()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📚 Active", stats["active_count"])
        st.metric("💰 Revenue", f"€{stats['revenue']:.0f}")
    with col2:
        st.metric("✅ Sold", stats["sold_count"])
        st.metric("📈 Profit", f"€{stats['profit']:.0f}")
    
    st.caption(f"📦 Total Stock: {stats['total_stock']}")

    # Debug mode
    if st.checkbox("🐛 Debug Mode"):
        st.caption("**📊 Status Breakdown:**")
        
        all_books_debug = get_books()
        for b in all_books_debug[:10]:  # Show first 10
            status_icon = "🟢" if b["status"] == "Active" else "🔴"
            st.caption(f"{status_icon} **{b['title'][:20]}** | Stock: {b['stock']} | Status: {b['status']}")


# ============================================================================
# INVENTORY PAGE
# ============================================================================
if page == "📚 Inventory":
    st.header("📚 Inventory Management")
    st.caption("💡 Stock = 0 → automatically moves to 'Sold' tab")
    
    # Filter tabs
    tab1, tab2, tab3 = st.tabs(["🟢 Active Books", "🔴 Sold Books", "📋 All Books"])
    
    def render_inventory(status_filter: Optional[str], tab_key: str):
        """Render inventory table with edit capability."""
        
        # Always fetch fresh data
        books = get_books(status_filter)

        if not books:
            st.info(
                f"No books found" + 
                (f" with filter '{status_filter}'" if status_filter else "")
            )
            
            # Show hint in Active tab
            if status_filter == "active":
                st.info("💡 Add a new book by clicking '+ Add row' below")
            
            # Create empty DataFrame with correct structure
            df = pd.DataFrame(columns=[
                "id", "title", "author", "genre", "buy_price", 
                "target_price", "stock", "status", "notes"
            ])
        else:
            st.success(f"📊 {len(books)} book(s)")
            df = pd.DataFrame(books)
        
        # Data editor
        edited = st.data_editor(
            df,
            num_rows="dynamic",
            hide_index=True,
            key=f"editor_{tab_key}_{st.session_state.refresh_key}",
            column_config={
                "id": st.column_config.NumberColumn(
                    "🆔 ID", 
                    disabled=True, 
                    width="small"
                ),
                "title": st.column_config.TextColumn(
                    "📖 Title", 
                    width="large", 
                    required=True,
                    help="Book title (required)"
                ),
                "author": st.column_config.TextColumn(
                    "✍️ Author", 
                    width="medium"
                ),
                "genre": st.column_config.SelectboxColumn(
                    "📂 Genre", 
                    options=[g.value for g in Genre], 
                    width="small"
                ),
                "buy_price": st.column_config.NumberColumn(
                    "💵 Buy €", 
                    format="%.2f",
                    min_value=0, 
                    width="small",
                    help="What YOU paid"
                ),
                "target_price": st.column_config.NumberColumn(
                    "🎯 Target €", 
                    format="%.2f",
                    min_value=0, 
                    width="small",
                    help="Your goal price (optional)"
                ),
                "stock": st.column_config.NumberColumn(
                    "📦 Stock", 
                    min_value=0, 
                    step=1, 
                    width="small",
                    help="When 0 → auto-moves to Sold"
                ),
                "status": st.column_config.TextColumn(
                    "📊 Status",
                    width="small",
                    disabled=True,
                    help="Auto-computed from stock"
                ),
                "notes": st.column_config.TextColumn(
                    "📝 Notes", 
                    width="medium"
                ),
                "created_at": None,  # Hide
            },
            column_order=[
                "id", "title", "author", "genre", 
                "buy_price", "target_price", "stock", "status", "notes"
            ],
            width=1400,
        )

        # Action buttons
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button(
                "💾 Save Changes", 
                type="primary", 
                key=f"save_{tab_key}",
                use_container_width=True
            ):
                success, msg = save_books_bulk(
                    edited.to_dict('records'), 
                    status_filter
                )
                if success:
                    st.toast(msg, icon="✅")
                    time.sleep(0.5)
                    st.session_state.refresh_key += 1
                    st.rerun()
                else:
                    st.error(msg)
        
        with col2:
            if st.button(
                "🔄 Refresh", 
                key=f"refresh_{tab_key}",
                use_container_width=True
            ):
                st.session_state.refresh_key += 1
                st.rerun()
        
        with col3:
            st.caption(f"🔄 Last refresh: now")

    # Render each tab
    with tab1:
        render_inventory("active", "active")
    
    with tab2:
        render_inventory("sold", "sold")
    
    with tab3:
        render_inventory(None, "all")


# ============================================================================
# SALES PAGE
# ============================================================================
elif page == "💰 Sales":
    st.header("💰 Record New Sale")
    
    # Get active books with stock
    active_books = get_books("active")
    available_books = [b for b in active_books if b["stock"] > 0]
    
    if not available_books:
        st.warning("⚠️ No books available for sale!")
        st.info("👉 Go to **Inventory** tab to add books or restock")
    else:
        col1, col2 = st.columns([1, 2])
        
        # LEFT: Sale form
        with col1:
            with st.form("sale_form", clear_on_submit=True):
                st.subheader("📝 Sale Details")
                
                # Book selector
                book_options = {
                    f"{b['title']}": b 
                    for b in available_books
                }
                
                selected_title = st.selectbox(
                    "📖 Select Book", 
                    list(book_options.keys()),
                    help="Only books with stock > 0 appear here"
                )
                selected_book = book_options[selected_title]
                
                # Show book info
                target_info = f"🎯 Target: €{selected_book['target_price']:.2f}" if selected_book['target_price'] > 0 else ""
                st.info(
                    f"📦 **Stock:** {selected_book['stock']} available\n\n"
                    f"💵 **Buy price:** €{selected_book['buy_price']:.2f}\n\n"
                    f"{target_info}"
                )
                
                # Sale inputs
                platform = st.selectbox(
                    "🛒 Platform", 
                    [p.value for p in Platform]
                )
                
                qty = st.number_input(
                    "📦 Quantity", 
                    min_value=1, 
                    max_value=selected_book["stock"], 
                    value=1
                )
                
                # Suggest total based on target price or buy price
                suggested_total = qty * (selected_book["target_price"] if selected_book["target_price"] > 0 else selected_book["buy_price"])
                
                total_paid = st.number_input(
                    "💰 Total Paid by Customer (€)", 
                    min_value=0.0, 
                    value=float(suggested_total),
                    step=0.50,
                    help="Total amount customer paid"
                )
                
                packaging_per_book = st.number_input(
                    "📦 Packaging per Book (€)", 
                    min_value=0.0, 
                    value=1.0,
                    step=0.10,
                    help="Shipping materials cost per book"
                )
                
                customer = st.text_input(
                    "👤 Customer Name",
                    placeholder="e.g., Ahmed M."
                )
                
                # Calculate totals
                price_per_book = total_paid / qty
                total_packaging = packaging_per_book * qty
                revenue = total_paid - total_packaging
                cost = selected_book["buy_price"] * qty
                profit = revenue - cost
                
                st.markdown("---")
                st.markdown("### 📊 Calculation")
                st.caption(f"💰 Total: €{total_paid:.2f}")
                st.caption(f"📖 Per book: €{price_per_book:.2f}")
                st.caption(f"📦 Packaging: €{total_packaging:.2f}")
                st.caption(f"💵 Revenue (after packaging): €{revenue:.2f}")
                st.caption(f"💸 Cost: €{cost:.2f}")
                
                if profit >= 0:
                    st.success(f"💚 **Profit: €{profit:.2f}**")
                else:
                    st.error(f"⚠️ **Loss: €{abs(profit):.2f}**")
                    st.warning("You're selling below cost!")
                
                # Submit button
                submitted = st.form_submit_button(
                    "✅ Record Sale", 
                    type="primary",
                    use_container_width=True
                )
                
                if submitted:
                    if not customer.strip():
                        st.error("❌ Please enter customer name")
                    else:
                        success, msg = add_sale(
                            selected_book["id"], 
                            qty, 
                            total_paid,
                            packaging_per_book,
                            customer, 
                            platform
                        )
                        if success:
                            st.success(msg)
                            st.balloons()
                            st.session_state.refresh_key += 1
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error(msg)
        
        # RIGHT: Recent sales
        with col2:
            st.subheader("📋 Recent Sales History")
            
            sales = get_sales()
            
            if sales:
                # Show last 15 sales
                sales_display = []
                for s in sales[:15]:
                    sales_display.append({
                        "ID": s["id"],
                        "📅 Date": s["date"].split()[0],
                        "📖 Book": s["book_title"][:30] + "..." if len(s["book_title"]) > 30 else s["book_title"],
                        "🛒": s["platform"],
                        "Qty": s["qty"],
                        "💰 Total": f"€{s['total']:.2f}",
                        "📦": f"€{s['packaging_per_book']:.2f}",
                        "👤 Customer": s["customer"],
                    })
                
                st.dataframe(
                    pd.DataFrame(sales_display),
                    hide_index=True,
                    width='stretch'
                )
                
                st.caption(f"Showing {len(sales_display)} of {len(sales)} total sales")
                
                # Delete sale (undo)
                with st.expander("🗑️ Undo Sale (Restore Stock)"):
                    sale_id = st.number_input(
                        "Enter Sale ID to delete", 
                        min_value=1, 
                        step=1,
                        help="Find ID in table above"
                    )
                    if st.button("🗑️ Delete Sale & Restore Stock", type="secondary"):
                        success, msg = delete_sale(sale_id)
                        if success:
                            st.success(msg)
                            st.session_state.refresh_key += 1
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(msg)
            else:
                st.info("🎉 No sales yet - make your first sale above!")


# ============================================================================
# ANALYTICS PAGE
# ============================================================================
elif page == "📊 Analytics":
    st.header("📊 Business Analytics")
    
    stats = get_stats()
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Total Revenue", f"€{stats['revenue']:.2f}")
        st.caption(f"📦 Packaging: -€{stats['total_packaging']:.2f}")
    with col2:
        profit_margin = (stats['profit'] / stats['net_revenue'] * 100) if stats['net_revenue'] > 0 else 0
        st.metric("📈 Net Profit", f"€{stats['profit']:.2f}", delta=f"{profit_margin:.1f}%")
    with col3:
        st.metric("📦 Items Sold", stats['items_sold'])
    with col4:
        avg_sale = stats['revenue'] / stats['items_sold'] if stats['items_sold'] > 0 else 0
        st.metric("📊 Avg Sale", f"€{avg_sale:.2f}")
    
    st.divider()
    
    # Inventory metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📚 Active Books", stats['active_count'])
    with col2:
        st.metric("🏦 Stock Value", f"€{stats['stock_value']:.2f}")
    with col3:
        if stats['potential_revenue'] > 0:
            potential_profit = stats['potential_revenue'] - stats['stock_value']
            st.metric("💎 Potential Profit", f"€{potential_profit:.2f}")
        else:
            st.metric("💎 Potential Profit", "Set targets")
    
    st.divider()
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛒 Sales by Platform")
        if stats['platform_sales']:
            platform_df = pd.DataFrame([
                {"Platform": k, "Revenue (€)": v} 
                for k, v in sorted(
                    stats['platform_sales'].items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
            ])
            st.bar_chart(platform_df.set_index("Platform"), height=300)
        else:
            st.info("No sales data yet")
    
    with col2:
        st.subheader("⚠️ Profitability Check")
        if stats['low_margin_books']:
            st.warning(f"**{len(stats['low_margin_books'])}** book(s) with target below cost!")
            for b in stats['low_margin_books']:
                loss = b['buy'] - b['target']
                st.write(f"• **{b['title']}** - Margin: -€{loss:.2f}")
                st.caption(f"  Buy: €{b['buy']:.2f} | Target: €{b['target']:.2f}")
        else:
            st.success("✅ All books have positive target margins!")