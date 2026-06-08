---
description: Loop-centered one-fixture improvement orchestrator. Runs safe mechanical steps through /fig_run and stops at host, human, patch, SVG, release, or optional-improvement boundaries.
---

Run a bounded improvement loop for one figure.

**Usage**: `/fig_improve <name> --goal "<goal>" [--execute] [--max-loops N] [--json | --format json]`

Run from the plugin root:

```bash
fig-agent improve <name> --goal "<goal>"
fig-agent improve <name> --goal "<goal>" --execute --max-loops 10
fig-agent improve <name> --goal "<goal>" --format json
```

`/fig_improve` is the loop-centered entry point for "use figure-agent to keep
improving this figure" requests. It does not replace `/fig_drive`; it calls the
existing bounded `/fig_run` workflow and summarizes where the loop stopped.
Output is JSON by default; `--json` and `--format json` are accepted as
compatibility no-ops.

This command is boundary-stopped. It may run more than one internal cycle only
when safe mechanical work hits the per-cycle step cap. It stops immediately at
host critique, human, patch, SVG polish, release, or optional-improvement
boundaries. After the required actor acts, rerun `/fig_improve`.

## What It Can Do

With `--execute`, it can only perform the same deterministic shell actions that
`/fig_run` already allows:

- compile;
- missing adjudication scaffold;
- verify-only `/fig_loop`;
- safe draft export.

It cannot author host vision critiques, patch source, edit SVG, force golden,
set accepted state, or mutate release/publication state.

## Stop Boundaries

The JSON result uses `schema: figure-agent.improve.v1` and includes:

- `cycles[]` — embedded `/fig_run` payloads; usually one unless the safe
  mechanical step cap was reached;
- `final_stop_reason` — why improvement stopped;
- `final_required_actor` — who must act next;
- `next_operator_instruction` — one concrete next step;
- `ready_improvement_summary` — optional Issue 94 candidates, when present.

Common final stop reasons:

- `host_boundary` — run `/fig_critique <name>` in the host vision session.
- `optional_improvement_available` — the figure is safe, but optional
  non-blocking candidates remain.
- `complete` — no required plugin action remains.
- `command_failed` — inspect stderr and rerun live status/driver.
- `repeated_boundary` — the same boundary repeated; inspect before continuing.

## Recommended Prompt

Use this when the user asks to loop repeatedly:

```text
Run /fig_improve <name> --goal "close structural, visual, design, and journal-polish issues" --execute --max-loops 10.
Stop at host critique, human gate, patch handoff, SVG polish, release, or optional-improvement boundaries.
Do not auto-patch source or mutate accepted/golden state.
```

If the result stops at `host_boundary`, run `/fig_critique <name>` and then
rerun `/fig_improve`. If it stops at `optional_improvement_available`, choose
at most one candidate from `ready_improvement_summary.candidates` before
continuing.
