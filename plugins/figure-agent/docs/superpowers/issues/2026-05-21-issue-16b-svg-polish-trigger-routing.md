# Issue 16B: SVG Polish Trigger Routing

**Date:** 2026-05-21 KST
**Status:** implemented
**Parent:** `2026-05-21-issue-16-editorial-illustration-quality-roadmap.md`
**Spec source:** `../specs/2026-05-21-editorial-art-direction-audit-design.md`

## Problem

Issue 16A made `/fig_critique` record
`editorial_art_direction.tikz_vs_svg_polish_trigger.recommended_path`, but the
loop runner and dry-run driver did not consume it. That left polish handoff
ambiguous: a fixture could look export-ready while the host critique had already
said the remaining problem belonged in TikZ source repair, human art-direction,
or semantic backport.

## Goal

Make the routing visible and machine-readable without adding hidden edits.
`/fig_loop` should surface a compact editorial art-direction summary, and
`/fig_drive --mode polish` should use the latest current loop checkpoint to
choose one conservative next action.

## Implemented Contract

`/fig_loop` records `editorial_art_direction_summary` when `critique.md` is
fresh schema `figure-agent.critique.v1.5` and contains a valid
`editorial_art_direction` block.

The summary includes:

- source and evidence path;
- slot count and verdict counts;
- weak/failed slots;
- high-impact blocking slots and count;
- worst verdict;
- `polish_recommended_path`;
- `polish_trigger_verdict`;
- `human_art_direction_gate_verdict`.

`/fig_drive --mode polish` keeps the existing hard gates first:

1. compile if render is missing or stale;
2. run critique if critique is missing, stale, or reference-blocked;
3. export if generated export is missing or stale;
4. stop on `final_artifact_state: BLOCKED`;
5. complete on `final_artifact_kind: polished_svg` and
   `final_artifact_state: FRESH`.

After those gates, if the latest current `/fig_loop` checkpoint has an
`editorial_art_direction_summary`, polish mode routes:

| `polish_recommended_path` | Driver action | Stop boundary |
|---|---|---|
| `continue_tikz` | `run_fig_loop` | `mode_forbidden_action` |
| `ready_for_svg_polish` | `polish_handoff_stop` | `null` |
| `needs_human_art_direction` | `human_gate_stop` | `human_gate_required` |
| `semantic_backport_required` | `polish_handoff_stop` | `semantic_backport_required` |

If `ready_for_svg_polish` conflicts with another editorial `fail`,
`needs_human`, or high-impact blocker, the human gate wins over polish handoff.

Review mode also treats editorial fail/needs-human/high-impact blockers as a
human gate, matching the existing top-tier audit handling.

## Non-Goals

- No automatic SVG editing.
- No automatic TikZ/source editing.
- No accepted/golden/final-artifact promotion.
- No mutation of generated exports, polished SVGs, or publication provenance.
- No migration of existing `critique.md` files.

## Verification Plan

- `uv run pytest -q tests/test_fig_loop_assessments.py tests/test_fig_loop_records.py tests/test_fig_loop.py tests/test_fig_driver.py`
- `uv run pytest -q`
- `uv run ruff check .`
- `git diff --check`
- `claude plugin validate .claude-plugin/plugin.json`
- `claude plugin validate .`
- `claude plugin validate ../../.claude-plugin/marketplace.json`
