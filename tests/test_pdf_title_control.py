from pathlib import Path

PAGE = Path(__file__).resolve().parent.parent / "src" / "turnbreak" / "page" / "index.html"


def test_pdf_embed_and_mark_done_independent():
    content = PAGE.read_text()
    # Ensure the PDF embed logic writes a data:application/pdf src
    assert 'data:application/pdf' in content
    # Ensure markDone sets the document title and favicon regardless of Notification
    start = content.index("function markDone")
    guard = content.index("if (window.Notification", start)
    unconditional = content[start:guard]
    assert "document.title" in unconditional
    assert 'getElementById("favicon")' in unconditional
