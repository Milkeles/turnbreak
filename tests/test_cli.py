from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import pytest

from turnbreak import cli
from turnbreak.core import state
from turnbreak.core.config import load_config


class FakePopen:
    calls: list[dict] = []

    def __init__(self, args, **kwargs):
        FakePopen.calls.append({"args": args, "kwargs": kwargs})


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


@pytest.fixture(autouse=True)
def fake_popen(monkeypatch):
    FakePopen.calls = []
    monkeypatch.setattr(cli.subprocess, "Popen", FakePopen)
    return FakePopen


@pytest.fixture(autouse=True)
def fake_push_done_signal(monkeypatch):
    calls: list[tuple[int, str]] = []

    def fake(port: int, session_id: str, timeout: float = 0.5) -> bool:
        calls.append((port, session_id))
        return False

    monkeypatch.setattr(cli, "push_done_signal", fake)
    return calls


def test_cmd_start_writes_only_json_to_stdout(capsys):
    cli.cmd_start("abc")
    out = capsys.readouterr().out
    lines = out.strip("\n").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {"ok": True}


def test_cmd_start_spawns_watcher_without_blocking(fake_popen):
    cli.cmd_start("abc")
    assert len(fake_popen.calls) == 1
    call = fake_popen.calls[0]
    args = call["args"]
    assert "--session-id" in args
    assert args[args.index("--session-id") + 1] == "abc"
    assert "--turn-start" in args
    assert call["kwargs"]["start_new_session"] is True
    assert call["kwargs"]["stdin"] == subprocess.DEVNULL
    assert call["kwargs"]["stdout"] == subprocess.DEVNULL
    assert call["kwargs"]["stderr"] == subprocess.DEVNULL


def test_cmd_start_returns_quickly():
    started = time.monotonic()
    cli.cmd_start("abc")
    elapsed = time.monotonic() - started
    assert elapsed < 0.05


def test_cmd_start_records_session_state():
    cli.cmd_start("abc")
    recorded = state.load_state()
    assert recorded is not None
    assert recorded.session_id == "abc"
    assert recorded.turn_ended is False


def test_cmd_stop_writes_only_json_to_stdout(capsys):
    cli.cmd_start("abc")
    capsys.readouterr()
    cli.cmd_stop("abc")
    out = capsys.readouterr().out
    lines = out.strip("\n").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {"ok": True}


def test_cmd_stop_marks_state_ended():
    cli.cmd_start("abc")
    cli.cmd_stop("abc")
    ended = state.load_state()
    assert ended is not None
    assert ended.turn_ended is True


def test_cmd_stop_pushes_done_signal(fake_push_done_signal):
    cli.cmd_start("abc")
    cli.cmd_stop("abc")
    assert fake_push_done_signal == [(7717, "abc")]


def test_cmd_serve_foreground_runs_serve_forever(monkeypatch):
    calls = []
    monkeypatch.setattr(cli, "serve_forever", lambda port: calls.append(port))

    rc = cli.cmd_serve(1234, foreground=True)

    assert rc == 0
    assert calls == [1234]


def test_cmd_serve_rejects_foreground_and_stop_together(capsys):
    rc = cli.cmd_serve(None, foreground=True, stop=True)

    assert rc == 2
    assert "--foreground and --stop" in capsys.readouterr().err


def test_cmd_serve_stop_reports_success(monkeypatch, capsys):
    monkeypatch.setattr(cli, "stop_server", lambda: True)

    rc = cli.cmd_serve(1234, stop=True)

    assert rc == 0
    assert "Stopped" in capsys.readouterr().out


def test_cmd_serve_stop_reports_when_nothing_was_running(monkeypatch, capsys):
    monkeypatch.setattr(cli, "stop_server", lambda: False)

    rc = cli.cmd_serve(1234, stop=True)

    assert rc == 1
    assert "No running turnbreak server" in capsys.readouterr().err


