def test_get_account_summary_empty(client):
    account_response = client.post(
        "/account/", json={"displayName": "Empty Account"}
    )
    account = account_response.json()

    response = client.get(f"/account/{account['id']}/summary")

    assert response.status_code == 200
    assert response.json() == {
        "accountId": account["id"],
        "displayName": "Empty Account",
        "totalTrades": 0,
        "settledTrades": 0,
        "pendingTrades": 0,
        "totalBuyQuantity": 0,
        "totalSellQuantity": 0,
        "netQuantity": 0,
    }


def test_get_account_summary_with_trades(client):
    account_response = client.post(
        "/account/", json={"displayName": "Trading Account"}
    )
    account_id = account_response.json()["id"]

    for security, side, quantity in [
        ("AAPL", "Buy", 100),
        ("MSFT", "Buy", 200),
        ("AAPL", "Sell", 50),
    ]:
        trade_response = client.post("/trade/", json={
            "accountId": account_id,
            "security": security,
            "side": side,
            "quantity": quantity,
        })
        assert trade_response.status_code == 200

    response = client.get(f"/account/{account_id}/summary")

    assert response.status_code == 200
    assert response.json() == {
        "accountId": account_id,
        "displayName": "Trading Account",
        "totalTrades": 3,
        "settledTrades": 3,
        "pendingTrades": 0,
        "totalBuyQuantity": 300,
        "totalSellQuantity": 50,
        "netQuantity": 250,
    }


def test_get_account_summary_pending_trades(client):
    tenant_headers = {"X-Tenant-ID": "initech"}
    account_response = client.post(
        "/account/",
        json={"displayName": "Pending Account"},
        headers=tenant_headers,
    )
    account_id = account_response.json()["id"]

    for security, side, quantity in [
        ("AAPL", "Buy", 100),
        ("MSFT", "Sell", 50),
    ]:
        trade_response = client.post(
            "/trade/",
            json={
                "accountId": account_id,
                "security": security,
                "side": side,
                "quantity": quantity,
            },
            headers=tenant_headers,
        )
        assert trade_response.status_code == 200
        assert trade_response.json()["trade"]["state"] == "Processing"

    response = client.get(
        f"/account/{account_id}/summary", headers=tenant_headers
    )

    assert response.status_code == 200
    assert response.json() == {
        "accountId": account_id,
        "displayName": "Pending Account",
        "totalTrades": 2,
        "settledTrades": 0,
        "pendingTrades": 2,
        "totalBuyQuantity": 0,
        "totalSellQuantity": 0,
        "netQuantity": 0,
    }


def test_get_account_summary_not_found(client):
    response = client.get("/account/99999/summary")

    assert response.status_code == 404


def test_get_account_summary_tenant_isolation(client):
    account_response = client.post(
        "/account/", json={"displayName": "Acme Account"}
    )
    account_id = account_response.json()["id"]

    response = client.get(
        f"/account/{account_id}/summary",
        headers={"X-Tenant-ID": "globex_inc"},
    )

    assert response.status_code == 404
