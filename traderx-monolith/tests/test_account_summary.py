def test_account_summary_unknown_account_returns_404(client):
    response = client.get("/account/999/summary")

    assert response.status_code == 404


def test_account_summary_without_trades_returns_zero_statistics(client):
    account_response = client.post(
        "/account/",
        json={"displayName": "Empty Account"},
    )
    account_id = account_response.json()["id"]

    response = client.get(f"/account/{account_id}/summary")

    assert response.status_code == 200
    assert response.json() == {
        "accountId": account_id,
        "totalTrades": 0,
        "settledTrades": 0,
        "pendingTrades": 0,
        "totalBuyQuantity": 0,
        "totalSellQuantity": 0,
        "netQuantity": 0,
    }


def test_account_summary_reports_trade_statistics(client):
    headers = {"X-Tenant-ID": "acme_corp"}
    account_response = client.post(
        "/account/",
        json={"displayName": "Trading Account"},
        headers=headers,
    )
    account_id = account_response.json()["id"]

    for side, quantity in (("Buy", 100), ("Sell", 40)):
        response = client.post(
            "/trade/",
            json={
                "accountId": account_id,
                "security": "AAPL",
                "side": side,
                "quantity": quantity,
            },
            headers=headers,
        )
        assert response.status_code == 200

    response = client.get(
        f"/account/{account_id}/summary",
        headers=headers,
    )

    assert response.status_code == 200
    statistics = response.json()
    assert statistics["totalTrades"] == 2
    assert statistics["settledTrades"] + statistics["pendingTrades"] == 2
    assert statistics["totalBuyQuantity"] == 100
    assert statistics["totalSellQuantity"] == 40
    assert statistics["netQuantity"] == (
        statistics["totalBuyQuantity"] - statistics["totalSellQuantity"]
    )


def test_account_summary_is_isolated_by_tenant(client):
    account_response = client.post(
        "/account/",
        json={"displayName": "Tenant Account"},
        headers={"X-Tenant-ID": "acme_corp"},
    )
    account_id = account_response.json()["id"]

    response = client.get(
        f"/account/{account_id}/summary",
        headers={"X-Tenant-ID": "initech"},
    )

    assert response.status_code == 404
