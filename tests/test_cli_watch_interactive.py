from turnbreak.core.items import save_list, load_list, load_history, Item, ListEntry
from turnbreak.cli import cmd_watch


def test_cmd_watch_interactive_read(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    item = Item(title="A", locator="/tmp/a.md", word_count=120, source="folder", body="one two")
    save_list([ListEntry(item=item)])

    responses = iter(["r", "q"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    rc = cmd_watch("session-1", once=False)
    assert rc == 0

    entries = load_list()
    assert entries[0].status == "read"
    history = load_history()
    assert history and history[0][1] == "match"


def test_cmd_watch_interactive_keep(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    item = Item(title="B", locator="/tmp/b.md", word_count=60, source="folder", body="one two")
    save_list([ListEntry(item=item)])

    responses = iter(["k"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    rc = cmd_watch("session-2", once=False)
    assert rc == 0

    # state should be held
    from turnbreak.core.state import load_state

    s = load_state()
    assert s is not None and s.hold_status == "held"
