# Real Fixture Production Readiness Baseline

Date: 2026-05-29

Related issues:

- `docs/superpowers/issues/2026-05-29-issue-71-real-fixture-production-readiness-roadmap.md`
- `docs/superpowers/issues/2026-05-29-issue-71a-real-fixture-baseline-and-queue-freeze.md`

Status: completed

## Goal

Freeze the current real-fixture queue before Issue 71 dogfood work continues.
This pass is read-only and planning-only: it classifies fixtures, records
driver stop shapes, and assigns each non-clean state to the next child issue.

No host critique, source edit, export, accepted/golden mutation, publication
mutation, or generated artifact commit was performed.

## Commands

From `plugins/figure-agent`:

```bash
uv run python3 scripts/status.py
find examples -mindepth 2 -maxdepth 2 -name spec.yaml -print | sort
uv run python3 scripts/fig_driver.py <fixture> --mode <review|release|polish> --goal issue-71-baseline --dry-run
```

The driver sweep covered every `examples/*/spec.yaml` fixture in review,
release, and polish modes.

## Production Fixture Queue

| Fixture | render | critique | export | acceptance | publication | review action | review boundary | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fig1_overview_v2` | FRESH | STALE | FRESH | NOT_ACCEPTED | HUMAN_ACCEPTANCE_REQUIRED | `run_critique` | `host_llm_critique_required` | 71B, then 71E |
| `fig1_overview_v2_pair_001_vault` | FRESH | STALE | TRACKED_GOLDEN | ACCEPTED | PASS | `run_critique` | `host_llm_critique_required` | 71B, then 71D/71E |
| `fig3_trapping_concept` | FRESH | NOT_REQUIRED | FRESH | NOT_DECLARED | NOT_APPLICABLE | `run_fig_loop` | `closeout_required` | 71C |
| `fig5_floating_clip_mechanism` | FRESH | NOT_REQUIRED | MISSING | NOT_ACCEPTED | HUMAN_ACCEPTANCE_REQUIRED | `run_export` | `closeout_required` | 71C, then 71E |
| `golden_trap_depth_picture` | FRESH | STALE | TRACKED_GOLDEN | NOT_ACCEPTED | HUMAN_ACCEPTANCE_REQUIRED | `run_critique` | `host_llm_critique_required` | 71B, then 71E |
| `n3_trial_01_trap_depth` | FRESH | STALE | MISSING | NOT_DECLARED | NOT_APPLICABLE | `run_critique` | `host_llm_critique_required` | 71B, then 71C |
| `n3_trial_02_actuation_sequence` | FRESH | STALE | FRESH | NOT_DECLARED | NOT_APPLICABLE | `run_critique` | `host_llm_critique_required` | 71B, then 71D candidate |
| `smoke_trap_demo` | FRESH | NOT_REQUIRED | FRESH | NOT_DECLARED | NOT_APPLICABLE | `run_fig_loop` | `closeout_required` | 71C |

## Mode Sweep Summary

| Fixture | release action / boundary | polish action / boundary |
| --- | --- | --- |
| `fig1_overview_v2` | `run_critique` / `host_llm_critique_required` | `run_critique` / `host_llm_critique_required` |
| `fig1_overview_v2_pair_001_vault` | `run_critique` / `host_llm_critique_required` | `run_critique` / `host_llm_critique_required` |
| `fig3_trapping_concept` | `release_blocked` / `accepted_or_final_ready_required` | `run_fig_loop` / `mode_forbidden_action` |
| `fig5_floating_clip_mechanism` | `run_export` / none | `run_export` / none |
| `golden_trap_depth_picture` | `run_critique` / `host_llm_critique_required` | `run_critique` / `host_llm_critique_required` |
| `n3_trial_01_trap_depth` | `run_critique` / `host_llm_critique_required` | `run_critique` / `host_llm_critique_required` |
| `n3_trial_02_actuation_sequence` | `run_critique` / `host_llm_critique_required` | `run_critique` / `host_llm_critique_required` |
| `smoke_trap_demo` | `release_blocked` / `accepted_or_final_ready_required` | `run_fig_loop` / `mode_forbidden_action` |

## Child-Issue Assignments

### 71B - Host-Vision Critique Queue Closeout

These fixtures have reference-grounded stale critique and must be refreshed by
host `/fig_critique`, not Codex-only synthesis:

- `fig1_overview_v2`
- `fig1_overview_v2_pair_001_vault`
- `golden_trap_depth_picture`
- `n3_trial_01_trap_depth`
- `n3_trial_02_actuation_sequence`

### 71C - Non-Critique Export And Closeout Rehearsal

These fixtures do not require reference-grounded critique and are suitable for
mechanical closeout/export rehearsal:

- `fig3_trapping_concept` - `run_fig_loop` review closeout.
- `fig5_floating_clip_mechanism` - `run_export` is mechanically selected in
  release/polish modes; review mode is closeout-bound.
- `smoke_trap_demo` - `run_fig_loop` review closeout.

### 71D - Positive SVG Polish Promotion Evidence

No fixture can be treated as a positive SVG-polish route before 71B/71C clears
freshness and closeout blockers. Candidate pool after those issues:

- `fig1_overview_v2_pair_001_vault`
- `n3_trial_02_actuation_sequence`

### 71E - Release, Golden, And Publication Gate Rehearsal

Release/golden/publication decisions remain explicit human-gated rehearsals:

- `fig1_overview_v2`
- `fig1_overview_v2_pair_001_vault`
- `fig5_floating_clip_mechanism`
- `golden_trap_depth_picture`

## Support And Legacy Folders

The following folders are not `examples/*/spec.yaml` production fixtures for
Issue 71. They may still appear in broad `status.py` output and should not be
counted as failed production targets:

| Folder | Classification |
| --- | --- |
| `_journal_art_direction_playbooks` | support corpus |
| `_macro_smoke` | smoke/support |
| `_paper_aesthetic_contexts` | support corpus |
| `_polymer_variants` | support corpus |
| `_snippet_smoke` | smoke/support |
| `_subregion_scratch` | scratch/support |
| `fig1_overview` | legacy no-spec example |
| `fig1_overview_hybrid` | legacy no-spec example |
| `fig1_overview_zpattern` | legacy no-spec example |
| `ispd_measurement_setup` | legacy no-spec example |

## Review Notes

- Support and legacy folders are separated from real production fixtures.
- Stale critiques are assigned to HITL 71B because host vision must read the
  rendered figure, high-zoom crops, reference material, and print-scale
  evidence.
- Accepted/golden/publication states are assigned to 71E and are not automatic
  work.
- The queue is specific enough for the next agent to start 71B or 71C without a
  new broad sweep.

## Verification

- `git status --short --untracked-files=no` before this milestone write showed
  no tracked fixture source, critique, accepted/golden, publication, or
  generated artifact mutation.
- `uv run python3 scripts/status.py` completed.
- `uv run python3 scripts/fig_driver.py <fixture> --mode <review|release|polish> --goal issue-71-baseline --dry-run`
  completed for all eight `spec.yaml` fixtures.

No known Issue 71A blocker remains.
