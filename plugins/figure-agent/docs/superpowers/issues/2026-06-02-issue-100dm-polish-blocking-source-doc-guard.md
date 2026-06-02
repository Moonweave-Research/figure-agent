# Issue 100DM - Polish Blocking-Source Doc Guard

Status: implemented in this slice

Type: documentation contract, release-contract guard, SVG polish queue

## Problem

Issue 100CR made `/fig_queue --mode polish`
`svg_polish_blocking_sources` merge blocker sources from both
`svg_polish_gate.blocking_items` and `svg_polish_readiness.blocking_items`.

The row documentation already named both sources, but the `summary` contract
still said `by_svg_polish_blocking_source` appears "when polish readiness
reports blocker sources." That was stale and could make operators or future
agents think gate-only blockers such as `driver_blocker` or
`driver_prerequisite` are not part of the summary contract.

## Scope

- Update `/fig_queue` summary documentation to say gate/readiness blocker
  sources.
- Add a release-contract guard so the doc cannot drift back to readiness-only
  wording.

## Non-goals

- Do not change queue row fields or summary behavior.
- Do not change SVG polish gate semantics.
- Do not add execution or mutation behavior.

## Verification

- TDD red:
  - `uv run pytest -q tests/test_release_contract.py::test_fig_queue_docs_describe_svg_blocking_sources_from_gate_and_readiness`
  failed because the summary section did not mention gate/readiness.
- Green:
  - The same test passed after the doc correction.

## Review Notes

1. **Contract accuracy** - Documentation now matches the existing merged
   gate/readiness blocking-source projection.
2. **Regression guard** - Release-contract coverage prevents future doc edits
   from narrowing the summary contract back to readiness-only wording.
3. **Scope containment** - This is docs/test hardening only; no runtime behavior
   changed.
