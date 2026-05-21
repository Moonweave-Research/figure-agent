# Issue 16C: Editorial Driver Policy Extraction

**Date:** 2026-05-21 KST
**Status:** implemented
**Parent:** `2026-05-21-issue-16-editorial-illustration-quality-roadmap.md`
**Depends on:** Issue 16B

## Problem

Issue 16B correctly taught `/fig_drive --mode polish` to consume
`editorial_art_direction_summary`, but the routing policy initially lived
directly inside `fig_driver.py`. That pushed the driver further toward a large
state-machine module, which contradicts the Issue 15 architecture direction:
new policy glue should move into focused helper modules instead of growing
`fig_driver.py` and `status.py`.

## Decision

Extract editorial art-direction routing into `scripts/fig_driver_editorial.py`.
The module owns the small policy interface:

- `editorial_review_requires_human_gate(summary)`
- `editorial_polish_route(summary)`

`fig_driver.py` remains the command-facing controller. It still maps helper
routes to the existing driver action vocabulary and stop-boundary vocabulary,
but it no longer owns the editorial verdict/count/path interpretation rules.

## Contract Preserved

No public driver action names changed.
No stop-boundary identifiers changed.
No generated export, polished SVG, accepted, golden, or source mutation was
added.

The helper keeps the Issue 16B precedence rule: semantic backport wins first;
otherwise any editorial `fail`, `needs_human`, `needs_human_art_direction`, or
positive high-impact blocker triggers the human gate before
`ready_for_svg_polish` can hand off to SVG polish.

## Verification Plan

- `uv run pytest -q tests/test_fig_driver_editorial.py tests/test_fig_driver.py`
- `uv run pytest -q tests/test_fig_loop_assessments.py tests/test_fig_loop_records.py tests/test_fig_loop.py tests/test_fig_driver.py tests/test_fig_driver_editorial.py`
- `uv run pytest -q -m "not render"`
- `uv run ruff check .`
- `git diff --check`
- `claude plugin validate .claude-plugin/plugin.json`
- `claude plugin validate .`
- `claude plugin validate ../../.claude-plugin/marketplace.json`
