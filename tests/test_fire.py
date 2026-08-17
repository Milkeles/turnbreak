from dataclasses import replace
from pathlib import Path

import pytest

from turnbreak.core import fire, state
from turnbreak.core.config import Config
from turnbreak.core.items import Item, ListEntry
from turnbreak.sources.finder import FinderContext


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


class FakeFinder:
    def __init__(self, items: list[Item]) -> None:
        self._items = items

    def find(self, context: FinderContext) -> list[Item]:
        return self._items


def test_on_fire_does_not_spawn_or_open_a_tab_when_a_client_is_already_connected(monkeypatch, home):
    monkeypatch.setattr(fire, "client_count", lambda port: 1)
    spawn_calls = []
    tab_calls = []
    monkeypatch.setattr(fire, "spawn_server", lambda port: spawn_calls.append(port))
    monkeypatch.setattr(fire, "open_reading_tab", lambda url: tab_calls.append(url))
    monkeypatch.setattr(fire, "_push_next_item", lambda sid, cfg: None)

    fire.on_fire("session-1")

    assert spawn_calls == []
    assert tab_calls == []


def test_on_fire_opens_a_tab_when_the_server_is_up_but_no_tab_is_connected(monkeypatch, home):
    monkeypatch.setattr(fire, "client_count", lambda port: 0)
    spawn_calls = []
    tab_calls = []
    monkeypatch.setattr(fire, "spawn_server", lambda port: spawn_calls.append(port))
    monkeypatch.setattr(fire, "open_reading_tab", lambda url: tab_calls.append(url))
    monkeypatch.setattr(fire, "_push_next_item", lambda sid, cfg: None)

    fire.on_fire("session-1")

    assert spawn_calls == []
    assert tab_calls == ["http://127.0.0.1:7717/"]


def test_on_fire_spawns_the_server_and_opens_a_tab_when_nothing_was_running(monkeypatch, home):
    monkeypatch.setattr(fire, "client_count", lambda port: None)
    spawn_calls = []
    tab_calls = []
    monkeypatch.setattr(fire, "spawn_server", lambda port: spawn_calls.append(port))
    monkeypatch.setattr(fire, "open_reading_tab", lambda url: tab_calls.append(url))
    monkeypatch.setattr(fire, "_push_next_item", lambda sid, cfg: None)
    monkeypatch.setattr(fire.time, "sleep", lambda seconds: None)

    fire.on_fire("session-1")

    assert spawn_calls == [7717]
    assert tab_calls == ["http://127.0.0.1:7717/"]


def test_on_fire_polls_until_a_freshly_spawned_server_responds(monkeypatch, home):
    """A cold server process can take longer than one retry to answer
    /status, especially while the agent it's watching is busy using the
    CPU. client_count staying None past the first retry must not be read
    as "a tab is already open" and skip opening one.
    """
    responses = iter([None, None, None, 2])
    monkeypatch.setattr(fire, "client_count", lambda port: next(responses))
    monkeypatch.setattr(fire, "spawn_server", lambda port: None)
    tab_calls = []
    monkeypatch.setattr(fire, "open_reading_tab", lambda url: tab_calls.append(url))
    monkeypatch.setattr(fire, "_push_next_item", lambda sid, cfg: None)
    sleep_calls = []
    monkeypatch.setattr(fire.time, "sleep", lambda seconds: sleep_calls.append(seconds))

    fire.on_fire("session-1")

    assert len(sleep_calls) == 3
    # clients ended up at 2 (a tab already connected by the time it answered)
    assert tab_calls == []


def test_on_fire_still_opens_a_tab_if_the_server_never_responds(monkeypatch, home):
    monkeypatch.setattr(fire, "client_count", lambda port: None)
    monkeypatch.setattr(fire, "spawn_server", lambda port: None)
    tab_calls = []
    monkeypatch.setattr(fire, "open_reading_tab", lambda url: tab_calls.append(url))
    monkeypatch.setattr(fire, "_push_next_item", lambda sid, cfg: None)
    monkeypatch.setattr(fire.time, "sleep", lambda seconds: None)

    fire.on_fire("session-1", max_attempts=3)

    assert tab_calls == ["http://127.0.0.1:7717/"]


def test_ensure_tab_open_opens_a_tab_when_the_server_is_up_but_no_tab_is_connected(
    monkeypatch, home
):
    """ensure_tab_open is the piece watcher.run calls on every turn start,
    independent of on_fire and the fire threshold -- covered directly so
    that guarantee doesn't rely on on_fire's own tests exercising it.
    """
    monkeypatch.setattr(fire, "client_count", lambda port: 0)
    spawn_calls = []
    tab_calls = []
    monkeypatch.setattr(fire, "spawn_server", lambda port: spawn_calls.append(port))
    monkeypatch.setattr(fire, "open_reading_tab", lambda url: tab_calls.append(url))

    fire.ensure_tab_open(Config())

    assert spawn_calls == []
    assert tab_calls == ["http://127.0.0.1:7717/"]


