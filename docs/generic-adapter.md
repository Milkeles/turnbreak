Adapter templates

Each agent registers a hook script via a local config file. The repository
ships templates for Claude Code, Codex, Gemini CLI, and Copilot. Use
`turnbreak install AGENT PATH` to copy the template into a location the
agent expects and adjust the path to `scripts/turnbreak-hook.py` if needed.

Claude Code
- File: `.claude/settings.json`
- Template: `adapters/claude_settings.json`
- Events: `UserPromptSubmit` -> start, `Stop` -> end

Codex
- File: `.codex/hooks.json`
- Template: `adapters/codex_hooks.json`
- Events: top-level keys named `UserPromptSubmit` and `Stop`

Gemini CLI
- File: `settings.json` (in the Gemini config dir)
- Template: `adapters/gemini_settings.json`
- Events: `BeforeAgent` and `AfterAgent`

Copilot
- Template: `adapters/copilot_template.json` is a placeholder. Verify the
  current Copilot hooks reference for correct event names and update the
  template before installing.

Security
- The hook writes only a single JSON object to stdout. Use stderr for
  any debug output so agent parsers are not confused.

Testing
- The hook script is importable as `scripts.turnbreak_hook` for unit
  testing; `main(payload, call_turnbreak=...)` accepts an injected
  callback to avoid subprocess side effects during tests.
