# Issue 8A: Figure Driver Protocol

**Status:** completed in commits `5a6d65b`, `9a01b99`.
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
  contract is dogfooded.

### Future-implementer contract

A later worker building dry-run `/fig_drive` should treat the following as
contract. Sources are: state-machine sketch in
`docs/superpowers/specs/2026-05-19-figure-driver-orchestration-design.md`
§"Driver State Machine" and §"Required Stop Boundaries"; per-mode
allowed/forbidden lists in `skills/figure-agent/SKILL.md` §"Driver rule for
agents"; pytest matrix in
`docs/superpowers/plans/2026-05-19-figure-driver-protocol.md` Task 2B.

**Action vocabulary and triggers** (mode-permitting):

| Action name             | Trigger (from `/fig_status` vector)                                                                | Allowed in modes              |
|-------------------------|----------------------------------------------------------------------------------------------------|-------------------------------|
| `create_or_fix_source`  | stage `0` (directory missing) or `1` (`render_state: NOT_AUTHORED`)                                 | authoring, review             |
| `run_compile`           | `render_state: MISSING | STALE`                                                                     | authoring, review, polish     |
| `run_critique`          | `critique_state: MISSING | STALE | REFERENCE_MISSING` and `render_state: FRESH`                     | review, release, polish       |
| `run_adjudicate`        | `critique_state: FRESH` and adjudication missing/stale                                              | review                        |
| `run_fig_loop`          | `render_state: FRESH`, `critique_state: FRESH | NOT_REQUIRED`, no patch ambiguity                   | review                        |
| `run_export`            | `export_state: MISSING | STALE`, `render_state: FRESH`, `critique_state: FRESH | NOT_REQUIRED`      | release, polish               |
| `patch_handoff_stop`    | `/fig_loop` emitted a single non-null `patch_handoff`                                               | review                        |
| `human_gate_stop`       | `escalation_level: human_review_required` or `ambiguous_patch_selection`                            | review, release               |
| `polish_handoff_stop`   | mode `polish` and `final_artifact_state: NONE | MISSING` while generated export is `FRESH`          | polish                        |
| `release_blocked`       | mode `release` and `release_ready: false`                                                           | release                       |
| `complete`              | mode `authoring`: `render_state: FRESH`; review: `workflow_ready: true`; release: `release_ready: true`; polish: `final_artifact_state: FRESH` | all |

**Stop-boundary identifier set** (canonical strings the pytest matrix asserts):

| Identifier                          | Raised when                                                                |
|-------------------------------------|----------------------------------------------------------------------------|
| `host_llm_critique_required`        | `critique_state: MISSING | STALE` and host-orchestrated vision step needed |
| `reference_missing`                 | `critique_state: REFERENCE_MISSING` or panel reference image missing       |
| `ambiguous_patch_selection`         | more than one actionable patch target in `/fig_loop` output                |
| `patch_handoff_required`            | exactly one non-null `patch_handoff` and outer agent must execute the patch |
| `human_gate_required`               | adjudication or escalation demands domain review                           |
| `accepted_or_final_ready_required`  | mode `release` and `release_ready: false` or `accepted: false`             |
| `force_golden_required`             | golden roll-forward needed (`--force-golden`)                              |
| `semantic_backport_required`        | SVG polish manifest declares `backport_required: true`                     |
| `mode_forbidden_action`             | next state-machine action is disallowed by the selected mode               |

**Forbidden-action JSON shape**: `summary["forbidden_actions"]` is a list of
action-name strings drawn from the action vocabulary above, not free text.
Example for mode `polish`: `["run_critique_authoring", "edit_source",
"set_accepted", "edit_generated_export"]`. The exact polish-mode forbidden
list is the SKILL.md §"Driver rule for agents" `polish` bullet rendered as
identifiers; a later worker may add identifier strings as needed but must
keep them stable once published.

