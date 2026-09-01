def test_get_account_summary(client):
    acct = client.post("/account/", json={"displayName": "Summary Account"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    trades = [
        {
            "accountId": account_id,
            "security": "AAPL",
            "side": "Buy",
            "quantity": 100,
        },
        {
            "accountId": account_id,
            "security": "MSFT",
            "side": "Sell",
            "quantity": 25,
        },
    ]
    for trade in trades:
        response = client.post("/trade/", json=trade)
        assert response.status_code == 200

    response = client.get(f"/account/{account_id}/summary")
    assert response.status_code == 200
    statistics = response.json()["statistics"]
    assert {
        "totalTrades",
        "settledTrades",
        "pendingTrades",
        "totalBuyQuantity",
        "totalSellQuantity",
        "netQuantity",
    } <= statistics.keys()
    assert statistics["totalTrades"] == len(trades)


def test_get_account_summary_not_found(client):
    response = client.get("/account/99999/summary")
    assert response.status_code == 404


def test_get_account_summary_tenant_isolation(client):
    tenant_a = {"X-Tenant-ID": "tenant_a"}
    tenant_b = {"X-Tenant-ID": "tenant_b"}

    acct = client.post(
        "/account/",
        json={"displayName": "Tenant A Account"},
        headers=tenant_a,
    )
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    trade = client.post(
        "/trade/",
        json={
            "accountId": account_id,
            "security": "AAPL",
            "side": "Buy",
            "quantity": 100,
        },
        headers=tenant_a,
    )
    assert trade.status_code == 200

    response = client.get(
        f"/account/{account_id}/summary",
        headers=tenant_b,
    )
    assert response.status_code == 404
