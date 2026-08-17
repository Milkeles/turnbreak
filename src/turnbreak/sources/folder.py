from __future__ import annotations

from pathlib import Path

from turnbreak.core.items import Item
from turnbreak.sources.extract import extract_html, extract_pdf_word_count

_SUPPORTED_SUFFIXES = {".md", ".txt", ".html", ".pdf"}


def list_folder_items(directory: Path) -> list[Item]:
    """List readable files in directory as candidate Items.

    .md and .txt count words directly. .html goes through the same
    extraction trafilatura uses on fetched pages, stripping markup before
    counting, and is dropped if extraction yields no text. .pdf is never
    dropped, even if its text layer can't be extracted for a word count:
    the page streams it from disk via /pdf (see server._serve_pdf) rather
    than this scan reading and embedding its bytes, so a folder of whole
    books stays cheap to scan and never balloons list.jsonl.
    """
    if not directory.is_dir():
        return []
    items = []
    for path in sorted(directory.iterdir()):
        suffix = path.suffix.lower()
        if not path.is_file() or suffix not in _SUPPORTED_SUFFIXES:
            continue
        is_pdf = suffix == ".pdf"
        if is_pdf:
            body = ""
            word_count = extract_pdf_word_count(path.read_bytes()) or 0
        elif suffix == ".html":
            extracted = extract_html(path.read_text(errors="ignore"))
            if extracted is None:
                continue
            body, word_count = extracted
        else:
            body = path.read_text(errors="ignore")
            word_count = len(body.split())
        items.append(
            Item(
                title=path.stem,
                locator=str(path.resolve()),
                word_count=word_count,
                source="folder",
                body=body,
                is_pdf=is_pdf,
            )
        )
    return items
