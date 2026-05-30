# SVG Polish Trigger Semantics

**Status:** completed

## Problem

Issue 71D proved the SVG polish route was conservative, but it also exposed an
operator ambiguity: `editorial_art_direction.tikz_vs_svg_polish_trigger` could
return `verdict: pass` while still recommending `continue_tikz`. That is safe,
but it did not explain the remaining source-level lever or the positive reason
needed before SVG polish can start.

## Implemented Contract

Schema/rubric `figure-agent.critique.v1.14` /
`figure-agent.critique-rubric.v1.14` now applies only to advanced
aesthetic/reference contracts:

- `aesthetic_intent.yaml` schema `figure-agent.aesthetic-intent.v2`
- `spec.yaml.journal_art_direction_playbook`
- `critique_reference_pack.yaml.reference_learning`

Default fixtures and legacy aesthetic intent v1 stay on v1.10 to avoid turning
normal critique refreshes stale just because the trigger contract was hardened.

For v1.14 critiques, `tikz_vs_svg_polish_trigger.recommended_path` still
selects the route. The matching rationale field is required:

| Route | Required field |
|---|---|
| `continue_tikz` | `remaining_tikz_lever` |
| `ready_for_svg_polish` | `svg_polish_candidate_reason` |
| `semantic_backport_required` | `semantic_backport_reason` |
| `needs_human_art_direction` | `human_art_direction_reason` |

`verdict` grades whether the routing judgment is supported. It does not grant
SVG polish by itself.

## Loop/Driver Surfacing

`/fig_loop` copies the selected route rationale into
`editorial_art_direction_summary.polish_route_detail`.

`/fig_driver --mode polish` preserves the existing hard rule:
`ready_for_svg_polish` is necessary before SVG polish can start. For
`continue_tikz`, the driver appends the route detail to
`svg_polish_readiness.blocking_reason` and
`blocking_items[].route_detail`; for positive readiness, it copies the
candidate reason into top-level `svg_polish_readiness.route_detail`.

## Backward Compatibility

- v1.13 and older critiques remain parseable without route-specific detail.
- Default brief output remains v1.10 unless an advanced opt-in is present.
- v1.14 still includes the v1.13 crop anomaly accounting contract.
- No source, export, accepted, golden, or polished-SVG artifact is mutated.

## Tests Added

- v1.14 schema validation accepts route detail and rejects missing route detail.
- `critique_lint.py` rejects a v1.14 trigger without the required route field.
- `critique_brief.py` emits v1.14 only for reference-learning, journal
  playbook, or aesthetic-intent v2 contracts.
- `quality_manifest.py` freshness expects v1.14 only for the same advanced
  contracts.
- `/fig_loop` and `/fig_driver --mode polish` surface route detail without
  weakening the readiness gate.

## Reviews

### Review 1 - Contract/Schema/Freshness

Initial implementation made v1.14 the global default, which would have made
legacy/default critiques stale unnecessarily. Fixed by making v1.14 opt-in for
advanced aesthetic/reference contracts only and preserving v1.10 default
freshness.

### Review 2 - Backward Compatibility/Scope

Legacy v1.13 critiques remain valid without route details. The new route
fields are required only under v1.14. The driver remains dry-run and the loop
remains verify-only.

### Review 3 - Integration Readiness

Brief, schema validator, lint, freshness, loop summary, and polish driver now
agree on the same route-specific field mapping. Command docs were updated so
operators know that `verdict: pass` is not a polish start signal.

## Verification

- `uv run pytest -q tests/test_critique_brief.py tests/test_quality_manifest.py tests/test_critique_schema_validator.py tests/test_critique_lint.py tests/test_fig_driver_editorial.py tests/test_fig_loop.py tests/test_status.py tests/test_sync_critique_adjudication.py`
  -> 496 passed.
- Targeted `uv run ruff check ...` -> all checks passed.
- `git diff --check` -> clean.

Full-suite verification passed at closeout before commit.
