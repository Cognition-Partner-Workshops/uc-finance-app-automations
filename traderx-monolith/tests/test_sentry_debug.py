"""Regression test for the /sentry-debug endpoint (Sentry issue TRADER-DEMO-APP-8)."""


def test_sentry_debug_does_not_raise(client):
    response = client.get("/sentry-debug")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error captured"
    assert "division by zero" in body["error"]
