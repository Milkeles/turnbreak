# Task plan: turnbreak

|  |  |
|---|---|
| **Covers** | Whole repo, from empty to first release |
| **Last reviewed** | 2026-08-16 |

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

- [x] Write `docs/architecture.md` covering the timer, the server, the two sources, the three actions, and the adapter boundary.
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
- [x] Implement the Keep reading action, which holds the current item on screen and suppresses the next fire.
- [x] Make the hold persist across turns until the user picks Read or Skip.
- [x] Add a test asserting a held item is not replaced when a new turn passes the threshold.
- [ ] Implement end-of-list handling, which asks whether to edit interests and build a new list, and never rebuilds silently.

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

- [ ] Implement first-run onboarding, which asks for interests and writes `~/.config/turnbreak/interests.md`.
- [x] Implement `turnbreak interests`, which opens the file in `$EDITOR` or prompts inline when `$EDITOR` is unset.
- [x] Implement `turnbreak watch`, a terminal pane offering the same three actions for users who prefer the keyboard.
- [ ] Add the `/turnbreak-interests` slash command for agents that support slash commands.

### P6. Agent support

- [ ] Write one hook script that reads JSON from stdin, writes nothing to stdout, and works unchanged across all four agents.
- [ ] Write the Claude Code adapter registering the script in `.claude/settings.json` under a `hooks` key.
- [ ] Write the Codex adapter registering the script in `.codex/hooks.json` with event names at the root, returning JSON on `Stop`.
- [ ] Write the Gemini CLI adapter registering the script in `settings.json`, mapping turn start to `BeforeAgent` and turn end to `AfterAgent`.
- [ ] Check the current Copilot hooks reference for its turn start and turn end event names, then write the Copilot adapter.
- [ ] Write `SKILL.md` so Claude Code and Codex can install turnbreak as a skill.
- [ ] Write `turnbreak install AGENT` to place adapter files in the right location for each agent.
- [ ] Write a generic adapter documenting the two commands any other agent must call.

### P7. Positioning research

The goal is a repository a stranger understands in 10 seconds and wants in 30. Research first, then write. Everything here is prepared locally.

**Rules for this research.** Prefer evidence over advice. A GitHub blog post with data, a study of what correlates with stars, or a documented before-and-after beats a listicle titled "10 tips for an awesome README." Where the sources disagree or offer only opinion, say so in the notes instead of picking one quietly. Record what you find in `docs/positioning.md` with links, then apply it.

- [ ] Research what makes a repository understandable in the first 10 seconds, focusing on what sits above the fold before a reader scrolls.
- [ ] Research how the GitHub About field works as a discovery surface: its character limit, how much of it shows in search results and on profile cards, and how much of the value lands in the first few words.
- [ ] Research GitHub topics: how many are useful, which ones this project should claim, and how people actually browse them.
- [ ] Research the social preview image: what size GitHub expects, and how much it changes what a shared link looks like on social platforms and in chat.
- [ ] Research README structure specifically for developer tools and CLI tools, not for libraries or frameworks, since the reader's first question differs.
- [ ] Research which badges carry information and which are noise, and pick the smallest set that answers a real question.
- [ ] Find where this project's audience already is: skill directories such as `skillsllm.com` and `skills.rest`, relevant awesome-lists, and the subreddits and forums where agent tooling gets discussed.
- [ ] For each place found, record its submission rules, its format, and whether it requires the project to already have traction.
- [ ] Research what a good launch post looks like on the two or three highest-value venues, and note what gets removed or downvoted.
- [ ] Write `docs/positioning.md` holding all findings with links, and a short note wherever the evidence is weak.

### P8. Presentation assets

- [ ] Write the one-sentence description that leads the README, the About field, and every listing, and use the same sentence in all of them.
- [ ] Test that sentence by showing it to someone unfamiliar with the project and asking what the tool does. Rewrite until they get it right.
- [ ] Record the browser flow as a screen capture: the agent starts working, an item appears in the tab, the done notification fires. This is the primary demo, because the browser tab is the primary interface.
- [ ] Record the terminal flow as an asciinema cast: a split terminal with the agent on one side and `turnbreak watch` on the other, showing an item arrive and the three actions.
- [ ] Lead the README with the screen capture, and place the asciinema cast lower as a second look.
- [ ] Drop the asciinema cast if it adds nothing the screen capture already shows, rather than including it because it was recorded.
- [ ] Keep each recording under 30 seconds, and make both readable at the width GitHub renders them.
- [ ] Place the primary demo above the fold in the README, before any installation instructions.
- [ ] Create the social preview image at the size the research found.
- [ ] Write the About field text and the topics list into `docs/positioning.md` so they are ready to paste at publish time.
- [ ] Draft the launch posts for each venue found in P7, matched to each venue's format and rules.

