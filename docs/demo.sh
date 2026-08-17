#!/usr/bin/env bash
# Runs turnbreak end to end in a scratch environment and prints what a
# folder-mode session looks like: install, point at a folder, a turn runs
# long enough to fire, watch shows the item, the turn ends.
#
# Safe to run from a repo checkout: it isolates HOME so it never touches
# your real ~/.config/turnbreak, and TURNBREAK_NO_BROWSER/NO_NOTIFY keep it
# from opening a tab or firing a desktop notification.
#
# To turn this into the README's terminal recording, run it through a
# recorder that captures a real pty, from a real terminal (this script
# alone won't work over a piped, non-tty shell):
#   pip install termtosvg
#   termtosvg docs/assets/demo.svg -c "bash docs/demo.sh" -g 90x24

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export HOME="${TURNBREAK_DEMO_HOME:-/tmp/turnbreak-demo}"
export TURNBREAK_NO_BROWSER=1
export TURNBREAK_NO_NOTIFY=1
export PATH="$repo_root/.venv/bin:$PATH"

rm -rf "$HOME"
mkdir -p "$HOME/.config/turnbreak" "$HOME/notes"

cat > "$HOME/.config/turnbreak/config.toml" <<'EOF'
port = 7799
threshold_seconds = 3
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

Static assets versioned by filename, like app.a3f1c2.js, sidestep the
whole question. The content behind that URL never changes, so you can
set an effectively infinite max-age and never worry about staleness.
The versioning happens at build time: a new deploy produces a new
filename, and the HTML that references it changes too. The HTML itself
usually gets a short max-age or none at all, since it is the one file
that has to be fresh on every visit to pick up the new asset names.

Private data complicates this. Cache-Control: private tells shared
caches, like a CDN or a corporate proxy, not to store the response at
all, while still letting the browser cache it for that one user. Get
this wrong in the other direction, no-store on something that could
safely be shared, and every user pays the full cost of a request that
a CDN could have answered from an edge node a few milliseconds away.

Most caching bugs are not about the algorithm. They are about a header
set once, for one environment, that quietly stops matching reality
after the app changes shape underneath it. A cache that is wrong by
being too aggressive serves stale content silently, which is worse
than serving nothing, because nothing fails loudly and stale content
just looks like a bug report nobody can reproduce.

None of this needs a library. It is a handful of response headers, set
correctly once per resource type, and left alone. The hard part is
almost never the mechanism. It is remembering that the header exists
at all when the resource it describes changes shape.
EOF

say() { printf '\033[32m$\033[0m %s\n' "$1"; sleep 0.4; }
note() { printf '\033[2m%s\033[0m\n' "$1"; sleep 0.4; }

clear
say "turnbreak install claude"
turnbreak install claude >/dev/null
sleep 1

say "turnbreak mode folder ~/notes"
turnbreak mode folder "$HOME/notes" >/dev/null
sleep 1
echo
note "# the agent starts a long task..."
turnbreak start --session-id demo >/dev/null
sleep 4
echo
say "turnbreak watch"
turnbreak watch --once
sleep 2
echo
note "# ...and the agent finishes"
turnbreak stop --session-id demo >/dev/null
sleep 1
echo

turnbreak serve --port 7799 --stop >/dev/null 2>&1 || true
