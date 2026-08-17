from turnbreak.core.actions import read_item, skip_item
from turnbreak.core.items import Item, ListEntry, history_locators, load_list, save_list


def make_item(title="Example", locator="https://example.com/a", word_count=460, source="curated"):
    return Item(title=title, locator=locator, word_count=word_count, source=source)


def paths(tmp_path):
    return tmp_path / "list.jsonl", tmp_path / "history.jsonl"


def test_read_item_marks_read_and_records_match(tmp_path):
    list_file, history_file = paths(tmp_path)
    entries = [ListEntry(make_item(locator="https://a"))]
    save_list(entries, list_file)

    read_item("s1", "https://a", list_file=list_file, history_file=history_file)

    updated = load_list(list_file)
    assert updated[0].status == "read"
    assert history_locators(history_file) == {"https://a"}


def test_skip_item_removes_it_from_the_list_and_records_miss(tmp_path):
    list_file, history_file = paths(tmp_path)
    entries = [ListEntry(make_item(locator="https://a"))]
    save_list(entries, list_file)

    skip_item("s1", "https://a", list_file=list_file, history_file=history_file)

    assert load_list(list_file) == []
    assert history_locators(history_file) == {"https://a"}


def test_skip_item_leaves_other_entries_in_place(tmp_path):
    list_file, history_file = paths(tmp_path)
    entries = [ListEntry(make_item(locator="https://a")), ListEntry(make_item(locator="https://b"))]
    save_list(entries, list_file)

    skip_item("s1", "https://a", list_file=list_file, history_file=history_file)

    remaining = load_list(list_file)
    assert len(remaining) == 1
    assert remaining[0].item.locator == "https://b"


def test_read_item_ignores_non_pending_entries(tmp_path):
    list_file, history_file = paths(tmp_path)
    entries = [ListEntry(make_item(locator="https://a"), "read")]
    save_list(entries, list_file)

    read_item("s1", "https://a", list_file=list_file, history_file=history_file)

    assert history_locators(history_file) == set()
