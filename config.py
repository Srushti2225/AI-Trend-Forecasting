import os
from dotenv import load_dotenv

load_dotenv()

# --- API Keys (add more as you get them) ---
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", None)

# These are not available yet — will be added later
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", None)
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", None)
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "trend-forecaster-v1")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", None)

# --- Reddit Communities (for later) ---
# --- Broad Seed Topics (NOT specific trends — just domain anchors) ---
# --- Fashion Keywords (India-focused, Gen Z) ---
# --- Fashion Keywords (India-focused, Gen Z) ---
FASHION_KEYWORDS = [
    # Ethnic / Indian styles
    "co-ord set", "ethnic fusion", "kurta set", "indo western",
    "mirror work", "bandhani dress", "ajrakh print", "phulkari dupatta",
    "saree draping", "lehenga skirt", "sharara set", "palazzo set",

    # Western trends popular in India
    "quiet luxury", "mob wife aesthetic", "Y2K fashion", "cottagecore",
    "dopamine dressing", "dark academia", "coastal grandmother",
    "clean girl aesthetic", "old money style", "ballet core",

    # Specific garment trends
    "barrel leg jeans", "wide leg pants", "maxi skirt", "corset top",
    "blazer dress", "shirt dress", "crop jacket", "shrug outfit"
]

# --- Beauty Keywords (India-focused, Gen Z) ---
BEAUTY_KEYWORDS = [
    # Skincare trends
    "glass skin", "glazed donut skin", "skin flooding", "slugging skincare",
    "dewy skin", "skinimalism", "double cleansing", "barrier repair",

    # Makeup trends
    "clean girl makeup", "no makeup makeup", "lip liner overline",
    "blush draping", "soap brows", "foxy eye", "graphic liner",
    "monochromatic makeup", "editorial makeup", "bollywood glam",

    # Specific product trends
    "lip liner", "bold brow", "watercolour blush", "skin tint",
    "tinted moisturizer", "bronzer makeup", "face oil routine"
]

# Seed topics for broad YouTube/News fetching
FASHION_SEED_TOPICS = [
    "indian fashion 2026",
    "outfit ideas india",
    "indian street style",
    "ethnic wear trend",
    "gen z fashion india"
]

BEAUTY_SEED_TOPICS = [
    "indian beauty trends 2026",
    "makeup tutorial india",
    "skincare routine india",
    "beauty tips hindi",
    "gen z makeup india"
]

ALL_KEYWORDS = FASHION_KEYWORDS + BEAUTY_KEYWORDS

# --- Industry Tags ---
INDUSTRY_TAGS = {
    "fashion": FASHION_KEYWORDS,
    "beauty": BEAUTY_KEYWORDS
}

# --- Trend Detection Thresholds ---
VELOCITY_THRESHOLD = 5
CONFIDENCE_HIGH = 0.75
CONFIDENCE_MEDIUM = 0.45

# --- Geography ---
DEFAULT_GEO = "IN"
DEFAULT_LANGUAGE = "en-IN"
DEFAULT_TIMEZONE = 330

# --- Data Collection Settings ---
YOUTUBE_MAX_RESULTS = 10
GOOGLE_TRENDS_TIMEFRAME = "now 7-d"
GOOGLE_TRENDS_MONTHLY = "today 1-m"

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
MEMORY_DIR = os.path.join(BASE_DIR, "memory")

# --- Sanity check on startup ---
def check_config():
    print("\n--- CONFIG STATUS ---")

    if YOUTUBE_API_KEY:
        print("  YOUTUBE_API_KEY     : OK")
    else:
        print("  YOUTUBE_API_KEY     : MISSING — add to .env")

    if ANTHROPIC_API_KEY:
        print("  ANTHROPIC_API_KEY   : OK")
    else:
        print("  ANTHROPIC_API_KEY   : not set yet (needed in Week 2)")

    if REDDIT_CLIENT_ID:
        print("  REDDIT_CLIENT_ID    : OK")
    else:
        print("  REDDIT_CLIENT_ID    : not set yet (optional for now)")

    if NEWS_API_KEY:
        print("  NEWS_API_KEY        : OK")
    else:
        print("  NEWS_API_KEY        : not set yet")
    
    print("---------------------\n")

if __name__ == "__main__":
    check_config()
    print(f"Fashion keywords ({len(FASHION_KEYWORDS)}): {FASHION_KEYWORDS}")
    print(f"Beauty keywords  ({len(BEAUTY_KEYWORDS)}): {BEAUTY_KEYWORDS}")