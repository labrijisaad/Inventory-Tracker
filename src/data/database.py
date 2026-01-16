"""
Database Operations
SQLite database management with SQLModel
"""

import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select

from src.config import load_default_messages

# ============================================================================
# ENVIRONMENT-AWARE DATABASE PATH
# ============================================================================

import os

# Detect environment and set database path
if os.getenv('PRODUCTION') == 'true':
    # Production: Use separate data directory on VM
    DB_PATH = Path('/opt/midad-data/midad.db')
    print("🚀 Running in PRODUCTION mode")
else:
    # Development: Use local data folder
    DATA_DIR = Path(__file__).parent.parent.parent / "data"
    DB_PATH = DATA_DIR / "midad.db"
    print("💻 Running in DEVELOPMENT mode")

# Ensure directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
print(f"📂 Database path: {DB_PATH}")

# ============================================================================
# ✅ CRITICAL FIX: Clear metadata BEFORE defining models
# ============================================================================
try:
    # Try to clear existing metadata/mappings
    if hasattr(SQLModel, 'metadata'):
        SQLModel.metadata.clear()

    # Also clear the registry if it exists
    if hasattr(SQLModel, 'registry'):
        try:
            SQLModel.registry.dispose()
        except:
            pass
except Exception as e:
    print(f"⚠️ Metadata clear warning (safe to ignore): {e}")


# ============================================================================
# MODELS
# ============================================================================
class Customer(SQLModel, table=True):
    """Customer database."""
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    vinted_username: str = Field(index=True, unique=True)
    name: str
    platform_preference: str = Field(default="Vinted")
    notes: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

    sales: list["Sale"] = Relationship(back_populates="customer_rel")


class Book(SQLModel, table=True):
    """Book in inventory."""
    __table_args__ = {"extend_existing": True}

    id: str = Field(primary_key=True)
    title: str = Field(index=True)
    author: str = ""
    genre: str = Field(default="Other")
    buy_price: float = Field(default=0, ge=0)
    target_price: float = Field(default=0, ge=0)
    stock: int = Field(default=1, ge=0)
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    notes: str = ""

    sales: list["Sale"] = Relationship(back_populates="book")

    @property
    def status(self) -> str:
        return "Sold Out" if self.stock == 0 else "Active"

    @property
    def is_available(self) -> bool:
        return self.stock > 0


class Sale(SQLModel, table=True):
    """Sale record."""
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    qty: int = Field(default=1, ge=1)
    price: float = Field(ge=0)
    packaging_per_book: float = Field(default=0, ge=0)
    total: float = Field(ge=0)
    platform: str = Field(default="Vinted")
    bundle_id: Optional[str] = Field(default=None, index=True)

    book_id: Optional[str] = Field(default=None, foreign_key="book.id")
    book: Optional[Book] = Relationship(back_populates="sales")

    customer_id: int = Field(foreign_key="customer.id")
    customer_rel: Customer = Relationship(back_populates="sales")


class QuickMessage(SQLModel, table=True):
    """Quick message templates."""
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    category: str = Field(default="General")
    message: str
    order_position: int = Field(default=0)
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    updated_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))


# ============================================================================
# DATABASE ENGINE (SINGLETON)
# ============================================================================
_engine = None

def get_engine():
    """Get or create database engine (singleton)."""
    global _engine
    if _engine is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    return _engine


def init_db():
    """Create tables and initialize default messages (only once per session)."""
    # ✅ Use Streamlit session state to track initialization
    import streamlit as st

    if 'db_initialized' in st.session_state and st.session_state['db_initialized']:
        return  # Already initialized in this session

    engine = get_engine()

    # Create all tables
    SQLModel.metadata.create_all(engine)

    # Initialize default messages if empty
    try:
        with Session(engine) as session:
            existing = session.exec(select(QuickMessage)).first()
            if not existing:
                default_messages = load_default_messages()
                for i, (key, msg) in enumerate(default_messages.items()):
                    quick_msg = QuickMessage(
                        title=msg['title'],
                        category=msg['category'],
                        message=msg['message'],
                        order_position=i
                    )
                    session.add(quick_msg)
                session.commit()
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize default messages: {e}")

    # Mark as initialized
    st.session_state['db_initialized'] = True


