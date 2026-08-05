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
    """Regression test for TRADER-DEMO-APP-4: unknown username caused an
    AttributeError on person.full_name instead of a 404."""
    resp = client.post("/accountuser/",
                       json={"accountId": 22214, "username": "demo_user"})
    assert resp.status_code == 404
    assert "demo_user" in resp.json()["detail"]


def test_create_account_user_known_person(client):
    resp = client.post("/accountuser/",
                       json={"accountId": 1, "username": "jsmith"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "jsmith"
