# Critique Structural Audit v1.1 Design

**Date:** 2026-05-18
**Issue:** Issue 6A
**Status:** design ready

## Purpose

`/fig_critique` currently asks the host LLM to classify findings into broad
categories. Dogfood showed that broad categories are treated as bins for already
noticed defects, not as mandatory prompts to search for missing structure.

This design upgrades the critique contract to v1.1 by adding a mandatory
`audit_enumeration` block. The goal is to force enumeration before conclusions:
what components exist, what labels point to, what physics looks plausible, and
what standard real-system elements are missing or weakly represented.

## Current Contract

`scripts/critique_brief.py` emits a host-LLM prompt with:

- render path,
- author intent,
- physics invariants,
- optional reference-conditioned authoring context,
- line-numbered TikZ source,
- a two-part critique rubric,
- a schema v1 output format.

The generated critique is written by the host LLM to
`examples/<name>/critique.md` as YAML frontmatter plus Markdown body.

Freshness is hash-based when metadata exists. `quality_manifest.py` owns
`CRITIQUE_RUBRIC_VERSION`, and `/fig_status` uses that value when deciding
whether an existing critique is fresh.

## Design Decision

Implement a narrow schema/rubric slice:

- New critique schema: `figure-agent.critique.v1.1`
- New rubric version: `figure-agent.critique-rubric.v1.1`
- New required frontmatter field for v1.1: `audit_enumeration`
- Legacy `figure-agent.critique.v1` remains parseable.
- v1.1 critiques with missing or empty audit blocks are rejected by
  `/fig_adjudicate` scaffold with a controlled `CritiqueAdjudicationError`.

Do not add `/fig_loop` state in this slice. `audit_incomplete` can be a later
integration issue if the adjudication-level rejection is not enough.

## Mandatory Brief Section

Insert this top-level section after `## Source under review (TikZ)` and before
`## Critique rubric` or `## Output format`:

```markdown
## Mandatory Audit Checklists (host LLM MUST enumerate)
```

The section must require four enumerations:

### A. Structural Completeness Audit

For each instrument/component currently drawn:

1. component name,
2. mounting/support visible,
3. visible connection endpoint audit,
4. one-line rationale.

Also list three standard real-system parts from provided references or briefing
context that are missing or weakly represented. Each must be marked as
`intentional_omission` or `incomplete`.

### B. Label-Target Matching Audit

For every visible label or annotation:

1. label text,
2. visually-nearest drawn object,
3. intended target from briefing/spec/source context,
4. match boolean,
5. one concrete fix when mismatched.

### C. Physical Plausibility Audit

Enumerate checks for:

- cable gravity,
- floating components,
- spatial proximity,
- direction/orientation,
- material distinction.

### D. Conceptual Completeness Audit

List three expected real-system elements that are missing or weak. Reference
provenance must be bounded. The host LLM may not invent paper citations.

Allowed `reference` values:

- `provided_reference`
- `briefing`
- `reference_pack`
- `not_provided`

## v1.1 YAML Shape

The output format must include:

```yaml
audit_enumeration:
  structural_completeness:
    components:
      - component: <name>
        mount_support: yes|no|N/A
        rationale: "<one-line>"
        connections: "<endpoint audit>"
    missing_from_reference:
      - element: <name>
        status: intentional_omission | incomplete
        rationale: "<one-line>"
  label_target_matching:
    - label: "<text>"
      nearest_object: "<drawn-object-name>"
      intended_target: "<from-briefing-or-spec>"
      matches: true | false
      proposed_fix: "<concrete or empty if matches=true>"
  physical_plausibility:
    - check: cable_gravity | floating_components | spatial_proximity | direction_orientation | material_distinction
      finding: "<what was observed>"
      verdict: convention_acceptable | structural_defect
  conceptual_completeness:
    - element: <name>
      reference: provided_reference | briefing | reference_pack | not_provided
      severity: BLOCKER | MAJOR | MINOR | NIT
      proposed_action: add | expand | accept_simplification
```

## Audit-to-Finding Rule

The brief must tell the host LLM:

- Any `structural_defect`, `incomplete`, `BLOCKER`, or `MAJOR` audit item must
  either appear as a normal panel/top-level finding or be explicitly justified
  as `accept_simplification`.
- The loop and adjudication layers continue to consume normal findings. Audit
  enumeration is evidence, not a replacement for actionable findings.

## Legacy Behavior

Legacy v1 critique files:

- remain parseable,
- can still scaffold adjudication,
- do not require `audit_enumeration`,
- may emit a deprecation warning in CLI output, but must not crash solely
  because they are v1.

v1.1 critique files:

- must include all four audit blocks,
- must have non-empty `structural_completeness.components`,
  `structural_completeness.missing_from_reference`,
  `label_target_matching`, `physical_plausibility`, and
  `conceptual_completeness`,
- fail scaffold validation if any required block is missing, wrongly typed, or
  empty,
- fail scaffold validation if any audit list contains a non-mapping item,
- fail scaffold validation if a known `figure-agent.critique.*` schema value is
  unsupported, because schema typos must not bypass v1.1 validation.

## Files

- `scripts/critique_brief.py`
- `scripts/quality_manifest.py`
- `scripts/critique_adjudication.py`
- `commands/fig_critique.md`
- `tests/test_critique_brief.py`
- `tests/test_critique_adjudication.py`
- `tests/test_status.py`
- `tests/test_run_export.py`

## Testing Strategy

Use temp fixtures for automated tests. Do not depend on
`fig1_overview_v2_pair_001_vault`, because it is an active dirty dogfood
fixture.

Required tests:

- brief contains mandatory checklist heading and A/B/C/D headers,
- brief output format uses schema v1.1,
- brief output format uses rubric v1.1,
- v1 critique remains legacy-parseable by adjudication scaffold,
- v1.1 critique with complete `audit_enumeration` scaffolds,
- v1.1 critique with missing audit block fails cleanly,
- v1.1 critique with empty audit list fails cleanly,
- v1.1 critique with malformed audit list item fails cleanly,
- unsupported known critique schema fails cleanly,
- status/run_export tests are updated for rubric v1.1 freshness expectations.

## Verification

Run from `plugins/figure-agent`:

```bash
uv run pytest -q tests/test_critique_brief.py tests/test_critique_adjudication.py tests/test_status.py tests/test_run_export.py
uv run pytest
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

## Risks

- Bumping rubric version intentionally marks existing hash-metadata critiques
  stale. This is expected because the critique instructions changed.
- If `/fig_critique.md` is not updated, the command and generator will disagree.
- If audit enumeration is not connected to normal findings by instruction, the
  host LLM may hide severe defects inside audit text only.
- If free-form paper citations are required, the host LLM may hallucinate
  literature. Use bounded reference provenance instead.
