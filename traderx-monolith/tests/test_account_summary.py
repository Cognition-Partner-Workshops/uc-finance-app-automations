"""Integration tests for account summary statistics."""


def test_get_account_summary_empty(client):
    account = client.post("/account/", json={"displayName": "Empty Account"})
    assert account.status_code == 200
    account_id = account.json()["id"]

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


def test_get_account_summary_with_trades(client):
    account = client.post("/account/", json={"displayName": "Trading Account"})
    assert account.status_code == 200
    account_id = account.json()["id"]

    for security, side, quantity in [
        ("AAPL", "Buy", 100),
        ("MSFT", "Buy", 50),
        ("AAPL", "Sell", 30),
    ]:
        response = client.post("/trade/", json={
            "accountId": account_id,
            "security": security,
            "side": side,
            "quantity": quantity,
        })
        assert response.status_code == 200

    response = client.get(f"/account/{account_id}/summary")

    assert response.status_code == 200
    assert response.json() == {
        "accountId": account_id,
        "totalTrades": 3,
        "settledTrades": 3,
        "pendingTrades": 0,
        "totalBuyQuantity": 150,
        "totalSellQuantity": 30,
        "netQuantity": 120,
    }


def test_get_account_summary_pending_trades(client):
    headers = {"X-Tenant-ID": "initech"}
    account = client.post(
        "/account/",
        json={"displayName": "Pending Account"},
        headers=headers,
    )
    assert account.status_code == 200
    account_id = account.json()["id"]

    for security, quantity in [("AAPL", 100), ("MSFT", 50)]:
        response = client.post(
            "/trade/",
            json={
                "accountId": account_id,
                "security": security,
                "side": "Buy",
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
    assert response.json() == {
        "accountId": account_id,
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
    assert response.json()["detail"] == "Account 99999 not found"


def test_get_account_summary_tenant_isolation(client):
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
