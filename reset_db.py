"""
Reset database with fresh data
Run: uv run python reset_db.py
"""

from pathlib import Path
from datetime import datetime, timedelta
from sqlmodel import Session
from src.data.database import Book, Sale, Customer, QuickMessage, get_engine, init_db, DB_PATH

def reset_database():
    """Delete and recreate database with mock data."""
    
    print("🗑️  Deleting old database...")
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"   ✅ Deleted: {DB_PATH}")
    
    print("\n📦 Creating fresh database...")
    init_db()
    
    print("\n🎭 Adding mock data...")
    
    engine = get_engine()
    
    with Session(engine) as session:
        # ============================================================================
        # 1. CREATE CUSTOMERS (Required for sales)
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
            Customer(
                vinted_username="labriji",
                name="Labriji",
                platform_preference="Vinted",
                notes="Bundle deals"
            ),
        ]
        session.add_all(customers)
        session.commit()
        for c in customers:
            session.refresh(c)
        print(f"   ✅ {len(customers)} customers created")
        
        # ============================================================================
        # 2. CREATE BOOKS
        # ============================================================================
        books = [
            # Active books (in stock)
            Book(
                title="ثلاثية غرناطة",
                author="رضوى عاشور",
                genre="Classic",
                buy_price=8.0,
                target_price=14.0,
                stock=3,
                notes="Popular trilogy"
            ),
            Book(
                title="الأب الغني والأب الفقير",
                author="روبرت كيوساكي",
                genre="Self-Help",
                buy_price=7.0,
                target_price=15.0,
                stock=2,
                notes="Finance classic"
            ),
            Book(
                title="مميز بالأصفر",
                author="ماجد عبدالله",
                genre="Self-Help",
                buy_price=8.0,
                target_price=16.0,
                stock=5,
                notes="Bestseller"
            ),
            Book(
                title="1984",
                author="George Orwell",
                genre="Classic",
                buy_price=6.0,
                target_price=12.0,
                stock=1,
                notes="Last copy!"
            ),
            Book(
                title="البؤساء",
                author="Victor Hugo",
                genre="Classic",
                buy_price=10.0,
                target_price=18.0,
                stock=2,
                notes="Les Misérables"
            ),
            Book(
                title="فن اللامبالاة",
                author="مارك مانسون",
                genre="Self-Help",
                buy_price=9.0,
                target_price=17.0,
                stock=4,
                notes="The Subtle Art"
            ),
            
            # Sold out books (stock = 0)
            Book(
                title="أرض زيكولا",
                author="عمرو عبد الحميد",
                genre="Fiction",
                buy_price=7.0,
                target_price=14.0,
                stock=0,
                notes="Sold out - popular"
            ),
            Book(
                title="في قلبي أنثى عبرية",
                author="خولة حمدي",
                genre="Romance",
                buy_price=6.0,
                target_price=13.0,
                stock=0,
                notes="Sold out"
            ),
            Book(
                title="أشياء جميلة",
                author="محمد السالم",
                genre="Self-Help",
                buy_price=5.0,
                target_price=11.0,
                stock=0,
                notes="Sold out"
            ),
            Book(
                title="test saad",
                author="Test Author",
                genre="Other",
                buy_price=5.0,
                target_price=10.0,
                stock=0,
                notes="Test book"
            ),
            Book(
                title="saad",
                author="Saad",
                genre="Other",
                buy_price=4.5,
                target_price=10.0,
                stock=0,
                notes="Test book 2"
            ),
        ]
        session.add_all(books)
        session.commit()
        for b in books:
            session.refresh(b)
        print(f"   ✅ {len(books)} books created")
        
        # ============================================================================
        # 3. CREATE SALES (with proper dates in YYYY-MM-DD format)
        # ============================================================================
        # Calculate dates relative to today
        today = datetime.now()
        
        sales = [
            # Sale 1: 10 days ago (outside weekly range)
            Sale(
                book_id=books[6].id,  # أرض زيكولا
                qty=2,
                price=14.0,
                packaging_per_book=1.0,
                total=28.0,
                customer_id=customers[0].id,  # Ahmed Mohamed
                platform="Vinted",
                date=(today - timedelta(days=10)).strftime("%Y-%m-%d"),
                bundle_id=None
            ),
            
            # Sale 2: 2 days ago (within weekly range)
            Sale(
                book_id=books[7].id,  # في قلبي أنثى عبرية
                qty=1,
                price=13.0,
                packaging_per_book=1.5,
                total=13.0,
                customer_id=customers[1].id,  # Sara Ali
                platform="Instagram",
                date=(today - timedelta(days=2)).strftime("%Y-%m-%d"),
                bundle_id=None
            ),
            
            # Sale 3: 1 day ago (test saad)
            Sale(
                book_id=books[9].id,  # test saad
                qty=9,
                price=10.0,
                packaging_per_book=1.0,
                total=90.0,
                customer_id=customers[2].id,  # Omar
                platform="Vinted",
                date=(today - timedelta(days=1)).strftime("%Y-%m-%d"),
                bundle_id=None
            ),
            
            # Bundle Sale: 1 day ago (2 books in bundle)
            Sale(
                book_id=books[8].id,  # أشياء جميلة
                qty=3,
                price=10.0,
                packaging_per_book=1.0,
                total=30.0,
                customer_id=customers[3].id,  # Labriji
                platform="Vinted",
                date=(today - timedelta(days=1)).strftime("%Y-%m-%d"),
                bundle_id="311b97"
            ),
            Sale(
                book_id=books[10].id,  # saad
                qty=2,
                price=10.0,
                packaging_per_book=1.0,
                total=20.0,
                customer_id=customers[3].id,  # Labriji
                platform="Vinted",
                date=(today - timedelta(days=1)).strftime("%Y-%m-%d"),
                bundle_id="311b97"
            ),
            
            # Sale 4: 1 day ago (saad - 10 books)
            Sale(
                book_id=books[10].id,  # saad
                qty=10,
                price=10.0,
                packaging_per_book=1.0,
                total=100.0,
                customer_id=customers[2].id,  # Omar
                platform="Vinted",
                date=(today - timedelta(days=1)).strftime("%Y-%m-%d"),
                bundle_id=None
            ),
            
            # Sale 5: Today (أشياء جميلة)
            Sale(
                book_id=books[8].id,  # أشياء جميلة
                qty=3,
                price=8.33,
                packaging_per_book=1.0,
                total=25.0,
                customer_id=customers[0].id,  # Ahmed
                platform="Vinted",
                date=today.strftime("%Y-%m-%d"),
                bundle_id=None
            ),
            
            # Sale 6: Today (البؤساء)
            Sale(
                book_id=books[4].id,  # البؤساء
                qty=1,
                price=18.0,
                packaging_per_book=1.0,
                total=18.0,
                customer_id=customers[2].id,  # Test
                platform="Vinted",
                date=today.strftime("%Y-%m-%d"),
                bundle_id=None
            ),
        ]
        
        session.add_all(sales)
        session.commit()
        print(f"   ✅ {len(sales)} sales created")
        
        # ============================================================================
        # 4. CREATE DEFAULT QUICK MESSAGES (if not exists)
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
        active = [b for b in books if b.stock > 0]
        sold = [b for b in books if b.stock == 0]
        
        total_revenue = sum(s.total for s in sales)
        total_profit = sum(
            (s.total - (s.packaging_per_book * s.qty) - (session.get(Book, s.book_id).buy_price * s.qty))
            for s in sales
        )
        
        print(f"\n📊 Database Summary:")
        print(f"   📚 Books: {len(books)} total")
        print(f"      ├─ 🟢 Active: {len(active)}")
        print(f"      └─ 🔴 Sold: {len(sold)}")
        print(f"   👥 Customers: {len(customers)}")
        print(f"   💰 Sales: {len(sales)} transactions")
        print(f"      ├─ Revenue: €{total_revenue:.2f}")
        print(f"      └─ Profit: €{total_profit:.2f}")
        print(f"   💬 Quick Messages: {len(DEFAULT_QUICK_MESSAGES)}")
    
    print("\n✅ Database reset complete!")
    print(f"📂 Location: {DB_PATH}")
    print(f"\n🚀 Run: streamlit run app.py")


if __name__ == "__main__":
    reset_database()