from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from turnbreak.core.config import config_dir

ItemSource = Literal["curated", "folder"]
ItemStatus = Literal["pending", "read", "skipped"]
HistoryOutcome = Literal["match", "miss"]


@dataclass(frozen=True)
class Item:
    title: str
    locator: str  # URL, or absolute file path
    word_count: int
    source: ItemSource


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
        data = json.loads(line)
        entries.append(ListEntry(item=Item(**data["item"]), status=data["status"]))
    return entries


def save_list(entries: list[ListEntry], path: Path | None = None) -> None:
    path = path or list_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps({"item": asdict(entry.item), "status": entry.status}) for entry in entries]
    path.write_text("".join(line + "\n" for line in lines))


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
        data = json.loads(line)
        records.append((Item(**data["item"]), data["outcome"]))
    return records


def history_locators(path: Path | None = None) -> set[str]:
    return {item.locator for item, _ in load_history(path)}


def read_minutes(item: Item, words_per_minute: int) -> float:
    return item.word_count / words_per_minute


def select_item(
    entries: list[ListEntry],
    target_read_minutes: tuple[int, int],
    words_per_minute: int,
) -> ListEntry | None:
    """Pick the next pending item to show.

    Prefers items whose read time falls inside target_read_minutes.
    Skips items over twice the upper bound; they're too long to
    suggest at this reading speed no matter how thin the list gets.
    """
    low, high = target_read_minutes
    in_range: list[ListEntry] = []
    fallback: list[ListEntry] = []
    for entry in entries:
        if entry.status != "pending":
            continue
        minutes = read_minutes(entry.item, words_per_minute)
        if minutes > high * 2:
            continue
        if low <= minutes <= high:
            in_range.append(entry)
        else:
            fallback.append(entry)
    if in_range:
        return in_range[0]
    if fallback:
        return fallback[0]
    return None
