# Wave 8 host critique readiness handoff

Date: 2026-06-30
Lane: `worker-2` / host-critique readiness
Source of truth: `.omx/context/figure-agent-wave8-boundary-unlock-20260630T080353Z.md`

## Scope boundary

This lane only ran read-only `critique_brief.py` probes and inspected fixture
inputs for the future host `/fig_critique <fixture>` pass. It did **not** write
`critique.md`, did **not** write `critique_adjudication.yaml`, and does **not**
claim host visual critique is complete.

## Probe command

For each fixture below:

```bash
./plugins/figure-agent/bin/fig-agent helper critique_brief.py examples/<fixture>
```

All six probes exited with code `2`, emitted no stdout, and stopped on the same
readiness blocker: the required compiled build PNG is missing. The helper's
operator hint is `run /fig_compile first`.

## Fixture readiness matrix

| Fixture | `briefing.md` | `spec.yaml` | `.tex` source | build PNG | build PDF | exports SVG/PDF | references / crops | existing critique state | Next host boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fig1_overview_v2_pair_001_vault` | yes | yes | yes | missing | missing | yes / yes | `reference/reference_pack.md` plus 50 non-gitkeep reference files; no build crops/zooms | existing `critique.md` and `critique_adjudication.yaml` | compile first, then rerun brief and host `/fig_critique`; stale critique likely needs host refresh |
| `fig2_trap_design_space` | yes | yes | yes | missing | missing | missing / missing | empty `reference/`; no build crops/zooms | existing `critique.md` and `critique_adjudication.yaml` | compile/export readiness is absent; host critique also needs build PNG |
| `fig3_floating_clip_protocol` | yes | yes | yes | missing | missing | missing / missing | empty `reference/`; no build crops/zooms | none | compile first; then rerun brief before first host critique |
| `fig3_resistance_mechanism` | yes | yes | yes | missing | missing | missing / missing | no `reference/`; no build crops/zooms | existing `critique.md` and `critique_adjudication.yaml` | compile first, then rerun brief and refresh stale host critique if still queued |
| `fig3_trapping_concept` | yes | yes | yes | missing | missing | missing / missing | no `reference/`; no build crops/zooms | none | compile first; then rerun brief before first host critique |
| `fig4_trap_energy_diagram` | yes | yes | yes | missing | missing | missing / missing | empty `reference/`; no build crops/zooms | none | compile first; then rerun brief before first host critique |

## Required host handoff

Before invoking `/fig_critique <fixture>`, produce or restore the compiled build
PNG at `plugins/figure-agent/examples/<fixture>/build/<fixture>.png`. The current
state is not ready for image-reading critique because `critique_brief.py` cannot
construct the host brief without that PNG. Where the queue classifies the first
blocker as `critique_briefing_required`, the blocker currently collapses to this
same missing-build-PNG prerequisite.

## Coordination protocol

- Shared source of truth: Wave 8 context file plus the six read-only probe
  results above.
- Boundary honored: no host critique files or adjudication files were written.
- Integration dependency: smoke/export or compile-capable lanes must supply build
  PNGs before the host slash workflow can honestly read images.
- Subagent skip reason: the lane was six identical bounded probes plus a
  deterministic artifact inventory; spawning a subagent would add coordination
  overhead without improving correctness.
