"""Account summary API regression tests."""
import pytest

from app.models.trade import Trade
from tests.conftest import TestingSessionLocal


def test_account_summary_empty(client):
    accountId = client.post("/account/", json={"displayName": "Empty"}).json()["id"]
    response = client.get(f"/account/{accountId}/summary")
    assert response.status_code == 200
    assert response.json() == {
        "totalTrades": 0, "settledTrades": 0, "pendingTrades": 0,
        "totalBuyQuantity": 0, "totalSellQuantity": 0, "netQuantity": 0,
    }


def test_account_summary_settled_trades_and_account_isolation(client):
    accountId = client.post("/account/", json={"displayName": "Trading"}).json()["id"]
    otherId = client.post("/account/", json={"displayName": "Other"}).json()["id"]
    for targetId, side, quantity in [
        (accountId, "Buy", 100), (accountId, "Buy", 200),
        (accountId, "Sell", 50), (otherId, "Buy", 999),
    ]:
        response = client.post("/trade/", json={
            "accountId": targetId, "security": "AAPL",
            "side": side, "quantity": quantity,
        })
        assert response.status_code == 200
    response = client.get(f"/account/{accountId}/summary")
    assert response.status_code == 200
    assert response.json() == {
        "totalTrades": 3, "settledTrades": 3, "pendingTrades": 0,
        "totalBuyQuantity": 300, "totalSellQuantity": 50, "netQuantity": 250,
    }


def test_account_summary_pending_workflow(client):
    headers = {"X-Tenant-ID": "initech"}
    accountId = client.post(
        "/account/", json={"displayName": "Pending"}, headers=headers
    ).json()["id"]
    for side in ["Buy", "Sell"]:
        response = client.post("/trade/", headers=headers, json={
            "accountId": accountId, "security": "AAPL",
            "side": side, "quantity": 100,
        })
        assert response.status_code == 200
    response = client.get(f"/account/{accountId}/summary", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "totalTrades": 2, "settledTrades": 0, "pendingTrades": 2,
        "totalBuyQuantity": 0, "totalSellQuantity": 0, "netQuantity": 0,
    }


def test_account_summary_mixed_states(client):
    accountId = client.post("/account/", json={"displayName": "Mixed"}).json()["id"]
    with TestingSessionLocal() as db:
        for state, side, quantity in [
            ("New", "Buy", 100), ("Processing", "Sell", 50),
            ("Cancelled", "Buy", 999), ("Settled", "Sell", 25),
        ]:
            db.add(Trade(account_id=accountId, tenant_id="acme_corp",
                         security="AAPL", side=side, quantity=quantity, state=state))
        db.commit()
    response = client.get(f"/account/{accountId}/summary")
    assert response.status_code == 200
    assert response.json() == {
        "totalTrades": 4, "settledTrades": 1, "pendingTrades": 2,
        "totalBuyQuantity": 0, "totalSellQuantity": 25, "netQuantity": -25,
    }


def test_account_summary_other_tenant_not_found(client):
    accountId = client.post("/account/", json={"displayName": "Private"}).json()["id"]
    response = client.get(f"/account/{accountId}/summary",
                          headers={"X-Tenant-ID": "globex_inc"})
    assert response.status_code == 404
    assert response.json() == {"detail": f"Account {accountId} not found"}


@pytest.mark.parametrize("accountId, statusCode", [(99999, 404), ("invalid", 422)])
def test_account_summary_invalid_account(client, accountId, statusCode):
    response = client.get(f"/account/{accountId}/summary")
    assert response.status_code == statusCode