### P9. Documentation

Every file here follows `docs/writing-style.md`. Apply the P7 findings to structure, and the style guide to the prose.

- [ ] Write `docs/writing-style.md` if it is missing, expanded from `AGENTS.md` section 6, with a pass and fail example per rule.
- [ ] Write `README.md` from `general-swe/foundations/service-readme.md`, restructured to match the P7 findings, leading with what the reader gains.
- [ ] Make the README answer, above the fold: what it does, what it looks like, and how to install it in one command.
- [ ] Write `CONTRIBUTING.md` from `general-swe/foundations/contributing-guide.md`, including the writing check as a merge requirement.
- [ ] Write `SECURITY.md` from `general-swe/foundations/security.md`, stating the loopback-only guarantee and what data never leaves the machine.
- [ ] Write `.github/PULL_REQUEST_TEMPLATE.md` from `general-swe/foundations/pull-request-template.md`.
- [ ] Write `.github/ISSUE_TEMPLATE/bug_report.md` from `general-swe/foundations/bug-report.md`.
- [ ] Write `.github/ISSUE_TEMPLATE/feature_request.md` from `general-swe/foundations/feature-request.md`.
- [ ] Write `CHANGELOG.md` from `general-swe/foundations/changelog.md`.
- [ ] Decide which remaining templates earn their place for a project this size, add them, and record which you skipped and why in `docs/adrs/`.
- [ ] Run the writing check over every prose file in the repo, including this one, and loop until all pass.

### P10. Release readiness, still local

- [ ] Write tests covering the threshold, read time arithmetic, the three actions, hold persistence, and the loopback bind.
- [ ] Decide whether to switch the dev toolchain from `pip`/`venv` to `uv` before CI locks the workflow in. Record the choice in `docs/adrs/`.
- [ ] Add a CI workflow running lint, type check, and tests on push and pull request, committed but not yet run.
- [ ] Add a `.pre-commit-config.yaml` running `ruff check`, `ruff format --check`, and `mypy` on commit.
- [ ] Verify the full flow by hand on Claude Code and one other agent, and record what broke.
- [ ] Verify notifications by hand on Linux, macOS, and Windows.
- [ ] Install the project from a clean checkout following only the README, and fix every step the README got wrong.
- [ ] Ask someone who has never seen the project to install it from the README alone, and fix what confused them.
- [ ] Check that no secrets, absolute local paths, or personal data sit anywhere in the history, since the first push publishes every commit.
- [ ] Squash or clean the history if it exposes anything the maintainer would not want public.
- [ ] Tag v0.1.0 locally and write release notes.
- [ ] Hand the project to the maintainer for testing, and stop.

### P11. Publish, on explicit instruction only

Do not start any of this until the maintainer says to push.

- [ ] Confirm with the maintainer that the repository should go public now.
- [ ] Create the GitHub repository, set the About field and topics from `docs/positioning.md`, and upload the social preview image.
- [ ] Push and verify the README renders correctly, especially the demo.
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
| Three actions | Reading page built |
| Hold persistence | Keep reading action and session state |
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

- **Spaced repetition.** Show one flashcard from a deck instead of an article. A 90 second gap suits a card better than an essay, and the same three actions map onto it.
- **Context-aware items.** Show docs for the library the agent just imported. Needs the agent to pass context through the hook, which breaks the rule that core knows nothing about any agent.
- **Read-it-later services.** Pull the list from Pocket, Wallabag, or Readwise instead of a local folder. Each needs an API token, which conflicts with the no-network-egress boundary unless made opt-in and explicit.
- **RSS.** A middle point between the two current modes: user-controlled like a folder, fetched like the curated list.
- **Rest mode.** Show a blank calm screen and no item. Some users want the notification and nothing else.
- **EPUB in the folder source.** Browsers have no native EPUB support, so it needs a reader library embedded in the page shell. Worth doing if people ask, since a book chapter is a natural 2 to 4 minute item.
- **`turnbreak stats`.** Report your real turn duration distribution, so the threshold default can be argued from your data rather than ours.
