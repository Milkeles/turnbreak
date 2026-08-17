# turnbreak

Shows you something worth reading while your coding agent works.

<!-- TODO before publishing: replace with the screen capture from P8 -->
<!-- Primary demo: the agent starts working, an item appears in the browser tab, the done notification fires. Belongs here, above the fold, before any install step. See docs/positioning.md for the recording spec. -->

## Why

An agent turn on a real task runs one to five minutes. That's too short to switch to something else and too long to just wait. Turnbreak points that time at something you already meant to read.

It watches how long the current turn has been running. Past a threshold (90 seconds by default), it opens one browser tab and puts something in it: an article pulled from your stated interests, an RSS feed, a search, or files from a folder you name. You read it while the agent works. When you click Read, or the turn ends, it gets out of the way.

The server binds to `127.0.0.1` only. Your interests, your reading history, and everything it shows you stay on disk. See [`SECURITY.md`](SECURITY.md) for the exact guarantee.

## Install

```bash
pip install "turnbreak[sources]"
turnbreak install claude   # or codex, gemini, copilot
turnbreak onboard          # write your interests, one per line
```

`turnbreak install` registers the hook for the agent you name. It only needs to run once per agent. `turnbreak onboard` writes `~/.config/turnbreak/interests.md` and, if you're using the agent-driven finder, asks you to confirm it can spend tokens fetching candidates.

The `sources` extra pulls in the article extraction and feed parsing that curated mode, the default, needs to turn a URL into real reading content. Skip it with a plain `pip install turnbreak` only if you plan to run `turnbreak mode folder PATH` against markdown or text files and nothing else.

Start your agent and work as usual. A turn that runs past the threshold opens the reading tab on its own.

## Usage

| Command | What it does |
|---|---|
| `turnbreak install <claude\|codex\|gemini\|copilot>` | Register the turn-start/turn-stop hook for an agent |
| `turnbreak onboard` | Write your interests file, and confirm token spend if needed |
| `turnbreak mode curated` / `turnbreak mode folder PATH` | Read from your interests, or from a folder of files instead |
| `turnbreak finder agent\|rss\|search` | Pick how curated mode finds candidates |
| `turnbreak watch` | A terminal view of the same list, for working without the browser tab |
| `turnbreak serve --port 7717` | Start the server and open the tab by hand |

Read, Next, and Previous are the only actions. Read marks the item done and moves on. Next and Previous just browse, without marking anything read. Doing neither leaves the item on screen. That's the default, not a separate command.

## Supported formats

- Markdown (`.md`) and plain text (`.txt`): rendered in the shell and counted directly.
- HTML (`.html`): stripped of markup and rendered. Word count uses `trafilatura` extraction.
- PDF (`.pdf`): embedded into the page as base64 bytes, so the page, buttons, title, and favicon stay under turnbreak's control. `pypdf` extracts text for a read-time estimate. If extraction fails, the PDF still shows, just without an estimate.

Not supported yet: EPUB. Browsers have no native EPUB renderer, and turnbreak doesn't ship one in v0.1.0.

## Supported agents

`turnbreak install` covers Claude Code, Codex, Gemini CLI, and Copilot CLI. Claude Code and Copilot CLI are what the maintainer runs day to day, so those two are tested against a real account. Codex and Gemini CLI support is built against their documented hook formats but not exercised the same way. Please report anything that breaks on either.

## Configuration

`~/.config/turnbreak/config.toml`, written on first run:

| Setting | Default | What it does |
|---|---|---|
| `threshold_seconds` | `90` | How long a turn runs before the tab gets an item |
| `port` | `7717` | The loopback port the server binds to |
| `words_per_minute` | `230` | Used to estimate read time, never to guess it |
| `target_read_minutes` | `2, 4` | The reading-time range turnbreak prefers when picking the next item |

## How it works

[`docs/architecture.md`](docs/architecture.md) covers the timer, the server, the two sources, and the adapter boundary in full. In short: a detached watcher process measures real elapsed time per turn, never a prediction, and pushes to a page over Server-Sent Events so the tab updates without a refresh.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Found a security issue instead? See [`SECURITY.md`](SECURITY.md).

## License

MIT. See [`LICENSE`](LICENSE).
