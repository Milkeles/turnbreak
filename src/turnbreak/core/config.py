from __future__ import annotations

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
    )