def test_ensure_tab_open_does_nothing_when_a_client_is_already_connected(monkeypatch, home):
    monkeypatch.setattr(fire, "client_count", lambda port: 1)
    spawn_calls = []
    tab_calls = []
    monkeypatch.setattr(fire, "spawn_server", lambda port: spawn_calls.append(port))
    monkeypatch.setattr(fire, "open_reading_tab", lambda url: tab_calls.append(url))

    fire.ensure_tab_open(Config())

    assert spawn_calls == []
    assert tab_calls == []


def test_on_fire_pushes_the_next_item(monkeypatch, home):
    monkeypatch.setattr(fire, "client_count", lambda port: 1)
    monkeypatch.setattr(fire, "open_reading_tab", lambda url: None)
    calls = []
    monkeypatch.setattr(fire, "_push_next_item", lambda sid, cfg: calls.append(sid))

    fire.on_fire("session-1")

    assert calls == ["session-1"]


def test_refill_list_skips_agent_finder_without_consent():
    config = Config(finder="agent", agent_finder_accepted=False)

    result = fire._refill_list([], config)

    assert result == []


def test_refill_list_calls_agent_finder_when_accepted(monkeypatch):
    config = Config(finder="agent", agent_finder_accepted=True)
    new_item = Item("Title", "https://a", 100, "curated")
    monkeypatch.setattr(fire, "_build_finder", lambda name: FakeFinder([new_item]))
    monkeypatch.setattr(fire, "build_context", lambda: FinderContext("", [], []))
    saved = {}
    monkeypatch.setattr(fire, "save_list", lambda entries: saved.setdefault("entries", entries))

    result = fire._refill_list([], config)

    assert result == [ListEntry(item=new_item)]
    assert saved["entries"] == result


def test_refill_list_dedupes_against_existing_locators(monkeypatch):
    config = Config(finder="rss")
    existing_item = Item("A", "https://a", 100, "curated")
    duplicate_locator_item = Item("B", "https://a", 50, "curated")
    monkeypatch.setattr(fire, "_build_finder", lambda name: FakeFinder([duplicate_locator_item]))
    monkeypatch.setattr(fire, "build_context", lambda: FinderContext("", [], []))
    monkeypatch.setattr(fire, "save_list", lambda entries: None)

    result = fire._refill_list([ListEntry(item=existing_item)], config)

    assert result == [ListEntry(item=existing_item)]


def test_refill_list_scans_folder_when_mode_is_folder(monkeypatch, tmp_path):
    config = Config(mode="folder", folder_path=str(tmp_path))
    folder_item = Item("Doc", str(tmp_path / "doc.txt"), 100, "folder")
    monkeypatch.setattr("turnbreak.sources.folder.list_folder_items", lambda path: [folder_item])
    saved = {}
    monkeypatch.setattr(fire, "save_list", lambda entries: saved.setdefault("entries", entries))

    def boom(*a, **k):
        raise AssertionError("should not build a finder in folder mode")

    monkeypatch.setattr(fire, "_build_finder", boom)

    result = fire._refill_list([], config)

    assert result == [ListEntry(item=folder_item)]
    assert saved["entries"] == result


def test_refill_list_folder_mode_noop_without_folder_path(monkeypatch):
    config = Config(mode="folder", folder_path=None)

    result = fire._refill_list([], config)

    assert result == []


def test_refill_list_does_not_save_when_finder_finds_nothing(monkeypatch):
    config = Config(finder="rss")
    monkeypatch.setattr(fire, "_build_finder", lambda name: FakeFinder([]))
    monkeypatch.setattr(fire, "build_context", lambda: FinderContext("", [], []))
    saved = []
    monkeypatch.setattr(fire, "save_list", lambda entries: saved.append(entries))

    result = fire._refill_list([], config)

    assert result == []
    assert saved == []


def test_push_next_item_pushes_first_selectable_pending_item(monkeypatch, home):
    config = Config(target_read_minutes=(2, 4), words_per_minute=200, port=1234)
    item = Item("Title", "https://a", 600, "curated")
    monkeypatch.setattr(fire, "load_list", lambda: [ListEntry(item=item)])
    calls = []
    monkeypatch.setattr(
        fire, "push_item_signal", lambda port, sid, it, wpm: calls.append((port, sid, it, wpm))
    )

    fire._push_next_item("session-1", config)

    assert calls == [(1234, "session-1", item, 200)]


