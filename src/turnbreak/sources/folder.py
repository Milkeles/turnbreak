from __future__ import annotations

from pathlib import Path

from turnbreak.core.items import Item
from turnbreak.sources.extract import extract_html

_SUPPORTED_SUFFIXES = {".md", ".txt", ".html"}


def list_folder_items(directory: Path) -> list[Item]:
    """List readable files in directory as candidate Items.

    .md and .txt count words directly. .html goes through the same
    extraction trafilatura uses on fetched pages, stripping markup before
    counting, and is dropped if extraction yields no text. Other formats
    need the work in TASKS.md P4b before they can produce a word count.
    """
    if not directory.is_dir():
        return []
    items = []
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.suffix.lower() not in _SUPPORTED_SUFFIXES:
            continue
        raw = path.read_text(errors="ignore")
        if path.suffix.lower() == ".html":
            extracted = extract_html(raw)
            if extracted is None:
                continue
            body, word_count = extracted
        else:
            body, word_count = raw, len(raw.split())
        items.append(
            Item(
                title=path.stem,
                locator=str(path.resolve()),
                word_count=word_count,
                source="folder",
                body=body,
            )
        )
    return items
