#!/usr/bin/env python3
"""Universal hook script for Claude Code, Codex, Gemini CLI, and Copilot.

Reads JSON from stdin and maps agent turn start/end events to
`turnbreak start` and `turnbreak stop`. Writes a single JSON object to
stdout on completion and nothing else to stdout. Use stderr for debug.

This script intentionally avoids heavy imports and uses subprocess to
call the installed `turnbreak` console script so the hook process stays
small and fast.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path


def config_dir() -> Path:
    return Path.home() / ".config" / "turnbreak"


def _read_payload() -> dict:
    data = sys.stdin.read()
    if not data:
        return {}
    try:
        return json.loads(data)
    except Exception:
        return {"raw": data}


START_EVENTS = {"UserPromptSubmit", "BeforeAgent"}
END_EVENTS = {"Stop", "AfterAgent"}


def _detect_event(payload: dict) -> str | None:
    # Search keys and values for known event names
    if not payload:
        return None
    # Direct key match (Codex uses top-level event names)
    for key in payload.keys():
        if key in START_EVENTS:
            return "start"
        if key in END_EVENTS:
            return "end"
    # Value search
    s = json.dumps(payload)
    for ev in START_EVENTS:
        if ev in s:
            return "start"
    for ev in END_EVENTS:
        if ev in s:
            return "end"
    return None


def _session_file() -> Path:
    return config_dir() / "hook_last_session"


def _call_turnbreak(args: list[str]) -> int:
    exe = sys.executable or "python3"
    cmd = [exe, "-m", "turnbreak.cli"] + args
    # Run and suppress stdout/stderr; hook must not write extra stdout
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return 0
    except Exception:
        return 1


def main(payload: dict | None = None, *, call_turnbreak: callable | None = None) -> dict:
    """Process a payload and return a dict describing the outcome.

    When called with payload None, it reads JSON from stdin. The
    optional call_turnbreak callback replaces the subprocess call for
    testing.
    """
    if payload is None:
        payload = _read_payload()
    event = _detect_event(payload)
    try:
        config_dir().mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    _call = call_turnbreak or _call_turnbreak
    if event == "start":
        session_id = uuid.uuid4().hex
        # record session id for the stop event
        try:
            _session_file().write_text(session_id)
        except Exception:
            pass
        _call(["start", "--session-id", session_id])
        out = {"ok": True}
        print(json.dumps(out))
        return out
    if event == "end":
        # read last session id
        try:
            sid = _session_file().read_text().strip()
        except Exception:
            sid = ""
        if not sid:
            sid = uuid.uuid4().hex
        _call(["stop", "--session-id", sid])
        try:
            _session_file().unlink()
        except Exception:
            pass
        out = {"ok": True}
        print(json.dumps(out))
        return out
    # Unknown event: exit gracefully with ok:false
    out = {"ok": False, "reason": "unrecognized_event"}
    print(json.dumps(out))
    return out


if __name__ == "__main__":
    main()
