"""
Application Configuration
All constants and settings in one place
"""

import json
from pathlib import Path

# Stock alerts
LOW_STOCK_THRESHOLD = 2
CRITICAL_STOCK_THRESHOLD = 1

# Default values
DEFAULT_PACKAGING_COST = 0.45
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


# ============================================================================
# LOAD DEFAULT QUICK MESSAGES FROM JSON
# ============================================================================
def load_default_messages() -> dict:
    """Load default quick messages from JSON file."""
    config_dir = Path(__file__).parent
    json_path = config_dir / "default_messages.json"

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Warning: {json_path} not found. Using empty defaults.")
        return {}
    except json.JSONDecodeError as e:
        print(f"⚠️ Warning: Error parsing {json_path}: {e}")
        return {}


# Load messages on import
DEFAULT_QUICK_MESSAGES = load_default_messages()
