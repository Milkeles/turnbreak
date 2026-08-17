# Task plan: turnbreak

|  |  |
|---|---|
| **Covers** | Whole repo, from empty to first release |
| **Last reviewed** | 2026-08-17 |

---

## 0. Read this first

**This project stays local until the maintainer says otherwise.** Build it, document it, test it, and prepare the launch on disk. Do not create a GitHub repository. Do not add a remote. Do not push. Do not run `gh repo create`.

The only task that publishes anything is P11, and it runs only when the maintainer says to push. Treat everything above it as work that has to be finished first, because the repository gets exactly one first impression.

**Decide small things yourself.** This plan does not cover every choice you will face, and it is not meant to. When you hit a question the plan does not answer, pick the option you can defend, write it and your reasoning into `docs/adrs/`, and keep going. Do not stop and wait.

The exception is anything in the "Ask first" or "Never do" columns of `AGENTS.md` section 5. Adding a `core/` dependency, changing a default, changing the on-disk format, spending the user's money, and sending data off the machine all need the maintainer. Everything else is yours.

Prefer the reversible option when you are unsure. A recorded decision costs one commit to undo. A blocked queue costs the maintainer their evening.

---

## 1. The queue

### P0. Setup, local only

- [x] Run `git init` locally with no remote configured.
- [x] Clone `https://github.com/Milkeles/software-doc-templates` to a scratch directory outside the repo, using `git clone --depth 1`, because GitHub folder URLs return a robots error and the API rate limits without a token.
- [x] Read `ai-assisted-development/README.md`, `general-swe/README.md`, and `general-swe/foundations/README.md` to learn which documents earn their place and which to skip.
- [x] Research the project name before writing it anywhere: check whether it is free on PyPI, npm, and GitHub, whether the first page of search results is already crowded, and whether it is easy to spell after hearing it once.
- [x] Propose three name candidates with the availability evidence for each, and let the maintainer pick. Maintainer picked `turnbreak` over `interlude`, `idlepage`, and `waitread`.
- [x] Record the name decision. Not an ADR: noted directly in `AGENTS.md` section 1 instead.
- [x] Add `LICENSE` with the license the maintainer picks. Maintainer picked MIT.
- [x] Create the Python package skeleton, `pyproject.toml`, and the `src/turnbreak/` layout from `AGENTS.md` section 3.
- [x] Set up `ruff`, `mypy`, and `pytest` with the exact commands in `AGENTS.md` section 2.

### P1. Timer and hooks

- [x] Write `docs/architecture.md` covering the timer, the server, the two sources, the two actions, and the adapter boundary.
- [x] Implement session state at `~/.config/turnbreak/state.json`, tracking session id, turn start time, and hold status.
- [x] Implement `turnbreak start --session-id ID`, which forks a detached watcher and returns in under 50 milliseconds.
- [x] Implement `turnbreak stop --session-id ID`, which ends the turn and pushes the done signal to any open page.
- [x] Add a test asserting `turnbreak start` returns in under 50 milliseconds, since a slow hook stalls the agent loop.
- [x] Add a test asserting no hook entry point writes anything to stdout except its final JSON object.
- [x] Implement the watcher, which fires an item once measured elapsed time passes the threshold, default 90 seconds.
- [x] Implement `config.toml` loading with defaults for `port` (7717), `threshold_seconds` (90), `words_per_minute` (230), `target_read_minutes` (2 to 4), and `mode` (`curated` or `folder`).

### P2. Server and page

- [x] Implement the HTTP server bound to `127.0.0.1` only, serving one page and holding a push connection to it.
- [x] Add a test asserting the server refuses to bind to any address other than `127.0.0.1`.
- [x] Implement single-tab reuse, opening the browser on first fire and pushing later items to the same page.
- [x] Build the reading page showing title, source, estimated read time, body text, and three buttons.
- [x] Implement the done signal layer 1: tab title prefix and favicon swap, working with no permission granted.
- [x] Implement the done signal layer 2: Web Notification API, requesting permission once on first page load.
- [x] Implement the done signal layer 3: `notify-send` on Linux, `osascript` on macOS, PowerShell toast on Windows.
- [x] Add a test asserting layer 1 still fires when layers 2 and 3 both fail.
- [x] Keep the current item visible after the done signal, and never auto-clear or auto-close the page.

