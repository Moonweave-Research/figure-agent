# Issue 100F - Advisory-Vs-Blocking Aesthetic Language

Status: completed on main in commit `52855e1`

Depends on:

- Issue 97 operator-facing aesthetic integration
- Issue 100B guided entrypoint and explanation UX
- Issue 100C final-readiness preset
- Issue 100E reference-learning template

## Problem

The plugin now has many useful quality signals: deterministic build gates,
host-vision critique, journal-grade scores, aesthetic levers, top-tier audits,
SVG-polish readiness, reference-learning metrics, human art-direction gates,
accepted/golden gates, and publication gates.

The remaining operator confusion is not that these signals are missing. It is
that a user or agent can still read "complete", "ready but improvable",
"human_gate_required", or "continue_tikz" and fail to see which authority is
speaking:

- deterministic plugin gate;
- host LLM critique gate;
- human domain/art-direction decision;
- release/golden human decision;
- SVG editor handoff;
- advisory improvement only;
- no remaining action.

This is why the plugin can feel like it says "done" while the user still sees
possible polish, or like an aesthetic score should block release when it is only
advisory.

## Goal

Add a compact, shared decision-boundary explanation to next-action UX so
`/fig_status`, `/fig_loop`, `/fig_drive`, and downstream queue/run consumers can
distinguish blocking gates from optional aesthetic guidance without changing the
existing action vocabulary.

## Contract

Additive JSON field:

```yaml
decision_boundary:
  schema: figure-agent.decision-boundary.v1
  kind: deterministic_plugin_gate | host_vision_gate | human_decision | release_decision | polish_handoff | advisory_only | none
  authority: plugin | host_llm | human | release_operator | svg_editor | none
  blocks_progress: true | false
  blocks_release: true | false
  explanation: "<one sentence>"
```

Rules:

- Deterministic commands such as compile/export/adjudicate are
  `deterministic_plugin_gate`.
- `/fig_critique` requirements are `host_vision_gate`.
- Missing critique reference inputs are not a host-vision gate: status-level
  `critique_reference_missing` stays a human/spec decision, while driver-level
  `reference_missing` stays a deterministic workflow blocker until the declared
  path/file is fixed.
- `human_gate_required` is `human_decision`.
- accepted/golden/final publication roll-forward is `release_decision`.
- SVG polish handoff is `polish_handoff`.
- Ready-but-improvable candidates are `advisory_only`; they must not imply
  release blocking.
- Fully complete states without optional improvement are `none`.

## Scope

In scope:

- additive `decision_boundary` in shared `next_action_summary`;
- copy that boundary into `/fig_drive.operator_guidance` for plain-language UX;
- docs/tests proving advisory improvement does not become a gate.

Out of scope:

- changing action vocabulary;
- changing release, accepted, golden, critique, or SVG gates;
- making aesthetic scores blocking;
- changing fixture source or generated artifacts;
- rewriting queue/run execution.

## Review Questions

1. Can a user tell whether a suggestion is mandatory or optional?
2. Can an agent tell who must act next?
3. Do advisory aesthetic signals stay non-blocking?
4. Do human art-direction gates still stop release/polish?
5. Does the field stay additive for existing consumers?

## Implementation Notes

- `scripts/next_action_summary.py` emits `decision_boundary` for all shared
  next-action summaries without changing the existing `action`,
  `safe_command`, `blocking_source`, or evidence fields.
- `scripts/fig_driver_guidance.py` copies that object into
  `operator_guidance`; direct helper callers also get a fallback boundary.
- Ready-but-improvable, safe-to-ship results are explicitly `advisory_only`, so
  optional aesthetic polish cannot masquerade as a release blocker.
- Reference-missing states are separated from host critique execution so an
  agent does not ask the host LLM to critique without the declared reference
  input.

## Review / Verification Log

Review 1 - contract/schema correctness:

- Found and fixed a reference-missing misclassification where `run_critique`
  could be labeled `host_vision_gate` even though the reference path/file must
  be fixed first.

Review 2 - backward compatibility and scope containment:

- Found and fixed a fallback-path gap where `operator_guidance()` could lose
  `advisory_only` when called directly with `ready_but_improvable` metadata but
  without a precomputed `next_action_summary`.

Review 3 - test coverage and docs readiness:

- Confirmed the change is additive, docs describe the new field without
  authorizing mutation, and targeted tests cover deterministic, host, human,
  release, reference-missing, and advisory-only boundaries.

Targeted verification:

- `uv run pytest -q tests/test_next_action_summary.py tests/test_fig_driver.py tests/test_fig_queue.py tests/test_fig_run.py`
  - `154 passed`
- `uv run ruff check scripts/next_action_summary.py scripts/fig_driver_guidance.py tests/test_next_action_summary.py tests/test_fig_driver.py`
  - passed
- `git diff --check`
  - clean

Final verification:

- `uv run pytest -q`
  - `1614 passed, 3 skipped, 1 xfailed, 6 warnings`
- `uv run ruff check .`
  - passed
- `git diff --check`
  - clean
- `claude plugin validate .claude-plugin/plugin.json`
  - passed
- `claude plugin validate .`
  - passed
- `claude plugin validate ../../.claude-plugin/marketplace.json`
  - passed
