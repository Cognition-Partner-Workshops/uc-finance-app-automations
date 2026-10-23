def create_trade(client, account_id, security, side, quantity, headers=None):
    return client.post(
        "/trade/",
        json={
            "accountId": account_id,
            "security": security,
            "side": side,
            "quantity": quantity,
        },
        headers=headers,
    )


def test_account_summary_for_empty_account(client):
    account = client.post("/account/", json={"displayName": "Empty Account"})
    account_id = account.json()["id"]

    response = client.get(f"/account/{account_id}/summary")

    assert response.status_code == 200
    assert response.json() == {
        "accountId": account_id,
        "displayName": "Empty Account",
        "totalTrades": 0,
        "settledTrades": 0,
        "pendingTrades": 0,
        "totalBuyQuantity": 0,
        "totalSellQuantity": 0,
        "netQuantity": 0,
    }


def test_account_summary_for_settled_trades(client):
    account = client.post("/account/", json={"displayName": "Trading Account"})
    account_id = account.json()["id"]

    for security, side, quantity in (
        ("AAPL", "Buy", 100),
        ("MSFT", "Buy", 50),
        ("AAPL", "Sell", 30),
    ):
        response = create_trade(client, account_id, security, side, quantity)
        assert response.status_code == 200

    response = client.get(f"/account/{account_id}/summary")

    assert response.status_code == 200
    assert response.json() == {
        "accountId": account_id,
        "displayName": "Trading Account",
        "totalTrades": 3,
        "settledTrades": 3,
        "pendingTrades": 0,
        "totalBuyQuantity": 150,
        "totalSellQuantity": 30,
        "netQuantity": 120,
    }


def test_account_summary_for_pending_trades(client):
    headers = {"X-Tenant-ID": "initech"}
    account = client.post(
        "/account/",
        json={"displayName": "Pending Account"},
        headers=headers,
    )
    account_id = account.json()["id"]

    for security, quantity in (("AAPL", 100), ("MSFT", 50)):
        response = create_trade(
            client, account_id, security, "Buy", quantity, headers
        )
        assert response.status_code == 200

    response = client.get(
        f"/account/{account_id}/summary",
        headers=headers,
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


def test_account_summary_returns_404_for_unknown_account(client):
    response = client.get("/account/999999/summary")

    assert response.status_code == 404
    assert response.json()["detail"] == "Account 999999 not found"


def test_account_summary_is_tenant_isolated(client):
    account = client.post("/account/", json={"displayName": "Acme Account"})
    account_id = account.json()["id"]

    response = client.get(
        f"/account/{account_id}/summary",
        headers={"X-Tenant-ID": "globex_inc"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == f"Account {account_id} not found"