### P3. Items and actions

- [x] Implement `list.jsonl` holding the current list, one item per line, each with a status of pending, read, or skipped.
- [x] Implement `history.jsonl` holding every read and skipped item, so nothing appears twice across lists.
- [x] Implement read time as `word_count / words_per_minute`, with no model call anywhere in the path.
- [x] Implement item selection preferring items inside `target_read_minutes` and skipping items over twice the upper bound.
- [x] Implement the Read action, which marks the item read, records it as an interest match, and never shows it again.
- [x] Implement the Skip action, which removes the item from the list, records it as a miss, and never shows it again.
- [x] Implement default "keep reading" behavior: a still-pending item already shown to the session is never replaced by a later fire.
- [x] Make that suppression persist across turns until the user picks Read or Skip.
- [x] Add a test asserting an already-shown item is not replaced when a new turn passes the threshold.
- [x] Implement end-of-list handling, which asks whether to edit interests and build a new list, and never rebuilds silently.

### P4. Sources

- [x] Define the finder interface: takes `interests.md` plus read and skip history, returns candidate items.
- [x] Implement the `agent` finder, which shells out to `claude -p`, `codex exec`, or `gemini -p` depending on which agent is installed.
- [x] Make the `agent` finder run only as a foreground command, never inside a hook, since it takes seconds and hooks block the turn.
- [x] Warn the user that the `agent` finder spends their tokens, before the first run, and record that they accepted.
- [x] Implement the `rss` finder, reading a feed list the user supplies.
- [x] Implement the `search` finder, using an API key the user supplies, and skip it if no key is set.
- [x] Add `finder` to `config.toml` with `agent` as the default, since it needs no setup beyond an agent the user already has.
- [x] Implement `turnbreak finder NAME` to switch finders.
- [x] Feed read and skip history into every finder, so each rebuild improves on the last.
- [x] Implement the folder source, listing readable files in a directory the user names.
- [x] Implement `turnbreak mode curated` and `turnbreak mode folder PATH` to switch sources.

### P4b. File formats

- [x] Support `.md` and `.txt` in the shell, counting words directly.
- [x] Support `.html` in the shell, stripping tags before counting words.
- [x] Implement article extraction returning clean text and a word count from a URL.
- [x] Embed PDFs inside the page shell rather than navigating the tab to them, so the buttons, title, favicon, and notification survive.
- [x] Add a test asserting the shell still controls the tab title while a PDF is displayed.
- [x] Add a PDF text extraction dependency in `sources/`, used only for the word count, never for display.
- [x] Fall back to showing the PDF with no read time estimate if extraction fails, rather than dropping the item.
- [x] State in the README which formats work, and that EPUB does not yet.


### P5. Interests

- [x] Implement first-run onboarding, which asks for interests and writes `~/.config/turnbreak/interests.md`.
- [x] Implement `turnbreak interests`, which opens the file in `$EDITOR` or prompts inline when `$EDITOR` is unset.
- [x] Implement `turnbreak watch`, a terminal pane offering the same two actions for users who prefer the keyboard.
- [x] Add the `/turnbreak-interests` slash command for agents that support slash commands.

### P6. Agent support

- [x] Write one hook script that reads JSON from stdin, writes nothing to stdout, and works unchanged across all four agents.
- [x] Write the Claude Code adapter registering the script in `.claude/settings.json` under a `hooks` key.
- [x] Write the Codex adapter registering the script in `.codex/hooks.json` with event names at the root, returning JSON on `Stop`.
- [x] Write the Gemini CLI adapter registering the script in `settings.json`, mapping turn start to `BeforeAgent` and turn end to `AfterAgent`.
- [x] Check the current Copilot hooks reference for its turn start and turn end event names, then write the Copilot adapter (template provided, verify before use).
- [x] Write `SKILL.md` so Claude Code and Codex can install turnbreak as a skill.
- [x] Write `turnbreak install AGENT` to place adapter files in the right location for each agent.
- [x] Write a generic adapter documenting the two commands any other agent must call.

