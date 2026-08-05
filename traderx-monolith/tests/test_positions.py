"""Tests for position endpoints."""


def test_list_positions_by_account_empty(client):
    """Regression test for TRADER-DEMO-APP-6: ValueError when account has no positions."""
    resp = client.get("/positions/4")
    assert resp.status_code == 200
    assert resp.json() == []
