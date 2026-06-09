---
name: add-integration-test
description: Guides writing integration tests for TraderX API endpoints. Use when adding tests for new or existing endpoints — covers test fixtures, multi-tenant testing, CRUD tests, workflow tests, and error case testing.
---

# Add Integration Test

This skill walks through writing integration tests for TraderX API endpoints using pytest and FastAPI's TestClient.

## Test Infrastructure

Tests use a shared `conftest.py` at `traderx-monolith/tests/conftest.py` that provides:

- **In-memory SQLite** database (created/dropped per test via `autouse` fixture)
- **`client` fixture** — a `FastAPI.TestClient` with the DB dependency overridden
- No seed data — each test starts with an empty database

### How the test DB works

```
conftest.py sets up:
  1. In-memory SQLite engine with StaticPool
  2. SessionLocal bound to that engine
  3. autouse fixture: create_all() before each test, drop_all() after
  4. Overrides app's get_db dependency to use the test session
  5. Provides `client` fixture → TestClient(app)
```

## Steps

### 1. Create or locate the test file

Test files live at `traderx-monolith/tests/test_<domain>.py`. One file per domain.

### 2. Write the test function

Every test function:

- Takes `client` as a parameter (injected by the pytest fixture)
- Sets up its own prerequisite data (e.g., creates an account before testing trades)
- Makes HTTP calls via `client.get()`, `client.post()`, `client.put()`
- Asserts on `resp.status_code` and `resp.json()`

See the template in [templates/test-file.py.md](templates/test-file.py.md).

### 3. Follow naming conventions

```
test_<action>_<thing>             # test_create_account
test_<action>_<thing>_<scenario>  # test_create_account_duplicate
test_<thing>_<behavior>           # test_trade_settles_automatically
```

### 4. Cover these categories

For each endpoint, write tests covering:

| Category | Example | Expected |
|---|---|---|
| **Happy path** | POST valid data | 200 + correct JSON |
| **List empty** | GET when no data exists | 200 + `[]` |
| **Not found** | GET with non-existent ID | 404 |
| **Validation** | POST with missing required field | 422 |
| **Multi-tenant** | Create in tenant A, query in tenant B | Not visible |
| **Workflow** | Create → Update → Verify | Each step correct |

### 5. Multi-tenant testing

Pass the `X-Tenant-ID` header to test tenant isolation:

```python
# Create in tenant A
client.post("/account/", json={"displayName": "Acme"},
            headers={"X-Tenant-ID": "acme_corp"})

# Should NOT be visible in tenant B
resp = client.get("/account/", headers={"X-Tenant-ID": "globex_inc"})
assert resp.json() == []
```

### 6. Run tests

```bash
cd traderx-monolith && python -m pytest tests/ -v
```

Run a single test file:

```bash
cd traderx-monolith && python -m pytest tests/test_<domain>.py -v
```

## Additional Resources

- [templates/test-file.py.md](templates/test-file.py.md) — Test file template
- [examples/crud-test.md](examples/crud-test.md) — CRUD test examples from `test_account_crud.py`
- [examples/workflow-test.md](examples/workflow-test.md) — Multi-step workflow test from `test_trade_submit.py`
