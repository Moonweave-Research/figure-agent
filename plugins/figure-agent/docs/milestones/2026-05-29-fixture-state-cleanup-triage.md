# Fixture State Cleanup Triage

**Date:** 2026-05-29 KST
**Status:** automatic compile cleanup performed; remaining work is host/human
gated

## Summary

After the v0.8.2 release sync, the next risk was fixture-state confusion rather
than plugin-code behavior. The fixture corpus is useful for dogfood, but it is
not a clean release corpus: several examples are stale by design, and some need
host-vision critique or human publication decisions before release-style use.

This triage followed the plugin's own state machine:

1. Read `/fig_status`.
2. Use `/fig_drive --mode review --dry-run` for fixture-specific next actions.
3. Execute only compile actions selected by the driver.
4. Stop at `/fig_critique`, accepted/golden, export, and publication
   boundaries.

## Commands Run

```bash
uv run python3 scripts/status.py
uv run python3 scripts/fig_driver.py --mode review --goal 'fixture state cleanup triage' --dry-run fig1_overview_v2_pair_001_vault
uv run python3 scripts/fig_driver.py --mode review --goal 'fixture state cleanup triage' --dry-run n3_trial_02_actuation_sequence
uv run python3 scripts/fig_driver.py --mode review --goal 'fixture state cleanup triage' --dry-run golden_trap_depth_picture
uv run python3 scripts/fig_driver.py --mode review --goal 'fixture state cleanup triage' --dry-run fig1_overview_v2
uv run python3 scripts/fig_driver.py --mode review --goal 'fixture state cleanup triage' --dry-run fig3_trapping_concept
uv run python3 scripts/fig_driver.py --mode review --goal 'fixture state cleanup triage' --dry-run smoke_trap_demo
uv run python3 scripts/fig_driver.py --mode review --goal 'fixture state cleanup triage' --dry-run n3_trial_01_trap_depth
uv run python3 scripts/fig_driver.py --mode review --goal 'fixture state cleanup triage' --dry-run fig5_floating_clip_mechanism
bash scripts/compile.sh examples/fig1_overview_v2/fig1_overview_v2.tex
bash scripts/compile.sh examples/fig3_trapping_concept/fig3_trapping_concept.tex
bash scripts/compile.sh examples/smoke_trap_demo/smoke_trap_demo.tex
bash scripts/compile.sh examples/n3_trial_01_trap_depth/n3_trial_01_trap_depth.tex
bash scripts/compile.sh examples/fig5_floating_clip_mechanism/fig5_floating_clip_mechanism.tex
```

## Automatic Cleanup Completed

| Fixture | Before | Action | After |
| --- | --- | --- | --- |
| `fig1_overview_v2` | render stale | compiled | render fresh; critique stale remains |
| `fig3_trapping_concept` | render stale | compiled | render fresh; stale export remains |
| `smoke_trap_demo` | render stale | compiled | render fresh; stale export remains |
| `n3_trial_01_trap_depth` | stage 2 / render stale | compiled | stage 3; critique stale and export missing remain |
| `fig5_floating_clip_mechanism` | stage 2 / render stale | compiled | stage 3; export missing and publication gate remain |

Compile outputs were ignored build artifacts. They were not staged.

## Remaining Queue

### Host-Vision Required

Run `/fig_critique` next for:

- `fig1_overview_v2_pair_001_vault`
- `n3_trial_02_actuation_sequence`
- `golden_trap_depth_picture`
- `fig1_overview_v2`
- `n3_trial_01_trap_depth`

These should be handled by the host-vision workflow because the plugin can
prepare evidence and lint the resulting `critique.md`, but it cannot honestly
author a fresh vision critique from Codex text alone.

### Export Or Publication Required

After critique gates are fresh, or when critique is not required:

- `fig3_trapping_concept`: stale export
- `smoke_trap_demo`: stale export
- `fig5_floating_clip_mechanism`: export missing plus human publication gate
- `golden_trap_depth_picture`: publication provenance and acceptance remain
  human-only

## Review

1. **Scope containment:** clean. No source `.tex`, critique, accepted/golden, or
   publication-provenance files were intentionally edited.
2. **State-machine fit:** clean. The driver selected compile where render was
   stale and selected host critique where critique was stale.
3. **Generated artifacts:** clean for git. Build and export artifacts reported
   by `git status --ignored` are ignored and remain untracked.
4. **Remaining blockers:** intentional. They are host-vision or human gate
   boundaries, not plugin-code defects.

## Next Handoff

The highest-value next fixture action is:

```bash
/fig_critique fig1_overview_v2_pair_001_vault
```

Reason: it is accepted/golden, publication gate passes, and the current first
blocker is a stale reference-grounded critique. Do not run
`/fig_export --force-golden` until the critique/adjudication/loop path is fresh
and human approval exists for golden roll-forward.
