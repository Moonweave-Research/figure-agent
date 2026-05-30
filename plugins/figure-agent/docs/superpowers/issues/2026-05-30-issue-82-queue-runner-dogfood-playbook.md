# Issue 82 - Queue Runner Dogfood And Operator Playbook

Status: completed

Depends on:

- Issue 77 - fixture driver queue
- Issue 78 - fixture queue actor handoff
- Issue 79 - fixture queue filters
- Issue 80 - fixture queue command plan
- Issue 81 - queue batch runner

Type: dogfood, operator documentation

## Problem

The plugin now has a multi-fixture operator stack:

- `/fig_queue`
- queue filters
- queue command plan
- `/fig_queue_run`

But the operator entry path is not yet frozen in one place. Without dogfood and
a short playbook, future sessions can still fall back to ad-hoc single-fixture
commands, or misread which actor should handle a queue row.

## Goal

Dogfood the current real fixture queue and document the canonical operator
sequence for multi-fixture work.

## Scope

- Run read-only queue and queue-run commands on the current fixture set.
- Record current actor/action/gate distribution in a milestone.
- Update command docs and the figure-agent skill with the queue-first operating
  path.
- Keep execution plan-only for this issue; do not mutate `.tex`, exports,
  accepted/golden/publication state, or generated artifacts.

## Non-Goals

- No host critique refresh.
- No source edits.
- No `/fig_queue_run --execute` dogfood in this slice.
- No release/golden approval.
- No generated artifact commits.

## Acceptance

- Dogfood evidence records queue, actor filters, command plan, and queue-run
  plan-only output.
- The playbook explains:
  1. inspect whole queue;
  2. close host LLM critique rows;
  3. run workflow-agent plan-only;
  4. execute only after reviewing the plan;
  5. handle human/release/SVG gates explicitly.
- `/fig_queue`, `/fig_queue_run`, and `SKILL.md` agree on the same operating
  order.
- Docs-only verification passes.

## Implementation

Milestone:

- `docs/milestones/2026-05-30-queue-runner-operator-playbook.md`

Documented the canonical multi-fixture operator order:

1. inspect the whole queue;
2. close host LLM critique rows;
3. inspect workflow-agent command plan;
4. run queue-run in plan-only mode;
5. add `--execute` only after reviewing the plan;
6. handle human/release/SVG gates explicitly.

Dogfood covered:

- full current queue snapshot;
- actor filters for `host_llm`, `workflow_agent`, `release_operator`, and
  `human`;
- workflow-agent command plan;
- `/fig_queue_run` plan-only batch with `--max-fixtures 2`.

No source, export, accepted, golden, publication, SVG, or generated artifact
state was mutated.

## Review

1. Contract/order review: clean. The command docs, skill entry, and milestone
   describe the same queue-first flow.
2. Safety review: clean. The dogfood path used read-only queue commands and
   plan-only queue-run output.
3. Integration review: clean. Workflow-agent execution remains delegated to
   `/fig_run`; host/release/human/SVG rows remain explicit boundaries.

Verification is recorded in the milestone.

No known Issue 82 blocker remains.
