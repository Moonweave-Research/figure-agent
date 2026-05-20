# Issue 12E: Print-Scale Audit Pack

**Date:** 2026-05-20 KST
**Status:** implemented and verified
**Type:** AFK visual audit evidence
**Parent:** `2026-05-20-issue-12-critical-visual-audit-gaps.md`
**Blocked by:** Issue 12A

## What To Build

Generate reduced-scale audit images so the critique loop checks whether labels,
arrow tips, line weights, and dense sub-regions survive manuscript-scale
reading. This is evidence for `journal_polish`, `reduction_print_readability`,
and `publication_readiness`; it is not an export or acceptance mutation.

## Acceptance Criteria

- [x] Audit images include a 178 mm equivalent render.
- [x] Audit images include one conservative thumbnail-scale render.
- [x] `/fig_critique` brief lists the images and requires inspection before
  setting `journal_polish` or `publication_readiness` to `pass`.
- [x] The generated files live under `build/audit_crops/` or a similarly
  ephemeral build subdirectory.
- [x] No export, accepted, golden, final-artifact, or source file is mutated.
- [x] Tests prove deterministic file naming and brief inclusion.

## Implementation Notes

- Added deterministic `print_178mm.png` and `print_thumbnail.png` under
  `build/audit_crops/`.
- Print-scale items share the 12A audit-pack plumbing but are listed in a
  separate brief section from original-pixel high-zoom quadrant crops.
- The brief requires host inspection before passing `journal_polish` or
  `publication_readiness`; this remains evidence-only and does not mutate
  exports or acceptance state.

## Verification

- `uv run pytest -q tests/test_critique_zoom_crops.py tests/test_critique_brief.py`
  -> 40 passed.
- `uv run ruff check scripts/critique_zoom_crops.py scripts/critique_brief.py tests/test_critique_zoom_crops.py tests/test_critique_brief.py`
  -> all checks passed.
- `uv run python3 scripts/critique_brief.py examples/fig1_overview_v2_pair_001_vault | rg 'Print-Scale Audit Images|print_178mm|print_thumbnail|print_scale_unreadable|journal_polish|publication_readiness'`
  -> emitted the print-scale section, both audit image paths, and both required
  quality-axis names.
- `uv run pytest -q` -> 746 passed, 1 skipped, 1 xfailed, 5 legacy
  deprecation warnings.
- `uv run ruff check .` -> all checks passed.
- `git diff --check` -> clean.
- `claude plugin validate .claude-plugin/plugin.json` -> passed.
- `claude plugin validate .` -> passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json` -> passed.

## Blocked By

- Issue 12A, because the crop/audit-pack plumbing should be shared.
