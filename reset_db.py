"""
Reset database with updated schema (customer_id required)
Run: uv run python reset_db.py
"""

from pathlib import Path
from datetime import datetime, timedelta
from sqlmodel import Session
from src.database import Book, Sale, Customer, Genre, Platform, get_engine, init_db, DB_PATH

def reset_database():
    """Delete and recreate database."""
    
    print("🗑️  Deleting old database...")
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"   ✅ Deleted")
    
    print("\n📦 Creating fresh database...")
    init_db()
    
    print("\n🎭 Adding mock data...")
    
    engine = get_engine()
    
    with Session(engine) as session:
        # Create customers first (REQUIRED for sales)
        customers = [
            Customer(vinted_username="ahmed_m", name="Ahmed Mohamed", platform_preference=Platform.VINTED.value),
            Customer(vinted_username="sara_ali", name="Sara Ali", platform_preference=Platform.INSTAGRAM.value),
            Customer(vinted_username="omar_h", name="Omar Hassan", platform_preference=Platform.VINTED.value),
        ]
        session.add_all(customers)
        session.commit()
        for c in customers:
            session.refresh(c)
        print(f"   ✅ {len(customers)} customers created")
        
        # Create books
        books = [
            Book(title="ثلاثية غرناطة", author="رضوى عاشور", genre=Genre.CLASSIC.value, buy_price=8, target_price=14, stock=3),
            Book(title="الأب الغني والأب الفقير", author="روبرت كيوساكي", genre=Genre.SELF_HELP.value, buy_price=7, target_price=15, stock=2),
            Book(title="مميز بالأصفر", author="ماجد عبدالله", genre=Genre.SELF_HELP.value, buy_price=8, target_price=16, stock=5),
            Book(title="1984", author="George Orwell", genre=Genre.CLASSIC.value, buy_price=6, target_price=12, stock=1),
            Book(title="البؤساء", author="Victor Hugo", genre=Genre.CLASSIC.value, buy_price=10, target_price=18, stock=2),
            Book(title="فن اللامبالاة", author="مارك مانسون", genre=Genre.SELF_HELP.value, buy_price=9, target_price=17, stock=4),
            Book(title="أرض زيكولا", author="عمرو عبد الحميد", genre=Genre.FICTION.value, buy_price=7, target_price=14, stock=0),
            Book(title="في قلبي أنثى عبرية", author="خولة حمدي", genre=Genre.ROMANCE.value, buy_price=6, target_price=13, stock=0),
            Book(title="أشياء جميلة", author="محمد السالم", genre=Genre.SELF_HELP.value, buy_price=5, target_price=11, stock=0),
        ]
        session.add_all(books)
        session.commit()
        for b in books:
            session.refresh(b)
        print(f"   ✅ {len(books)} books created")
        
        # Create sales (customer_id now REQUIRED)
        base_date = datetime.now() - timedelta(days=10)
        
        sales = [
            # Single sales
            Sale(
                book_id=books[6].id, qty=2, price=14, packaging_per_book=1.0, total=28,
                customer_id=customers[0].id, platform=Platform.VINTED.value,
                date=(base_date + timedelta(days=1)).strftime("%Y-%m-%d 14:30")
            ),
            Sale(
                book_id=books[7].id, qty=1, price=13, packaging_per_book=1.5, total=13,
                customer_id=customers[1].id, platform=Platform.INSTAGRAM.value,
                date=(base_date + timedelta(days=5)).strftime("%Y-%m-%d 16:45")
            ),
            
            # Bundle sale (3 books)
            Sale(
                book_id=books[8].id, qty=3, price=11, packaging_per_book=1.0, total=33,
                customer_id=customers[2].id, platform=Platform.VINTED.value,
                date=(base_date + timedelta(days=8)).strftime("%Y-%m-%d 11:20"),
                bundle_id="bundle001"
            ),
        ]
        
        session.add_all(sales)
        session.commit()
        print(f"   ✅ {len(sales)} sales created")
        
        # Summary
        active = [b for b in books if b.stock > 0]
        sold = [b for b in books if b.stock == 0]
        
        print(f"\n📊 Summary:")
        print(f"   📚 Books: {len(books)} ({len(active)} active, {len(sold)} sold)")
        print(f"   👥 Customers: {len(customers)}")
        print(f"   💰 Sales: {len(sales)}")
    
    print("\n✅ Done! Run: uv run streamlit run app.py")


if __name__ == "__main__":
    reset_database()