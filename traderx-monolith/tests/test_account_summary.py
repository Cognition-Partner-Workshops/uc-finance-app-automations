"""Tests for the account summary statistics endpoint."""


def _create_account(client, display_name="Summary Account"):
    resp = client.post("/account/", json={"displayName": display_name})
    assert resp.status_code == 200
    return resp.json()["id"]


def test_account_summary_empty_account(client):
    account_id = _create_account(client)

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
    account_id = _create_account(client)

    for security, side, quantity in [
        ("AAPL", "Buy", 100),
        ("AAPL", "Sell", 40),
        ("MSFT", "Buy", 25),
    ]:
        resp = client.post("/trade/", json={
            "accountId": account_id,
            "security": security,
            "side": side,
            "quantity": quantity,
        })
        assert resp.status_code == 200

    stats = client.get(f"/account/{account_id}/summary").json()["statistics"]
    assert stats["totalTrades"] == 3
    assert stats["settledTrades"] + stats["pendingTrades"] == 3
    assert stats["netQuantity"] == (
        stats["totalBuyQuantity"] - stats["totalSellQuantity"]
    )


def test_account_summary_not_found(client):
    resp = client.get("/account/999999/summary")
    assert resp.status_code == 404


def test_account_summary_is_tenant_scoped(client):
    resp = client.post("/account/", json={"displayName": "Acme"},
                       headers={"X-Tenant-ID": "acme_corp"})
    account_id = resp.json()["id"]

    same_tenant = client.get(f"/account/{account_id}/summary",
                             headers={"X-Tenant-ID": "acme_corp"})
    assert same_tenant.status_code == 200

    other_tenant = client.get(f"/account/{account_id}/summary",
                              headers={"X-Tenant-ID": "globex_inc"})
    assert other_tenant.status_code == 404
