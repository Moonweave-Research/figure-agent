# Issue 6A: Critique Structural Audit Enumeration v1.1

## What to build

Extend `/fig_critique` so the host LLM cannot stay in narrow coordinate,
palette, or font-fix mode. The generated critique brief must force the host LLM
to enumerate structural completeness, label-target matching, physical
plausibility, and conceptual completeness before writing `critique.md`.

This issue introduces `figure-agent.critique.v1.1` and
`figure-agent.critique-rubric.v1.1`. A v1.1 critique must include a non-empty
`audit_enumeration` frontmatter block. Legacy v1 critiques remain parseable by
`/fig_adjudicate`; they are legacy, not malformed.

## Why now

Dogfood on `fig1_overview_v2_pair_001_vault` showed a recurring failure mode:
the host LLM found local polish issues but missed broader structural defects
such as missing real-system components, mislabeled targets, implausible cable
geometry, and incomplete apparatus context. Category names like `structural`
and `label_placement` are not enough; the brief must require enumeration.

## Acceptance criteria

- [x] `scripts/critique_brief.py` emits `## Mandatory Audit Checklists (host LLM MUST enumerate)` between `Source under review (TikZ)` and `Output format`.
- [x] The brief includes the four required checklist headers:
  - `### A. Structural Completeness Audit`
  - `### B. Label-Target Matching Audit`
  - `### C. Physical Plausibility Audit`
  - `### D. Conceptual Completeness Audit`
- [x] The output schema in the brief is bumped to `figure-agent.critique.v1.1`.
- [x] `CRITIQUE_RUBRIC_VERSION` is bumped to `figure-agent.critique-rubric.v1.1`.
- [x] `/fig_critique` command documentation matches the v1.1 schema and audit requirement.
- [x] `critique_adjudication.py scaffold` accepts legacy v1 critiques without crashing.
- [x] `critique_adjudication.py scaffold` rejects v1.1 critiques when any of the four `audit_enumeration` blocks is missing or empty.
- [x] `critique_adjudication.py scaffold` rejects malformed non-mapping audit list items.
- [x] `critique_adjudication.py scaffold` rejects unsupported `figure-agent.critique.*` schema typos instead of silently bypassing v1.1 validation.
- [x] The audit schema avoids hallucinated external citations by using bounded reference provenance values, not free-form invented literature claims.
- [x] No existing `examples/<name>/critique.md` files are migrated in this issue.
- [x] `/fig_loop`, `/fig_status`, and `/fig_export` behavior are not changed except for the intentional rubric-version freshness effect.

## Out of scope

- Migrating existing critique files to v1.1.
- Adding `audit_incomplete` as a `/fig_loop` or `/fig_status` state.
- Auto-applying audit findings.
- Calling external literature or vision APIs.
- Changing the findings schema beyond allowing audit-driven findings to remain
  in the existing `panels[].findings` and top-level `findings` lists.

## Blocked by

None - can start immediately.

## Implementation reference

Use the design spec:

- `docs/superpowers/specs/2026-05-18-critique-structural-audit-v1-1-design.md`

Use the execution plan:

- `docs/superpowers/plans/2026-05-18-critique-structural-audit-v1-1.md`
