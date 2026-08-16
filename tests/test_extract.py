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


class _FakePage:
    def __init__(self, text):
        self._text = text

    def extract_text(self):
        return self._text


class _FakeReader:
    def __init__(self, pages):
        self._pages = pages

    def __call__(self, stream):
        return self

    @property
    def pages(self):
        return self._pages


def test_extract_pdf_word_count_counts_words_in_the_text_layer(monkeypatch):
    monkeypatch.setattr(extract, "pypdf", type("M", (), {"PdfReader": _FakeReader([_FakePage("one two three")])})())

    assert extract.extract_pdf_word_count(b"fake pdf bytes") == 3


def test_extract_pdf_word_count_returns_none_for_a_scanned_pdf_with_no_text_layer(monkeypatch):
    monkeypatch.setattr(extract, "pypdf", type("M", (), {"PdfReader": _FakeReader([_FakePage("")])})())

    assert extract.extract_pdf_word_count(b"fake pdf bytes") is None


def test_extract_pdf_word_count_returns_none_for_a_corrupt_file():
    assert extract.extract_pdf_word_count(b"not a real pdf") is None
