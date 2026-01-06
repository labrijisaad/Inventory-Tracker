"""
Data Formatters
Format data for display
"""

from datetime import datetime


def format_currency(amount: float, currency: str = "€") -> str:
    """Format number as currency."""
    return f"{currency}{amount:.2f}"


def format_date(date_str: str, format: str = "%d/%m/%Y") -> str:
    """Format date string."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime(format)
    except:
        return date_str


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format number as percentage."""
    return f"{value:.{decimals}f}%"


def truncate_text(text: str, max_length: int = 30) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."