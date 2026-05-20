# Issue 9B Numeric Quality Score Calibration Design

## Status

Drafted on 2026-05-19 KST for implementation on branch
`codex/issue-9b-numeric-quality-score-calibration`.

## Source Evidence

Issue 9B is unblocked by Issue 9C evidence:

- 8 attempted dogfood fixtures.
- 5 valid v1.2 critique-grounded `journal_grade_assessment` runs.
- 3 critique-not-required blockers retained as fixture-contract evidence.
- Observed levels: `draft` (2) and `solid_manuscript` (3).
- Unobserved real-fixture levels: `high_impact_candidate`,
  `needs_human_art_direction`, `blocked`.
- Observed bottlenecks: `polish`, `scientific_plausibility`,
  `component_fidelity`.
- Observed end-state gates: `force_golden_required`,
  `human_gate_required`, and `agent_action_required`.

The evidence proves that level-only assessment is useful and falsifiable, but it
also shows that level-only output is too coarse for later calibration: three
different `solid_manuscript` fixtures had different visual ceilings, and two
`draft` fixtures had different failure causes. Numeric scores are therefore
useful only as advisory fresh re-audit diagnostics, not as release authority.

## Goal

Add optional numeric score fields to `journal_grade_assessment` so a host LLM can
summarize current-artifact quality more finely than `benchmark_level`, while
preserving the existing gate hierarchy:

1. missing/stale render, critique, adjudication, export, final artifact, and
   accepted/golden gates remain authoritative;
2. `quality_axes` verdicts remain authoritative over score;
3. `benchmark_level` remains the primary coarse quality label;
4. numeric scores are advisory and cannot unlock release, export, acceptance,
   final-artifact readiness, or human-gated findings.

## Non-Goals

- No learned quality model.
- No external API or journal corpus scoring.
- No objective Nature/Science acceptance claim.
- No auto-accept, auto-export, auto-patch, or safe executor behavior.
- No score-driven release gate in this slice.
- No migration requirement for existing v1.2 critiques without scores.

## Schema Extension

Keep `schema: figure-agent.critique.v1.2` and
`journal_grade_assessment.schema:
figure-agent.journal-grade-assessment.v1`. The score fields are optional
additions inside `journal_grade_assessment`; their absence preserves current
behavior.

When any score field is present, the complete score block must be valid:

```yaml
journal_grade_assessment:
  schema: figure-agent.journal-grade-assessment.v1
  scoring_mode: fresh_reaudit
  assessed_artifact_hash: sha256:<current critique input hash>
  benchmark_level: draft | solid_manuscript | high_impact_candidate | needs_human_art_direction | blocked
  confidence: low | medium | high
  blockers: []
  regression_detected: true | false
  regressions:
    - axis: "<score or quality axis name>"
      previous_state: "<prior fresh score/level/verdict>"
      current_state: "<current fresh score/level/verdict>"
      reason: "<why the current artifact regressed>"
  score_is_gateable: true | false
  next_quality_bottleneck: storyline | composition | component_fidelity | scientific_plausibility | label_semantics | polish | reference_fidelity | export_scale_readability | human_policy
  rationale: "<current artifact-only quality rationale>"
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
  score_rationale: "<why these numbers describe only the current artifact>"
```

The score block is all-or-nothing. If `overall_score`, `sub_scores`, or
`score_rationale` appears, all three must appear and pass validation.

## Score Semantics

Scores are fresh re-audit scores for the current rendered/exported artifact.
They are not cumulative progress meters.

- `100` does not mean journal acceptance.
- `0` does not mean the figure is unusable in every context.
- A later loop may produce a lower score after a patch if new defects appear or
  if an old defect becomes newly visible.
- Scores compare the current artifact against the rubric, not against the
  previous artifact.
- `score_is_gateable: true` only means the score belongs to the current
  `critique_input_hash`; it does not mean any release gate can be passed.

## Score Calibration Guidance

These ranges guide host-LLM scoring but are not hard gates:

- `0-39`: structurally poor or scientifically misleading draft.
- `40-59`: draft; narrative may be recoverable, but major axes need patching.
- `60-74`: manuscript-directional; usable structure with obvious quality
  limitations.
- `75-87`: solid manuscript schematic; coherent and useful, still below
  high-impact visual standard.
- `88-94`: high-impact candidate; visually strong and scientifically coherent,
  with only minor polish left.
- `95-100`: reserved for exceptional artifact evidence. The brief must warn the
  host that this is not a Nature/Science acceptance claim.

Implementation must not encode these ranges as gate thresholds in this slice.
The ranges are prompt calibration text only.

## Validation Rules

`scripts/critique_adjudication.py` must enforce:

- Score fields are optional for v1.2 legacy compatibility.
- If any score field appears, all score fields are required.
- `overall_score` must be an integer or float in `[0, 100]`.
- `sub_scores` must be a mapping with exactly these keys:
  `storyline`, `composition`, `component_fidelity`,
  `scientific_plausibility`, `label_semantics`, `polish`,
  `reference_fidelity`, `export_scale_readability`.
- Every `sub_scores` value must be an integer or float in `[0, 100]`.
- `score_rationale` must be a non-empty string.
- `score_is_gateable: true` still requires
  `assessed_artifact_hash == critique_input_hash`.
