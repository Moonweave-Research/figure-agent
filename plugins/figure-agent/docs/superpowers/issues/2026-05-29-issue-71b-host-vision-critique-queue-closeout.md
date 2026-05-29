# Issue 71B - Host-Vision Critique Queue Closeout

Status: proposed

Depends on: Issue 71A

Type: HITL

## Problem

Several production candidate fixtures are blocked at stale or missing
reference-grounded critique. This is not safe AFK work: `/fig_critique` requires
the host vision model to read the rendered figure, audit crops, clash
candidates, reference images, and print-scale outputs.

## Goal

Refresh the host-vision critique queue fixture by fixture, lint the resulting
critique, scaffold or repair adjudication, and record the next `/fig_loop`
state without source edits or hidden release decisions.

## Scope

In scope:

- For each 71A-assigned stale critique fixture, run `/fig_critique <name>` with
  all required images/crops read by the host session.
- Run `uv run python3 scripts/critique_lint.py <name>`.
- Run `/fig_adjudicate <name>` only when scaffolding is safe; repair existing
  adjudication explicitly when needed.
- Run `/fig_loop <name> --goal "<issue-71-goal>"` after critique/adjudication
  is current.
- Record whether the refreshed critique exposes a plugin blind spot, a source
  figure issue, or a human gate.

Out of scope:

- Fabricating critique content without host vision.
- Editing `.tex` source.
- Export/golden/publication mutation.
- SVG polish editing.
- Treating numeric score as release authority.

## Acceptance

- Each attempted fixture has a milestone row with critique schema, lint result,
  adjudication state, loop stop reason, and next owner.
- Any critique-lint failure is fixed or recorded as a controlled blocker.
- Any plugin defect found during critique is split into a follow-up issue with
  the evidence path.
- No generated build/export artifacts or accepted/golden state are staged.
- Verification includes targeted critique/adjudication/loop tests plus full
  `uv run pytest -q` before closeout.

## Review Questions

1. Did the host actually read required high-zoom, print-scale, clash, and
   reference evidence before writing critique?
2. Did stale critique get refreshed without silently mutating source or release
   state?
3. Are unresolved findings visible through adjudication and loop evidence?
4. Did any repeated blind spot deserve a plugin issue rather than a fixture
   patch?
