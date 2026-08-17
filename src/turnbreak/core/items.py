from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from turnbreak.core.config import atomic_write_text, config_dir

ItemSource = Literal["curated", "folder"]
ItemStatus = Literal["pending", "read", "skipped"]
HistoryOutcome = Literal["match", "miss"]


@dataclass(frozen=True)
class Item:
    title: str
    locator: str  # URL, or absolute file path
    word_count: int
    source: ItemSource
    body: str = ""  # cached at build time, so firing never re-fetches
    is_pdf: bool = False  # locator is a local file path; the page streams it from /pdf


@dataclass(frozen=True)
class ListEntry:
    item: Item
    status: ItemStatus = "pending"


def list_path() -> Path:
    return config_dir() / "list.jsonl"


def history_path() -> Path:
    return config_dir() / "history.jsonl"


def load_list(path: Path | None = None) -> list[ListEntry]:
    path = path or list_path()
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            entries.append(ListEntry(item=Item(**data["item"]), status=data["status"]))
        except (json.JSONDecodeError, KeyError, TypeError):
            # A concurrent writer (another agent's watcher, an overlapping
            # turn) can tear a line mid-write. Skip it rather than losing
            # every other entry in the list to one bad line.
            print(f"turnbreak: skipping corrupt line in {path}", file=sys.stderr)
    return entries


def save_list(entries: list[ListEntry], path: Path | None = None) -> None:
    path = path or list_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps({"item": asdict(entry.item), "status": entry.status}) for entry in entries]
    atomic_write_text(path, "".join(line + "\n" for line in lines))


def append_history(item: Item, outcome: HistoryOutcome, path: Path | None = None) -> None:
    path = path or history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps({"item": asdict(item), "outcome": outcome}) + "\n")


def load_history(path: Path | None = None) -> list[tuple[Item, HistoryOutcome]]:
    path = path or history_path()
    if not path.exists():
        return []
    records = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            records.append((Item(**data["item"]), data["outcome"]))
        except (json.JSONDecodeError, KeyError, TypeError):
            print(f"turnbreak: skipping corrupt line in {path}", file=sys.stderr)
    return records


def history_locators(path: Path | None = None) -> set[str]:
    return {item.locator for item, _ in load_history(path)}


def read_minutes(item: Item, words_per_minute: int) -> float:
    return item.word_count / words_per_minute


def select_item(
    entries: list[ListEntry],
    target_read_minutes: tuple[int, int],
    words_per_minute: int,
    *,
    exclude: set[str] | None = None,
) -> ListEntry | None:
    """Pick the next pending item to show.

    Prefers items whose read time falls inside target_read_minutes, then
    any other pending item within twice the upper bound, then finally any
    remaining pending item regardless of length. That last tier matters for
    folder mode: a folder of whole PDFs (book chapters, papers) will often
    have nothing under the twice-the-bound cutoff, and showing nothing at
    all is worse than showing a longer read.

    `exclude` lets a caller rule out locators already browsed this session
    (used by the page's Next button) without changing their status --
    unlike Read, moving past an item with Next doesn't resolve it.
    """
    exclude = exclude or set()
    low, high = target_read_minutes
    in_range: list[ListEntry] = []
    fallback: list[ListEntry] = []
    too_long: list[ListEntry] = []
    for entry in entries:
        if entry.status != "pending" or entry.item.locator in exclude:
            continue
        minutes = read_minutes(entry.item, words_per_minute)
        if low <= minutes <= high:
            in_range.append(entry)
        elif minutes <= high * 2:
            fallback.append(entry)
        else:
            too_long.append(entry)
    if in_range:
        return in_range[0]
    if fallback:
        return fallback[0]
    if too_long:
        return too_long[0]
    return None


def item_payload(item: Item, session_id: str, words_per_minute: int) -> dict[str, object]:
    """Shape an item the way the page expects it.

    Shared by the live push in `signal.push_item_signal` and the
    `/current` snapshot the server reconstructs on a fresh page load, so
    the two never drift apart on what fields the page needs.
    """
    minutes = int(item.word_count / words_per_minute) if item.word_count else 0
    return {
        "session_id": session_id,
        "locator": item.locator,
        "title": item.title,
        "source": item.source,
        "read_minutes": minutes,
        "body": item.body,
        "is_pdf": item.is_pdf,
    }
