# Issue 100B - Guided Entrypoint And Explanation UX

Status: implemented

Type: operator workflow, command contract, UX explanation

## Problem

The plugin has the right workflow pieces, but operators can still ask:

- which command should I run first;
- why did the driver say `complete`;
- who must act next when a boundary is reached.

Before this issue, `/fig_drive` exposed machine-readable action fields and a
compact `next_action_summary`, but it did not always give one plain
operator-facing instruction.

## Decision

Do not add another slash command. `/fig_drive` remains the canonical dry-run
router and now emits additive `operator_guidance` for every mode.

The guidance names:

- `state`: `next_action`, `host_boundary`, `human_boundary`,
  `polish_boundary`, `blocked`, or `complete`;
- `required_actor`: `workflow_agent`, `host_llm`, `human`,
  `release_operator`, `svg_editor`, or `none`;
- `next_step`: one plain instruction.

This is explanatory only. It does not authorize mutation, reinterpret
`safe_command`, or replace `status_explanation`, `audit_evidence`,
`loop_checkpoint`, `closeout`, or `next_action_summary`.

## Implemented Contract

- `operator_guidance.schema`: `figure-agent.operator-guidance.v1`
- `complete` states say no required plugin action remains for the selected
  mode.
- host-vision critique boundaries name `host_llm`.
- human and release boundaries name the appropriate human actor and do not
  expose hidden source, accepted, golden, SVG, or publication mutations.
- runnable shell/slash recommendations continue to be selected by the existing
  top-level `action` and `safe_command`.

## Tests

Covered in `tests/test_fig_driver.py` through final-mode tests that assert:

- stale render final mode explains strict compile as a workflow-agent action;
- tracked-golden final mode explains release-operator force-golden approval;
- complete final mode explains that no required plugin action remains.

## Non-Goals

- No hidden source patching.
- No automatic host critique authoring.
- No accepted/golden/publication mutation.
- No replacement of `/fig_status`, `/fig_run`, or `/fig_improve`.
