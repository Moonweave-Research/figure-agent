# Issue 97A - Aesthetic Anti-Pattern Checklist

Status: first prompt-hardening slice implemented; schema/lint enforcement remains
proposed for a later narrow slice

Type: critique rubric hardening, schema/lint candidate

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

Preferred output field for a future schema slice:

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

The first implementation slice uses the smaller safe path: it adds the closed
anti-pattern checklist to the host critique brief without introducing a new
required critique field. A later vNext slice can promote the checklist into a
linted schema field once the fixture refresh cost is acceptable.

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

First-slice acceptance:

- The critique brief names every anti-pattern id with a concrete inspection
  question.
- The prompt explicitly tells the host LLM to route present/uncertain
  anti-patterns through existing TikZ/SVG/semantic/human/accept-simplification
  paths.
- No schema/rubric version is bumped in this slice.

## Verification

- `uv run pytest -q tests/test_critique_brief.py::test_critique_brief_includes_aesthetic_antipattern_checklist`
  - Result: 1 passed.
- `uv run pytest -q tests/test_ready_improvement.py tests/test_critique_brief.py::test_critique_brief_includes_aesthetic_antipattern_checklist tests/test_fig_driver.py`
  - Result: 87 passed.
- `uv run ruff check scripts/ready_improvement.py tests/test_ready_improvement.py scripts/critique_brief.py scripts/critique_brief_sections.py scripts/critique_schema_vocab.py tests/test_critique_brief.py`
  - Result: all checks passed.
- `git diff --check`
  - Result: clean.

## Review Checklist

1. Does this checklist add concrete visual questions rather than generic taste
   words?
2. Can a non-passing anti-pattern silently become release approval? It must not.
3. Can this force a figure to copy an irrelevant reference? It must not.
4. Can it recommend SVG polish before the existing SVG gate? It must not.
5. Does it preserve older critique compatibility?