# ============================================================================
# HELPER: STANDARDIZE DATE FORMAT
# ============================================================================
def standardize_date(sale_date) -> str:
    """
    Convert any date format to YYYY-MM-DD string.
    Handles: date objects, DD/MM/YYYY, YYYY-MM-DD, datetime strings
    """
    if not sale_date:
        return datetime.now().strftime("%Y-%m-%d")

    try:
        # If it's already a date/datetime object
        if isinstance(sale_date, (date, datetime)):
            return sale_date.strftime("%Y-%m-%d")

        # If it's a string
        sale_date_str = str(sale_date).strip()

        # Try DD/MM/YYYY format
        if '/' in sale_date_str:
            date_obj = datetime.strptime(sale_date_str, "%d/%m/%Y")
            return date_obj.strftime("%Y-%m-%d")

        # Try YYYY-MM-DD format (may have time component)
        if ' ' in sale_date_str:
            # Remove time component if present
            sale_date_str = sale_date_str.split()[0]

        # Parse YYYY-MM-DD
        date_obj = datetime.strptime(sale_date_str, "%Y-%m-%d")
        return date_obj.strftime("%Y-%m-%d")

    except Exception as e:
        print(f"⚠️ Date parse error '{sale_date}', using today: {e}")
        return datetime.now().strftime("%Y-%m-%d")


# ============================================================================
# CUSTOMER OPERATIONS
# ============================================================================
def get_customers() -> list[dict]:
    """Get all customers with stats."""
    with Session(get_engine()) as session:
        customers = session.exec(select(Customer).order_by(Customer.created_at.desc())).all()

        result = []
        for c in customers:
            customer_sales = [s for s in c.sales]

            # Count unique orders (bundle_id or individual sale)
            unique_orders = set()
            for s in customer_sales:
                if s.bundle_id:
                    unique_orders.add(s.bundle_id)
                else:
                    unique_orders.add(f"sale_{s.id}")

            total_purchases = len(unique_orders)
            total_spent = sum(s.total for s in customer_sales)
            last_purchase = max([s.date for s in customer_sales]) if customer_sales else "Never"

            result.append({
                "id": c.id,
                "vinted_username": c.vinted_username,
                "name": c.name,
                "platform_preference": c.platform_preference,
                "total_purchases": total_purchases,
                "total_spent": total_spent,
                "last_purchase": last_purchase,
                "notes": c.notes,
                "created_at": c.created_at,
            })

        return result


# ============================================================================
# BOOK OPERATIONS
# ============================================================================
def generate_book_id() -> str:
    """Generate next book ID in format BOOK-XXX."""
    with Session(get_engine()) as session:
        books = session.exec(select(Book)).all()

        # Extract numeric parts from existing IDs
        max_num = 0
        for book in books:
            if book.id and book.id.startswith("BOOK-"):
                try:
                    num = int(book.id.replace("BOOK-", ""))
                    max_num = max(max_num, num)
                except ValueError:
                    pass

        # Return next ID
        return f"BOOK-{max_num + 1:03d}"


def get_books(filter_type: Optional[str] = None) -> list[dict]:
    """Get all books with computed status."""
    with Session(get_engine()) as session:
        # ✅ FIXED: Sort by ID ascending (BOOK-001, BOOK-002, ...)
        query = select(Book).order_by(Book.id)
        books = session.exec(query).all()

        result = []
        for b in books:
            status = "Sold Out" if b.stock == 0 else "Active"

            # Apply filter
            if filter_type == "active" and b.stock == 0:
                continue
            if filter_type == "sold" and b.stock > 0:
                continue

            result.append({
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "genre": b.genre,
                "buy_price": b.buy_price,
                "target_price": b.target_price,
                "stock": b.stock,
                "status": status,
                "notes": b.notes,
                "created_at": b.created_at,
            })

        return result


# Add this function to database.py after get_books()

