from __future__ import annotations

from collections.abc import Callable
from typing import Any

import feedparser

from turnbreak.core.feeds import load_feeds
from turnbreak.core.items import Item
from turnbreak.sources.extract import extract_word_count
from turnbreak.sources.finder import FinderContext


class RssFinder:
    """Finder that reads the user's feed list and turns entries into candidates.

    Feed entries never carry a trustworthy word count, so this fetches
    each entry's own page and extracts real article text, same as the
    agent finder, dropping any candidate that fails to extract.
    """

    def __init__(
        self,
        feeds: list[str] | None = None,
        parser: Callable[[str], Any] = feedparser.parse,
        word_counter: Callable[[str], int | None] = extract_word_count,
    ) -> None:
        self._feeds = feeds
        self._parser = parser
        self._word_counter = word_counter

    def find(self, context: FinderContext) -> list[Item]:
        feeds = self._feeds if self._feeds is not None else load_feeds()
        seen = {item.locator for item in (*context.read_items, *context.skipped_items)}
        items = []
        for feed_url in feeds:
            parsed = self._parser(feed_url)
            for entry in getattr(parsed, "entries", []):
                url = entry.get("link")
                title = entry.get("title")
                if not url or not title or url in seen:
                    continue
                seen.add(url)
                word_count = self._word_counter(url)
                if word_count is None:
                    continue
                items.append(
                    Item(title=title, locator=url, word_count=word_count, source="curated")
                )
        return items
