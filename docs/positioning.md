# Positioning

|  |  |
|---|---|
| **Covers** | Research behind the README, the About field, topics, the social preview, and launch venues |
| **Last reviewed** | 2026-08-17 |

---

## Above the fold

Nielsen Norman Group's eye-tracking research found that readers spend most of their time on the visible part of a page, and only scroll further when that visible part gives them a reason to. Their original study put 80 percent of viewing time above the fold. A later re-run put it at 57 percent, with 74 percent inside the first two screens. Either way, the first screen carries most of the weight. This research covers web pages in general, not READMEs specifically, so treat it as the closest evidence available rather than a README study.

Three high-star CLI tools show the same pattern in practice. `cli/cli`'s README opens with the name, a one-sentence tagline, and a screenshot of `gh pr status` running, before any badge or install step. `junegunn/fzf` leads with a logo and a one-line description, then a preview image, then a four-item feature list, before installation. `BurntSushi/ripgrep` opens with the name and a one-sentence description, states what it does and does not do, then shows a screenshot of real search output, before installation. All three put a name, a one-sentence description, and a picture of the tool running above any install command.

An analysis of 1,950 READMEs across ten programming languages found that READMEs in the more popular projects are organized with lists and images, and link out to external sources. Projects with contribution guidelines and references correlated with higher popularity. ([arxiv.org/abs/2206.10772](https://arxiv.org/abs/2206.10772))

Turnbreak's README should open with the same shape: the name, the one-sentence description written in P8, and the screen capture of the browser tab receiving an item. No badge or install step above that.

## GitHub About field

GitHub's description field, the one line shown in the About sidebar, caps at 350 characters. `github-limits`, a maintained list of GitHub's undocumented limits, states this, and a GitHub Desktop issue against the real form confirms it: entering more than 350 characters throws the exact error, so the number is a measured fact, not a guess. ([dead-claudia/github-limits](https://github.com/dead-claudia/github-limits), [desktop/desktop#19465](https://github.com/desktop/desktop/issues/19465))

How much of that 350 characters shows on a search result card or a profile card before truncation is not documented anywhere found in this research. Write the About field so the first sentence stands alone and says what the tool does, and treat the rest as room for a fragment that would not be missed if cut.

## GitHub topics

GitHub's own docs state the rules directly: topics use lowercase letters, numbers, and hyphens, each topic tops out at 50 characters, and a repository can carry at most 20. GitHub also scans public repository content and suggests topics, which an admin can accept or decline. ([GitHub Docs: classifying your repository with topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics))

GitHub does not publish a recommended count below the 20-topic ceiling. Blog posts converge on 5 to 8 as a practical number, but none of them cite data, so treat that range as opinion, not a documented rule. Claim topics that name what the tool is (`cli-tool`, `claude-code`, `productivity`) and what it plugs into (`claude`, `codex`, `gemini-cli`), since those are the terms someone would type into GitHub's topic search.

## Social preview image

GitHub's docs give exact numbers: the image should be a PNG, JPG, or GIF under 1 MB, at least 640 by 320 pixels, with 1280 by 640 recommended for the sharpest rendering on social platforms and in chat previews. PNG supports transparency. ([GitHub Docs: customizing your repository's social media preview](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview))

## README structure for CLI tools

The same three repositories read in "Above the fold" show a shared shape once past the opening screen: a short "why use this" or comparison section, then installation, then usage, then a related-tools or contributing section near the bottom. None of the three lead with installation. `ripgrep` puts "Why should I use ripgrep?" and "Why shouldn't I use ripgrep?" before a single install command. `fzf` puts a four-item highlights list first. `cli/cli` puts a screenshot and a platform-support line first.

This differs from a library README, where the reader's first question is usually "what's the API," not "what does running this look like." A CLI tool's reader wants to see it run before they read how to call it. Turnbreak's README should follow the same order: name and description, the screen capture, a short why-this-exists section, then install, then usage.

## Badges

No study measuring which README badges affect a reader's trust or a project's adoption turned up in this research. What exists is blog-level consensus: a badge only carries information if it is live and verifiable, like a build-status badge wired to real CI or a real coverage percentage, and a row of unlinked or decorative badges gets discounted by readers who have seen enough of them to know the difference. Treat this as opinion, not evidence.

Turnbreak's badge row should stay small: a CI build-status badge once P10 adds one, and a license badge. Nothing else earns a place until it ties to something that is actually checked on every commit.

## Audience venues

**skillsllm.com.** A skill-directory listing site. The submission mechanism was not confirmed by this research. Its site did not yield a clear submission page in the searches run. Confirm the actual process before drafting a listing.

**skills.rest.** Lists individual Claude Code skills, each with its own page (for example `skills.rest/skill/skill-file-structure`). A direct fetch of the site returned an HTTP 403, and search results did not turn up a documented submission form. Turnbreak is a CLI tool with an installable hook, not a `SKILL.md`-shaped skill, so it may not fit this directory's model at all. Confirm fit and process before treating this as a venue.

**`hesreallyhim/awesome-claude-code`.** A curated list with its own `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md`, and over 870 open issues at the time of this research, which points to an actively maintained list rather than an abandoned one. The exact submission requirements, including whether a project needs existing traction, were not read in full. Read `CONTRIBUTING.md` directly before submitting.

**`ComposioHQ/awesome-claude-skills`, `travisvn/awesome-claude-skills`, `karanb192/awesome-claude-skills`.** Three more curated lists in the same space, each accepting outside contributions through a PR against the list. None of these were confirmed to require existing traction, but none were fully read either.

**r/ClaudeAI.** A subreddit with roughly 1.1 million members focused on Claude and Claude Code. Its specific self-promotion rules were not found in this research. Check the subreddit's sidebar and rules wiki directly before posting.

**r/SideProject.** Roughly 180,000 members, and self-promotion is explicitly allowed. The expected shape of a post is what was built, why, what it's built with, and what feedback the poster wants, not a bare link. A waitlist or email-gated link gets removed. A launch, a major update, or a real milestone gets a post, at a rough cadence of once every three to four weeks per project.

**Hacker News, Show HN.** Not a directory, but a launch venue with the most explicit rules of anything found in this research.

## Launch post practices

Hacker News publishes its own Show HN rules directly, which makes this the strongest-sourced item in this file. The title must start with "Show HN". The project has to be something the poster built personally and can discuss, not a landing page, a newsletter, a sign-up gate, or a version-bump post like "Foo 1.3.1 is out." Soliciting upvotes or comments, from anyone, gets it flagged. ([news.ycombinator.com/showhn.html](https://news.ycombinator.com/showhn.html))

Blog-level sources converge on a 9 AM to 12 PM Pacific posting window and a comment style that explains what the tool does and why it was built, then answers every reply. These are not sourced from Hacker News itself, so treat the timing claim as a community observation rather than a documented rule.

r/SideProject's norms are covered above, under "Audience venues": show the real thing, describe the build, skip the waitlist link.

For turnbreak specifically, a Show HN post and an r/SideProject post are the two venues with the clearest rules and the least ambiguity about fit. r/ClaudeAI needs its rules read first. The skill directories need their submission process and their fit confirmed before any post gets drafted for them.

## Ready to paste

**The one-sentence description.** Used unchanged in the About field, and as the opening line of the README with "Turnbreak" prefixed:

> Shows you something worth reading while your coding agent works.

**The About field.** The sentence above, exactly as written. 67 characters, well under the 350-character limit.

**Topics.** Eight, naming what the tool is and what it plugs into, inside GitHub's 20-topic ceiling and within the practitioner-opinion range of 5 to 8 noted above:

`claude-code`, `codex-cli`, `gemini-cli`, `cli-tool`, `developer-tools`, `productivity`, `reading`, `rss`

## Launch post drafts

Drafted only for the two venues with confirmed rules: Show HN and r/SideProject. The others need their rules or their fit confirmed first, per "Audience venues" above.

**Show HN.**

Title: `Show HN: Turnbreak – a reading tab that opens while your coding agent works`

> Turnbreak watches how long my coding agent's turn has been running. Past 90 seconds it opens one browser tab and puts something to read in it: an article, a paper, a file from a folder I point it at. I read it while the agent works. When I click Read, or the turn ends, it gets out of the way.
>
> It runs a small HTTP server bound to 127.0.0.1 and pushes updates over Server-Sent Events, so the tab updates without a refresh. It installs as a hook for Claude Code, Codex, Gemini CLI, or Copilot. Nothing it reads or shows ever leaves the machine.
>
> I built it because agent turns on real tasks often run one to five minutes, and I kept unlocking my phone to fill that time instead of reading something I actually meant to get to. Happy to answer questions about the hook timing, the source finders, or anything else.

**r/SideProject.**

Title: `Built a tool that gives me something to read while my coding agent is thinking`

> **What it is.** Turnbreak is a small CLI tool. It hooks into your coding agent (Claude Code, Codex, Gemini CLI, or Copilot) and watches how long the current turn has been running. Past a threshold, it opens a browser tab and shows something worth reading: an article pulled from your stated interests, an RSS feed, a search, or files from a folder you name.
>
> **Why I built it.** My agent's turns run one to five minutes on real tasks. I was spending that time doomscrolling instead of reading things I already wanted to read. Turnbreak points that dead time at my own reading list instead.
>
> **How it's built.** Python, a stdlib-only HTTP server bound to loopback only, Server-Sent Events for pushing updates to the tab, and a thin adapter per agent that just calls `turnbreak start` and `turnbreak stop`. No third-party server dependencies, so there's less to audit before you trust something that watches your terminal.
>
> **What I want feedback on.** Whether 90 seconds is the right default threshold, and whether the reading-list sources (agent-driven suggestions, RSS, search, a plain folder) cover how people actually want to feed it. Repo's local for now while I finish the last pieces. Happy to answer anything in the meantime.
