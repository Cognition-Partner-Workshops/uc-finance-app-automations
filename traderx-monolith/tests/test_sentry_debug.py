"""Regression tests for the /sentry-debug endpoint (Sentry issue TRADER-DEMO-APP-9)."""


def test_sentry_debug_does_not_return_500(client):
    resp = client.get("/sentry-debug")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


def test_sentry_debug_does_not_crash_app(client):
    client.get("/sentry-debug")
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "UP"}
