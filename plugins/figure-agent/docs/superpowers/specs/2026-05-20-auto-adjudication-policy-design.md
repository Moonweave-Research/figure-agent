# Auto Adjudication Policy Design

**Date:** 2026-05-20 KST
**Status:** proposed for review
**Related:** Issue 13

## Problem

The current critique loop is too conservative after a host critique. The host
can produce a high-quality `critique.md`, but `critique_adjudication.py
scaffold` turns every unresolved finding into `decision: needs_human`.
`fig_loop` then stops at the first `needs_human` decision. In the
`fig1_overview_v2_pair_001_vault` v1.4 dogfood run, that turned five mostly
policy/style findings into a full human gate even though only the
target-journal art-direction decision was truly fundamental.

The desired workflow is not "no human review". It is narrower:

- let policy handle routine findings,
- let the agent patch safe, local style/readability issues one at a time,
- reserve human review for science, mechanism, reference interpretation,
  target-journal fit, acceptance/golden/final-artifact promotion, and other
  irreversible or domain-sensitive choices.

## Goals

- Add deterministic auto-adjudication support for `critique_adjudication.yaml`.
- Reduce broad human gates by converting safe findings to `dismiss`, `defer`,
  or a single `apply` decision.
- Keep `/fig_loop` verify-only and keep `may_edit: false` semantics.
- Allow at most one automatic `apply` decision per run so patch handoff remains
  one-target-at-a-time.
- Record the policy rule id and evidence in each automatic decision.
- Preserve the current conservative scaffold as the default unless the caller
  explicitly opts into policy application.

## Non-Goals

- No hidden source editing.
- No automatic accepted/golden/export/final-artifact mutation.
- No automatic `critique.md` mutation.
- No LLM-generated adjudication in the deterministic core path.
- No promotion of target-journal, high-impact, or physics decisions out of
  human review.

## Command Surface

Extend `scripts/critique_adjudication.py` with an explicit policy option:

```bash
uv run python3 scripts/critique_adjudication.py scaffold <name> --force --policy conservative-v1
uv run python3 scripts/critique_adjudication.py sync <name> --force --policy conservative-v1
```

Without `--policy`, behavior remains unchanged: unresolved findings scaffold to
`needs_human`.

With `--policy conservative-v1`, the tool builds the normal scaffold, then
rewrites decisions according to the policy. The output schema remains
`figure-agent.critique-adjudication.v1`; no schema bump is needed because the
decision vocabulary already supports `apply`, `dismiss`, `defer`,
`needs_human`, and `resolved`.

## Policy Inputs

The policy reads only validated `critique.md` frontmatter and the generated
scaffold:

- finding id,
- severity,
- category,
- status,
- `tex_lines`,
- observation,
- suggested_fix,
- linked micro-defects,
- top-tier audit links,
- quality-axis links,
- `journal_grade_assessment.score_is_gateable`,
- `journal_grade_assessment.next_quality_bottleneck`.

The policy does not read rendered images directly. Visual evidence remains in
`critique.md`.

## Decision Rules

Rules are evaluated in order. Human-protection rules win over automation.

### Human-Protected Findings

Any finding remains `needs_human` when any of these are true:

- severity is `BLOCKER` or `MAJOR`;
- category is `physics` or `structural`;
- observation or suggested fix mentions `target_journal_fit`,
  `human_review`, `human_policy`, `publication safety`, `mechanism`,
  `topology`, `reference interpretation`, `accepted`, `golden`, `export`,
  `final artifact`, `semantic backport`, or `Theory Guard`;
- the finding links to a top-tier audit item with verdict `needs_human` or
  `fail`;
- applying the suggested fix would add/remove a scientific claim or change the
  figure's semantic model.

Rule id: `HUMAN_CORE_SEMANTIC_OR_POLICY`.

### Auto Dismiss

A finding becomes `dismiss` when all are true:

- severity is `NIT` or `MINOR`;
- suggested fix or observation contains `accept_simplification`;
- category is `style`, `palette`, `whitespace`, `hierarchy`, or
  `label_placement`;
