from turnbreak.sources import extract


def test_extract_word_count_counts_words_in_extracted_text(monkeypatch):
    monkeypatch.setattr(extract.trafilatura, "fetch_url", lambda url: "<html>raw</html>")
    monkeypatch.setattr(extract.trafilatura, "extract", lambda html: "one two three four five")

    assert extract.extract_word_count("https://example.com/a") == 5


def test_extract_word_count_returns_none_when_fetch_fails(monkeypatch):
    monkeypatch.setattr(extract.trafilatura, "fetch_url", lambda url: None)

    assert extract.extract_word_count("https://example.com/a") is None


def test_extract_word_count_returns_none_when_extraction_yields_no_text(monkeypatch):
    monkeypatch.setattr(extract.trafilatura, "fetch_url", lambda url: "<html>raw</html>")
    monkeypatch.setattr(extract.trafilatura, "extract", lambda html: None)

    assert extract.extract_word_count("https://example.com/a") is None
