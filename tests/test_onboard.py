from turnbreak.cli import cmd_onboard
from turnbreak.core.interests import interests_path


def test_onboard_writes_file_when_missing(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    inputs = iter(["rust", "distributed systems", ""])  # empty line to finish
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    rc = cmd_onboard()
    assert rc == 0
    path = interests_path()
    assert path.exists()
    content = path.read_text()
    assert "rust" in content


def test_onboard_noop_if_exists(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    path = interests_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("already\n")

    rc = cmd_onboard()
    assert rc == 0
    captured = capsys.readouterr()
    assert "already" in path.read_text()