- `high_impact_candidate` still requires every applicable upstream
  `quality_axes` verdict to be `pass` or `not_applicable`.
- A high numeric score cannot bypass non-passing upstream `quality_axes`.
- A high numeric score cannot bypass `benchmark_level: draft`,
  `needs_human_art_direction`, or `blocked`.

Validator should not force consistency between `benchmark_level` and exact
numeric ranges in the first slice. The 9C evidence does not cover enough levels
to make strict range enforcement safe. The host prompt may guide ranges; code
should validate shape and gate safety.

## Loop Surfacing

`scripts/fig_loop.py` should preserve current behavior and add only compact
score surfacing when the assessment is present:

```json
"journal_grade_assessment": {
  "...existing fields": "...",
  "overall_score": 72,
  "sub_scores": {
    "storyline": 78,
    "composition": 70,
    "component_fidelity": 55,
    "scientific_plausibility": 82,
    "label_semantics": 76,
    "polish": 64,
    "reference_fidelity": 80,
    "export_scale_readability": 68
  },
  "score_rationale": "current artifact only",
  "score_policy": "advisory_fresh_reaudit_not_gate"
}
```

If the assessment is absent, malformed, stale, or non-gateable, current null or
stale behavior remains. `fig_loop` must not create synthetic scores, and it
must attach `score_policy: advisory_fresh_reaudit_not_gate` only to complete
score blocks from fresh gateable assessments.

## Gate Precedence

Score cannot change stop reason or escalation. This is the key safety rule.

Examples:

- `overall_score: 91` plus `human_gate_required` still stops at
  `human_gate_required`.
- `overall_score: 90` plus stale/blocked final artifact still stops at the
  status/final-artifact gate.
- `overall_score: 85` plus `quality_axes.publication_readiness.verdict: block`
  still surfaces publication safety as blocked.
- `overall_score: 95` plus `benchmark_level: solid_manuscript` remains
  `solid_manuscript`; the numeric score cannot promote the benchmark level.
- `journal_grade_assessment: null` remains valid for critique-not-required
  fixtures.

## Brief Changes

`scripts/critique_brief.py` should add score guidance under the existing
Journal-Grade Fresh Re-Audit Assessment section:

- Scores are optional but recommended when the host can justify them.
- Scores must be current-artifact-only.
- Scores may decrease after a patch.
- Scores cannot override blockers, human gates, stale exports, final-artifact
  gates, or accepted/golden gates.
- Do not invent journal acceptance probabilities.
- Use the full `sub_scores` mapping if any numeric score is emitted.

The output schema block should show the optional fields and explicitly label
them as advisory.

## Test Plan

Add focused tests before implementation:

1. `tests/test_critique_adjudication.py`
   - valid score block is accepted;
   - score value below 0 or above 100 fails;
   - partial score block fails;
   - missing sub-score key fails;
   - extra sub-score key fails;
   - high numeric score with non-passing upstream quality axis still fails via
     existing `high_impact_candidate` rule when the level is high-impact;
   - high numeric score with `benchmark_level: draft` is accepted but does not
     imply promotion.

2. `tests/test_fig_loop.py`
   - valid score block is surfaced unchanged with
     `score_policy: advisory_fresh_reaudit_not_gate`;
   - stale hash forces `score_is_gateable: false` and `evaluation_state:
     stale`, even if `overall_score` is high, and does not attach
     `score_policy`;
   - malformed score blocks do not receive `score_policy`;
   - human-gated adjudication still stops at `human_gate_required` even when
     `overall_score` is high;
   - missing assessment remains `None`.

3. `tests/test_critique_brief.py`
   - brief contains `overall_score`, `sub_scores`, `score_rationale`;
   - brief states scores are advisory fresh re-audit values and not release
     gates.

Run targeted tests first, then full release verification:

```bash
uv run pytest -q tests/test_critique_adjudication.py tests/test_fig_loop.py tests/test_critique_brief.py
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

## Implementation Slices

1. **Policy and prompt schema only.**
   Update brief text and schema block. Tests verify generated brief strings.

2. **Validator score block.**
   Add local helpers for numeric ranges and exact sub-score keys. Keep unknown
   future fields otherwise preserved by existing frontmatter behavior.

3. **Loop surfacing.**
   Add `score_policy` only when the score block is complete and the assessment
   is fresh/gateable. Do not modify stop reason, escalation, driver action,
   status, export, accepted, or final-artifact behavior.

4. **Documentation closeout.**
   Update Issue 9B status and record that numeric scores are advisory-only in
   this slice.

## Open Risks

- Real dogfood has not exercised `high_impact_candidate`,
  `needs_human_art_direction`, or `blocked`. Do not write strict range gates for
  those levels yet.
- Host LLM may over-score weak artifacts unless prompt text strongly says that
  `solid_manuscript` can span a wide range below high-impact standard.
- Users may read `overall_score` as progress. The field name is convenient but
  risky; `score_rationale` and prompt wording must explicitly say fresh
  re-audit, not progress.
- Future UI should consider showing score beside gate status, never instead of
  gate status.

## Decision

Proceed with an advisory-only numeric score block. It gives the loop more
granularity while preserving the current safety architecture. Do not implement
score-based gates in Issue 9B.
