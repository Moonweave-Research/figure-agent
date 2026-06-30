# Wave 4 Bottleneck Reconciliation

Date: 2026-06-30

## Scope and boundaries

This is the Wave 4 worker reconciliation artifact for the live queue snapshot in
this worktree. It intentionally does not edit figure source, accepted state,
golden exports, publication state, or human acceptance records.

Explicit no-touch boundary preserved:

- `examples/fig5_actuation_mechanism/fig5_actuation_mechanism.tex` was not
  staged, reverted, overwritten, or edited.
- Host-LLM critique rows are left as host-only work; this artifact narrows the
  handoff instead of fabricating visual judgment.
- Reference-context rows were audited by generating host critique briefs from
  the current render/build evidence; no `critique.md` was authored by the
  workflow agent.

## Commands executed

From `plugins/figure-agent`:

```bash
./bin/fig-agent queue-run --mode review --goal Wave4-entry-worker1 --dry-run --json --max-fixtures 20
./bin/fig-agent queue-run --mode review --goal Wave4-worker1-mechanical --execute --json --max-fixtures 20
./bin/fig-agent queue-run --mode review --goal Wave4-after-compile-worker1 --dry-run --json --max-fixtures 20
./bin/fig-agent export fig5_actuation_mechanism
./bin/fig-agent export smoke_annotation_box_demo
./bin/fig-agent export smoke_contrast_demo
./bin/fig-agent export smoke_label_overlap_demo
./bin/fig-agent export smoke_leader_line_demo
./bin/fig-agent export smoke_panel_spacing_demo
./bin/fig-agent export smoke_trap_demo
./bin/fig-agent queue-run --mode review --goal Wave4-loop-closeout-worker1 --execute --json --max-fixtures 20
./bin/fig-agent queue-run --mode review --goal Wave4-final-worker1 --dry-run --json --max-fixtures 20
PYTHONPATH=scripts:scripts/quality:scripts/svg_polish uv run python scripts/critique_brief.py examples/<fixture>
./bin/fig-agent context-pack <fixture> --json
```

Observed CLI contract note: `fig-agent export` does not accept `--json`; the
export rows were rerun with the supported text-output command.

## Queue count reconciliation

| Snapshot | Total | Executable | Blocked | Complete | By bottleneck category |
| --- | ---: | ---: | ---: | ---: | --- |
| Entry in this worker | 14 | 13 | 1 | 0 | `{'mechanical_tool': 14}` |
| After compile execution | 14 | 0 | 14 | 0 | `{'host_critique': 3, 'mechanical_tool': 8, 'reference_context': 3}` |
| After export execution | 14 | 7 | 7 | 0 | `{'host_critique': 3, 'mechanical_tool': 8, 'reference_context': 3}` |
| Final dry run | 14 | 7 | 7 | 0 | `{'host_critique': 3, 'mechanical_tool': 8, 'reference_context': 3}` |

Final first-blocker counts:

```text
{'acceptance_not_declared': 7, 'critique_briefing_required': 3, 'critique_stale': 3, 'source_not_authored': 1}
```

## Deterministic mechanical closeout performed

- Compiled 13 safe `run_compile` rows with
  `queue-run --execute`; command summary: `{'attempted': 7, 'blocked': 7, 'executed_commands': 7, 'failed': 0, 'planned_blocked': 7, 'planned_complete': 0, 'planned_executable': 7, 'unattempted_executable': 0}` for the loop
  pass and `{'attempted': 13, 'blocked': 1, 'executed_commands': 13, 'failed': 0, 'planned_blocked': 1, 'planned_complete': 0, 'planned_executable': 13, 'unattempted_executable': 0}` for compile pass.
- Exported 7 safe `run_export` rows without `--force-golden` and without
  accepted/publication mutation.
- Ran 7 safe `run_fig_loop` rows. They remain executable in the final queue
  because the next visible blocker is `acceptance_not_declared`; this worker did
  not invent acceptance.

Final executable rows that remain:

