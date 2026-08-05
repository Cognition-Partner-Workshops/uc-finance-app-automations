"""Regression test for the /sentry-debug endpoint (Sentry issue TRADER-DEMO-APP-8)."""


def test_sentry_debug_does_not_raise(client):
    """GET /sentry-debug must not propagate ZeroDivisionError to the client."""
    response = client.get("/sentry-debug")
    assert response.status_code == 200
    assert response.json() == {"status": "error captured"}
