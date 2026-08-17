from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from turnbreak.core.config import Config, load_config, save_config
from turnbreak.core.items import Item
from turnbreak.sources.finder import FinderContext

# In the order AGENTS.md lists them: claude -p, codex exec, gemini -p.
_AGENT_COMMANDS: list[tuple[str, list[str]]] = [
    ("claude", ["claude", "-p"]),
    ("codex", ["codex", "exec"]),
    ("gemini", ["gemini", "-p"]),
]

_PROMPT = """You are finding reading material for someone waiting on a coding agent to finish \
a turn.

Their interests:
{interests}

They have already read (don't repeat these):
{read_locators}

They already skipped these (don't repeat these either):
{skipped_locators}

Find {count} articles, blog posts, or pages matching their interests that they have not \
seen yet. Respond with ONLY a JSON array, no prose before or after it. Each element must be \
an object with exactly two string fields: "title" and "url".
"""


def detect_agent_command() -> list[str] | None:
    """Return the CLI invocation for whichever supported agent is installed, if any."""
    for binary, command in _AGENT_COMMANDS:
        if shutil.which(binary):
            return command
    return None


def _build_prompt(context: FinderContext, count: int) -> str:
    return _PROMPT.format(
        interests=context.interests.strip() or "(none given)",
        read_locators="\n".join(item.locator for item in context.read_items) or "(none)",
        skipped_locators="\n".join(item.locator for item in context.skipped_items) or "(none)",
        count=count,
    )


def _parse_candidates(output: str) -> list[dict[str, str]]:
    """Parse the agent's JSON array, tolerating prose wrapped around it."""
    text = output.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("["), text.rfind("]")
        if start == -1 or end == -1 or end < start:
            return []
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return []
    if not isinstance(data, list):
        return []
    candidates = []
    for entry in data:
        if (
            isinstance(entry, dict)
            and isinstance(entry.get("title"), str)
            and isinstance(entry.get("url"), str)
        ):
            candidates.append({"title": entry["title"], "url": entry["url"]})
    return candidates


class AgentFinder:
    """Finder that asks the user's installed coding agent for reading candidates.

    Spends the user's tokens on every find() call, since it shells out to
    claude -p / codex exec / gemini -p. Callers must gate this behind
    confirm_token_spend before the first run.
    """

    def __init__(
        self,
        command: list[str] | None = None,
        count: int = 5,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
        extractor: Callable[[str], tuple[str, int] | None] | None = None,
    ) -> None:
        self._command = command
        self._count = count
        self._runner = runner
        if extractor is None:
            # Imported lazily so confirm_token_spend, and anyone who just
            # wants agent detection, don't need the `sources` extra
            # (trafilatura/pypdf) installed. Only actually finding
            # candidates does.
            from turnbreak.sources.extract import extract_article

            extractor = extract_article
        self._extractor = extractor

    def find(self, context: FinderContext) -> list[Item]:
        command = self._command or detect_agent_command()
        if command is None:
            return []
        prompt = _build_prompt(context, self._count)
        result = self._runner(
            [*command, prompt],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []
        seen = {item.locator for item in (*context.read_items, *context.skipped_items)}
        items = []
        for candidate in _parse_candidates(result.stdout):
            url = candidate["url"]
            if url in seen:
                continue
            seen.add(url)
            extracted = self._extractor(url)
            if extracted is None:
                continue
            body, word_count = extracted
            items.append(
                Item(
                    title=candidate["title"],
                    locator=url,
                    word_count=word_count,
                    source="curated",
                    body=body,
                )
            )
        return items


def confirm_token_spend(
    prompt: Callable[[str], str] = input,
    config: Config | None = None,
    path: Path | None = None,
) -> bool:
    """Warn that the agent finder spends tokens before its first run, and record acceptance.

    Returns True once the finder is cleared to run, either because a past
    call already recorded acceptance or because this call just did.
    """
    current = config if config is not None else load_config(path)
    if current.agent_finder_accepted:
        return True
    answer = prompt(
        "The agent finder runs your coding agent's CLI to find reading material. "
        "This spends your tokens every time it runs. Continue? [y/N] "
    )
    if answer.strip().lower() != "y":
        return False
    save_config(replace(current, agent_finder_accepted=True), path)
    return True
