"""
Health Check Endpoint
For monitoring if app is running correctly
Access: http://your-domain.com/99_health
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(page_title="Health", page_icon="💚", layout="centered")

# Hide from sidebar
st.markdown("""
<style>
    [data-testid="stSidebarNav"] li:last-child {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("# 💚 Health Check")

try:
    from src.data.database import init_db, get_engine, DB_PATH
    from sqlmodel import Session, select, func
    from src.data.database import Book

    # Test database connection
    init_db()
    engine = get_engine()

    with Session(engine) as session:
        book_count = session.exec(select(func.count(Book.id))).one()

    # Check database file
    db_exists = DB_PATH.exists()
    db_size = DB_PATH.stat().st_size if db_exists else 0

    # Success!
    st.success("✅ Application Healthy")

    st.json({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": {
            "path": str(DB_PATH),
            "exists": db_exists,
            "size_mb": round(db_size / (1024*1024), 2),
            "books_count": book_count
        }
    })

except Exception as e:
    st.error("❌ Health Check Failed")
    st.json({
        "status": "unhealthy",
        "error": str(e),
        "timestamp": datetime.now().isoformat()
    })
