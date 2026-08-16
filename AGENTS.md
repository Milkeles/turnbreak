# Agent instructions file: turnbreak

|  |  |
|---|---|
| **Covers** | Whole repo |
| **Last reviewed** | 2026-08-16 |

---

## 1. Project overview

Turnbreak is an installable agent skill. It shows you something worth reading while your coding agent works, then notifies you when the agent is done.

It fires only after the agent has been running for a set time. It runs in one reused browser tab, never in the agent's terminal.

The name is `turnbreak`, chosen 2026-08-16 over `interlude`, `idlepage`, and `waitread`. Naming decisions aren't ADRs and don't live in `docs/adrs/`. If the maintainer renames the project again, rename it everywhere in one commit.

---

## 2. Commands

| Task | Command |
|---|---|
| Install dependencies | `pip install -e ".[dev]"` |
| Run all tests | `pytest` |
| Run a single test | `pytest tests/test_timer.py::test_fires_after_threshold -x` |
| Lint | `ruff check .` |
| Format | `ruff format .` |
| Type check | `mypy src/turnbreak` |
| Build | `python -m build` |
| Run the server by hand | `turnbreak serve --port 7717 --foreground` |

---

## 3. Code style

Python 3.11 or newer. Standard library only in `src/turnbreak/core/`. Third-party packages are allowed in `src/turnbreak/sources/` and in tests.

This split exists because the core runs on every agent turn, inside a synchronous hook. A slow import is a slow turn.

Type hints on every public function. Dataclasses over dicts for anything crossing a module boundary.

**For any substantial piece of work, look for an established, well-tested library or API before writing it from scratch.** Hand-rolled code for a solved problem, like feed parsing or article extraction, is more likely to be buggy and harder to maintain than a maintained dependency. `sources/` and tests may take on third-party dependencies for this reason. Only implement from scratch once a real search turns up nothing suitable, and say why in the commit or ADR.

```python
@dataclass(frozen=True)
class Item:
    title: str
    locator: str  # URL, or absolute file path
    word_count: int
    source: Literal["curated", "folder"]
```

---

## 4. Repository conventions

|  |  |
|---|---|
| **Branch naming** | `feat/short-name`, `fix/short-name`, `docs/short-name` |
| **Commit message format** | Conventional Commits: `feat(server): reuse the open tab` |
| **PR requirements** | Tests and lint pass. One change per PR. Prose changes need the check in section 6. |

---

## 5. Boundaries

| Always do (no approval needed) | Ask first (needs review before proceeding) | Never do (hard stop) |
|---|---|---|
| Add tests with code | Add a runtime dependency to `core/` | Commit secrets, credentials, or `.env` files |
| Update `TASKS.md` when a task closes | Change the default port, threshold, or reading speed | Bind the server to anything but `127.0.0.1` |
| Run lint and tests before a PR | Change the on-disk config or state format | Send interests, item lists, or reading history off the machine |
| Follow section 6 for every prose file | Add a build step that needs Node | Write to stdout from a hook script (see section 7) |
| | | Prompt for input in the agent's own terminal (see section 7) |
| | | Publish anything (see below) |

The server is local only. It has no auth because it never listens beyond loopback. If a change makes it reachable from elsewhere, that change is wrong.

**This project is local until the maintainer says otherwise.** Do not create a GitHub repository, add a git remote, push, run `gh repo create`, or submit the project anywhere. Commit locally as often as you like.

This holds even when a task looks finished, even when the maintainer sounds pleased, and even when publishing seems like the obvious next step. Only an explicit instruction to push lifts it. The repository gets one first impression, and the maintainer wants to test the tool before anyone sees it.

---

## 6. Writing rules

These apply to every file a human reads: README, docs, CONTRIBUTING, SECURITY, issue and PR templates, CLI help, error messages, and code comments.

**Read `docs/writing-style.md` before writing any of them.** It holds the full rules, the banned-pattern list, and the verify loop.

The short version:

- Put the main point first.
- Short sentences. Short paragraphs.
- Plain words. Active voice.
- Say what the reader gains, not what the feature is.
- Replace vague claims with numbers or examples.
- Cut every word that carries no meaning.
- No em dashes.

**Verify before you commit.** Check the draft against `docs/writing-style.md`, fix what fails, then check again. Repeat until a full pass finds nothing. Then run the humanize pass in section 4 of that file.

Do not skip this because a change looks small.

---

## 7. Gotchas and environment quirks

### Hooks

**Hooks block the agent loop.** All four supported agents run hooks synchronously and wait for them to finish. `turnbreak start` must fork a detached process and return in milliseconds. Never do network or disk-heavy work inside the hook process.

**Hook scripts must not write to stdout.** Anything other than the final JSON object breaks parsing. Gemini CLI treats polluted stdout as a total parse failure. Use stderr for all debugging.

**One script serves all four agents.** Claude Code, Codex, Gemini CLI, and Copilot share the JSON-over-stdin contract and exit code semantics. Only the config file that registers the hook differs, and Gemini renames the turn events.

