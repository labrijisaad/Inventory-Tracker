"""
Reset database and create fresh mock data
Run: uv run python reset_db.py
"""

from pathlib import Path
from datetime import datetime, timedelta
from sqlmodel import Session, select
from src.database import Book, Sale, Genre, Platform, get_engine, init_db, DATA_DIR, DB_PATH

def reset_database():
    """Delete and recreate database with realistic mock data."""
    
    print("🗑️  Deleting old database...")
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"   ✅ Deleted")
    
    print("\n📦 Creating fresh database...")
    init_db()
    
    print("\n🎭 Adding mock data...")
    
    engine = get_engine()
    
    with Session(engine) as session:
        # Create books (NO DUPLICATES)
        books = [
            Book(
                title="ثلاثية غرناطة", 
                author="رضوى عاشور", 
                genre=Genre.CLASSIC.value,
                buy_price=8, 
                target_price=14, 
                stock=3, 
                notes="Popular trilogy"
            ),
            
            Book(
                title="الأب الغني والأب الفقير", 
                author="روبرت كيوساكي", 
                genre=Genre.SELF_HELP.value,
                buy_price=7, 
                target_price=15, 
                stock=2
            ),
            
            Book(
                title="مميز بالأصفر", 
                author="ماجد عبدالله", 
                genre=Genre.SELF_HELP.value,
                buy_price=8, 
                target_price=16, 
                stock=5
            ),
            
            Book(
                title="1984", 
                author="George Orwell", 
                genre=Genre.CLASSIC.value,
                buy_price=6, 
                target_price=12, 
                stock=1
            ),
            
            Book(
                title="البؤساء", 
                author="Victor Hugo", 
                genre=Genre.CLASSIC.value,
                buy_price=10, 
                target_price=18, 
                stock=2
            ),
            
            Book(
                title="فن اللامبالاة", 
                author="مارك مانسون", 
                genre=Genre.SELF_HELP.value,
                buy_price=9, 
                target_price=17, 
                stock=4
            ),
            
            # Sold out books
            Book(
                title="أرض زيكولا", 
                author="عمرو عبد الحميد", 
                genre=Genre.FICTION.value,
                buy_price=7, 
                target_price=14, 
                stock=0, 
                notes="Completely sold out"
            ),
            
            Book(
                title="في قلبي أنثى عبرية", 
                author="خولة حمدي", 
                genre=Genre.ROMANCE.value,
                buy_price=6, 
                target_price=13, 
                stock=0
            ),
            
            Book(
                title="أشياء جميلة", 
                author="محمد السالم", 
                genre=Genre.SELF_HELP.value,
                buy_price=5, 
                target_price=11, 
                stock=0
            ),
        ]
        
        session.add_all(books)
        session.commit()
        
        # Refresh to get IDs
        for b in books:
            session.refresh(b)
        
        # Create sales with different dates (realistic timeline)
        base_date = datetime.now() - timedelta(days=15)
        
        sales = [
            Sale(
                book_id=books[6].id,  # أرض زيكولا
                qty=2, 
                price=14, 
                packaging_per_book=1.0, 
                total=28, 
                customer="Ahmed Mohamed", 
                platform=Platform.VINTED.value, 
                date=(base_date + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
            ),
            Sale(
                book_id=books[7].id,  # في قلبي أنثى عبرية
                qty=1, 
                price=13, 
                packaging_per_book=1.5, 
                total=13, 
                customer="Sara Ali", 
                platform=Platform.INSTAGRAM.value, 
                date=(base_date + timedelta(days=5)).strftime("%Y-%m-%d %H:%M")
            ),
            Sale(
                book_id=books[8].id,  # أشياء جميلة
                qty=3, 
                price=11, 
                packaging_per_book=1.0, 
                total=33, 
                customer="Omar Hassan", 
                platform=Platform.VINTED.value, 
                date=(base_date + timedelta(days=10)).strftime("%Y-%m-%d %H:%M")
            ),
        ]
        
        session.add_all(sales)
        session.commit()
        
        # Verify
        active = [b for b in books if b.stock > 0]
        sold = [b for b in books if b.stock == 0]
        
        print(f"   ✅ {len(books)} books created")
        print(f"   🟢 {len(active)} active")
        print(f"   🔴 {len(sold)} sold out")
        print(f"   💰 {len(sales)} sales")
        
        # Calculate stats
        total_revenue = sum(s.total for s in sales)
        print(f"\n📊 Summary:")
        print(f"   💰 Revenue: €{total_revenue:.2f}")
        print(f"   📦 Items sold: {sum(s.qty for s in sales)}")
    
    print("\n✅ Done! Run: uv run streamlit run app.py")


if __name__ == "__main__":
    reset_database()