# Wave 4 Worker 3 Bottleneck Reconciliation

Date: 2026-06-30

Source of truth: `.omx/context/figure-agent-wave4-bottleneck-reduction-20260630T042137Z.md`

## Scope and non-mutation boundary

This is a documentation/reconciliation slice for Wave 4. It intentionally does
not mutate fixture source, accepted state, golden exports, publication state, or
leader-owned dirty work.

Hard boundaries preserved:

- Did not stage, revert, overwrite, compile, or export
  `plugins/figure-agent/examples/fig5_actuation_mechanism/fig5_actuation_mechanism.tex`.
- Did not run `/fig_export`, `--force-golden`, acceptance, publication, or golden
  roll-forward commands.
- Did not edit fixture `.tex`, `critique.md`, `critique_adjudication.yaml`,
  `spec.yaml`, `briefing.md`, `reference/`, `build/`, or `exports/` files.
- Treated host-LLM critique refresh as host-only authority unless a fresh host
  critique artifact already exists.

## Worker-worktree live queue snapshot

Command:

```bash
./plugins/figure-agent/bin/fig-agent queue-run --mode review --goal Wave4-worker3-current --dry-run --json --max-fixtures 20
```

Observed in the worker-3 clean worktree:

- attempted: 13
- blocked: 1
- executed_commands: 0
- planned_executable: 13
- planned_blocked: 1
- bottleneck categories: `mechanical_tool: 14`, `host_critique: 0`,
  `reference_context: 0`, `human_acceptance: 0`, `template_style: 0`
- executable rows are all `run_compile`:
  `fig1_overview_v2_pair_001_vault`, `fig2_trap_design_space`,
  `fig3_floating_clip_protocol`, `fig3_resistance_mechanism`,
  `fig3_trapping_concept`, `fig4_trap_energy_diagram`,
  `fig5_actuation_mechanism`, `smoke_annotation_box_demo`,
  `smoke_contrast_demo`, `smoke_label_overlap_demo`,
  `smoke_leader_line_demo`, `smoke_panel_spacing_demo`, `smoke_trap_demo`
- blocked row: `_volume_shading_demo` with `create_or_fix_source` and no
  `safe_command`.

This differs from the Wave 4 entry snapshot in the source-of-truth context,
which reported 2 executable rows and 12 blocked rows split across mechanical,
host-critique, and reference-context categories. The difference is treated as a
worktree/artifact-state divergence, not a reason to mutate accepted/golden or
fixture source state from this worker.

## Mechanical closeout/export inspection

| Fixture | Worker status evidence | Safe next action | Worker-3 decision |
| --- | --- | --- | --- |
| `fig1_overview_v2_pair_001_vault` | `render_state=MISSING`, `export_state=TRACKED_GOLDEN`, `critique_state=STALE`, `acceptance_state=ACCEPTED` | `/fig_compile fig1_overview_v2_pair_001_vault`; later host critique and explicit `--force-golden` approval would be needed before golden roll-forward | Blocked beyond compile inspection by accepted/tracked-golden boundary; no export/golden mutation. |
| `fig2_trap_design_space` | `render_state=MISSING`, `export_state=MISSING`, first blocker `render_missing` | `/fig_compile fig2_trap_design_space` | Compile is deterministic but was not executed in this documentation slice. |
| `fig3_resistance_mechanism` | `render_state=MISSING`, `export_state=MISSING`, first blocker `render_missing` | `/fig_compile fig3_resistance_mechanism` | Compile is deterministic but was not executed in this documentation slice. |
| `fig3_floating_clip_protocol` | `render_state=MISSING`, `export_state=MISSING`, first blocker `render_missing` | `/fig_compile fig3_floating_clip_protocol` | Compile is deterministic but was not executed in this documentation slice. |
| `fig3_trapping_concept` | `render_state=MISSING`, `export_state=MISSING`, first blocker `render_missing` | `/fig_compile fig3_trapping_concept` | Compile is deterministic but was not executed in this documentation slice. |
| `fig4_trap_energy_diagram` | `render_state=MISSING`, `export_state=MISSING`, first blocker `render_missing` | `/fig_compile fig4_trap_energy_diagram` | Compile is deterministic but was not executed in this documentation slice. |
| `fig5_actuation_mechanism` | `render_state=MISSING`, `export_state=MISSING`, first blocker `render_missing` | `/fig_compile fig5_actuation_mechanism` | Not executed to preserve the leader-owned dirty fig5 source boundary. |
| `_volume_shading_demo` | `render_state=NOT_AUTHORED`, first blocker `source_not_authored`, `safe_command=null` | source authoring/fix required | Honestly blocked; source mutation is outside this worker slice. |

