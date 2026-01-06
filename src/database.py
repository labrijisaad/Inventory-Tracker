"""
Midad Books - SQLite + SQLModel Database
With packaging costs and detailed logging
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select

# Database path
DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "midad.db"

print(f"📂 Database path: {DB_PATH}")


# ============================================================================
# ENUMS
# ============================================================================
class Platform(str, Enum):
    VINTED = "Vinted"
    INSTAGRAM = "Instagram"


class Genre(str, Enum):
    FICTION = "Fiction"
    SELF_HELP = "Self-Help"
    CLASSIC = "Classic"
    HORROR = "Horror"
    ROMANCE = "Romance"
    PHILOSOPHY = "Philosophy"
    RELIGION = "Religion"
    CHILDREN = "Children"
    OTHER = "Other"


# ============================================================================
# MODELS
# ============================================================================
class Book(SQLModel, table=True):
    """Book in inventory - status computed from stock."""
    id: Optional[int] = Field(default=None, primary_key=True)

    # Basic info
    title: str = Field(index=True)
    author: str = ""
    genre: str = Field(default=Genre.OTHER.value)

    # Pricing
    buy_price: float = Field(default=0, ge=0)  # What YOU paid
    target_price: float = Field(default=0, ge=0)  # Your goal price (reference only)

    # Inventory (SINGLE SOURCE OF TRUTH)
    stock: int = Field(default=1, ge=0)

    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    notes: str = ""

    # Relationship
    sales: list["Sale"] = Relationship(back_populates="book")
    
    @property
    def status(self) -> str:
        """Computed property - not stored in database."""
        return "Sold Out" if self.stock == 0 else "Active"
    
    @property
    def is_available(self) -> bool:
        """Can this book be sold?"""
        return self.stock > 0


class Sale(SQLModel, table=True):
    """Sale record with packaging costs."""
    id: Optional[int] = Field(default=None, primary_key=True)
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    qty: int = Field(default=1, ge=1)
    price: float = Field(ge=0)  # Price per book (total_paid / qty)
    packaging_per_book: float = Field(default=0, ge=0)  # Packaging cost per book
    total: float = Field(ge=0)  # Total customer paid
    customer: str
    platform: str = Field(default=Platform.VINTED.value)

    # Foreign key
    book_id: Optional[int] = Field(default=None, foreign_key="book.id")
    book: Optional[Book] = Relationship(back_populates="sales")


# ============================================================================
# DATABASE ENGINE
# ============================================================================
def get_engine():
    """Get or create database engine."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{DB_PATH}", echo=False)


def init_db():
    """Create tables."""
    print("🔧 Initializing database...")
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    print("✅ Database initialized")


# ============================================================================
# BOOK OPERATIONS
# ============================================================================
def get_books(filter_type: Optional[str] = None) -> list[dict]:
    """
    Get all books with COMPUTED status.
    
    Args:
        filter_type: "active" | "sold" | None
    """
    print(f"\n📚 get_books(filter_type={filter_type})")
    
    with Session(get_engine()) as session:
        query = select(Book).order_by(Book.id.desc())
        books = session.exec(query).all()
        
        print(f"   Found {len(books)} total books in database")
        
        result = []
        for b in books:
            # Compute status from stock
            status = "Sold Out" if b.stock == 0 else "Active"
            
            print(f"   Book #{b.id}: {b.title[:20]} | Stock: {b.stock} | Status: {status}")
            
            # Apply filter
            if filter_type == "active" and b.stock == 0:
                print(f"      ❌ Filtered out (sold)")
                continue
            if filter_type == "sold" and b.stock > 0:
                print(f"      ❌ Filtered out (active)")
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
        
        print(f"   Returning {len(result)} books after filter")
        return result


