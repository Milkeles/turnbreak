from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import replace
from typing import Literal

from turnbreak.core import state
from turnbreak.core.browser import open_reading_tab
from turnbreak.core.config import load_config, save_config
from turnbreak.core.server import serve_forever
from turnbreak.core.server_control import client_count, spawn_server, stop_server
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


def cmd_serve(port: int | None, *, foreground: bool = False, stop: bool = False) -> int:
    """Start, run, or stop the reading page server.

    With no flags, starts the server in the background (if one isn't
    already running), opens the reading tab, and prints its URL so the
    caller can link to it. --foreground runs it attached to this terminal
    instead, blocking until interrupted. --stop stops a server that was
    started in the background, either by this command or by a turn firing.
    """
    if foreground and stop:
        sys.stderr.write("--foreground and --stop can't be used together\n")
        return 2
    if stop:
        if stop_server():
            sys.stdout.write("Stopped the turnbreak server.\n")
            return 0
        sys.stderr.write("No running turnbreak server found.\n")
        return 1
    resolved_port = port if port is not None else load_config().port
    if foreground:
        serve_forever(resolved_port)
        return 0
    url = f"http://127.0.0.1:{resolved_port}/"
    if client_count(resolved_port) is None:
        spawn_server(resolved_port)
        time.sleep(0.3)
    open_reading_tab(url)
    sys.stdout.write(url + "\n")
    return 0


def cmd_mode(target: Literal["curated", "folder"], folder_path: str | None) -> int:
    if target == "folder" and not folder_path:
        sys.stderr.write("turnbreak mode folder requires a PATH\n")
        return 1
    if target == "folder" and folder_path is not None:
        from pathlib import Path

        if not Path(folder_path).is_dir():
            # Not fatal: the directory might be created after this call
            # (e.g. scripted setup that mkdirs afterwards). Left unwarned,
            # a typo here just silently returns nothing to read forever,
            # which is what happened in practice.
            sys.stderr.write(f"warning: {folder_path} is not a directory\n")
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


def cmd_onboard() -> int:
    """Interactive first-run onboarding writing interests.md and, if the
    configured finder is "agent", recording consent to spend tokens.

    Both steps are idempotent: an existing interests file, or already
    recorded consent, is left untouched.
    """
    from turnbreak.core.interests import interests_path

    path = interests_path()
    if path.exists():
        sys.stdout.write("Interests file already exists: " + str(path) + "\n")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        sys.stdout.write("Enter interests, one per line. Finish with an empty line:\n")
        lines: list[str] = []
        try:
            while True:
                line = input().rstrip("\n")
                if not line:
                    break
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            pass
        path.write_text("\n".join(lines) + ("\n" if lines else ""))
        sys.stdout.write("Wrote interests to " + str(path) + "\n")

    _confirm_agent_finder_if_needed()
    return 0


def _confirm_agent_finder_if_needed() -> int:
    from turnbreak.core.config import load_config
    from turnbreak.sources.agent import confirm_token_spend

    config = load_config()
    if config.finder != "agent" or config.agent_finder_accepted:
        return 0
    try:
        accepted = confirm_token_spend()
    except (EOFError, KeyboardInterrupt):
        accepted = False
    if accepted:
        sys.stdout.write("Agent finder enabled.\n")
    else:
        sys.stdout.write(
            "Agent finder not enabled; turnbreak won't show curated content until you "
            "run 'turnbreak onboard' again or switch finders with 'turnbreak finder'.\n"
        )
    return 0


def cmd_slash() -> int:
    """Write a simple slash command manifest to the config directory.

    The manifest is a small JSON file that other tools can read to register
    a slash command named `/turnbreak-interests` which opens the interests
    editor.
    """
    from turnbreak.core.config import config_dir

    manifest = {
        "name": "/turnbreak-interests",
        "description": "Edit your turnbreak interests",
        "action": {"type": "open_file", "path": str(config_dir() / "interests.md")},
    }
    path = config_dir() / "slash_turnbreak_interests.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    import json

    path.write_text(json.dumps(manifest, indent=2))
    sys.stdout.write("Wrote slash manifest to " + str(path) + "\n")
    return 0


def cmd_install(agent: str, target: str | None) -> int:
    """Install turnbreak's hook for agent in a single step.

    Merges into the agent's default config location (or the given target
    path) without disturbing existing settings already there.
    """
    from pathlib import Path

    from turnbreak import install as install_module

    dest_arg = Path(target) if target is not None else None
    try:
        dest = install_module.install(agent, dest_arg)
    except Exception as e:
        sys.stderr.write("Failed to install: " + str(e) + "\n")
        return 1
    sys.stdout.write("Installed turnbreak hook for " + agent + " into " + str(dest) + "\n")
    if agent == "claude":
        skill_dir = install_module.default_skill_dir(agent)
        sys.stdout.write("Installed turnbreak skill into " + str(skill_dir) + "\n")
    elif agent == "copilot":
        hooks_dir = install_module.default_copilot_hooks_dir()
        sys.stdout.write(
            "Installed turnbreak hooks into " + str(hooks_dir / "turnbreak.json") + "\n"
        )
    return 0


