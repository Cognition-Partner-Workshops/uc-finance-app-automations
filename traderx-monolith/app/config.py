"""
Global configuration module for TraderX Monolith.

WARNING: This module is imported by every other module using `from app.config import *`.
This is an intentional architectural smell — mutable global state shared everywhere.
"""

import os

# =============================================================================
# Database Configuration
# =============================================================================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///traderx.db")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# =============================================================================
# Socket.io Configuration
# =============================================================================
SOCKETIO_ADDRESS = os.getenv("SOCKETIO_ADDRESS", "http://localhost:8000")
SOCKETIO_ASYNC_MODE = "asgi"
SOCKETIO_CORS_ALLOWED = os.getenv("SOCKETIO_CORS_ALLOWED", "*")

# =============================================================================
# Reference Data Configuration
# =============================================================================
REFERENCE_DATA_FILE = os.getenv(
    "REFERENCE_DATA_FILE",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "s-and-p-500-companies.csv")
)

# =============================================================================
# People Data Configuration
# =============================================================================
PEOPLE_DATA_FILE = os.getenv(
    "PEOPLE_DATA_FILE",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "people.json")
)

# =============================================================================
# Application Configuration
# =============================================================================
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
APP_TITLE = "TraderX Monolith API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Monolithic backend replacing all TraderX microservices"

# =============================================================================
# CORS Configuration
# =============================================================================
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# =============================================================================
# Trade Processing Configuration
# =============================================================================
TRADE_PROCESSING_DELAY_MS = int(os.getenv("TRADE_PROCESSING_DELAY_MS", "0"))
MAX_TRADE_QUANTITY = int(os.getenv("MAX_TRADE_QUANTITY", "1000000"))
MIN_TRADE_QUANTITY = int(os.getenv("MIN_TRADE_QUANTITY", "1"))

# =============================================================================
# Trade Business Rules (intentional smell — config as business logic)
# =============================================================================
ALLOWED_TRADE_SIDES = os.getenv("ALLOWED_TRADE_SIDES", "Buy,Sell").split(",")
AUTO_SETTLE_TRADES = os.getenv("AUTO_SETTLE_TRADES", "true").lower() == "true"

# =============================================================================
# Audit Configuration
# =============================================================================
AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "true").lower() == "true"
AUDIT_LOG_FILE = os.getenv("AUDIT_LOG_FILE", "traderx_audit.log")

# =============================================================================
# Mutable Runtime State (intentional smell)
# =============================================================================
_runtime_state = {
    "total_trades_processed": 0,
    "last_trade_timestamp": None,
    "active_sessions": 0,
    "startup_time": None,
}


def get_runtime_state():
    """Get mutable runtime state dict."""
    return _runtime_state


def update_runtime_state(key, value):
    """Update mutable runtime state — called from various modules."""
    _runtime_state[key] = value

