"""Tests for the account summary statistics endpoint."""


def test_account_summary_empty_account(client):
    acct = client.post("/account/", json={"displayName": "Summary Account"})
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["accountId"] == account_id
    assert data["displayName"] == "Summary Account"
    assert data["totalTrades"] == 0
    assert data["settledTrades"] == 0
    assert data["pendingTrades"] == 0
    assert data["netQuantity"] == 0


def test_account_summary_counts_trades(client):
    acct = client.post("/account/", json={"displayName": "Active Account"})
    account_id = acct.json()["id"]

    for security, side, quantity in [("AAPL", "Buy", 100),
                                     ("MSFT", "Buy", 50),
                                     ("AAPL", "Sell", 30)]:
        r = client.post("/trade/", json={
            "accountId": account_id,
            "security": security,
            "side": side,
            "quantity": quantity,
        })
        assert r.status_code == 200

    data = client.get(f"/account/{account_id}/summary").json()
    assert data["totalTrades"] == 3
    assert data["settledTrades"] + data["pendingTrades"] == 3
    assert (data["totalBuyQuantity"] - data["totalSellQuantity"]
            == data["netQuantity"])


def test_account_summary_not_found(client):
    resp = client.get("/account/99999/summary")
    assert resp.status_code == 404


def test_account_summary_tenant_isolation(client):
    acct = client.post("/account/", json={"displayName": "Acme Account"},
                       headers={"X-Tenant-ID": "acme_corp"})
    account_id = acct.json()["id"]

    resp = client.get(f"/account/{account_id}/summary",
                      headers={"X-Tenant-ID": "globex_inc"})
    assert resp.status_code == 404
