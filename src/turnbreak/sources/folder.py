from __future__ import annotations

from pathlib import Path

from turnbreak.core.items import Item

_SUPPORTED_SUFFIXES = {".md", ".txt"}


def list_folder_items(directory: Path) -> list[Item]:
    """List readable files in directory as candidate Items.

    Only .md and .txt are supported so far. Other formats need the
    extraction work in TASKS.md P4b before they can produce a word count.
    """
    if not directory.is_dir():
        return []
    items = []
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.suffix.lower() not in _SUPPORTED_SUFFIXES:
            continue
        text = path.read_text(errors="ignore")
        items.append(
            Item(
                title=path.stem,
                locator=str(path.resolve()),
                word_count=len(text.split()),
                source="folder",
                body=text,
            )
        )
    return items
