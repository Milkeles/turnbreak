# Architecture

|  |  |
|---|---|
| **Covers** | The shape of the system: timer, server, sources, actions, adapters |
| **Last reviewed** | 2026-08-17 |

---

## The shape

Turnbreak has four parts. A timer measures how long the agent's turn has been running. A server holds one browser tab open and pushes items to it. Two sources produce the items. Three actions let the reader move through them.

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

The watcher polls real elapsed time against `threshold_seconds` from `config.toml`, default 90. It never estimates duration. When elapsed time crosses the threshold, it calls a fire hook, which calls `ensure_tab_open` and pushes an item to the open tab.

Before that polling even starts, the watcher also calls `ensure_tab_open` on its own, which starts the server if needed and opens the reading tab if no tab is connected. This runs on every turn, not only turns that cross the threshold. The tab reappears even for a short turn, and even if the reader closed it earlier.

`turnbreak stop --session-id ID` marks the turn ended in state, which cancels any watcher still polling for that session. It also pushes a done signal to `127.0.0.1:{port}`.

Session state holds a `shown_locator` field: the locator of the last item pushed to this session. Before pushing, `fire.py` compares the item it's about to select against `shown_locator`. If they match, the item is still pending and was already shown, so nothing new is pushed. The reader just keeps reading. Read removes the item from the pending list, so the next selection naturally differs and a new item gets pushed. Next and Previous only browse. They never touch the pending list. There is no separate hold to set or clear. Doing nothing is the default.

---

## The server

**Status: implemented.**

An HTTP server bound to `127.0.0.1` only, serving one page and holding a push connection to it over Server-Sent Events. `turnbreak serve` starts it as a detached background process (unless one is already running), opens the reading tab, and prints its URL. `--foreground` runs it attached to the current terminal instead, and `--stop` stops a server started either way.

`fire.py`'s `ensure_tab_open` starts the server the same way if it isn't already running, then opens the browser tab only when no tab is connected. The watcher calls it at the start of every turn, and `on_fire` calls it again right before pushing an item, so a tab the reader closed in between still comes back. `client_count` checks real live connections before either call, so a tab that's already open is left alone. Both paths go through `server_control.py`, so a server started by a turn and one started by `turnbreak serve` share the same PID file and can stop each other. Later items push over the same connection instead of opening a second tab.

The page renders a waiting placeholder until the first item arrives. It then calls `GET /current` to check whether something is already showing, so that placeholder doesn't sit there needlessly.

The broker itself holds no history. It only fans a broadcast out to whoever is connected at that instant. So `/current` is reconstructed from `state.json`'s `shown_locator` plus a lookup into `list.jsonl`, the same source of truth `fire.py` writes to. This is what lets a reload, a new tab, or a reconnect after the server restarted pick back up on the same item instead of going blank until the next turn fires. `item_payload()` in `items.py` shapes the item the same way for both this snapshot and the live `push_item_signal` push, so the two can't drift apart on what fields the page expects.

Once the list runs dry (nothing pending, and a refill attempt finds nothing new), `fire.py` pushes an `end` event over the same connection instead of leaving the last item on screen with no explanation. The page then shows a message pointing at `turnbreak interests`, so an empty list never rebuilds silently.

The three action buttons post to `/action`. Read resolves the item against `list.jsonl` and `history.jsonl`. Next and Previous only move browse position, and never touch either file. See `docs/adrs/0001-stdlib-server-and-native-os-notifications.md` for why the server and notifications use no third-party dependencies.

---

## The two sources

**Status: folder, the finder interface, all three finders, and switching between them are implemented. No command yet builds a list by calling the active finder (P4).**

`curated`: a finder (`agent`, `rss`, or `search`) turns `interests.md` plus read and skip history into candidate items. `folder`: the user names a directory and its files become the list. Both produce the same `Item` dataclass and feed the same three actions. Every `Item` carries its full body text, cached at list-build time, so a rebuild fetches or reads each item exactly once and firing an item never touches the network or disk again. `select_item()` in `items.py` prefers items inside `target_read_minutes`, then anything within twice that upper bound, then any remaining pending item regardless of length rather than showing nothing. That last tier exists for folder mode: a folder of whole PDFs (book chapters, papers) routinely has nothing under the twice-the-bound cutoff, and turnbreak would otherwise report the list empty despite files sitting right there.

`turnbreak mode curated` and `turnbreak mode folder PATH` switch which source is active, writing to `config.toml`. `turnbreak finder NAME` switches which finder curated mode uses, defaulting to `agent` since that needs no setup beyond an agent the user already has.

A `Finder` is a `Protocol` with one method, `find(context) -> list[Item]`, so `agent`, `rss`, and `search` share no code beyond the `FinderContext` they receive. `build_context()` composes that context from `interests.md` and `history.jsonl`, split into past matches and misses. Every finder filters candidates against both lists before returning them, so a rebuild never resurfaces something already read or skipped.

The `agent` finder shells out to whichever of `claude -p`, `codex exec`, or `gemini -p` is installed, asking it for a JSON array of `{title, url}` candidates. It never asks the agent to estimate a word count, since read time must stay arithmetic. Instead it fetches each URL and extracts real article text with `trafilatura`, dropping any candidate that fails to extract rather than guessing, and caches that text on `Item.body` alongside the word count it derives from. Because it spends the user's tokens on every call, `confirm_token_spend()` gates the first run behind a prompt and records acceptance in `config.toml`, and nothing in `core/` or the hook path calls it. It only runs as an explicit foreground command, once one exists to call it (P4, tracked separately from the finder itself).

The `rss` finder reads a feed list the user maintains at `~/.config/turnbreak/feeds.txt`, one URL per line, and parses each with `feedparser`. Feed entries carry a title and link but no trustworthy word count either, so this finder extracts real article text with the same `trafilatura` step as the `agent` finder, dropping any entry that fails to extract and caching the extracted text on `Item.body`.

The `search` finder queries the Brave Search API with the text of `interests.md`, reading the key from `TURNBREAK_BRAVE_API_KEY`. It returns an empty list with no key set or no interests written, which is what "skip it if no key is set" means in practice: nothing breaks, that finder just contributes nothing to the list. Results go through the same `trafilatura` extraction step as the other two finders, caching body text the same way.

---

## The three actions

**Status: implemented.**

Read marks an item read in `list.jsonl` and records it as an interest match in `history.jsonl`. Next and Previous browse without touching either file. A `BrowseHistory` in `server.py` tracks position per session, so Previous can step back to whatever Next moved past. Doing nothing is the default: the item stays on screen across turns, since `fire.py` never replaces a pending item that's already been shown to the session. All three actions live as buttons in the page the server serves. Nothing prompts in the agent's terminal.

`turnbreak watch`, the terminal alternative, still offers its own read and skip commands instead of this three-action model. See the note in `TASKS.md`'s P10 section.

See "The server" above for what happens when the list runs out.

---

## The adapter boundary

Claude Code, Codex, Gemini CLI, and Copilot each register the same hook script under a different config file and different event names. The script reads JSON from stdin, writes nothing to stdout but its own final JSON object, and calls `turnbreak start` or `turnbreak stop`. `src/turnbreak/core/` has no knowledge of any of this. It only sees a session id and a timestamp.

See `AGENTS.md` section 7 for the exact config file and event name per agent.

---

## Related documents

- [`AGENTS.md`](../AGENTS.md). Commands, boundaries, and gotchas
- [`TASKS.md`](../TASKS.md). The build queue this architecture supports