def test_push_next_item_refills_when_nothing_selectable(monkeypatch, home):
    config = Config(target_read_minutes=(2, 4), words_per_minute=200, port=1234)
    item = Item("Title", "https://a", 600, "curated")
    monkeypatch.setattr(fire, "load_list", lambda: [])
    monkeypatch.setattr(fire, "_refill_list", lambda entries, cfg: [ListEntry(item=item)])
    calls = []
    monkeypatch.setattr(
        fire, "push_item_signal", lambda port, sid, it, wpm: calls.append((port, sid, it, wpm))
    )

    fire._push_next_item("session-1", config)

    assert calls == [(1234, "session-1", item, 200)]


def test_push_next_item_pushes_end_signal_when_nothing_available(monkeypatch, home):
    config = Config(port=1234)
    monkeypatch.setattr(fire, "load_list", lambda: [])
    monkeypatch.setattr(fire, "_refill_list", lambda entries, cfg: [])
    item_calls = []
    end_calls = []
    monkeypatch.setattr(fire, "push_item_signal", lambda *a: item_calls.append(a))
    monkeypatch.setattr(fire, "push_end_signal", lambda port: end_calls.append(port))

    fire._push_next_item("session-1", config)

    assert item_calls == []
    assert end_calls == [1234]


def test_push_next_item_does_not_repeat_end_signal_for_the_same_session(monkeypatch, home):
    config = Config(port=1234)
    monkeypatch.setattr(fire, "load_list", lambda: [])
    monkeypatch.setattr(fire, "_refill_list", lambda entries, cfg: [])
    end_calls = []
    monkeypatch.setattr(fire, "push_end_signal", lambda port: end_calls.append(port))
    started = state.start_turn("session-1", 0.0)
    state.save_state(replace(started, shown_locator=""))

    fire._push_next_item("session-1", config)

    assert end_calls == []


def test_push_next_item_pushes_end_signal_again_for_a_new_session_after_it_was_shown(
    monkeypatch, home
):
    config = Config(port=1234)
    monkeypatch.setattr(fire, "load_list", lambda: [])
    monkeypatch.setattr(fire, "_refill_list", lambda entries, cfg: [])
    end_calls = []
    monkeypatch.setattr(fire, "push_end_signal", lambda port: end_calls.append(port))
    started = state.start_turn("other-session", 0.0)
    state.save_state(replace(started, shown_locator=""))

    fire._push_next_item("session-1", config)

    assert end_calls == [1234]


def test_push_next_item_records_shown_locator_after_pushing(monkeypatch, home):
    config = Config(target_read_minutes=(2, 4), words_per_minute=200, port=1234)
    item = Item("Title", "https://a", 600, "curated")
    monkeypatch.setattr(fire, "load_list", lambda: [ListEntry(item=item)])
    monkeypatch.setattr(fire, "push_item_signal", lambda *a: None)
    state.start_turn("session-1", 0.0)

    fire._push_next_item("session-1", config)

    assert state.load_state().shown_locator == "https://a"


def test_push_next_item_skips_when_same_item_already_shown_this_session(monkeypatch, home):
    config = Config(target_read_minutes=(2, 4), words_per_minute=200, port=1234)
    item = Item("Title", "https://a", 600, "curated")
    monkeypatch.setattr(fire, "load_list", lambda: [ListEntry(item=item)])
    calls = []
    monkeypatch.setattr(fire, "push_item_signal", lambda *a: calls.append(a))
    started = state.start_turn("session-1", 0.0)
    state.save_state(replace(started, shown_locator="https://a"))

    fire._push_next_item("session-1", config)

    assert calls == []


def test_push_next_item_pushes_when_a_different_item_is_now_selected(monkeypatch, home):
    config = Config(target_read_minutes=(2, 4), words_per_minute=200, port=1234)
    item = Item("Title", "https://b", 600, "curated")
    monkeypatch.setattr(fire, "load_list", lambda: [ListEntry(item=item)])
    calls = []
    monkeypatch.setattr(fire, "push_item_signal", lambda *a: calls.append(a))
    started = state.start_turn("session-1", 0.0)
    state.save_state(replace(started, shown_locator="https://a"))

    fire._push_next_item("session-1", config)

    assert len(calls) == 1
    assert state.load_state().shown_locator == "https://b"


def test_push_next_item_ignores_shown_locator_from_a_different_session(monkeypatch, home):
    config = Config(target_read_minutes=(2, 4), words_per_minute=200, port=1234)
    item = Item("Title", "https://a", 600, "curated")
    monkeypatch.setattr(fire, "load_list", lambda: [ListEntry(item=item)])
    calls = []
    monkeypatch.setattr(fire, "push_item_signal", lambda *a: calls.append(a))
    started = state.start_turn("other-session", 0.0)
    state.save_state(replace(started, shown_locator="https://a"))

    fire._push_next_item("session-1", config)

    assert len(calls) == 1
