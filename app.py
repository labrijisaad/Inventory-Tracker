"""
Midad Books - Main Application Entry Point
Home page with overview and quick stats
"""

import streamlit as st

from src.data.database import init_db
from src.services.analytics_service import get_overview_stats
from src.ui.components import render_page_header
from src.ui.sidebar import render_sidebar
from src.ui.styles import load_custom_css

# Configure page
st.set_page_config(
    page_title="Midad Books - Home",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize
load_custom_css()
init_db()

if "refresh_key" not in st.session_state:
    st.session_state.refresh_key = 0

# ✅ SET CURRENT PAGE
st.session_state.current_page = "Home"

# Render sidebar
render_sidebar()

# ============================================================================
# HOME PAGE CONTENT
# ============================================================================

render_page_header(
    "Welcome to Midad Books", 
    "Arabic Literature Management System • نظام إدارة المكتبة"
)

st.markdown("### 🚀 Quick Start")
st.info("👈 Use the sidebar navigation to access different sections")

st.markdown("<br>", unsafe_allow_html=True)

# Quick navigation cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 25px; border-radius: 12px; text-align: center; color: white;
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);">
            <h2 style="margin: 0; font-size: 40px;">📚</h2>
            <h3 style="margin: 15px 0 5px 0; font-size: 18px;">Inventory</h3>
            <p style="margin: 0; font-size: 13px; opacity: 0.9;">Manage your books</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
                    padding: 25px; border-radius: 12px; text-align: center; color: white;
                    box-shadow: 0 4px 12px rgba(67, 233, 123, 0.3);">
            <h2 style="margin: 0; font-size: 40px;">💰</h2>
            <h3 style="margin: 15px 0 5px 0; font-size: 18px;">Sales</h3>
            <p style="margin: 0; font-size: 13px; opacity: 0.9;">Record transactions</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                    padding: 25px; border-radius: 12px; text-align: center; color: white;
                    box-shadow: 0 4px 12px rgba(250, 112, 154, 0.3);">
            <h2 style="margin: 0; font-size: 40px;">📊</h2>
            <h3 style="margin: 15px 0 5px 0; font-size: 18px;">Analytics</h3>
            <p style="margin: 0; font-size: 13px; opacity: 0.9;">View insights</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    padding: 25px; border-radius: 12px; text-align: center; color: white;
                    box-shadow: 0 4px 12px rgba(79, 172, 254, 0.3);">
            <h2 style="margin: 0; font-size: 40px;">💬</h2>
            <h3 style="margin: 15px 0 5px 0; font-size: 18px;">Messages</h3>
            <p style="margin: 0; font-size: 13px; opacity: 0.9;">Quick templates</p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<br><br>", unsafe_allow_html=True)

# Overview stats
st.markdown("### 📈 Business Overview")

stats = get_overview_stats()

col1, col2, col3, col4 = st.columns(4)
col1.metric("📚 Total Books", stats['book_count'])
col2.metric("📦 In Stock", stats['active_count'])
col3.metric("💰 Total Revenue", f"€{stats['revenue']:.2f}")
col4.metric("📈 Total Profit", f"€{stats['profit']:.2f}")

st.markdown("<br>", unsafe_allow_html=True)

# Recent activity
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🔥 This Week")
    st.info(f"**{stats['weekly_sales']}** sales recorded")
    st.caption(f"Total: €{stats['weekly_revenue']:.2f}")

with col2:
    st.markdown("#### ⚠️ Alerts")
    if stats['low_stock_count'] > 0:
        st.warning(f"**{stats['low_stock_count']}** books need restocking")
    else:
        st.success("All stock levels healthy")