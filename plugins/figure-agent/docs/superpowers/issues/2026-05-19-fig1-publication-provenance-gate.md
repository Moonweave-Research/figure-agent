# Issue: Fig1 Publication Provenance Gate

**Date:** 2026-05-19 KST
**Status:** open
**Fixture:** `examples/fig1_overview_v2_pair_001_vault`

## Problem

`fig1_overview_v2_pair_001_vault` now passes the technical dogfood gates needed
before final human acceptance:

- render fresh
- critique fresh
- tracked golden export refreshed
- golden basic artifact gate passing
- accepted-mode failures reduced to `accepted: true` and `submission-safe: true`

The remaining blocker is not a TikZ or plugin defect. It is a publication
provenance decision: the target venue is not declared and no human author has
recorded provenance/disclosure responsibility.

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

Only after the human inputs above are recorded:

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
