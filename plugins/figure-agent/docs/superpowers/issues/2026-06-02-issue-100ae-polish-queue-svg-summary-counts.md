# Issue 100AE - Polish Queue SVG Summary Counts

Status: implemented

Type: operator workflow, SVG polish triage, queue summary

## Problem

Issue 100AD made `/fig_queue --mode polish` copy SVG polish gate/readiness
fields into individual rows. That fixed per-fixture visibility but left
corpus-level triage weaker than it needed to be: the queue summary still did
not say how many fixtures were `ready`, `blocked`, `continue_tikz`, or blocked
by a specific SVG-readiness source.

## Goal

Aggregate the SVG polish row fields already copied from `/fig_drive` so an
operator can see dominant polish blockers from the queue summary without
opening every row or per-fixture driver JSON.

## Scope

In scope:

- aggregate `svg_polish_gate_state`;
- aggregate `svg_polish_recommended_path`;
- aggregate unique row-level `svg_polish_blocking_sources`;
- document the additive summary fields.

Out of scope:

- changing SVG polish readiness policy;
- promoting real fixtures to `ready_for_svg_polish`;
- changing row fields from Issue 100AD;
- changing command execution, export, accepted/golden, publication, source, or
  SVG artifact mutation behavior.

## Implemented Behavior

When rows contain the relevant polish fields, `summary` may include:

- `by_svg_polish_gate_state`
- `by_svg_polish_recommended_path`
- `by_svg_polish_blocking_source`

The fields are omitted when there is no SVG-polish data, preserving non-polish
queue output.

## Review Cycles

1. **Contract correctness** - PASS. Summary counts are derived from row fields
   already copied from `/fig_drive`; no readiness reinterpretation is added.
2. **Scope containment** - PASS. The queue remains read-only and does not make
   polish rows executable.
3. **Operator readiness** - PASS. A corpus-level polish queue now shows the
   dominant gate/path/blocker classes without per-fixture JSON inspection.

## Verification

- `uv run pytest -q tests/test_fig_queue.py`
- `uv run ruff check scripts/fig_queue.py tests/test_fig_queue.py`
- `git diff --check`
