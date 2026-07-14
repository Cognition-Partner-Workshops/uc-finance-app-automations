import pytest


def test_submitTrade(client):
    # create an account first
    acct = client.post("/account/", json={'displayName': 'Trading Account'})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    resp = client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 100,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body['success'] is True
    assert body["trade"]["state"] in ("New", "Settled")
    assert body["trade"]['quantity'] == 100


def test_submit_trade_buy(client):
    """Verify a basic buy trade works end to end"""
    acct = client.post("/account/",
                       json={"displayName": "Another Account"})
    account_id = acct.json()['id']

    result = client.post('/trade/', json={
          "accountId": account_id,
          "security": "MSFT",
          "side": "Buy",
          "quantity": 50
    })
    assert result.status_code == 200
    data = result.json()
    assert data["success"] == True
    assert data["trade"]["security"] == "MSFT"


def test_sell_full_position_to_zero(client):
    """Regression: selling the full position brings quantity to 0 and must not
    raise ZeroDivisionError when computing the position change percentage
    (Sentry TRADER-DEMO-APP-5)."""
    acct = client.post("/account/", json={"displayName": "Zero Position Acct"})
    account_id = acct.json()["id"]

    buy = client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Buy",
        "quantity": 70,
    })
    assert buy.status_code == 200

    sell = client.post("/trade/", json={
        "accountId": account_id,
        "security": "AAPL",
        "side": "Sell",
        "quantity": 70,
    })
    assert sell.status_code == 200
    data = sell.json()
    assert data["success"] is True
    assert data["position"]["quantity"] == 0
