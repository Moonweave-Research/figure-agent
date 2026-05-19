# Issue 8D: Fig Drive Loop Output Ingestion

**Date:** 2026-05-19 KST
**Status:** completed
**Depends on:** Issue 8B, Issue 8C

## Problem

`/fig_drive` is now the canonical dry-run traffic controller, but it only reads
the current `/fig_status` vector. After it recommends `run_fig_loop`, a user or
outer agent can run `/fig_loop --json`, but a later `/fig_drive` call does not
yet ingest that loop evidence. This can make the driver repeat `run_fig_loop`
instead of surfacing the actual stop boundary recorded by the loop, such as one
patch handoff, an ambiguous patch selection, or a human gate.

## Goal

Teach `/fig_drive` to read the latest valid verify-only `/fig_loop` run for the
same fixture and translate its loop stop state into one driver action, without
mutating any figure, build, export, polish, accepted, or git state.

## Public Behavior

The driver remains dry-run only and keeps `schema: figure-agent.driver.v1`.
Additive top-level fields are allowed because v1 consumers must ignore unknown
fields.

When review-mode prerequisites are closed and a latest valid current loop run
exists:

- `patch_target_recommended` or `active_subregion_recommended` with a
  `patch_handoff` becomes `action: patch_handoff_stop` and
  `stop_boundary: patch_handoff_required`.
- `ambiguous_patch_selection` becomes `action: patch_handoff_stop` and
  `stop_boundary: ambiguous_patch_selection`.
- `human_gate_required` or `escalation_level: human_review_required` becomes
  `action: human_gate_stop` and `stop_boundary: human_gate_required`.
- `status_action_required` whose recommendation asks for `--force-golden`
  becomes `action: release_blocked` and
  `stop_boundary: force_golden_required`.
- `no_actionable_findings` or `verify_only_complete` becomes
  `action: complete`.
- Other loop states stay conservative: recommend `run_fig_loop` again.
- Loop runs older than the current source, authoring context, critique,
  adjudication, publication audit, theory guard, subregion log, or build
  evidence are ignored.

The output may include a compact `loop_checkpoint` object with the paths and
selected loop fields that caused the recommendation.

## Non-Goals

- Do not execute `/fig_loop`.
- Do not edit source, adjudication, exports, polish artifacts, accepted state,
  golden state, `.scratch/`, or git state.
- Do not implement auto-patch or safe auto-patch.
- Do not change `/fig_loop` output schema.
- Do not consume non-latest, stale, or malformed loop runs as authority.

## Test Plan

- Latest patch handoff loop run routes to `patch_handoff_stop`.
- Latest ambiguous patch loop run routes to `patch_handoff_stop` with
  `ambiguous_patch_selection`.
- Latest human gate loop run routes to `human_gate_stop`.
- Latest clean loop run routes to `complete`.
- Malformed or wrong-fixture loop runs are ignored.
- Loop runs older than adjudication evidence are ignored.
- Driver dry run remains non-mutating.

## Verification

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_driver.py
uv run pytest -q tests/test_fig_driver.py tests/test_fig_loop.py tests/test_status.py
uv run ruff check scripts/fig_driver.py tests/test_fig_driver.py
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```
