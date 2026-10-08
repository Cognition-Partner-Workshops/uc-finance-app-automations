"""
Shared utility functions imported everywhere.
This module provides common helpers used across all layers of the application.
"""

import csv
import json
import logging
import os
from datetime import datetime
from typing import List, Optional

from app.config import *  # noqa: F401,F403 — intentional global config import

logger = logging.getLogger(__name__)

# =============================================================================
# Reference Data Helpers
# =============================================================================

_stocks_cache = None


def load_stocks_from_csv(file_path: Optional[str] = None) -> List[dict]:
    """Load S&P 500 stock data from CSV file. Results are cached in memory."""
    global _stocks_cache
    if _stocks_cache is not None:
        return _stocks_cache

    if file_path is None:
        file_path = REFERENCE_DATA_FILE

    stocks = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                stocks.append({
                    "ticker": row.get("Symbol", ""),
                    "companyName": row.get("Security", ""),
                })
        _stocks_cache = stocks
        logger.info("Loaded %d stocks from %s", len(stocks), file_path)
    except FileNotFoundError:
        logger.error("Stock data file not found: %s", file_path)
    except Exception as e:
        logger.error("Error loading stock data: %s", str(e))

    return stocks


def find_stock_by_ticker(ticker: str) -> Optional[dict]:
    """Find a single stock by ticker symbol."""
    stocks = load_stocks_from_csv()
    for stock in stocks:
        if stock["ticker"] == ticker:
            return stock
    return None


def clear_stocks_cache():
    """Clear the in-memory stocks cache. Useful for testing."""
    global _stocks_cache
    _stocks_cache = None


# =============================================================================
# People Data Helpers
# =============================================================================

_people_cache = None


def load_people_from_json(file_path: Optional[str] = None) -> List[dict]:
    """Load people data from JSON file. Results are cached in memory."""
    global _people_cache
    if _people_cache is not None:
        return _people_cache

    if file_path is None:
        file_path = PEOPLE_DATA_FILE

    people = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            people = json.load(f)
        _people_cache = people
        logger.info("Loaded %d people from %s", len(people), file_path)
    except FileNotFoundError:
        logger.error("People data file not found: %s", file_path)
    except Exception as e:
        logger.error("Error loading people data: %s", str(e))

    return people


def clear_people_cache():
    """Clear the in-memory people cache. Useful for testing."""
    global _people_cache
    _people_cache = None


# =============================================================================
# Date/Time Helpers
# =============================================================================

def now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.utcnow()


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format a datetime to ISO string, or return None."""
    if dt is None:
        return None
    return dt.isoformat()


# =============================================================================
# Validation Helpers
# =============================================================================

def validate_trade_side(side: str) -> bool:
    """Validate that a trade side is either Buy or Sell."""
    return side in ("Buy", "Sell")


def validate_trade_quantity(quantity: int) -> bool:
    """Validate that trade quantity is within allowed range."""
    return MIN_TRADE_QUANTITY <= quantity <= MAX_TRADE_QUANTITY


def validate_trade_state(state: str) -> bool:
    """Validate that a trade state is one of the allowed values."""
    return state in ("New", "Processing", "Settled", "Cancelled")


# =============================================================================
# Logging Helpers
# =============================================================================

def log_audit_event(event_type: str, details: str):
    """Log an audit event. Used by trade_processor and other services."""
    if not AUDIT_ENABLED:
        return
    timestamp = now_utc().isoformat()
    audit_msg = f"[AUDIT] [{timestamp}] [{event_type}] {details}"
    logger.info(audit_msg)


def log_trade_event(trade_id, account_id, action, extra=""):
    """Log a trade-specific event for audit trail."""
    details = f"trade_id={trade_id} account_id={account_id} action={action} {extra}"
    log_audit_event("TRADE", details)


def log_position_event(account_id, security, action, extra=""):
    """Log a position-specific event for audit trail."""
    details = f"account_id={account_id} security={security} action={action} {extra}"
    log_audit_event("POSITION", details)


# =============================================================================
# Misc Helpers
# =============================================================================

def safe_int(value, default=0) -> int:
    """Safely convert a value to int, returning default on failure."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def truncate_string(s: str, max_length: int = 100) -> str:
    """Truncate a string to max_length characters."""
    if len(s) <= max_length:
        return s
    return s[:max_length - 3] + "..."
