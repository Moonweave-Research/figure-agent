# Reference-Conditioned Authoring Loop Decision

**Date:** 2026-05-16
**Pilot:** `examples/fig1_overview_v2_pair_001_vault`
**Decision:** integrate manual artifacts into critique brief, then add narrow accepted/sub-region parsers

## Decision

The manual protocol changed critique and acceptance decisions enough to justify
two narrow tooling changes:

1. make `scripts/critique_brief.py` include `authoring_contract.md`,
   `reference/reference_pack.md`, `authoring_plan.md`, `theory_guard.md`, and
   the live sub-region active-set summary when those files exist;
2. make `check_golden_artifacts.py --require-accepted` reject `accepted: true`
   unless theory and provenance/publication evidence are explicitly passing.

Do not implement a reference-pack parser, schema-level sub-region model, cropper,
or auto-segmentation yet. The current evidence supports parsing the live
Markdown active-set log, but not a durable `spec.yaml` schema.

## Evidence From This Loop

- Export initially blocked on `critique_stale`, so the normal export path did
  enforce the review loop.
- `scripts/critique_brief.py` did not surface the new contract/reference-pack
  artifacts, and its briefing parser reported empty author-intent/physics
  sections for this Korean/numbered brief shape.
- The host-written `critique.md` used the new manual artifacts to avoid
  reopening the old Panel A network-vs-linear conflict as a MAJOR finding.
- The manual theory guard kept the audit focused on scientific BLOCKERs rather
  than compile success.
- The sub-region log supplied live evidence. Its active target set is empty
  after v7, which is enough to parse and preserve the current active-set state,
  but not enough to design a schema or crop pipeline.

## Manual Artifacts Changed Decisions

They changed critique decisions:

- Panel A network reference is now an anti-reference, not an open
  structural target.
- No new BLOCKER/MAJOR theory finding was raised.
- Visual QA warnings were adjudicated as MINOR visual-polish risks rather than
  acceptance blockers.

They did not change patch decisions in this loop:

- No TikZ patch was applied.
- Existing dirty `briefing.md` and `.tex` edits were preserved.
- The final decision stayed `accepted: false`.

## Implemented Tooling Slice

Implemented a narrow `critique_brief.py` enhancement:

1. If `authoring_contract.md` exists, include its Theory Invariants,
   Forbidden Transfers, Source Limitations, and Acceptance Rubric sections in
   the critique brief.
2. If `reference/reference_pack.md` exists, include the reference-role table and
   anti-reference boundaries.
3. If `theory_guard.md` exists, include the guard table as explicit
   physics/narrative checks.
4. If `authoring_plan.md` exists, include Patch Order and Human Checkpoints.
5. If `subregion_iteration_log.md` exists, parse its Active Target Set and
   Iteration Log tables and include active targets plus observed patch units.
6. Preserve backward compatibility: figures without these files must produce
   the same critique brief shape as before.

Implemented an accepted-fixture gate enhancement:

1. Require `theory_guard.md` in accepted mode.
2. Reject BLOCKER rows whose evidence does not start with a passing status.
3. Require `QUALITY_AUDIT.md` to include provenance/publication compliance and
   `submission-safe: true` before `accepted: true` can pass.

## Deferred States

- `no code yet, manual protocol unstable`: rejected. The protocol exposed a
  concrete generated-brief gap.
- `implement sub-region schema/crop pipeline`: deferred until more active-patch
  cycles and cross-fixture evidence exist.
- `implement a stronger theory-guard checker`: deferred because current guard
  evidence is prose-level and requires human/source/render adjudication; the
  accepted gate only checks explicit BLOCKER pass/fail status.
- `implement reference-pack parser`: deferred; include prose first, then decide
  whether structure is stable enough to parse.

## Residual Low Risk

- The current visual warnings are MINOR and remain accepted residual risk only
  for this milestone decision. They must be revisited before any
  `accepted: true` or submission-safe claim.
- Target-venue publication policy was not supplied; the audit explicitly blocks
  submission-safe status until that future input exists.
