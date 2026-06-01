# Issue 63C - Aesthetic Metric Surfacing In Status And Loop

Status: completed; merged to main

Depends on: Issue 63B non-model aesthetic metrics pack

## Problem

A metrics file is not useful if it stays hidden in `build/`. The loop needs to
surface metric freshness, severe divergence, and the next recommended action in
the same places users and agents already check: `/fig_status`, `/fig_loop`, and
the critique brief.

At the same time, metric surfacing must not become a release shortcut or a
false authority over physics, author intent, accepted state, or human gates.

## Goal

Make aesthetic metrics visible and actionable without letting them silently
unlock or mutate anything.

## Scope

In scope:

- Add status notes for missing, stale, invalid, and severe-divergence metric
  states when the fixture opts in.
- Add a compact `/fig_loop` summary such as
  `reference_aesthetic_metrics_summary`.
- Route severe divergence to an action-required or human-review path depending
  on the configured threshold profile.
- Include metric summary in the critique brief so the host LLM must explain or
  link any severe divergence.
- Preserve existing export, release, accepted, golden, SVG-polish, and
  publication gates.

Out of scope:

- Changing the underlying metrics.
- Making all metrics blocking by default.
- Replacing journal-grade assessment.
- Auto-patching source.

## Acceptance

- [x] `/fig_status` surfaces opted-in metric states.
- [x] `/fig_loop` records metric state in iteration JSON and stdout summary.
- [x] Severe divergence cannot silently pass as "all clear".
- [x] Missing opt-in preserves current behavior.
- [x] Stale metrics cannot make a current critique look fresh.
- [x] Tests cover pass, warn, severe, missing, stale, invalid, and no-opt-in
  cases.

## Implementation Notes

- `scripts/reference_aesthetic_metrics.py` now exposes
  `reference_aesthetic_metrics_summary()` for read-only consumers.
- The summary is opt-in only: fixtures without `reference_learning` preserve
  existing status/loop stdout behavior.
- Summary states are `missing`, `invalid`, `stale`, `passed`, `warning`,
  `severe_divergence`, and `skipped`.
- `/fig_status` adds `reference_aesthetic_metrics` plus
  `reference_aesthetic_metrics_*` notes/checks when the fixture opts in.
- `/fig_loop` records `reference_aesthetic_metrics_summary` and routes
  `severe_divergence` to `human_gate_required`; warning/pass states remain
  advisory.
- `critique_brief.py` emits a `## Reference Aesthetic Metrics` section when
  metrics are opted in, so host critique sees the same summary.
- `quality_manifest.py` includes `build/reference_aesthetic_metrics.json` in
  critique freshness inputs when present.

## Verification

- `uv run pytest -q tests/test_reference_aesthetic_metrics.py tests/test_status.py tests/test_fig_loop.py tests/test_critique_brief.py tests/test_quality_manifest.py`
  - 304 passed.
- `uv run ruff check scripts/reference_aesthetic_metrics.py scripts/status.py scripts/fig_loop.py scripts/fig_loop_records.py scripts/critique_brief.py scripts/quality_manifest.py tests/test_reference_aesthetic_metrics.py tests/test_status.py tests/test_fig_loop.py tests/test_critique_brief.py tests/test_quality_manifest.py`
  - All checks passed.

## Review Questions

1. Is surfacing visible enough that users do not miss severe divergence?
2. Are existing hard gates preserved?
3. Is the route conservative while thresholds are still being calibrated?
4. Does the summary explain what to do next rather than just reporting a number?
