"""
Sidebar Component
Displays navigation, stats, and alerts
"""

from datetime import datetime, timedelta

import streamlit as st

from src.data.database import get_stats
from src.ui.components import (
    load_custom_css,
    render_alerts,
    render_custom_navigation,
    render_footer,
    render_logo,
    render_stats_card,
    render_title,
)
from src.utils.helpers import get_low_stock_books, group_sales_by_bundle


def get_current_week_range() -> tuple[datetime, datetime, str]:
    """
    Get current Monday-Sunday week range.
    
    Returns:
        tuple: (monday_date, sunday_date, formatted_string)
    """
    today = datetime.now()

    # Get Monday of current week (weekday() returns 0 for Monday)
    days_since_monday = today.weekday()  # 0 = Monday, 6 = Sunday
    monday = today - timedelta(days=days_since_monday)

    # Get Sunday of current week
    sunday = monday + timedelta(days=6)

    # Format as "Mon 13/01 - Sun 19/01/2026"
    formatted = f"Mon {monday.strftime('%d/%m')} - Sun {sunday.strftime('%d/%m/%Y')}"

    return monday, sunday, formatted


def render_sidebar():
    """Render complete sidebar with all components."""
    with st.sidebar:
        load_custom_css()
        render_logo()
        render_title()
        render_custom_navigation()

        # Get stats
        stats = get_stats()
        render_stats_card(stats)

        # Get alerts data with PROPER MONDAY-SUNDAY WEEK
        low_stock = get_low_stock_books()

        # ✅ Calculate Monday-Sunday week range
        monday, sunday, week_range_str = get_current_week_range()

        # ✅ FIXED: Group sales first, then filter by week
        from src.data.database import get_sales
        all_sales = get_sales()

        # Filter sales by current week first
        weekly_sales = []
        for sale in all_sales:
            try:
                # Parse sale date
                date_str = sale['date']
                if '/' in date_str:
                    sale_date = datetime.strptime(date_str, "%d/%m/%Y")
                elif ' ' in date_str:
                    sale_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                else:
                    sale_date = datetime.strptime(date_str, "%Y-%m-%d")

                # Check if sale is in current week (Monday to Sunday inclusive)
                if monday.date() <= sale_date.date() <= sunday.date():
                    weekly_sales.append(sale)
            except:
                continue

        # ✅ NOW group by bundles (bundles count as 1 transaction)
        grouped_weekly_sales = group_sales_by_bundle(weekly_sales)

        render_alerts(low_stock, grouped_weekly_sales, week_range_str)
        render_footer()
