from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

from turnbreak.core.browser import open_reading_tab
from turnbreak.core.config import load_config


def on_fire(session_id: str, *, retry_delay: float = 0.3) -> None:
    """Ensure the server is running and the reading tab is open.

    Item content is pushed by the sources and actions layer (P3, P4),
    which doesn't exist yet. This seam only guarantees a tab exists for
    it to land in, and reuses the tab instead of opening a new one.
    """
    config = load_config()
    clients = _client_count(config.port)
    if clients is None:
        _spawn_server(config.port)
        time.sleep(retry_delay)
        clients = _client_count(config.port)
    if clients == 0:
        open_reading_tab(f"http://127.0.0.1:{config.port}/")


def _client_count(port: int, timeout: float = 0.5) -> int | None:
    url = f"http://127.0.0.1:{port}/status"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = json.loads(response.read())
            return int(data.get("clients", 0))
    except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError):
        return None


def _spawn_server(port: int) -> None:
    subprocess.Popen(
        [sys.executable, "-m", "turnbreak.cli", "serve", "--port", str(port)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
