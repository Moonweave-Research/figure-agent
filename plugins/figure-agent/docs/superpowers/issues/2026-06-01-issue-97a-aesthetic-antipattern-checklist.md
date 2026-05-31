# Issue 97A - Aesthetic Anti-Pattern Checklist

Status: implemented through schema v1.17

Type: critique rubric hardening, schema/lint contract

Parent:

- Issue 97 - Top-Tier Aesthetic Edge-Case Audit Roadmap

## Problem

Current aesthetic audit surfaces are useful but still too broad. A host LLM can
say the figure has "professional polish" or "coherent visual hierarchy" without
checking the concrete anti-patterns users actually notice in top-tier figure
work:

- childish/cartoonish shapes;
- poster-like decoration;
- generic template feel;
- dead-flat vector finish;
- uniform line-weight monotony;
- weak hero/visual anchor;
- cramped or dead whitespace;
- low-authority typography;
- annotation noise;
- panel style mismatch;
- reference over-copying;
- reference under-learning;
- decorative detail that competes with the science.

## Goal

Add a closed anti-pattern checklist to the critique contract so every advanced
critique must explicitly mark each anti-pattern as absent, present, or
needs-human.

The checklist should be route-aware:

- TikZ micro-polish for source-level layout/style fixes;
- SVG polish for optical cleanup only when existing SVG gates permit it;
- semantic backport when the issue changes meaning or briefing/spec intent;
- human art direction when the decision is subjective;
- accept simplification only with concrete rationale.

## Expected Contract

Implemented output field for schema `figure-agent.critique.v1.17`:

```yaml
aesthetic_antipattern_audit:
  - id: generic_template_look
    verdict: absent | present | needs_human | not_applicable
    severity: BLOCKER | MAJOR | MINOR | NIT
    route: none | tikz_patch | svg_polish | semantic_backport | human_art_direction | accept_simplification
    evidence: "<crop/current-artifact evidence>"
    rationale: "<why this verdict/route is correct>"
    linked_evidence:
      - top_tier_audit.aesthetic_coherence | editorial_art_direction.aesthetic_risk | finding id | micro_defect id
```

The first prompt-hardening slice added the closed checklist to the host brief.
The second slice promotes it into `aesthetic_antipattern_audit` for grounded
v1.17 critiques. Legacy v1.16 and older critiques remain parseable, but new
grounded critiques with audit crops must answer the closed checklist.

## Anti-Pattern IDs

- `childish_shape_language`
- `poster_gradient_decoration`
- `generic_template_look`
- `dead_flat_vector_finish`
- `uniform_line_weight_monotony`
- `weak_hero_anchor`
- `cramped_or_dead_whitespace`
- `low_authority_typography`
- `annotation_noise_competes_with_science`
- `panel_style_mismatch`
- `reference_overcopying`
- `reference_underlearning`
- `decorative_detail_without_explanatory_value`

## Acceptance Criteria

- The critique brief names every anti-pattern id with a concrete inspection
  question.
- Schema/lint behavior prevents non-passing anti-patterns from becoming vague
  prose.
- `svg_polish` routes cannot appear unless the existing SVG polish route is
  ready.
- `semantic_backport` routes must cite semantic evidence.
- Legacy critiques remain parseable.
- Tests cover brief output, schema/lint acceptance, unknown ids, missing ids,
  invalid route, and generic evidence rejection.

Implemented contract:

- The critique brief names every anti-pattern id with a concrete inspection
  question.
- The prompt explicitly tells the host LLM to route present/uncertain
  anti-patterns through existing TikZ/SVG/semantic/human/accept-simplification
  paths.
- The output format requires `aesthetic_antipattern_audit` under schema
  `figure-agent.critique.v1.17`.
- Validation rejects missing, duplicate, or unknown anti-pattern ids.
- Validation rejects present/needs-human anti-patterns with no linked evidence
  or no route.
- `svg_polish` routes require the existing
  `editorial_art_direction.tikz_vs_svg_polish_trigger.recommended_path:
  ready_for_svg_polish`.
- `semantic_backport` and `human_art_direction` routes must cite their matching
  downstream evidence paths.

## Verification

- `uv run pytest -q tests/test_critique_brief.py::test_critique_brief_includes_aesthetic_antipattern_checklist`
  - Result: 1 passed.
- `uv run pytest -q tests/test_ready_improvement.py tests/test_critique_brief.py::test_critique_brief_includes_aesthetic_antipattern_checklist tests/test_fig_driver.py`
  - Result: 87 passed.
- `uv run ruff check scripts/ready_improvement.py tests/test_ready_improvement.py scripts/critique_brief.py scripts/critique_brief_sections.py scripts/critique_schema_vocab.py tests/test_critique_brief.py`
  - Result: all checks passed.
- `git diff --check`
  - Result: clean.
- `uv run pytest -q tests/test_critique_schema_validator.py tests/test_quality_manifest.py tests/test_critique_brief.py tests/test_critique_lint.py`
  - Result: 282 passed.
- `uv run pytest -q tests/test_status.py tests/test_fig_driver.py tests/test_fig_loop.py tests/test_ready_improvement.py`
  - Result: 311 passed, 1 skipped.
- `uv run pytest -q tests/test_fig_loop_assessments.py tests/test_fig_loop.py tests/test_fig_driver.py tests/test_critique_schema_validator.py tests/test_critique_brief.py tests/test_quality_manifest.py tests/test_status.py::test_hash_metadata_accepts_v1_17_rubric_for_audit_crop_manifest`
  - Result: 362 passed.
- `uv run pytest -q tests/test_status.py::test_hash_metadata_accepts_v1_17_rubric_for_audit_crop_manifest tests/test_fig_loop_assessments.py::test_v1_17_critique_surfaces_loop_audit_summaries`
  - Result: 2 passed.
- `uv run pytest -q`
  - Result: 1561 passed, 3 skipped, 1 xfailed.
- `uv run ruff check .`
  - Result: all checks passed.
- `claude plugin validate .claude-plugin/plugin.json`
  - Result: passed.
- `claude plugin validate .`
  - Result: passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json`
  - Result: passed.

## Review Checklist

1. Does this checklist add concrete visual questions rather than generic taste
   words?
2. Can a non-passing anti-pattern silently become release approval? It must not.
3. Can this force a figure to copy an irrelevant reference? It must not.
4. Can it recommend SVG polish before the existing SVG gate? It must not.
5. Does it preserve older critique compatibility?
