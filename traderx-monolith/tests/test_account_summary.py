"""Tests for the account summary statistics endpoint."""


def test_account_summary_counts_trades(client):
    account_id = client.post(
        "/account/", json={"displayName": "Summary Account"}
    ).json()["id"]

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
    stats = resp.json()
    assert stats["totalTrades"] == 2
    assert stats["settledTrades"] + stats["pendingTrades"] == 2
    assert (stats["netQuantity"]
            == stats["totalBuyQuantity"] - stats["totalSellQuantity"])


def test_account_summary_empty_account(client):
    account_id = client.post(
        "/account/", json={"displayName": "Empty Account"}
    ).json()["id"]

    stats = client.get(f"/account/{account_id}/summary").json()
    assert stats["totalTrades"] == 0
    assert stats["netQuantity"] == 0


def test_account_summary_unknown_account(client):
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404
