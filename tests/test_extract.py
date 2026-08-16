from turnbreak.sources import extract


def test_extract_article_returns_text_and_word_count(monkeypatch):
    monkeypatch.setattr(extract.trafilatura, "fetch_url", lambda url: "<html>raw</html>")
    monkeypatch.setattr(extract.trafilatura, "extract", lambda html: "one two three four five")

    assert extract.extract_article("https://example.com/a") == ("one two three four five", 5)


def test_extract_article_returns_none_when_fetch_fails(monkeypatch):
    monkeypatch.setattr(extract.trafilatura, "fetch_url", lambda url: None)

    assert extract.extract_article("https://example.com/a") is None


def test_extract_article_returns_none_when_extraction_yields_no_text(monkeypatch):
    monkeypatch.setattr(extract.trafilatura, "fetch_url", lambda url: "<html>raw</html>")
    monkeypatch.setattr(extract.trafilatura, "extract", lambda html: None)

    assert extract.extract_article("https://example.com/a") is None


def test_extract_html_returns_text_and_word_count(monkeypatch):
    monkeypatch.setattr(extract.trafilatura, "extract", lambda html: "one two three four five")

    assert extract.extract_html("<html>raw</html>") == ("one two three four five", 5)


def test_extract_html_returns_none_when_extraction_yields_no_text(monkeypatch):
    monkeypatch.setattr(extract.trafilatura, "extract", lambda html: None)

    assert extract.extract_html("<html>raw</html>") is None