| Fixture | Action | Actor | Command/reason |
| --- | --- | --- | --- |
| `fig5_actuation_mechanism` | `run_fig_loop` | `workflow_agent` | fig-agent loop fig5_actuation_mechanism --goal Wave4-final-worker1 --json |
| `smoke_annotation_box_demo` | `run_fig_loop` | `workflow_agent` | fig-agent loop smoke_annotation_box_demo --goal Wave4-final-worker1 --json |
| `smoke_contrast_demo` | `run_fig_loop` | `workflow_agent` | fig-agent loop smoke_contrast_demo --goal Wave4-final-worker1 --json |
| `smoke_label_overlap_demo` | `run_fig_loop` | `workflow_agent` | fig-agent loop smoke_label_overlap_demo --goal Wave4-final-worker1 --json |
| `smoke_leader_line_demo` | `run_fig_loop` | `workflow_agent` | fig-agent loop smoke_leader_line_demo --goal Wave4-final-worker1 --json |
| `smoke_panel_spacing_demo` | `run_fig_loop` | `workflow_agent` | fig-agent loop smoke_panel_spacing_demo --goal Wave4-final-worker1 --json |
| `smoke_trap_demo` | `run_fig_loop` | `workflow_agent` | fig-agent loop smoke_trap_demo --goal Wave4-final-worker1 --json |

## Host critique handoff rows

These rows require host visual judgment via `/fig_critique`; the workflow agent
must not author a fresh critique as a substitute for host inspection.

| Fixture | Action | Actor | Reason |
| --- | --- | --- | --- |
| `fig1_overview_v2_pair_001_vault` | `run_critique` | `host_llm` | required_actor:host_llm |
| `fig2_trap_design_space` | `run_critique` | `host_llm` | required_actor:host_llm |
| `fig3_resistance_mechanism` | `run_critique` | `host_llm` | required_actor:host_llm |

Actionable handoff:

```bash
/fig_critique fig1_overview_v2_pair_001_vault
/fig_critique fig2_trap_design_space
/fig_critique fig3_resistance_mechanism
```

After each host critique, rerun:

```bash
./bin/fig-agent status <fixture> --json
./bin/fig-agent drive <fixture> --mode review --goal Wave4-host-refresh --json
./bin/fig-agent queue-run --mode review --goal Wave4-after-host-refresh --dry-run --json --max-fixtures 20
```

## Reference-context briefing audit rows

The reference-context rows now have generated, host-ready critique brief evidence
from the current build outputs. The command used was:

```bash
PYTHONPATH=scripts:scripts/quality:scripts/svg_polish uv run python scripts/critique_brief.py examples/<fixture>
```

| Fixture | Brief evidence | Context-pack audit | Next host action |
| --- | --- | --- | --- |
| `fig3_floating_clip_protocol` | 1096 lines; high_zoom=True; print_scale=True; first visual-clash total=12 | `fig-agent context-pack fig3_floating_clip_protocol --json` succeeded; fixture semantic contracts present; no panel reference images declared where warnings noted | `/fig_critique fig3_floating_clip_protocol` using the generated brief and build/audit crops |
| `fig3_trapping_concept` | 1108 lines; high_zoom=True; print_scale=True; first visual-clash total=14 | `fig-agent context-pack fig3_trapping_concept --json` succeeded; fixture semantic contracts present; no panel reference images declared where warnings noted | `/fig_critique fig3_trapping_concept` using the generated brief and build/audit crops |
| `fig4_trap_energy_diagram` | 1000 lines; high_zoom=True; print_scale=True; first visual-clash total=9 | `fig-agent context-pack fig4_trap_energy_diagram --json` succeeded; fixture semantic contracts present; no panel reference images declared where warnings noted | `/fig_critique fig4_trap_energy_diagram` using the generated brief and build/audit crops |

These rows remain blocked on `host_llm` because the generated brief is input to
host vision review, not a replacement for it.

## Other blocked rows

| Fixture | Action | Actor | Reason |
| --- | --- | --- | --- |
| `_volume_shading_demo` | `create_or_fix_source` | `workflow_agent` | safe_command:missing |

`_volume_shading_demo` has no safe command because the source is not authored;
this worker left it blocked rather than creating source outside a narrowed
source-authoring task.

## Wave 5 recommended next work

1. Host runs `/fig_critique` for the 6 host rows above and commits refreshed
   `critique.md`/adjudication evidence where appropriate.
2. A human or explicit acceptance task decides whether the 7 exported/looped
   fixtures should receive acceptance records; this is not workflow-agent
   authority.
3. `_volume_shading_demo` needs a dedicated source-authoring or removal decision.
4. Rerun `queue-run --dry-run --json --max-fixtures 20` on the leader branch
   after integrating this worker commit and any host critique artifacts.
