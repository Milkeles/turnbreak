from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import replace
from typing import Literal

from turnbreak.core import state
from turnbreak.core.config import load_config, save_config
from turnbreak.core.server import serve_forever
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


def cmd_serve(port: int | None) -> int:
    serve_forever(port if port is not None else load_config().port)
    return 0


def cmd_mode(target: Literal["curated", "folder"], folder_path: str | None) -> int:
    if target == "folder" and not folder_path:
        sys.stderr.write("turnbreak mode folder requires a PATH\n")
        return 1
    config = load_config()
    updated = replace(
        config,
        mode=target,
        folder_path=folder_path if target == "folder" else config.folder_path,
    )
    save_config(updated)
    sys.stdout.write(json.dumps({"ok": True, "mode": updated.mode}) + "\n")
    return 0


def cmd_finder(name: Literal["agent", "rss", "search"]) -> int:
    config = load_config()
    updated = replace(config, finder=name)
    save_config(updated)
    sys.stdout.write(json.dumps({"ok": True, "finder": updated.finder}) + "\n")
    return 0


def cmd_interests() -> int:
    """Open the user's interests file in $EDITOR, creating it if missing.

    If $EDITOR is not set, print the path so the caller can open it.
    """
    from turnbreak.core.interests import interests_path

    path = interests_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Your interests, one per line\n")
    editor = os.environ.get("EDITOR")
    if editor:
        try:
            subprocess.call([editor, str(path)])
            return 0
        except Exception:
            sys.stderr.write("Failed to launch editor\n")
            return 1
    else:
        sys.stdout.write(str(path) + "\n")
        return 0


def cmd_watch(session_id: str | None, once: bool = False) -> int:
    """Terminal watch UI. When --once is true, print the current item and exit.

    This is intentionally simple: it reads the list.jsonl from the config
    directory and prints the first pending item. It must not prompt when
    run inside an agent hook; watch is designed for a separate terminal.
    """
    from turnbreak.core.items import load_list, select_item
    from turnbreak.core.config import load_config

    config = load_config()
    entries = load_list()
    entry = select_item(entries, config.target_read_minutes, config.words_per_minute)
    if entry is None:
        sys.stdout.write("Nothing to read right now\n")
        return 0
    item = entry.item
    minutes = int(item.word_count / config.words_per_minute) if item.word_count else 0
    sys.stdout.write(f"{item.title} ({item.source}) — ~{minutes} min read\n")
    if item.pdf_data:
        sys.stdout.write("[PDF]\n")
    else:
        sys.stdout.write((item.body or "")[:1000] + "\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="turnbreak")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="Begin watching a turn.")
    start.add_argument("--session-id", required=True)

    stop = subparsers.add_parser("stop", help="End a turn and notify the page.")
    stop.add_argument("--session-id", required=True)

    serve = subparsers.add_parser("serve", help="Run the reading page server.")
    serve.add_argument("--port", type=int, default=None)
    serve.add_argument("--foreground", action="store_true")

    mode = subparsers.add_parser("mode", help="Switch between curated and folder sources.")
    mode.add_argument("target", choices=["curated", "folder"])
    mode.add_argument("path", nargs="?", default=None)

    finder = subparsers.add_parser("finder", help="Switch which finder builds the curated list.")
    finder.add_argument("name", choices=["agent", "rss", "search"])

    interests = subparsers.add_parser("interests", help="Edit or show your interests file.")

    watch = subparsers.add_parser("watch", help="Terminal watch UI offering the three actions.")
    watch.add_argument("--session-id", default=None)
    watch.add_argument("--once", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    parsed = build_parser().parse_args(args)
    if parsed.command == "start":
        return cmd_start(parsed.session_id)
    if parsed.command == "stop":
        return cmd_stop(parsed.session_id)
    if parsed.command == "serve":
        return cmd_serve(parsed.port)
    if parsed.command == "mode":
        return cmd_mode(parsed.target, parsed.path)
    if parsed.command == "finder":
        return cmd_finder(parsed.name)
    if parsed.command == "interests":
        return cmd_interests()
    if parsed.command == "watch":
        return cmd_watch(parsed.session_id, parsed.once)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
