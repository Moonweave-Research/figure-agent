# Issue 71 - Real-Fixture Production Readiness Evidence Roadmap

Status: completed

Depends on: Issue 70 operator-grade guided autonomy

## Problem

The plugin kernel is now strong enough to compile, audit, critique, route,
close out, export, and stop safely at host/human/release boundaries. The next
risk is different: real fixtures still do not demonstrate a clean production
path through those layers.

A fresh `status.py` sweep on 2026-05-29 showed the fixture corpus is not
release-clean:

- five reference-grounded active fixtures still need host `/fig_critique`
  refresh or critique/adjudication closeout;
- several non-critique fixtures still have stale or missing exports;
- accepted/golden/publication gates are correctly human-only, but not yet
  rehearsed as a release operator workflow;
- positive `ready_for_svg_polish` promotion remains unproven on a fresh real
  fixture;
- some support/example folders are intentionally not production fixtures and
  should not pollute readiness claims.

Without an evidence roadmap, future agents may keep adding kernel behavior
instead of proving that the existing kernel can carry real figures from stale
state to production-ready state without hidden mutation.

## Goal

Turn the current fixture corpus into a clear production-readiness evidence
program: classify every real fixture state, close safe mechanical gaps, run
host/human-gated steps only where appropriate, and record where the plugin still
needs better behavior.

This roadmap does not promise that every fixture becomes accepted or golden. It
proves which parts of the production workflow are automatic, semi-automatic,
host-mediated, human-mediated, or still blocked by real design work.

## Design Principles

- Real fixture state outranks idealized workflow diagrams.
- `/fig_status`, `/fig_drive`, `/fig_run`, `/fig_closeout`, and `/fig_loop` are
  the canonical operational surfaces.
- Host `/fig_critique` work is HITL: do not fabricate critique content from
  Codex-only context.
- Accepted, golden, publication, and force-golden decisions stay human-only.
- SVG polish promotion must be proven on fresh critique/adjudication/loop
  evidence before it becomes routine.
- Generated build/export/polish artifacts remain untracked unless an issue
  explicitly authorizes an accepted/golden artifact update.
- Any code change discovered during dogfood must be split into a narrow defect
  issue with tests, not hidden inside fixture maintenance.

## Child Issues

1. Issue 71A - Real Fixture Baseline And Queue Freeze
2. Issue 71B - Host-Vision Critique Queue Closeout
3. Issue 71C - Non-Critique Export And Closeout Rehearsal
4. Issue 71D - Positive SVG Polish Promotion Evidence
5. Issue 71E - Release, Golden, And Publication Gate Rehearsal

## Recommended Order

Run 71A first. It freezes the fixture queue and prevents dogfood from drifting
while evidence is being gathered.

Run 71B and 71C next. They separate host-mediated critique work from mechanical
export/closeout work.

Run 71D only after at least one candidate has fresh critique, adjudication, and
loop evidence. `ready_for_svg_polish` without fresh review evidence is not a
valid positive signal.

Run 71E last, after ordinary workflow states are understood, because accepted,
tracked-golden, and publication gates intentionally require explicit human
approval.

```text
71A baseline and queue freeze
  -> 71B host-vision critique queue closeout
  -> 71C non-critique export and closeout rehearsal
  -> 71D positive SVG polish promotion evidence
  -> 71E release/golden/publication gate rehearsal
```

## Current Fixture Snapshot

The 2026-05-29 sweep produced these important buckets:

- Reference-grounded stale critique queue:
  `fig1_overview_v2`, `fig1_overview_v2_pair_001_vault`,
  `golden_trap_depth_picture`, `n3_trial_01_trap_depth`,
  `n3_trial_02_actuation_sequence`.
- Non-critique mechanical closeout/export queue:
  `fig3_trapping_concept`, `smoke_trap_demo`,
  `fig5_floating_clip_mechanism`.
- Accepted/golden/publication gate rehearsal candidates:
  `fig1_overview_v2_pair_001_vault`, `golden_trap_depth_picture`,
  `fig1_overview_v2`, `fig5_floating_clip_mechanism`.
- Intentional support/smoke folders that should be classified but not treated
  as paper-ready targets:
  `_journal_art_direction_playbooks`, `_macro_smoke`,
  `_paper_aesthetic_contexts`, `_polymer_variants`, `_snippet_smoke`,
  `_subregion_scratch`.

## Out Of Scope For Issue 71

- New hidden autonomy.
- Source drawing or aesthetic patching unless a child issue explicitly records
  it as a human/outer-agent fixture task.
- Automatic host critique writing.
- Automatic accepted/golden/publication decisions.
- Force-golden execution without explicit human approval.
- SVG/vector edits.
- External provider API calls.
- Treating metrics, scores, or reference-learning signals as release authority.

## Acceptance

- Each child issue has a milestone with exact commands, fixture list, outcomes,
  and verification.
- Every real fixture is classified into production target, smoke/support, or
  intentionally deferred.
- Safe mechanical work is closed with `/fig_run` or exact lower-level commands
  and no tracked generated artifacts.
- Host critique work is recorded as HITL evidence and linted before loop use.
- At least one valid SVG-polish promotion attempt is recorded, even if the
  result is a justified no-go.
- Release/golden/publication gates are rehearsed without accidental mutation.
- Any plugin defect discovered by dogfood is turned into a separate narrow
  issue with tests.

## Closeout

All child issues have milestone evidence:

- 71A: `docs/milestones/2026-05-29-real-fixture-production-readiness-baseline.md`
- 71B: `docs/milestones/2026-05-29-issue-71b-host-vision-critique-closeout.md`
- 71C: `docs/milestones/2026-05-29-non-critique-export-closeout-rehearsal.md`
- 71D: `docs/milestones/2026-05-29-positive-svg-polish-promotion-evidence.md`
- 71E: `docs/milestones/2026-05-29-release-golden-publication-gate-rehearsal.md`

Final judgment:

- Real fixtures now have explicit production-readiness evidence rather than an
  assumed happy path.
- Host-vision critique, release/golden, publication, accepted, and SVG-polish
  boundaries remain explicit.
- The plugin did not discover a release-boundary mutation bug in 71E.
- Issue 73 addressed the main SVG-polish trigger ambiguity found by 71D.
- Post-Issue-73 critique generator changes correctly make affected critiques
  stale, so any future release rehearsal starts with a host-vision refresh
  queue.

## Review Questions

1. Does this roadmap prove real production workflow behavior instead of adding
   speculative features?
2. Are host, human, accepted/golden, publication, and SVG polish boundaries
   still explicit?
3. Can each child issue be run by an AFK/HITL agent without touching unrelated
   fixture source?
4. Does the roadmap distinguish plugin defects from ordinary stale fixture
   maintenance?
5. Does it generate enough evidence to decide the next code slice after Issue
   71, rather than guessing?