def get_sold_books_with_sales() -> list[dict]:
    """
    Get books that have been sold (stock = 0) with their complete sales history.
    Returns aggregated view with expandable sale details.
    """
    with Session(get_engine()) as session:
        # Get all books with stock = 0
        sold_books = session.exec(
            select(Book).where(Book.stock == 0).order_by(Book.id)
        ).all()

        result = []
        for book in sold_books:
            # Get all sales for this book
            book_sales = [s for s in book.sales]

            if not book_sales:
                # Book has 0 stock but no sales recorded (shouldn't happen, but handle it)
                continue

            # Aggregate sales data
            total_qty_sold = sum(s.qty for s in book_sales)
            total_revenue = sum(s.total for s in book_sales)
            total_packaging = sum(s.packaging_per_book * s.qty for s in book_sales)
            total_cost = book.buy_price * total_qty_sold
            total_profit = (total_revenue - total_packaging) - total_cost

            # Get date range
            sale_dates = [datetime.strptime(s.date, "%Y-%m-%d") for s in book_sales]
            first_sale = min(sale_dates).strftime("%d/%m/%Y")
            last_sale = max(sale_dates).strftime("%d/%m/%Y")

            # Get unique customers
            unique_customers = set(s.customer_rel.name for s in book_sales)

            # Individual sale details (for expandable section)
            sale_details = []
            for s in book_sales:
                sale_date = datetime.strptime(s.date, "%Y-%m-%d").strftime("%d/%m/%Y")
                sale_id = f"SE{s.id:03d}" if not s.bundle_id else f"B-{s.bundle_id[:7]}"

                # Calculate profit for this specific sale
                sale_revenue = s.total - (s.packaging_per_book * s.qty)
                sale_cost = book.buy_price * s.qty
                sale_profit = sale_revenue - sale_cost

                sale_details.append({
                    'sale_id': sale_id,
                    'date': sale_date,
                    'qty': s.qty,
                    'customer': s.customer_rel.name,
                    'platform': s.platform,
                    'total': s.total,
                    'profit': sale_profit
                })

            result.append({
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'genre': book.genre,
                'buy_price': book.buy_price,
                'target_price': book.target_price,
                'total_qty_sold': total_qty_sold,
                'num_sales': len(book_sales),
                'total_revenue': total_revenue,
                'total_profit': total_profit,
                'first_sale_date': first_sale,
                'last_sale_date': last_sale,
                'num_customers': len(unique_customers),
                'sale_details': sale_details  # List of individual sales
            })

        return result

def save_books_bulk(books_data: list[dict], filter_type: Optional[str] = None) -> tuple[bool, str]:
    """Save multiple books with validation."""
    try:
        with Session(get_engine()) as session:
            # Get existing books based on filter
            query = select(Book)
            if filter_type == "active":
                query = query.where(Book.stock > 0)
            elif filter_type == "sold":
                query = query.where(Book.stock == 0)

            existing = {b.id: b for b in session.exec(query).all()}
            processed_ids = set()

            # Process each book
            for data in books_data:
                title = str(data.get("title", "")).strip()
                if not title:
                    continue

                # Validate numbers
                try:
                    buy_price = float(data.get("buy_price", 0) or 0)
                    target_price = float(data.get("target_price", 0) or 0)
                    stock = int(data.get("stock", 0) or 0)

                    if buy_price < 0:
                        return False, f"❌ Buy price cannot be negative for '{title}'"
                    if target_price < 0:
                        return False, f"❌ Target price cannot be negative for '{title}'"
                    if stock < 0:
                        return False, f"❌ Stock cannot be negative for '{title}'"

                except ValueError as e:
                    return False, f"❌ Invalid number format for '{title}': {e}"

                # Check if book exists
                book_id = data.get("id")
                is_existing = (
                    book_id is not None
                    and not (isinstance(book_id, float) and pd.isna(book_id))
                    and str(book_id) != ""
                    and str(book_id) in existing
                )

                if is_existing:
                    # Update existing book
                    book = existing[str(book_id)]
                    book.title = title
                    book.author = str(data.get("author", ""))
                    book.genre = str(data.get("genre", "Other"))
                    book.buy_price = buy_price
                    book.target_price = target_price
                    book.stock = stock
                    book.notes = str(data.get("notes", ""))
                    processed_ids.add(str(book_id))
                else:
                    # Create new book
                    new_id = generate_book_id()
                    book = Book(
                        id=new_id,
                        title=title,
                        author=str(data.get("author", "")),
                        genre=str(data.get("genre", "Other")),
                        buy_price=buy_price,
                        target_price=target_price,
                        stock=stock,
                        notes=str(data.get("notes", "")),
                    )
                    session.add(book)

            # Handle deleted rows
            if filter_type:
                for book_id, book in existing.items():
                    if book_id not in processed_ids:
                        # Check if book has sales history
                        if len(book.sales) > 0:
                            return False, f"❌ Cannot delete '{book.title}' - has sales history!"
                        session.delete(book)

            session.commit()
            return True, "✅ Saved successfully"

    except Exception as e:
        return False, f"❌ Error: {str(e)}"


