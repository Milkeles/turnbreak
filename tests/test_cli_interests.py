import subprocess

from turnbreak.cli import cmd_interests
from turnbreak.core.interests import interests_path


def test_cmd_interests_opens_editor(monkeypatch, tmp_path):
    # Point config_dir to tmp by setting HOME
    monkeypatch.setenv("HOME", str(tmp_path))
    called = {}

    def fake_call(args):
        called["args"] = args
        return 0

    monkeypatch.setenv("EDITOR", "fake-editor")
    monkeypatch.setattr(subprocess, "call", fake_call)

    rc = cmd_interests()
    assert rc == 0
    path = interests_path()
    assert path.exists()
    assert "args" in called


def test_cmd_interests_prints_path_when_no_editor(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("EDITOR", raising=False)

    rc = cmd_interests()
    assert rc == 0
    captured = capsys.readouterr()
    assert str(interests_path()) in captured.out
