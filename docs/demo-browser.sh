#!/usr/bin/env bash
# Same scratch flow as demo.sh, but the real thing: a real browser tab
# opens with the item, and a real desktop notification fires when the
# turn ends. Meant to be screen-recorded, not terminal-recorded, since
# the browser tab is the point.
#
# Safe to run from a repo checkout: HOME is isolated, so it never touches
# your real ~/.config/turnbreak. Unlike demo.sh, this deliberately does
# NOT set TURNBREAK_NO_BROWSER or TURNBREAK_NO_NOTIFY, so start a screen
# recorder before running it.

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export HOME="${TURNBREAK_DEMO_HOME:-/tmp/turnbreak-demo}"
export PATH="$repo_root/.venv/bin:$PATH"

rm -rf "$HOME"
mkdir -p "$HOME/.config/turnbreak" "$HOME/notes"

cat > "$HOME/.config/turnbreak/config.toml" <<'EOF'
port = 7799
threshold_seconds = 5
EOF

cat > "$HOME/notes/ownership.md" <<'EOF'
# Ownership in Rust

Every value in Rust has a single owner, and when that owner goes out of
scope, the value is dropped. This one rule replaces both manual memory
management and a garbage collector. No malloc, no free, no pause while a
collector walks the heap deciding what is still reachable.

Passing a value to a function moves it by default. The caller loses
access, and the compiler enforces that at compile time: use the value
again after the move and the build fails, not the program at runtime.
Borrowing lets a function read or modify a value without taking
ownership, through a reference. The compiler checks that no reference
outlives the data it points to, and that a value is never mutated while
another part of the program is reading it.

This is what people mean when they say Rust has no data races by
construction. The borrow checker rejects the program before it runs,
rather than catching the race under load in production, or not catching
it at all and shipping a bug that only shows up on one customer's
machine under one specific timing.
EOF

cat > "$HOME/notes/http-caching.md" <<'EOF'
# HTTP caching, briefly

Cache-Control tells a client how long a response stays fresh, in
seconds, with max-age. ETag gives the client a fingerprint of the
response body, so a later request can ask "has this changed?" with
If-None-Match instead of downloading the whole thing again.

A server that supports both can answer most repeat requests with a
304 Not Modified and no body at all. The client keeps its cached copy.
This is why a well-configured static site can serve a returning
visitor almost nothing on their second load, and why a misconfigured
one re-sends the same megabyte of JavaScript on every single request.

The two headers solve different problems. max-age lets the client skip
the request entirely for a while, which is the cheapest possible cache
hit: no round trip at all. ETag matters once max-age has expired, or
was never set, because it lets the round trip happen without the
transfer. A request with If-None-Match still costs a connection and a
server-side lookup, just not the bandwidth.
EOF

turnbreak mode folder "$HOME/notes" >/dev/null

echo "Starting a turn. The reading tab should open in about 5 seconds."
turnbreak start --session-id demo

echo "Waiting for the tab and the item... click Read on the page when it shows up."
sleep 12

echo "Press Enter here once you've clicked Read, to end the turn and see the done notification."
read -r

turnbreak stop --session-id demo
echo "Turn ended. Check for the title/favicon change and the desktop notification."
sleep 3

turnbreak serve --port 7799 --stop >/dev/null 2>&1 || true
