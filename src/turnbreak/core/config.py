from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


def config_dir() -> Path:
    return Path.home() / ".config" / "turnbreak"


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
    agent_finder_accepted: bool = False


def load_config(path: Path | None = None) -> Config:
    path = path or config_path()
    if not path.exists():
        return Config()
    with path.open("rb") as f:
        data = tomllib.load(f)
    defaults = Config()
    target = data.get("target_read_minutes", list(defaults.target_read_minutes))
    return Config(
        port=data.get("port", defaults.port),
        threshold_seconds=data.get("threshold_seconds", defaults.threshold_seconds),
        words_per_minute=data.get("words_per_minute", defaults.words_per_minute),
        target_read_minutes=(target[0], target[1]),
        mode=data.get("mode", defaults.mode),
        folder_path=data.get("folder_path", defaults.folder_path),
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
        f"agent_finder_accepted = {json.dumps(config.agent_finder_accepted)}",
    ]
    if config.folder_path is not None:
        lines.append(f"folder_path = {json.dumps(config.folder_path)}")
    path.write_text("".join(line + "\n" for line in lines))
