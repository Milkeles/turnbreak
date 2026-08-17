"""Install turnbreak's turn-start/turn-stop hook into an agent's config.

Each agent registers hooks differently, but every format here is JSON
(Claude Code, Gemini CLI, and Codex share the same hooks-array shape;
Copilot CLI's hooks and extension manifest are also JSON), and
installation is always a merge into whatever config the user already
has there, never a raw overwrite.
"""

from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path
from typing import Any

AGENTS = ("claude", "codex", "gemini", "copilot")


def adapters_dir() -> Path:
    return Path(__file__).resolve().parent / "adapters"


def hook_script_path() -> Path:
    return adapters_dir() / "turnbreak-hook.py"


def hook_command() -> str:
    exe = sys.executable or "python3"
    return f"{shlex.quote(exe)} {shlex.quote(str(hook_script_path()))}"


def turnbreak_command() -> str:
    """The concrete invocation for this installed turnbreak, since it isn't on PATH.

    turnbreak isn't published to a package index, so a bare `turnbreak` in
    installed docs would send a future session guessing for an install
    source. Point at this exact interpreter and module instead.
    """
    exe = sys.executable or "python3"
    return f"{shlex.quote(exe)} -m turnbreak.cli"


def skill_source_path() -> Path:
    return adapters_dir() / "SKILL.md"


def copilot_snap_common_dir() -> Path:
    return Path.home() / "snap" / "copilot-cli" / "common"


def copilot_home() -> Path:
    """Copilot CLI's config root, accounting for snap confinement.

    A snap-installed copilot-cli writes its real config under
    $SNAP_USER_COMMON (~/snap/copilot-cli/common/.copilot), not
    ~/.copilot. ~/.copilot can exist as a stray, unused directory even
    on a snap install, so presence of the snap common dir wins.
    """
    snap_common = copilot_snap_common_dir()
    if snap_common.is_dir():
        return snap_common / ".copilot"
    return Path.home() / ".copilot"


def default_skill_dir(agent: str) -> Path:
    if agent == "claude":
        return Path.home() / ".claude" / "skills" / "turnbreak"
    if agent == "copilot":
        return copilot_home() / "skills" / "turnbreak"
    raise ValueError(f"No skill directory for agent: {agent}")


def install_skill(target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    rendered = skill_source_path().read_text().replace("{{TURNBREAK_COMMAND}}", turnbreak_command())
    (target_dir / "SKILL.md").write_text(rendered)


def default_target(agent: str) -> Path:
    home = Path.home()
    if agent == "claude":
        return home / ".claude" / "settings.json"
    if agent == "codex":
        return home / ".codex" / "hooks.json"
    if agent == "gemini":
        return home / ".gemini" / "settings.json"
    if agent == "copilot":
        return copilot_home() / "extensions" / "turnbreak"
    raise ValueError(f"Unknown agent: {agent}")


def _deep_merge_json(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    for key, value in incoming.items():
        existing = base.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            _deep_merge_json(existing, value)
        elif isinstance(existing, list) and isinstance(value, list):
            base[key] = existing + [item for item in value if item not in existing]
        else:
            base[key] = value
    return base


def _render_template(name: str) -> str:
    return (adapters_dir() / name).read_text().replace("{{HOOK_COMMAND}}", hook_command())


def install_json(template_name: str, target: Path) -> None:
    template = json.loads(_render_template(template_name))
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(target.read_text()) if target.exists() else {}
    merged = _deep_merge_json(existing, template)
    target.write_text(json.dumps(merged, indent=2) + "\n")


def install_copilot_extension(target_dir: Path) -> None:
    from shutil import copyfile

    src_dir = adapters_dir() / "copilot_extension"
    target_dir.mkdir(parents=True, exist_ok=True)
    for name in ("extension.mjs", "package.json"):
        copyfile(src_dir / name, target_dir / name)


def default_copilot_hooks_dir() -> Path:
    return copilot_home() / "hooks"


def install_copilot_hooks(target_dir: Path) -> Path:
    """Install turnbreak's turn-start/turn-stop hooks for Copilot CLI.

    Copilot CLI reads every hooks/*.json file under its config root as
    an independent document, so unlike the other agents' shared config
    files this one is safe to own outright and overwrite in full rather
    than deep-merge.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    template = json.loads(_render_template("copilot_hooks.json"))
    dest = target_dir / "turnbreak.json"
    dest.write_text(json.dumps(template, indent=2) + "\n")
    return dest


def install(agent: str, target: Path | None) -> Path:
    """Install turnbreak's hook for agent, merging into target (or the
    agent's default config location if target is None). Returns the path
    written to.
    """
    dest = target if target is not None else default_target(agent)
    if agent == "claude":
        install_json("claude_settings.json", dest)
        install_skill(default_skill_dir(agent))
    elif agent == "gemini":
        install_json("gemini_settings.json", dest)
    elif agent == "codex":
        install_json("codex_hooks.json", dest)
    elif agent == "copilot":
        install_copilot_extension(dest)
        install_copilot_hooks(default_copilot_hooks_dir())
        install_skill(default_skill_dir(agent))
    else:
        raise ValueError(f"Unknown agent: {agent}")
    return dest
