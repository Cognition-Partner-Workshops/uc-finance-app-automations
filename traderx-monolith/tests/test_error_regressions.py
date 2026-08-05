"""Regression tests for runtime errors that must never reach the client."""
import sentry_sdk


def test_list_positions_for_account_without_positions(client):
    account_id = client.post("/account/", json={"displayName": "No Positions"}).json()["id"]

    resp = client.get(f"/positions/{account_id}")

    assert resp.status_code == 200
    assert resp.json() == []


def test_create_account_user_with_unknown_person(client):
    account_id = client.post("/account/", json={"displayName": "Acct"}).json()["id"]

    resp = client.post("/accountuser/", json={"accountId": account_id, "username": "nobody_xyz"})

    assert resp.status_code == 404
    assert "not found in People service" in resp.json()["detail"]


def test_selling_entire_position_closes_it_to_zero(client):
    account_id = client.post("/account/", json={"displayName": "Closer"}).json()["id"]
    trade = {"accountId": account_id, "security": "AAPL", "side": "Buy", "quantity": 10}
    assert client.post("/trade/", json=trade).status_code == 200

    trade["side"] = "Sell"
    resp = client.post("/trade/", json=trade)

    assert resp.status_code == 200
    positions = client.get(f"/positions/{account_id}").json()
    assert [p["quantity"] for p in positions] == [0]


def test_trade_analytics_without_sells(client):
    account_id = client.post("/account/", json={"displayName": "Buys Only"}).json()["id"]
    client.post("/trade/", json={"accountId": account_id, "security": "AAPL",
                                 "side": "Buy", "quantity": 5})

    resp = client.get("/analytics/trades")

    assert resp.status_code == 200
    assert resp.json()["buySellRatio"] == 1.0


def test_sentry_debug_reports_without_failing(client):
    resp = client.get("/sentry-debug")

    assert resp.status_code == 200
    assert resp.json() == {"status": "error captured"}


def test_sentry_debug_does_not_send_events_during_tests(client):
    resp = client.get("/sentry-debug")

    assert resp.status_code == 200
    assert not sentry_sdk.is_initialized()
