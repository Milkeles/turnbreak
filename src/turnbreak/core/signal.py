from __future__ import annotations

import json
import urllib.error
import urllib.request

from turnbreak.core.items import Item, item_payload


def push_item_signal(
    port: int, session_id: str, item: Item, words_per_minute: int, timeout: float = 0.5
) -> bool:
    """Tell the server to show item, if one is running.

    Returns False, silently, whenever no server is listening.
    """
    url = f"http://127.0.0.1:{port}/item"
    body = json.dumps(item_payload(item, session_id, words_per_minute)).encode()
    request = urllib.request.Request(url, data=body, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout):
            return True
    except (urllib.error.URLError, OSError):
        return False


def push_end_signal(port: int, timeout: float = 0.5) -> bool:
    """Tell the server the list is exhausted, if one is running.

    Returns False, silently, whenever no server is listening.
    """
    url = f"http://127.0.0.1:{port}/end"
    request = urllib.request.Request(url, data=b"{}", method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout):
            return True
    except (urllib.error.URLError, OSError):
        return False


def push_done_signal(port: int, session_id: str, timeout: float = 0.5) -> bool:
    """Tell the server a turn ended, if one is running.

    Returns False, silently, whenever no server is listening.
    """
    url = f"http://127.0.0.1:{port}/done"
    body = json.dumps({"session_id": session_id}).encode()
    request = urllib.request.Request(url, data=body, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout):
            return True
    except (urllib.error.URLError, OSError):
        return False
