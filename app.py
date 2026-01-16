import streamlit as st
from src.ui.components import load_custom_css  # ✅ Import first
from src.data.database import init_db
from src.ui.sidebar import render_sidebar

# ✅ SET PAGE CONFIG FIRST
st.set_page_config(
    page_title="Midad Books - Home",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"  # ✅ Force expanded
)

# ✅ LOAD CSS IMMEDIATELY (BEFORE ANYTHING ELSE)
load_custom_css()

# Initialize database
init_db()

# Current page
st.session_state.current_page = "Home"

# Render sidebar
render_sidebar()

# ... rest of your app code ...

# ✅ Redirect to inventory page
st.switch_page("pages/01_inventory.py")