# ============================================================================
# SALE OPERATIONS
# ============================================================================
def get_sales() -> list[dict]:
    """Get all sales with details."""
    with Session(get_engine()) as session:
        sales = session.exec(select(Sale).order_by(Sale.id.desc())).all()

        result = []
        for s in sales:
            book = session.get(Book, s.book_id) if s.book_id else None

            result.append({
                "id": s.id,
                "date": s.date,
                "qty": s.qty,
                "price": s.price,
                "packaging_per_book": s.packaging_per_book,
                "total": s.total,
                "customer": s.customer_rel.name,
                "customer_username": s.customer_rel.vinted_username,
                "platform": s.platform,
                "book_id": s.book_id,
                "book_title": book.title if book else "Unknown",
                "bundle_id": s.bundle_id,
                "customer_id": s.customer_id,
            })

        return result


def add_sale(book_id: str, qty: int, total_paid: float, packaging_per_book: float,
             customer_name: str, customer_username: str, platform: str,
             sale_date: Optional[str] = None) -> tuple[bool, str]:
    """Record single book sale."""
    # Validation
    if qty < 1:
        return False, "❌ Quantity must be at least 1"
    if total_paid < 0:
        return False, "❌ Total paid must be positive"
    if not customer_name.strip():
        return False, "❌ Customer name required"
    if not customer_username.strip():
        return False, "❌ Username required"

    try:
        with Session(get_engine()) as session:
            # Get or create customer
            customer = session.exec(
                select(Customer).where(Customer.vinted_username == customer_username.strip())
            ).first()

            if not customer:
                customer = Customer(
                    vinted_username=customer_username.strip(),
                    name=customer_name.strip(),
                    platform_preference=platform,
                )
                session.add(customer)
                session.commit()
                session.refresh(customer)

            # Get book
            book = session.get(Book, book_id)
            if not book:
                return False, "❌ Book not found"

            # Check stock
            if book.stock < qty:
                return False, f"❌ Not enough stock! Only {book.stock} available"

            # Calculate financials
            price_per_book = total_paid / qty
            total_packaging = packaging_per_book * qty
            revenue = total_paid - total_packaging
            cost = book.buy_price * qty
            profit = revenue - cost

            # Standardize date
            date_str = standardize_date(sale_date)

            # Create sale
            sale = Sale(
                book_id=book_id,
                qty=qty,
                price=price_per_book,
                packaging_per_book=packaging_per_book,
                total=total_paid,
                customer_id=customer.id,
                platform=platform,
                date=date_str,
                bundle_id=None
            )
            session.add(sale)

            # Update stock
            book.stock -= qty

            session.commit()

            new_status = "Sold Out" if book.stock == 0 else "Active"
            return True, f"✅ Sold {qty}x '{book.title}' for €{total_paid:.2f} | Profit: €{profit:.2f} | Stock: {book.stock} ({new_status})"

    except Exception as e:
        return False, f"❌ Error: {str(e)}"


