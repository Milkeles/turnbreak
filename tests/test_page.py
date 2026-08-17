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


def test_end_of_list_keeps_previous_reachable_when_a_session_is_known():
    """Regression test: hiding #actions unconditionally at end-of-list
    stranded Previous once Next had been clicked through to the end,
    even though BrowseHistory still had somewhere to step back to.
    """
    content = _read()
    start = content.index("function showEndOfList")
    end = content.index("function markDone", start)
    body = content[start:end]
    assert 'document.getElementById("actions").hidden = !lastSessionId;' in body
    assert "lastSessionId = null" not in body


def test_show_item_records_last_session_id_for_later_use_at_end_of_list():
    content = _read()
    start = content.index("function showItem")
    end = content.index("function showEndOfList", start)
    body = content[start:end]
    assert "lastSessionId = item.session_id" in body


def test_send_action_does_nothing_without_a_current_item_or_known_session():
    content = _read()
    start = content.index("function sendAction")
    end = content.index("}", content.index("fetch(", start))
    body = content[start:end]
    assert "if (!currentItem && !lastSessionId) return;" in body


def test_pdf_display_never_navigates_the_shell():
    content = _read()
    start = content.index("function showItem")
    end = content.index("function showEndOfList", start)
    body = content[start:end]
    assert "location" not in body
    assert ".src = " not in body
    assert "/pdf?locator=" in body


def test_pdf_embed_element_exists_and_starts_hidden():
    content = _read()
    start = content.index('<embed id="pdf"')
    end = content.index("/>", start)
    tag = content[start:end]
    assert "hidden" in tag
