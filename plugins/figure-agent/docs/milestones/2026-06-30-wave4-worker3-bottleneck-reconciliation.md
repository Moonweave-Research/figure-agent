# Wave 4 Worker 3 Bottleneck Reconciliation

Date: 2026-06-30

Source of truth: `.omx/context/figure-agent-wave4-bottleneck-reduction-20260630T042137Z.md`

## Scope and non-mutation boundary

This is a documentation/reconciliation slice for Wave 4 plus safe mechanical
execution. It intentionally does not mutate fixture source, accepted state,
golden exports, or publication state.

Hard boundaries preserved:

- Did not stage, revert, overwrite, or edit
  `plugins/figure-agent/examples/fig5_actuation_mechanism/fig5_actuation_mechanism.tex`.
- Did not run `/fig_export`, `--force-golden`, acceptance, publication, or golden
  roll-forward commands.
- Did not edit fixture `.tex`, `critique.md`, `critique_adjudication.yaml`,
  `spec.yaml`, `briefing.md`, `reference/`, or `exports/` files.
- Host-LLM critique rows remain host-only authority. Worker-3 produced handoff
  evidence; it did not fabricate critique/adjudication outputs.

## Entry versus worker-worktree state

Entry snapshot from the source-of-truth context:

- total rows: 14
- executable: 2
- blocked: 12
- bottleneck categories: `mechanical_tool: 8`, `host_critique: 3`,
  `reference_context: 3`
- host critique rows: `fig1_overview_v2_pair_001_vault`,
  `fig2_trap_design_space`, `fig3_resistance_mechanism`
- reference-context rows: `fig3_floating_clip_protocol`,
  `fig3_trapping_concept`, `fig4_trap_energy_diagram`
- closeout/export rows: five smoke fixtures
- source row: `_volume_shading_demo`

Initial worker-3 clean-worktree dry run:

```bash
./plugins/figure-agent/bin/fig-agent queue-run --mode review --goal Wave4-worker3-current --dry-run --json --max-fixtures 20
```

Observed before mechanical execution:

- attempted: 13
- blocked: 1
- executed_commands: 0
- planned_executable: 13
- planned_blocked: 1
- bottleneck categories: `mechanical_tool: 14`, `host_critique: 0`,
  `reference_context: 0`
- blocked row: `_volume_shading_demo` with `create_or_fix_source` and no
  `safe_command`.

Interpretation: generated build artifacts were absent in the worker worktree, so
render-missing compile freshness hid the host/reference bottlenecks seen in the
entry snapshot. Worker-3 reduced that bottleneck with deterministic compile only.

## Mechanical execution performed

Command:

```bash
./plugins/figure-agent/bin/fig-agent queue-run --mode review --goal Wave4-worker3-mechanical-execute --execute --json --max-fixtures 20
```

Result:

- attempted: 13
- blocked: 1
- executed_commands: 13
- failed: 0
- planned_executable: 13
- planned_blocked: 1

Executed compile rows:

- `fig1_overview_v2_pair_001_vault`
- `fig2_trap_design_space`
- `fig3_floating_clip_protocol`
- `fig3_resistance_mechanism`
- `fig3_trapping_concept`
- `fig4_trap_energy_diagram`
- `fig5_actuation_mechanism`
- `smoke_annotation_box_demo`
- `smoke_contrast_demo`
- `smoke_label_overlap_demo`
- `smoke_leader_line_demo`
- `smoke_panel_spacing_demo`
- `smoke_trap_demo`

Post-execution source safety check:

```bash
git status --short -- plugins/figure-agent/examples/fig5_actuation_mechanism/fig5_actuation_mechanism.tex
```

Output was empty. The fig5 source remained unmodified.

## Post-execution live queue

Command:

```bash
./plugins/figure-agent/bin/fig-agent queue-run --mode review --goal Wave4-worker3-post-execute --dry-run --json --max-fixtures 20
```

Observed after compile freshness:

- attempted: 0
- blocked: 14
- executed_commands: 0
- planned_executable: 0
- planned_blocked: 14
- bottleneck categories: `mechanical_tool: 8`, `host_critique: 3`,
  `reference_context: 3`
- actions: `run_critique: 6`, `run_export: 7`, `create_or_fix_source: 1`
- required actors: `host_llm: 6`, `workflow_agent: 8`
- stop boundaries: `host_llm_critique_required: 6`, `closeout_required: 7`

This reconciles the worker worktree back to the same bottleneck shape as the
Wave 4 entry context: compile freshness is no longer the dominant blocker; the
remaining rows are host critique, reference-context critique briefing, closeout
export, and one source-authoring row.

## Closeout/export inspection

Read-only closeout inspection was run for the seven post-execution export rows:
`fig5_actuation_mechanism` and the six smoke fixtures. Each command returned
`rc=1` with schema `figure-agent.closeout.v1` and next action
`/fig_export <fixture>`.

Worker-3 did not run export because the task only required safe deterministic
mechanical execution plus closeout/export inspection, and because the fig5 leader
source is explicitly dirty/user-owned. Exporting generated artifacts from this
worker worktree would be a separate integration decision.

## Host critique handoff reconciliation

Post-execution queue/status evidence names three stale host-critique rows:

| Fixture | Evidence | Handoff |
| --- | --- | --- |
| `fig1_overview_v2_pair_001_vault` | `render_state=FRESH`, `export_state=TRACKED_GOLDEN`, `critique_state=STALE`, `acceptance_state=ACCEPTED`, first blocker `critique_stale` | Run `/fig_critique fig1_overview_v2_pair_001_vault`; do not export or roll forward golden without explicit authority. |
| `fig2_trap_design_space` | `render_state=FRESH`, `export_state=MISSING`, `critique_state=STALE`, first blocker `critique_stale` | Run `/fig_critique fig2_trap_design_space`; then rerun queue/status before export. |
| `fig3_resistance_mechanism` | `render_state=FRESH`, `export_state=MISSING`, `critique_state=STALE`, first blocker `critique_stale` | Run `/fig_critique fig3_resistance_mechanism`; then rerun queue/status before export. |

No host-only critique file was fabricated in this slice. Rows that require
visual judgment remain handoff rows rather than hidden source/adjudication
mutation.

## Reference-context briefing audit

Post-execution queue/status evidence names three briefing-required host critique
rows:

| Fixture | Brief/spec evidence | Reference payload evidence | Reconciliation |
| --- | --- | --- | --- |
| `fig3_floating_clip_protocol` | `briefing.md` defines schematic-only 4-phase floating-clip protocol, polarity-dependent bending, floating clip during drive, vertical cantilever convention, and author-intent constraints. | `reference/` contains only `.gitkeep` in this worker worktree. | `render_state=FRESH`, `critique_state=BRIEFING_REQUIRED`; run host critique against briefing/spec and detector evidence, or promote durable reference-context artifacts before critique. |
| `fig3_trapping_concept` | `briefing.md` defines reset schematic intent, PDMS vs sulfur-polymer mechanism contrast, trap-level invariants, and author-intent constraints. | No populated `reference/` payload is present in this worker worktree. | `render_state=FRESH`, `critique_state=BRIEFING_REQUIRED`; run host critique against briefing/spec, or promote durable reference-context artifacts before critique. |
| `fig4_trap_energy_diagram` | `briefing.md`, `design.md`, and `spec.yaml` define the energy-level/DOS schematic, shallow/deep ordering, bimodal DOS alignment, and qualitative/no-numeric constraint. | `reference/` contains only `.gitkeep` in this worker worktree. | `render_state=FRESH`, `critique_state=BRIEFING_REQUIRED`; keep the `>1 eV` vs `0.74–0.80 eV` tension qualitative and resolve via host critique, not export/build mutation. |

A read-only subagent probe reported additional ignored/generated build-side
evidence in the leader root (`convention_receipt`, `physics_grounding`,
`tex_assertions`, `semantic_assertions`). Those files are absent from this clean
worker worktree and are therefore not cited as committed closure evidence here.
If the leader wants them to close reference-context rows, they should be
promoted to durable artifacts or summarized in a leader-owned audit.

## Remaining honestly blocked rows

| Row | Blocker | Actionable next step |
| --- | --- | --- |
| `_volume_shading_demo` | `create_or_fix_source`, no safe command | Narrow source-authoring task for `_volume_shading_demo.tex`, or remove/deprioritize the fixture from Wave 4 if source authoring is out of scope. |
| `fig1_overview_v2_pair_001_vault` | accepted/tracked-golden plus stale critique | Host critique refresh first; any golden roll-forward requires explicit human/release authority. |
| `fig2_trap_design_space` and `fig3_resistance_mechanism` | stale host critique | Refresh `/fig_critique` with host vision, then rerun queue/status. |
| `fig3_floating_clip_protocol`, `fig3_trapping_concept`, `fig4_trap_energy_diagram` | briefing-grounded critique missing | Run host critique against the existing briefing/spec/design context, or first promote durable reference-context artifacts if the leader requires that as a precondition. |
| `fig5_actuation_mechanism` and smoke fixtures | closeout export required | Export is deterministic for non-golden rows, but worker-3 only inspected closeout/export handoffs; run export in a follow-up integration slice if desired. |

## Verification performed

- Queue dry-run before compile: PASS — `planned_executable=13`,
  `planned_blocked=1`, `failed=0`, `executed_commands=0`.
- Mechanical execute: PASS — `executed_commands=13`, `failed=0`.
- Queue dry-run after compile: PASS — `planned_executable=0`,
  `planned_blocked=14`, with `mechanical_tool=8`, `host_critique=3`,
  `reference_context=3`.
- Fixture status inspection: PASS — `fig-agent status <fixture> --json` ran for
  the six named host/reference rows plus `fig5_actuation_mechanism` and
  `_volume_shading_demo`.
- Closeout/export inspection: PASS — `fig-agent closeout <fixture> --json`
  returned expected `next_action=/fig_export <fixture>` for fig5 and six smoke
  rows, without git-visible source/doc changes.
- Mutation check: PASS — `git status --short --
  plugins/figure-agent/examples/fig5_actuation_mechanism/fig5_actuation_mechanism.tex`
  was empty after compile execution.

## Coordination note

Coordination protocol: coordinated - boundaries checked for leader-owned fig5,
accepted/tracked-golden fig1, host-only critique authority, reference-context
handoff rows, generated closeout/export rows, and clean-worktree versus
leader-root generated-artifact divergence.