def test_cmd_serve_background_spawns_when_nothing_is_running(monkeypatch, capsys):
    monkeypatch.setattr(cli, "client_count", lambda port: None)
    spawn_calls = []
    tab_calls = []
    monkeypatch.setattr(cli, "spawn_server", lambda port: spawn_calls.append(port))
    monkeypatch.setattr(cli, "open_reading_tab", lambda url: tab_calls.append(url))
    monkeypatch.setattr(cli.time, "sleep", lambda seconds: None)

    rc = cli.cmd_serve(1234)

    assert rc == 0
    assert spawn_calls == [1234]
    assert tab_calls == ["http://127.0.0.1:1234/"]
    assert capsys.readouterr().out == "http://127.0.0.1:1234/\n"


def test_cmd_serve_background_does_not_spawn_when_already_running(monkeypatch):
    monkeypatch.setattr(cli, "client_count", lambda port: 0)
    spawn_calls = []
    monkeypatch.setattr(cli, "spawn_server", lambda port: spawn_calls.append(port))
    monkeypatch.setattr(cli, "open_reading_tab", lambda url: None)

    cli.cmd_serve(1234)

    assert spawn_calls == []


def test_main_with_no_args_raises_system_exit():
    with pytest.raises(SystemExit):
        cli.main([])


def test_main_dispatches_start():
    exit_code = cli.main(["start", "--session-id", "abc"])
    assert exit_code == 0
    recorded = state.load_state()
    assert recorded is not None
    assert recorded.session_id == "abc"


def test_main_dispatches_stop():
    cli.cmd_start("abc")
    exit_code = cli.main(["stop", "--session-id", "abc"])
    assert exit_code == 0
    ended = state.load_state()
    assert ended is not None
    assert ended.turn_ended is True


def test_cmd_mode_folder_requires_a_path():
    exit_code = cli.cmd_mode("folder", None)
    assert exit_code == 1


def test_cmd_mode_folder_sets_mode_and_path():
    exit_code = cli.cmd_mode("folder", "/home/user/reading")
    assert exit_code == 0
    config = load_config()
    assert config.mode == "folder"
    assert config.folder_path == "/home/user/reading"


def test_cmd_mode_folder_warns_when_path_is_not_a_directory(capsys):
    exit_code = cli.cmd_mode("folder", "/no/such/directory")

    assert exit_code == 0
    assert "not a directory" in capsys.readouterr().err
    assert load_config().folder_path == "/no/such/directory"


def test_cmd_mode_folder_does_not_warn_for_a_real_directory(tmp_path, capsys):
    exit_code = cli.cmd_mode("folder", str(tmp_path))

    assert exit_code == 0
    assert capsys.readouterr().err == ""


def test_cmd_mode_curated_clears_back_to_curated():
    cli.cmd_mode("folder", "/home/user/reading")
    exit_code = cli.cmd_mode("curated", None)
    assert exit_code == 0
    config = load_config()
    assert config.mode == "curated"


def test_cmd_mode_writes_only_json_to_stdout(capsys):
    cli.cmd_mode("curated", None)
    out = capsys.readouterr().out
    lines = out.strip("\n").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {"ok": True, "mode": "curated"}


def test_main_dispatches_mode():
    exit_code = cli.main(["mode", "folder", "/home/user/reading"])
    assert exit_code == 0
    assert load_config().mode == "folder"


def test_cmd_finder_sets_finder():
    exit_code = cli.cmd_finder("rss")
    assert exit_code == 0
    assert load_config().finder == "rss"


def test_cmd_finder_writes_only_json_to_stdout(capsys):
    cli.cmd_finder("search")
    out = capsys.readouterr().out
    lines = out.strip("\n").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {"ok": True, "finder": "search"}


def test_main_dispatches_finder():
    exit_code = cli.main(["finder", "rss"])
    assert exit_code == 0
    assert load_config().finder == "rss"


def test_main_rejects_unknown_finder_name():
    with pytest.raises(SystemExit):
        cli.main(["finder", "bogus"])
