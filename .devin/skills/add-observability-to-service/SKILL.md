---
name: add-observability-to-service
description: Guides adding structured logging, health checks, and request timing to a TraderX service module. Use when instrumenting a new or existing service with observability — following the target requirements in TARGET_ARCHITECTURE_CONSTRAINTS.md §10.
---

# Add Observability to Service

This skill walks through adding structured logging, health check endpoints, and request timing to a TraderX service. These are repeatable steps applied to each service as it is created or extracted from the monolith.

## Context

The current codebase uses basic `logging.getLogger(__name__)` with unstructured text messages. The target architecture ([TARGET_ARCHITECTURE_CONSTRAINTS.md](../../../TARGET_ARCHITECTURE_CONSTRAINTS.md) §10) requires:

- **Structured JSON logs** with correlation IDs, tenant IDs, and request IDs
- **Health check endpoints** with dependency checks (DB connectivity)
- **Request/response metrics** (latency, status codes)

## Steps

### 1. Add structured JSON logging

Replace the basic logging setup with structured JSON output. See [templates/structured-logging.py.md](templates/structured-logging.py.md) for the full implementation.

**What to change in each service module:**

```python
# BEFORE (current pattern)
import logging
logger = logging.getLogger(__name__)
logger.info("Created account %d for tenant %s", account.id, tenant_id)

# AFTER (structured pattern)
import logging
from app.utils.logging_config import get_logger
logger = get_logger(__name__)
logger.info("account_created", extra={
    "account_id": account.id,
    "tenant_id": tenant_id,
})
```

The structured logger emits JSON lines:
```json
{"timestamp": "2025-01-15T10:30:00Z", "level": "INFO", "logger": "app.services.account_service", "message": "account_created", "account_id": 42, "tenant_id": "acme_corp", "correlation_id": "abc-123"}
```

### 2. Add correlation ID middleware

Add middleware that generates or extracts a correlation ID per request and makes it available to all log statements. This enables tracing a single request across all log lines.

Add to `app/middleware.py` alongside the existing `TenantMiddleware`:

```python
import uuid

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
```

Register it in `app/main.py`:
```python
app.add_middleware(CorrelationIdMiddleware)
```

### 3. Add a health check endpoint

Add a `/health` endpoint that verifies DB connectivity. See [templates/health-endpoint.py.md](templates/health-endpoint.py.md) for the full implementation.

The current `/health` endpoint in `main.py` returns a static response. Replace it with one that actually checks dependencies:

```python
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": str(e)},
        )
```

### 4. Add request timing middleware

Add middleware that logs request duration for every API call:

```python
import time

class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info("request_completed", extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "tenant_id": getattr(request.state, "tenant_id", None),
        })
        return response
```

### 5. Convert existing log statements

For each service module, convert existing `logger.info()` calls to the structured format. See [examples/logging-examples.md](examples/logging-examples.md) for before/after examples from the real codebase.

**Key fields to include in every log line:**
- `tenant_id` — always present for tenant-scoped operations
- `entity_id` — the ID of the resource being operated on (account_id, trade_id, etc.)
- `action` — what happened (created, updated, deleted, failed)

### 6. Verify

```bash
# Run tests to ensure nothing is broken
cd traderx-monolith && python -m pytest tests/ -v

# Start the server and check health
python run.py
curl http://localhost:8000/health

# Verify structured logs appear in console output
curl http://localhost:8000/account/
# Check terminal output for JSON log lines
```

## Additional Resources

- [templates/structured-logging.py.md](templates/structured-logging.py.md) — Structured logging module
- [templates/health-endpoint.py.md](templates/health-endpoint.py.md) — Health check endpoint with DB verification
- [examples/logging-examples.md](examples/logging-examples.md) — Before/after conversion examples
