from types import SimpleNamespace

from turnbreak.core.items import Item
from turnbreak.sources.finder import FinderContext
from turnbreak.sources.rss import RssFinder


def _context(read=(), skipped=()):
    return FinderContext(interests="rust", read_items=list(read), skipped_items=list(skipped))


def _feed(*entries):
    return SimpleNamespace(entries=[dict(link=link, title=title) for title, link in entries])


def test_find_returns_empty_list_when_no_feeds_configured():
    finder = RssFinder(feeds=[], parser=lambda url: (_ for _ in ()).throw(AssertionError()))
    assert finder.find(_context()) == []


def test_find_parses_entries_and_attaches_word_counts():
    def parser(url):
        assert url == "https://a.example/feed.xml"
        return _feed(("A Post", "https://a.example/a"))

    finder = RssFinder(
        feeds=["https://a.example/feed.xml"], parser=parser, word_counter=lambda url: 300
    )
    items = finder.find(_context())
    assert items == [
        Item(title="A Post", locator="https://a.example/a", word_count=300, source="curated")
    ]


def test_find_reads_every_configured_feed():
    calls = []

    def parser(url):
        calls.append(url)
        return _feed((f"Post from {url}", f"{url}/post"))

    finder = RssFinder(
        feeds=["https://a.example/feed.xml", "https://b.example/feed.xml"],
        parser=parser,
        word_counter=lambda url: 100,
    )
    items = finder.find(_context())
    assert calls == ["https://a.example/feed.xml", "https://b.example/feed.xml"]
    assert [item.locator for item in items] == [
        "https://a.example/feed.xml/post",
        "https://b.example/feed.xml/post",
    ]


def test_find_drops_entries_missing_a_link_or_title():
    def parser(url):
        return SimpleNamespace(
            entries=[
                {"title": "No link"},
                {"link": "https://a.example/no-title"},
                {"link": "https://a.example/ok", "title": "OK"},
            ]
        )

    finder = RssFinder(
        feeds=["https://a.example/feed.xml"], parser=parser, word_counter=lambda url: 100
    )
    items = finder.find(_context())
    assert [item.locator for item in items] == ["https://a.example/ok"]


def test_find_drops_candidates_the_word_counter_cannot_extract():
    def parser(url):
        return _feed(("A", "https://a.example/a"))

    finder = RssFinder(
        feeds=["https://a.example/feed.xml"], parser=parser, word_counter=lambda url: None
    )
    assert finder.find(_context()) == []


def test_find_skips_entries_already_read_or_skipped():
    def parser(url):
        return _feed(
            ("Read already", "https://a.example/read"),
            ("New", "https://a.example/new"),
        )

    finder = RssFinder(
        feeds=["https://a.example/feed.xml"], parser=parser, word_counter=lambda url: 100
    )
    context = _context(
        read=[Item(title="x", locator="https://a.example/read", word_count=1, source="curated")]
    )
    items = finder.find(context)
    assert [item.locator for item in items] == ["https://a.example/new"]


def test_find_uses_configured_feed_list_by_default(monkeypatch):
    import turnbreak.sources.rss as rss_module

    monkeypatch.setattr(rss_module, "load_feeds", lambda: ["https://configured.example/feed.xml"])
    calls = []

    def parser(url):
        calls.append(url)
        return _feed()

    finder = RssFinder(parser=parser)
    finder.find(_context())
    assert calls == ["https://configured.example/feed.xml"]
