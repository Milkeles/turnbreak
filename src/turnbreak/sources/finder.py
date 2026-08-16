from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from turnbreak.core.interests import load_interests
from turnbreak.core.items import Item, load_history


@dataclass(frozen=True)
class FinderContext:
    """Everything a finder needs to propose new candidates.

    read_items and skipped_items are past matches and misses, oldest
    first, so a finder can steer toward what worked and away from
    what didn't.
    """

    interests: str
    read_items: list[Item]
    skipped_items: list[Item]


class Finder(Protocol):
    def find(self, context: FinderContext) -> list[Item]:
        """Return candidate items for the curated list."""
        ...


def build_context(
    interests_file: Path | None = None,
    history_file: Path | None = None,
) -> FinderContext:
    history = load_history(history_file)
    return FinderContext(
        interests=load_interests(interests_file),
        read_items=[item for item, outcome in history if outcome == "match"],
        skipped_items=[item for item, outcome in history if outcome == "miss"],
    )
