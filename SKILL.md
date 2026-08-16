turnbreak skill

This folder contains adapter templates and a universal hook script that
lets external agents call the local turnbreak CLI on turn start and end.

Installation

1. Copy the appropriate adapter template into your agent's config folder:
   turnbreak install claude ~/.claude/settings.json
2. Verify the `script` path points to `scripts/turnbreak-hook.py` and is
   executable.
3. Restart or reload your agent as required.

Behavior

- The hook reads JSON from stdin and maps start/end events to
  `turnbreak start` and `turnbreak stop`.
- The hook writes exactly one JSON object to stdout and nothing else.
- The hook must not run network or long-running tasks; it forks a watcher.
