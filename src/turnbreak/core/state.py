from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from turnbreak.core.config import config_dir

HoldStatus = Literal["none", "held"]


@dataclass(frozen=True)
class SessionState:
    session_id: str
    turn_start: float
    hold_status: HoldStatus = "none"
    turn_ended: bool = False


def state_path() -> Path:
    return config_dir() / "state.json"


def load_state(path: Path | None = None) -> SessionState | None:
    path = path or state_path()
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return SessionState(**data)


def save_state(state: SessionState, path: Path | None = None) -> None:
    path = path or state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state)))


def start_turn(session_id: str, turn_start: float, path: Path | None = None) -> SessionState:
    existing = load_state(path)
    hold_status: HoldStatus = existing.hold_status if existing else "none"
    state = SessionState(session_id=session_id, turn_start=turn_start, hold_status=hold_status)
    save_state(state, path)
    return state


def end_turn(session_id: str, path: Path | None = None) -> SessionState | None:
    existing = load_state(path)
    if existing is None or existing.session_id != session_id:
        return None
    ended = SessionState(
        session_id=existing.session_id,
        turn_start=existing.turn_start,
        hold_status=existing.hold_status,
        turn_ended=True,
    )
    save_state(ended, path)
    return ended
