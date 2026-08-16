from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Callable

from turnbreak.core import state
from turnbreak.core.config import load_config
from turnbreak.core.fire import on_fire as _on_fire


def wait_for_threshold(
    turn_start: float,
    threshold_seconds: float,
    *,
    now: Callable[[], float] = time.time,
    sleep: Callable[[float], None] = time.sleep,
    poll_interval: float = 1.0,
    is_cancelled: Callable[[], bool] = lambda: False,
) -> bool:
    """Block until threshold_seconds have passed since turn_start.

    Returns True once the threshold is reached. Returns False as soon as
    is_cancelled reports True, without waiting any further.
    """
    while True:
        if is_cancelled():
            return False
        elapsed = now() - turn_start
        if elapsed >= threshold_seconds:
            return True
        sleep(min(poll_interval, threshold_seconds - elapsed))


def default_on_fire(session_id: str) -> None:
    _on_fire(session_id)


def make_is_cancelled(session_id: str) -> Callable[[], bool]:
    def is_cancelled() -> bool:
        current = state.load_state()
        if current is None or current.session_id != session_id or current.turn_ended:
            return True
        return current.hold_status == "held"

    return is_cancelled


def run(
    session_id: str,
    turn_start: float,
    on_fire: Callable[[str], None] = default_on_fire,
) -> None:
    config = load_config()
    reached = wait_for_threshold(
        turn_start,
        config.threshold_seconds,
        is_cancelled=make_is_cancelled(session_id),
    )
    if reached:
        on_fire(session_id)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="turnbreak-watcher")
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--turn-start", required=True, type=float)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    run(args.session_id, args.turn_start)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
