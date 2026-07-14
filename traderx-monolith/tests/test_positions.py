"""Tests for position endpoints."""


def test_list_positions_by_account_empty(client):
    """Regression: account with no positions must return 200 + [] and not
    raise ValueError from max() on an empty iterable (TRADER-DEMO-APP-6)."""
    acct = client.post("/account/", json={"displayName": "Empty Account"})
    account_id = acct.json()["id"]

    resp = client.get(f"/positions/{account_id}")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_positions_by_account_nonexistent(client):
    """An account that never traded has no positions and must not 500."""
    resp = client.get("/positions/999999")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_positions_by_account_with_data(client):
    """Account with positions returns them after a trade."""
    acct = client.post("/account/", json={"displayName": "Trading Account"})
    account_id = acct.json()["id"]

    client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    })

    resp = client.get(f"/positions/{account_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["security"] == "AAPL"
    assert data[0]["quantity"] == 100
