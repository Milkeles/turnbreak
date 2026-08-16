import pytest


@pytest.fixture(autouse=True)
def no_browser_or_notify(monkeypatch):
    monkeypatch.setenv("TURNBREAK_NO_BROWSER", "1")
    monkeypatch.setenv("TURNBREAK_NO_NOTIFY", "1")
