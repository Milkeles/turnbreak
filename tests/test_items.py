from turnbreak.core.items import (
    Item,
    ListEntry,
    append_history,
    history_locators,
    load_history,
    load_list,
    read_minutes,
    save_list,
    select_item,
)


def make_item(title="Example", locator="https://example.com/a", word_count=460, source="curated"):
    return Item(title=title, locator=locator, word_count=word_count, source=source)


def test_save_and_load_list_round_trips(tmp_path):
    path = tmp_path / "list.jsonl"
    entries = [ListEntry(make_item("A"), "pending"), ListEntry(make_item("B"), "read")]
    save_list(entries, path)
    assert load_list(path) == entries


def test_load_list_missing_file_returns_empty(tmp_path):
    assert load_list(tmp_path / "list.jsonl") == []


def test_append_history_and_read_locators(tmp_path):
    path = tmp_path / "history.jsonl"
    append_history(make_item("A", locator="https://a"), "match", path)
    append_history(make_item("B", locator="https://b"), "miss", path)
    assert history_locators(path) == {"https://a", "https://b"}


def test_history_locators_missing_file_returns_empty_set(tmp_path):
    assert history_locators(tmp_path / "history.jsonl") == set()


def test_load_history_returns_items_with_outcomes(tmp_path):
    path = tmp_path / "history.jsonl"
    append_history(make_item("A", locator="https://a"), "match", path)
    append_history(make_item("B", locator="https://b"), "miss", path)
    records = load_history(path)
    assert records == [
        (make_item("A", locator="https://a"), "match"),
        (make_item("B", locator="https://b"), "miss"),
    ]


def test_load_history_missing_file_returns_empty_list(tmp_path):
    assert load_history(tmp_path / "history.jsonl") == []


def test_read_minutes_is_word_count_over_words_per_minute():
    item = make_item(word_count=460)
    assert read_minutes(item, 230) == 2.0


def test_select_item_prefers_items_inside_target_range():
    short = ListEntry(make_item("Short", word_count=115))  # 0.5 min at 230 wpm
    in_range = ListEntry(make_item("InRange", word_count=690))  # 3 min
    entries = [short, in_range]
    picked = select_item(entries, target_read_minutes=(2, 4), words_per_minute=230)
    assert picked == in_range


def test_select_item_skips_items_over_twice_the_upper_bound():
    too_long = ListEntry(make_item("TooLong", word_count=230 * 9))  # 9 min, > 2x4
    entries = [too_long]
    assert select_item(entries, target_read_minutes=(2, 4), words_per_minute=230) is None


def test_select_item_falls_back_to_any_pending_item_within_twice_the_bound():
    short = ListEntry(make_item("Short", word_count=115))  # 0.5 min
    entries = [short]
    picked = select_item(entries, target_read_minutes=(2, 4), words_per_minute=230)
    assert picked == short


def test_select_item_ignores_non_pending_entries():
    already_read = ListEntry(make_item("Read", word_count=690), "read")
    entries = [already_read]
    assert select_item(entries, target_read_minutes=(2, 4), words_per_minute=230) is None


def test_select_item_returns_none_for_empty_list():
    assert select_item([], target_read_minutes=(2, 4), words_per_minute=230) is None
