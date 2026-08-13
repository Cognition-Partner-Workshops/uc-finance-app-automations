"""Tests for the account summary statistics endpoint."""


def test_account_summary_reflects_trades(client):
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
        "security": "AAPL",
        "side": "Sell",
        "quantity": 40,
    })

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["accountId"] == account_id
    assert body["displayName"] == "Summary Account"

    stats = body["statistics"]
    assert stats["totalTrades"] == 2
    assert stats["settledTrades"] + stats["pendingTrades"] == 2
    assert stats["netQuantity"] == (
        stats["totalBuyQuantity"] - stats["totalSellQuantity"]
    )


def test_account_summary_empty_account(client):
    acct = client.post("/account/", json={"displayName": "Empty Account"})
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    stats = resp.json()["statistics"]
    assert stats["totalTrades"] == 0
    assert stats["netQuantity"] == 0


def test_account_summary_missing_account(client):
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404
