from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

from turnbreak.core import state
from turnbreak.core.config import load_config
from turnbreak.core.signal import push_done_signal


def cmd_start(session_id: str) -> int:
    turn_start = time.time()
    state.start_turn(session_id, turn_start)
    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "turnbreak.core.watcher",
            "--session-id",
            session_id,
            "--turn-start",
            repr(turn_start),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    sys.stdout.write(json.dumps({"ok": True}) + "\n")
    return 0


def cmd_stop(session_id: str) -> int:
    state.end_turn(session_id)
    config = load_config()
    push_done_signal(config.port, session_id)
    sys.stdout.write(json.dumps({"ok": True}) + "\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="turnbreak")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="Begin watching a turn.")
    start.add_argument("--session-id", required=True)

    stop = subparsers.add_parser("stop", help="End a turn and notify the page.")
    stop.add_argument("--session-id", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    parsed = build_parser().parse_args(args)
    if parsed.command == "start":
        return cmd_start(parsed.session_id)
    if parsed.command == "stop":
        return cmd_stop(parsed.session_id)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
