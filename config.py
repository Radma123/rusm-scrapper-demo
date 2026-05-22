import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

# --- Rusmarket portal ---
RUSMARKET_API_URL = os.getenv(
    "RUSMARKET_API_URL",
    "https://rusmarket.top/api/v1/products/availability",
)
RUSMARKET_TIMEOUT = float(os.getenv("RUSMARKET_TIMEOUT", "30"))

# --- Scrapers ---
SCRAPER_MAX_LISTINGS = int(os.getenv("SCRAPER_MAX_LISTINGS", "5"))
SCRAPER_AVITO_REGION = os.getenv("SCRAPER_AVITO_REGION", "all")

MARKETPLACE_SOURCES = [
    s.strip()
    for s in os.getenv(
        "MARKETPLACE_SOURCES",
        "avito,aliexpress,autopiter",
    ).split(",")
    if s.strip()
]

# --- HTTP API ---
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "6767"))
