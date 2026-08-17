from __future__ import annotations

import json
import os
import tomllib
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


def config_dir() -> Path:
    return Path.home() / ".config" / "turnbreak"


def atomic_write_text(path: Path, text: str) -> None:
    """Write text to path so readers never see a torn/partial file.

    turnbreak's hook fires once per turn per agent, and several agents can
    have overlapping turns (or the same agent's background watcher can
    overlap a hook invocation). Concurrent plain write_text() calls to the
    same shared state file can interleave and leave a corrupt file that
    crashes every subsequent reader. Writing to a uniquely-named sibling
    temp file first and renaming is atomic on POSIX, so a reader only ever
    sees the fully-old or fully-new content.
    """
    tmp = path.with_name(f".{path.name}.tmp-{uuid.uuid4().hex}")
    try:
        tmp.write_text(text)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def config_path() -> Path:
    return config_dir() / "config.toml"


@dataclass(frozen=True)
class Config:
    port: int = 7717
    threshold_seconds: float = 90
    words_per_minute: int = 230
    target_read_minutes: tuple[int, int] = (2, 4)
    mode: Literal["curated", "folder"] = "curated"
    folder_path: str | None = None
    finder: Literal["agent", "rss", "search"] = "agent"
    agent_finder_accepted: bool = False


def load_config(path: Path | None = None) -> Config:
    path = path or config_path()
    if not path.exists():
        return Config()
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError:
        # A concurrent writer can tear this file mid-write; fall back to
        # defaults rather than crashing whatever is reading config.
        return Config()
    defaults = Config()
    target = data.get("target_read_minutes", list(defaults.target_read_minutes))
    return Config(
        port=data.get("port", defaults.port),
        threshold_seconds=data.get("threshold_seconds", defaults.threshold_seconds),
        words_per_minute=data.get("words_per_minute", defaults.words_per_minute),
        target_read_minutes=(target[0], target[1]),
        mode=data.get("mode", defaults.mode),
        folder_path=data.get("folder_path", defaults.folder_path),
        finder=data.get("finder", defaults.finder),
        agent_finder_accepted=data.get("agent_finder_accepted", defaults.agent_finder_accepted),
    )


def save_config(config: Config, path: Path | None = None) -> None:
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"port = {config.port}",
        f"threshold_seconds = {config.threshold_seconds}",
        f"words_per_minute = {config.words_per_minute}",
        f"target_read_minutes = [{config.target_read_minutes[0]}, {config.target_read_minutes[1]}]",
        f"mode = {json.dumps(config.mode)}",
        f"finder = {json.dumps(config.finder)}",
        f"agent_finder_accepted = {json.dumps(config.agent_finder_accepted)}",
    ]
    if config.folder_path is not None:
        lines.append(f"folder_path = {json.dumps(config.folder_path)}")
    atomic_write_text(path, "".join(line + "\n" for line in lines))
