"""
Import Sales Data - Keeps Existing Inventory
Adds 36 historical sales and auto-updates stock levels
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data.database import add_sale, get_books, init_db

# Initialize database
init_db()

# ============================================================================
# BOOK TITLE MAPPING (Spreadsheet → Database)
# ============================================================================

TITLE_MAPPING = {
    'فن اللامبالاة': 'BOOK-001',
    'جلسات نفسية': 'BOOK-043',
    'أحببت وغدا': 'BOOK-002',
    'الأب الغني الأب الفقير': 'BOOK-003',
    'أول مرة أتدبر القران': 'BOOK-004',
    'عقدك النفسية': 'BOOK-005',
    'كل السماء ازرق': 'BOOK-006',
    'ثلاثية غرناطة': 'BOOK-007',
    'هلكوت': 'BOOK-008',
    'قواعد العشق': 'BOOK-044',
    'الخيميائي': 'BOOK-009',
    'الاخوة كارامازوف': 'BOOK-010',
    'الجريمة و العقاب': 'BOOK-011',
    'التحول': 'BOOK-012',
    'لأنها كيارا': 'BOOK-013',
    'سيكولوجية المال': 'BOOK-014',
    'مميز بالأصفر': 'BOOK-045',
}

# ============================================================================
# SALES DATA (Only rows with sale dates - 36 sales total)
# ============================================================================

SALES_DATA = [
    # Format: (book_title, qty, sold_price, sale_date, customer_name, customer_username)
    
    # فن اللامبالاة (4 sales)
    ('فن اللامبالاة', 1, 10.00, '2026-01-03', 'Ahmed', 'ahmed_vinted'),
    ('فن اللامبالاة', 1, 12.00, '2026-01-04', 'Sara', 'sara_m'),
    ('فن اللامبالاة', 1, 10.00, '2026-01-05', 'Karim', 'karim23'),
    ('فن اللامبالاة', 1, 12.00, '2026-01-14', 'lil1478', 'lil1478'),
    
    # جلسات نفسية (2 sales)
    ('جلسات نفسية', 1, 12.00, '2026-01-02', 'Fatima', 'fatima_z'),
    ('جلسات نفسية', 1, 11.00, '2026-01-08', 'Customer 22', 'customer22'),
    
    # أحببت وغدا (4 sales)
    ('أحببت وغدا', 1, 12.50, '2026-01-12', 'Customer 5', 'customer5'),
    ('أحببت وغدا', 1, 11.00, '2026-01-08', 'Customer 20', 'customer20'),
    ('أحببت وغدا', 1, 10.00, '2026-01-07', 'Customer 18', 'customer18'),
    ('أحببت وغدا', 1, 10.00, '2026-01-06', 'nabila93380', 'nabila93380'),
    
    # الأب الغني الأب الفقير (3 sales)
    ('الأب الغني الأب الفقير', 1, 10.00, '2026-01-03', 'Omar', 'omar_k'),
    ('الأب الغني الأب الفقير', 1, 10.00, '2026-01-05', 'Customer 7', 'customer7'),
    ('الأب الغني الأب الفقير', 1, 12.00, '2026-01-11', 'grave2017', 'grave2017'),
    
    # أول مرة أتدبر القران (2 sales)
    ('أول مرة أتدبر القران', 1, 13.00, '2026-01-07', 'mina773', 'mina773'),
    ('أول مرة أتدبر القران', 1, 12.75, '2026-01-10', 'mia___sd', 'mia___sd'),
    
    # عقدك النفسية (4 sales)
    ('عقدك النفسية', 1, 10.00, '2026-01-05', 'Customer 11', 'customer11'),
    ('عقدك النفسية', 1, 10.00, '2026-01-06', 'Customer 14', 'customer14'),
    ('عقدك النفسية', 1, 11.00, '2026-01-08', 'Customer 21', 'customer21'),
    ('عقدك النفسية', 1, 12.50, '2026-01-12', 'Customer 8', 'customer8'),
    
    # كل السماء ازرق (1 sale)
    ('كل السماء ازرق', 1, 12.00, '2026-01-01', 'Customer 9', 'customer9'),
    
    # ثلاثية غرناطة (2 sales)
    ('ثلاثية غرناطة', 1, 11.80, '2026-01-07', 'Customer 10', 'customer10'),
    ('ثلاثية غرناطة', 1, 10.50, '2026-01-08', 'douddi', 'douddi'),
    
    # قواعد العشق (2 sales)
    ('قواعد العشق', 1, 11.80, '2026-01-07', 'Customer 11', 'customer11b'),
    ('قواعد العشق', 1, 10.00, '2026-01-06', 'Customer 15', 'customer15'),
    
    # الخيميائي (2 sales)
    ('الخيميائي', 1, 11.00, '2026-01-04', 'Customer 12', 'customer12'),
    ('الخيميائي', 1, 11.50, '2026-01-10', 'silviatiken', 'silviatiken'),
    
    # الجريمة و العقاب (3 bundle sales - qty=2 each)
    ('الجريمة و العقاب', 2, 24.00, '2026-01-03', 'Customer 6', 'customer6'),
    ('الجريمة و العقاب', 2, 24.00, '2026-01-03', 'judyy.hd', 'judyy.hd'),
    ('الجريمة و العقاب', 2, 25.50, '2026-01-08', 'zyaddxt', 'zyaddxt'),
    
    # لأنها كيارا (1 sale)
    ('لأنها كيارا', 1, 12.00, '2026-01-01', 'Customer 13', 'customer13'),
    
    # سيكولوجية المال (2 sales)
    ('سيكولوجية المال', 1, 12.00, '2026-01-01', 'Customer 14', 'customer14b'),
    ('سيكولوجية المال', 1, 10.00, '2026-01-05', 'hanane2929', 'hanane2929'),
    
    # مميز بالأصفر (1 sale)
    ('مميز بالأصفر', 1, 13.00, '2026-01-06', 'thaynamoon', 'thaynamoon'),
]


def import_sales():
    """Import all 36 sales from spreadsheet."""
    print("="*70)
    print("📚 MIDAD BOOKS - SALES IMPORT")
    print("="*70)
    print("\n🚀 Starting import of 36 historical sales...\n")
    
    # Get current books to verify stock
    all_books = get_books()
    book_dict = {b['id']: b for b in all_books}
    
    print("📦 Current Stock Levels:")
    print("-" * 70)
    for book_id in sorted(TITLE_MAPPING.values()):
        if book_id in book_dict:
            book = book_dict[book_id]
            print(f"  {book_id}: {book['title'][:40]:.<40} Stock: {book['stock']}")
    print()
    
    # Counters
    success_count = 0
    error_count = 0
    errors = []
    
    # Import each sale
    print("\n📥 Importing Sales:")
    print("-" * 70)
    
    for i, (book_title, qty, sold_price, sale_date, customer_name, customer_username) in enumerate(SALES_DATA, 1):
        # Get book ID
        book_id = TITLE_MAPPING.get(book_title)
        
        if not book_id:
            error_msg = f"❌ [{i:02d}/36] Book not found: {book_title}"
            print(error_msg)
            errors.append(error_msg)
            error_count += 1
            continue
        
        # Get book details
        book = book_dict.get(book_id)
        if not book:
            error_msg = f"❌ [{i:02d}/36] Book ID {book_id} not in database"
            print(error_msg)
            errors.append(error_msg)
            error_count += 1
            continue
        
        # Check stock
        if book['stock'] < qty:
            error_msg = f"⚠️ [{i:02d}/36] {book_title[:25]:.<25} → Not enough stock! (Need {qty}, have {book['stock']})"
            print(error_msg)
            errors.append(error_msg)
            error_count += 1
            continue
        
        # Add sale
        print(f"✅ [{i:02d}/36] {book_title[:30]:.<30} → €{sold_price:.2f} on {sale_date[5:]} ({customer_name[:15]})")
        
        success, msg = add_sale(
            book_id=book_id,
            qty=qty,
            total_paid=sold_price,
            packaging_per_book=0.45,  # Standard packaging cost
            customer_name=customer_name,
            customer_username=customer_username,
            platform='Vinted',
            sale_date=sale_date
        )
        
        if success:
            success_count += 1
            # Update local book dict to track stock changes
            book['stock'] -= qty
        else:
            error_msg = f"  ❌ Error: {msg}"
            print(error_msg)
            errors.append(error_msg)
            error_count += 1
    
    # Final Summary
    print("\n" + "="*70)
    print("📊 IMPORT SUMMARY")
    print("="*70)
    print(f"✅ Successful Sales: {success_count}/36")
    print(f"❌ Failed Sales: {error_count}/36")
    print(f"💰 Expected Revenue: €410.85")
    
    # Show updated stock levels
    print("\n📦 Updated Stock Levels:")
    print("-" * 70)
    fresh_books = get_books()
    book_dict_updated = {b['id']: b for b in fresh_books}
    
    for book_id in sorted(TITLE_MAPPING.values()):
        if book_id in book_dict_updated:
            book = book_dict_updated[book_id]
            status = "✅ In Stock" if book['stock'] > 0 else "❌ Sold Out"
            print(f"  {book_id}: {book['title'][:35]:.<35} Stock: {book['stock']:>2} {status}")
    
    # Show errors if any
    if errors:
        print("\n⚠️ ERRORS ENCOUNTERED:")
        print("-" * 70)
        for error in errors:
            print(f"  {error}")
    
    print("\n✨ Import Complete!")
    print("="*70)
    
    # Verification tips
    print("\n💡 NEXT STEPS:")
    print("  1. Run: streamlit run app.py")
    print("  2. Go to 📊 Analytics page")
    print("  3. Verify: Revenue = €410.85")
    print("  4. Check: 36 sales total")
    print()


if __name__ == "__main__":
    try:
        import_sales()
    except KeyboardInterrupt:
        print("\n\n⚠️ Import cancelled by user")
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()