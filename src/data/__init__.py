"""
Data Access Layer
Database operations and models
"""

from src.data.database import (
    init_db,
    get_books,
    save_books_bulk,
    get_sales,
    add_sale,
    add_bundle_sale,
    delete_sale,
    get_stats,
    get_customers,
    get_quick_messages,
    add_quick_message,
    update_quick_message,
    delete_quick_message,
)

__all__ = [
    'init_db',
    'get_books',
    'save_books_bulk',
    'get_sales',
    'add_sale',
    'add_bundle_sale',
    'delete_sale',
    'get_stats',
    'get_customers',
    'get_quick_messages',
    'add_quick_message',
    'update_quick_message',
    'delete_quick_message',
]