### P7. Positioning research

The goal is a repository a stranger understands in 10 seconds and wants in 30. Research first, then write. Everything here is prepared locally.

**Rules for this research.** Prefer evidence over advice. A GitHub blog post with data, a study of what correlates with stars, or a documented before-and-after beats a listicle titled "10 tips for an awesome README." Where the sources disagree or offer only opinion, say so in the notes instead of picking one quietly. Record what you find in `docs/positioning.md` with links, then apply it.

- [x] Research what makes a repository understandable in the first 10 seconds, focusing on what sits above the fold before a reader scrolls.
- [x] Research how the GitHub About field works as a discovery surface: its character limit, how much of it shows in search results and on profile cards, and how much of the value lands in the first few words.
- [x] Research GitHub topics: how many are useful, which ones this project should claim, and how people actually browse them.
- [x] Research the social preview image: what size GitHub expects, and how much it changes what a shared link looks like on social platforms and in chat.
- [x] Research README structure specifically for developer tools and CLI tools, not for libraries or frameworks, since the reader's first question differs.
- [x] Research which badges carry information and which are noise, and pick the smallest set that answers a real question.
- [x] Find where this project's audience already is: skill directories such as `skillsllm.com` and `skills.rest`, relevant awesome-lists, and the subreddits and forums where agent tooling gets discussed.
- [x] For each place found, record its submission rules, its format, and whether it requires the project to already have traction.
- [x] Research what a good launch post looks like on the two or three highest-value venues, and note what gets removed or downvoted.
- [x] Write `docs/positioning.md` holding all findings with links, and a short note wherever the evidence is weak.

### P8. Presentation assets

- [x] Write the one-sentence description that leads the README, the About field, and every listing, and use the same sentence in all of them.
- [ ] Test that sentence by showing it to someone unfamiliar with the project and asking what the tool does. Rewrite until they get it right. **Needs the maintainer**: this requires an actual unfamiliar person.
- [ ] Record the browser flow as a screen capture: the agent starts working, an item appears in the tab, the done notification fires. This is the primary demo, because the browser tab is the primary interface. **Needs the maintainer**: a real recording of a real agent turn and a real OS notification, not a staged one.
- [ ] Record the terminal flow as an asciinema cast: a split terminal with the agent on one side and `turnbreak watch` on the other, showing an item arrive and the two actions. **Needs the maintainer**: same reason, plus a live agent session.
- [ ] Lead the README with the screen capture, and place the asciinema cast lower as a second look. Blocked on the recording above.
- [ ] Drop the asciinema cast if it adds nothing the screen capture already shows, rather than including it because it was recorded. Blocked on the recording above.
- [ ] Keep each recording under 30 seconds, and make both readable at the width GitHub renders them. Blocked on the recording above.
- [ ] Place the primary demo above the fold in the README, before any installation instructions. Blocked on the recording above.
- [x] Create the social preview image at the size the research found. `docs/assets/social-preview.png`, 1280x640.
- [x] Write the About field text and the topics list into `docs/positioning.md` so they are ready to paste at publish time.
- [x] Draft the launch posts for each venue found in P7, matched to each venue's format and rules. Drafted for Show HN and r/SideProject, the two venues with confirmed rules. The rest are blocked on confirming their rules first.

### P9. Documentation

Every file here follows `docs/writing-style.md`. Apply the P7 findings to structure, and the style guide to the prose.

