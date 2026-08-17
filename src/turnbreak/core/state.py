from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from turnbreak.core.config import atomic_write_text, config_dir


@dataclass(frozen=True)
class SessionState:
    session_id: str
    turn_start: float
    shown_locator: str | None = None
    turn_ended: bool = False


def state_path() -> Path:
    return config_dir() / "state.json"


def load_state(path: Path | None = None) -> SessionState | None:
    path = path or state_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return SessionState(**data)
    except (json.JSONDecodeError, KeyError, TypeError):
        # A concurrent writer (another agent's hook firing at the same
        # moment) can tear this file mid-write. Treat it as "no state"
        # rather than crashing the hook that's reading it.
        return None


def save_state(state: SessionState, path: Path | None = None) -> None:
    path = path or state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, json.dumps(asdict(state)))


def start_turn(session_id: str, turn_start: float, path: Path | None = None) -> SessionState:
    existing = load_state(path)
    shown_locator = existing.shown_locator if existing else None
    state = SessionState(session_id=session_id, turn_start=turn_start, shown_locator=shown_locator)
    save_state(state, path)
    return state


def end_turn(session_id: str, path: Path | None = None) -> SessionState | None:
    existing = load_state(path)
    if existing is None or existing.session_id != session_id:
        return None
    ended = SessionState(
        session_id=existing.session_id,
        turn_start=existing.turn_start,
        shown_locator=existing.shown_locator,
        turn_ended=True,
    )
    save_state(ended, path)
    return ended
