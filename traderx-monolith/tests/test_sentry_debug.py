"""Regression tests for the /sentry-debug endpoint (Sentry issue TRADER-DEMO-APP-1)."""


def test_sentry_debug_returns_handled_500(client):
    """The endpoint must not raise an unhandled ZeroDivisionError."""
    response = client.get("/sentry-debug")
    assert response.status_code == 500
    assert response.json() == {"detail": "Sentry demo error triggered"}


def test_server_survives_sentry_debug(client):
    """The app keeps serving requests after the demo error is triggered."""
    client.get("/sentry-debug")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}
