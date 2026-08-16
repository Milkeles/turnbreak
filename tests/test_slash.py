from turnbreak.cli import cmd_slash
from turnbreak.core.config import config_dir


def test_cmd_slash_writes_manifest(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    rc = cmd_slash()
    assert rc == 0
    path = config_dir() / "slash_turnbreak_interests.json"
    assert path.exists()
    content = path.read_text()
    assert "/turnbreak-interests" in content
