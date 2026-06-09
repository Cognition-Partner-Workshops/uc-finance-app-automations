---
name: add-api-endpoint
description: Guides adding a new REST API endpoint to an existing TraderX route module. Use when adding GET, POST, PUT, or DELETE endpoints — covers Pydantic models, route handlers, service calls, error handling, and audit logging.
---

# Add API Endpoint

This skill walks through adding a new REST endpoint to an existing route module in the TraderX monolith.

## Prerequisites

- The route module already exists at `traderx-monolith/app/routes/<domain>.py`
- The corresponding service module exists at `traderx-monolith/app/services/<domain>_service.py`
- If neither exists, use the [add-new-service](../add-new-service/SKILL.md) skill first

## Steps

### 1. Add the service function

Add the business logic to the service module (`app/services/<domain>_service.py`) first. The service function should:

- Accept `db: Session` and `tenant_id: str` as the first two arguments
- Always filter queries by `tenant_id`
- Use `log_audit_event()` for state-changing operations
- Return model instances (or `None` / raise exceptions for errors)

```python
def get_<thing>_by_<field>(db: Session, field_value: str, tenant_id: str):
    return db.query(<Model>).filter(
        <Model>.<field> == field_value,
        <Model>.tenant_id == tenant_id,
    ).first()
```

### 2. Define Pydantic request/response models

Add Pydantic models in the route file's `# Pydantic Request/Response Models` section:

- Use **camelCase** field names to match frontend JSON conventions
- Use `Optional` for fields that are not required
- Keep models co-located in the route file (not in a separate schemas file — this matches the existing pattern)

```python
class <Thing>Request(BaseModel):
    fieldName: str
    optionalField: Optional[int] = None
```

### 3. Create the route handler

Add the endpoint to the route file. Every endpoint must:

- Extract tenant via `get_tenant_from_request(request)`
- Inject DB session via `Depends(get_db)`
- Call the service layer — **never write inline SQLAlchemy queries**
- Return serialized data via `to_dict()`
- Raise `HTTPException` for errors (404, 400, etc.)

See the full endpoint template in [templates/endpoint.py.md](templates/endpoint.py.md).

### 4. Add a test

Add at least one test per endpoint in `traderx-monolith/tests/test_<domain>.py`:

- Test the happy path
- Test error cases (missing resource → 404, bad input → 422)
- See the [add-integration-test](../add-integration-test/SKILL.md) skill for patterns

### 5. Verify

```bash
cd traderx-monolith && python -m pytest tests/ -v
```

## Endpoint Pattern Reference

| HTTP Method | Use Case | Returns | Error |
|---|---|---|---|
| `GET /<domain>/` | List all for tenant | `[item.to_dict()]` | — |
| `GET /<domain>/{id}` | Get single by ID | `item.to_dict()` | 404 if not found |
| `POST /<domain>/` | Create new | `item.to_dict()` | 400 for validation |
| `PUT /<domain>/` | Update existing | `item.to_dict()` | 404 if not found |
| `DELETE /<domain>/{id}` | Delete by ID | `{"deleted": True}` | 404 if not found |

## Additional Resources

- [templates/endpoint.py.md](templates/endpoint.py.md) — Full endpoint template with all patterns
- [examples/get-endpoint.md](examples/get-endpoint.md) — GET endpoint example from `accounts.py`
- [examples/post-endpoint.md](examples/post-endpoint.md) — POST endpoint example from `trades.py`
