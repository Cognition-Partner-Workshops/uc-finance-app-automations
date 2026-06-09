# Health Check Endpoint Template

This template provides a `/health` endpoint that verifies database connectivity. Add or replace the existing health check in `traderx-monolith/app/main.py`.

## Template

```python
from fastapi import Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint with dependency verification.
    Returns 200 if all dependencies are healthy, 503 if any are unhealthy.
    """
    checks = {}

    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    # Determine overall status
    all_healthy = all(
        v == "connected" or v == "ok"
        for v in checks.values()
    )

    status_code = 200 if all_healthy else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": checks,
        },
    )
```

## Current vs target

**Current** (`app/main.py`):
```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

**Target**: The template above — actually verifies DB connectivity and returns proper HTTP status codes (503 for unhealthy).

## Extending for future services

When the monolith is decomposed, each service should check its own dependencies:

| Service | Checks |
|---|---|
| Account Service | Database |
| Trading Service | Database, Account Service API |
| Position Service | Database |
| Reference Data Service | CSV file loaded in memory |
| People Service | JSON file loaded in memory |

Example with multiple checks:

```python
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    checks = {}

    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    # Check reference data is loaded
    from app.utils.helpers import _stocks_cache
    checks["reference_data"] = "loaded" if _stocks_cache else "not_loaded"

    all_healthy = all(v in ("connected", "loaded", "ok") for v in checks.values())

    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content={
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": checks,
        },
    )
```

## Notes

- **Return 503** (Service Unavailable) when unhealthy — Kubernetes liveness/readiness probes use the HTTP status code
- **Include `checks` dict** so operators can see which specific dependency failed
- **Keep health checks fast** — just a `SELECT 1`, not a full table scan
- **Do not include sensitive information** in the health response (no connection strings, credentials, etc.)
