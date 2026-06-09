# Structured Logging Module Template

This template provides a JSON-based structured logging configuration that can be added to `traderx-monolith/app/utils/logging_config.py`.

## Template: `app/utils/logging_config.py`

```python
"""
Structured JSON logging configuration for TraderX.

Replaces the default Python logging with JSON-formatted output that includes
correlation IDs, tenant IDs, and structured fields for log aggregation.
"""

import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields passed via logger.info("msg", extra={...})
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "relativeCreated",
                "exc_info", "exc_text", "stack_info", "lineno", "funcName",
                "pathname", "filename", "module", "levelno", "levelname",
                "thread", "threadName", "process", "processName",
                "getMessage", "message", "msecs", "taskName",
            ):
                log_entry[key] = value

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def configure_logging(level: str = "INFO"):
    """
    Configure root logger with JSON formatting.
    Call this once at application startup (in run.py or main.py).
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance. Drop-in replacement for logging.getLogger().
    Usage: logger = get_logger(__name__)
    """
    return logging.getLogger(name)
```

## Usage in a service module

```python
# Replace this:
import logging
logger = logging.getLogger(__name__)
logger.info("Created account %d for tenant %s", account.id, tenant_id)

# With this:
from app.utils.logging_config import get_logger
logger = get_logger(__name__)
logger.info("account_created", extra={
    "account_id": account.id,
    "tenant_id": tenant_id,
    "display_name": display_name,
})
```

## Usage at application startup

Add to `run.py` before starting the server:

```python
from app.utils.logging_config import configure_logging
configure_logging(level="INFO")
```

## Output example

```json
{"timestamp": "2025-01-15T10:30:00.123456+00:00", "level": "INFO", "logger": "app.services.account_service", "message": "account_created", "account_id": 42, "tenant_id": "acme_corp", "display_name": "Trading Account Alpha"}
```

## Notes

- **`extra` dict keys** become top-level fields in the JSON output — use snake_case
- **Call `configure_logging()` once** at startup, before any logging happens
- **Use `get_logger(__name__)`** instead of `logging.getLogger(__name__)` — functionally identical but signals intent
- **Do not log sensitive data** — no passwords, tokens, or PII in log fields