- [x] Write `docs/writing-style.md` if it is missing, expanded from `AGENTS.md` section 6, with a pass and fail example per rule. It existed at the repo root instead of `docs/`. Moved it to match every reference to it in `AGENTS.md` and `TASKS.md`.
- [x] Write `README.md` from `general-swe/foundations/service-readme.md`, restructured to match the P7 findings, leading with what the reader gains. Skipped the owner/on-call/tier table per the template's own note that it doesn't fit a published tool.
- [x] Make the README answer, above the fold: what it does, what it looks like, and how to install it in one command. "What it looks like" is a placeholder marking where the P8 screen capture goes. The recording itself is still blocked on the maintainer.
- [x] Write `CONTRIBUTING.md` from `general-swe/foundations/contributing-guide.md`, including the writing check as a merge requirement.
- [x] Write `SECURITY.md` from `general-swe/foundations/security.md`, stating the loopback-only guarantee and what data never leaves the machine.
- [x] Write `.github/PULL_REQUEST_TEMPLATE.md` from `general-swe/foundations/pull-request-template.md`.
- [x] Write `.github/ISSUE_TEMPLATE/bug_report.md` from `general-swe/foundations/bug-report.md`.
- [x] Write `.github/ISSUE_TEMPLATE/feature_request.md` from `general-swe/foundations/feature-request.md`.
- [x] Write `CHANGELOG.md` from `general-swe/foundations/changelog.md`.
- [x] Decide which remaining templates earn their place for a project this size, add them, and record which you skipped and why in `docs/adrs/`. See `docs/adrs/0004-which-repo-templates-earn-a-place.md`. Added `CODE_OF_CONDUCT.md`, skipped the rest.
- [x] Run the writing check over every prose file in the repo, including this one, and loop until all pass. Covered every `.md` file except vendor files under `.venv/`, `.pytest_cache/`, and `CODE_OF_CONDUCT.md` (kept verbatim from the Contributor Covenant, per `docs/adrs/0004`, since editing adopted external text for house style would defeat the point of adopting it unmodified). Fixed em dashes, semicolons joining full sentences, and banned words across `AGENTS.md`, `docs/architecture.md`, `docs/generic-adapter.md`, `docs/adrs/0003`, `SKILL.md`, `src/turnbreak/adapters/SKILL.md`, `src/turnbreak/adapters/copilot_extension/README.md`, `TASKS.md`, `README.md`, and `docs/positioning.md`. Found and fixed a real accuracy bug along the way, not just style: `README.md` and `docs/positioning.md`'s Show HN draft both still said "Read and Skip are the only two actions," but the server code (`src/turnbreak/core/server.py`) implements Read/Next/Previous, an already-shipped redesign that `AGENTS.md` documents but `docs/architecture.md` had not caught up to. Rewrote the affected sections of `docs/architecture.md` to match, and left a note on the P10 test-coverage item about `turnbreak watch` still running the older read/skip model on its own.

### P10. Release readiness, still local