def save_books_bulk(books_data: list[dict], filter_type: Optional[str] = None) -> tuple[bool, str]:
    """Save multiple books."""
    print(f"\n💾 save_books_bulk(filter_type={filter_type}, {len(books_data)} books)")
    
    try:
        with Session(get_engine()) as session:
            # Get existing books in current filter
            query = select(Book)
            if filter_type == "active":
                query = query.where(Book.stock > 0)
            elif filter_type == "sold":
                query = query.where(Book.stock == 0)
            
            existing = {b.id: b for b in session.exec(query).all()}
            print(f"   Found {len(existing)} existing books in filter")
            processed_ids = set()
            
            for data in books_data:
                title = str(data.get("title", "")).strip()
                if not title:
                    continue
                
                book_id = data.get("id")
                is_existing = (
                    book_id is not None 
                    and not (isinstance(book_id, float) and pd.isna(book_id))
                    and int(book_id) in existing
                )
                
                if is_existing:
                    # UPDATE
                    book = existing[int(book_id)]
                    old_stock = book.stock
                    book.title = title
                    book.author = str(data.get("author", ""))
                    book.genre = str(data.get("genre", Genre.OTHER.value))
                    book.buy_price = max(0, float(data.get("buy_price", 0) or 0))
                    book.target_price = max(0, float(data.get("target_price", 0) or 0))
                    book.stock = max(0, int(data.get("stock", 0) or 0))
                    book.notes = str(data.get("notes", ""))
                    print(f"   UPDATE Book #{book_id}: {title[:20]} | Stock: {old_stock} → {book.stock}")
                    processed_ids.add(int(book_id))
                else:
                    # CREATE
                    new_stock = max(0, int(data.get("stock", 1) or 1))
                    book = Book(
                        title=title,
                        author=str(data.get("author", "")),
                        genre=str(data.get("genre", Genre.OTHER.value)),
                        buy_price=max(0, float(data.get("buy_price", 0) or 0)),
                        target_price=max(0, float(data.get("target_price", 0) or 0)),
                        stock=new_stock,
                        notes=str(data.get("notes", "")),
                    )
                    session.add(book)
                    print(f"   CREATE: {title[:20]} | Stock: {new_stock}")
            
            # DELETE removed books
            if filter_type:
                for book_id, book in existing.items():
                    if book_id not in processed_ids:
                        if len(book.sales) > 0:
                            return False, f"Cannot delete '{book.title}' - has sales history!"
                        session.delete(book)
                        print(f"   DELETE Book #{book_id}")
            
            session.commit()
            print("   ✅ Committed to database")
            return True, "✅ Saved successfully"
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False, f"Error: {str(e)}"


# ============================================================================
# SALE OPERATIONS
# ============================================================================
def get_sales() -> list[dict]:
    """Get all sales with book details."""
    print(f"\n💰 get_sales()")
    
    with Session(get_engine()) as session:
        sales = session.exec(select(Sale).order_by(Sale.id.desc())).all()
        print(f"   Found {len(sales)} sales")
        
        result = []
        for s in sales:
            book = session.get(Book, s.book_id) if s.book_id else None
            print(f"   Sale #{s.id}: Book #{s.book_id} ({book.title if book else 'Unknown'}) | Qty: {s.qty} | Total: €{s.total}")
            result.append({
                "id": s.id,
                "date": s.date,
                "qty": s.qty,
                "price": s.price,
                "packaging_per_book": s.packaging_per_book,
                "total": s.total,
                "customer": s.customer,
                "platform": s.platform,
                "book_id": s.book_id,
                "book_title": book.title if book else "Unknown",
            })
        
        return result


