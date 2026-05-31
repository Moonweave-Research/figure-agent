# Issue 92 - Post-Issue91 Real-Fixture Migration And Operator Dogfood

Status: completed

Type: real-fixture migration, operator dogfood, post-contract validation

Depends on:

- Issue 91 - TikZ/SVG semantic near-miss audit hardening

## Problem

Issue 91 hardened the plugin kernel: crop evidence, undeclared TikZ geometry,
SVG semantic diff, and SVG delta freshness now have stronger contracts. The
unit and integration tests prove the contracts on synthetic fixtures.

The remaining risk is operational: real fixtures may now route differently
because fresh critiques with audit crops or undeclared-geometry reports require
schema `figure-agent.critique.v1.16`. That is desirable, but it must be
dogfooded deliberately so operators understand what became stale, which gates
are true human gates, and whether `/fig_status`, `/fig_drive`, `/fig_loop`, and
queue views remain usable.

## Goal

Run a non-mutating real-fixture migration pass after Issue 91 and record exactly
what the operator should do next for each production fixture.

The issue is complete when the real fixture corpus has a fresh post-Issue91
status/driver snapshot, v1.16 critique refresh needs are separated from source
figure defects, and no plugin code regression or workflow ambiguity remains
unreported.

## Production Fixture Queue

Start with the existing production-like fixtures:

- `fig1_overview_v2_pair_001_vault`
- `fig1_overview_v2`
- `golden_trap_depth_picture`
- `n3_trial_01_trap_depth`
- `n3_trial_02_actuation_sequence`
- `fig3_trapping_concept`
- `smoke_trap_demo`
- `fig5_floating_clip_mechanism`

Support/smoke folders such as `_macro_smoke`, `_snippet_smoke`,
`_polymer_variants`, `_paper_aesthetic_contexts`, and `_journal_art_direction_playbooks`
must stay out of production-readiness claims.

## Scope

In scope:

- non-mutating `fig_queue` snapshots in `review`, `release`, and `polish` modes;
- per-fixture `fig_status` and `fig_driver --dry-run` checks where needed;
- identifying which critiques must be regenerated under v1.16;
- host-vision critique refresh prompts for fixtures that are stale only because
  of Issue 91 contract changes;
- milestone evidence documenting commands, outcomes, and next human/host/agent
  actions.

Out of scope:

- editing `.tex` figure sources;
- force-golden, accepted, publication, export roll-forward, or SVG polish
  mutation;
- fabricating host-vision critiques from Codex-only context;
- adding more deterministic checkers unless the dogfood reveals a tested,
  narrow plugin defect.

## Acceptance Criteria

- [x] A milestone under `docs/milestones/` records the queue snapshot and
      fixture-by-fixture outcomes.
- [x] Every production fixture is classified as one of:
      `ready/no-op`, `host_critique_required`, `human_gate_required`,
      `release_operator_required`, `workflow_agent_mechanical`, `svg_editor`,
      or `plugin_defect`.
- [x] Any v1.16 migration need is explicit and not confused with a figure
      quality defect.
- [x] No source/export/golden/accepted/publication/SVG artifacts are mutated.
- [x] If a plugin defect is found, it is split into a narrow follow-up issue
      with tests before fixture maintenance continues.
- [x] Final verification passes:
      `uv run pytest -q tests/test_status.py tests/test_fig_driver.py tests/test_fig_queue.py tests/test_fig_loop.py`,
      `uv run ruff check scripts/status.py scripts/fig_driver.py scripts/fig_queue.py scripts/fig_loop.py`,
      `git diff --check`.

## Closeout

- Milestone:
  `docs/milestones/2026-05-31-post-issue91-real-fixture-migration.md`
- Defect fixed during dogfood:
  `docs/superpowers/issues/2026-05-31-issue-93-content-fresh-export-status-next-ux.md`
- Verification:
  - `uv run pytest -q tests/test_status.py tests/test_fig_driver.py tests/test_fig_queue.py tests/test_fig_loop.py tests/test_status_next_policy.py`
    - Result: 330 passed.
  - `uv run pytest -q`
    - Result: 1530 passed, 1 skipped, 1 xfailed.
  - `uv run ruff check .`
    - Result: all checks passed.
  - `git diff --check`
    - Result: clean.
- Protected mutation:
  no `examples/` files changed.

## Review Questions

1. Did Issue 91 create legitimate v1.16 refresh work, or did it create noisy
   false blockers?
2. Can an operator tell which command to run next without reading all issue
   history?
3. Are human/release/SVG boundaries still explicit and non-mutating?
4. Are stale-contract states separated from real drawing defects?
5. Does the fixture queue reveal another plugin-code gap that should outrank
   ordinary fixture maintenance?
