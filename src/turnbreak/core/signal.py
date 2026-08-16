from __future__ import annotations

import json
import urllib.error
import urllib.request


def push_done_signal(port: int, session_id: str, timeout: float = 0.5) -> bool:
    """Tell the server a turn ended, if one is running.

    Returns False, silently, whenever no server is listening. Until P2
    implements the server's /done route, that's every call.
    """
    url = f"http://127.0.0.1:{port}/done"
    body = json.dumps({"session_id": session_id}).encode()
    request = urllib.request.Request(url, data=body, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout):
            return True
    except (urllib.error.URLError, OSError):
        return False
