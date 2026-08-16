from __future__ import annotations

import io

import pypdf
import trafilatura


def _extract_from_html(html: str) -> tuple[str, int] | None:
    text = trafilatura.extract(html)
    if not text:
        return None
    return text, len(text.split())


def extract_article(url: str) -> tuple[str, int] | None:
    """Fetch url and extract clean article text plus its word count.

    Returns None if the page can't be fetched or yields no extractable
    article text, so callers can drop the candidate rather than fabricate
    a word count or push an empty body. The text is cached on the Item at
    build time, so a rebuild fetches each URL exactly once, and firing an
    item never fetches at all.
    """
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return None
    return _extract_from_html(downloaded)


def extract_html(html: str) -> tuple[str, int] | None:
    """Strip markup from local HTML text and count words in what remains.

    Shares the trafilatura pipeline with extract_article, since it already
    separates real content from boilerplate better than a naive tag strip.
    Returns None if extraction yields no text, so callers can drop the file
    rather than fabricate a word count.
    """
    return _extract_from_html(html)


def extract_pdf_word_count(data: bytes) -> int | None:
    """Count words in a PDF's text layer, for the read time estimate only.

    The extracted text is discarded, never cached for display, since the
    shell embeds the PDF's own bytes instead of rendered text. Catches
    any parse failure broadly, since a scanned PDF with no text layer and
    a corrupt file both fail in library-specific ways we can't enumerate,
    and either way the PDF should still display with no read time
    estimate rather than being dropped.
    """
    try:
        reader = pypdf.PdfReader(io.BytesIO(data))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return None
    text = text.strip()
    if not text:
        return None
    return len(text.split())
