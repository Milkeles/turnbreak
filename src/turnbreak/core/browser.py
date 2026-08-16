from __future__ import annotations

import os
import webbrowser


def open_reading_tab(url: str) -> bool:
    """Open the reading page in the user's default browser.

    Returns False, without opening anything, when TURNBREAK_NO_BROWSER is
    set. Tests must set this so they never pop open a real browser window.
    """
    if os.environ.get("TURNBREAK_NO_BROWSER"):
        return False
    return webbrowser.open(url)
