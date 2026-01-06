"""
Shared Sidebar Component
"""

from datetime import datetime, timedelta
import streamlit as st

from src.data.database import get_stats
from src.ui.components import (
    render_logo,
    render_title,
    render_custom_navigation,
    render_stats_card,
    render_alerts,
    render_footer,
)
from src.utils.helpers import get_low_stock_books, get_sales_by_date_range


def render_sidebar():
    """Render sidebar."""
    with st.sidebar:
        render_logo()
        render_title()
        render_custom_navigation()
        
        stats = get_stats()
        render_stats_card(stats)
        
        low_stock = get_low_stock_books()
        recent_sales = get_sales_by_date_range(7)
        
        today = datetime.now()
        week_start = today - timedelta(days=7)
        week_range = f"{week_start.strftime('%d/%m')} - {today.strftime('%d/%m/%Y')}"
        
        render_alerts(low_stock, recent_sales, week_range)
        render_footer()