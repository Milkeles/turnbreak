# ADR-0005: Use `uv` for the dev toolchain instead of `pip`/`venv`

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-08-17 |
| **Deciders** | Hristo Hristov (maintainer), via agent-assisted build |

---

## Context and problem statement

P10 needs a CI workflow running lint, type check, and tests on every push and pull request. Before that workflow gets written, `TASKS.md` calls for deciding whether the dev toolchain stays on `pip`/`venv` or switches to `uv`, since the CI workflow will lock in whichever choice is made here.

The project so far used `pip install -e ".[dev]"` into a `.venv` created by `python -m venv`, documented in `AGENTS.md` section 2. There was no lockfile, so a fresh install could resolve different dependency versions than whatever the maintainer or CI last ran.

---

## Decision drivers

- `uv` was already installed on the machine this project is built on (`uv 0.12.1` at `~/.local/bin/uv`), so switching costs nothing in tooling setup.
- `uv lock` produces a committed `uv.lock`, so CI, the maintainer's machine, and any future contributor's machine resolve the exact same dependency versions. `pip`/`venv` alone has no equivalent lockfile.
- `uv sync` installs from that lock in under two seconds against a cold cache in this environment, against several seconds for `pip install -e ".[dev]"`. CI runs on every push and pull request, so install time adds up.
- `uv` reads the existing `pyproject.toml` as is. No dependency or optional-dependency group needed to move or change shape to adopt it.
- This is a dev-toolchain choice, not a runtime dependency added to `core/`, not a default, and not an on-disk format change, so it does not fall under `AGENTS.md` section 5's "Ask first" column. It is the kind of small, reversible choice that section 4 delegates.

---

## Considered options

1. Keep `pip`/`venv`, add a `requirements-dev.txt` produced by `pip freeze` as a manual lockfile substitute.
2. Switch to `uv` for dependency resolution, virtual environment creation, and running dev commands, keeping `pyproject.toml` as the single source of dependency declarations and adding a committed `uv.lock`.
3. Switch to Poetry.

---

## Decision

We will use option 2. `uv lock` generated `uv.lock`, now committed at the repository root. `uv sync --extra dev --extra sources` replaces `python -m venv .venv && pip install -e ".[dev]"` as the setup command, still producing a `.venv` at the same path so nothing else in the repo (scripts, editor config, this machine's shell profile) needs to know the difference. `AGENTS.md` section 2's install row is updated to the `uv` command.

Option 1 was rejected because a hand-maintained `requirements-dev.txt` drifts from `pyproject.toml` the first time someone edits one file and forgets the other, and `pip freeze` output is harder to review in a diff than `uv.lock`.

Option 3 was rejected because it would replace the build backend (`hatchling`, set in `pyproject.toml`'s `[build-system]`) as well as the dev workflow, a larger change than this task calls for. `uv` layers on top of the existing `pyproject.toml` without touching the build backend.

---

## Consequences

**Positive**

- Every install, human or CI, resolves the same dependency versions from `uv.lock`.
- Faster installs, which matters most for CI, run on every push and pull request.
- `AGENTS.md` section 2 now documents one command (`uv sync --extra dev --extra sources`) instead of a `python -m venv` step plus a `pip install` step.

**Negative**

- Contributors without `uv` installed need to install it first. `uv` is a single static binary with a documented one-line install script, so this is a small addition to `CONTRIBUTING.md`'s eventual setup instructions, not a new category of friction.
- `uv.lock` is another generated file to keep in sync. `uv lock --check` in CI catches drift between `pyproject.toml` and the lock before it reaches a contributor.

**Follow-on work**

- The CI workflow (`TASKS.md` P10, next item) should use `uv` directly, for example via the `astral-sh/setup-uv` GitHub Action, rather than reintroducing a `pip` step.
- `.pre-commit-config.yaml` (`TASKS.md` P10) should invoke `ruff`, `ruff format --check`, and `mypy` through `uv run` so the pre-commit environment matches the locked versions instead of whatever is on the contributor's `PATH`.

---

## Confirmation

Verified with a clean-checkout simulation: copied the repository to a scratch directory, removed any existing `.venv`, ran `uv sync --extra dev --extra sources`, then ran `pytest` (249 passed), `ruff check .` (all checks passed), and `mypy src/turnbreak` (no issues found in 25 source files) from that freshly synced environment.

---

## More information

- `uv` documentation: https://docs.astral.sh/uv/

---

## Related documents

- [`TASKS.md`](../../TASKS.md) P10, the delegated decision this ADR resolves.
- [`AGENTS.md`](../../AGENTS.md) section 2, updated to the `uv sync` command.
