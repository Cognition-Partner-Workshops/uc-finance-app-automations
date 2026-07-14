"""Tests for position endpoints."""
import pytest


def test_list_positions_by_account_empty(client):
    """Regression (TRADER-DEMO-APP-6): an account with no positions must
    return 200 + [] instead of raising ValueError from max() on an empty
    iterable."""
    acct = client.post("/account/", json={"displayName": "Empty Account"})
    account_id = acct.json()["id"]

    resp = client.get(f"/positions/{account_id}")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_positions_by_account_nonexistent(client):
    """A non-existent account has no positions and must not error."""
    resp = client.get("/positions/999999")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_positions_by_account_with_data(client):
    """An account with positions returns them without error."""
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
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["security"] == "AAPL"
    assert data[0]["quantity"] == 100
