from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from turnbreak.core.items import (
    HistoryOutcome,
    Item,
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
) -> None:
    """Mark an item read and record it as an interest match."""
    _resolve(session_id, locator, "match", list_file, history_file, remove=False)


def skip_item(
    session_id: str,
    locator: str,
    *,
    list_file: Path | None = None,
    history_file: Path | None = None,
) -> None:
    """Remove an item from the list and record it as a miss."""
    _resolve(session_id, locator, "miss", list_file, history_file, remove=True)


def _resolve(
    session_id: str,
    locator: str,
    outcome: HistoryOutcome,
    list_file: Path | None,
    history_file: Path | None,
    *,
    remove: bool,
) -> None:
    entries = load_list(list_file)
    updated: list[ListEntry] = []
    resolved: Item | None = None
    for entry in entries:
        if resolved is None and entry.item.locator == locator and entry.status == "pending":
            resolved = entry.item
            if not remove:
                updated.append(replace(entry, status="read"))
        else:
            updated.append(entry)
    save_list(updated, list_file)
    if resolved is not None:
        append_history(resolved, outcome, history_file)
