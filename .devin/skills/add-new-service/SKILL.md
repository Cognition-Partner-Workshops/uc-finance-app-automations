---
name: add-new-service
description: Guides extraction of a new domain service from the TraderX monolith. Use when creating a new service module with its model, routes, service layer, and tests — following the target microservice boundaries defined in TARGET_ARCHITECTURE_CONSTRAINTS.md.
---

# Add New Service to TraderX

This skill walks through creating a complete new domain service within the monolith, following existing patterns and preparing for future microservice extraction.

## Context

The TraderX monolith is being decomposed into domain-aligned services per [TARGET_ARCHITECTURE_CONSTRAINTS.md](../../../TARGET_ARCHITECTURE_CONSTRAINTS.md) §7:

| Service | Domain | Responsibilities |
|---|---|---|
| **Account Service** | Accounts | Account CRUD, account user management, account validation |
| **Trading Service** | Trading | Trade submission, trade validation, trade state machine |
| **Position Service** | Positions | Position tracking, position queries, position recalculation |
| **Reference Data Service** | Reference Data | Stock ticker lookup, S&P 500 data |
| **People Service** | People | Person directory, person validation |

## Steps

### 1. Create the SQLAlchemy model

Create a new model file at `traderx-monolith/app/models/<domain>.py`.

- Follow the pattern in [templates/model.py.md](templates/model.py.md)
- Include `tenant_id` column for multi-tenant filtering
- Include a `to_dict()` method that uses camelCase keys
- Import `Base` from `app.database` and `from app.config import *`
- Register the model in `traderx-monolith/app/models/__init__.py`

### 2. Create the service module

Create a new service file at `traderx-monolith/app/services/<domain>_service.py`.

- Follow the pattern in [templates/service.py.md](templates/service.py.md)
- Accept `db: Session` and `tenant_id: str` as parameters on every function
- Use `log_audit_event()` from `app.utils.helpers` for create/update/delete operations
- Use standard `logging.getLogger(__name__)` for operational logs
- Register the service in `traderx-monolith/app/services/__init__.py`

### 3. Create the route module

Create a new route file at `traderx-monolith/app/routes/<domain>.py`.

- Follow the pattern in [templates/routes.py.md](templates/routes.py.md)
- Define Pydantic request/response models at the top of the file
- Use `get_tenant_from_request(request)` for tenant extraction
- Use `Depends(get_db)` for database session injection
- Always call the service layer — do NOT write inline SQLAlchemy queries in route handlers
- Register the router in `traderx-monolith/app/main.py` inside `create_app()`

### 4. Register in main.py

Add the router import and `app.include_router()` call in `traderx-monolith/app/main.py`:

```python
from app.routes.<domain> import router as <domain>_router
app.include_router(<domain>_router, tags=["<Domain>"])
```

### 5. Add tests

Create a test file at `traderx-monolith/tests/test_<domain>.py`.

- Use the `client` fixture from `conftest.py` (TestClient with in-memory SQLite)
- Test the happy path for each endpoint (create, read, list)
- Test error cases (404 for missing resources, validation failures)
- See the [add-integration-test](../add-integration-test/SKILL.md) skill for detailed test patterns

### 6. Verify

Run the test suite to confirm nothing is broken:

```bash
cd traderx-monolith && python -m pytest tests/ -v
```

## Checklist

See [examples/service-checklist.md](examples/service-checklist.md) for a copy-paste checklist of every file to create or modify.

## Additional Resources

- [templates/model.py.md](templates/model.py.md) — SQLAlchemy model template
- [templates/service.py.md](templates/service.py.md) — Service layer template
- [templates/routes.py.md](templates/routes.py.md) — FastAPI route module template
- [examples/service-checklist.md](examples/service-checklist.md) — Full file checklist
