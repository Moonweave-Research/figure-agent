# Issue 8A: Figure Driver Protocol

**Status:** open
**Design:** `docs/superpowers/specs/2026-05-19-figure-driver-orchestration-design.md`

## Problem

Agents currently treat `figure-agent` commands inconsistently. Some keep
iterating inside `/fig_compile`, some jump to `/fig_export`, some ask the user
for critique, and some expect `/fig_loop` to execute the whole loop. The
low-level gates are useful, but there is no canonical driver contract that
forces all agents to start from `/fig_status` and follow one state-derived next
action.

## What to build

Create the first driver protocol slice so future agents stop improvising the
workflow.

The lowest-risk acceptable implementation is:

- document the driver contract
- update the figure-agent skill and relevant command docs so agents know the
  canonical entry order
- add a dry-run driver command only if the implementer finds the command
  surface small enough to test safely

If code is added, it must be dry-run/advisory first. It must not edit source,
compile implicitly, export implicitly, critique implicitly, accept artifacts, or
polish SVG unless a later issue explicitly permits those operations.

## Required behavior

Every driver path must start by reading `/fig_status <name>` or the equivalent
`scripts/status.py` state vector.

The protocol must make these truths explicit:

- `figure-agent` skill is a workflow guide, not an automatic executor.
- `/fig_status` is the traffic controller.
- `/fig_loop` is verify-only evidence, not the end-to-end runner.
- `/fig_export` is where export freshness and reference-grounded critique
  prerequisites are enforced.
- SVG polish is a finalization layer after generated export freshness, not a
  build-loop step.

## Driver modes

Define these modes in the docs and, if a command is added, in its CLI:

- `authoring`: compile-focused source loop only.
- `review`: compile/critique/adjudication/loop checkpoint, one patch target at
  a time.
- `release`: accepted/golden/final-artifact readiness checks.
- `polish`: final-artifact SVG polish handoff after export is current.

Each mode must list allowed actions, forbidden actions, and stop boundaries.

## Stop boundaries

The driver must stop rather than continue when:

- host LLM critique is required
- reference inputs are missing
- `critique_adjudication.yaml` requires human review
- more than one patch target is actionable
- `/fig_loop` emits a `patch_handoff`
- accepted/golden promotion is needed
- `--force-golden` would be needed
- SVG polish declares semantic change or backport required
- the selected mode forbids the next action

## Optional code surface

If implemented in this issue, create:

- `scripts/fig_driver.py`
- `commands/fig_drive.md`
- `tests/test_fig_driver.py`

Initial CLI:

```bash
uv run python3 scripts/fig_driver.py <name> --mode review --goal "<goal>" --dry-run
```

Dry-run output should be JSON-compatible and include:

- fixture
- mode
- goal
- current status vector
- selected next action
- safe command, if any
- stop boundary, if any
- reason
- forbidden actions

## Acceptance criteria

- [ ] The design/spec explains why agents were inconsistent and what the
  canonical traffic-controller rule is.
- [ ] `skills/figure-agent/SKILL.md` says agents should start with
  `/fig_status <name>` unless the user explicitly requested a specific command.
- [ ] `/fig_loop` docs clearly say it is verify-only and not a full executor.
- [ ] `/fig_export` docs clearly say export is where critique-before-export is
  enforced.
- [ ] SVG polish docs clearly say polish starts only after generated export is
  current.
- [ ] If `fig_driver.py` is added, tests cover each mode's stop boundaries and
  prove dry-run does not mutate fixture files.
- [ ] No implementation in this issue silently patches source, exports,
  critique, accepted state, golden state, or polished SVG.

## Out of scope

- Full auto-runner.
- Auto-patching.
- Running host LLM critique automatically.
- Adding `accepted: true`.
- Force-overwriting golden exports.
- SVG editing.
- Replacing existing low-level commands.

## Implementation Decision

- Decision: docs-only
- Reason: Issue 8A's immediate blocker is agent workflow ambiguity, not
  missing low-level gate behavior. The existing commands (`/fig_status`,
  `/fig_compile`, `/fig_critique`, `/fig_adjudicate`, `/fig_loop`,
  `/fig_export`, `/fig_closeout`) already enforce the right gates; what was
  missing was a canonical traffic-controller rule and explicit mode/stop
  language so agents stop choosing the next step from memory. A docs-first
  contract lands before any dry-run driver command so that future
  implementation (if any) can be evaluated against a stable protocol that has
  been dogfooded.
- Deferred: `scripts/fig_driver.py`, `commands/fig_drive.md`, and
  `tests/test_fig_driver.py` remain deferred to a later issue after the docs
  contract is dogfooded. The action-name vocabulary in the plan
  (`create_or_fix_source`, `run_compile`, `run_critique`, `run_export`,
  `run_adjudicate`, `run_fig_loop`, `patch_handoff_stop`, `human_gate_stop`,
  `polish_handoff_stop`, `release_blocked`, `complete`) plus the per-mode
  allowed/forbidden lists in `skills/figure-agent/SKILL.md` are the contract a
  later worker should implement as dry-run/read-only JSON, with the test
  matrix in `docs/superpowers/plans/2026-05-19-figure-driver-protocol.md`
  Task 2B.