- [x] Write tests covering the threshold, read time arithmetic, the two actions, shown-item persistence, and the loopback bind. Note found during the P9 writing pass: the browser's actions are now read/next/previous, not read/skip. `turnbreak watch` still offers read/skip on its own. Cover both action sets, and flag the mismatch between the two interfaces for the maintainer to decide whether `watch` should move to read/next/previous too. Audited coverage: `test_watcher.py` already covers the threshold, `test_items.py` already covers `read_minutes`/`select_item`/`item_payload` arithmetic including the zero-word edge case, `test_server.py` already covers the browser's read/next/previous trio (including cross-session isolation and history retracing), `test_state.py` already covers shown-locator persistence across turns, and `test_server.py` already covers the loopback-only bind. The one real gap was `turnbreak watch`'s own read/skip/quit loop at the CLI layer: added `test_cmd_watch_interactive_skip`, `test_cmd_watch_interactive_quit_immediately_leaves_item_untouched`, and `test_cmd_watch_interactive_eof_exits_cleanly` to `tests/test_cli_watch_interactive.py`. The read/next/previous vs. read/skip mismatch between the browser and `watch` remains unresolved and is still flagged here for the maintainer; fixing it would be a functional change beyond a test-coverage task.
- [x] Decide whether to switch the dev toolchain from `pip`/`venv` to `uv` before CI locks the workflow in. Record the choice in `docs/adrs/`. See `docs/adrs/0005-uv-for-the-dev-toolchain.md`: switched. `uv.lock` committed, `AGENTS.md`'s install command updated, verified with a clean-checkout `uv sync` followed by a full pytest/ruff/mypy pass.
- [x] Add a CI workflow running lint, type check, and tests on push and pull request, committed but not yet run. See `.github/workflows/ci.yml`: installs `uv`, syncs from `uv.lock`, checks the lock matches `pyproject.toml`, then runs `ruff check`, `ruff format --check`, `mypy`, and `pytest`. Every step verified locally first with the same `uv run` invocations the workflow uses. Not yet run by GitHub Actions itself, since that requires a pushed remote, which is P11 territory.
- [x] Add a `.pre-commit-config.yaml` running `ruff check`, `ruff format --check`, and `mypy` on commit. Local hooks calling `uv run`, per `docs/adrs/0005`'s follow-on note, so pre-commit uses the same locked versions as CI instead of its own separately managed environment. Verified with `uvx pre-commit run --all-files`: all three hooks pass. Installed into `.git/hooks/pre-commit` via `uvx pre-commit install`, a local-only operation.
- [x] Verify the full flow by hand on Claude Code and one other agent, and record what broke. No real Claude Code or Codex session was available to trigger hooks live, so verified with simulated payloads shaped like each agent's real documented hook body, piped straight into `src/turnbreak/adapters/turnbreak-hook.py`, against an isolated `HOME` and a 2-second threshold: for both Claude Code (`hook_event_name: UserPromptSubmit` / `Stop`) and Codex (`event: UserPromptSubmit` / `Stop`, the real field name confirmed by fetching OpenAI's Codex CLI hooks docs), the start hook registered a session, the detached watcher fired after the threshold, `/current` served the real folder item, and the stop hook marked the turn ended in `state.json`. First attempt forgot to set `TURNBREAK_NO_BROWSER=1`, which popped two real Firefox windows on the maintainer's desktop mid-test; closed them immediately and reran every subsequent check with that variable set. Not yet confirmed against either agent's actual CLI firing the hook itself, the same live-session gap `docs/adrs/0003-copilot-hooks-turn-boundary-events.md` already recorded for Copilot.
- [ ] Verify notifications by hand on Linux, macOS, and Windows. Linux done: `notify_native()` (`src/turnbreak/core/notify.py`) called directly on this machine, `notify-send` fired a real "turnbreak: Your agent finished its turn." desktop notification, returned `True`. Confirmed `TURNBREAK_NO_NOTIFY=1` suppresses it and returns `False`. macOS and Windows still need a maintainer with those machines; this environment is Linux only.
- [x] Install the project from a clean checkout following only the README, and fix every step the README got wrong. Copied the repo to a scratch directory, used a plain `python3 -m venv` and system `pip`, ran every command the README documents (install, onboard accepting and declining the token-spend prompt, mode, finder, watch, serve, serve --stop) against an isolated `HOME`. Found and fixed two real bugs, not just doc drift: (1) `src/turnbreak/sources/agent.py` imported `extract_article` at module level purely to use as a default-argument value, so a bare `pip install turnbreak` (exactly what the README told a new user to run) crashed inside `turnbreak onboard` with `ModuleNotFoundError: No module named 'pypdf'`, since `pypdf`/`trafilatura` only ship in the optional `sources` extra. Made the import lazy inside `AgentFinder.__init__`, so `confirm_token_spend` and agent detection no longer need extraction libraries at all, only actually finding candidates does. (2) The README's install command was plain `pip install turnbreak`, but the default config (curated mode, agent finder) needs the `sources` extra to return real content, so changed it to `pip install "turnbreak[sources]"` with a line explaining when the bare install is enough. While verifying the four `turnbreak install` targets in the same pass, found `docs/generic-adapter.md`'s Codex section still described an unimplemented `codex_hooks.toml`/`config.toml` design (also stale-referenced in `docs/adrs/0003`); the shipped adapter has always used a `~/.codex/hooks.json` sidecar file. Looked up Codex CLI's real hooks.json schema and found it does not support the `matcher` field the template was sending on `UserPromptSubmit`/`Stop`, unlike Claude Code and Gemini CLI. Removed `matcher` from `src/turnbreak/adapters/codex_hooks.json` and rewrote the doc section to match. Not yet confirmed against a live Codex CLI session, since Codex isn't installed in this environment, the same limitation ADR-0003 already recorded for Copilot.
- [ ] Ask someone who has never seen the project to install it from the README alone, and fix what confused them.
- [x] Check that no secrets, absolute local paths, or personal data sit anywhere in the history, since the first push publishes every commit. Swept `git log -p --all` for API keys, tokens, private key headers, `.env`/credential files ever added, and real home-directory paths: none found. Test fixtures use placeholder values (`api_key="key"`, `/home/user/reading`), never real ones. One real finding: the git author email on 28 of the repository's 35 commits (everything through `3b8259f`, dated 2026-08-16) is the maintainer's real personal address, `milkeles.apps@gmail.com`, read from this machine's global `git config`. At some point a local `user.email = hristo@example.com` override was added to this repo's `.git/config`, and the 7 most recent commits (this session) correctly picked up that placeholder instead. Did not rewrite anything: changing 28 commits' author identity means rewriting history and every commit hash after it, which is exactly the kind of operation this project holds for explicit instruction rather than doing unprompted. Flagged in full on the next item and in my reply to the maintainer.
- [x] Squash or clean the history if it exposes anything the maintainer would not want public. Maintainer chose the GitHub noreply address over the placeholder: `91317021+Milkeles@users.noreply.github.com` (built from the account id and username on the authenticated `gh` session, since the account has no public email and I did not request the wider token scope needed to read private ones). Backed up the full repo directory first. Rewrote every commit's author and committer identity with `uvx git-filter-repo --mailmap ... --force`, mapping both `milkeles.apps@gmail.com` and the interim `hristo@example.com` placeholder to the GitHub address, so all 36 commits (not just the 28 flagged) carry one consistent identity. `git-filter-repo` needed `--force` since the repo has no `origin` remote and doesn't look like a fresh clone, which is expected for a repo that has never been pushed. Verified after: `git log --all --format="%an <%ae>" | sort -u` shows exactly one identity, the `v0.1.0` tag still points at the right commit, `git status` is clean, and the full test suite (249 tests) still passes, since a mailmap rewrite touches only commit metadata. Updated `.git/config`'s local `user.email` to the same address so future commits match without another override. Removed the backup once verification passed. Safe to do without a second confirmation because nothing had ever been pushed, so no hash anyone else holds was invalidated.
- [x] Tag v0.1.0 locally and write release notes. Release notes in `CHANGELOG.md`'s new `[0.1.0]` section. Tagged locally with `git tag -a v0.1.0`, not pushed, per the P11 boundary. Survived the history rewrite above; still points at the correct commit.
- [x] Hand the project to the maintainer for testing, and stop. Two open items still need the maintainer directly and cannot be closed autonomously: notifications on macOS/Windows (this environment is Linux only), and a fresh install by someone who has never seen the project. The history-email decision that was pending here is resolved (see the item above).

