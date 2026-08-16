# Writing style

Every file a human reads follows this. That means README, docs, CONTRIBUTING, SECURITY, issue and PR templates, CLI help text, error messages, and code comments.

Read this file before you write any of them. Check your draft against it before you commit.

---

## 1. The rules

Each rule has a failing example and a passing one. The failing examples are real patterns, not strawmen.

### Write for understanding, not to impress

The reader wants the idea. They do not want to admire your writing.

Fail: Turnbreak leverages a sophisticated event-driven architecture to surface curated intellectual content during agentic execution windows.

Pass: Turnbreak shows you something to read while your agent works.

### Put the main point first

Do not build up to it. Say it, then explain it.

Fail: There are many ways to configure the threshold. Some users prefer longer waits, others shorter. After weighing the trade-offs, we settled on 90 seconds as the default.

Pass: The default threshold is 90 seconds. Most agent turns finish in under 3 minutes, so a longer wait means the skill rarely fires.

### Use plain language

Replace any word the reader might have to look up.

Fail: Instantiate the daemon to facilitate content delivery.

Pass: Start the server. It sends items to the page.

### Focus on what the reader gains

Describe the outcome, not the mechanism.

Fail: Turnbreak implements a dual-source item pipeline with queue precedence.

Pass: Turnbreak reads your saved list first. When that runs out, it finds new things you might like.

### Use short sentences

If a sentence has two ideas, make it two sentences.

Fail: The watcher, which starts when your turn begins and is killed by the stop hook, measures real elapsed time rather than predicting duration, because predictions are unreliable for exactly the short tasks where a wrong guess is most disruptive.

Pass: The watcher measures real elapsed time. It never predicts how long a task will take. Predictions fail most often on short tasks, which is where a wrong guess hurts most.

### Keep paragraphs short

Three sentences is usually enough. Break anything longer.

### Use active voice

Name who does the thing.

Fail: The configuration file is read at startup and defaults are applied where values are absent.

Pass: Turnbreak reads the config file at startup. It fills in defaults for anything you left out.

### Remove unnecessary words

Cut every word that carries no meaning.

Fail: It is important to note that in order to utilize this feature, you will first need to make sure that you have configured your interests.

Pass: Set your interests first.

### Use specific language

Replace vague claims with numbers, examples, or evidence.

Fail: Turnbreak fires after a reasonable delay and shows appropriately sized content.

Pass: Turnbreak fires after 90 seconds. It prefers items that take 2 to 4 minutes to read.

### Avoid unnecessary terminology

Use a term only if your reader already knows it. If you must introduce one, define it once in plain words.

Fail: The adapter marshals the hook payload across the IPC boundary.

Pass: The hook sends JSON to the server over a local socket.

### Write for the audience

A contributor reading CONTRIBUTING wants to know how to get a PR merged. They do not want your design philosophy.

### Address objections directly

Name the doubt and answer it.

Fail: Turnbreak is safe and private.

Pass: Turnbreak runs a server on your machine only. It binds to 127.0.0.1, so nothing outside your computer can reach it. Your interests and reading history never leave the disk.

### Support claims with proof

Back a claim with a number, a source, or a link.

Fail: Most agent turns are short.

Pass: In our own use, most agent turns finish in 30 seconds to 3 minutes. Measure your own with `turnbreak stats` before changing the threshold.

### Avoid clever writing that reduces clarity

A joke that costs the reader a re-read is a bad trade. Keep the joke only if the sentence still reads clean without it.

### Edit aggressively

Write it, then cut it. A second pass should remove 20 percent.

### Guide the reader logically

Order sections so each one only needs what came before it. Never reference a concept you have not introduced.

---

## 2. Banned patterns

These are AI writing tells. Search for each one before committing.

**Punctuation**

- Em dashes. Use a period, a comma, or a colon.
- Semicolons joining two full sentences. Use a period.

**Words**

Delve, leverage as a verb, utilize, seamless, robust, comprehensive, powerful, cutting-edge, elevate, unlock, harness, realm, landscape, tapestry, testament, crucial, vital, pivotal.

**Phrases**

- "It is important to note that"
- "It is worth noting that"
- "In today's fast-paced world"
- "Let's dive in"
- "In conclusion" or "To summarize" at the end of anything short
- "When it comes to"
- "In order to" where "to" works
- "That being said"
- "At the end of the day"

**Structures**

- "It's not just X, it's Y." Say what it is.
- "Whether you're a beginner or an expert." Pick one reader.
- Three-item lists where two items would do, repeated across a document.
- Chains of "Furthermore," "Moreover," "Additionally."
- Stacked hedges: "may potentially," "could possibly," "might perhaps."
- Section openings that restate the heading. Under "Installation," do not begin "To install Turnbreak, follow these steps."
- Every paragraph the same length. Vary them.
- A closing paragraph that adds nothing. Stop when you are done.

---

## 3. The verify loop

Do this every time you write or edit a prose file, however small the change.

1. Write the draft.
2. Check the draft against section 1, rule by rule. Fix each failure.
3. Search the draft for every banned pattern in section 2. Remove each hit.
4. Read the draft again. If any rule now fails because of a fix you made in step 3, go back to step 2.
5. Repeat until a full pass finds nothing to change.
6. Run the humanize pass in section 4.
7. If the humanize pass changes anything, go back to step 2.

Do not skip this because a change looks small. A one-line README edit is a prose change.

---

## 4. The humanize pass

There is no external tool for this step, and that is deliberate. The available humanizer tools are built to defeat AI detectors like GPTZero and Turnitin. Their main technique translates text through other languages and back, which rewrites meaning. Applied to technical documentation, that produces prose that sounds human and states the wrong thing.

So the humanize pass is a self-review. Read the draft as a person, not as its writer, and answer these:

1. **Would a person say this out loud?** Read it aloud. Anything you would not say in conversation gets rewritten.
2. **Does every paragraph sound the same?** Uniform rhythm is the strongest tell. Vary sentence length on purpose. A four-word sentence after a long one works.
3. **Is there a real detail in here?** Specific numbers, real commands, actual file paths, a named failure. Generic writing has none. If a paragraph would fit any project, it is not about this one.
4. **Did I hedge because I did not know?** Replace the hedge with the fact, or say plainly that it is undecided.
5. **Am I explaining something the reader already knows?** Cut it.
6. **Does it end where it stops being useful?** Delete any wrap-up that repeats what came before.

Rewrite what fails. Then return to step 2 of the verify loop.

---

## 5. Applies to code too

Error messages and CLI help are prose. They get the same treatment.

Fail: `Error: invalid configuration state detected.`

Pass: `Can't read ~/.config/turnbreak/config.toml: line 4 sets threshold_seconds to "ninety". It needs a number.`

Comments explain why, never what.

Fail: `# increment the counter`

Pass: `# Gemini sends AfterAgent once per turn, Codex sends Stop once per turn. Count turns, not events.`
