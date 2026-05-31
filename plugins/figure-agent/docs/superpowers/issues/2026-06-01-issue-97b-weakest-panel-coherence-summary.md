# Issue 97B - Weakest-Panel Coherence Summary

Status: first prompt-hardening slice implemented; structured output surfacing
remains proposed

Type: critique/loop summary, paper-quality audit

Parent:

- Issue 97 - Top-Tier Aesthetic Edge-Case Audit Roadmap

## Problem

Top-tier figures often fail by the weakest panel. Current audits can pass each
axis locally while one panel still feels less mature, less integrated, or less
publication-grade than the rest.

## Goal

Add a structured weakest-panel summary that names the weakest panel/subregion,
explains why it is weak, and routes the next decision to TikZ micro-polish, SVG
polish, semantic backport, human art direction, or accept-simplification.

## Expected Contract

```yaml
weakest_panel_summary:
  panel_id: <panel id or none>
  subregion_id: <subregion id or empty>
  weakness_type: composition | typography | color | density | component_fidelity | story_role | style_mismatch | none
  severity: BLOCKER | MAJOR | MINOR | NIT
  route: none | tikz_patch | svg_polish | semantic_backport | human_art_direction | accept_simplification
  evidence: "<crop/current-artifact evidence>"
  rationale: "<why this panel is or is not the limiting panel>"
```

## Acceptance

- [x] The brief asks the host LLM to identify the weakest panel or explicitly state
  none.
- [x] Non-`none` routes are constrained to existing route names and cannot
  bypass existing gates in this prompt-hardening slice.
- [ ] `fig_loop` and `ready_improvement_summary` can surface the weakest panel as
  optional only when no stronger blocker exists.
- [x] Legacy critiques remain parseable because this slice adds prompt text
  only and does not add a required schema field.

## Verification

- `uv run pytest -q tests/test_critique_brief.py::test_critique_brief_includes_weakest_panel_coherence_check tests/test_critique_brief.py::test_critique_brief_includes_aesthetic_antipattern_checklist`
  - Result: 2 passed.

## Review Questions

1. Can this mislabel a real blocker as optional? It must not.
2. Does it create useful action, or only subjective ranking?
3. Can it handle single-panel figures?
