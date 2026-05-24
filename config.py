# ─────────────────────────────────────────────
# config.py — Central configuration
# ─────────────────────────────────────────────

import os

# =========================================================
# GEMINI API SETTINGS
# =========================================================

# Reads API key from environment variable
# If not found, uses the fallback string below
GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    "AIzaSyD3R57Rhgli1h266ztj-P-ytFs0IlCFFgg"
)

# Gemini model name
MODEL_NAME = "gemini-2.5-flash-lite"


# =========================================================
# SERVER SETTINGS
# =========================================================

HOST = "0.0.0.0"
PORT = 8000


# =========================================================
# OCR SETTINGS
# =========================================================

# OCR language
OCR_LANG = "en"

# Minimum confidence score
OCR_SCORE_THRESHOLD = 0.5


# =========================================================
# ACCOUNTING SETTINGS
# =========================================================

DEFAULT_CURRENCY = "INR"
DEFAULT_USER = "system"


# =========================================================
# FILE UPLOAD SETTINGS
# =========================================================

UPLOAD_DIR = "uploads"

# Allowed file types
ALLOWED_EXTENSIONS = [
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg"
]


# =========================================================
# LOGGING SETTINGS
# =========================================================

LOG_LEVEL = "INFO"


# =========================================================
# DEBUG SETTINGS
# =========================================================

DEBUG = True


# =========================================================
# VALIDATION
# =========================================================

if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
    print("⚠ WARNING: Gemini API key not set.")