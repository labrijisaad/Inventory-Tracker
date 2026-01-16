"""
Inventory Management Page
Manage book collection, stock, and pricing
"""

import streamlit as st

from src.data.database import init_db
from src.services.inventory_service import render_inventory_page
from src.ui.sidebar import render_sidebar
from src.ui.styles import load_custom_css

# Page config
st.set_page_config(
    page_title="Inventory - Midad Books",
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
st.session_state.current_page = "Inventory"

# Render sidebar
render_sidebar()

# Render page content
render_inventory_page()
