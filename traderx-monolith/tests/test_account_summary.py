"""Tests for the account summary statistics endpoint."""


def test_account_summary_empty_account(client):
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


def test_account_summary_counts_trades(client):
    acct = client.post("/account/", json={"displayName": "Busy Account"})
    account_id = acct.json()["id"]

    for side, quantity in (("Buy", 100), ("Buy", 50), ("Sell", 30)):
        r = client.post("/trade/", json={
            "accountId": account_id,
            "security": "AAPL",
            "side": side,
            "quantity": quantity,
        })
        assert r.status_code == 200

    stats = client.get(f"/account/{account_id}/summary").json()["statistics"]
    assert stats["totalTrades"] == 3
    assert stats["settledTrades"] + stats["pendingTrades"] == 3
    assert stats["netQuantity"] == (
        stats["totalBuyQuantity"] - stats["totalSellQuantity"]
    )


def test_account_summary_not_found(client):
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404


def test_account_summary_is_tenant_scoped(client):
    acct = client.post(
        "/account/",
        json={"displayName": "Tenant A Account"},
        headers={"X-Tenant-ID": "tenant-a"},
    )
    account_id = acct.json()["id"]

    resp = client.get(
        f"/account/{account_id}/summary",
        headers={"X-Tenant-ID": "tenant-b"},
    )
    assert resp.status_code == 404
