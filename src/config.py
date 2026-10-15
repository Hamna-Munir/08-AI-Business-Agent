"""
config.py
Central place for environment variables, model settings, and constants.

Follows the same pattern as earlier weeks (Groq's OpenAI-compatible endpoint,
key name OPENAI_API_KEY, model 'openai/gpt-oss-120b').
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# LLM (Groq / OpenAI-compatible endpoint)
# ---------------------------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

# ---------------------------------------------------------------------------
# External research (optional — graceful fallback if not configured)
# ---------------------------------------------------------------------------
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# ---------------------------------------------------------------------------
# Business data
# ---------------------------------------------------------------------------
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "business.db"

CUSTOMERS_CSV = DATA_DIR / "customers.csv"
PRODUCTS_CSV = DATA_DIR / "products.csv"
ORDERS_CSV = DATA_DIR / "orders.csv"
SALES_CSV = DATA_DIR / "sales.csv"

# File-tool access is restricted to these directories (never arbitrary paths)
FILE_TOOL_ALLOWED_DIRS = [DATA_DIR, ROOT_DIR / "docs", ROOT_DIR / "notes"]

# ---------------------------------------------------------------------------
# Business question categories (Day 50)
# ---------------------------------------------------------------------------
QUESTION_CATEGORIES = [
    "sales",
    "marketing",
    "customers",
    "operations",
    "finance",
    "inventory",
    "general",
]

# ---------------------------------------------------------------------------
# Agent behaviour
# ---------------------------------------------------------------------------
MAX_TOOL_CALLS_PER_QUESTION = 6
INSUFFICIENT_EVIDENCE_MESSAGE = (
    "Insufficient evidence to determine the cause from the available business data."
)
