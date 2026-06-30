# Wave 8 Worker 1 Boundary Unlock Handoff

Date: 2026-06-30

Source of truth: `.omx/context/figure-agent-wave8-boundary-unlock-20260630T080353Z.md`.

## Scope and non-mutation boundary

This worker slice unlocked the deterministic smoke export boundary, probed the
host-critique readiness boundary without authoring critique, and preserved the
`_volume_shading_demo` source boundary as a source-authoring/removal decision.

Hard boundary preserved:

- Did not edit or commit `plugins/figure-agent/examples/fig5_actuation_mechanism/fig5_actuation_mechanism.tex`.
- Did not run `--force-golden`, acceptance, release, publication, or provenance commands.
- Did not write `critique.md` or `critique_adjudication.yaml` for host-critique fixtures.
- Generated build/export artifacts from this worker remained ignored/untracked;
  this handoff is the only durable tracked artifact.

## Smoke export lane

Initial allowed export commands for the five closeout smoke fixtures reported
missing build PDFs and made no tracked changes:

```bash
./plugins/figure-agent/bin/fig-agent export smoke_annotation_box_demo
./plugins/figure-agent/bin/fig-agent export smoke_contrast_demo
./plugins/figure-agent/bin/fig-agent export smoke_label_overlap_demo
./plugins/figure-agent/bin/fig-agent export smoke_leader_line_demo
./plugins/figure-agent/bin/fig-agent export smoke_panel_spacing_demo
```

Each initial export returned `build/<fixture>.pdf not found; run /fig_compile
first`. The worker treated compile as a local build prerequisite, then reran the
same export command shape without `--force-golden`:

```bash
./plugins/figure-agent/bin/fig-agent compile <fixture>
./plugins/figure-agent/bin/fig-agent export <fixture>
```

Observed export result for all five fixtures:

- `run_export.py: regenerated exports/ for <fixture> (was MISSING)`
- `fig-agent status <fixture> --json`: `render_state=FRESH`,
  `export_state=FRESH`, `critique_state=NOT_REQUIRED`, `workflow_ready=true`,
  `next_action_summary.action=complete`
- `fig-agent closeout <fixture> --json`: export step passed; remaining closeout
  blocker is `loop_rerun` with reason `no post-patch fig_loop run was found`

Smoke fixtures unlocked:

- `smoke_annotation_box_demo`
- `smoke_contrast_demo`
- `smoke_label_overlap_demo`
- `smoke_leader_line_demo`
- `smoke_panel_spacing_demo`

## Host-critique readiness lane

Read-only probes were run exactly through the allowed helper shape:

```bash
./plugins/figure-agent/bin/fig-agent helper critique_brief.py examples/<fixture>
```

Probe result for all six host fixtures: `missing .../build/<fixture>.png; run
/fig_compile first`. No critique or adjudication files were written.

| Fixture | Read-only probe result | Next honest owner |
| --- | --- | --- |
| `fig1_overview_v2_pair_001_vault` | build PNG missing | workflow compile before host `/fig_critique` |
| `fig2_trap_design_space` | build PNG missing | workflow compile before host `/fig_critique` |
| `fig3_floating_clip_protocol` | build PNG missing | workflow compile before host `/fig_critique` |
| `fig3_resistance_mechanism` | build PNG missing | workflow compile before host `/fig_critique` |
| `fig3_trapping_concept` | build PNG missing | workflow compile before host `/fig_critique` |
| `fig4_trap_energy_diagram` | build PNG missing | workflow compile before host `/fig_critique` |

After these probes, a host-actor queue query returned zero host rows because the
current worker worktree state exposes render/build freshness as the next
mechanical prerequisite before host critique:

```bash
./plugins/figure-agent/bin/fig-agent queue --mode review --goal Wave8-host-critique --actor host_llm --json
```

Observed summary: `total=0`, `unfiltered_total=14`.

## `_volume_shading_demo` source boundary

Read-only status confirmed the fixture is not an export or critique task in its
current state:

```bash
./plugins/figure-agent/bin/fig-agent status _volume_shading_demo --json
```

Observed:

- `render_state=NOT_AUTHORED`
- `export_state=MISSING`
- `next_action_summary.action=create_or_fix_source`
- `next_action_summary.blocking_source=source_not_authored`
- `next_action_summary.safe_command=null`
- files present: `briefing.md`, `spec.yaml`,
  `exports/_volume_shading_demo.svg`, and
  `polish/_volume_shading_demo.polished.svg`
- source file absent: `_volume_shading_demo.tex`

This remains a dedicated source-authoring/removal decision; this worker did not
author source or attempt export/critique.

## Final queue snapshot

Command:

```bash
./plugins/figure-agent/bin/fig-agent queue-run --mode review --goal Wave8-final --dry-run --json --max-fixtures 30
```

Observed:

- `planned_executable=13`
- `planned_blocked=1`
- `failed=0`
- `executed_commands=0`
- actions: `run_compile=8`, `run_fig_loop=5`, `create_or_fix_source=1`
- first blockers: `render_missing=8`, `acceptance_not_declared=5`,
  `source_not_authored=1`

Final executable groups:

- compile rows for the six host-critique fixtures, `fig5_actuation_mechanism`,
  and `smoke_trap_demo`
- loop rows for the five smoke fixtures whose export boundary was unlocked here

The blocked row remains `_volume_shading_demo` with `safe_command:missing`.

## Verification performed

- Smoke export lane: PASS — five compile prerequisites and export retries
  completed; status reports `export_state=FRESH` for all five smoke fixtures.
- Host-critique probe lane: PASS — six read-only `critique_brief.py` probes ran;
  each stopped at missing build PNG; no critique/adjudication writes occurred.
- Source boundary classification: PASS — `_volume_shading_demo` remains
  `source_not_authored` with no safe command.
- Final queue dry-run: PASS — `planned_executable=13`, `planned_blocked=1`,
  `failed=0`, `executed_commands=0`.
- Git cleanliness before this handoff: PASS — build/export byproducts were
  ignored/untracked; no fixture source changes were tracked.

## Coordination note

Coordination protocol: coordinated - boundaries checked for Wave 8 source of
truth, leader-owned fig5 dirty source, non-golden export scope, host-only visual
critique authority, `_volume_shading_demo` source-authoring boundary, and final
queue integration state.
