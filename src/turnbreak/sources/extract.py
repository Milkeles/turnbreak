from __future__ import annotations

import trafilatura


def extract_word_count(url: str) -> int | None:
    """Fetch url and count words in its extracted article text.

    Returns None if the page can't be fetched or yields no extractable
    article text, so callers can drop the candidate rather than fabricate
    a word count.
    """
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return None
    text = trafilatura.extract(downloaded)
    if not text:
        return None
    return len(text.split())
