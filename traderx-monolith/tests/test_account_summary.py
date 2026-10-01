"""Tests for the account summary statistics endpoint."""


def _create_account(client, name="Summary Account", tenant=None):
    headers = {"X-Tenant-ID": tenant} if tenant else None
    resp = client.post("/account/", json={"displayName": name}, headers=headers)
    assert resp.status_code == 200
    return resp.json()["id"]


def _submit_trade(client, accountId, side, quantity, security="AAPL"):
    resp = client.post("/trade/", json={
        "accountId": accountId,
        "security": security,
        "side": side,
        "quantity": quantity,
    })
    assert resp.status_code == 200
    return resp.json()["trade"]


def test_get_account_summary_empty(client):
    accountId = _create_account(client)

    resp = client.get(f"/account/{accountId}/summary")
    assert resp.status_code == 200
    assert resp.json() == {
        "accountId": accountId,
        "totalTrades": 0,
        "settledTrades": 0,
        "pendingTrades": 0,
        "totalBuyQuantity": 0,
        "totalSellQuantity": 0,
        "netQuantity": 0,
    }


def test_get_account_summary_with_trades(client):
    accountId = _create_account(client)
    trades = [
        _submit_trade(client, accountId, "Buy", 100),
        _submit_trade(client, accountId, "Buy", 50, security="MSFT"),
        _submit_trade(client, accountId, "Sell", 30),
    ]
    settled = [t for t in trades if t["state"] == "Settled"]
    expectedBuy = sum(t["quantity"] for t in settled if t["side"] == "Buy")
    expectedSell = sum(t["quantity"] for t in settled if t["side"] == "Sell")

    resp = client.get(f"/account/{accountId}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["accountId"] == accountId
    assert data["totalTrades"] == 3
    assert data["settledTrades"] == len(settled)
    assert data["pendingTrades"] == 3 - len(settled)
    assert data["totalBuyQuantity"] == expectedBuy
    assert data["totalSellQuantity"] == expectedSell
    assert data["netQuantity"] == expectedBuy - expectedSell


def test_get_account_summary_not_found(client):
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404


def test_get_account_summary_tenant_isolation(client):
    accountId = _create_account(client, tenant="acme_corp")

    resp = client.get(f"/account/{accountId}/summary",
                      headers={"X-Tenant-ID": "globex_inc"})
    assert resp.status_code == 404
