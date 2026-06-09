# Test File Template

Use this template when creating a new test file. Replace `<domain>` and `<Domain>` with the actual domain name.

## Template

```python
"""Tests for <domain> endpoints."""
import pytest


# =============================================================================
# Happy Path
# =============================================================================

def test_create_<domain>(client):
    """Test creating a <domain> via POST and retrieving it."""
    resp = client.post("/<domain>/", json={
        # Provide required fields matching the Pydantic model:
        # "fieldName": "value",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    # assert data["fieldName"] == "value"

    # Verify it can be retrieved
    item_id = data["id"]
    resp2 = client.get(f"/<domain>/{item_id}")
    assert resp2.status_code == 200
    fetched = resp2.json()
    assert fetched["id"] == item_id


def test_list_<domain>s_empty(client):
    """Test listing <domain>s when none exist."""
    resp = client.get("/<domain>/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_<domain>s(client):
    """Test listing <domain>s after creating some."""
    client.post("/<domain>/", json={"fieldName": "First"})
    client.post("/<domain>/", json={"fieldName": "Second"})

    resp = client.get("/<domain>/")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2


# =============================================================================
# Error Cases
# =============================================================================

def test_get_<domain>_not_found(client):
    """Test getting a non-existent <domain> returns 404."""
    resp = client.get("/<domain>/99999")
    assert resp.status_code == 404


def test_create_<domain>_missing_field(client):
    """Test creating a <domain> with missing required field returns 422."""
    resp = client.post("/<domain>/", json={})
    assert resp.status_code == 422


# =============================================================================
# Update
# =============================================================================

def test_update_<domain>(client):
    """Test updating an existing <domain>."""
    # Create first
    create_resp = client.post("/<domain>/", json={"fieldName": "Original"})
    item_id = create_resp.json()["id"]

    # Update
    update_resp = client.put("/<domain>/", json={
        "id": item_id,
        "fieldName": "Updated",
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["fieldName"] == "Updated"


def test_update_<domain>_not_found(client):
    """Test updating a non-existent <domain> returns 404."""
    resp = client.put("/<domain>/", json={
        "id": 99999,
        "fieldName": "Nope",
    })
    assert resp.status_code == 404


# =============================================================================
# Multi-Tenant Isolation
# =============================================================================

def test_<domain>_tenant_isolation(client):
    """Test that <domain>s in one tenant are not visible in another."""
    # Create in tenant A
    client.post("/<domain>/", json={"fieldName": "Tenant A Item"},
                headers={"X-Tenant-ID": "acme_corp"})

    # Should not be visible in tenant B
    resp = client.get("/<domain>/", headers={"X-Tenant-ID": "globex_inc"})
    assert resp.json() == []

    # Should be visible in tenant A
    resp = client.get("/<domain>/", headers={"X-Tenant-ID": "acme_corp"})
    assert len(resp.json()) == 1
```

## Notes

- **Each test starts with an empty database** — the `conftest.py` autouse fixture creates/drops tables per test
- **No imports needed for fixtures** — `client` is auto-discovered by pytest from `conftest.py`
- **Multi-tenant tests** use the `X-Tenant-ID` header; without it, the default tenant (`acme_corp`) is used
- **Pydantic validation errors** return HTTP 422, not 400
