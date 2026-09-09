"""Tests for account summary statistics."""


def test_account_summary_empty(client):
    account = client.post("/account/", json={"displayName": "Empty Account"})
    assert account.status_code == 200
    account_id = account.json()["id"]

    response = client.get(f"/account/{account_id}/summary")

    assert response.status_code == 200
    summary = response.json()
    assert summary["accountId"] == account_id
    assert summary["totalTrades"] == 0
    assert summary["settledTrades"] == 0
    assert summary["pendingTrades"] == 0
    assert summary["netQuantity"] == 0


def test_account_summary_with_trades(client):
    account = client.post("/account/", json={"displayName": "Trading Account"})
    assert account.status_code == 200
    account_id = account.json()["id"]

    buy = client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    })
    sell = client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Sell",
        "quantity": 40,
    })
    assert buy.status_code == 200
    assert sell.status_code == 200

    response = client.get(f"/account/{account_id}/summary")

    assert response.status_code == 200
    summary = response.json()
    assert summary["totalTrades"] == 2
    assert summary["settledTrades"] + summary["pendingTrades"] == 2
    assert summary["totalBuyQuantity"] == 100
    assert summary["totalSellQuantity"] == 40
    assert summary["netQuantity"] == 60


def test_account_summary_not_found(client):
    response = client.get("/account/99999/summary")

    assert response.status_code == 404


def test_account_summary_tenant_isolation(client):
    account = client.post(
        "/account/",
        json={"displayName": "Acme Account"},
        headers={"X-Tenant-ID": "acme_corp"},
    )
    assert account.status_code == 200
    account_id = account.json()["id"]

    response = client.get(
        f"/account/{account_id}/summary",
        headers={"X-Tenant-ID": "globex_inc"},
    )

    assert response.status_code == 404
