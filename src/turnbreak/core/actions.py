from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from turnbreak.core import state
from turnbreak.core.items import (
    HistoryOutcome,
    Item,
    ItemStatus,
    ListEntry,
    append_history,
    load_list,
    save_list,
)


def read_item(
    session_id: str,
    locator: str,
    *,
    list_file: Path | None = None,
    history_file: Path | None = None,
    state_file: Path | None = None,
) -> None:
    """Mark an item read, record it as an interest match, and clear any hold."""
    _resolve(session_id, locator, "read", "match", list_file, history_file, state_file)


def skip_item(
    session_id: str,
    locator: str,
    *,
    list_file: Path | None = None,
    history_file: Path | None = None,
    state_file: Path | None = None,
) -> None:
    """Mark an item skipped, record it as a miss, and clear any hold."""
    _resolve(session_id, locator, "skipped", "miss", list_file, history_file, state_file)


def keep_reading(session_id: str, *, state_file: Path | None = None) -> state.SessionState | None:
    """Hold the current item on screen and suppress the next fire."""
    current = state.load_state(state_file)
    if current is None or current.session_id != session_id:
        return None
    held = replace(current, hold_status="held")
    state.save_state(held, state_file)
    return held


def _resolve(
    session_id: str,
    locator: str,
    new_status: ItemStatus,
    outcome: HistoryOutcome,
    list_file: Path | None,
    history_file: Path | None,
    state_file: Path | None,
) -> None:
    entries = load_list(list_file)
    updated: list[ListEntry] = []
    resolved: Item | None = None
    for entry in entries:
        if resolved is None and entry.item.locator == locator and entry.status == "pending":
            resolved = entry.item
            updated.append(replace(entry, status=new_status))
        else:
            updated.append(entry)
    save_list(updated, list_file)
    if resolved is not None:
        append_history(resolved, outcome, history_file)

    current = state.load_state(state_file)
    if current is not None and current.session_id == session_id and current.hold_status == "held":
        state.save_state(replace(current, hold_status="none"), state_file)
