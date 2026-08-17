from __future__ import annotations

import signal
from pathlib import Path

import pytest

from turnbreak.core import server_control


class FakePopen:
    def __init__(self, args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs
        self.pid = 4242


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


def test_pid_path_lives_under_config_dir(home):
    assert server_control.pid_path() == home / ".config" / "turnbreak" / "server.pid"


def test_spawn_server_writes_pid_file(home, monkeypatch):
    monkeypatch.setattr(server_control.subprocess, "Popen", FakePopen)

    server_control.spawn_server(1234)

    assert server_control.pid_path().read_text() == "4242"


def test_spawn_server_runs_the_child_in_foreground_mode(home, monkeypatch):
    captured = {}

    def fake_popen(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return FakePopen(args, **kwargs)

    monkeypatch.setattr(server_control.subprocess, "Popen", fake_popen)

    server_control.spawn_server(1234)

    args = captured["args"]
    assert "serve" in args
    assert "--port" in args
    assert args[args.index("--port") + 1] == "1234"
    assert "--foreground" in args


def test_spawn_server_detaches_the_process(home, monkeypatch):
    captured = {}

    def fake_popen(args, **kwargs):
        captured["kwargs"] = kwargs
        return FakePopen(args, **kwargs)

    monkeypatch.setattr(server_control.subprocess, "Popen", fake_popen)

    server_control.spawn_server(1234)

    assert captured["kwargs"]["start_new_session"] is True


def test_stop_server_returns_false_when_no_pid_file(home):
    assert server_control.stop_server() is False


def test_stop_server_signals_the_recorded_pid_and_clears_the_file(home, monkeypatch):
    server_control.pid_path().parent.mkdir(parents=True)
    server_control.pid_path().write_text("4242")
    calls = []
    monkeypatch.setattr(server_control.os, "kill", lambda pid, sig: calls.append((pid, sig)))

    result = server_control.stop_server()

    assert result is True
    assert calls == [(4242, signal.SIGTERM)]
    assert not server_control.pid_path().exists()


def test_stop_server_returns_false_when_the_recorded_process_is_already_gone(home, monkeypatch):
    server_control.pid_path().parent.mkdir(parents=True)
    server_control.pid_path().write_text("4242")

    def boom(pid, sig):
        raise ProcessLookupError

    monkeypatch.setattr(server_control.os, "kill", boom)

    assert server_control.stop_server() is False
    assert not server_control.pid_path().exists()


def test_client_count_returns_none_when_nothing_listening(home):
    assert server_control.client_count(1) is None
