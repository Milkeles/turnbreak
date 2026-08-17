"""Start, find, and stop the background reading-page server process.

`fire.py`'s watcher path and the `turnbreak serve` CLI command both need to
spawn the server as a detached background process and later check whether
one is already running. This module is the one place that does either, so
a server started by a turn firing can be stopped by `turnbreak serve --stop`
and vice versa.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from turnbreak.core.config import config_dir


def pid_path() -> Path:
    return config_dir() / "server.pid"


def client_count(port: int, timeout: float = 0.5) -> int | None:
    """Number of connected reading tabs, or None if no server answers."""
    url = f"http://127.0.0.1:{port}/status"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = json.loads(response.read())
            return int(data.get("clients", 0))
    except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError):
        return None


def spawn_server(port: int) -> None:
    """Start the server as a detached background process and record its PID."""
    process = subprocess.Popen(
        [sys.executable, "-m", "turnbreak.cli", "serve", "--port", str(port), "--foreground"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    path = pid_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(process.pid))


def stop_server() -> bool:
    """Stop a server started by `spawn_server`, if one is still running.

    Returns True if a process was signaled, False if there was nothing to
    stop (no recorded PID, or the recorded process is already gone).
    """
    path = pid_path()
    if not path.exists():
        return False
    try:
        pid = int(path.read_text().strip())
    except ValueError:
        path.unlink(missing_ok=True)
        return False
    path.unlink(missing_ok=True)
    try:
        os.kill(pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        return False
    return True