def add_sale(
    book_id: int, 
    qty: int, 
    total_paid: float, 
    packaging_per_book: float,
    customer: str, 
    platform: str
) -> tuple[bool, str]:
    """
    Record sale with packaging costs.
    
    Args:
        book_id: Book to sell
        qty: Quantity
        total_paid: Total amount customer paid
        packaging_per_book: Packaging cost per book
        customer: Customer name
        platform: Vinted or Instagram
    
    Returns:
        (success, message)
    """
    print(f"\n🔥 add_sale(book_id={book_id}, qty={qty}, total_paid={total_paid}, packaging={packaging_per_book}, customer={customer}, platform={platform})")
    
    # Validations
    if qty < 1:
        print("   ❌ Quantity < 1")
        return False, "❌ Quantity must be at least 1"
    
    if total_paid < 0:
        print("   ❌ Total paid < 0")
        return False, "❌ Total paid must be positive"
    
    if packaging_per_book < 0:
        print("   ❌ Packaging < 0")
        return False, "❌ Packaging must be positive"
    
    if not customer.strip():
        print("   ❌ No customer name")
        return False, "❌ Customer name required"
    
    try:
        with Session(get_engine()) as session:
            # Get book
            print(f"   📖 Fetching book #{book_id} from database...")
            book = session.get(Book, book_id)
            
            if not book:
                print(f"   ❌ Book #{book_id} not found!")
                return False, "❌ Book not found"
            
            print(f"   ✅ Found: {book.title}")
            print(f"   📦 Current stock BEFORE sale: {book.stock}")
            
            # Verify stock
            if book.stock < qty:
                print(f"   ❌ Not enough stock! {book.stock} < {qty}")
                return False, f"❌ Not enough stock! Only {book.stock} available"
            
            # Calculate pricing
            price_per_book = total_paid / qty
            total_packaging = packaging_per_book * qty
            revenue = total_paid - total_packaging
            cost = book.buy_price * qty
            profit = revenue - cost
            
            print(f"   💰 Pricing breakdown:")
            print(f"      Total paid: €{total_paid:.2f}")
            print(f"      Price per book: €{price_per_book:.2f}")
            print(f"      Packaging total: €{total_packaging:.2f}")
            print(f"      Revenue (after packaging): €{revenue:.2f}")
            print(f"      Cost (buy price × qty): €{cost:.2f}")
            print(f"      Profit: €{profit:.2f}")
            
            if profit < 0:
                print(f"      ⚠️ WARNING: Selling at a LOSS!")
            
            # Create sale record
            print(f"   💾 Creating sale record...")
            sale = Sale(
                book_id=book_id,
                qty=qty,
                price=price_per_book,
                packaging_per_book=packaging_per_book,
                total=total_paid,
                customer=customer.strip(),
                platform=platform,
            )
            session.add(sale)
            print(f"   ✅ Sale record created")
            
            # REDUCE STOCK
            old_stock = book.stock
            book.stock = book.stock - qty
            print(f"   🔥 REDUCING STOCK: {old_stock} - {qty} = {book.stock}")
            
            # Commit transaction
            print(f"   💾 Committing transaction...")
            session.commit()
            print(f"   ✅ Transaction committed!")
            
            # Verify it worked
            session.refresh(book)
            print(f"   🔍 Verification: Book stock after commit = {book.stock}")
            
            new_status = "Sold Out" if book.stock == 0 else "Active"
            
            msg = f"✅ Sold {qty}x '{book.title}' for €{total_paid:.2f} | Profit: €{profit:.2f} | New stock: {book.stock} ({new_status})"
            print(f"   {msg}")
            
            return True, msg
            
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False, f"❌ Error: {str(e)}"


def delete_sale(sale_id: int) -> tuple[bool, str]:
    """Delete sale and restore stock."""
    print(f"\n🗑️ delete_sale(sale_id={sale_id})")
    
    try:
        with Session(get_engine()) as session:
            sale = session.get(Sale, sale_id)
            if not sale:
                print(f"   ❌ Sale #{sale_id} not found")
                return False, "❌ Sale not found"
            
            print(f"   Found sale: {sale.qty}x Book #{sale.book_id}")
            
            # Restore stock
            book = session.get(Book, sale.book_id)
            if book:
                old_stock = book.stock
                book.stock = book.stock + sale.qty
                print(f"   📦 Restoring stock: {old_stock} + {sale.qty} = {book.stock}")
            
            session.delete(sale)
            session.commit()
            print(f"   ✅ Sale deleted, stock restored")
            
            return True, f"✅ Sale deleted, stock restored to {book.stock}"
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False, f"❌ Error: {str(e)}"


# ============================================================================
# ANALYTICS
# ============================================================================
def get_stats() -> dict:
    """Calculate statistics with packaging costs."""
    with Session(get_engine()) as session:
        books = list(session.exec(select(Book)).all())
        sales = list(session.exec(select(Sale)).all())
        
        # Compute status from stock
        active_books = [b for b in books if b.stock > 0]
        sold_books = [b for b in books if b.stock == 0]
        
        total_stock = sum(b.stock for b in books)
        stock_value = sum(b.stock * b.buy_price for b in books)
        potential_revenue = sum(b.stock * b.target_price for b in books if b.target_price > 0)
        
        # Sales metrics with packaging
        revenue = 0
        total_packaging = 0
        items_sold = 0
        cogs = 0
        
        for sale in sales:
            items_sold += sale.qty
            revenue += sale.total
            packaging_cost = sale.packaging_per_book * sale.qty
            total_packaging += packaging_cost
            
            # COGS
            book = session.get(Book, sale.book_id)
            if book:
                cogs += sale.qty * book.buy_price
        
        # Profit = Revenue - Packaging - COGS
        net_revenue = revenue - total_packaging
        profit = net_revenue - cogs
        
        # Platform breakdown
        platform_sales = {}
        for sale in sales:
            platform_sales[sale.platform] = platform_sales.get(sale.platform, 0) + sale.total
        
        # Low margin books
        low_margin_books = [
            {"title": b.title, "buy": b.buy_price, "target": b.target_price}
            for b in active_books 
            if b.target_price > 0 and b.target_price < b.buy_price
        ]
        
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
        }