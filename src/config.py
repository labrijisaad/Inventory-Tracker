"""
Application configuration.
Midad Books - كتب مداد
"""

# ============================================================================
# STOCK ALERTS
# ============================================================================
LOW_STOCK_THRESHOLD = 2
CRITICAL_STOCK_THRESHOLD = 1

# ============================================================================
# DEFAULT VALUES
# ============================================================================
DEFAULT_PACKAGING_COST = 1.0
DEFAULT_PLATFORM = "Vinted"

# ============================================================================
# PLATFORMS
# ============================================================================
PLATFORMS = [
    "Vinted",
    "Instagram",
    "Facebook Marketplace",
    "WhatsApp",
    "In Person",
    "Other"
]

# ============================================================================
# GENRES - Comprehensive Arabic Literature Categories
# ============================================================================
GENRES = [
    # Fiction
    "Fiction - General",
    "Fiction - Historical",
    "Fiction - Contemporary",
    "Fiction - Science Fiction",
    "Fiction - Fantasy",
    "Fiction - Mystery/Thriller",
    "Fiction - Romance",
    "Fiction - Horror",
    
    # Non-Fiction
    "Self-Help & Personal Development",
    "Psychology",
    "Philosophy",
    "Religion & Spirituality",
    "Islamic Studies",
    "Biography & Memoir",
    "History",
    "Politics & Society",
    "Business & Economics",
    "Science & Nature",
    
    # Arabic Classics
    "Arabic Classics",
    "Poetry - Classical",
    "Poetry - Modern",
    
    # Children & Young Adult
    "Children's Books",
    "Young Adult",
    
    # Other
    "Art & Photography",
    "Cooking",
    "Travel",
    "Education & Reference",
    "Other"
]

# ============================================================================
# UI SETTINGS
# ============================================================================
MAX_SALES_HISTORY = 20
CACHE_TTL_SECONDS = 60

# ============================================================================
# PROFIT WARNINGS
# ============================================================================
LOW_MARGIN_THRESHOLD = 10  # percent
HIGH_MARGIN_THRESHOLD = 50  # percent

# ============================================================================
# DATE FORMATS
# ============================================================================
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d"  # Removed time component
DISPLAY_DATE_FORMAT = "%d/%m/%Y"

# ============================================================================
# QUICK MESSAGES - Templates for customer communication
# ============================================================================
QUICK_MESSAGES = {
    "order_confirmation": {
        "title": "📦 Order Confirmation",
        "message": """Hello! 👋

Thank you for your order! Your book(s) will be carefully packed and shipped within 1-2 business days.

📚 Books ordered: [LIST HERE]
💰 Total: €[AMOUNT]
📦 Tracking: [TRACKING NUMBER]

Looking forward to serving you again!

Best regards,
Midad Books Team"""
    },
    
    "shipping_notification": {
        "title": "🚚 Shipping Notification",
        "message": """Hello! 📦

Great news! Your order has been shipped today.

📦 Tracking number: [TRACKING]
🚚 Expected delivery: [DATE]

You can track your package here: [LINK]

Thank you for choosing Midad Books!

Best regards,
Midad Books"""
    },
    
    "thank_you": {
        "title": "💚 Thank You Message",
        "message": """Thank you so much for your order! 🙏

We hope you enjoy your book(s)! 📚

If you're satisfied with your purchase, we'd appreciate a positive review! ⭐

Feel free to reach out anytime for new arrivals or recommendations.

Best wishes,
Midad Books 📖"""
    },
    
    "payment_reminder": {
        "title": "💳 Payment Reminder",
        "message": """Hello! 👋

This is a friendly reminder about your pending order:

📚 Books: [LIST]
💰 Total: €[AMOUNT]

Please complete payment at your earliest convenience to reserve these books.

Payment methods: [METHODS]

Thank you!
Midad Books"""
    },
    
    "book_inquiry": {
        "title": "📖 Book Inquiry Response",
        "message": """Hello! 👋

Thank you for your interest in [BOOK TITLE]!

✅ Availability: In stock
💰 Price: €[PRICE]
📦 Condition: [CONDITION]
📸 Photos: [Available upon request]

Would you like to proceed with the order?

Best regards,
Midad Books"""
    },
    
    "signature": {
        "title": "✍️ Standard Signature",
        "message": """Best regards,
Midad Books 📚
كتب مداد

📧 Email: [YOUR EMAIL]
📱 Phone: [YOUR PHONE]
🛒 Platform: [PLATFORM]"""
    }
}