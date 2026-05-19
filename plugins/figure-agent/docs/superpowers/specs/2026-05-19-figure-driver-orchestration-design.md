# Figure Driver Orchestration Design

**Date:** 2026-05-19
**Status:** design ready

## Purpose

`figure-agent` now has strong individual gates for compile, critique, export,
adjudication, loop evidence, final artifacts, and accepted-mode validation. The
remaining workflow gap is not another low-level gate. The gap is that agents do
not have one canonical driver contract that decides which gate to run next.

Without a driver, agents improvise:

- one agent keeps looping inside `/fig_compile`
- another jumps to `/fig_export`
- another stops and asks for `/fig_critique`
- another runs `/fig_loop` and assumes it is an executor

This creates inconsistent behavior even when the underlying gates are correct.
The driver contract should make `/fig_status` the authoritative traffic
controller and prevent agents from choosing build/export/critique/polish paths
from memory or preference.

## Current State

The active commands are intentionally separated:

- `/fig_compile` builds and checks the editable source.
- `/fig_critique` is host-orchestrated vision critique and writes
  `critique.md`.
- `/fig_adjudicate` scaffolds `critique_adjudication.yaml`.
- `/fig_loop` is verify-only; it records state, stop reason, patch handoff,
  evidence, and next action. It does not compile, export, critique, patch,
  accept, polish, or mutate git state.
- `/fig_export` regenerates export artifacts and enforces reference-grounded
  critique freshness before export.
- `/fig_status` is read-only stage inference. It reports `Next:`,
  `render_state`, `critique_state`, `export_state`, `workflow_ready`,
  `release_ready`, and final-artifact state.
- `/fig_closeout` is read-only post-patch checklist.

This separation is safe, but it leaves no single command or skill rule that
answers: "from the current filesystem state, what should this agent do next,
and when must it stop for host/human work?"

## Design Decision

Add a driver protocol before adding any mutating full automation.

The driver must be a conservative orchestration layer over existing gates:

```text
read /fig_status
  -> follow exactly one next action
  -> run only commands that are safe for the selected mode
  -> stop at host-LLM, human, patch, or final-polish handoff boundaries
  -> rerun /fig_status after each completed action
  -> never infer a different path from chat-only context
```

The first implementation should be **dry-run / advisory first**, not a hidden
auto-runner. It may later gain opt-in execution modes after dogfood evidence
shows stable behavior.

## Terminology

Use these terms consistently:

- **Driver**: the canonical layer that reads `/fig_status` and chooses the next
  command or stop condition.
- **Authoring loop**: repeated source edits and `/fig_compile` until render is
  fresh enough for review.
- **Review loop**: compile, critique, adjudication, loop evidence, and one
  patch target at a time.
- **Export loop**: export regeneration after build and critique prerequisites
  are satisfied.
- **Polish loop**: final-artifact SVG polish after generated export is current.
- **Release loop**: accepted/golden/final-artifact validation before treating a
  fixture as final.

Do not call `/fig_loop` an executor. It is a verify-only checkpoint.

## Driver Modes

The driver should support explicit modes so agents do not silently choose a
different depth of work.

### `authoring`

Purpose: fast source/build iteration.

Allowed:

- inspect `/fig_status`
- recommend or run `/fig_compile`
- stop when render is fresh or when source authoring is required

Forbidden:

- export
- critique
- adjudication
- accepted/golden mutation
- SVG polish

### `review`

Purpose: close the normal figure loop before release.

Allowed:

- inspect `/fig_status`
- run `/fig_compile` when needed
- request or hand off `/fig_critique` when critique is missing/stale
- run `/fig_adjudicate` when critique is fresh and adjudication is missing/stale
- run `/fig_loop` to produce evidence
- stop on exactly one patch handoff or a human gate

Forbidden:

- hidden source editing inside the driver
- automatic host-LLM critique authoring without the host step
- final SVG polish
- accepted/golden mutation

### `release`

