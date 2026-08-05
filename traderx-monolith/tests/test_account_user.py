"""Tests for account user endpoints."""


def _create_account(client):
    resp = client.post("/account/", json={"displayName": "Test Account"})
    assert resp.status_code == 200
    return resp.json()["id"]


def test_create_account_user_unknown_person_returns_404(client):
    """Regression test for TRADER-DEMO-APP-4: unknown username must not 500."""
    account_id = _create_account(client)
    resp = client.post(
        "/accountuser/",
        json={"accountId": account_id, "username": "anobody_xyz"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Person not found"


def test_create_account_user_known_person(client):
    account_id = _create_account(client)
    resp = client.post(
        "/accountuser/",
        json={"accountId": account_id, "username": "jsmith"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "jsmith"
