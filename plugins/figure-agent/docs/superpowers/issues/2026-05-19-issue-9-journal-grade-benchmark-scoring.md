# Issue 9: Journal-Grade Benchmark and Scoring Contract

**Date:** 2026-05-19 KST
**Status:** completed for the v1 advisory fresh re-audit contract on branch `codex/issue-9b-numeric-quality-score-calibration`
**Type:** AFK for schema/docs/tests, HITL for benchmark calibration policy
**Depends on:** Issue 6B, Issue 6C, Issue 8D

## Problem

`/fig_critique` now forces the host LLM to inspect journal-grade quality axes:
storyline, panel roles, sub-region integration, component fidelity, scientific
plausibility, composition, label semantics, polish, reference fidelity, and
publication readiness. `/fig_loop` can ingest those axis verdicts and
`/fig_drive` can now route from loop evidence.

The remaining gap is calibration. The plugin can say an axis is `pass`,
`needs_patch`, `needs_human`, or `block`, but it does not yet produce a stable
quality-level assessment such as:

- draft schematic,
- solid manuscript figure,
- high-impact candidate,
- requires human art direction,
- publication blocked.

That means a loop can clear local findings without clearly answering whether
the whole figure is approaching high-impact journal quality or merely becoming
less broken.

## Goal

Add a conservative benchmark/scoring contract that summarizes the existing
quality axes into a reproducible, loop-consumable current-quality level without
claiming objective Nature, Science, Nature Materials, or Nature Communications
acceptance.

The score must help the loop decide whether to continue polishing, request
human art direction, patch a concrete issue, or stop as complete.

The score is not a progress meter. It is a fresh re-audit of the current
rendered/exported artifact and current critique inputs. A previously solved
problem can become a problem again if a later patch damages layout, story,
scale, label semantics, or visual balance.

## What to Build

Introduce an additive critique frontmatter block, for example:

```yaml
journal_grade_assessment:
  schema: figure-agent.journal-grade-assessment.v1
  scoring_mode: fresh_reaudit
  assessed_artifact_hash: sha256:<current artifact/input hash>
  benchmark_level: draft | solid_manuscript | high_impact_candidate | needs_human_art_direction | blocked
  confidence: low | medium | high
  overall_score: 0-100
  sub_scores:
    storyline: 0-100
    composition: 0-100
    component_fidelity: 0-100
    scientific_plausibility: 0-100
    label_semantics: 0-100
    polish: 0-100
    reference_fidelity: 0-100
    export_scale_readability: 0-100
  blockers:
    - "<axis or finding id with reason>"
  regression_detected: true | false
  regressions:
    - axis: composition
      previous_state: pass
      current_state: needs_patch
      reason: "<why the current artifact regressed>"
  score_is_gateable: true | false
  next_quality_bottleneck: storyline | composition | component_fidelity | scientific_plausibility | label_semantics | polish | reference_fidelity | export_scale_readability | human_policy
  rationale: "<short explanation grounded in current quality_axes and visible evidence>"
```

This block must be derived from `quality_axes`; it must not replace them. The
axis verdicts remain the source of truth for detailed critique.

`assessed_artifact_hash` must bind the assessment to the current critique input
set or an equivalent current artifact/input hash. If the figure source,
briefing, spec, reference input, critique, export, or final artifact changes,
the previous assessment is stale and cannot gate completion.

## Required Semantics

- `blocked` if any upstream axis verdict is `block`, or if publication safety
  is blocked.
- `needs_human_art_direction` if the figure may be scientifically correct but
  the remaining issue is taste, story framing, target-journal fit, policy, or
  high-impact visual direction that the plugin cannot safely decide.
- `draft` if the figure has unresolved structural, scientific, storyline, or
  layout problems that would make it unsuitable for manuscript use.
- `solid_manuscript` if all blocking and major problems are cleared, but the
  polish/story/composition score is not strong enough to call it a high-impact
  candidate.
- `high_impact_candidate` only if all required quality axes pass, no human gate
  is required, export-scale readability is strong, and the rationale states why
  the figure is above ordinary manuscript quality.

`overall_score` is advisory and non-monotonic. It must not override hard
blockers, `quality_axes`, `benchmark_level`, human gates, freshness gates,
export/final-artifact gates, or accepted/golden gates. A lower score after a
patch is a valid outcome when the fresh audit finds a regression.

## Fresh Re-Audit Rules

The assessment must be recomputed from the current artifact on every critique
cycle. Previous assessments are historical evidence only.

- A previous `high_impact_candidate` does not remain valid after any source,
  export, reference, critique, adjudication, or final-artifact input changes.
- Passing an axis in a prior loop does not exempt that axis from the next
  audit.
- Score and benchmark level may rise or fall between iterations.
- Regressions must be recorded when the current audit downgrades an axis or
  reveals a new quality problem introduced by a prior fix.
- `/fig_loop` may attach advisory score policy only when
  `score_is_gateable: true`, `scoring_mode: fresh_reaudit`, the assessment hash
  matches the current input state, and the score block is complete and
  well-formed.
- Stale critique, stale adjudication, stale loop checkpoint, or stale final
  artifact state prevents the assessment from acting as completion evidence.

## Audit Coverage

The assessment must explicitly consider:

- whole-figure scientific message and first-read path,
- panel-to-panel narrative continuity,
- individual panel necessity and redundancy,
- sub-region integration after local patches,
- component recognizability and structural credibility,
- physical plausibility of arrows, forces, flows, fields, and connections,
- label-target correctness and annotation usefulness,
- layout balance, whitespace, density, alignment, and scale hierarchy,
- palette economy, line weight economy, typography, and contrast,
- export-scale readability at likely 1-column and 2-column sizes,
- reference role/topology fidelity,
- whether remaining quality issues are patchable or require human art
  direction.

## Loop Integration

`/fig_loop` should surface the assessment in `axis_verdicts` or a sibling
`journal_grade_assessment` field once present in a fresh v1.2+ critique.

Implemented loop behavior:

- `/fig_loop` surfaces the host-authored `journal_grade_assessment` as a
  sibling field in the iteration JSON.
- hash mismatch or stale inputs force `score_is_gateable: false` and
  `evaluation_state: stale`.
- `blocked` and `needs_human_art_direction` assessments surface as blocked
  evaluation states.
- complete numeric score blocks receive
  `score_policy: advisory_fresh_reaudit_not_gate` only when the assessment is
  fresh and gateable.
- stop reason, escalation, compile/export behavior, driver action, accepted
  state, golden state, and final-artifact state remain controlled by existing
  gates rather than by numeric score.

The loop must remain verify-only. It must not auto-polish, auto-accept, mutate
golden artifacts, or decide publication policy.

## Acceptance Criteria

- [x] `/fig_critique` brief explains the new benchmark assessment and includes
  the YAML schema.
- [x] Validator rejects malformed assessment blocks in fresh critiques that
  declare the assessment schema.
- [x] Assessment remains optional for legacy critiques.
- [x] Assessment declares `scoring_mode: fresh_reaudit`; any other value is
  invalid in v1.
- [x] Assessment includes an `assessed_artifact_hash` using the repo's existing
  `sha256:` convention.
- [x] `/fig_loop` only attaches advisory score policy to fresh, gateable,
  well-formed score blocks whose assessment hash matches the current
  input/artifact state.
- [x] Assessment cannot report `high_impact_candidate` while any upstream
  quality axis is `needs_patch`, `needs_human`, or `block`.
- [x] Assessment can carry a high advisory numeric score with a lower
  `benchmark_level`, but the score cannot promote the level or bypass gates.
- [x] `overall_score` is documented and tested as non-monotonic; the plugin
  must allow score decreases after a fresh audit.
- [x] Regressions are represented explicitly when a previously passing axis is
  downgraded by the current audit.
- [x] `export_scale_readability` is represented explicitly, even if first
  implementation is host-LLM judged rather than deterministic OCR.
- [x] `/fig_loop` surfaces the assessment without changing compile/export
  behavior.
- [x] `/fig_drive` keeps using `/fig_loop` evidence and does not independently
  invent quality scores.
- [x] Tests cover valid assessment, impossible high-impact state, blocker
  precedence, legacy critique compatibility, and loop surfacing.

## Completed Slices

- Issue 9A added the level-only fresh re-audit assessment contract.
- Issue 9C collected real host-LLM dogfood evidence and unblocked numeric
  calibration.
- Issue 9B added optional advisory numeric score fields, strict score-shape
  validation, and guarded `/fig_loop` surfacing.

## Remaining Calibration Risks

- Real dogfood has not yet exercised `high_impact_candidate`,
  `needs_human_art_direction`, or `blocked` on real fixtures.
- Numeric ranges are prompt calibration guidance only; code does not enforce
  range-to-level thresholds in v1.
- Future dogfood should check whether host LLMs use the numeric fields
  consistently across repeated fresh critiques.

## Closeout Review

Issue 9 was closed only after three checks:

1. **Parent contract check.** The parent issue was reconciled with Issues 9A,
   9B, and 9C. The stale high-score threshold rule was removed because v1
   scores are advisory and cannot promote benchmark level or bypass gates.
2. **Implementation coverage check.** Existing tests cover brief emission,
   validator shape checks, legacy compatibility, invalid high-impact state,
   stale/non-gateable hash handling, malformed score blocks, human-gate
   precedence, and score decrease after a fresh regression audit.
3. **Consumer boundary check.** `/fig_loop` surfaces
   `journal_grade_assessment` but does not change stop reason, escalation,
   compile/export behavior, driver action, accepted state, golden state, or
   final-artifact state from numeric score.

## Non-Goals

- Do not claim objective Nature/Science acceptance.
- Do not scrape journal figures or call external web/vision APIs in this slice.
- Do not build a learned visual-quality model.
- Do not treat scores as cumulative progress or permanent achievement.
- Do not auto-edit TikZ, SVG, accepted flags, golden artifacts, or
  `QUALITY_AUDIT.md`.
- Do not replace `quality_axes`; this is a summary layer over them.
- Do not make human publication provenance optional.

## Dependency Status

- Issue 6B remains the source of truth for required quality axes.
- Issue 6C ingests the quality axes into `/fig_loop`.
- Issue 8D remains the source of truth for driver routing from loop evidence.
- Issue 9A, 9B, and 9C close the v1 advisory fresh re-audit contract.

## Review Questions

- Should a future Issue 9D collect numeric-score dogfood evidence across fresh
  critiques before any UI or driver consumer treats score as more than
  advisory context?
- Should `export_scale_readability` remain host-LLM judged, or should a later
  slice add deterministic 1-column/2-column raster/OCR checks?
- Which user goals should treat `solid_manuscript` as enough versus requiring
  `high_impact_candidate` plus human art-direction signoff?
