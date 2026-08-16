from __future__ import annotations

from pathlib import Path

from turnbreak.core.config import config_dir


def feeds_path() -> Path:
    return config_dir() / "feeds.txt"


def load_feeds(path: Path | None = None) -> list[str]:
    """Read the user's feed list, one URL per line, blank lines ignored."""
    path = path or feeds_path()
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]
