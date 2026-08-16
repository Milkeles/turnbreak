from turnbreak.core import state
from turnbreak.core.actions import keep_reading, read_item, skip_item
from turnbreak.core.items import Item, ListEntry, history_locators, load_list, save_list


def make_item(title="Example", locator="https://example.com/a", word_count=460, source="curated"):
    return Item(title=title, locator=locator, word_count=word_count, source=source)


def paths(tmp_path):
    return tmp_path / "list.jsonl", tmp_path / "history.jsonl", tmp_path / "state.json"


def test_read_item_marks_read_and_records_match(tmp_path):
    list_file, history_file, state_file = paths(tmp_path)
    entries = [ListEntry(make_item(locator="https://a"))]
    save_list(entries, list_file)

    read_item(
        "s1", "https://a", list_file=list_file, history_file=history_file, state_file=state_file
    )

    updated = load_list(list_file)
    assert updated[0].status == "read"
    assert history_locators(history_file) == {"https://a"}


def test_skip_item_marks_skipped_and_records_miss(tmp_path):
    list_file, history_file, state_file = paths(tmp_path)
    entries = [ListEntry(make_item(locator="https://a"))]
    save_list(entries, list_file)

    skip_item(
        "s1", "https://a", list_file=list_file, history_file=history_file, state_file=state_file
    )

    updated = load_list(list_file)
    assert updated[0].status == "skipped"
    assert history_locators(history_file) == {"https://a"}


def test_read_item_ignores_non_pending_entries(tmp_path):
    list_file, history_file, state_file = paths(tmp_path)
    entries = [ListEntry(make_item(locator="https://a"), "read")]
    save_list(entries, list_file)

    read_item(
        "s1", "https://a", list_file=list_file, history_file=history_file, state_file=state_file
    )

    assert history_locators(history_file) == set()


def test_read_item_clears_held_status(tmp_path):
    list_file, history_file, state_file = paths(tmp_path)
    save_list([ListEntry(make_item(locator="https://a"))], list_file)
    state.save_state(
        state.SessionState(session_id="s1", turn_start=0.0, hold_status="held"), state_file
    )

    read_item(
        "s1", "https://a", list_file=list_file, history_file=history_file, state_file=state_file
    )

    assert state.load_state(state_file).hold_status == "none"


def test_skip_item_clears_held_status(tmp_path):
    list_file, history_file, state_file = paths(tmp_path)
    save_list([ListEntry(make_item(locator="https://a"))], list_file)
    state.save_state(
        state.SessionState(session_id="s1", turn_start=0.0, hold_status="held"), state_file
    )

    skip_item(
        "s1", "https://a", list_file=list_file, history_file=history_file, state_file=state_file
    )

    assert state.load_state(state_file).hold_status == "none"


def test_resolve_does_not_clear_hold_for_other_session(tmp_path):
    list_file, history_file, state_file = paths(tmp_path)
    save_list([ListEntry(make_item(locator="https://a"))], list_file)
    state.save_state(
        state.SessionState(session_id="other", turn_start=0.0, hold_status="held"), state_file
    )

    read_item(
        "s1", "https://a", list_file=list_file, history_file=history_file, state_file=state_file
    )

    assert state.load_state(state_file).hold_status == "held"


def test_keep_reading_sets_hold_status(tmp_path):
    _, _, state_file = paths(tmp_path)
    state.save_state(state.SessionState(session_id="s1", turn_start=0.0), state_file)

    result = keep_reading("s1", state_file=state_file)

    assert result.hold_status == "held"
    assert state.load_state(state_file).hold_status == "held"


def test_keep_reading_returns_none_for_mismatched_session(tmp_path):
    _, _, state_file = paths(tmp_path)
    state.save_state(state.SessionState(session_id="other", turn_start=0.0), state_file)

    assert keep_reading("s1", state_file=state_file) is None


def test_keep_reading_returns_none_when_no_state(tmp_path):
    _, _, state_file = paths(tmp_path)

    assert keep_reading("s1", state_file=state_file) is None
