Copilot CLI integration for turnbreak

turnbreak uses two separate Copilot CLI mechanisms:

1. A CLI extension (this directory), for the manual `/turnbreak-interests`
   slash command.
2. A personal hooks file at `~/.copilot/hooks/turnbreak.json` (see
   `../copilot_hooks.json`), for the actual turn-start/turn-stop signal.
   Copilot CLI's `userPromptSubmitted` and `agentStop` events map to
   `turnbreak start`/`turnbreak stop`, the same as the other agents.

Files
- `extension.mjs`: the extension itself. Exports `activate(sdk)`, which
  registers the slash command via `sdk.registerSlashCommand`. Logs
  activation and handler calls to `~/.copilot/extensions/turnbreak/turnbreak.log`
  for debugging.
- `package.json`: extension manifest.

Install

Run `turnbreak install copilot`. It installs both the extension (into
`~/.copilot/extensions/turnbreak/`) and the hooks file (into
`~/.copilot/hooks/turnbreak.json`) for you. No manual steps needed.

Copilot CLI's documented hook payloads don't carry the event name the
way Claude Code, Codex, and Gemini CLI's do, so the hooks file passes an
extra `--hint start`/`--hint end` argument to `turnbreak-hook.py` instead
of relying on payload sniffing.

Notes
- Extensions run with your user privileges. Only install extensions you
  trust.
- See the Copilot CLI extension docs for the full SDK reference:
  https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-cli-extensions
- See the Copilot CLI hooks reference for the hooks file format:
  https://docs.github.com/en/copilot/reference/hooks-reference
