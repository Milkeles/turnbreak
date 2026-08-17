#!/usr/bin/env python3
"""Universal hook script for Claude Code, Codex, Gemini CLI, and Copilot.

Reads JSON from stdin and maps agent turn start/end events to
`turnbreak start` and `turnbreak stop`. Writes a single JSON object to
stdout on completion and nothing else to stdout. Use stderr for debug.

This script intentionally avoids heavy imports and uses subprocess to
call the installed `turnbreak` console script so the hook process stays
small and fast.

Claude Code, Codex, and Gemini CLI all put the event name somewhere in
the stdin payload, so those agents are handled by sniffing it there (see
_detect_event). Copilot CLI's documented hook payloads don't include the
event name at all, so its hooks.json config passes `--hint start`/`--hint
end` as an extra argument instead; that takes priority when present.
"""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any


def config_dir() -> Path:
    return Path.home() / ".config" / "turnbreak"


def _read_payload() -> dict[str, Any]:
    data = sys.stdin.read()
    if not data:
        return {}
    try:
        parsed: Any = json.loads(data)
    except Exception:
        return {"raw": data}
    return parsed if isinstance(parsed, dict) else {"raw": data}


START_EVENTS = {"UserPromptSubmit", "BeforeAgent", "userPromptSubmitted"}
END_EVENTS = {"Stop", "AfterAgent", "agentStop"}


def _detect_event(payload: dict[str, Any]) -> str | None:
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


def _hint_event(argv: list[str]) -> str | None:
    if "--hint" not in argv:
        return None
    index = argv.index("--hint")
    if index + 1 >= len(argv):
        return None
    value = argv[index + 1]
    return value if value in ("start", "end") else None


def main(
    payload: dict[str, Any] | None = None,
    *,
    call_turnbreak: Callable[[list[str]], int] | None = None,
    argv: list[str] | None = None,
) -> dict[str, Any]:
    """Process a payload and return a dict describing the outcome.

    When called with payload None, it reads JSON from stdin. The
    optional call_turnbreak callback replaces the subprocess call for
    testing.
    """
    if payload is None:
        payload = _read_payload()
    event = _hint_event(sys.argv[1:] if argv is None else argv) or _detect_event(payload)
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
    result: dict[str, Any] = {"ok": False, "reason": "unrecognized_event"}
    print(json.dumps(result))
    return result


if __name__ == "__main__":
    main()
