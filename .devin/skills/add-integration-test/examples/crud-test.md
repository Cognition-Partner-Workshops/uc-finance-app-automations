# Example: CRUD Tests

These examples are based on the real tests in `traderx-monolith/tests/test_account_crud.py`.

## Create and retrieve

```python
def test_createAccount(client):
    """Test creating an account via POST and retrieving it."""
    resp = client.post("/account/", json={"displayName": "Test Account"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["displayName"] == "Test Account"
    assert "id" in data

    # retrieve it
    account_id = data['id']
    resp2 = client.get(f"/account/{account_id}")
    assert resp2.status_code == 200
    fetched = resp2.json()
    assert fetched['displayName'] == "Test Account"
    assert fetched["id"] == account_id
```

**Pattern:**
1. POST to create
2. Assert 200 and check response fields
3. GET to verify persistence
4. Assert the fetched data matches

## List when empty

```python
def test_list_accounts_empty(client):
    r = client.get('/account/')
    assert r.status_code == 200
    assert r.json() == []
```

**Pattern:**
- GET the list endpoint on a fresh (empty) database
- Assert 200 and empty list

## Update (upsert pattern)

```python
def test_update_account(client):
    """Create an account then update its display name."""
    # Create
    resp = client.post("/account/", json={"displayName": "Original Name"})
    account_id = resp.json()["id"]

    # Update via PUT
    resp2 = client.put("/account/", json={
        "id": account_id,
        "displayName": "Updated Name",
    })
    assert resp2.status_code == 200
    assert resp2.json()["displayName"] == "Updated Name"

    # Verify via GET
    resp3 = client.get(f"/account/{account_id}")
    assert resp3.json()["displayName"] == "Updated Name"
```

**Pattern:**
1. Create the resource
2. PUT with updated fields
3. GET to confirm the update persisted

## Not found

```python
def test_get_account_not_found(client):
    """Requesting a non-existent account returns 404."""
    resp = client.get("/account/99999")
    assert resp.status_code == 404
```

**Pattern:**
- GET with an ID that doesn't exist
- Assert 404
