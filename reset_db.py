"""
Reset/Initialize database with data from inventory.json
Works in both development and production environments
Automatically detects environment and database location
"""

import json
import os
from pathlib import Path

from sqlmodel import Session

from src.data.database import DB_PATH, Book, Customer, QuickMessage, get_engine, init_db

# Path to inventory.json
INVENTORY_JSON = Path(__file__).parent / "inventory.json"

# Detect environment
IS_PRODUCTION = os.getenv('PRODUCTION') == 'true'

# Defaults
DEFAULT_BUY_PRICE = 2.50  # €2.50


def confirm_reset():
    """Ask for confirmation before resetting database."""

    if DB_PATH.exists():
        db_size = DB_PATH.stat().st_size / (1024 * 1024)  # MB

        print(f"\n{'='*60}")
        print(f"📂 Database: {DB_PATH}")
        print(f"📦 Size: {db_size:.2f} MB")
        print(f"🌍 Environment: {'PRODUCTION ⚠️' if IS_PRODUCTION else 'DEVELOPMENT'}")
        print(f"{'='*60}\n")

        if IS_PRODUCTION:
            print("🚨 WARNING: You are in PRODUCTION mode!")
            print("   This will DELETE all real customer data!")
            print("   Are you ABSOLUTELY sure?\n")
            response = input("   Type 'YES DELETE PRODUCTION' to confirm: ")
            return response == "YES DELETE PRODUCTION"
        else:
            response = input("Delete existing database and recreate? (yes/no): ")
            return response.lower() == 'yes'

    # No database exists, safe to create
    return True


def map_genre(category: str, genre_field: str = None) -> str:
    """
    Map inventory.json category/genre to database genre.
    
    Simplified genres: Fiction, Non-fiction, Other
    
    Priority:
    1. Use 'genre' field if present
    2. Map 'category' field if genre missing
    3. Default to 'Other'
    """

    # If explicit genre field provided, use it
    if genre_field:
        genre_normalized = genre_field.strip().lower()
        if 'fiction' in genre_normalized and 'non' not in genre_normalized:
            return 'Fiction'
        elif 'non-fiction' in genre_normalized or 'nonfiction' in genre_normalized:
            return 'Non-fiction'
        else:
            return genre_field.strip()  # Use as-is if already simple

    # Otherwise, map from category
    category_lower = category.lower()

    # Fiction categories
    fiction_keywords = ['fiction', 'novel', 'romance', 'thriller', 'mystery', 'fantasy', 'sci-fi']
    if any(keyword in category_lower for keyword in fiction_keywords):
        if 'non' not in category_lower:  # Avoid "non-fiction"
            return 'Fiction'

    # Non-fiction categories
    nonfiction_keywords = [
        'non-fiction', 'nonfiction', 'self-help', 'psychology', 'biography',
        'history', 'philosophy', 'religion', 'islamic', 'business',
        'science', 'education', 'development'
    ]
    if any(keyword in category_lower for keyword in nonfiction_keywords):
        return 'Non-fiction'

    # Default
    return 'Other'


def load_books_from_inventory() -> list[Book]:
    """Load books from inventory.json."""

    if not INVENTORY_JSON.exists():
        print(f"\n❌ inventory.json not found at: {INVENTORY_JSON}")
        print("📋 Please ensure inventory.json is in the project root")
        return []

    print(f"📖 Reading inventory from: {INVENTORY_JSON}")

    try:
        with open(INVENTORY_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading inventory.json: {e}")
        return []

    books = []
    stats = {'fiction': 0, 'non_fiction': 0, 'other': 0}

    for book_data in data.get('books', []):
        # Get genre (with fallback to category)
        category = book_data.get('category', 'Other')
        genre_field = book_data.get('genre', None)
        genre = map_genre(category, genre_field)

        # Track stats
        if genre == 'Fiction':
            stats['fiction'] += 1
        elif genre == 'Non-fiction':
            stats['non_fiction'] += 1
        else:
            stats['other'] += 1

        # Get buy price (default to €2.50)
        buy_price = book_data.get('buy_price', DEFAULT_BUY_PRICE)

        # Get stock (default to 1)
        stock = book_data.get('stock', 1)

        # Create Book object
        book = Book(
            id=book_data['id'],
            title=book_data['name'],
            author=book_data.get('author', ''),
            genre=genre,
            buy_price=buy_price,
            target_price=book_data.get('price', 15.99),
            stock=stock,
            notes=f"ISBN: {book_data.get('isbn', 'N/A')}"
        )
        books.append(book)

    print(f"✅ Loaded {len(books)} books from inventory.json")
    print(f"   📖 Fiction: {stats['fiction']}")
    print(f"   📚 Non-fiction: {stats['non_fiction']}")
    print(f"   📦 Other: {stats['other']}\n")

    return books


def reset_database():
    """Delete and recreate database with data from inventory.json."""

    # Show banner
    print("\n" + "="*60)
    print(" 🗄️  MIDAD BOOKS - DATABASE RESET")
    print("="*60)

    # Confirm reset
    if not confirm_reset():
        print("\n❌ Database reset cancelled\n")
        return

    # Delete old database
    print("\n🗑️  Deleting old database...")
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"   ✅ Deleted: {DB_PATH}")

    # Create new database
    print("\n📦 Creating fresh database...")
    init_db()
    print("   ✅ Tables created")

    # Load books from inventory.json
    print("\n📚 Loading books from inventory.json...")
    books = load_books_from_inventory()

    if not books:
        print("\n⚠️  WARNING: No books loaded!")
        print("   Database will be empty (only default messages)")
        response = input("\nContinue anyway? (yes/no): ")
        if response.lower() != 'yes':
            print("\n❌ Aborted\n")
            return

    # Populate database
    engine = get_engine()

    with Session(engine) as session:
        # Add books
        if books:
            session.add_all(books)
            session.commit()
            print(f"   ✅ Added {len(books)} books")

        # Add sample customer (only in dev mode)
        if not IS_PRODUCTION:
            sample_customer = Customer(
                vinted_username="test_user",
                name="Test Customer",
                platform_preference="Vinted",
                notes="Sample customer for testing"
            )
            session.add(sample_customer)
            session.commit()
            print("   ✅ Added sample customer")

        # Add default quick messages
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
        print(f"   ✅ Added {len(DEFAULT_QUICK_MESSAGES)} quick messages")

    # Success message
    print("\n" + "="*60)
    print("✅ DATABASE RESET COMPLETE!")
    print("="*60)
    print(f"\n📂 Location: {DB_PATH}")
    print(f"📊 Books: {len(books)}")
    print(f"💰 Default buy price: €{DEFAULT_BUY_PRICE:.2f}")

    if IS_PRODUCTION:
        print("\n🚨 PRODUCTION DATABASE INITIALIZED")
        print("   Next steps:")
        print("   1. Review data in the app")
        print("   2. Commit to git: git add data/midad.db && git commit -m 'db: reset'")
        print("   3. Push to GitHub: git push origin main")
    else:
        print("\n📝 Next steps:")
        print("   1. Run: uv run streamlit run app.py")
        print("   2. Go to Inventory tab")
        print("   3. Fill in missing data:")
        print("      - Authors (if not in inventory.json)")
        print("      - Buy prices (default: €2.50)")
        print("      - Stock quantities")

    print()


if __name__ == "__main__":
    try:
        reset_database()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user\n")
    except Exception as e:
        print(f"\n\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
