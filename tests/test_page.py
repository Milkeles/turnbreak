from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / "src" / "turnbreak" / "page" / "index.html"


def _read() -> str:
    return PAGE.read_text()


def test_page_shell_exists():
    assert PAGE.exists()


def test_mark_done_sets_title_and_favicon_before_any_notification_check():
    content = _read()
    start = content.index("function markDone")
    guard = content.index("if (window.Notification", start)
    unconditional = content[start:guard]
    assert "document.title" in unconditional
    assert 'getElementById("favicon")' in unconditional


def test_done_handler_never_clears_or_hides_the_item():
    content = _read()
    start = content.index('addEventListener("done"')
    end = content.index("});", start)
    handler = content[start:end]
    assert "textContent" not in handler
    assert "hidden" not in handler
    assert "innerHTML" not in handler


def test_page_listens_for_end_event():
    content = _read()
    assert 'addEventListener("end"' in content


def test_page_has_end_of_list_placeholder_element():
    content = _read()
    assert 'id="end-of-list"' in content


def test_send_action_does_nothing_without_a_current_item():
    content = _read()
    start = content.index("function sendAction")
    end = content.index("}", content.index("fetch(", start))
    body = content[start:end]
    assert "if (!currentItem) return;" in body
