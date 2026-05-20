# Issue: Fig1 Publication Provenance Gate

**Date:** 2026-05-19 KST
**Status:** open; current technical recheck failed on 2026-05-20 KST
**Fixture:** `examples/fig1_overview_v2_pair_001_vault`

## Problem

`fig1_overview_v2_pair_001_vault` previously passed the technical dogfood gates
needed before final human acceptance:

- render fresh
- critique fresh
- tracked golden export refreshed
- golden basic artifact gate passing
- accepted-mode failures reduced to `accepted: true` and `submission-safe: true`

That is no longer the current repo truth after later fig1 source iterations.
The remaining blocker is still partly a publication provenance decision, but a
fresh technical recheck now also fails accepted-mode gates.

## Current Recheck — 2026-05-20 KST

Commands run from `plugins/figure-agent`:

```bash
uv run python3 scripts/status.py fig1_overview_v2_pair_001_vault
uv run python3 scripts/check_golden_artifacts.py examples/fig1_overview_v2_pair_001_vault --require-accepted
```

Observed state:

- `status.py`: render `FRESH`, critique `FRESH`, export `TRACKED_GOLDEN`,
  acceptance `NOT_ACCEPTED`, workflow/golden/release/final readiness all false.
- Next action: tracked golden artifact is stale; intentional roll-forward
  requires `/fig_export fig1_overview_v2_pair_001_vault --force-golden`.
- Accepted-mode gate failures:
  - fixture is not marked `accepted: true`;
  - rendered PDF labels missing: `high n`, `low n`;
  - source inventory too low: `surface_charge_markers 0 < 1`;
  - `QUALITY_AUDIT.md` is stale or missing;
  - `QUALITY_AUDIT.md` does not declare `submission-safe: true`.

Therefore the issue is not ready for a pure provenance closeout. It needs a
technical rebaseline or source/golden/audit update before the human publication
gate can be cleanly evaluated.

## Recheck After Issue 13 — 2026-05-20 KST

Commands rerun from `plugins/figure-agent` after the auto-adjudication policy
landed on `main`:

```bash
uv run python3 scripts/status.py fig1_overview_v2_pair_001_vault
uv run python3 scripts/check_golden_artifacts.py examples/fig1_overview_v2_pair_001_vault --require-accepted
```

Result is unchanged:

- `status.py`: render `FRESH`, critique `FRESH`, export `TRACKED_GOLDEN`,
  acceptance `NOT_ACCEPTED`, workflow/golden/release/final readiness all false.
- Next action remains `/fig_export fig1_overview_v2_pair_001_vault --force-golden`.
- Accepted-mode gate still fails on `accepted: true`, rendered labels `high n`
  and `low n`, `surface_charge_markers`, stale/missing `QUALITY_AUDIT.md`, and
  missing `submission-safe: true`.

Conclusion: Issue 13 reduces adjudication friction but does not unblock this
publication provenance gate. This issue still requires technical rebaseline
plus human provenance inputs.

## Policy Snapshot

Checked on 2026-05-18 UTC:

- Nature Portfolio AI policy:
  `https://www.nature.com/nature-portfolio/editorial-policies/ai`
  - Generative AI images/videos are not permitted for publication except narrow,
    clearly labelled cases.
  - Non-generative ML tools used to manipulate, combine, or enhance figures must
    be disclosed in the relevant caption for case-by-case review.
- ACS Publications AI policy:
  `https://researcher-resources.acs.org/publish/aipolicy`
  - AI tool use must be disclosed.
  - Graphics need figure-caption disclosure explaining how the image was created.
  - Authors are responsible for accuracy, attribution, and tool terms.
- Science-family policy:
  - Requires a final check against the official Science author guidelines before
    submission. Secondary summaries indicate AI-generated multimedia may require
    explicit editor permission, so this fixture should not be marked
    Science-ready from current evidence alone.

## Required Human Inputs

1. Target venue:
   - e.g. Nature Materials, Nature Communications, Science, ACS journal, or
     internal/non-submission only.
2. Final submitted artifact scope:
   - main-text figure, cover image, graphical abstract, supplementary figure, or
     internal draft.
3. AI/provenance declaration:
   - whether any generative AI image is included in the submitted artifact.
   - whether AI-generated images were only used as internal style references.
   - which LLM/image/vector/raster tools touched the source or design.
4. Disclosure draft:
   - figure caption disclosure if needed.
   - Methods/Acknowledgements/cover-letter disclosure if needed.
5. Human visual acceptance:
   - named author confirms the final export is scientifically accurate and not
     misleading.

## Acceptance Path

Only after the technical recheck above is resolved and the human inputs above
are recorded:

1. Update `QUALITY_AUDIT.md`:
   - target venue
   - policy URL/date
   - disclosure text
   - human provenance statement
   - `submission-safe: true` only if the target venue permits the final artifact
2. Change `spec.yaml`:
   - `accepted: true`
3. Run:
   - `uv run python3 scripts/status.py fig1_overview_v2_pair_001_vault`
   - `uv run python3 scripts/check_golden_artifacts.py examples/fig1_overview_v2_pair_001_vault --require-accepted`
   - `uv run pytest`
   - `git diff --check`

## Non-Goals

- Do not auto-decide submission safety.
- Do not claim Nature/Science readiness without target-specific policy evidence.
- Do not remove the provenance gate just because technical artifact checks pass.
