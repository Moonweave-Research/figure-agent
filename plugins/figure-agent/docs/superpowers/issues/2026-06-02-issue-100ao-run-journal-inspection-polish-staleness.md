# Issue 100AO - Run Journal Inspection and SVG Polish Evidence Staleness

Status: completed

Type: continuation UX, inspection trace freshness, SVG polish evidence freshness

## Problem

Issue 100AN made `fig_run_journal.py` stale against newer optional critique
evidence such as `external_vision_review.yaml`, reference packs, aesthetic
intent, and detector reports. A follow-up review found two remaining optional
evidence families that can still change the correct continuation route after a
journal stops:

- `inspection_trace.yaml`, which records whether host/subagent/human inspection
  actually read the expected artifacts;
- SVG polish sidecars under `polish/`, including recipe, delta images,
  semantic diff, audit, final polish manifest, and polished SVG.

If either family changed after an interrupted `/fig_run`, the previous journal
could still look `available` even though the review evidence had moved.

## Decision

Extend the non-authoritative journal staleness sweep to include:

- `inspection_trace.yaml`
- `polish/svg_polish_recipe.yaml`
- `polish/aesthetic_delta/{before.png,after.png,diff.png,delta_manifest.json}`
- `polish/svg_semantic_diff.json`
- `polish/svg_polish_audit.md`
- `polish/svg_polish_manifest.yaml`
- `polish/<fixture>.polished.svg`

The helper still does not replay old commands, validate the sidecars, or mutate
fixture state. It only forces the operator back to live `/fig_status` and
`/fig_drive` when the continuation context is no longer current.

## Tests

Covered by:

- `tests/test_fig_run_journal.py::test_latest_journal_summary_marks_inspection_trace_newer_as_stale`
- `tests/test_fig_run_journal.py::test_latest_journal_summary_marks_svg_polish_sidecar_newer_as_stale`
