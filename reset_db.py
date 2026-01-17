"""
Reset/Initialize database with data from inventory.json
Works in both development and production environments
Automatically detects environment and database location

NEW FEATURES:
- Automatic backup before reset
- Dry-run mode (preview without committing)
- Data validation
- Post-import report
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, select

from src.data.database import DB_PATH, Book, Customer, QuickMessage, get_engine, init_db

# Path to inventory.json
INVENTORY_JSON = Path(__file__).parent / "inventory.json"

# Backup directory
BACKUP_DIR = Path(__file__).parent / "data" / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Detect environment
IS_PRODUCTION = os.getenv('PRODUCTION') == 'true'

# Defaults
DEFAULT_BUY_PRICE = 2.50  # €2.50
DEFAULT_STOCK = 1  # 1 copy per book by default


def backup_database():
    """Create backup of existing database."""
    if not DB_PATH.exists():
        print("ℹ️  No existing database to backup")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"midad_backup_{timestamp}.db"
    backup_path = BACKUP_DIR / backup_name

    try:
        shutil.copy2(DB_PATH, backup_path)
        backup_size = backup_path.stat().st_size / (1024 * 1024)  # MB
        print(f"✅ Backup created: {backup_path}")
        print(f"   Size: {backup_size:.2f} MB")
        return backup_path
    except Exception as e:
        print(f"⚠️  Backup failed: {e}")
        return None


def confirm_reset():
    """Ask for confirmation before resetting database."""

    print(f"\n{'='*60}")
    print(f"📂 Database: {DB_PATH}")

    if DB_PATH.exists():
        db_size = DB_PATH.stat().st_size / (1024 * 1024)  # MB
        print(f"📦 Current Size: {db_size:.2f} MB")

        # Show current stats
        try:
            engine = get_engine()
            with Session(engine) as session:
                book_count = len(session.exec(select(Book)).all())
                customer_count = len(session.exec(select(Customer)).all())
                print(f"📚 Current Books: {book_count}")
                print(f"👥 Current Customers: {customer_count}")
        except:
            pass
    else:
        print("📦 Status: No database exists (will create new)")

    print(f"🌍 Environment: {'PRODUCTION ⚠️' if IS_PRODUCTION else 'DEVELOPMENT'}")
    print(f"{'='*60}\n")

    if IS_PRODUCTION:
        print("🚨 WARNING: You are in PRODUCTION mode!")
        print("   This will DELETE all real data (books, customers, sales)!")
        print("   A backup will be created automatically.\n")
        response = input("   Type 'YES DELETE PRODUCTION' to confirm: ")
        return response == "YES DELETE PRODUCTION"
    else:
        response = input("Delete existing database and recreate? (yes/no): ")
        return response.lower() == 'yes'


def map_genre(category: str, genre_field: str = None) -> str:
    """
    Map inventory.json category/genre to database genre.
    
    Supported genres:
    - Fiction
    - Non-fiction
    - Self-Help
    - Religion
    - Classic
    - Romance
    - Poetry
    - Biography
    - History
    - Philosophy
    - Other
    """

    # If explicit genre field provided, use it
    if genre_field:
        genre_normalized = genre_field.strip()

        # Map common variations
        genre_map = {
            'fiction': 'Fiction',
            'non-fiction': 'Non-fiction',
            'nonfiction': 'Non-fiction',
            'self-help': 'Self-Help',
            'selfhelp': 'Self-Help',
            'religion': 'Religion',
            'religious': 'Religion',
            'islamic': 'Religion',
            'classic': 'Classic',
            'classics': 'Classic',
            'romance': 'Romance',
            'poetry': 'Poetry',
            'poem': 'Poetry',
            'biography': 'Biography',
            'bio': 'Biography',
            'history': 'History',
            'historical': 'History',
            'philosophy': 'Philosophy',
        }

        genre_lower = genre_normalized.lower()
        if genre_lower in genre_map:
            return genre_map[genre_lower]

        # Return as-is if already valid
        return genre_normalized

    # Map from category
    category_lower = category.lower()

    # Fiction
    if any(word in category_lower for word in ['fiction', 'novel', 'story']) and 'non' not in category_lower:
        return 'Fiction'

    # Non-fiction
    if any(word in category_lower for word in ['non-fiction', 'nonfiction']):
        return 'Non-fiction'

    # Self-Help
    if any(word in category_lower for word in ['self-help', 'selfhelp', 'personal development', 'psychology']):
        return 'Self-Help'

    # Religion
    if any(word in category_lower for word in ['religion', 'islamic', 'quran', 'spiritual']):
        return 'Religion'

    # Other categories
    if 'classic' in category_lower:
        return 'Classic'
    if 'romance' in category_lower:
        return 'Romance'
    if 'poetry' in category_lower or 'poem' in category_lower:
        return 'Poetry'
    if 'biography' in category_lower or 'bio' in category_lower:
        return 'Biography'
    if 'history' in category_lower or 'historical' in category_lower:
        return 'History'
    if 'philosophy' in category_lower:
        return 'Philosophy'

    return 'Other'


def validate_book_data(book_data: dict, index: int) -> tuple[bool, str]:
    """Validate book data from inventory.json."""

    # Required fields
    if 'id' not in book_data:
        return False, f"Book #{index}: Missing 'id' field"

    if 'name' not in book_data or not book_data['name'].strip():
        return False, f"Book {book_data.get('id', index)}: Missing or empty 'name'"

    # Validate ID format (should be BOOK-XXX)
    book_id = book_data['id']
    if not book_id.startswith('BOOK-'):
        return False, f"Book {book_id}: Invalid ID format (should start with 'BOOK-')"

    # Validate prices
    if 'price' in book_data:
        try:
            price = float(book_data['price'])
            if price < 0:
                return False, f"Book {book_id}: Negative price ({price})"
        except ValueError:
            return False, f"Book {book_id}: Invalid price format"

    if 'buy_price' in book_data:
        try:
            buy_price = float(book_data['buy_price'])
            if buy_price < 0:
                return False, f"Book {book_id}: Negative buy_price ({buy_price})"
        except ValueError:
            return False, f"Book {book_id}: Invalid buy_price format"

    # Validate stock
    if 'stock' in book_data:
        try:
            stock = int(book_data['stock'])
            if stock < 0:
                return False, f"Book {book_id}: Negative stock ({stock})"
        except ValueError:
            return False, f"Book {book_id}: Invalid stock format (must be integer)"

    return True, "OK"


def load_books_from_inventory(dry_run=False) -> tuple[list[Book], dict]:
    """
    Load books from inventory.json.
    
    Args:
        dry_run: If True, only validate without creating Book objects
    
    Returns:
        (books, stats)
    """

    if not INVENTORY_JSON.exists():
        print(f"\n❌ inventory.json not found at: {INVENTORY_JSON}")
        print("📋 Please ensure inventory.json is in the project root")
        return [], {}

    print(f"📖 Reading inventory from: {INVENTORY_JSON}")

    try:
        with open(INVENTORY_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return [], {}
    except Exception as e:
        print(f"❌ Error reading inventory.json: {e}")
        return [], {}

    books_data = data.get('books', [])

    if not books_data:
        print("⚠️  Warning: 'books' array is empty in inventory.json")
        return [], {}

    print(f"📊 Found {len(books_data)} books in inventory.json")

    # Validate all books first
    print("\n🔍 Validating data...")
    validation_errors = []

    for i, book_data in enumerate(books_data, 1):
        is_valid, error_msg = validate_book_data(book_data, i)
        if not is_valid:
            validation_errors.append(error_msg)

    if validation_errors:
        print(f"\n❌ Found {len(validation_errors)} validation error(s):")
        for error in validation_errors[:10]:  # Show first 10
            print(f"   • {error}")
        if len(validation_errors) > 10:
            print(f"   ... and {len(validation_errors) - 10} more")
        return [], {}

    print("✅ All data validated successfully")

    # If dry run, stop here
    if dry_run:
        return [], {
            'total': len(books_data),
            'validated': True
        }

    # Create Book objects
    books = []
    stats = {
        'total': 0,
        'by_genre': {},
        'with_buy_price': 0,
        'with_stock': 0,
        'total_stock': 0,
        'warnings': []
    }

    for book_data in books_data:
        # Get genre
        category = book_data.get('category', 'Other')
        genre_field = book_data.get('genre', None)
        genre = map_genre(category, genre_field)

        # Track genre stats
        stats['by_genre'][genre] = stats['by_genre'].get(genre, 0) + 1

        # Get buy price
        buy_price = book_data.get('buy_price', DEFAULT_BUY_PRICE)
        if 'buy_price' in book_data:
            stats['with_buy_price'] += 1

        # Get stock
        stock = book_data.get('stock', DEFAULT_STOCK)
        if 'stock' in book_data:
            stats['with_stock'] += 1
        stats['total_stock'] += stock

        # Get target price
        target_price = book_data.get('price', 0.0)

        # Warning if no target price
        if target_price == 0:
            stats['warnings'].append(f"{book_data['id']}: No target price set")

        # Create Book object
        book = Book(
            id=book_data['id'],
            title=book_data['name'],
            author=book_data.get('author', ''),
            genre=genre,
            buy_price=buy_price,
            target_price=target_price,
            stock=stock,
            notes=f"ISBN: {book_data.get('isbn', 'N/A')}"
        )
        books.append(book)
        stats['total'] += 1

    return books, stats


def preview_import():
    """Preview what will be imported without committing."""
    print("\n" + "="*60)
    print(" 👁️  PREVIEW MODE - No changes will be made")
    print("="*60)

    books, stats = load_books_from_inventory(dry_run=False)

    if not books:
        print("\n❌ No books to import")
        return False

    print("\n📊 Import Summary:")
    print(f"   Total books: {stats['total']}")
    print(f"   Total stock: {stats['total_stock']} copies")
    print("\n📚 By Genre:")
    for genre, count in sorted(stats['by_genre'].items()):
        print(f"   • {genre}: {count}")

    print("\n💰 Pricing:")
    print(f"   Books with buy price: {stats['with_buy_price']}/{stats['total']}")
    missing_buy = stats['total'] - stats['with_buy_price']
    if missing_buy > 0:
        print(f"   ⚠️  {missing_buy} will use default (€{DEFAULT_BUY_PRICE:.2f})")

    print("\n📦 Stock:")
    print(f"   Books with stock set: {stats['with_stock']}/{stats['total']}")
    missing_stock = stats['total'] - stats['with_stock']
    if missing_stock > 0:
        print(f"   ⚠️  {missing_stock} will use default ({DEFAULT_STOCK} copy)")

    if stats['warnings']:
        print(f"\n⚠️  Warnings ({len(stats['warnings'])}):")
        for warning in stats['warnings'][:5]:
            print(f"   • {warning}")
        if len(stats['warnings']) > 5:
            print(f"   ... and {len(stats['warnings']) - 5} more")

    print("\n" + "="*60)
    return True


def reset_database(dry_run=False):
    """Delete and recreate database with data from inventory.json."""

    # Show banner
    print("\n" + "="*60)
    print(f" 🗄️  MIDAD BOOKS - DATABASE {'PREVIEW' if dry_run else 'RESET'}")
    print("="*60)

    # Preview mode
    if dry_run:
        return preview_import()

    # Confirm reset
    if not confirm_reset():
        print("\n❌ Database reset cancelled\n")
        return

    # Backup existing database
    if DB_PATH.exists():
        print("\n💾 Creating backup...")
        backup_path = backup_database()
        if backup_path:
            print("   Keep this backup in case you need to restore!")

    # Delete old database
    print("\n🗑️  Deleting old database...")
    if DB_PATH.exists():
        # ✅ NEW: Close any open connections first
        from src.data.database import _engine

        if _engine is not None:
            _engine.dispose()
            print("   🔓 Closed database connections")

        # Try to delete with retries
        import time
        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                DB_PATH.unlink()
                print(f"   ✅ Deleted: {DB_PATH}")
                break
            except PermissionError:
                if attempt < max_attempts:
                    print(f"   ⚠️  Attempt {attempt}/{max_attempts} failed (file locked)")
                    print("      💡 Tip: Close Streamlit app if running")
                    print("      ⏳ Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    print("\n❌ Cannot delete database (file is locked by another process)")
                    print("\n🔧 Solutions:")
                    print("   1. Close Streamlit app (Ctrl+C in terminal)")
                    print("   2. Close any Python processes using the database")
                    print("   3. Restart your terminal/IDE")
                    print("\n   Then run: uv run python reset_db.py\n")
                    return

    # Create new database
    print("\n📦 Creating fresh database...")
    init_db()
    print("   ✅ Tables created")

    # Load books from inventory.json
    print("\n📚 Loading books from inventory.json...")
    books, stats = load_books_from_inventory(dry_run=False)

    if not books:
        print("\n⚠️  WARNING: No books loaded!")
        print("   Database will be empty (only default messages)")
        response = input("\nContinue anyway? (yes/no): ")
        if response.lower() != 'yes':
            print("\n❌ Aborted\n")
            return

    # Populate database
    engine = get_engine()

    print("\n💾 Populating database...")
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
    print(f"📚 Books: {stats['total']}")
    print(f"📦 Total Stock: {stats['total_stock']} copies")
    print("\n📊 By Genre:")
    for genre, count in sorted(stats['by_genre'].items()):
        print(f"   • {genre}: {count}")

    if stats['warnings']:
        print(f"\n⚠️  Please review {len(stats['warnings'])} warning(s) in the app")

    if IS_PRODUCTION:
        print("\n🚨 PRODUCTION DATABASE INITIALIZED")
        print("   Next steps:")
        print("   1. Run: uv run streamlit run app.py")
        print("   2. Review all data in Inventory tab")
        print("   3. Fill in missing buy prices and target prices")
        print("   4. Commit: git add data/midad.db && git commit -m 'db: production data'")
        print("   5. Push: git push origin main")
    else:
        print("\n📝 Next steps:")
        print("   1. Run: uv run streamlit run app.py")
        print("   2. Go to Inventory → Active Inventory tab")
        print("   3. Review and fill in missing data")

    print()


if __name__ == "__main__":
    import sys

    # Check for dry-run flag
    dry_run = '--preview' in sys.argv or '--dry-run' in sys.argv

    if dry_run:
        print("ℹ️  Running in PREVIEW mode (no changes will be made)\n")

    try:
        reset_database(dry_run=dry_run)
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user\n")
    except Exception as e:
        print(f"\n\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