### P11. Publish, on explicit instruction only

Do not start any of this until the maintainer says to push.

Note: on the maintainer's explicit instruction, `github.com/Milkeles/turnbreak` was created as a **private** repository and `main` plus the `v0.1.0` tag were pushed, so the maintainer could read through the result before deciding whether to go further. This is not the same as this checklist. The repo stays private, no release was published, and nothing below was started, until the maintainer says it's ready and makes it public themselves.

- [ ] Confirm with the maintainer that the repository should go public now.
- [ ] Create the GitHub repository, set the About field and topics from `docs/positioning.md`, and upload the social preview image.
- [ ] Push and verify the README renders correctly, especially the demo. The demo itself is still an open gap: `README.md` carries a TODO for the P8 screen capture, but no recording was ever made, only the spec in `docs/positioning.md`.
- [ ] Publish the release.
- [ ] Submit to the directories and lists found in P7, using the drafts from P8.
- [ ] Post the launch posts, spaced as the P7 research recommends rather than all at once.

---

## 2. Dependencies

| Task | Blocked by |
|---|---|
| Every prose file | `docs/writing-style.md` exists |
| All P9 documentation | Templates repo cloned, group READMEs read, P7 research done |
| Watcher fires an item | Session state and config loading |
| Single-tab reuse | Server running |
| Done signal layers | `turnbreak stop` and single-tab reuse |
| Two actions | Reading page built |
| Shown-item persistence | Default keep-reading behavior and session state |
| Item selection | Read time calculation |
| Curated source | `interests.md` exists |
| List improvement | `history.jsonl` and the curated source |
| All four adapters | One shared hook script, `turnbreak start`, `turnbreak stop` |
| Codex, Gemini, Copilot adapters | Claude Code adapter |
| The demo recording | Both sources and the done signal working end to end |
| README structure | P7 research and the demo recording |
| Everything in P11 | Every task above, plus the maintainer saying to push |

