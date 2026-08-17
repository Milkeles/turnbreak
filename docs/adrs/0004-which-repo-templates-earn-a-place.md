# ADR-0004: Which repository templates earn a place at v0.1.0

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-08-17 |
| **Deciders** | Hristo Hristov (maintainer), via agent-assisted build |

---

## Context and problem statement

P9 names six documents to write from `general-swe/foundations/` in the cloned `software-doc-templates` scratch copy: `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, a pull request template, two issue templates, and `CHANGELOG.md`. It then asks: "Decide which remaining templates earn their place for a project this size, add them, and record which you skipped and why."

`general-swe/foundations/` holds 29 templates. This ADR covers the 23 not already named by P9, plus `CODE_OF_CONDUCT.md`, which isn't in that folder at all but is referenced by the `contributing-guide.md` template as something to link rather than paste.

---

## Decision drivers

- Turnbreak has one maintainer and no on-call rotation, no deployment pipeline beyond a future PyPI release, and no second team consuming an internal interface.
- Several of the named six documents already point at some of these templates as "the place I'd normally link to but I'm skipping" (`code-review-guidelines.md`, `branching-strategy.md`, `threat-model.md`). Adding a stub for each just to satisfy a link is worse than not linking it.
- `service-readme.md` itself says the template is for an internally-owned service with an on-call rotation, and to skip that shape entirely for a published tool. The same reasoning extends to the other service-oriented templates in the set.
- Every template not added here still exists in the scratch clone, so nothing is lost. Adding one later, if the project grows a second maintainer or a real release pipeline, costs one file.

---

## Decision

Add `CODE_OF_CONDUCT.md`, adapted from the Contributor Covenant 2.1, unmodified except for the enforcement contact. `CONTRIBUTING.md` links to it, per the template's own advice not to write one from scratch.

Skip the rest. Grouped by why:

**Already covered by an existing document, under a different name.**
`architecture-overview.md` and `technical-design-document.md` → `docs/architecture.md`. `architecture-decision-record.md` → the `docs/adrs/` convention already in use, including this file. `coding-standards.md` → `AGENTS.md` sections 2 to 4.

**Assumes a team, an on-call rotation, or a deployment pipeline this project doesn't have.**
`branching-strategy.md`, `code-review-guidelines.md`, `configuration-management-plan.md`, `data-model.md`, `deployment-plan.md`, `governance.md`, `incident-postmortem.md`, `interface-control-document.md`, `onboarding-guide.md`, `runbook.md`. A one-maintainer CLI tool has no branch policy beyond what `AGENTS.md` section 4 already states, no second reviewer, no deployment beyond a release tag, and no incidents in the on-call sense, since nothing here runs as a service.

**The question it answers doesn't exist yet.**
`rfc.md` and `deprecation-plan.md` need a change large enough to need a formal design process or a deprecation window first. `glossary.md` needs jargon dense enough that inline explanation stops working, and the project doesn't have that yet. `support.md` needs a support channel distinct from GitHub issues. `CONTRIBUTING.md`'s "where to get help" section already answers this at the project's current size.

**Belongs to a later task, not this one.**
`release-notes.md` is P10's job, at v0.1.0 tag time, not P9's.

**No non-obvious threat model to write down.**
`threat-model.md`. `SECURITY.md`'s own guidance is to skip this file unless the threat model is non-obvious enough to outgrow a paragraph. Turnbreak's is one paragraph: loopback-only bind, nothing leaves the machine except each source finder's own outbound fetch. That paragraph is already in `SECURITY.md`.

**QA-process documents for a project whose test suite is the process.**
`test-strategy.md`, `test-case-specification.md`, `test-summary-report.md`. `pytest` and the coverage it already has serve this purpose directly for a project this size.

---

## Consequences

Nothing blocks re-adding any of these later. If turnbreak grows a second maintainer, `code-review-guidelines.md` and `branching-strategy.md` become worth writing. If it grows a hosted component, the deployment and incident documents would apply for the first time. Revisit this list if either happens, rather than writing the docs speculatively now.
