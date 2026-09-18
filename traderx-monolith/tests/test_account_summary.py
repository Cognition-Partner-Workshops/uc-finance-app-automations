"""Tests for the account summary endpoint."""


def test_account_summary_empty(client):
    acct = client.post("/account/", json={"displayName": "Empty Account"})
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["accountId"] == account_id
    assert body["statistics"] == {
        "totalTrades": 0,
        "settledTrades": 0,
        "pendingTrades": 0,
        "totalBuyQuantity": 0,
        "totalSellQuantity": 0,
        "netQuantity": 0,
    }


def test_account_summary_counts_trades(client):
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
    assert stats["netQuantity"] == (
        stats["totalBuyQuantity"] - stats["totalSellQuantity"]
    )


def test_account_summary_not_found(client):
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404


def test_account_summary_is_tenant_scoped(client):
    acct = client.post("/account/", json={"displayName": "Acme Account"},
                       headers={"X-Tenant-ID": "acme_corp"})
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary",
                      headers={"X-Tenant-ID": "globex_inc"})
    assert resp.status_code == 404
