# Fig3 Human-Gated Design Dogfood Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only fig-agent path that turns live `fig3_trapping_concept` queue/style evidence into a human-gated design dogfood packet with concrete agent-proposed choices, risks, missing-evidence blockers, and follow-up slices. The packet must not mutate source, accepted state, release state, exports, or golden artifacts.

**Architecture:** Keep the existing queue and style-direction layers authoritative. Add a thin `design_dogfood_packet` builder that consumes a queue row plus existing design-direction/style-direction data, normalizes options for human review, and exposes it through `fig-agent design-dogfood <fixture>`. The CLI reads live queue state and only writes when an explicit `--output` path is provided.

**Tech Stack:** Python 3.12 stdlib, existing `fig-agent` CLI, `fig_queue`, `design_direction_packet`, `editorial_redesign_packet`, pytest, ruff.

---

## Current Evidence

`fig-agent queue fig3_trapping_concept --mode review --json` currently reports:

- `render_state=FRESH`, `critique_state=FRESH`, `export_state=FRESH`
- `action=complete`, `first_blocker=acceptance_not_declared`
- `style_benchmark_pack_state=missing`
- `style_benchmark_comparison_state=missing`
- `design_direction_state=blocked_missing_style_pack`
- existing `style_direction_packet` already offers keep-current, bounded TikZ polish, SVG polish handoff, and full redesign choices

This means the tool should not claim the art direction is solved. It should present the current style as an acceptable manuscript baseline, while making the missing style-benchmark evidence explicit before broader redesign or SVG polish work.

## Non-Goals

- Do not edit `examples/fig3_trapping_concept/*.tex`, `spec.yaml`, acceptance flags, exports, or golden artifacts.
- Do not run external vision/image/model APIs.
- Do not generate or apply visual candidates in this slice.
- Do not treat the packet recommendation as human acceptance.
- Do not create a new source of truth that bypasses `fig_queue`.

## Data Contract

New packet schema: `figure-agent.design-dogfood-packet.v1`

Required packet fields:

- `schema`
- `fixture`
- `state`
- `mode`
- `mutation_boundary`
- `source_queue`
- `evidence_summary`
- `human_question`
- `agent_recommendation`
- `recommended_choice_id`
- `choices`
- `missing_evidence`
- `disallowed_actions`
- `follow_up`

State rules:

- `ready_for_human_choice`: queue row exists and at least one style-direction choice can be presented.
- `blocked_missing_queue_row`: no live queue row exists for the fixture.
- `blocked_invalid_fixture`: fixture name is unsafe.

Choice rules:

- Always preserve the existing style-direction choice intent when available.
- Every choice must include `id`, `label`, `agent_position`, `follow_up`, `risk`, `scope_change`, and `authorizes_mutation`.
- Every choice must have `authorizes_mutation=false`.
- The recommended choice defaults to `keep_current_style` when review is complete and no defect blocker remains.
- If style benchmark pack/comparison is missing, `full_style_redesign` remains available but its follow-up must create benchmark evidence before source or release mutation.

## Implementation Tasks

- [x] Create tests for packet builder contract.
  - Add `plugins/figure-agent/tests/test_design_dogfood_packet.py`.
  - Test a `fig3_trapping_concept` row with a `style_direction_packet` produces schema `figure-agent.design-dogfood-packet.v1`, `state=ready_for_human_choice`, `mutation_boundary=no_source_mutation`, recommended choice `keep_current_style`, and four concrete choices.
  - Test missing style benchmark states appear in `missing_evidence`.
  - Test all choices have `authorizes_mutation=false`.
  - Test empty rows return `blocked_missing_queue_row`.
  - Command: `cd plugins/figure-agent && uv run pytest tests/test_design_dogfood_packet.py -q`
  - Expected: all tests pass.

- [x] Implement `scripts/design_dogfood_packet.py`.
  - Export `SCHEMA`, `MUTATION_BOUNDARY`, `DesignDogfoodPacketError`, and `build_design_dogfood_packet(...)`.
  - Accept `fixture`, `queue`, `mode`, and optional `goal`.
  - Validate fixture names using `fig_driver.is_safe_fixture_name`.
  - Select the matching row from `queue["rows"]`.
  - Reuse `row["style_direction_packet"]["choices"]` when present; otherwise synthesize the same four bounded options from queue/design-direction state.
  - Populate `missing_evidence` from `style_benchmark_pack_state`, `style_benchmark_comparison_state`, and `design_direction_state`.
  - Keep output deterministic and JSON-serializable.

- [x] Add `fig-agent design-dogfood` CLI.
  - Add a private `_design_dogfood(argv)` function to `plugins/figure-agent/bin/fig-agent`.
  - Positional args: `name`.
  - Options: `--mode` with default `review`, `--goal` default `human-gated design dogfood`, `--output`, `--json`, `--format json`.
  - Build live queue with `fig_queue.build_queue(repo_root=_paths().workspace_root, mode=args.mode, goal=args.goal, fixtures=[name])`.
  - Print pretty JSON to stdout.
  - If `--output` is provided, write the same JSON to that path after creating parent directories.
  - Do not write anything unless `--output` is explicit.

- [x] Add CLI smoke coverage.
  - Add tests in `plugins/figure-agent/tests/test_design_dogfood_packet.py` or a focused CLI test file.
  - Invoke `bin/fig-agent design-dogfood fig3_trapping_concept --json`.
  - Assert the command exits 0, returns the new schema, includes `missing_evidence`, and does not require mutation authority.
  - Command: `cd plugins/figure-agent && uv run pytest tests/test_design_dogfood_packet.py -q`
  - Expected: all tests pass.

- [x] Run verification.
  - Command: `cd plugins/figure-agent && uv run pytest tests/test_design_dogfood_packet.py tests/test_design_direction_packet.py -q`
  - Expected: all tests pass.
  - Command: `cd plugins/figure-agent && uv run ruff check scripts/design_dogfood_packet.py bin/fig-agent tests/test_design_dogfood_packet.py`
  - Expected: no ruff findings.
  - Command: `plugins/figure-agent/bin/fig-agent design-dogfood fig3_trapping_concept --json`
  - Expected: JSON schema `figure-agent.design-dogfood-packet.v1`, `fixture=fig3_trapping_concept`, `state=ready_for_human_choice`, and `mutation_boundary=no_source_mutation`.

## Review Checkpoints

- The packet must make an agent recommendation and offer concrete options before asking the human.
- Missing evidence must be explicit; it cannot be hidden behind a generic “review needed” state.
- The CLI must not mutate source/release/golden state by default.
- A broader style redesign can be suggested only as a follow-up slice that first creates benchmark evidence.
- Human acceptance remains separate from this packet.

## Stop Condition

Stop when the new plan file exists, the packet builder and CLI are implemented, focused tests pass, ruff passes for touched files, and the live fig3 CLI smoke returns a deterministic read-only dogfood packet.
