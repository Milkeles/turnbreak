# ADR-0001: Use the standard library for the server and native OS commands for notifications

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-08-16 |
| **Deciders** | Hristo Hristov (maintainer), via agent-assisted build |

---

## Context and problem statement

P2 needs an HTTP server that binds to `127.0.0.1`, holds one page open, and pushes items and a done signal to it. It also needs a notification that reaches the user outside the browser tab, on Linux, macOS, and Windows.

`AGENTS.md` restricts `src/turnbreak/core/` to the standard library, because that code runs inside every synchronous agent hook and a slow import stalls the turn. The server and the notification call are not on that hook path. They run in a detached process. That leaves room to add a dependency here if one earns its place.

---

## Decision drivers

- No new operational surface: one CLI tool a user installs with `pip install`, not a service with its own dependency tree to patch.
- The push mechanism only needs to send data from server to page. It does not need two-way, low-latency messaging.
- The notification only needs to reach the OS's own notification system. It does not need click callbacks, action buttons, or delivery guarantees.

---

## Considered options

1. Standard library `http.server` for the server, with Server-Sent Events for the push; `notify-send` / `osascript` / PowerShell for notifications.
2. A web framework (Flask, FastAPI + uvicorn) for the server, with a matching SSE helper.
3. A cross-platform notification library (`desktop-notifier`, `notify-py`, or `plyer`).

---

## Decision

We will use `http.server.ThreadingHTTPServer` for the server and Server-Sent Events for the push. For notifications, we will shell out to `notify-send`, `osascript`, and PowerShell's toast API. All of it comes from the standard library.

Server-Sent Events need nothing beyond a `text/event-stream` response and a socket held open, which `http.server` already provides. A search turned up no dependency-free SSE library. The available ones are thin wrappers around Flask or FastAPI, which would pull in a web framework for one local page.

For notifications, `desktop-notifier` and `notify-py` exist, but both add dependencies (`jeepney` or `loguru` on Linux, WinRT bindings on Windows) to reach the same commands this project can call directly.

---

## Consequences

**Positive**

- Zero new runtime dependencies. `pip install turnbreak` stays fast and has nothing to conflict with.
- The server is about 130 lines and easy to read end to end, instead of hidden behind a framework's request-handling internals.

**Negative**

- We own the SSE wire format by hand: heartbeats, reconnection, and header correctness are our bug to fix, not a library's.
- The Windows toast path uses an inline PowerShell script calling WinRT APIs. It has not been tested on a real Windows machine.

**Follow-on work**

- Verify the Windows notification path on real Windows once CI covers that platform (tracked in `TASKS.md` P10).

---

## Confirmation

`tests/test_core_is_stdlib_only.py` parses every module under `src/turnbreak/core/` and fails if any imports a top-level module outside the standard library.

---

## More information

Revisit if the push channel needs to carry more than server-to-page events, for example if actions need acknowledgment beyond a plain HTTP response.

---

## Related documents

- [`AGENTS.md`](../../AGENTS.md). The `core/` stdlib-only rule this decision operates under
- [`docs/architecture.md`](../architecture.md). Where the server fits in the overall shape
