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


def test_create_account_user_unknown_person(client):
    """Regression: unknown username must not crash (TRADER-DEMO-APP-4).

    get_person returns None for an unrecognized logon id; the endpoint
    previously raised AttributeError accessing person.full_name.
    """
    acct = client.post("/account/", json={"displayName": "Regression Acct"})
    assert acct.status_code == 200
    account_id = acct.json()["id"]

    resp = client.post(
        "/accountuser/",
        json={"accountId": account_id, "username": "demo_user"},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "demo_user"
