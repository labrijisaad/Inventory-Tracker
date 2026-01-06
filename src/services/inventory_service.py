"""
Inventory Service
Business logic for inventory management
"""

import time
import pandas as pd
import streamlit as st
from typing import Optional

from src.data.database import get_books, save_books_bulk, get_stats
from src.ui.components import render_page_header, render_info_banner
from src.config import GENRES
from src.utils.helpers import show_success_toast, show_error_toast


def render_inventory_page():
    """Main inventory page."""
    stats = get_stats()
    
    render_page_header(
        "Inventory Management",
        "Manage your book collection - Track stock, prices, and sales history"
    )
    
    render_info_banner(
        "💡 Books with stock = 0 automatically move to 'Sold' tab",
        type="info"
    )
    
    # Total Stock metric
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        st.metric("📦 Total Stock", stats["total_stock"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([
        f"🟢 Active ({stats['active_count']})", 
        f"🔴 Sold ({stats['sold_count']})", 
        "📋 All"
    ])
    
    with tab1:
        st.caption("📦 Books currently in stock")
        _render_inventory_table("active", "active")
    
    with tab2:
        st.caption("🔴 Books sold out (stock = 0)")
        _render_inventory_table("sold", "sold")
    
    with tab3:
        st.caption("📋 All books in inventory")
        _render_inventory_table(None, "all")


def _render_inventory_table(status_filter: Optional[str], tab_key: str):
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
    column_config, column_order = _get_column_config(status_filter)
    
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
        if st.button("💾 Save Changes", type="primary", key=f"save_{tab_key}", width='stretch'):
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
        if st.button("🔄 Refresh", key=f"refresh_{tab_key}", width='stretch'):
            show_success_toast("Refreshed!")
            st.session_state.refresh_key += 1
            st.rerun()
    
    if books:
        st.caption("💡 Tip: Edit cells directly, add rows with '+', then click Save")


def _get_column_config(status_filter: Optional[str]) -> tuple[dict, list]:
    """Get column configuration based on filter."""
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
    
    return column_config, column_order