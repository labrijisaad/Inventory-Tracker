"""
Helper Functions
Utility functions for common operations
"""

from datetime import datetime, timedelta
import streamlit as st


def show_success_toast(message: str):
    """Show success toast notification."""
    st.toast(f"✅ {message}", icon="✅")


def show_error_toast(message: str):
    """Show error toast notification."""
    st.toast(f"❌ {message}", icon="❌")


def show_info_toast(message: str):
    """Show info toast notification."""
    st.toast(f"ℹ️ {message}", icon="ℹ️")


def get_sales_by_date_range(days: int) -> list[dict]:
    """Get sales within last N days (excluding future dates)."""
    from src.data.database import get_sales

    today = datetime.now().date()
    start_date = today - timedelta(days=days)

    all_sales = get_sales()
    filtered = []

    for s in all_sales:
        try:
            date_str = s['date']

            # Parse different date formats
            if '/' in date_str:
                sale_date = datetime.strptime(date_str, "%d/%m/%Y").date()
            elif ' ' in date_str:
                sale_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d").date()
            else:
                sale_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Only include sales within range AND not in future
            if start_date <= sale_date <= today:
                filtered.append(s)

        except Exception:
            continue

    return filtered


def get_low_stock_books(threshold: int = 2) -> list[dict]:
    """Get books with stock below threshold."""
    from src.data.database import get_books

    books = get_books("active")
    return [b for b in books if 0 < b["stock"] <= threshold]


def format_currency(amount: float) -> str:
    """Format amount as Euro currency."""
    return f"€{amount:.2f}"


def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value:.1f}%"


# ✅ FIXED: Calculate profit with proper book lookup
def group_sales_by_bundle(sales: list[dict]) -> list[dict]:
    """Group sales by bundle_id and calculate profits."""
    from src.data.database import get_books

    if not sales:
        return []

    # Get all books for profit calculation
    all_books = get_books()
    books_dict = {b['id']: b for b in all_books}

    # Group by bundle
    bundles = {}
    singles = []

    for sale in sales:
        bundle_id = sale.get('bundle_id')

        if bundle_id:
            if bundle_id not in bundles:
                bundles[bundle_id] = {
                    'id': f"B-{bundle_id[:7]}",
                    'type': 'bundle',
                    'date': sale['date'],
                    'platform': sale['platform'],
                    'customer': sale['customer'],
                    'customer_username': sale['customer_username'],
                    'total': 0,
                    'qty': 0,
                    'profit': 0,
                    'bundle_details': [],
                    'bundle_id': bundle_id
                }

            # Calculate profit for this sale item
            book = books_dict.get(sale['book_id'])
            if book:
                revenue = sale['total'] - (sale['packaging_per_book'] * sale['qty'])
                cost = book['buy_price'] * sale['qty']
                profit = revenue - cost
            else:
                profit = 0

            bundles[bundle_id]['total'] += sale['total']
            bundles[bundle_id]['qty'] += sale['qty']
            bundles[bundle_id]['profit'] += profit
            bundles[bundle_id]['bundle_details'].append(
                f"{sale['qty']}x {sale['book_title']}"
            )
        else:
            # Single sale - calculate profit
            book = books_dict.get(sale['book_id'])
            if book:
                revenue = sale['total'] - (sale['packaging_per_book'] * sale['qty'])
                cost = book['buy_price'] * sale['qty']
                profit = revenue - cost
            else:
                profit = 0

            singles.append({
                'id': sale['id'],
                'type': 'single',
                'date': sale['date'],
                'book_title': sale['book_title'],
                'platform': sale['platform'],
                'customer': sale['customer'],
                'customer_username': sale['customer_username'],
                'qty': sale['qty'],
                'total': sale['total'],
                'profit': profit,
                'bundle_details': None
            })

    # Combine and sort by date (newest first)
    result = list(bundles.values()) + singles

    # ✅ FIXED: Sort with proper date parsing
    def parse_sale_date(sale):
        try:
            date_str = sale['date']
            if '/' in date_str:
                return datetime.strptime(date_str, "%d/%m/%Y")
            elif ' ' in date_str:
                return datetime.strptime(date_str.split()[0], "%Y-%m-%d")
            else:
                return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            return datetime.min

    result.sort(key=parse_sale_date, reverse=True)

    return result


def calculate_margin_percentage(profit: float, revenue: float) -> float:
    """Calculate profit margin percentage."""
    if revenue <= 0:
        return 0
    return (profit / revenue) * 100
