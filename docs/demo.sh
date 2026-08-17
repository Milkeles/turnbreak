#!/usr/bin/env bash
# Runs turnbreak end to end in a scratch environment: install, point at a
# folder, a turn runs long enough to fire, the item shows up, the turn
# ends. Prints a condensed view (a spinner, then a boxed excerpt) rather
# than dumping the full article, so the recording stays short.
#
# Safe to run from a repo checkout: it isolates HOME so it never touches
# your real ~/.config/turnbreak, and TURNBREAK_NO_BROWSER/NO_NOTIFY keep it
# from opening a tab or firing a desktop notification.
#
# To turn this into an animated recording, run it through a recorder that
# captures a real pty, from a real terminal (this script alone won't work
# over a piped, non-tty shell):
#   pip install termtosvg
#   termtosvg docs/assets/demo.svg -c "bash docs/demo.sh" -g 64x18

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
all, while still letting the browser cache it for that one user.
EOF

say() { printf '\033[32m$\033[0m %s\n' "$1"; sleep 0.3; }
note() { printf '\033[2m%s\033[0m\n' "$1"; sleep 0.3; }

spinner() {
  local frames='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
  local msg="$1" secs="$2" i=0
  local end=$((SECONDS + secs))
  while [ "$SECONDS" -lt "$end" ]; do
    i=$(( (i + 1) % ${#frames} ))
    printf '\r\033[36m%s\033[0m %s' "${frames:$i:1}" "$msg"
    sleep 0.1
  done
  printf '\r\033[32m✓\033[0m %s\n' "$msg"
}

# Renders piped lines as a bordered card. The first line becomes a bold
# header, separated from the rest by a rule.
box() {
  local width=58
  local border; border=$(printf '─%.0s' $(seq 1 "$width"))
  printf '┌%s┐\n' "$border"
  # Pad by character count, not printf's %-*s field width, which counts
  # bytes: a multi-byte glyph like the em dash in turnbreak's own output
  # otherwise throws off the right border by a column or two.
  local first=1 pad
  while IFS= read -r line; do
    pad=$(( width - 2 - ${#line} ))
    [ "$pad" -lt 0 ] && pad=0
    if [ "$first" = 1 ]; then
      printf '│ \033[1m%s\033[0m%*s │\n' "$line" "$pad" ""
      printf '├%s┤\n' "$border"
      first=0
    else
      printf '│ %s%*s │\n' "$line" "$pad" ""
    fi
  done
  printf '└%s┘\n' "$border"
}

clear
say "turnbreak install claude"
turnbreak install claude >/dev/null
say "turnbreak mode folder ~/notes"
turnbreak mode folder "$HOME/notes" >/dev/null
echo

turnbreak start --session-id demo >/dev/null
spinner "agent working..." 5
echo

item_output=$(turnbreak watch --once)
title_line=$(printf '%s' "$item_output" | head -n1)
body=$(printf '%s' "$item_output" | tail -n +2 | grep -v '^#' | sed '/^$/d' | fold -s -w 56 | head -n 5)
{
  printf '%s\n' "$title_line"
  printf '%s\n' "$body"
  printf '…\n'
} | box
echo

turnbreak stop --session-id demo >/dev/null
note "turn ended · tab title and favicon updated"

turnbreak serve --port 7799 --stop >/dev/null 2>&1 || true
