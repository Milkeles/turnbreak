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

The watcher polls real elapsed time against `threshold_seconds` from `config.toml`, default 90. It never estimates duration. When elapsed time crosses the threshold, it calls a fire hook. Today that hook only logs to stderr, because the server that would receive a real item doesn't exist yet. That call site is where P2 connects.

`turnbreak stop --session-id ID` marks the turn ended in state, which cancels any watcher still polling for that session. It also tries to push a done signal to `127.0.0.1:{port}`. Until the server exists, that push fails silently and the watcher's poll loop is the only thing `stop` actually needs to do.

Session state holds a `hold_status` field for the "Keep reading" action. Nothing sets it yet. It exists now so the state file's shape doesn't change once P3 starts writing to it.

---

## The server

**Status: implemented.**

An HTTP server bound to `127.0.0.1` only, serving one page and holding a push connection to it over Server-Sent Events. `turnbreak serve --port 7717` runs it in the foreground. The watcher's `on_fire` seam starts it as a detached process on first fire if it isn't already running, then opens the browser tab only when no tab is connected. Later items push over the same connection instead of opening a second tab.

The page itself has no real items to show yet, since the sources that produce them (P4) don't exist. It renders a waiting placeholder until P3 and P4 land. The three action buttons post to `/action`, which is a stub today; see `docs/adrs/0001-stdlib-server-and-native-os-notifications.md` for why the server and notifications use no third-party dependencies.

---

## The two sources

**Status: not yet implemented (P4).**

`curated`: a finder (`agent`, `rss`, or `search`) turns `interests.md` plus read and skip history into candidate items. `folder`: the user names a directory and its files become the list. Both produce the same `Item` dataclass and feed the same three actions.

---

## The three actions

**Status: not yet implemented (P3).**

Read marks an item read and records it as an interest match. Skip removes it and records a miss. Keep reading holds the item on screen and suppresses the next fire, across turns, until the reader picks Read or Skip. All three live as buttons in the page the server serves; nothing prompts in the agent's terminal.

---

## The adapter boundary

Claude Code, Codex, Gemini CLI, and Copilot each register the same hook script under a different config file and different event names. The script reads JSON from stdin, writes nothing to stdout but its own final JSON object, and calls `turnbreak start` or `turnbreak stop`. `src/turnbreak/core/` has no knowledge of any of this. It only sees a session id and a timestamp.

See `AGENTS.md` section 7 for the exact config file and event name per agent.

---

## Related documents

- [`AGENTS.md`](../AGENTS.md). Commands, boundaries, and gotchas
- [`TASKS.md`](../TASKS.md). The build queue this architecture supports
