from __future__ import annotations

import trafilatura


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
    text = trafilatura.extract(downloaded)
    if not text:
        return None
    return text, len(text.split())
