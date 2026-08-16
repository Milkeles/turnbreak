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
