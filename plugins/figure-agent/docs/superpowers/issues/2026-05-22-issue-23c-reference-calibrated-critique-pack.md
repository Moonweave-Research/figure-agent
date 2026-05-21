# Issue 23C: Reference-Calibrated Critique Pack

**Date:** 2026-05-22 KST
**Status:** planned
**Type:** top-tier critique calibration
**Parent:** `2026-05-22-issue-23-zoom-and-reference-calibrated-audit-roadmap.md`
**Blocked by:** Issue 23B recommended

## What to build

Add optional fixture-level reference calibration through
`examples/<name>/critique_reference_pack.yaml`. The pack tells `/fig_critique`
what the figure should be compared against: target journal, reference class,
visual ambition, exemplar references, must-match traits, must-avoid traits, and
calibration questions.

This makes "Nature/Science-level" critique less dependent on generic host-LLM
taste and more grounded in explicit project-specific standards.

## Proposed Pack Shape

```yaml
schema: figure-agent.critique-reference-pack.v1
fixture: <name>
target_journal: Nature Communications | Nature Materials | Science | ACS | internal | unknown
reference_class: mechanism_schematic | apparatus_schematic | multipanel_story | data_plus_schematic | graphical_abstract
visual_ambition: draft | solid_manuscript | high_impact_candidate | cover_style
comparison_references:
  - id: R001
    source: provided_reference | paper | briefing | human_note
    path_or_citation: "<relative path or citation>"
    role: layout | style | component_fidelity | storyline | journal_register
must_match_traits:
  - id: T001
    trait: "<specific trait the current figure should match>"
    reference_id: R001
must_avoid_traits:
  - id: A001
    trait: "<specific anti-pattern to avoid>"
    severity: BLOCKER | MAJOR | MINOR | NIT
calibration_questions:
  - id: Q001
    question: "<targeted comparison question for host critique>"
```

Implementation may adjust exact enum values, but it should keep the pack small,
human-authorable, and deterministic.

## Acceptance Criteria

- [ ] Pack parser loads valid `critique_reference_pack.yaml`.
- [ ] Malformed pack produces controlled errors.
- [ ] `/fig_critique` brief includes a
  `## Reference-Calibrated Top-Tier Comparison` section when the pack exists.
- [ ] The brief asks the host LLM to evaluate every must-match trait,
  must-avoid trait, and calibration question.
- [ ] Missing pack is allowed and preserves current behavior.
- [ ] Pack content is included in critique input hashing so pack edits make old
  critiques stale.
- [ ] If pack semantics change the required critique output contract, the
  implementation bumps the rubric version rather than silently changing prompt
  meaning under the same version.
- [ ] Tests cover valid pack, missing pack, malformed pack, brief inclusion, and
  freshness impact.

## Suggested Files

- `scripts/critique_reference_pack.py`
- `scripts/critique_brief.py`
- `scripts/quality_manifest.py`
- `tests/test_critique_reference_pack.py`
- `tests/test_critique_brief.py`
- `tests/test_quality_manifest.py`

## Verification

```bash
uv run pytest -q tests/test_critique_reference_pack.py tests/test_critique_brief.py tests/test_quality_manifest.py
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

## Non-Goals

- No automatic web search.
- No copyrighted image ingestion.
- No automatic claim that a figure meets a journal standard.
- No requirement that every fixture has a reference pack.
