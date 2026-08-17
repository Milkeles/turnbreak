from dataclasses import replace

from turnbreak.cli import cmd_onboard
from turnbreak.core.config import load_config, save_config
from turnbreak.core.interests import interests_path


def _accept_agent_finder(tmp_path) -> None:
    save_config(replace(load_config(), agent_finder_accepted=True))


def test_onboard_writes_file_when_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    _accept_agent_finder(tmp_path)
    inputs = iter(["rust", "distributed systems", ""])  # empty line to finish
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    rc = cmd_onboard()
    assert rc == 0
    path = interests_path()
    assert path.exists()
    content = path.read_text()
    assert "rust" in content


def test_onboard_noop_if_exists(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    path = interests_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("already\n")
    _accept_agent_finder(tmp_path)

    rc = cmd_onboard()
    assert rc == 0
    assert "already" in path.read_text()


def test_onboard_prompts_for_agent_finder_consent(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    path = interests_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("already\n")
    monkeypatch.setattr("turnbreak.sources.agent.confirm_token_spend", lambda *a, **k: True)

    rc = cmd_onboard()

    assert rc == 0
    assert "Agent finder enabled" in capsys.readouterr().out


def test_onboard_records_decline(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    path = interests_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("already\n")
    monkeypatch.setattr("turnbreak.sources.agent.confirm_token_spend", lambda *a, **k: False)

    rc = cmd_onboard()

    assert rc == 0
    assert "not enabled" in capsys.readouterr().out
    assert load_config().agent_finder_accepted is False


def test_onboard_skips_consent_for_non_agent_finder(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    path = interests_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("already\n")
    save_config(replace(load_config(), finder="rss"))

    def boom(*a, **k):
        raise AssertionError("should not prompt when finder is not agent")

    monkeypatch.setattr("turnbreak.sources.agent.confirm_token_spend", boom)

    rc = cmd_onboard()
    assert rc == 0
