"""Tests for account CRUD operations."""
import pytest


def test_createAccount(client):
    """Test creating an account via POST and retrieving it."""
    resp = client.post("/account/", json={"displayName": "Test Account"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["displayName"] == "Test Account"
    assert "id" in data

    # retrieve it
    account_id = data['id']
    resp2 = client.get(f"/account/{account_id}")
    assert resp2.status_code == 200
    fetched = resp2.json()
    assert fetched['displayName'] == "Test Account"
    assert fetched["id"] == account_id


def test_list_accounts_empty(client):
    r = client.get('/account/')
    assert r.status_code == 200
    assert r.json() == []


def test_create_account_user_unknown_person_returns_404(client):
    """Regression: unknown username must not raise AttributeError (TRADER-DEMO-APP-4)."""
    acct = client.post("/account/", json={"displayName": "Acct"}).json()

    resp = client.post(
        "/accountuser/",
        json={"accountId": acct["id"], "username": "zzghost_user"},
    )

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Person not found"


def test_create_account_user_known_person(client):
    """Happy path: a valid person can be added as an account user."""
    acct = client.post("/account/", json={"displayName": "Acct"}).json()

    resp = client.post(
        "/accountuser/",
        json={"accountId": acct["id"], "username": "jsmith"},
    )

    assert resp.status_code == 200
    assert resp.json()["username"] == "jsmith"