---

## 3. Completion

|  |  |
|---|---|
| **Convention** | Check off and keep. The queue doubles as the build log until v0.1.0, then switch to delete on completion. |

---

## 4. Delegated decisions

Decide these yourself when you reach the task. Do not stop and ask.

Each one below gives the rule to decide by. Pick, write the choice and your reasoning into `docs/adrs/`, and keep going. A recorded decision can be reversed later. A blocked queue cannot.

- **Which Copilot events map to turn start and turn end?** Read the current Copilot hooks reference and match the events to the two the other three agents use. If Copilot has no clean equivalent, ship without the Copilot adapter and say so in the README. Three agents working beats four half-working.
- **Which PDF text extraction library?** It only counts words, never displays anything. Pick the smallest one that handles ordinary text PDFs. Scanned PDFs yielding nothing is acceptable.
- **Does the `agent` finder produce a usable list?** This is a test, not a judgment. Build a list, check how many links resolve. Keep `agent` as the default if most do. Make `rss` the default if most do not, and note the result in the README so users know why.

**When to break this rule and ask anyway.** Escalate if a decision would change something in the "Ask first" or "Never do" columns of `AGENTS.md` section 5: adding a `core/` dependency, changing a default, changing the on-disk format, spending the user's money, or sending data off the machine. Everything else is yours.

**Decisions already made, kept for the record.**

- *How does the curated source find candidates?* All three finders ship. The user picks in `config.toml`. Default is `agent`, subject to the link check above.
- *Does the folder source handle PDF and EPUB?* PDF yes, embedded in the page shell, with separate text extraction for the word count. EPUB no, deferred.
- *What records the demo?* Screen capture for the browser flow, which is primary. An asciinema cast for the terminal flow, kept only if it earns its place.



---

## 5. Deferred ideas

Not in scope for v0.1.0. Recorded so they are not re-proposed as new.

- **Spaced repetition.** Show one flashcard from a deck instead of an article. A 90 second gap suits a card better than an essay, and the same two actions map onto it.
- **Context-aware items.** Show docs for the library the agent just imported. Needs the agent to pass context through the hook, which breaks the rule that core knows nothing about any agent.
- **Read-it-later services.** Pull the list from Pocket, Wallabag, or Readwise instead of a local folder. Each needs an API token, which conflicts with the no-network-egress boundary unless made opt-in and explicit.
- **RSS.** A middle point between the two current modes: user-controlled like a folder, fetched like the curated list.
- **Rest mode.** Show a blank calm screen and no item. Some users want the notification and nothing else.
- **EPUB in the folder source.** Browsers have no native EPUB support, so it needs a reader library embedded in the page shell. Worth doing if people ask, since a book chapter is a natural 2 to 4 minute item.
- **`turnbreak stats`.** Report your real turn duration distribution, so the threshold default can be argued from your data rather than ours.
