"""Tests for account user operations."""


def _create_account(client):
    resp = client.post("/account/", json={"displayName": "Test Account"})
    assert resp.status_code == 200
    return resp.json()["id"]


def test_create_account_user(client):
    """A known person can be granted access to an account."""
    account_id = _create_account(client)
    resp = client.post("/accountuser/",
                       json={"accountId": account_id, "username": "jsmith"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "jsmith"


def test_create_account_user_unknown_person(client):
    """An unknown username returns 404 instead of crashing (TRADER-DEMO-APP-4)."""
    account_id = _create_account(client)
    resp = client.post("/accountuser/",
                       json={"accountId": account_id, "username": "demo"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Person not found"
