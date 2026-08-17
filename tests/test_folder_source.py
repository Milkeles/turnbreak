from turnbreak.sources import extract
from turnbreak.sources.folder import list_folder_items


def test_list_folder_items_finds_markdown_and_text_files(tmp_path):
    (tmp_path / "a.md").write_text("one two three four five")
    (tmp_path / "b.txt").write_text("one two")

    items = list_folder_items(tmp_path)

    titles = {item.title for item in items}
    assert titles == {"a", "b"}


def test_list_folder_items_counts_words_directly(tmp_path):
    (tmp_path / "a.md").write_text("one two three four five")

    items = list_folder_items(tmp_path)

    assert items[0].word_count == 5


def test_list_folder_items_skips_unsupported_formats(tmp_path):
    (tmp_path / "a.md").write_text("one two")
    (tmp_path / "b.pdf").write_bytes(b"%PDF-1.4")
    (tmp_path / "c.epub").write_bytes(b"epub")

    items = list_folder_items(tmp_path)

    # PDFs are supported and embedded; EPUB is unsupported and skipped.
    assert [item.title for item in items] == ["a", "b"]


def test_list_folder_items_skips_subdirectories(tmp_path):
    (tmp_path / "a.md").write_text("one two")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.md").write_text("three four")

    items = list_folder_items(tmp_path)

    assert [item.title for item in items] == ["a"]


def test_list_folder_items_sets_locator_to_absolute_path(tmp_path):
    (tmp_path / "a.md").write_text("one two")

    items = list_folder_items(tmp_path)

    assert items[0].locator == str((tmp_path / "a.md").resolve())


def test_list_folder_items_sets_source_to_folder(tmp_path):
    (tmp_path / "a.md").write_text("one two")

    items = list_folder_items(tmp_path)

    assert items[0].source == "folder"


def test_list_folder_items_missing_directory_returns_empty(tmp_path):
    assert list_folder_items(tmp_path / "missing") == []


def test_list_folder_items_caches_file_text_as_body(tmp_path):
    (tmp_path / "a.md").write_text("one two three four five")

    items = list_folder_items(tmp_path)

    assert items[0].body == "one two three four five"


def test_list_folder_items_strips_tags_from_html(tmp_path, monkeypatch):
    monkeypatch.setattr(extract.trafilatura, "extract", lambda html: "one two three")
    (tmp_path / "a.html").write_text("<html><body><p>one two three</p></body></html>")

    items = list_folder_items(tmp_path)

    assert items[0].body == "one two three"
    assert items[0].word_count == 3


def test_list_folder_items_drops_html_that_fails_to_extract(tmp_path, monkeypatch):
    monkeypatch.setattr(extract.trafilatura, "extract", lambda html: None)
    (tmp_path / "a.html").write_text("<html></html>")

    assert list_folder_items(tmp_path) == []


def test_list_folder_items_includes_large_pdfs(tmp_path):
    """PDFs are streamed from disk by the server rather than embedded as
    base64 at scan time, so a whole book is never dropped or capped here.
    """
    (tmp_path / "big.pdf").write_bytes(b"%PDF-1.4" + b"0" * 100)

    items = list_folder_items(tmp_path)

    assert [item.title for item in items] == ["big"]


def test_list_folder_items_marks_pdfs_with_is_pdf(tmp_path):
    (tmp_path / "a.pdf").write_bytes(b"%PDF-1.4")
    (tmp_path / "b.md").write_text("one two")

    items = list_folder_items(tmp_path)

    by_title = {item.title: item for item in items}
    assert by_title["a"].is_pdf is True
    assert by_title["b"].is_pdf is False
