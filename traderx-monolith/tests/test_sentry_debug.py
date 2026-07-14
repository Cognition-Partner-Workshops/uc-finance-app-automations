"""Regression tests for the /sentry-debug endpoint.

Guards against the ZeroDivisionError reported in Sentry issue TRADER-DEMO-APP-1
(https://cognition-workshops.sentry.io/issues/7609233139/), where an unguarded
`1 / 0` in trigger_error raised an unhandled 500.
"""


def test_sentry_debug_does_not_raise_zero_division(client):
    resp = client.get("/sentry-debug")
    assert resp.status_code == 200
    assert resp.json() == {"result": None}
