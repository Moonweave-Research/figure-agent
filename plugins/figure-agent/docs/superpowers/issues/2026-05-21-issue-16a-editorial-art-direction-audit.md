# Issue 16A: Editorial Art-Direction Audit v1.5

**Date:** 2026-05-21 KST
**Status:** proposed
**Parent:** Issue 16
**Spec:** `../specs/2026-05-21-editorial-art-direction-audit-design.md`

## Problem

The current v1.4 critique contract is strong at technical and structural
quality control, but it does not force a sufficiently concrete editorial
art-direction decision. A figure can pass many technical checks and still look
like an ordinary schematic rather than a target-journal illustration.

The next audit layer should ask whether the figure has hero focus, visual
narrative, illustration register, consistent abstraction level, visual identity,
and a clear TikZ-vs-SVG polish boundary.

## What to Build

Add a new required v1.5 `critique.md` block:

```yaml
editorial_art_direction:
  hero_focus:
  narrative_choreography:
  illustration_readiness:
  abstraction_consistency:
  reference_class_fit:
  visual_identity:
  claim_payload_fit:
  aesthetic_risk:
  tikz_vs_svg_polish_trigger:
  human_art_direction_gate:
```

Each slot must include:

```yaml
verdict: pass | weak | fail | needs_human
evidence: "<specific current-artifact evidence>"
rationale: "<why this matters for target-journal illustration quality>"
concrete_fix: "<specific edit, polish handoff, or accept_simplification>"
blocks_high_impact: true | false
```

## Acceptance Criteria

- [ ] `/fig_critique` brief includes a mandatory Editorial Art-Direction Audit
  section.
- [ ] Output schema is bumped to `figure-agent.critique.v1.5`.
- [ ] Rubric version is bumped to `figure-agent.critique-rubric.v1.5`.
- [ ] `critique_schema_validator.py` accepts valid v1.5 critiques.
- [ ] Validator rejects missing `editorial_art_direction`.
- [ ] Validator rejects missing required editorial slots.
- [ ] Validator rejects invalid editorial verdicts.
- [ ] Validator rejects empty `evidence`, `rationale`, or `concrete_fix`.
- [ ] Validator rejects non-boolean `blocks_high_impact`.
- [ ] Blocking editorial slots must link to normal findings or
  `quality_axes.*.blocking_items`, unless `concrete_fix` explicitly uses
  `accept_simplification`.
- [ ] `journal_grade_assessment.benchmark_level: high_impact_candidate` is
  rejected unless all editorial slots pass.
- [ ] v1.0-v1.4 critiques remain legacy-compatible.
- [ ] Existing examples are not migrated in this slice.

## Out of Scope

- SVG editing or SVG polish manifest changes.
- `/fig_loop` or `/fig_drive` routing changes.
- Auto-patch or hidden source editing.
- Accepted/golden/final-artifact mutation.
- Claiming guaranteed Nature/Science acceptance.

## Verification Commands

```bash
uv run pytest -q tests/test_critique_brief.py tests/test_critique_adjudication.py tests/test_critique_schema_validator.py tests/test_critique_lint.py
uv run pytest -q
uv run ruff check scripts/critique_brief.py scripts/critique_brief_sections.py scripts/critique_schema_validator.py tests/test_critique_brief.py tests/test_critique_adjudication.py
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

## Follow-Up

Issue 16B should consume `editorial_art_direction.tikz_vs_svg_polish_trigger`
inside `/fig_loop` and `/fig_drive --mode polish`. That routing is deliberately
excluded from this slice so the audit contract can land first.