def add_bundle_sale(book_ids: list[str], quantities: list[int], total_paid: float,
                   packaging_per_book: float, customer_name: str, customer_username: str,
                   platform: str, sale_date: Optional[str] = None) -> tuple[bool, str]:
    """Record bundle sale."""
    # Validation
    if len(book_ids) < 2:
        return False, "❌ Bundle must have at least 2 books"
    if len(book_ids) != len(quantities):
        return False, "❌ Book IDs and quantities must match"
    if total_paid < 0:
        return False, "❌ Total paid must be positive"
    if not customer_name.strip() or not customer_username.strip():
        return False, "❌ Customer name and username required"

    try:
        with Session(get_engine()) as session:
            # Get or create customer
            customer = session.exec(
                select(Customer).where(Customer.vinted_username == customer_username.strip())
            ).first()

            if not customer:
                customer = Customer(
                    vinted_username=customer_username.strip(),
                    name=customer_name.strip(),
                    platform_preference=platform,
                )
                session.add(customer)
                session.commit()
                session.refresh(customer)

            # Validate all books and stock
            books = []
            for book_id, qty in zip(book_ids, quantities):
                book = session.get(Book, book_id)
                if not book:
                    return False, f"❌ Book #{book_id} not found"
                if book.stock < qty:
                    return False, f"❌ Not enough stock for '{book.title}'! Only {book.stock} available"
                books.append(book)

            # Calculate financials
            total_books = sum(quantities)
            price_per_book = total_paid / total_books
            total_packaging = packaging_per_book * total_books
            revenue = total_paid - total_packaging
            total_cost = sum(book.buy_price * qty for book, qty in zip(books, quantities))
            profit = revenue - total_cost

            # Generate bundle ID
            bundle_id = str(uuid.uuid4())[:8]

            # Standardize date
            date_str = standardize_date(sale_date)

            # Create sales for each book in bundle
            for book, qty in zip(books, quantities):
                sale_total = price_per_book * qty

                sale = Sale(
                    book_id=book.id,
                    qty=qty,
                    price=price_per_book,
                    packaging_per_book=packaging_per_book,
                    total=sale_total,
                    customer_id=customer.id,
                    platform=platform,
                    date=date_str,
                    bundle_id=bundle_id
                )
                session.add(sale)

                # Update stock
                book.stock -= qty

            session.commit()

            return True, f"✅ Bundle sold: {total_books} books for €{total_paid:.2f} | Profit: €{profit:.2f}"

    except Exception as e:
        return False, f"❌ Error: {str(e)}"


def delete_sale(sale_id: int) -> tuple[bool, str]:
    """Delete sale and restore stock."""
    try:
        with Session(get_engine()) as session:
            sale = session.get(Sale, sale_id)
            if not sale:
                return False, "Sale not found"

            # If part of bundle, delete entire bundle
            if sale.bundle_id:
                bundle_sales = session.exec(
                    select(Sale).where(Sale.bundle_id == sale.bundle_id)
                ).all()

                for s in bundle_sales:
                    book = session.get(Book, s.book_id)
                    if book:
                        book.stock += s.qty
                    session.delete(s)

                session.commit()
                return True, f"✅ Bundle deleted ({len(bundle_sales)} items), stock restored"
            else:
                # Single sale
                book = session.get(Book, sale.book_id)
                if book:
                    book.stock += sale.qty

                session.delete(sale)
                session.commit()
                return True, "✅ Sale deleted, stock restored"

    except Exception as e:
        return False, f"❌ Error: {str(e)}"


