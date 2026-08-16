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
