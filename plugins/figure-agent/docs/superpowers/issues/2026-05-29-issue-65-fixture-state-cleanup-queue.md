# Issue 65 - Fixture State Cleanup Queue

Status: completed in commit `545e376`

Depends on: v0.8.2 / Issue 64 release metadata sync

## Problem

The plugin code and release metadata are current, but the checked-in fixture
corpus is intentionally not all release-ready. A plain `/fig_status` sweep on
2026-05-29 showed many fixtures at `ready: false`, mostly because of stale
critiques, stale exports, missing briefing files, or human-only publication
gates.

Without a concrete cleanup queue, future agents may confuse fixture-state
maintenance with plugin-kernel defects, or may cross host-vision and
accepted/golden boundaries without explicit approval.

## Goal

Separate safe automatic fixture-state cleanup from host-vision, human,
accepted/golden, and publication-provenance boundaries.

## Scope

In scope:

- Run read-only `/fig_status` over the fixture corpus.
- Run `/fig_drive --mode review --dry-run` on representative stale fixtures.
- Execute safe compile-only next actions where the driver chooses `run_compile`.
- Record the remaining host/human queue.
- Keep generated build/export artifacts ignored and uncommitted.

Out of scope:

- Rewriting `critique.md` through host-vision review.
- Editing fixture source `.tex` files.
- Exporting or forcing golden artifacts.
- Changing `accepted`, `golden_contract`, publication provenance, or
  `QUALITY_AUDIT.md`.
- Changing plugin state-machine behavior.

## Findings

### Safe Automatic Work

The following fixtures had `run_compile` as the driver-selected review action
and were compiled successfully:

| Fixture | Compile result | Notable report-only signal |
| --- | --- | --- |
| `fig1_overview_v2` | exit 0 | 3 collision WARNs; critique remains stale |
| `fig3_trapping_concept` | exit 0 | no collisions; critique not required |
| `smoke_trap_demo` | exit 0 | no collisions; critique not required |
| `n3_trial_01_trap_depth` | exit 0 | no collisions; critique remains stale |
| `fig5_floating_clip_mechanism` | exit 0 | no collisions; critique not required |

Generated build artifacts remained ignored and were not staged.

### Remaining Host-Vision Queue

These fixtures are blocked at `/fig_critique` and should be handled by the host
vision workflow, not by Codex fabricating critique content:

| Fixture | Current first action | Notes |
| --- | --- | --- |
| `fig1_overview_v2_pair_001_vault` | `/fig_critique fig1_overview_v2_pair_001_vault` | accepted/golden fixture; stale critique/export; golden roll-forward remains human-only |
| `n3_trial_02_actuation_sequence` | `/fig_critique n3_trial_02_actuation_sequence` | render/export fresh; stale critique; reference-aesthetic metrics warning |
| `golden_trap_depth_picture` | `/fig_critique golden_trap_depth_picture` | tracked golden, not accepted; publication provenance requires human action |
| `fig1_overview_v2` | `/fig_critique fig1_overview_v2` | render now fresh; legacy/stale critique; publication audit missing |
| `n3_trial_01_trap_depth` | `/fig_critique n3_trial_01_trap_depth` | render now fresh; stale critique; exports missing after critique |

### Remaining Non-Critique Fixture Work

These fixtures do not require reference-grounded critique, but still need export
or publication handling before release-style use:

| Fixture | Current issue |
| --- | --- |
| `fig3_trapping_concept` | stale export |
| `smoke_trap_demo` | stale export |
| `fig5_floating_clip_mechanism` | export missing; not accepted; publication gate requires human action |

## Decision

Issue 65 is a cleanup triage slice, not a kernel feature slice. The plugin is
behaving conservatively: it routes stale reference-grounded fixtures to
`/fig_critique`, compile-stale fixtures to `/fig_compile`, and accepted/golden
or publication decisions to human-only gates.

The next live work should be fixture-specific:

1. Run host `/fig_critique` for the stale reference-grounded fixtures above.
2. Run `/fig_adjudicate` after critique lint passes.
3. Run `/fig_loop` to record the next state.
4. Export only after render and critique state are fresh.
5. Force golden or change accepted/publication state only with explicit human
   approval.

## Verification

Commands:

```bash
uv run python3 scripts/status.py
uv run python3 scripts/fig_driver.py --mode review --goal 'fixture state cleanup triage' --dry-run <fixture>
bash scripts/compile.sh examples/<fixture>/<fixture>.tex
git status --short --branch
```

Results:

- Safe compile commands completed with exit code 0.
- No tracked fixture source, critique, export, accepted/golden, or provenance
  files were modified.
- Remaining blockers are host-vision or human/publication boundaries, not
  plugin-code failures.
