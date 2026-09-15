"""Tests for GET /account/{id}/summary."""


def _submit(client, account_id, side, quantity):
    resp = client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": side,
        "quantity": quantity,
    })
    assert resp.status_code == 200
    return resp.json()["trade"]


def test_summary_not_found(client):
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404


def test_summary_empty_account(client):
    acct = client.post("/account/", json={"displayName": "Empty"})
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    assert resp.json() == {
        "accountId": account_id,
        "positionCount": 0,
        "totalTrades": 0,
        "settledTrades": 0,
        "pendingTrades": 0,
        "totalBuyQuantity": 0,
        "totalSellQuantity": 0,
        "netQuantity": 0,
    }


def test_summary_aggregates_trades(client):
    acct = client.post("/account/", json={"displayName": "Active"})
    account_id = acct.json()["id"]

    trades = [
        _submit(client, account_id, "Buy", 100),
        _submit(client, account_id, "Buy", 50),
        _submit(client, account_id, "Sell", 30),
    ]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()

    settled = [t for t in trades if t["state"] == "Settled"]
    pending = [t for t in trades if t["state"] in ("New", "Processing")]
    buy_qty = sum(t["quantity"] for t in settled if t["side"] == "Buy")
    sell_qty = sum(t["quantity"] for t in settled if t["side"] == "Sell")

    assert data["totalTrades"] == 3
    assert data["settledTrades"] == len(settled)
    assert data["pendingTrades"] == len(pending)
    assert data["totalBuyQuantity"] == buy_qty
    assert data["totalSellQuantity"] == sell_qty
    assert data["netQuantity"] == buy_qty - sell_qty


def test_summary_is_tenant_scoped(client):
    acct = client.post("/account/", json={"displayName": "Tenant A"})
    account_id = acct.json()["id"]
    _submit(client, account_id, "Buy", 10)

    resp = client.get(f"/account/{account_id}/summary",
                      headers={"X-Tenant-ID": "other-tenant"})
    assert resp.status_code == 404
