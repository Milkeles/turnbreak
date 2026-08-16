# ADR-0002: Use third-party libraries for article extraction, feed parsing, and web search

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-08-16 |
| **Deciders** | Hristo Hristov (maintainer), via agent-assisted build |

---

## Context and problem statement

P4 needs three finders that turn `interests.md` plus history into candidate `Item` objects: `agent`, `rss`, and `search`. All three need real, non-estimated word counts for URLs, which means fetching a page and extracting its main text. The `rss` finder needs to read feeds in whatever RSS or Atom variant a site happens to publish. The `search` finder needs a web search API.

`AGENTS.md` section 3 allows third-party dependencies in `src/turnbreak/sources/`, unlike `core/`, because this code never runs inside a synchronous hook.

---

## Decision drivers

- Read time depends on `word_count`, and `AGENTS.md` bans ever asking a model to estimate it. A finder that returns a URL still needs a real extracted word count before the item is usable.
- Feed formats vary across RSS 0.9x, RSS 2.0, and Atom, each with their own quirks. Hand-rolled XML parsing would need to cover all of them correctly to avoid silently dropping feeds.
- Per the ready-solutions rule added to `AGENTS.md` section 3 this same session, a maintained library beats hand-rolled code for a solved problem like this.
- The `search` finder is opt-in and skipped entirely with no API key configured, so the chosen API must have a real free tier for anyone trying the feature without committing to a paid plan.

---

## Considered options

**Article extraction (agent and search finders, to turn a URL into clean text and a word count)**

1. `trafilatura`. A multi-stage heuristic pipeline, no ML or GPU, actively maintained.
2. `readability-lxml`. The algorithm behind Firefox Reader View. Returns cleaned HTML rather than plain text.
3. Hand-rolled: fetch HTML, strip tags with `html.parser`.

**Feed parsing (rss finder)**

1. `feedparser`. The long-standing standard for Python feed parsing, handling RSS 0.9x/1.0/2.0 and Atom.
2. Hand-rolled: parse feed XML directly with `xml.etree`.

**Web search (search finder)**

1. Brave Search API. Independent index, plain REST interface, 2,000 queries/month free tier.
2. Google Programmable Search Engine. Being discontinued for new customers.
3. Serper. Wraps Google's own results rather than an independent index.
4. Tavily / Exa. Priced and positioned for AI-agent search rather than general web search, with no meaningfully free tier for this project's scale.

---

## Decision

We will use `trafilatura` for article extraction, `feedparser` for feed parsing, and the Brave Search API for the `search` finder.

`trafilatura` scores highest on published extraction benchmarks (F1 0.958 against `readability-lxml`'s 0.922) and strips navigation, ads, and boilerplate rather than just tags, which naive tag-stripping would count as words and skew every read-time estimate. Hand-rolled tag-stripping was rejected for the same reason: a full page has more non-article text than article text, so a rough tool would make read times wrong on exactly the items it recommends.

`feedparser` is the de facto standard for this problem in Python. Hand-rolling feed XML parsing means re-discovering every format quirk `feedparser` already handles, one broken feed at a time.

Brave Search API was chosen over the alternatives because it has an independent index rather than reselling Google's, a real free tier sized for this project's usage, and a plain REST interface that needs no SDK, which fits the project's minimal-dependency ethos better than a heavier agent-search-focused API.

---

## Consequences

**Positive**

- Word counts for fetched URLs reflect the actual article, not the whole page or a model's guess.
- Feed parsing handles real-world feeds on the first try instead of failing on formats not seen during development.
- The `search` finder works with a free API key and no paid commitment.

**Negative**

- Three more runtime dependencies land in `sources/`, all absent from `core/`.
- The Brave Search API is a paid vendor beyond its free tier. If usage grows past 2,000 queries/month, that becomes a cost decision for the maintainer, not just a technical one.

**Follow-on work**

- None expected. Revisit only if a dependency stops being maintained or a vendor's free tier terms change.

---

## Confirmation

`tests/test_core_is_stdlib_only.py` continues to pass, confirming none of these three land in `core/`. `pyproject.toml` lists all three under an install extra scoped to `sources/`, never as a bare top-level dependency.

---

## More information

None.

---

## Related documents

- [`AGENTS.md`](../../AGENTS.md). The ready-solutions rule and the `core`/`sources` dependency split this decision operates under
- [`docs/architecture.md`](../architecture.md). Where the finders fit in the overall shape
