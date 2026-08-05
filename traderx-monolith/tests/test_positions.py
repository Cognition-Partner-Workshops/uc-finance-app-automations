"""Regression tests for position endpoints (Sentry TRADER-DEMO-APP-6)."""


def test_list_positions_by_account_empty(client):
    """GET /positions/{account_id} with no positions must not raise ValueError."""
    resp = client.get("/positions/8648")
    assert resp.status_code == 200
    assert resp.json() == []
