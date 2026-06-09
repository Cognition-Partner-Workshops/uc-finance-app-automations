# Logging Conversion Examples

Before/after examples showing how to convert existing unstructured log statements in the TraderX codebase to structured JSON format.

## account_service.py

### Create account

```python
# BEFORE
logger.info("Created account %d for tenant %s", account.id, tenant_id)

# AFTER
logger.info("account_created", extra={
    "account_id": account.id,
    "tenant_id": tenant_id,
    "display_name": display_name,
})
```

### Update account

```python
# BEFORE
logger.info("Updated account %d for tenant %s", account.id, tenant_id)

# AFTER
logger.info("account_updated", extra={
    "account_id": account.id,
    "tenant_id": tenant_id,
    "display_name": display_name,
})
```

### Create account user

```python
# BEFORE
logger.info("Created account user %s for account %d tenant %s",
            username, account_id, tenant_id)

# AFTER
logger.info("account_user_created", extra={
    "account_id": account_id,
    "username": username,
    "tenant_id": tenant_id,
})
```

## trade_processor.py

### Trade processed

```python
# BEFORE
logger.info("Trade %d processed: %s %d %s for account %d",
            trade.id, side, quantity, security, account_id)

# AFTER
logger.info("trade_processed", extra={
    "trade_id": trade.id,
    "account_id": account_id,
    "security": security,
    "side": side,
    "quantity": quantity,
    "state": trade.state,
    "tenant_id": tenant_id,
})
```

### Trade validation failed

```python
# BEFORE
logger.warning("Trade validation failed: account %d not found", account_id)

# AFTER
logger.warning("trade_validation_failed", extra={
    "reason": "account_not_found",
    "account_id": account_id,
    "tenant_id": tenant_id,
})
```

### Position updated

```python
# BEFORE
logger.info("Position updated for account %d security %s: qty=%d",
            account_id, security, new_quantity)

# AFTER
logger.info("position_updated", extra={
    "account_id": account_id,
    "security": security,
    "quantity": new_quantity,
    "previous_quantity": old_quantity,
    "delta": delta,
    "tenant_id": tenant_id,
})
```

## Audit events (helpers.py)

### log_audit_event

```python
# BEFORE
def log_audit_event(event_type: str, tenant_id: str, details: str):
    logger.info("[AUDIT] %s tenant=%s %s", event_type, tenant_id, details)

# AFTER
def log_audit_event(event_type: str, tenant_id: str, details: str, **extra):
    logger.info("audit_event", extra={
        "event_type": event_type,
        "tenant_id": tenant_id,
        "details": details,
        **extra,
    })
```

## Key principles

- **Message is a short, lowercase, snake_case event name** — not a formatted string
- **Structured data goes in `extra` dict** — not interpolated into the message
- **Always include `tenant_id`** — required for filtering in log aggregation
- **Include entity IDs** — `account_id`, `trade_id`, `position_id` for correlation
- **Use appropriate log levels**:
  - `DEBUG` — verbose diagnostic info
  - `INFO` — normal operations (created, updated, processed)
  - `WARNING` — expected failures (validation errors, not-found)
  - `ERROR` — unexpected failures (DB errors, unhandled exceptions)