## Host critique handoff reconciliation

The Wave 4 entry snapshot named three host-critique rows:
`fig1_overview_v2_pair_001_vault`, `fig2_trap_design_space`, and
`fig3_resistance_mechanism`.

Current worker-worktree status evidence:

- `fig1_overview_v2_pair_001_vault`: still has durable stale critique evidence.
  `critique_state=STALE`; freshness mismatches include `critique_input_hash`,
  `rubric_version`, `generator_version`, and `schema_rubric`. Because this
  fixture is `ACCEPTED` with `TRACKED_GOLDEN` exports, worker-3 leaves the row
  blocked for host critique plus explicit golden roll-forward authority.
- `fig2_trap_design_space`: `critique_state=NOT_REQUIRED` in this worker
  worktree, but stale `critique_freshness` metadata still exists and mismatches
  the expected input hash/rubric. The actionable next step is compile freshness
  first; if the leader branch still classifies it as host-critique-blocked,
  refresh `/fig_critique fig2_trap_design_space` after render exists.
- `fig3_resistance_mechanism`: `critique_state=NOT_REQUIRED` in this worker
  worktree, but stale `critique_freshness` metadata still exists and mismatches
  the expected input hash/rubric. The actionable next step is compile freshness
  first; if the leader branch still classifies it as host-critique-blocked,
  refresh `/fig_critique fig3_resistance_mechanism` after render exists.

No host-only critique file was fabricated in this slice. Rows that require
visual judgment remain handoff rows rather than hidden source or adjudication
mutation.

## Reference-context briefing audit

The Wave 4 entry snapshot named three reference-context rows:
`fig3_floating_clip_protocol`, `fig3_trapping_concept`, and
`fig4_trap_energy_diagram`.

| Fixture | Brief/spec evidence | Reference payload evidence | Reconciliation |
| --- | --- | --- | --- |
| `fig3_floating_clip_protocol` | `briefing.md` defines schematic-only 4-phase floating-clip protocol, polarity-dependent bending, floating clip during drive, vertical cantilever convention, and author-intent constraints. | `reference/` contains only `.gitkeep` in this worker worktree. | Briefing/spec are usable as host critique context, but no durable reference payload is populated; leave as reference-context handoff unless leader provides generated/ignored build evidence. |
| `fig3_trapping_concept` | `briefing.md` defines reset schematic intent, PDMS vs sulfur-polymer mechanism contrast, trap-level invariants, and author-intent constraints. | No populated `reference/` payload is present in this worker worktree. | Briefing/spec are usable as host critique context, but reference-context row is not fully closed without durable reference payload or accepted host briefing. |
| `fig4_trap_energy_diagram` | `briefing.md`, `design.md`, and `spec.yaml` define the energy-level/DOS schematic, shallow/deep ordering, bimodal DOS alignment, and qualitative/no-numeric constraint. | `reference/` contains only `.gitkeep` in this worker worktree. | Briefing/spec/design are usable as host critique context, but reference-context row remains a handoff until durable reference payload or host briefing acceptance exists. |

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
| `fig1_overview_v2_pair_001_vault` | accepted/tracked-golden plus stale critique | Compile may refresh build evidence, but host critique refresh and `--force-golden` require explicit host/human/release authority. |
| `fig2_trap_design_space` and `fig3_resistance_mechanism` | source-of-truth entry says stale host critique; current worker status says render-missing first and critique not required | Re-run queue/status on the integration branch after mechanical compile artifacts are present; if host critique remains required, refresh `/fig_critique` with host vision. |
| `fig3_floating_clip_protocol`, `fig3_trapping_concept`, `fig4_trap_energy_diagram` | source-of-truth entry says critique briefing/reference context required; worker worktree has briefing/spec but no populated durable reference payload | Either promote/build durable reference-context artifacts, or accept briefing/spec/design as sufficient critique context in a leader-owned audit. |

## Verification performed

- Queue dry-run: PASS — `queue-run --mode review --goal Wave4-worker3-current
  --dry-run --json --max-fixtures 20` produced no failures and executed no
  commands.
- Fixture status inspection: PASS — `fig-agent status <fixture> --json` ran for
  the six named host/reference rows plus `fig5_actuation_mechanism` and
  `_volume_shading_demo`.
- Mutation check: PASS — `git status --short --
  plugins/figure-agent/examples/fig5_actuation_mechanism/fig5_actuation_mechanism.tex`
  was empty before documentation edit.

## Coordination note

Coordination protocol: coordinated - boundaries checked for leader-owned fig5,
accepted/tracked-golden fig1, host-only critique authority, reference-context
handoff rows, and clean-worktree versus leader-root generated-artifact divergence.
