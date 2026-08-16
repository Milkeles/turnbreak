from __future__ import annotations

from pathlib import Path

from turnbreak.core.config import config_dir


def interests_path() -> Path:
    return config_dir() / "interests.md"


def load_interests(path: Path | None = None) -> str:
    path = path or interests_path()
    if not path.exists():
        return ""
    return path.read_text()
