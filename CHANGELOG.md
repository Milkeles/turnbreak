# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added

### Changed

### Fixed

---

## [0.1.0] - 2026-08-17

### Added

- Turn-boundary hooks for Claude Code, Codex, Gemini CLI, and Copilot CLI, installed with `turnbreak install <agent>`.
- A local reading server bound to `127.0.0.1` that opens one browser tab and keeps it updated over Server-Sent Events.
- Curated mode, pulling candidates from an agent CLI, an RSS feed, or a web search, gated on a configurable read-time range.
- Folder mode, reading directly from a local folder of Markdown, text, HTML, or PDF files.
- Read, Next, and Previous actions on the page, plus a terminal alternative via `turnbreak watch`.
- Native desktop notifications on Linux, macOS, and Windows when a turn ends.
- `turnbreak onboard` for first-run interest collection and agent-finder token-spend consent.
