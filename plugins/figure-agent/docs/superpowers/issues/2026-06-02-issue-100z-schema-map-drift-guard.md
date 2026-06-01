# Issue 100Z - Schema Map Drift Guard

Status: implemented

Type: maintainability, schema governance, release contract

## Problem

Issue 100H/I created a schema capability matrix and module ownership map, but
it was still manually maintained. Follow-up slices added schemas such as
warning budgets, inspection traces, adjudication diff previews, SVG polish
positive harness output, detector feedback ledgers, and plugin install
freshness diagnostics. Some of those contracts were not reflected in the map.

That drift matters because new agents use the map to decide where a schema
belongs. If the map is incomplete, future work can add detached reports or
duplicate a responsibility already owned by a module.

## Goal

Add a release-contract guard that extracts `SCHEMA` / `*_SCHEMA` constants from
`scripts/*.py` and verifies that every `figure-agent.*` schema appears in
`docs/superpowers/issues/2026-06-01-issue-100hi-schema-module-map.md`.

Critique lineage entries may use the existing shorthand form (`v1.17`) in the
matrix; non-critique schemas must appear by full schema id.

## Implemented

- Added `test_schema_module_map_covers_script_schema_constants()` to
  `tests/test_release_contract.py`.
- Updated the module map for:
  - `figure-agent.warning-budget.v1`;
  - `figure-agent.adjudication-decision-diff.v1`;
  - `figure-agent.inspection-trace.v1`;
  - `figure-agent.svg-polish-positive-harness.v1`.

## Non-Goals

- No runtime schema behavior changes.
- No critique schema deprecation.
- No new schema version.
- No generated schema registry file.

## Verification

- `uv run pytest -q tests/test_release_contract.py::test_schema_module_map_covers_script_schema_constants`
  -> 1 passed after map updates.

## Review Results

1. Contract correctness: the guard checks stable script-level schema constants
   and allows existing critique lineage shorthand.
2. Scope containment: docs and release-contract tests only; no figure workflow
   or runtime gate changed.
3. Future protection: any new `figure-agent.*` schema constant now forces an
   ownership-map update before release tests pass.
