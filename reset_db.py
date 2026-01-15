"""
Reset database with fresh data from inventory.json
Run: uv run python reset_db.py
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from sqlmodel import Session

from src.data.database import DB_PATH, Book, Customer, QuickMessage, Sale, get_engine, init_db

# Path to inventory.json in project root
INVENTORY_JSON = Path(__file__).parent / "inventory.json"


def load_books_from_inventory() -> list[Book]:
    """Load books from inventory.json."""
    
    if not INVENTORY_JSON.exists():
        print(f"❌ inventory.json not found at: {INVENTORY_JSON}")
        print("📋 Please copy inventory.json to the root of this project")
        return []
    
    print(f"📖 Reading inventory from: {INVENTORY_JSON}")
    
    with open(INVENTORY_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    books = []
    for book_data in data.get('books', []):
        # Map category to genre
        category = book_data.get('category', 'Other')
        genre_map = {
            'Fiction': 'Fiction',
            'Non-fiction': 'Non-fiction',
            'Self-Help': 'Self-Help',
            'Islamic Studies': 'Religion',
        }
        genre = genre_map.get(category, 'Other')
        
        # Create Book object
        book = Book(
            id=book_data['id'],                    # BOOK-001, BOOK-002...
            title=book_data['name'],               # Arabic name
            author="",                             # Empty (fill later in UI)
            genre=genre,
            buy_price=0.0,                         # Empty (fill later)
            target_price=book_data.get('price', 15.99),  # Use Vinted price
            stock=1,                               # Default stock
            notes=f"ISBN: {book_data.get('isbn', 'N/A')}"
        )
        books.append(book)
    
    print(f"✅ Loaded {len(books)} books from inventory.json")
    return books


def reset_database():
    """Delete and recreate database with data from inventory.json."""
    
    print("🗑️  Deleting old database...")
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"   ✅ Deleted: {DB_PATH}")
    
    print("\n📦 Creating fresh database...")
    init_db()
    
    print("\n🎭 Adding data from inventory.json...")
    
    # Load books from inventory.json
    books = load_books_from_inventory()
    
    if not books:
        print("\n❌ No books loaded! Aborting.")
        return
    
    engine = get_engine()
    
    with Session(engine) as session:
        # ============================================================================
        # 1. CREATE CUSTOMERS (Sample data)
        # ============================================================================
        customers = [
            Customer(
                vinted_username="ahmed_m",
                name="Ahmed Mohamed",
                platform_preference="Vinted",
                notes="Regular customer"
            ),
            Customer(
                vinted_username="sara_ali",
                name="Sara Ali",
                platform_preference="Instagram",
                notes="Prefers Instagram"
            ),
            Customer(
                vinted_username="omar_h",
                name="Omar Hassan",
                platform_preference="Vinted",
                notes="Bulk buyer"
            ),
        ]
        session.add_all(customers)
        session.commit()
        for c in customers:
            session.refresh(c)
        print(f"   ✅ {len(customers)} customers created")
        
        # ============================================================================
        # 2. CREATE BOOKS FROM INVENTORY.JSON
        # ============================================================================
        session.add_all(books)
        session.commit()
        for b in books:
            session.refresh(b)
        print(f"   ✅ {len(books)} books created from inventory.json")
        
        # ============================================================================
        # 3. CREATE SAMPLE SALES (Optional - for demo purposes)
        # ============================================================================
        today = datetime.now()
        
        # Only create sales for first 3 books as example
        sales = [
            Sale(
                book_id=books[0].id,  # First book
                qty=1,
                price=14.99,
                packaging_per_book=1.0,
                total=14.99,
                customer_id=customers[0].id,
                platform="Vinted",
                date=(today - timedelta(days=5)).strftime("%Y-%m-%d"),
                bundle_id=None
            ),
            Sale(
                book_id=books[1].id,  # Second book
                qty=2,
                price=15.99,
                packaging_per_book=1.0,
                total=31.98,
                customer_id=customers[1].id,
                platform="Vinted",
                date=(today - timedelta(days=2)).strftime("%Y-%m-%d"),
                bundle_id=None
            ),
        ]
        
        session.add_all(sales)
        session.commit()
        print(f"   ✅ {len(sales)} sample sales created")
        
        # ============================================================================
        # 4. CREATE DEFAULT QUICK MESSAGES
        # ============================================================================
        from src.config import DEFAULT_QUICK_MESSAGES
        
        for i, (key, msg) in enumerate(DEFAULT_QUICK_MESSAGES.items()):
            quick_msg = QuickMessage(
                title=msg['title'],
                category=msg['category'],
                message=msg['message'],
                order_position=i
            )
            session.add(quick_msg)
        session.commit()
        print(f"   ✅ {len(DEFAULT_QUICK_MESSAGES)} quick messages created")
        
        # ============================================================================
        # SUMMARY
        # ============================================================================
        total_revenue = sum(s.total for s in sales)
        
        print(f"\n📊 Database Summary:")
        print(f"   📚 Books: {len(books)} total (from inventory.json)")
        print(f"   👥 Customers: {len(customers)}")
        print(f"   💰 Sales: {len(sales)} sample transactions")
        print(f"      └─ Revenue: €{total_revenue:.2f}")
        print(f"   💬 Quick Messages: {len(DEFAULT_QUICK_MESSAGES)}")
    
    print("\n✅ Database reset complete!")
    print(f"📂 Location: {DB_PATH}")
    print(f"\n📝 Next Steps:")
    print(f"   1. Run: streamlit run app.py")
    print(f"   2. Go to Inventory tab")
    print(f"   3. Fill in missing data:")
    print(f"      - Author names")
    print(f"      - Buy prices (what you paid)")
    print(f"      - Adjust stock quantities")
    print(f"\n🔄 To sync names back to Vinted bot:")
    print(f"   python sync_names_to_vinted.py")


if __name__ == "__main__":
    reset_database()