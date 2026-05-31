# Issue 95 - Loop Improve Orchestrator

Status: implemented; pending commit

Type: workflow UX, loop orchestration, guided autonomy

Depends on:

- Issue 70 - operator-grade guided autonomy
- Issue 94 - ready improvement discovery mode

Design:
`docs/superpowers/specs/2026-06-01-loop-improve-orchestrator-design.md`

## Problem

Users naturally operate figure improvement as repeated critique and patch
loops, but the plugin exposes many low-level commands. "Use figure-agent to fix
this" is currently under-specified: the agent may not know whether to start
with status, compile, critique, adjudication, loop, export, SVG polish, or
human review.

## Goal

Introduce `/fig_improve` as the loop-centered entry point for one fixture. It
should run safe mechanical steps through existing `/fig_run`, then stop at the
first non-automatic boundary with a clear actor and instruction.

The first implementation must not imply that one Python process can complete
host vision, source patching, SVG editing, or human decisions. It is a safe
loop wrapper: repeat `/fig_improve` after the required actor completes the
boundary action.

## Hard Scope

Implement:

- `scripts/fig_improve.py`
- `commands/fig_improve.md`
- tests for host boundary, complete, optional improvement, plan-only, and
  repeated boundary behavior
- `SKILL.md` entry pointing users/agents at `/fig_improve` when they ask for
  repeated figure improvement

Do not implement:

- host-vision critique authoring inside Python
- source auto-patching
- SVG editing
- force-golden
- release mutation
- accepted/publication mutation
- resume from old journals

## Acceptance Criteria

- `/fig_improve <name> --goal "<goal>" --max-loops N` emits
  `figure-agent.improve.v1` JSON.
- With `--execute`, it only executes whatever `/fig_run` would already execute.
- It stops after the first host/human/patch/SVG/release/optional-improvement
  boundary even when `--max-loops` is greater than one.
- Host critique stops with `final_required_actor: host_llm`.
- Complete with Issue 94 candidates stops as
  `optional_improvement_available`.
- Complete without candidates stops as `complete`.
- Human/release/SVG/patch boundaries are surfaced without mutation.
- Full tests, lint, diff-check, and plugin validation pass.

## Implementation Notes

Implemented `/fig_improve` as a boundary-stopped wrapper over
`fig_run.run_workflow()`. It keeps `fig_driver.py` and `fig_run.py`
authoritative and adds only an additive `figure-agent.improve.v1` summary.

The command may continue to another internal cycle only when `/fig_run` ends at
`max_steps_exceeded`; it stops immediately at host critique, human, patch, SVG,
release, and optional-improvement boundaries. This preserves the intended
manual/host gates while giving agents one command to start the repeated
improvement workflow.

## Verification

- `uv run pytest -q tests/test_fig_improve.py` -> 8 passed
- `uv run pytest -q tests/test_fig_improve.py tests/test_fig_run.py tests/test_fig_driver.py` -> 128 passed
- `uv run pytest -q` -> 1552 passed, 3 skipped, 1 xfailed
- `uv run ruff check .` -> passed
- `git diff --check` -> clean
- `claude plugin validate .claude-plugin/plugin.json` -> passed
- `claude plugin validate .` -> passed
- `claude plugin validate ../../.claude-plugin/marketplace.json` -> passed

## Review Notes

1. Contract/safety: clean. `/fig_improve` delegates to `/fig_run`, executes no
   broader command allowlist, and cannot cross host/human/release boundaries.
2. UX: fixed during review. Early docs made `--max-loops` sound like one call
   could complete host critique or source patching; docs now state that the
   operator reruns `/fig_improve` after the required actor acts.
3. Test coverage: clean. Tests cover host boundary, internal continuation after
   safe step cap, complete, optional improvements, plan-only mode, repeated
   boundary, CLI JSON, and invalid max loops.
