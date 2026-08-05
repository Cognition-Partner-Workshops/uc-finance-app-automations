"""Tests for the account summary statistics endpoint."""


def test_account_summary_returns_statistics(client):
    """Summary endpoint aggregates trade statistics for an account."""
    acct = client.post("/account/", json={"displayName": "Summary Account"})
    account_id = acct.json()["id"]

    client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    })
    client.post("/trade/", json={
        "accountId": account_id,
        "security": "MSFT",
        "side": "Buy",
        "quantity": 50,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    stats = resp.json()

    assert stats["totalTrades"] == 2
    assert stats["settledTrades"] + stats["pendingTrades"] <= stats["totalTrades"]
    assert "netQuantity" in stats
    assert "totalBuyQuantity" in stats
    assert "totalSellQuantity" in stats


def test_account_summary_empty_account(client):
    """An account with no trades returns zeroed statistics."""
    acct = client.post("/account/", json={"displayName": "Empty Account"})
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["totalTrades"] == 0
    assert stats["settledTrades"] == 0
    assert stats["pendingTrades"] == 0
    assert stats["netQuantity"] == 0


def test_account_summary_not_found(client):
    """A missing account returns 404."""
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
