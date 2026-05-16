# Reference-Conditioned Authoring Loop Decision

**Date:** 2026-05-16
**Pilot:** `examples/fig1_overview_v2_pair_001_vault`
**Decision:** integrate contract/reference pack into critique brief

## Decision

The manual protocol changed critique and acceptance decisions enough to justify
one narrow tooling change: make `scripts/critique_brief.py` include
`authoring_contract.md`, `reference/reference_pack.md`, `authoring_plan.md`,
and `theory_guard.md` when they exist.

Do not implement a sub-region parser, theory-guard checker, or reference-pack
parser yet. The current evidence proves that the documents are useful in the
host review loop, but it does not prove the schema or checker shape.

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
- The sub-region log supplied live evidence, but the active target set is empty
  after v7. That is not enough to design a parser.

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

## Next Implementation Slice

Implement a narrow `critique_brief.py` enhancement:

1. If `authoring_contract.md` exists, include its Theory Invariants,
   Forbidden Transfers, Source Limitations, and Acceptance Rubric sections in
   the critique brief.
2. If `reference/reference_pack.md` exists, include the reference-role table and
   anti-reference boundaries.
3. If `theory_guard.md` exists, include the guard table as explicit
   physics/narrative checks.
4. If `authoring_plan.md` exists, include Patch Order and Human Checkpoints.
5. Preserve backward compatibility: figures without these files must produce
   the same critique brief shape as before.

## Deferred States

- `no code yet, manual protocol unstable`: rejected. The protocol exposed a
  concrete generated-brief gap.
- `implement sub-region active-set parser`: deferred until more active-patch
  cycles and cross-fixture evidence exist.
- `implement theory-guard checker`: deferred because current guard evidence is
  prose-level and requires human/source/render adjudication.
- `implement reference-pack parser`: deferred; include prose first, then decide
  whether structure is stable enough to parse.

## Residual Low Risk

- The current visual warnings are MINOR and remain accepted residual risk only
  for this milestone decision. They must be revisited before any
  `accepted: true` or submission-safe claim.
- Target-venue publication policy was not supplied; the audit explicitly blocks
  submission-safe status until that future input exists.