| Agent | Config file | Turn start | Turn end |
|---|---|---|---|
| Claude Code | `.claude/settings.json`, under a `hooks` key | `UserPromptSubmit` | `Stop` |
| Codex | `.codex/hooks.json`, event names at the root, no wrapper | `UserPromptSubmit` | `Stop` |
| Gemini CLI | `settings.json`, under a `hooks` object | `BeforeAgent` | `AfterAgent` |
| Copilot | Copilot hooks config | verify against current docs | verify against current docs |

Codex requires JSON output on `Stop`. Plain text is invalid there.

Gemini sets `CLAUDE_PROJECT_DIR` as a compatibility alias, so path handling can be shared.

`src/turnbreak/core/` knows nothing about any specific agent. Adding a fifth agent must not require touching core.

### Timing

**Elapsed time is measured, never estimated.** The watcher starts when the turn starts and stops when it ends. Delete any heuristic that guesses duration.

**The threshold is 90 seconds by default, not 5 minutes.** Most turns finish in under 3 minutes. A high threshold means the skill never fires and users remove it.

**Read time is arithmetic.** `word_count / words_per_minute`. Default 230 wpm, configurable. Never ask a model to estimate it.

### Display and control

**One tab, reused.** The first fire opens `http://127.0.0.1:7717`. Later items update that same page over the open connection. Opening a second tab is a bug.

**Never prompt in the agent's terminal.** The agent owns that terminal and is drawing to it. A prompt there corrupts the display and can swallow input meant for the agent. All three item actions live as buttons on the page. Users who want terminal control run `turnbreak watch` in a separate pane, which offers the same three actions.

**The item stays after the agent finishes.** The done signal changes the tab title, the favicon, and fires a notification. It does not clear the page or close the tab. A user mid-paragraph loses nothing.

### Item actions

Every item offers exactly three actions. Their effects differ and must not be collapsed.

| Action | Effect on this item | Effect on future items |
|---|---|---|
| **Read** | Marked read. Never shown again. | Recorded as a match. Feeds the next curated list. |
| **Skip** | Removed from the list. Never shown again. | Recorded as a miss. Feeds the next curated list. |
| **Keep reading** | Stays on screen. | Suppresses the next fire, including across turns, until cleared. |

**Keep reading persists across turns.** It holds the whole skill, not one item. If the next turn fires a new item over a held one, that is a bug.

### Sources

Two modes, one pipeline. Both produce `Item` objects and both use the same three actions.

- **`curated`**: interests produce a list of candidates, fetched from the web.
- **`folder`**: the user names a directory, and its files become the list.

**Candidate finding is pluggable.** Curated mode does not hardcode where candidates come from. A finder takes `interests.md` plus read and skip history, and returns candidate items. The user picks which finder to use in `config.toml`.

| Finder | Needs | Cost |
|---|---|---|
| `agent` | The host agent's CLI in headless mode | Tokens, billed to the user |
| `rss` | A feed list the user supplies | None |
| `search` | An API key | Per query |

The `agent` finder shells out to the installed agent: `claude -p`, `codex exec`, or `gemini -p`. It never runs inside a hook, because hooks block the turn and this call takes seconds. It runs when a list is built, which is a separate foreground command.

**The `agent` finder spends the user's tokens.** Say so before the first run and record the choice. Silently billing someone for background reading suggestions is the kind of thing that gets a tool uninstalled.

**When a list runs out, ask before rebuilding.** Offer to edit interests, then build a new list. Never rebuild silently, because a silent rebuild hides that the interests were wrong.

### File formats

**The page shell always stays.** Never navigate the tab to a file directly. The tab title, the favicon, the notification, and the three buttons all live in the shell. Handing the tab a raw PDF replaces the shell with the browser's own viewer and takes all four with it. Embed file content inside the shell instead.

**Every item needs a word count, whatever its format.** Read time is `word_count / words_per_minute`, and item selection depends on it. A format that renders but yields no word count breaks both. So a browser being able to display a format is not enough to support it.

| Format | Display | Word count |
|---|---|---|
| `.md`, `.txt` | Render in the shell | Direct |
| `.html` | Render in the shell | Strip tags, then count |
| `.pdf` | Embed in the shell | Needs a text extraction dependency in `sources/` |
| `.epub` | Not supported in v0.1.0 | Needs a reader library |


### Notifications

The done signal fires on Linux, macOS, and Windows through three layers, in order. Each degrades to the next.

1. Tab title prefix and favicon swap. Always works, needs no permission.
2. Web Notification API, if the user granted permission once.
3. A native command: `notify-send` on Linux, `osascript` on macOS, PowerShell toast on Windows.

Never make layer 1 depend on layers 2 or 3.

### Files

**Config lives at `~/.config/turnbreak/`.** `config.toml` for settings, `interests.md` for stated interests in plain text, `list.jsonl` for the current list with per-item status, `history.jsonl` for read and skipped items. Never write into the repo working tree at runtime.

**Tests must not open a browser or send a notification.** Set `TURNBREAK_NO_BROWSER=1` and `TURNBREAK_NO_NOTIFY=1`, which the test fixtures do.

---

## Related documents

- [`TASKS.md`](TASKS.md). The current work queue
- [`docs/writing-style.md`](docs/writing-style.md). Full writing rules and the verify loop
- [`docs/architecture.md`](docs/architecture.md). How the timer, server, sources, and adapters fit together
