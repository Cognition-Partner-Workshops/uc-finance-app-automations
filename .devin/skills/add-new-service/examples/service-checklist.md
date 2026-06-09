# New Service Checklist

Copy this checklist when extracting a new domain service. Replace `<domain>` with the actual domain name (e.g., `position`, `notification`).

## Files to Create

- [ ] `traderx-monolith/app/models/<domain>.py` — SQLAlchemy model with `tenant_id` and `to_dict()`
- [ ] `traderx-monolith/app/services/<domain>_service.py` — CRUD + business logic
- [ ] `traderx-monolith/app/routes/<domain>.py` — FastAPI router with Pydantic models
- [ ] `traderx-monolith/tests/test_<domain>.py` — Integration tests using `client` fixture

## Files to Modify

- [ ] `traderx-monolith/app/models/__init__.py` — Add `from app.models.<domain> import <Domain>`
- [ ] `traderx-monolith/app/services/__init__.py` — Add `from app.services import <domain>_service`
- [ ] `traderx-monolith/app/main.py` — Add `from app.routes.<domain> import router as <domain>_router` and `app.include_router(<domain>_router, tags=["<Domain>"])`

## Verification

- [ ] `python -m pytest tests/ -v` — All tests pass
- [ ] `python run.py` — Server starts without import errors
- [ ] `curl http://localhost:8000/<domain>/` — Returns `[]` or seeded data
- [ ] `curl http://localhost:8000/health` — Health check still works

## Architecture Rules (from TARGET_ARCHITECTURE_CONSTRAINTS.md)

- [ ] Service owns its own model — no cross-domain model imports
- [ ] No direct database queries to other domain's tables
- [ ] Inter-service communication goes through service function calls (future: API calls)
- [ ] No circular dependencies with other service modules
- [ ] Dependency graph remains a DAG
