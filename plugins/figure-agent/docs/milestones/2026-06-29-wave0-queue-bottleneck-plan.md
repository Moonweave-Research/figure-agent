# Wave 0 Queue Bottleneck Plan

Date: 2026-06-29

## Scope

Wave 0 is a repo-local, read-only planning slice for the current figure-agent
fixture corpus. It does not compile, export, patch, accept, force golden state,
or edit figure sources. Its purpose is to make the next bottleneck visible from
live `/fig_queue` and `/fig_status`-derived driver state before any operator
chooses an execution wave.

The diagnostic question is: are fixtures blocked by mechanical/tool execution,
host critique, human acceptance, missing reference/context, or template/style
judgment? Wave 0 must answer that before the agent edits figures.

## Live command

Run from `plugins/figure-agent`:

```bash
fig-agent queue --mode review --goal "Wave 0 bottleneck scan" --json
```

The JSON output includes `bottleneck_report` with schema
`figure-agent.queue-bottleneck-report.v1`. The report is derived from the
filtered queue rows, which are themselves produced by `/fig_drive` over live
status inference. It summarizes:

- total row and error counts;
- dominant actions;
- dominant first status blockers;
- dominant required actors;
- dominant blocking sources;
- `by_bottleneck_category` across five root-cause buckets:
  `mechanical_tool`, `host_critique`, `human_acceptance`,
  `reference_context`, and `template_style`;
- `bottleneck_categories[]` entries with definition, count, example fixtures,
  and top signals;
- command-plan counts for executable, blocked, and mode-complete rows.

## Reading the report

Do not treat checked-in counts as product truth. The queue is a live read of the
current worktree, and counts change when generated artifacts, critiques, exports,
or acceptance files appear. During the 2026-06-29 team run, clean-worktree and
source-worktree snapshots diverged because generated artifacts differed; that is
expected. The checked-in contract is the category taxonomy and command, not a
static row count.

Use this priority order when reading `bottleneck_report`:

1. If `mechanical_tool` dominates and `command_plan.executable > 0`, run a
   bounded `/fig_queue_run` plan over deterministic `workflow_agent` rows.
2. If `reference_context` dominates, fix missing/stale reference paths, briefing
   inputs, or context packs before asking the host LLM for critique.
3. If `host_critique` dominates, refresh `/fig_critique` outputs and sync
   adjudication; do not auto-apply visual judgment.
4. If `template_style` dominates, create or update explicit style/template/SVG
   polish handoff artifacts before editing source or polished SVG.
5. If `human_acceptance` dominates, stop for explicit acceptance, publication,
   release, or golden-state review.

## Implementation waves

Wave 0 - Visibility and taxonomy:

- Add `bottleneck_report` and five-bucket category counts to `/fig_queue`.
- Keep the command read-only and test the taxonomy independent of current
  fixture state.
- Success: one JSON report can distinguish mechanical/tool, host critique,
  human acceptance, reference/context, and template/style bottlenecks.

Wave 1 - Mechanical/tool freshness:

- Use `/fig_queue_run` plan-only first for `workflow_agent` rows.
- Execute only deterministic safe commands after reviewing the plan.
- Success: source/render/export freshness blockers shrink without acceptance or
  golden-state mutation.

Wave 2 - Reference/context and host critique:

- Repair missing references, briefing context, and context packs before critique.
- Refresh host critiques and adjudication where queue rows require `host_llm`.
- Success: critique blockers shrink and remaining rows expose concrete
  adjudication or visual-improvement work.

Wave 3 - Template/style foundation:

- Convert repeated aesthetic/style problems into explicit template, reference,
  or SVG-polish handoff artifacts.
- Avoid treating subjective style judgment as implicit source mutation.
- Success: style rows name a reusable artifact or human scope decision instead
  of a vague "make it prettier" loop.

Wave 4 - Human acceptance and release:

- Handle accepted, final-ready, publication, provenance, and golden-state gates
  only with explicit human/release-operator approval.
- Success: release rows close without implicit `--force-golden` or hidden
  accepted-state mutation.

## Execution boundary

Allowed next step: inspect `bottleneck_report`, then decide whether to run a
bounded `/fig_queue_run` plan for deterministic `workflow_agent` rows.

Forbidden in Wave 0: accepted/golden mutation, source edits, unreviewed export
mutation, TeX execution as part of this plan document, or plugin-side model/API
calls.
