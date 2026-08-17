from __future__ import annotations

import time
from dataclasses import replace
from pathlib import Path

from turnbreak.core.browser import open_reading_tab
from turnbreak.core.config import Config, load_config
from turnbreak.core.items import Item, ListEntry, load_list, save_list, select_item
from turnbreak.core.server_control import client_count, spawn_server
from turnbreak.core.signal import push_end_signal, push_item_signal
from turnbreak.core.state import load_state, save_state
from turnbreak.sources.finder import Finder, build_context

# Sentinel for `shown_locator`: no real item locator is ever empty, so this
# marks "the end-of-list notice is what's currently on screen" the same way
# a real locator marks "this item is currently on screen".
_END_OF_LIST = ""


def ensure_tab_open(config: Config, *, retry_delay: float = 0.3, max_attempts: int = 10) -> None:
    """Make sure the server is running and exactly one reading tab is open.

    client_count() reflects real live SSE connections, so a tab the reader
    still has open is left alone -- this never opens a second one. Called
    both by the watcher the instant a turn starts (so the tab reappears
    even for turns that finish before the fire threshold, and even if the
    reader closed it earlier) and by on_fire right before it pushes an
    item, in case the tab was closed again in between.

    A freshly spawned server can take longer than one retry_delay to start
    answering /status, especially while the agent it's watching is busy
    using the CPU. Poll up to max_attempts times rather than checking once,
    so a slow-to-start server doesn't get mistaken for "already has a tab
    open" (clients == 0 is that case; clients is None means "didn't
    answer") and silently skip opening the tab.
    """
    clients = client_count(config.port)
    if clients is None:
        spawn_server(config.port)
        for _ in range(max_attempts):
            time.sleep(retry_delay)
            clients = client_count(config.port)
            if clients is not None:
                break
    if not clients:
        open_reading_tab(f"http://127.0.0.1:{config.port}/")


def on_fire(session_id: str, *, retry_delay: float = 0.3, max_attempts: int = 10) -> None:
    """Ensure the server is running, the reading tab is open, and an item is pushed."""
    config = load_config()
    ensure_tab_open(config, retry_delay=retry_delay, max_attempts=max_attempts)
    _push_next_item(session_id, config)


def _push_next_item(session_id: str, config: Config) -> None:
    entries = load_list()
    entry = select_item(entries, config.target_read_minutes, config.words_per_minute)
    if entry is None:
        entries = _refill_list(entries, config)
        entry = select_item(entries, config.target_read_minutes, config.words_per_minute)
    shown_locator = entry.item.locator if entry is not None else _END_OF_LIST
    current = load_state()
    if (
        current is not None
        and current.session_id == session_id
        and current.shown_locator == shown_locator
    ):
        # Same state already shown earlier in this session, and the
        # reader hasn't picked Read or Skip yet (or the list was already
        # reported empty): don't push it again.
        return
    if entry is None:
        # Nothing pending and the refill found nothing new. Say so on the
        # page rather than leaving the reader staring at a stale item with
        # no explanation — a silent rebuild attempt every fire would hide
        # that interests.md needs editing.
        push_end_signal(config.port)
    else:
        push_item_signal(config.port, session_id, entry.item, config.words_per_minute)
    if current is not None and current.session_id == session_id:
        save_state(replace(current, shown_locator=shown_locator))


def _build_finder(name: str) -> Finder | None:
    if name == "agent":
        from turnbreak.sources.agent import AgentFinder

        return AgentFinder()
    if name == "rss":
        from turnbreak.sources.rss import RssFinder

        return RssFinder()
    if name == "search":
        from turnbreak.sources.search import SearchFinder

        return SearchFinder()
    return None


def _refill_list(entries: list[ListEntry], config: Config) -> list[ListEntry]:
    """Find more candidates for the list, if any source is available.

    In folder mode, candidates come from re-scanning the configured
    folder rather than a finder. Otherwise, the agent finder spends the
    user's tokens on every call, so it only runs once turnbreak onboard
    has recorded explicit consent. It can't prompt for that consent
    itself: this runs from a background watcher with no terminal
    attached.
    """
    if config.mode == "folder":
        new_items = _find_folder_items(config)
    elif config.finder == "agent" and not config.agent_finder_accepted:
        return entries
    else:
        finder = _build_finder(config.finder)
        new_items = finder.find(build_context()) if finder is not None else []
    if not new_items:
        return entries
    existing_locators = {entry.item.locator for entry in entries}
    merged = entries + [
        ListEntry(item=item) for item in new_items if item.locator not in existing_locators
    ]
    save_list(merged)
    return merged


def _find_folder_items(config: Config) -> list[Item]:
    if not config.folder_path:
        return []
    from turnbreak.sources.folder import list_folder_items

    return list_folder_items(Path(config.folder_path))