def cmd_watch(session_id: str | None, once: bool = False) -> int:
    """Terminal watch UI. When --once is true, print the current item and exit.

    Interactive mode offers simple single-character commands:
      r - mark read
      s - skip
      q - quit

    Doing nothing (or entering anything else) just redisplays the same
    item; there's no separate "keep reading" command since that's the
    default until you pick read or skip.

    The function avoids prompting when run inside an agent hook by being
    designed for a separate terminal. Tests call it directly with mocked
    input to exercise behavior.
    """
    from turnbreak.core.actions import read_item, skip_item
    from turnbreak.core.config import load_config
    from turnbreak.core.items import load_list, select_item

    config = load_config()
    sid = session_id or "watch-session"

    if once:
        entries = load_list()
        entry = select_item(entries, config.target_read_minutes, config.words_per_minute)
        if entry is None:
            sys.stdout.write("Nothing to read right now\n")
            return 0
        item = entry.item
        minutes = int(item.word_count / config.words_per_minute) if item.word_count else 0
        sys.stdout.write(f"{item.title} ({item.source}) — ~{minutes} min read\n")
        if item.is_pdf:
            sys.stdout.write("[PDF]\n")
        else:
            sys.stdout.write((item.body or "")[:1000] + "\n")
        return 0

    while True:
        entries = load_list()
        entry = select_item(entries, config.target_read_minutes, config.words_per_minute)
        if entry is None:
            sys.stdout.write("Nothing to read right now\n")
            return 0
        item = entry.item
        minutes = int(item.word_count / config.words_per_minute) if item.word_count else 0
        sys.stdout.write(f"{item.title} ({item.source}) — ~{minutes} min read\n")
        if item.is_pdf:
            sys.stdout.write("[PDF]\n")
        else:
            sys.stdout.write((item.body or "")[:1000] + "\n")
        try:
            choice = input("[r]ead [s]kip [q]uit: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            sys.stdout.write("\n")
            return 0
        if choice == "r":
            read_item(sid, item.locator)
            sys.stdout.write("Marked read.\n")
        elif choice == "s":
            skip_item(sid, item.locator)
            sys.stdout.write("Skipped.\n")
        elif choice == "q":
            return 0
        else:
            sys.stdout.write("Unknown command. Use r/s/q.\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="turnbreak")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="Begin watching a turn.")
    start.add_argument("--session-id", required=True)

    stop = subparsers.add_parser("stop", help="End a turn and notify the page.")
    stop.add_argument("--session-id", required=True)

    serve = subparsers.add_parser(
        "serve",
        help="Start the reading page server in the background, or run it in the foreground.",
    )
    serve.add_argument("--port", type=int, default=None)
    serve.add_argument(
        "--foreground",
        action="store_true",
        help="Run attached to this terminal instead of backgrounding.",
    )
    serve.add_argument(
        "--stop", action="store_true", help="Stop a server running in the background."
    )

    mode = subparsers.add_parser("mode", help="Switch between curated and folder sources.")
    mode.add_argument("target", choices=["curated", "folder"])
    mode.add_argument("path", nargs="?", default=None)

    finder = subparsers.add_parser("finder", help="Switch which finder builds the curated list.")
    finder.add_argument("name", choices=["agent", "rss", "search"])

    subparsers.add_parser("interests", help="Edit or show your interests file.")

    subparsers.add_parser("onboard", help="Run first-run onboarding to collect interests.")

    watch = subparsers.add_parser("watch", help="Terminal watch UI offering the two actions.")
    watch.add_argument("--session-id", default=None)
    watch.add_argument("--once", action="store_true")

    subparsers.add_parser("slash", help="Write the /turnbreak-interests slash command manifest.")

    install = subparsers.add_parser("install", help="Install turnbreak's hook for an agent.")
    install.add_argument("agent", choices=["claude", "codex", "gemini", "copilot"])
    install.add_argument("path", nargs="?", default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    parsed = build_parser().parse_args(args)
    if parsed.command == "start":
        return cmd_start(parsed.session_id)
    if parsed.command == "stop":
        return cmd_stop(parsed.session_id)
    if parsed.command == "serve":
        return cmd_serve(parsed.port, foreground=parsed.foreground, stop=parsed.stop)
    if parsed.command == "mode":
        return cmd_mode(parsed.target, parsed.path)
    if parsed.command == "finder":
        return cmd_finder(parsed.name)
    if parsed.command == "interests":
        return cmd_interests()
    if parsed.command == "onboard":
        return cmd_onboard()
    if parsed.command == "watch":
        return cmd_watch(parsed.session_id, parsed.once)
    if parsed.command == "slash":
        return cmd_slash()
    if parsed.command == "install":
        return cmd_install(parsed.agent, parsed.path)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
