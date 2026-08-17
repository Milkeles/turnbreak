from turnbreak.cli import cmd_watch
from turnbreak.core.items import Item, ListEntry, load_history, load_list, save_list


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


def test_cmd_watch_interactive_unknown_command_redisplays_same_item(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    item = Item(title="B", locator="/tmp/b.md", word_count=60, source="folder", body="one two")
    save_list([ListEntry(item=item)])

    responses = iter(["x", "q"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    rc = cmd_watch("session-2", once=False)
    assert rc == 0

    entries = load_list()
    assert entries[0].status == "pending"


def test_cmd_watch_interactive_skip(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    item = Item(title="C", locator="/tmp/c.md", word_count=60, source="folder", body="one two")
    save_list([ListEntry(item=item)])

    responses = iter(["s", "q"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    rc = cmd_watch("session-3", once=False)
    assert rc == 0

    entries = load_list()
    assert entries == []
    history = load_history()
    assert history and history[0][1] == "miss"


def test_cmd_watch_interactive_quit_immediately_leaves_item_untouched(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    item = Item(title="D", locator="/tmp/d.md", word_count=60, source="folder", body="one two")
    save_list([ListEntry(item=item)])

    responses = iter(["q"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    rc = cmd_watch("session-4", once=False)
    assert rc == 0

    entries = load_list()
    assert entries[0].status == "pending"


def test_cmd_watch_interactive_eof_exits_cleanly(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    item = Item(title="E", locator="/tmp/e.md", word_count=60, source="folder", body="one two")
    save_list([ListEntry(item=item)])

    def raise_eof(prompt=""):
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)

    rc = cmd_watch("session-5", once=False)
    assert rc == 0

    entries = load_list()
    assert entries[0].status == "pending"
