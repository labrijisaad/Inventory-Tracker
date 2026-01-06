"""
Quick Messages Management Page
Create, edit, and manage message templates
"""

import streamlit as st

from src.data.database import init_db
from src.services.message_service import render_messages_page
from src.ui.sidebar import render_sidebar
from src.ui.styles import load_custom_css

# Page config
st.set_page_config(
    page_title="Messages - Midad Books",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize
load_custom_css()
init_db()

# ✅ SET CURRENT PAGE
st.session_state.current_page = "Messages"

# Render sidebar
render_sidebar()

# Render page content
render_messages_page()