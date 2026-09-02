# Fig1 review lineage

This directory preserves Fig1 authoring and repair provenance. It is not a
second source of paper-artifact authority: `review/current-candidate.json` is
the only machine selector for the active child, and the external ResearchOS
artifact registry owns paper-artifact promotion.

## Active working source

- `review/current-candidate.json` now resolves to the fixture-root
  `fig1_updated_agent_redraw_v1.tex`, promoted byte-for-byte from
  `failure-first/comparable-v3-repair-c5/repaired.tex`.
- Edit the source path resolved by that pointer. Do not select a child by its
  directory order, timestamp, or an older development verdict.
- Promotion moved the source only. The figure stays `publication_acceptance:
  not_claimed` with the human gate pending; a fresh render or strict compile
  does not promote it to a paper artifact.
- `failure-first/comparable-v3-repair-c5/` is preserved as the promotion origin
  and is no longer a candidate; it must not be edited as the working source.

## Preserved historical lineage

| Location | Disposition | Why it remains in place |
|---|---|---|
| `failure-first/comparable-v1` through `comparable-v3` | comparative authoring controls | Bound prompts, packets, sources, and attribution measurements support regression and R5 evidence. |
| `failure-first/comparable-v3-repair-c1` through `comparable-v3-repair-c4` | prior repair children | They retain bounded-repair provenance and regression evidence; they are not candidates unless the pointer changes. |
| `r5-prospective-v1` through `r5-prospective-v4` | prospective R5 experiments | Their own run records are machine-blocked, review-pending, or not admitted; they do not establish a product or publication claim. |
| `closed-loop-archive/` | rejected stale-evidence attempt | It is a quarantined state-history archive and must not be resumed as a current attempt. |

## Cleanup rule

Do not delete or relocate a preserved child merely because it is older than the
current candidate. Several paths are cited by tests, evidence records, and
hash-bound packets. A future retention change must first prove that all live
references have a stable replacement, then preserve a content-addressed archive
or an explicit removal receipt. Ignored `build/` and `exports/` artifacts are
generated evidence, not legacy source files; regenerate or remove them only in
a separately authorized storage-maintenance task.
