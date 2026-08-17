from dataclasses import replace

from turnbreak.core.state import end_turn, load_state, save_state, start_turn


def test_start_turn_creates_state(tmp_path):
    path = tmp_path / "state.json"
    state = start_turn("abc", 100.0, path)
    assert state.session_id == "abc"
    assert state.turn_start == 100.0
    assert state.turn_ended is False
    assert load_state(path) == state


def test_start_turn_preserves_shown_locator_across_turns(tmp_path):
    path = tmp_path / "state.json"
    start_turn("abc", 100.0, path)
    shown = replace(load_state(path), shown_locator="https://a")
    save_state(shown, path)

    next_state = start_turn("abc", 200.0, path)

    assert next_state.shown_locator == "https://a"


def test_end_turn_marks_ended(tmp_path):
    path = tmp_path / "state.json"
    start_turn("abc", 100.0, path)

    ended = end_turn("abc", path)

    assert ended.turn_ended is True
    assert load_state(path).turn_ended is True


def test_end_turn_ignores_mismatched_session(tmp_path):
    path = tmp_path / "state.json"
    start_turn("abc", 100.0, path)

    result = end_turn("some-other-session", path)

    assert result is None
    assert load_state(path).turn_ended is False


def test_end_turn_with_no_state_is_a_noop(tmp_path):
    path = tmp_path / "state.json"
    assert end_turn("abc", path) is None


def test_load_state_missing_file_returns_none(tmp_path):
    path = tmp_path / "state.json"
    assert load_state(path) is None


def test_load_state_torn_file_returns_none(tmp_path):
    path = tmp_path / "state.json"
    path.write_text('{"session_id": "abc", "turn_st')  # cut off mid-write
    assert load_state(path) is None


def test_save_state_leaves_no_temp_file(tmp_path):
    path = tmp_path / "state.json"
    start_turn("abc", 100.0, path)
    assert list(tmp_path.iterdir()) == [path]
