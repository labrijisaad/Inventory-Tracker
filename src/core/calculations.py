"""
Business Calculations
Profit, revenue, and margin calculations
"""

def calculate_sale_profit(qty: int, total_paid: float, packaging_per_book: float, buy_price: float) -> dict:
    """Calculate profit for a single sale."""
    price_per_book = total_paid / qty if qty > 0 else 0
    total_packaging = packaging_per_book * qty
    revenue = total_paid - total_packaging
    cost = buy_price * qty
    profit = revenue - cost
    margin = (profit / revenue * 100) if revenue > 0 else 0
    
    return {
        'price_per_book': price_per_book,
        'total_packaging': total_packaging,
        'revenue': revenue,
        'cost': cost,
        'profit': profit,
        'margin_percent': margin
    }


def calculate_bundle_profit(quantities: list[int], buy_prices: list[float], 
                           total_paid: float, packaging_per_book: float) -> dict:
    """Calculate profit for bundle sale."""
    total_books = sum(quantities)
    price_per_book = total_paid / total_books if total_books > 0 else 0
    total_packaging = packaging_per_book * total_books
    revenue = total_paid - total_packaging
    
    total_cost = sum(qty * price for qty, price in zip(quantities, buy_prices))
    profit = revenue - total_cost
    margin = (profit / revenue * 100) if revenue > 0 else 0
    
    return {
        'total_books': total_books,
        'price_per_book': price_per_book,
        'total_packaging': total_packaging,
        'revenue': revenue,
        'cost': total_cost,
        'profit': profit,
        'margin_percent': margin
    }


def calculate_profit_for_sale(sale: dict, books: list[dict]) -> float:
    """Calculate profit for a sale record."""
    book = next((b for b in books if b["id"] == sale["book_id"]), None)
    if not book:
        return 0
    
    revenue = sale["total"] - (sale["packaging_per_book"] * sale["qty"])
    cost = book["buy_price"] * sale["qty"]
    return revenue - cost