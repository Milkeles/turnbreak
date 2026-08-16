import json
import subprocess
from pathlib import Path

import pytest

from turnbreak.core.config import Config, load_config
from turnbreak.core.items import Item
from turnbreak.sources.agent import AgentFinder, confirm_token_spend, detect_agent_command
from turnbreak.sources.finder import FinderContext


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


def _context(read=(), skipped=()):
    return FinderContext(
        interests="rust and distributed systems", read_items=list(read), skipped_items=list(skipped)
    )


def _completed(stdout, returncode=0):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")


def test_detect_agent_command_returns_none_when_nothing_installed(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda binary: None)
    assert detect_agent_command() is None


def test_detect_agent_command_prefers_claude(monkeypatch):
    monkeypatch.setattr(
        "shutil.which", lambda binary: f"/usr/bin/{binary}" if binary == "claude" else None
    )
    assert detect_agent_command() == ["claude", "-p"]


def test_detect_agent_command_falls_back_to_codex(monkeypatch):
    monkeypatch.setattr(
        "shutil.which", lambda binary: f"/usr/bin/{binary}" if binary == "codex" else None
    )
    assert detect_agent_command() == ["codex", "exec"]


def test_find_returns_empty_list_when_no_agent_installed(monkeypatch):
    import turnbreak.sources.agent as agent_module

    monkeypatch.setattr(agent_module, "detect_agent_command", lambda: None)
    finder = AgentFinder(command=None)
    assert finder.find(_context()) == []


def test_find_returns_empty_list_when_agent_call_fails():
    def runner(*args, **kwargs):
        return _completed("", returncode=1)

    finder = AgentFinder(command=["claude", "-p"], runner=runner)
    assert finder.find(_context()) == []


def test_find_parses_candidates_and_attaches_word_counts():
    payload = json.dumps(
        [
            {"title": "A Post", "url": "https://example.com/a"},
            {"title": "Another Post", "url": "https://example.com/b"},
        ]
    )

    def runner(*args, **kwargs):
        return _completed(payload)

    finder = AgentFinder(
        command=["claude", "-p"],
        runner=runner,
        extractor=lambda url: ("body text", 400),
    )
    items = finder.find(_context())
    assert items == [
        Item(
            title="A Post",
            locator="https://example.com/a",
            word_count=400,
            source="curated",
            body="body text",
        ),
        Item(
            title="Another Post",
            locator="https://example.com/b",
            word_count=400,
            source="curated",
            body="body text",
        ),
    ]


def test_find_tolerates_prose_wrapped_around_the_json_array():
    payload = (
        'Sure, here you go:\n[{"title": "A", "url": "https://example.com/a"}]\nHope that helps!'
    )

    def runner(*args, **kwargs):
        return _completed(payload)

    finder = AgentFinder(
        command=["claude", "-p"], runner=runner, extractor=lambda url: ("body", 100)
    )
    items = finder.find(_context())
    assert [item.locator for item in items] == ["https://example.com/a"]


def test_find_drops_candidates_the_extractor_cannot_extract():
    payload = json.dumps([{"title": "A", "url": "https://example.com/a"}])

    def runner(*args, **kwargs):
        return _completed(payload)

    finder = AgentFinder(command=["claude", "-p"], runner=runner, extractor=lambda url: None)
    assert finder.find(_context()) == []


def test_find_skips_candidates_already_read_or_skipped():
    payload = json.dumps(
        [
            {"title": "Read already", "url": "https://example.com/read"},
            {"title": "Skipped already", "url": "https://example.com/skipped"},
            {"title": "New", "url": "https://example.com/new"},
        ]
    )

    def runner(*args, **kwargs):
        return _completed(payload)

    finder = AgentFinder(
        command=["claude", "-p"], runner=runner, extractor=lambda url: ("body", 200)
    )
    context = _context(
        read=[Item(title="x", locator="https://example.com/read", word_count=1, source="curated")],
        skipped=[
            Item(title="y", locator="https://example.com/skipped", word_count=1, source="curated")
        ],
    )
    items = finder.find(context)
    assert [item.locator for item in items] == ["https://example.com/new"]


def test_confirm_token_spend_skips_prompt_once_already_accepted(tmp_path):
    path = tmp_path / "config.toml"
    from turnbreak.core.config import save_config

    save_config(Config(agent_finder_accepted=True), path)
    called = []
    assert confirm_token_spend(prompt=lambda msg: called.append(msg) or "n", path=path) is True
    assert called == []


def test_confirm_token_spend_records_acceptance_on_yes(tmp_path):
    path = tmp_path / "config.toml"
    assert confirm_token_spend(prompt=lambda msg: "y", path=path) is True
    assert load_config(path).agent_finder_accepted is True


def test_confirm_token_spend_returns_false_on_decline(tmp_path):
    path = tmp_path / "config.toml"
    assert confirm_token_spend(prompt=lambda msg: "n", path=path) is False
    assert load_config(path).agent_finder_accepted is False
