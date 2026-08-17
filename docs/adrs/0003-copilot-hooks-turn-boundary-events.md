# ADR-0003: Use Copilot CLI's `~/.copilot/hooks/*.json` mechanism for the Copilot adapter, with a `--hint` argument instead of payload sniffing

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-08-16 |
| **Deciders** | Hristo Hristov (maintainer), via agent-assisted build |

---

## Context and problem statement

P6 needed the Copilot adapter's turn-start and turn-end event names, per the delegated decision in `TASKS.md` section 4: match Copilot's events to the two the other three agents use, or ship without the Copilot adapter and say so.

The repo already shipped a Copilot CLI *extension* (`~/.copilot/extensions/turnbreak/`, `extension.mjs`) registering a manual `/turnbreak-interests` slash command. It never called `turnbreak start`/`turnbreak stop` on any turn boundary. `turnbreak-hook.py`'s docstring claimed universal support across all four agents, which was untrue for Copilot specifically until this decision.

---

## Decision drivers

- The other three adapters (`claude_settings.json`, `codex_hooks.json`, `gemini_settings.json`) all register the same `turnbreak-hook.py` script under agent-specific turn-start/turn-end event keys, and that script detects which event fired by sniffing the JSON payload on stdin for the event name.
- Copilot CLI's extension SDK (the `activate(sdk)` function extensions export) only exposes `registerSlashCommand`/`registerTool`-style APIs, not turn-boundary hooks. Confirmed via the Copilot CLI extension docs.
- Copilot CLI separately supports a real hooks mechanism: JSON files at `~/.copilot/hooks/*.json` (`version: 1`, event names as keys, `{"type": "command", "bash": "..."}` entries), confirmed via the official Copilot hooks reference and "Using hooks with GitHub Copilot CLI" docs. `userPromptSubmitted` fires on turn start. `agentStop` fires on turn end. That's a clean match to the other three agents' events.
- The documented payload shapes for those two events (`{"sessionId", "timestamp", "cwd", "prompt"}` for `userPromptSubmitted`; `{"sessionId", "timestamp", "transcriptPath", "stopReason", "stop_hook_active"}` for `agentStop`) do not include the event name anywhere in the payload, unlike Claude Code, Codex, and Gemini CLI's payloads. The existing sniffing approach in `_detect_event` would silently fail to classify either event.

---

## Considered options

1. Register the same universal `turnbreak-hook.py` command under both `userPromptSubmitted` and `agentStop` in a hooks.json file, relying on `_detect_event`'s existing payload-sniffing fallback.
2. Same as (1), but pass an extra CLI argument (`--hint start` / `--hint end`) in the hooks.json config, distinguishing the event by which config entry invoked the script rather than by payload content.
3. Ship without a Copilot turn-boundary adapter, keep the extension as slash-command-only, and say so in the README, per the fallback the delegated decision explicitly allows.

---

## Decision

We will use option 2: a new `copilot_hooks.json` template installed to `~/.copilot/hooks/turnbreak.json` via `turnbreak install copilot`, registering `turnbreak-hook.py --hint start` under `userPromptSubmitted` and `turnbreak-hook.py --hint end` under `agentStop`. `turnbreak-hook.py` now checks `sys.argv` for `--hint` before falling back to payload sniffing, so the other three agents' behavior is unchanged.

Option 1 was rejected because it depends on the documented payload actually containing the event name somewhere, which the reference docs show it does not for either Copilot event. Sniffing would work by accident if some undocumented field carries the event name, or fail silently if it doesn't. The `--hint` argument removes that uncertainty entirely, since the hooks.json config itself controls which invocation runs under which event.

Option 3 was rejected because option 2 works and is not meaningfully harder to build than the other three adapters. "Three agents working beats four half-working" was written for the case where no clean equivalent exists, and Copilot's `userPromptSubmitted`/`agentStop` pair is as clean an equivalent as Codex's or Gemini's.

The pre-existing Copilot extension (`/turnbreak-interests` slash command) is kept alongside the new hooks file. `turnbreak install copilot` installs both. They serve different purposes: one is a manual interests editor, the other is the automatic turn-boundary signal. Neither depends on the other.

---

## Consequences

**Positive**

- Copilot CLI now gets the actual core feature (a reading break while the agent works, a notification when it's done), not just a manual interests editor.
- `turnbreak-hook.py`'s docstring claim of universal four-agent support is now true.
- The `--hint` mechanism does not depend on undocumented payload fields the way sniffing does, and could be backported to the other adapters later if their payload shapes ever change, without needing another ADR to justify it.

**Negative**

- `turnbreak-hook.py` now has two independent detection paths (`--hint` argument, payload sniffing) instead of one, which is a small amount of extra surface to keep in sync if either agent's format changes.
- Verified only against the documented payload shapes and a simulated end-to-end run (real `hooks.json` invocation form, real stdin JSON, real SSE item push and done signal) in an isolated scratch environment. Not yet exercised against Copilot CLI actually firing these hooks itself in a live session, since that requires a real Copilot session to confirm the CLI invokes hooks exactly as documented.

**Follow-on work**

- Confirm against a real live Copilot CLI session (not just simulated payloads) that `userPromptSubmitted` and `agentStop` fire with the documented shape and timing, and update this ADR's confirmation section once done.

---

## Confirmation

`tests/test_hook.py` covers `_hint_event` and the full `--hint`-driven `main()` path with realistic Copilot payload shapes. `tests/test_install.py` covers `install_copilot_hooks` producing a valid, idempotent `~/.copilot/hooks/turnbreak.json`. A manual end-to-end run in an isolated scratch `HOME` (isolated port, no interference with any real server) confirmed: `--hint start` triggers `turnbreak start`, a background watcher fires after the threshold, `on_fire` scans the configured folder, and the item and done events arrive over SSE exactly as they do for the other three agents.

---

## More information

- Copilot hooks reference: https://docs.github.com/en/copilot/reference/hooks-reference
- Using hooks with GitHub Copilot CLI: https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-hooks
- Copilot CLI extension docs (confirms the extension SDK does not expose turn-boundary hooks): https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-cli-extensions

---

## Related documents

- [`TASKS.md`](../../TASKS.md) section 4, the delegated decision this ADR resolves.
- [`src/turnbreak/adapters/copilot_extension/README.md`](../../src/turnbreak/adapters/copilot_extension/README.md). Documents both the extension and the hooks file installed by `turnbreak install copilot`.
