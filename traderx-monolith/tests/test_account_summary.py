"""Tests for GET /account/{account_id}/summary."""
from app.models.trade import Trade
from tests.conftest import TestingSessionLocal


def _createAccount(client, name="Summary Account", tenant=None):
    headers = {"X-Tenant-ID": tenant} if tenant else {}
    resp = client.post("/account/", json={"displayName": name}, headers=headers)
    assert resp.status_code == 200
    return resp.json()["id"]


def _addTrades(accountId, trades, tenantId="acme_corp"):
    db = TestingSessionLocal()
    try:
        for security, side, quantity, state in trades:
            db.add(Trade(tenant_id=tenantId, account_id=accountId,
                         security=security, side=side,
                         quantity=quantity, state=state))
        db.commit()
    finally:
        db.close()


def test_summary_aggregates_trade_statistics(client):
    accountId = _createAccount(client)
    _addTrades(accountId, [
        ("AAPL", "Buy", 100, "Settled"),
        ("MSFT", "Buy", 50, "Settled"),
        ("AAPL", "Sell", 30, "Settled"),
        ("IBM", "Buy", 10, "New"),
        ("GOOG", "Sell", 5, "Processing"),
        ("TSLA", "Buy", 7, "Cancelled"),
    ])

    resp = client.get(f"/account/{accountId}/summary")
    assert resp.status_code == 200
    assert resp.json() == {
        "accountId": accountId,
        "totalTrades": 6,
        "settledTrades": 3,
        "pendingTrades": 2,
        "totalBuyQuantity": 150,
        "totalSellQuantity": 30,
        "netQuantity": 120,
    }


def test_summary_for_account_without_trades(client):
    accountId = _createAccount(client)
    resp = client.get(f"/account/{accountId}/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["totalTrades"] == 0
    assert body["settledTrades"] == 0
    assert body["pendingTrades"] == 0
    assert body["netQuantity"] == 0


def test_summary_reflects_submitted_trades(client):
    accountId = _createAccount(client)
    tradeResp = client.post("/trade/", json={
        "accountId": accountId, "security": "AAPL",
        "side": "Buy", "quantity": 25,
    })
    assert tradeResp.status_code == 200

    body = client.get(f"/account/{accountId}/summary").json()
    assert body["totalTrades"] == 1
    assert body["settledTrades"] + body["pendingTrades"] == 1


def test_summary_unknown_account_returns_404(client):
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404


def test_summary_is_tenant_scoped(client):
    accountId = _createAccount(client, tenant="acme_corp")
    _addTrades(accountId, [("AAPL", "Buy", 100, "Settled")])

    resp = client.get(f"/account/{accountId}/summary",
                      headers={"X-Tenant-ID": "globex_inc"})
    assert resp.status_code == 404
