from __future__ import annotations

import base64
from pathlib import Path

from turnbreak.core.items import Item
from turnbreak.sources.extract import extract_html, extract_pdf_word_count

_SUPPORTED_SUFFIXES = {".md", ".txt", ".html", ".pdf"}


def _read_pdf(path: Path) -> tuple[str, int, str]:
    """Return (body, word_count, pdf_data) for a PDF file.

    body always stays empty: the extracted text counts words only and is
    never shown, since the shell embeds the PDF's own bytes instead. A
    PDF that fails extraction still gets pdf_data, so it displays with a
    word_count of 0 (no read time estimate) rather than being dropped.
    """
    data = path.read_bytes()
    word_count = extract_pdf_word_count(data) or 0
    return "", word_count, base64.b64encode(data).decode("ascii")


def list_folder_items(directory: Path) -> list[Item]:
    """List readable files in directory as candidate Items.

    .md and .txt count words directly. .html goes through the same
    extraction trafilatura uses on fetched pages, stripping markup before
    counting, and is dropped if extraction yields no text. .pdf is
    embedded in the shell via pdf_data and never dropped, even if its
    text layer can't be extracted for a word count.
    """
    if not directory.is_dir():
        return []
    items = []
    for path in sorted(directory.iterdir()):
        suffix = path.suffix.lower()
        if not path.is_file() or suffix not in _SUPPORTED_SUFFIXES:
            continue
        pdf_data = ""
        if suffix == ".pdf":
            body, word_count, pdf_data = _read_pdf(path)
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
                pdf_data=pdf_data,
            )
        )
    return items