Purpose: prove final readiness.

Allowed:

- inspect `/fig_status`
- run missing compile/export checks when prerequisites allow
- run accepted/golden validation
- report `release_ready` / `final_ready`

Forbidden:

- changing `accepted`
- forcing golden export overwrite
- creating or modifying polished SVG
- hiding unresolved critique/adjudication findings

### `polish`

Purpose: guide final-artifact polish only after generated export is current.

Allowed:

- inspect `/fig_status`
- verify generated export freshness
- require current critique/adjudication before final promotion
- hand off SVG polish using the existing final-artifact protocol
- validate `polish/svg_polish_manifest.yaml`

Forbidden:

- editing generated `exports/`
- treating SVG polish as source repair
- setting `accepted: true`
- bypassing semantic backport when `backport_required` or
  `semantic_change_declared` is true

## Driver State Machine

```text
START
  -> run /fig_status <name>
  -> if stage 0/1: stop with scaffold/source-authoring action
  -> if render_state is MISSING or STALE: compile action
  -> if critique_state is REFERENCE_MISSING: stop for reference repair
  -> if critique_state is MISSING or STALE: stop for /fig_critique handoff
  -> if export_state is MISSING or STALE and mode permits export: /fig_export
  -> if critique is FRESH and adjudication missing/stale: /fig_adjudicate
  -> run /fig_loop for evidence
  -> if patch_handoff exists: stop with exactly one patch target
  -> if human gate: stop for human/domain review
  -> if mode is polish and final artifact not fresh: follow polish handoff
  -> if mode is release and final_ready false: report blocking gate
  -> if workflow/release target reached: complete
```

The state machine must use structured fields where possible, not free-text
parsing alone. `/fig_status` currently lacks JSON output, so Issue 8A should
decide whether to add status JSON before building any runner.

## Required Stop Boundaries

The driver must stop instead of continuing when:

- `/fig_critique` requires host LLM vision review.
- reference inputs are missing.
- more than one patch target is actionable.
- `patch_handoff` is non-null; the driver must not patch in this issue.
- `human_gate_status` is required.
- accepted/golden roll-forward would be needed.
- `--force-golden` would be needed.
- SVG polish requires semantic backport.
- current mode forbids the next command.

## Public Behavior Target

The first public surface should be one of:

```bash
uv run python3 scripts/fig_driver.py <name> --mode review --goal "<goal>" --dry-run
```

or a slash-command equivalent:

```text
/fig_drive <name> --mode review --goal "<goal>" --dry-run
```

The first slice may be docs-only plus skill-command clarification if that is
the lowest-risk step. If code is implemented, prefer dry-run JSON output first.

The output should include:

- fixture name
- selected mode
- current `/fig_status` vector
- selected next action
- command to run, if safe
- stop boundary, if any
- reason
- forbidden actions for this state

## Non-Goals

- Do not make `/fig_loop` auto-edit.
- Do not make `/fig_loop` run compile/export/critique implicitly.
- Do not bypass host LLM critique.
- Do not mutate accepted/golden state.
- Do not implement SVG editing.
- Do not create an all-powerful command that hides which layer is failing.

## Success Criteria

Issue 8A is successful when a future agent can answer these questions without
guessing:

- Which command is the canonical first check? `/fig_status`.
- Is `/fig_loop` the executor? No, it is a verify-only checkpoint.
- When do we stay in build loop? Only in authoring mode or when render is not
  fresh.
- When does critique gate fire? Before export when reference-grounded critique
  is required, and before review-loop closure when critique is missing/stale.
- When does export gate fire? After build is fresh and critique prerequisites
  are closed or intentionally skipped for draft export.
- When does polish gate fire? Only after generated export is current and
  `spec.yaml.final_artifact.kind: polished_svg` opts in.
- When must the agent stop for a human or host LLM? At critique, ambiguous
  patch selection, human gate, accepted/golden promotion, or semantic polish
  backport.

