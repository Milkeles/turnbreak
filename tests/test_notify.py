from turnbreak.core.notify import notify_native


def test_notify_native_returns_false_when_disabled_by_env(monkeypatch):
    monkeypatch.setenv("TURNBREAK_NO_NOTIFY", "1")
    assert notify_native() is False


def test_notify_native_returns_false_when_command_missing(monkeypatch):
    monkeypatch.delenv("TURNBREAK_NO_NOTIFY", raising=False)
    monkeypatch.setattr("turnbreak.core.notify.shutil.which", lambda command: None)
    assert notify_native() is False


def test_notify_native_returns_false_on_unknown_platform(monkeypatch):
    monkeypatch.delenv("TURNBREAK_NO_NOTIFY", raising=False)
    monkeypatch.setattr("turnbreak.core.notify.platform.system", lambda: "Plan9")
    assert notify_native() is False
