from turnbreak.cli import cmd_watch
from turnbreak.core.items import save_list, Item, ListEntry
from turnbreak.core.config import config_dir
import json


def test_cmd_watch_once_no_list(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    rc = cmd_watch(None, once=True)
    assert rc == 0
    captured = capsys.readouterr()
    assert "Nothing to read right now" in captured.out


def test_cmd_watch_once_shows_item(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    # create a list.jsonl with one pending item
    item = Item(title="A", locator="/tmp/a.md", word_count=120, source="folder", body="one two")
    save_list([ListEntry(item=item)])
    rc = cmd_watch(None, once=True)
    assert rc == 0
    captured = capsys.readouterr()
    assert "A (folder)" in captured.out
