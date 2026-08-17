Adapter templates

Each agent registers a hook script via a local config file. The repository
ships templates in `src/turnbreak/adapters/` for Claude Code, Codex,
Gemini CLI, and Copilot CLI. Run `turnbreak install AGENT` (with
an optional PATH override) to merge the hook into the agent's config in
place. Existing settings are preserved, not overwritten.

Claude Code
- File: `~/.claude/settings.json` by default
- Template: `src/turnbreak/adapters/claude_settings.json`
- Events: `UserPromptSubmit` -> start, `Stop` -> end
- Schema: `hooks.<Event>` is an array of `{"matcher": "*", "hooks": [{"type": "command", "command": ..., "timeout": ...}]}`

Codex
- File: `~/.codex/config.toml` by default (hooks live under the `[hooks]`
  table alongside the rest of Codex's config, not a standalone file)
- Template: `src/turnbreak/adapters/codex_hooks.toml`
- Events: `UserPromptSubmit` and `Stop`, each an array of `[[hooks.<Event>]]` tables with a `hooks` array of `{type = "command", command = ...}`

Gemini CLI
- File: `~/.gemini/settings.json` by default
- Template: `src/turnbreak/adapters/gemini_settings.json`
- Events: `BeforeAgent` and `AfterAgent`, same matcher-group array shape as Claude Code (matcher optional)

Copilot CLI
- File: `~/.copilot/hooks/turnbreak.json`, installed alongside a
  `/turnbreak-interests` slash command extension at
  `~/.copilot/extensions/turnbreak/`. `turnbreak install copilot`
  installs both.
- Template: `src/turnbreak/adapters/copilot_hooks.json`
- Events: `userPromptSubmitted` -> start, `agentStop` -> end. Copilot's
  documented payloads carry no event name, unlike the other three agents,
  so the hooks file passes `--hint start` / `--hint end` to
  `turnbreak-hook.py` instead of relying on payload sniffing. See
  `docs/adrs/0003-copilot-hooks-turn-boundary-events.md` for why.

All templates use a `{{HOOK_COMMAND}}` placeholder, filled in at install
time with the current Python interpreter and the absolute path to
`src/turnbreak/adapters/turnbreak-hook.py`, so the installed hook works
regardless of the caller's working directory.

Security
- The hook writes only a single JSON object to stdout. Use stderr for
  any debug output so agent parsers are not confused.

Testing
- Tests load the hook script directly by file path (see `tests/test_hook.py`).
  `main(payload, call_turnbreak=...)` accepts an injected callback to avoid
  subprocess side effects during tests.
