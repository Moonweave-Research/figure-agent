# Issue 97B - Weakest-Panel Coherence Summary

Status: implemented through schema v1.17

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
weakest_panel_coherence:
  panel_id: <panel id or none>
  subregion_id: <subregion id or none>
  weakness_type: composition | typography | color | density | component_fidelity | story_role | style_mismatch | none
  route: none | tikz_patch | svg_polish | semantic_backport | human_art_direction | accept_simplification
  evidence: "<crop/current-artifact evidence>"
  rationale: "<why this panel is or is not the limiting panel>"
  linked_evidence:
    - quality_axes.<axis> | top_tier_audit.<slot> | editorial_art_direction.<slot> | finding id | micro_defect id
```

## Acceptance

- [x] The brief asks the host LLM to identify the weakest panel or explicitly state
  none.
- [x] Non-`none` routes are constrained to existing route names and cannot
  bypass existing gates in this prompt-hardening slice.
- [x] Schema v1.17 requires `weakest_panel_coherence` for grounded critiques.
- [x] Non-`none` weakness must choose a non-`none` route and linked evidence.
- [x] Legacy v1.16 and older critiques remain parseable.

## Verification

- `uv run pytest -q tests/test_critique_brief.py::test_critique_brief_includes_weakest_panel_coherence_check tests/test_critique_brief.py::test_critique_brief_includes_aesthetic_antipattern_checklist`
  - Result: 2 passed.
- `uv run pytest -q tests/test_critique_schema_validator.py tests/test_critique_brief.py tests/test_quality_manifest.py tests/test_status.py::test_hash_metadata_accepts_v1_17_rubric_for_audit_crop_manifest`
  - Result: 183 passed.

## Review Questions

1. Can this mislabel a real blocker as optional? It must not.
2. Does it create useful action, or only subjective ranking?
3. Can it handle single-panel figures?
