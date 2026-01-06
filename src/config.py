"""
Application Configuration
All constants and settings in one place
"""

# Stock alerts
LOW_STOCK_THRESHOLD = 2
CRITICAL_STOCK_THRESHOLD = 1

# Default values
DEFAULT_PACKAGING_COST = 1.0
DEFAULT_PLATFORM = "Vinted"

# Platforms
PLATFORMS = [
    "Vinted",
    "Instagram",
    "Facebook Marketplace",
    "WhatsApp",
    "In Person",
    "Other"
]

# Genres
GENRES = [
    "Fiction - General",
    "Fiction - Historical",
    "Fiction - Contemporary",
    "Fiction - Science Fiction",
    "Fiction - Fantasy",
    "Fiction - Mystery/Thriller",
    "Fiction - Romance",
    "Fiction - Horror",
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
    "Arabic Classics",
    "Poetry - Classical",
    "Poetry - Modern",
    "Children's Books",
    "Young Adult",
    "Art & Photography",
    "Cooking",
    "Travel",
    "Education & Reference",
    "Other"
]

# UI settings
MAX_SALES_HISTORY = 20
CACHE_TTL_SECONDS = 60

# Profit warnings
LOW_MARGIN_THRESHOLD = 10  # percent
HIGH_MARGIN_THRESHOLD = 50  # percent

# Date formats
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d"
DISPLAY_DATE_FORMAT = "%d/%m/%Y"

# Message categories
MESSAGE_CATEGORIES = [
    "General",
    "Shipping",
    "Promotion",
    "Follow-up",
    "Support",
    "Custom"
]

# Default quick messages
DEFAULT_QUICK_MESSAGES = {
    "shipped": {
        "title": "📦 Shipped Notification",
        "category": "Shipping",
        "message": """Hello 🌸📦

Good news! Your order has been shipped today 🚚✨

We hope it reaches you very soon 🤍

نتمنى أن يصلك في أقرب وقت 🌷

Happy reading in advance 📚💫

قراءة ممتعة 🤍

Kind regards,
Midad | كتب عربية 🪶🍂
Instagram: @midad.books"""
    },
    "thank_you": {
        "title": "💖 Thank You",
        "category": "Follow-up",
        "message": """Thank you so much, your message truly made our day 🥰💖
شكراً لكِ من القلب 🌸

InshaaAllah, we will add more books of this kind very soon 📚✨

تابعينا دائماً، القادم أجمل بإذن الله 💫

Wishing you a wonderful reading experience 🌸"""
    },
    "welcome_discount": {
        "title": "🌸 Welcome + Discount",
        "category": "Promotion",
        "message": """Welcome to Midad.Books 🤍📚

We're happy to have you here ✨🥰

If you're interested in this book or any other Arabic titles, we currently offer up to 20% off on bundles 🍂

Feel free to ask anything — we'll be happy to help 🤎

يسعدنا خدمتك دائماً 🤍

Kind regards,
Midad | كتب عربية 🪶🍂
Instagram: @midad.books"""
    },
    "price_inquiry": {
        "title": "💰 Price Response",
        "category": "General",
        "message": """Hello 😊✨

Thank you for your interest 🤍📚

The price for this book is €12💰
If you're interested in multiple books, I can offer a special bundle discount 🌸✨

يسعدني مساعدتك 🤍

Kind regards,
Midad | كتب عربية 🪶🍂"""
    },
    "order_ready": {
        "title": "✅ Order Ready",
        "category": "General",
        "message": """Hello, Your order is ready 🤎

Kind regards,
Midad | كتب عربية 🪶🍂
Instagram: @midad.books"""
    },
    "general_welcome": {
        "title": "👋 General Welcome",
        "category": "General",
        "message": """Hello☺️,

Welcome to Midad.Books, a page for Arabic books. If you're interested in this book or any other titles, we currently offer discounts of up to 20% off.

Feel free to ask ☺️we'll be happy to help you.🤎

Kind regards,
Midad | كتب عربية 🪶🍂
Instagram: @midad.books
قراءة ممتعة دائماً 🤍"""
    }
}