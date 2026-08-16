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

    assert [item.title for item in items] == ["a"]


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
