"""Tests for the account summary statistics endpoint."""


def _create_account(client, display_name="Summary Account"):
    resp = client.post("/account/", json={"displayName": display_name})
    assert resp.status_code == 200
    return resp.json()["id"]


def test_account_summary_empty(client):
    """An account with no trades reports zeroed statistics."""
    account_id = _create_account(client)

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["accountId"] == account_id
    assert data["totalTrades"] == 0
    assert data["settledTrades"] == 0
    assert data["pendingTrades"] == 0
    assert data["totalBuyQuantity"] == 0
    assert data["totalSellQuantity"] == 0
    assert data["netQuantity"] == 0


def test_account_summary_with_trades(client):
    """Statistics aggregate the account's trades."""
    account_id = _create_account(client)

    client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    })
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "MSFT",
        "side": "Sell",
        "quantity": 40,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["accountId"] == account_id
    assert data["totalTrades"] == 2
    assert data["settledTrades"] + data["pendingTrades"] <= data["totalTrades"]
    assert data["netQuantity"] == (
        data["totalBuyQuantity"] - data["totalSellQuantity"]
    )


def test_account_summary_scoped_to_account(client):
    """Trades on another account do not leak into the summary."""
    account_id = _create_account(client, "Account A")
    other_id = _create_account(client, "Account B")

    client.post("/trade/", json={
        "accountId": other_id,
        "security": "TSLA",
        "side": "Buy",
        "quantity": 10,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    assert resp.json()["totalTrades"] == 0


def test_account_summary_nonexistent_account(client):
    """Unknown accounts return 404."""
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404
