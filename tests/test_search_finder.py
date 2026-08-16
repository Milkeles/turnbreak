import json
import urllib.error

from turnbreak.core.items import Item
from turnbreak.sources.finder import FinderContext
from turnbreak.sources.search import SearchFinder, brave_search


def _context(interests="rust and distributed systems", read=(), skipped=()):
    return FinderContext(interests=interests, read_items=list(read), skipped_items=list(skipped))


def test_find_returns_empty_list_when_no_api_key_configured(monkeypatch):
    monkeypatch.delenv("TURNBREAK_BRAVE_API_KEY", raising=False)
    finder = SearchFinder(api_key=None, searcher=lambda *a: (_ for _ in ()).throw(AssertionError()))
    assert finder.find(_context()) == []


def test_find_returns_empty_list_when_interests_are_blank():
    finder = SearchFinder(
        api_key="key", searcher=lambda *a: (_ for _ in ()).throw(AssertionError())
    )
    assert finder.find(_context(interests="   ")) == []


def test_find_reads_api_key_from_environment_when_not_passed_explicitly(monkeypatch):
    monkeypatch.setenv("TURNBREAK_BRAVE_API_KEY", "env-key")
    seen_keys = []

    def searcher(query, api_key, count):
        seen_keys.append(api_key)
        return []

    finder = SearchFinder(api_key=None, searcher=searcher)
    finder.find(_context())
    assert seen_keys == ["env-key"]


def test_find_queries_with_the_interests_text_and_attaches_word_counts():
    seen_queries = []

    def searcher(query, api_key, count):
        seen_queries.append(query)
        return [{"title": "A Post", "url": "https://example.com/a"}]

    finder = SearchFinder(api_key="key", searcher=searcher, word_counter=lambda url: 250)
    items = finder.find(_context(interests="rust"))
    assert seen_queries == ["rust"]
    assert items == [
        Item(title="A Post", locator="https://example.com/a", word_count=250, source="curated")
    ]


def test_find_drops_candidates_the_word_counter_cannot_extract():
    def searcher(query, api_key, count):
        return [{"title": "A", "url": "https://example.com/a"}]

    finder = SearchFinder(api_key="key", searcher=searcher, word_counter=lambda url: None)
    assert finder.find(_context()) == []


def test_find_skips_candidates_already_read_or_skipped():
    def searcher(query, api_key, count):
        return [
            {"title": "Read already", "url": "https://example.com/read"},
            {"title": "New", "url": "https://example.com/new"},
        ]

    finder = SearchFinder(api_key="key", searcher=searcher, word_counter=lambda url: 200)
    context = _context(
        read=[Item(title="x", locator="https://example.com/read", word_count=1, source="curated")]
    )
    items = finder.find(context)
    assert [item.locator for item in items] == ["https://example.com/new"]


def test_brave_search_sends_the_subscription_token_header_and_parses_results(monkeypatch):
    captured_request = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return json.dumps(
                {"web": {"results": [{"title": "A Post", "url": "https://example.com/a"}]}}
            ).encode()

    def fake_urlopen(request, timeout=None):
        captured_request["headers"] = request.headers
        captured_request["url"] = request.full_url
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    candidates = brave_search("rust", "secret-key", 5)

    assert candidates == [{"title": "A Post", "url": "https://example.com/a"}]
    assert captured_request["headers"]["X-subscription-token"] == "secret-key"
    assert "q=rust" in captured_request["url"]


def test_brave_search_returns_empty_list_on_request_failure(monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise urllib.error.URLError("boom")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    assert brave_search("rust", "secret-key", 5) == []


def test_brave_search_returns_empty_list_when_response_body_is_not_json(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b"not json"

    def fake_urlopen(request, timeout=None):
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    assert brave_search("rust", "secret-key", 5) == []
