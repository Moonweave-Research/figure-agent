# Issue 8B: Dry-Run Figure Driver

**Status:** completed in commits `c0453aa`, `38f3b89`.
**Design:** `docs/superpowers/specs/2026-05-19-figure-driver-orchestration-design.md`
**Predecessor:** `docs/superpowers/issues/2026-05-19-issue-8a-figure-driver-protocol.md`

## Problem

Issue 8A made the driver contract explicit in docs, but agents can still ignore
or misread the docs. The next step is a machine-readable advisory command that
starts from `/fig_status` state and returns exactly one recommended next action
without mutating the fixture.

This closes the practical ambiguity between build-only loops, critique
handoffs, export gates, `/fig_loop` checkpoints, SVG polish, and release
readiness.

## What to build

Add a dry-run-only driver:

- `scripts/fig_driver.py`
- `commands/fig_drive.md`
- `tests/test_fig_driver.py`

Initial CLI:

```bash
uv run python3 scripts/fig_driver.py <name> --mode review --goal "<goal>" --dry-run
```

`--dry-run` is required in Issue 8B. The command must return advisory JSON and
must not run compile/export/critique/adjudication/loop commands.

## Public behavior

The JSON summary must include:

- `schema`: `figure-agent.driver.v1`
- `fixture`
- `mode`: `authoring | review | release | polish`
- `goal`
- `status`: compact `/fig_status` vector
- `action`: one canonical action name
- `safe_command`: command string when a user/agent may run the next command
- `stop_boundary`: canonical stop identifier or `null`
- `reason`
- `forbidden_actions`: list of stable identifier strings
- `may_execute`: always `false` in Issue 8B

## Action vocabulary

Use the action names from Issue 8A:

- `create_or_fix_source`
- `run_compile`
- `run_critique`
- `run_adjudicate`
- `run_fig_loop`
- `run_export`
- `patch_handoff_stop`
- `human_gate_stop`
- `polish_handoff_stop`
- `release_blocked`
- `complete`

Do not add synonyms in Issue 8B.

## Stop-boundary identifiers

Use the canonical strings from Issue 8A:

- `host_llm_critique_required`
- `reference_missing`
- `ambiguous_patch_selection`
- `patch_handoff_required`
- `human_gate_required`
- `accepted_or_final_ready_required`
- `force_golden_required`
- `semantic_backport_required`
- `mode_forbidden_action`

If no stop boundary applies, return `null`.

## Mode behavior

### `authoring`

- Missing/stale render -> `run_compile`
- Fresh render -> `complete`
- Critique/export/release/polish actions are forbidden

### `review`

- Missing source -> `create_or_fix_source`
- Missing/stale render -> `run_compile`
- Missing reference -> `reference_missing`
- Missing/stale critique with fresh render -> `run_critique`
- Fresh critique with missing/stale adjudication -> `run_adjudicate`
- Prerequisites closed -> `run_fig_loop`
- Patch/human gate output from an optional loop summary must stop, not patch

### `release`

- Missing/stale render or export may recommend safe prerequisite commands
- `release_ready: true` -> `complete`
- `release_ready: false` after prerequisites -> `release_blocked`
- Accepted/golden mutation is forbidden

### `polish`

- Missing/stale render or export may recommend prerequisite commands
- Generated export current and no polished opt-in -> `polish_handoff_stop`
- Polished final artifact `FRESH` -> `complete`
- Polished final artifact `BLOCKED` -> `semantic_backport_required`
- SVG editing is forbidden to the driver itself

## Hard scope

Do not implement:

- non-dry-run execution
- source patching
- SVG editing
- host-LLM critique authoring
- export regeneration
- adjudication file writing
- `/fig_loop` execution as part of the driver
- accepted/golden mutation
- git mutation

The command may import `status.infer_stage()` and may inspect existing files.
It must not write under `examples/<name>/`, `build/`, `exports/`, `polish/`, or
`.scratch/`.

## Acceptance criteria

- [ ] `fig_driver.py` requires `--dry-run`.
- [ ] `fig_driver.py` prints JSON with the public fields above.
- [ ] Every mode returns exactly one action.
- [ ] Missing/stale render maps to `run_compile` where the mode permits it.
- [ ] Reference/critique gaps stop at critique handoff instead of export.
- [ ] Review mode reaches `run_fig_loop` only after render and critique
  prerequisites are closed.
- [ ] Release mode reports `release_blocked` instead of mutating accepted state.
- [ ] Polish mode starts only after generated export is current.
- [ ] Tests prove dry-run does not mutate fixture files.
- [ ] Existing status, loop, and export tests still pass.

## Out of scope

- Adding a full executor.
- Adding `--execute-safe`.
- Making `/fig_loop` mutate or run commands.
- Changing accepted gate semantics.
- Changing SVG polish manifest schema.

