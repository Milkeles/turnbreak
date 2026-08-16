# Architecture

|  |  |
|---|---|
| **Covers** | The shape of the system: timer, server, sources, actions, adapters |
| **Last reviewed** | 2026-08-16 |

---

## The shape

Turnbreak has four parts. A timer measures how long the agent's turn has been running. A server holds one browser tab open and pushes items to it. Two sources produce the items. Three actions let the reader dispose of each one.

A thin adapter sits between each of the four supported agents and this core. The adapter's whole job is calling `turnbreak start` when a turn begins and `turnbreak stop` when it ends. Nothing past that line knows which agent is running.

```
agent hook  ->  turnbreak start/stop  ->  timer  ->  server  ->  browser tab
                                            |
                                        sources (curated, folder)
```

---

## The timer

**Status: implemented.**

`turnbreak start --session-id ID` runs inside a hook, so it has to return in under 50 milliseconds. It writes turn state to `~/.config/turnbreak/state.json`, then forks a detached watcher process and returns. The watcher, not the hook, does the waiting.

The watcher polls real elapsed time against `threshold_seconds` from `config.toml`, default 90. It never estimates duration. When elapsed time crosses the threshold, it calls a fire hook, which starts the server if needed and pushes an item to the open tab.

`turnbreak stop --session-id ID` marks the turn ended in state, which cancels any watcher still polling for that session. It also pushes a done signal to `127.0.0.1:{port}`.

Session state holds a `hold_status` field for the "Keep reading" action. The watcher treats a held session as cancelled, so a held item is never overwritten by a later fire. Read and Skip clear the hold when they resolve an item.

---

## The server

**Status: implemented.**

An HTTP server bound to `127.0.0.1` only, serving one page and holding a push connection to it over Server-Sent Events. `turnbreak serve --port 7717` runs it in the foreground. The watcher's `on_fire` seam starts it as a detached process on first fire if it isn't already running, then opens the browser tab only when no tab is connected. Later items push over the same connection instead of opening a second tab.

The page itself has no real items to show yet, since the sources that produce them (P4) don't exist. It renders a waiting placeholder until P4 lands. The three action buttons post to `/action`, which resolves Read, Skip, and Keep reading against `list.jsonl` and session state. See `docs/adrs/0001-stdlib-server-and-native-os-notifications.md` for why the server and notifications use no third-party dependencies.

---

## The two sources

**Status: folder, the finder interface, all three finders, and switching between them are implemented. No command yet builds a list by calling the active finder (P4).**

`curated`: a finder (`agent`, `rss`, or `search`) turns `interests.md` plus read and skip history into candidate items. `folder`: the user names a directory and its files become the list. Both produce the same `Item` dataclass and feed the same three actions. Every `Item` carries its full body text, cached at list-build time, so a rebuild fetches or reads each item exactly once and firing an item never touches the network or disk again.

`turnbreak mode curated` and `turnbreak mode folder PATH` switch which source is active, writing to `config.toml`. `turnbreak finder NAME` switches which finder curated mode uses, defaulting to `agent` since that needs no setup beyond an agent the user already has.

A `Finder` is a `Protocol` with one method, `find(context) -> list[Item]`, so `agent`, `rss`, and `search` share no code beyond the `FinderContext` they receive. `build_context()` composes that context from `interests.md` and `history.jsonl`, split into past matches and misses. Every finder filters candidates against both lists before returning them, so a rebuild never resurfaces something already read or skipped.

The `agent` finder shells out to whichever of `claude -p`, `codex exec`, or `gemini -p` is installed, asking it for a JSON array of `{title, url}` candidates. It never asks the agent to estimate a word count, since read time must stay arithmetic. Instead it fetches each URL and extracts real article text with `trafilatura`, dropping any candidate that fails to extract rather than guessing, and caches that text on `Item.body` alongside the word count it derives from. Because it spends the user's tokens on every call, `confirm_token_spend()` gates the first run behind a prompt and records acceptance in `config.toml`, and nothing in `core/` or the hook path calls it. It only runs as an explicit foreground command, once one exists to call it (P4, tracked separately from the finder itself).

The `rss` finder reads a feed list the user maintains at `~/.config/turnbreak/feeds.txt`, one URL per line, and parses each with `feedparser`. Feed entries carry a title and link but no trustworthy word count either, so this finder extracts real article text with the same `trafilatura` step as the `agent` finder, dropping any entry that fails to extract and caching the extracted text on `Item.body`.

The `search` finder queries the Brave Search API with the text of `interests.md`, reading the key from `TURNBREAK_BRAVE_API_KEY`. It returns an empty list with no key set or no interests written, which is what "skip it if no key is set" means in practice: nothing breaks, that finder just contributes nothing to the list. Results go through the same `trafilatura` extraction step as the other two finders, caching body text the same way.

---

## The three actions

**Status: implemented.**

Read marks an item read in `list.jsonl` and records it as an interest match in `history.jsonl`. Skip removes the item from `list.jsonl` and records a miss. Keep reading sets `hold_status` to held, which the watcher checks before every fire, so the item stays on screen across turns until the reader picks Read or Skip. All three live as buttons in the page the server serves. Nothing prompts in the agent's terminal.

The page has no real items to show yet, since the sources that would populate `list.jsonl` (P4) don't exist. When a rebuild finds nothing pending, the page shows a placeholder instead of going blank. Asking whether to edit interests and rebuild waits on P4 and P5.

---

## The adapter boundary

Claude Code, Codex, Gemini CLI, and Copilot each register the same hook script under a different config file and different event names. The script reads JSON from stdin, writes nothing to stdout but its own final JSON object, and calls `turnbreak start` or `turnbreak stop`. `src/turnbreak/core/` has no knowledge of any of this. It only sees a session id and a timestamp.

See `AGENTS.md` section 7 for the exact config file and event name per agent.

---

## Related documents

- [`AGENTS.md`](../AGENTS.md). Commands, boundaries, and gotchas
- [`TASKS.md`](../TASKS.md). The build queue this architecture supports
