---
name: turnbreak
description: Shows you something worth reading while your coding agent works, then notifies you when it's done. Use this skill to install turnbreak's turn-start/turn-stop hooks for Claude Code, Codex, Gemini CLI, or Copilot CLI, or to manage its interests and settings.
argument-hint: "install <agent>|onboard|interests|mode <curated|folder>|finder <agent|rss|search>"
disable-model-invocation: true
---

# turnbreak skill

turnbreak shows you something worth reading while your coding agent works,
then notifies you when it's done. It hooks into your agent's turn
start/turn end events to time this.

turnbreak isn't published to a package index. It's already installed on
this machine at a fixed location, invoked below as `{{TURNBREAK_COMMAND}}`.
Always use that exact invocation. Don't assume a bare `turnbreak` binary is
on PATH, and don't guess an install source for it.

## First, read ARGUMENTS

Whatever the user typed after `/turnbreak` appears below.

$ARGUMENTS

**If that's empty, do NOT run `install` or any other command.** Instead,
show this menu verbatim and stop. Do not take any action until the user
picks one:

> turnbreak can:
> 1. install: set up (or update) the turn-start/turn-stop hook for an agent
> 2. onboard: first-run setup for reading interests and finder token consent
> 3. interests: open the interests file to edit what you want to read
> 4. mode: switch between a curated list and a local folder of files
> 5. finder: switch which finder builds the curated list
>
> Which one?

**If ARGUMENTS names one of the commands below** (e.g. `interests`, `mode
folder ~/notes`, `onboard`, `finder rss`, `install claude`), skip the menu
entirely and just run that exact `{{TURNBREAK_COMMAND}} ...` invocation,
then report the result.

## Commands

- `{{TURNBREAK_COMMAND}} install <claude|codex|gemini|copilot>`: install or
  update the turn-start/turn-stop hook for that agent. Merges into existing
  config, never overwrites.
- `{{TURNBREAK_COMMAND}} onboard`: first-run setup. Collects reading
  interests, and if the agent finder is selected, confirms it's allowed to
  spend tokens.
- `{{TURNBREAK_COMMAND}} interests`: open the interests file in $EDITOR (or
  print its path if $EDITOR isn't set).
- `{{TURNBREAK_COMMAND}} mode <curated|folder> [path]`: switch between a
  curated reading list and a local folder of files.
- `{{TURNBREAK_COMMAND}} finder <agent|rss|search>`: switch which finder
  builds the curated list.

## Behavior

- The hook reads JSON from stdin and maps start/end events to
  `turnbreak start` and `turnbreak stop`.
- The hook writes exactly one JSON object to stdout and nothing else.
- The hook must not run network or long-running tasks. It forks a watcher.
