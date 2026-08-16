from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import pytest

from turnbreak import cli
from turnbreak.core import state


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
