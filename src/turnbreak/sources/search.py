from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from collections.abc import Callable

from turnbreak.core.items import Item
from turnbreak.sources.extract import extract_word_count
from turnbreak.sources.finder import FinderContext

_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
_API_KEY_ENV = "TURNBREAK_BRAVE_API_KEY"


def brave_search(query: str, api_key: str, count: int) -> list[dict[str, str]]:
    """Query the Brave Search API and return {title, url} candidates.

    Returns an empty list on any request failure, so a flaky search
    never breaks a list rebuild that could still use the other finders.
    """
    params = urllib.parse.urlencode({"q": query, "count": count})
    request = urllib.request.Request(
        f"{_ENDPOINT}?{params}",
        headers={"Accept": "application/json", "X-Subscription-Token": api_key},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read())
    except (OSError, json.JSONDecodeError):
        return []
    results = data.get("web", {}).get("results", [])
    candidates = []
    for result in results:
        url, title = result.get("url"), result.get("title")
        if isinstance(url, str) and isinstance(title, str):
            candidates.append({"title": title, "url": url})
    return candidates


class SearchFinder:
    """Finder that queries the Brave Search API for reading candidates.

    Skipped entirely when no API key is configured, since search is the
    one finder that costs money per query.
    """

    def __init__(
        self,
        api_key: str | None = None,
        count: int = 5,
        searcher: Callable[[str, str, int], list[dict[str, str]]] = brave_search,
        word_counter: Callable[[str], int | None] = extract_word_count,
    ) -> None:
        self._api_key = api_key
        self._count = count
        self._searcher = searcher
        self._word_counter = word_counter

    def find(self, context: FinderContext) -> list[Item]:
        api_key = self._api_key if self._api_key is not None else os.environ.get(_API_KEY_ENV)
        if not api_key:
            return []
        query = context.interests.strip()
        if not query:
            return []
        seen = {item.locator for item in (*context.read_items, *context.skipped_items)}
        items = []
        for candidate in self._searcher(query, api_key, self._count):
            url = candidate["url"]
            if url in seen:
                continue
            seen.add(url)
            word_count = self._word_counter(url)
            if word_count is None:
                continue
            items.append(
                Item(title=candidate["title"], locator=url, word_count=word_count, source="curated")
            )
        return items
