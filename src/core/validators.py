"""
Input Validation
Validate user inputs and data integrity
"""

def validate_book_data(title: str, buy_price: float, target_price: float, stock: int) -> tuple[bool, str]:
    """Validate book data before saving."""
    if not title or not title.strip():
        return False, "Title is required"
    
    if buy_price < 0:
        return False, "Buy price cannot be negative"
    
    if target_price < 0:
        return False, "Target price cannot be negative"
    
    if stock < 0:
        return False, "Stock cannot be negative"
    
    return True, "Valid"


def validate_sale_data(qty: int, total_paid: float, customer_name: str, customer_username: str) -> tuple[bool, str]:
    """Validate sale data before recording."""
    if qty < 1:
        return False, "Quantity must be at least 1"
    
    if total_paid < 0:
        return False, "Total paid must be positive"
    
    if not customer_name or not customer_name.strip():
        return False, "Customer name is required"
    
    if not customer_username or not customer_username.strip():
        return False, "Customer username is required"
    
    return True, "Valid"


def validate_message_data(title: str, message: str) -> tuple[bool, str]:
    """Validate message template data."""
    if not title or not title.strip():
        return False, "Title is required"
    
    if not message or not message.strip():
        return False, "Message content is required"
    
    return True, "Valid"