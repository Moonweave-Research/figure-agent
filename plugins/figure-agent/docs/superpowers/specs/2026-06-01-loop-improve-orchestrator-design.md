# Loop Improve Orchestrator Design

Date: 2026-06-01

Parent issue:
`docs/superpowers/issues/2026-06-01-issue-95-loop-improve-orchestrator.md`

## Problem

`figure-agent` now has strong lower-level pieces, but the user-facing workflow
is still too fragmented for the way figures are actually improved. In practice,
LLMs rarely finish a journal-grade schematic in one pass. The effective pattern
is a repeated loop:

1. inspect current state;
2. run safe mechanical steps;
3. refresh host critique when needed;
4. record a loop checkpoint;
5. patch one target or stop at a human/SVG/release boundary;
6. repeat until the remaining work is subjective or not worth another pass.

Today the user must explicitly decide whether to run `/fig_status`,
`/fig_drive`, `/fig_run`, `/fig_critique`, `/fig_adjudicate`, or `/fig_loop`.
That makes "use figure-agent to improve this" ambiguous for both humans and
LLMs.

## Goal

Add a conservative top-level **improvement orchestrator** that treats looped
review as the default operating shape while preserving all existing boundaries.

The orchestrator should answer:

- What did the plugin try automatically?
- Where did it stop?
- Which actor must act next?
- Is this a host-vision, human, patch, SVG-polish, release, or optional
  improvement boundary?
- If the figure is complete, are there still non-blocking improvement
  candidates?

## First Slice

Implement `/fig_improve` as a bounded wrapper over existing `/fig_run` behavior.
It should not become a new route selector. It delegates each cycle to
`fig_run.run_workflow()` and summarizes the final boundary.

The first slice is **boundary-stopped**, not a hidden autonomous designer. It
may continue to another internal cycle only when `/fig_run` exhausts its safe
step cap (`max_steps_exceeded`). It must stop immediately when the next actor is
host vision, a human, patch handoff, SVG polish, release/golden handling, or an
optional-improvement decision. After that actor acts, the operator reruns
`/fig_improve`.

The first slice may execute only the same deterministic actions that
`/fig_run` already allows:

- compile;
- missing adjudication scaffold;
- verify-only `/fig_loop`;
- safe draft export.

It must stop at:

- host critique boundary;
- human gate;
- patch handoff;
- SVG polish handoff;
- accepted/golden/release gate;
- command failure;
- repeated no-progress action;
- optional improvement available from Issue 94;
- max loops after repeated safe mechanical cycles.

## Contract

```yaml
schema: figure-agent.improve.v1
fixture: <name>
mode: review
goal: "<goal>"
execute: true | false
max_loops: <int>
cycles:
  - index: 1
    run: <fig_run payload>
    stop_reason: host_boundary | complete | optional_improvement_available | boundary | command_failed | max_steps_exceeded
    required_actor: host_llm | workflow_agent | human | svg_editor | release_operator | none
final_stop_reason: <same closed set>
final_required_actor: <same actor set>
final_action: <driver action>
final_stop_boundary: <driver stop boundary or null>
ready_improvement_summary: <copied from final driver, if present>
next_operator_instruction: "<one concrete instruction>"
```

The contract is additive and does not change `figure-agent.run.v1` or
`figure-agent.driver.v1`.

## Actor Semantics

- `host_llm`: run `/fig_critique` in a host vision session.
- `workflow_agent`: a normal agent can continue with another safe mechanical
  pass.
- `human`: user/domain decision required.
- `svg_editor`: SVG polish handoff, not source repair.
- `release_operator`: accepted/golden/final release decision.
- `none`: no next action required.

## Non-Goals

- Do not auto-author critique.md.
- Do not auto-patch source.
- Do not generate patches.
- Do not edit SVG.
- Do not force golden.
- Do not change accepted/release/publication state.
- Do not implement resume/replay from old journals.
- Do not replace `/fig_drive` as the canonical next-action selector.

## Edge Cases

1. `fig_run` stops at host critique.
   - Expected: final actor `host_llm`, instruction to run `/fig_critique`.

2. `fig_run` stops at complete with no improvement candidates.
   - Expected: final actor `none`, stop `complete`.

3. `fig_run` stops at complete with
   `ready_improvement_summary.state: ready_but_improvable`.
   - Expected: stop `optional_improvement_available`, no auto patch.

4. `fig_run` stops at patch handoff.
   - Expected: actor `workflow_agent` or `human` depending on driver handoff,
     but no automatic source mutation.

5. `fig_run` stops at human gate.
   - Expected: actor `human`, no loop continuation.

6. `fig_run` stops at release/golden gate.
   - Expected: actor `release_operator`, no force-golden.

7. Plan-only mode.
   - Expected: one cycle, no command execution, explain what would happen.

8. Same stop repeats.
   - Expected: stop rather than spinning until max loops.

9. `max_loops < 1`.
   - Expected: controlled CLI error.

10. Host/human/release/SVG/optional-improvement boundary appears on the first
    cycle.
    - Expected: stop after one cycle even when `--max-loops` is greater than
      one.

## Review Questions

- Does this make the common "loop 10 times" user intent easier without hiding
  host/human boundaries?
- Does this avoid becoming a second driver?
- Does this preserve `/fig_run` safety predicates?
- Does it explain why the loop stopped in one sentence?
- Does it expose Issue 94 optional candidates instead of saying only
  "complete"?
