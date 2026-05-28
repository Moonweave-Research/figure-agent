# Issue 64 - Loop Summary And Export Closeout UX

Status: implemented on branch `codex/issue64-loop-closeout-ux`

Depends on: Issue 63 reference-learning and aesthetic metrics roadmap

## Problem

Issue 63 introduced critique schema `figure-agent.critique.v1.13` for
reference-learning crop anomaly accountability. The validators, lints, and
brief generator understand v1.13, but `/fig_loop` summary helpers still list
only older critique schemas. A fresh v1.13 critique can therefore contain
`journal_grade_assessment`, `top_tier_audit`, `editorial_art_direction`, and
`crop_audit_log` while `/fig_loop` surfaces those summaries as missing.

The closeout workflow has a second operational friction point: generated
`exports/<name>.svg` currently participates in `critique_input_hash` whenever it
exists. That makes routine `/fig_export` change critique freshness even for
fixtures that have not opted into polished SVG final-artifact review. Users see
this as a confusing critique -> export -> critique loop.

Finally, `/fig_status` next-action wording does not explain the distinction
between reference-grounded pre-export critique and optional final-review
critique after generated exports exist.

## Goal

Make latest critique schemas visible to `/fig_loop` and make generated-export
closeout behavior explicit without changing release, accepted, golden, or
polished-SVG gates.

## Scope

In scope:

- Add v1.13 to `/fig_loop` summary schema allowlists.
- Keep v1.13 reference calibration summaries visible.
- Keep optional v1.11/v1.12 fields visible when they appear in a v1.13
  critique.
- Stop routine generated `exports/<name>.svg` from affecting critique freshness
  unless a fixture has opted into polished SVG/final-artifact inputs.
- Clarify status next-action copy for generated export closeout.
- Add regression tests for the above behavior.

Out of scope:

- New critique schema versions.
- New visual/aesthetic detectors.
- Source figure edits.
- Auto critique, auto export, auto patching, accepted/golden mutation, or
  hidden SVG polish mutation.
- Changing polished-SVG source-set hashing.

## Acceptance

- [x] v1.13 `journal_grade_assessment` surfaces in `/fig_loop` summaries.
- [x] v1.13 `top_tier_audit`, `editorial_art_direction`, and `crop_audit_log`
  summaries surface when present.
- [x] v1.13 `reference_calibration_summary` remains visible.
- [x] v1.13 optional `aesthetic_lever_audit` and
  `journal_art_direction_playbook_audit` summaries surface when those optional
  fields are present.
- [x] Routine generated `exports/<name>.svg` does not change
  `critique_input_hash` for non-polished fixtures.
- [x] Polished-SVG opt-in or existing polish-layer evidence still includes
  generated export SVG in critique hash inputs.
- [x] `/fig_status` next-action wording explains pre-export critique and
  post-export final review without implying hidden automation.
- [x] Targeted tests, full pytest, ruff, diff check, and plugin validation pass.

## Implementation Notes

- Added `figure-agent.critique.v1.13` to `/fig_loop` assessment allowlists for
  quality axes, top-tier audit, editorial art direction, crop audit, reference
  calibration summary, optional aesthetic levers, and optional journal
  playbook summaries.
- Changed critique input hashing so routine generated `exports/<name>.svg` is
  ignored for non-polished fixtures. It remains a critique hash input when
  `spec.yaml.final_artifact.kind: polished_svg` opts into polished-SVG
  final-artifact review or when polish-layer evidence already exists.
- Clarified `/fig_status` and `/fig_export` wording so users can distinguish
  pre-export reference-grounded critique from final-review snapshot critique.

## Verification

- `uv run pytest -q tests/test_fig_loop_assessments.py -k "v1_13"` - 1 passed.
- `uv run pytest -q tests/test_fig_loop_assessments.py` - 23 passed.
- `uv run pytest -q tests/test_quality_manifest.py -k "generated_export_svg"` -
  3 passed.
- `uv run pytest -q tests/test_quality_manifest.py` - 23 passed.
- `uv run pytest -q tests/test_status_next_policy.py -k "stage_3_stale_critique or stage_4_fresh_exports"` -
  2 passed.
- `uv run pytest -q tests/test_status_next_policy.py tests/test_status.py tests/test_quality_manifest.py tests/test_fig_loop_assessments.py` -
  200 passed.
- `uv run pytest -q` - 1376 passed, 1 skipped, 1 xfailed, 6 warnings.
- `uv run ruff check .` - all checks passed.
- `git diff --check` - clean.
- `claude plugin validate .claude-plugin/plugin.json` - passed.
- `claude plugin validate .` - passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json` - passed.

## Review Result

- Schema/contract review: latest v1.13 critiques now surface the same loop
  evidence as prior v1.12-compatible critiques, including optional inherited
  fields.
- Freshness review: generated exports no longer churn critique freshness for
  routine generated-export fixtures, while polished-SVG opt-in and polish-layer
  evidence still track the generated SVG source.
- Scope review: no release, accepted, golden, publication, source figure, or
  hidden automation behavior changed.

## Review Questions

1. Can a latest-schema critique still be silently hidden by `/fig_loop`?
2. Does generated export closeout avoid stale-hash churn without weakening
   polished-SVG final-artifact contracts?
3. Does the next-action wording reduce operator confusion without changing
   state-machine behavior?
4. Are release, accepted, golden, and publication gates unchanged?
