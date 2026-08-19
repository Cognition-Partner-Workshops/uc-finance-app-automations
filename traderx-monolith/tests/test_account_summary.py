"""Tests for the account summary statistics endpoint."""


def test_summary_empty_account(client):
    acct = client.post("/account/", json={"displayName": "Summary Account"})
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["accountId"] == account_id
    assert body["displayName"] == "Summary Account"
    assert body["statistics"] == {
        "totalTrades": 0,
        "settledTrades": 0,
        "pendingTrades": 0,
        "totalBuyQuantity": 0,
        "totalSellQuantity": 0,
        "netQuantity": 0,
    }


def test_summary_counts_trades(client):
    acct = client.post("/account/", json={"displayName": "Busy Account"})
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

    stats = client.get(f"/account/{account_id}/summary").json()["statistics"]
    assert stats["totalTrades"] == 2
    assert stats["settledTrades"] + stats["pendingTrades"] == 2
    assert (stats["netQuantity"]
            == stats["totalBuyQuantity"] - stats["totalSellQuantity"])


def test_summary_unknown_account(client):
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404