# ============================================================================
# ANALYTICS
# ============================================================================
def get_stats() -> dict:
    """Calculate statistics."""
    with Session(get_engine()) as session:
        books = list(session.exec(select(Book)).all())
        sales = list(session.exec(select(Sale)).all())
        customers = list(session.exec(select(Customer)).all())

        # Book stats
        active_books = [b for b in books if b.stock > 0]
        sold_books = [b for b in books if b.stock == 0]

        total_stock = sum(b.stock for b in books)
        stock_value = sum(b.stock * b.buy_price for b in books)
        potential_revenue = sum(b.stock * b.target_price for b in books if b.target_price > 0)

        # Sales stats
        revenue = sum(s.total for s in sales)
        items_sold = sum(s.qty for s in sales)
        total_packaging = sum(s.packaging_per_book * s.qty for s in sales)

        # Calculate COGS
        cogs = 0
        for sale in sales:
            book = session.get(Book, sale.book_id)
            if book:
                cogs += sale.qty * book.buy_price

        # Profit calculation
        net_revenue = revenue - total_packaging
        profit = net_revenue - cogs

        # Platform breakdown
        platform_sales = {}
        for sale in sales:
            platform_sales[sale.platform] = platform_sales.get(sale.platform, 0) + sale.total

        # Low margin books warning
        low_margin_books = [
            {"title": b.title, "buy": b.buy_price, "target": b.target_price}
            for b in active_books
            if b.target_price > 0 and b.target_price < b.buy_price
        ]

        # Bundle count
        bundle_ids = set(s.bundle_id for s in sales if s.bundle_id)
        bundle_count = len(bundle_ids)

        return {
            "book_count": len(books),
            "active_count": len(active_books),
            "sold_count": len(sold_books),
            "total_stock": total_stock,
            "stock_value": stock_value,
            "potential_revenue": potential_revenue,
            "revenue": revenue,
            "total_packaging": total_packaging,
            "net_revenue": net_revenue,
            "cogs": cogs,
            "profit": profit,
            "items_sold": items_sold,
            "platform_sales": platform_sales,
            "low_margin_books": low_margin_books,
            "customer_count": len(customers),
            "bundle_count": bundle_count,
        }


# ============================================================================
# QUICK MESSAGES OPERATIONS
# ============================================================================
def get_quick_messages() -> list[dict]:
    """Get all quick messages."""
    with Session(get_engine()) as session:
        messages = session.exec(select(QuickMessage).order_by(QuickMessage.order_position)).all()
        return [{
            "id": m.id,
            "title": m.title,
            "category": m.category,
            "message": m.message,
            "order_position": m.order_position,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
        } for m in messages]


def add_quick_message(title: str, category: str, message: str) -> tuple[bool, str]:
    """Add new quick message."""
    if not title.strip():
        return False, "❌ Title is required"
    if not message.strip():
        return False, "❌ Message is required"

    try:
        with Session(get_engine()) as session:
            # Get next position
            max_pos = session.exec(select(QuickMessage)).all()
            next_pos = len(max_pos)

            quick_msg = QuickMessage(
                title=title.strip(),
                category=category,
                message=message.strip(),
                order_position=next_pos
            )
            session.add(quick_msg)
            session.commit()
            return True, "✅ Message added successfully"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"


def update_quick_message(msg_id: int, title: str, category: str, message: str) -> tuple[bool, str]:
    """Update existing quick message."""
    if not title.strip():
        return False, "❌ Title is required"
    if not message.strip():
        return False, "❌ Message is required"

    try:
        with Session(get_engine()) as session:
            msg = session.get(QuickMessage, msg_id)
            if not msg:
                return False, "❌ Message not found"

            msg.title = title.strip()
            msg.category = category
            msg.message = message.strip()
            msg.updated_at = datetime.now().strftime("%Y-%m-%d")
            session.commit()
            return True, "✅ Message updated successfully"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"


def delete_quick_message(msg_id: int) -> tuple[bool, str]:
    """Delete quick message."""
    try:
        with Session(get_engine()) as session:
            msg = session.get(QuickMessage, msg_id)
            if not msg:
                return False, "❌ Message not found"

            session.delete(msg)
            session.commit()
            return True, "✅ Message deleted successfully"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

# Add these two functions to database.py