- no human-protection rule matched.

Rule id: `AUTO_DISMISS_ACCEPTED_SIMPLIFICATION`.

### Auto Defer

A finding becomes `defer` when all are true:

- severity is `NIT` or `MINOR`;
- the finding concerns thumbnail-only readability, social-media reuse, or
  non-submission-scale polish;
- `journal_grade_assessment.score_is_gateable` is `false` or absent;
- no human-protection rule matched.

Rule id: `AUTO_DEFER_NON_GATEABLE_THUMBNAIL_POLISH`.

### Auto Apply Candidate

A finding becomes `apply` only when all are true:

- severity is `NIT`;
- category is `style`, `whitespace`, `hierarchy`, `palette`, or
  `label_placement`;
- `tex_lines` is exactly two integers;
- suggested fix is concrete and local;
- observation/suggested fix does not contain any human-protected term;
- no other finding has already been auto-selected as `apply`.

Rule id: `AUTO_APPLY_SINGLE_SAFE_NIT_STYLE_PATCH`.

If more than one finding qualifies for auto-apply, choose the first one in
critique order and leave later candidates as `defer` with rule id
`AUTO_DEFER_APPLY_LIMIT_ONE_TARGET`.

## Output Decision Shape

Automatic decisions must be explicit:

```yaml
- finding_id: C001
  decision: defer
  reason: "AUTO_DEFER_NON_GATEABLE_THUMBNAIL_POLISH: thumbnail-only readability is non-gateable and score_is_gateable=false."
  patch_target: ""
  evidence: "critique.md finding C001; linked micro_defects M001."
```

For `apply`, `patch_target` and `evidence` must remain non-empty, satisfying
the existing validator.

## Example: v1.4 Dogfood Fixture

For the current `fig1_overview_v2_pair_001_vault` critique:

- `P001`, `P002`, `P003`: `dismiss` because each says
  `accept_simplification` and describes intentional iconic abstraction.
- `C001`: `defer` because it is thumbnail-only readability,
  `score_is_gateable=false`, and full 178 mm proxy remains readable.
- `C002`: remains `needs_human` because it explicitly asks for
  target-journal art-direction review.

Expected result: human gate shrinks from five findings to one fundamental
question.

## Integration With `/fig_loop`

No `fig_loop` behavior change is required for the first slice. Existing logic
already does the right thing:

- any remaining `needs_human` stops at `human_gate_required`;
- exactly one `apply` becomes `patch_target_recommended`;
- multiple `apply` decisions stop at `ambiguous_patch_selection`;
- no actionable findings can proceed toward workflow/export status gates.

The new policy changes only the quality of the adjudication input.

## Safety Properties

- Default behavior is unchanged unless `--policy conservative-v1` is passed.
- The policy never writes source files.
- The policy never edits `critique.md`.
- The policy never marks `BLOCKER`, `MAJOR`, `physics`, or `structural`
  findings as automatic.
- The policy never auto-resolves target-journal fit, high-impact readiness,
  accepted/golden/export/final-artifact state, or semantic backport questions.
- The policy produces deterministic output from checked-in text inputs.

## Tests

Add focused tests around `critique_adjudication.py`:

- default scaffold remains fully conservative;
- `--policy conservative-v1` auto-dismisses accepted simplification style
  findings;
- `--policy conservative-v1` auto-defers non-gateable thumbnail-only polish;
- `--policy conservative-v1` preserves target-journal fit as `needs_human`;
- policy never auto-applies more than one finding;
- policy refuses or leaves human-protected `BLOCKER`, `MAJOR`, `physics`, and
  `structural` findings as `needs_human`;
- CLI `scaffold --force --policy conservative-v1` writes reloadable YAML;
- existing `fig_loop` tests still pass with policy-produced decisions.

## Deferred Follow-Up

LLM-assisted adjudication explanation is intentionally deferred. If added
later, it must remain outside the deterministic core. The deterministic policy
provides the baseline, and any LLM suggestion is reviewed against it.