def get_sales_history_grouped() -> list[dict]:
    """
    Get all sales grouped by sale/bundle ID for chronological display.
    Returns sales/bundles in reverse chronological order.
    """
    with Session(get_engine()) as session:
        sales = session.exec(select(Sale).order_by(Sale.date.desc(), Sale.id.desc())).all()

        # Group by bundle_id or individual sale
        grouped = {}

        for sale in sales:
            if sale.bundle_id:
                # Bundle sale
                if sale.bundle_id not in grouped:
                    grouped[sale.bundle_id] = {
                        'type': 'bundle',
                        'sale_id': f"B-{sale.bundle_id[:7]}",
                        'date': sale.date,
                        'customer': sale.customer_rel.name,
                        'platform': sale.platform,
                        'total': 0,
                        'books': []
                    }

                # Add book to bundle
                book = session.get(Book, sale.book_id)
                book_revenue = sale.total - (sale.packaging_per_book * sale.qty)
                book_cost = book.buy_price * sale.qty if book else 0
                book_profit = book_revenue - book_cost

                grouped[sale.bundle_id]['total'] += sale.total
                grouped[sale.bundle_id]['books'].append({
                    'book_id': sale.book_id,
                    'title': book.title if book else 'Unknown',
                    'qty': sale.qty,
                    'price_per_book': sale.price,
                    'total': sale.total,
                    'profit': book_profit
                })
            else:
                # Single sale
                book = session.get(Book, sale.book_id)
                book_revenue = sale.total - (sale.packaging_per_book * sale.qty)
                book_cost = book.buy_price * sale.qty if book else 0
                book_profit = book_revenue - book_cost

                grouped[f"single_{sale.id}"] = {
                    'type': 'single',
                    'sale_id': f"SE{sale.id:03d}",
                    'date': sale.date,
                    'customer': sale.customer_rel.name,
                    'platform': sale.platform,
                    'total': sale.total,
                    'books': [{
                        'book_id': sale.book_id,
                        'title': book.title if book else 'Unknown',
                        'qty': sale.qty,
                        'price_per_book': sale.price,
                        'total': sale.total,
                        'profit': book_profit
                    }]
                }

        # Convert to list and sort by date
        result = list(grouped.values())
        result.sort(key=lambda x: x['date'], reverse=True)

        # Calculate total profit for each transaction
        for transaction in result:
            transaction['profit'] = sum(b['profit'] for b in transaction['books'])
            transaction['num_books'] = sum(b['qty'] for b in transaction['books'])

        return result


def get_book_performance_stats() -> list[dict]:
    """
    Get lifetime performance statistics for ALL books (active + sold).
    Useful for analyzing which books sell well, which don't, etc.
    """
    with Session(get_engine()) as session:
        books = session.exec(select(Book).order_by(Book.id)).all()

        result = []
        for book in books:
            # Get all sales for this book
            book_sales = [s for s in book.sales]

            total_qty_sold = sum(s.qty for s in book_sales)
            total_revenue = sum(s.total for s in book_sales)
            total_packaging = sum(s.packaging_per_book * s.qty for s in book_sales)
            total_cost = book.buy_price * total_qty_sold
            total_profit = (total_revenue - total_packaging) - total_cost

            avg_margin = (total_profit / (total_revenue - total_packaging) * 100) if (total_revenue - total_packaging) > 0 else 0

            # Calculate days since first sale
            if book_sales:
                sale_dates = [datetime.strptime(s.date, "%Y-%m-%d") for s in book_sales]
                first_sale = min(sale_dates)
                last_sale = max(sale_dates)
                days_on_market = (last_sale - first_sale).days + 1
                velocity = total_qty_sold / days_on_market if days_on_market > 0 else 0
            else:
                first_sale = None
                last_sale = None
                days_on_market = 0
                velocity = 0

            result.append({
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'genre': book.genre,
                'buy_price': book.buy_price,
                'target_price': book.target_price,
                'current_stock': book.stock,
                'status': book.status,
                'total_sold': total_qty_sold,
                'total_revenue': total_revenue,
                'total_profit': total_profit,
                'avg_margin': avg_margin,
                'num_sales': len(book_sales),
                'first_sale': first_sale.strftime("%d/%m/%Y") if first_sale else 'Never',
                'last_sale': last_sale.strftime("%d/%m/%Y") if last_sale else 'Never',
                'velocity': velocity  # Books sold per day
            })

        return result
