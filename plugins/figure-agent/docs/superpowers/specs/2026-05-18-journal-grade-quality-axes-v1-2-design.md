# Journal-Grade Figure Quality Axes v1.2 Design

**Date:** 2026-05-18
**Issue:** Issue 6B
**Status:** design ready

## Purpose

`figure-agent` must repeatedly ask whether a figure is becoming a strong
scientific figure, not merely whether it compiles or lacks obvious label
collisions. Issue 6A added mandatory structural audit enumeration to
`/fig_critique`. Issue 6B adds a broader quality-axis contract for
journal-grade figure readiness.

The intent is not to claim that the plugin can guarantee Nature, Science,
Nature Materials, or Nature Communications acceptance. The intent is to force
every loop to inspect the same high-impact-figure concerns: story, panel role,
sub-region integration, component fidelity, scientific plausibility,
composition, label semantics, polish, reference fidelity, and publication
readiness.

## Current State

The current workflow already has useful layers:

- `/fig_compile` runs style lock, compile, collision, visual clash, optional
  layout drift, and perception pack generation.
- `/fig_critique` uses the host LLM as the vision critic and now requires
  `audit_enumeration` in schema v1.1.
- `/fig_adjudicate` scaffolds finding decisions from `critique.md`.
- `/fig_loop` records axis verdict slots, patch handoff, and stop reasons, but
  several quality axes still remain `not_evaluated`.

The gap is that the loop lacks a durable, required quality-axis schema. A
critique can list findings but still fail to say whether the whole figure has a
coherent scientific story, panel-level logic, high-impact visual hierarchy, or
publication-grade polish.

## Design Decision

Introduce critique schema v1.2:

- `schema: figure-agent.critique.v1.2`
- `rubric_version: figure-agent.critique-rubric.v1.2`
- keep v1.1 `audit_enumeration`
- add required top-level `quality_axes`
- preserve v1 and v1.1 as legacy-parseable contracts
- validate v1.2 shape before adjudication scaffold
- do not implement hidden patching, compile/export changes, or acceptance
  automation in this issue

Quality axes must remain separate. A compact summary is allowed, but a single
opaque score must not replace the raw axis verdicts.

## Allowed Values

Common axis fields use bounded values so malformed critiques cannot silently
enter the loop.

| Field | Allowed values |
|---|---|
| `verdict` | `pass`, `needs_patch`, `needs_human`, `block`, `not_applicable` |
| `confidence` | `low`, `medium`, `high` |
| `recommended_action` | `none`, `patch`, `human_review`, `revise_briefing`, `block_release` |
| `panel_roles[].role` | `setup`, `mechanism`, `result`, `comparison`, `control`, `zoom`, `model`, `workflow`, `context` |
| `panel_roles[].role_quality` | `clear`, `weak`, `missing`, `redundant` |

Severity order for readiness aggregation is:

```text
pass < needs_patch < needs_human < block
```

`not_applicable` removes an axis from aggregation; it is not passing evidence.

## Required Quality Axes

### 1. `message_storyline`

Question: does the whole figure communicate a clear scientific claim?

Audit items:

- one-sentence figure message,
- first-read order and whether it matches the intended story,
- relationship between figure content and manuscript claim,
- missing bridge between setup, mechanism, result, or implication,
- whether the main conclusion is visually prominent,
- whether any panel or annotation is decorative rather than explanatory.

Common failures:

- locally polished panels with no global story,
- important result hidden behind secondary decoration,
- mechanism and result panels disconnected,
- figure requires too much caption text to understand the core message.

### 2. `panel_role_coherence`

Question: does each panel have a necessary role in the figure?

Each panel must be classified as one of:

- `setup`
- `mechanism`
- `result`
- `comparison`
- `control`
- `zoom`
- `model`
- `workflow`
- `context`

Audit items:

- role of each panel,
- whether any role is duplicated without purpose,
- whether a required role is missing,
- whether panel order supports the story,
- whether panel scale, label grammar, and visual density are consistent.

### 3. `subregion_integration`

Question: do local edits and active sub-regions fit the whole figure?

Audit items:

- active sub-region ids from `subregion_iteration_log.md`,
- whether active sub-regions are visually integrated with stable regions,
- whether local fixes created global imbalance,
- whether one region has mismatched detail level, line weight, or color grammar,
- whether callouts and zoom links connect to the correct source region.

This axis is `not_applicable` when no sub-region context exists.

### 4. `component_fidelity`

Question: are individual components recognizable, structurally credible, and
scientifically meaningful?

Audit items:

- component identity and recognizability,
- required support, mount, frame, or stage,
- material boundaries,
- endpoint visibility for wires, cables, arrows, and connectors,
- missing standard parts from references or briefing,
- whether omissions are schematic simplifications or incomplete drawing.

This axis consumes v1.1 `audit_enumeration.structural_completeness` as evidence
but gives a figure-quality verdict rather than just a list.

### 5. `scientific_plausibility`

Question: does the schematic avoid misleading science?

Audit items:

- direction of arrows, fields, flows, forces, charge motion, and current,
- energy ordering and band/level relations,
- scale/proximity consistency for the represented physical system,
- material identity and interface meaning,
- theory-guard invariants,
- mechanism-level conflicts between labels and drawn objects.

This axis must use `needs_human` when the host LLM cannot judge a scientific
claim from provided evidence.

### 6. `composition_layout`

Question: is the composition natural, balanced, and readable beyond mechanical
collision absence?

Audit items:

- visual hierarchy,
- reading path,
- spacing and alignment,
- density and white space,
- relative scale of panels and components,
- thumbnail readability,
- whether the figure reads as a coherent system rather than assembled fragments,
- whether callouts, arrows, and labels interrupt the main visual path.

This axis complements, but does not replace, collision, visual clash, and layout
drift scripts.

### 7. `label_annotation_semantics`

Question: do labels and annotations identify the right objects with the right
meaning?

Audit items:

- every label in v1.1 `label_target_matching`,
- nearest object versus intended target,
- terminology consistency with briefing/spec/theory guard,
- leader-line necessity,
- label density,
- cross-panel label grammar consistency,
- annotation usefulness versus clutter.

### 8. `journal_polish`

Question: does the figure have the restraint and finish expected of a strong
scientific schematic?

Audit items:

- typography hierarchy,
- line weight economy,
- palette economy and semantic consistency,
- contrast at export scale,
- overuse of gradients, shadows, textures, or pseudo-3D,
- absence of decorative noise,
- consistent schematic style across panels,
- readability after downscaling.

This axis must not enforce a single journal house style. It must reject
obvious amateur, cluttered, inconsistent, or over-decorated presentation.

### 9. `reference_fidelity`

Question: were references translated by role, topology, and visual grammar
rather than copied or ignored?

Audit items:

- figure-level reference role,
- per-panel reference crop comparisons,
- preserved topology and key relations,
- intentional omissions versus incomplete drawing,
- hallucinated additions not supported by reference/briefing,
- whether reference limitations are respected.

This axis is `not_applicable` when no reference input exists.

### 10. `publication_readiness`

Question: what is the conservative next decision for manuscript use?

Audit items:

- whether any axis is `block`,
- whether any axis requires domain/human review,
- whether remaining work is patchable by an outer agent,
- whether the figure is suitable only as a draft,
- whether export/accepted/golden state must stay gated.

This axis is a summary verdict, not a replacement for the other axes.

## v1.2 YAML Shape

The output format must include `quality_axes` after `audit_enumeration` and
before `panels`.

```yaml
quality_axes:
  message_storyline:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<why this verdict was chosen>"
    evidence: "<visible evidence, briefing/spec reference, or critique finding id>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
  panel_role_coherence:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<role coherence summary>"
    evidence: "<panel ids and visual evidence>"
    panel_roles:
      - panel_id: "<id>"
        role: setup | mechanism | result | comparison | control | zoom | model | workflow | context
        role_quality: clear | weak | missing | redundant
        rationale: "<one-line>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
  subregion_integration:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<sub-region/global integration summary>"
    evidence: "<subregion id, log evidence, or visible evidence>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
  component_fidelity:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<component fidelity summary>"
    evidence: "<component audit ids or visible evidence>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
  scientific_plausibility:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<scientific plausibility summary>"
    evidence: "<theory guard, briefing invariant, or visible evidence>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
  composition_layout:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<layout/composition summary>"
    evidence: "<visible evidence, checker output, or critique finding id>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
  label_annotation_semantics:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<label semantics summary>"
    evidence: "<label-target audit ids or visible evidence>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
  journal_polish:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<polish summary>"
    evidence: "<visible evidence or export-scale issue>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
  reference_fidelity:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<reference fidelity summary>"
    evidence: "<reference path, panel id, or reference_pack note>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
  publication_readiness:
    verdict: pass | needs_patch | needs_human | block | not_applicable
    confidence: low | medium | high
    rationale: "<conservative readiness summary>"
    evidence: "<axis verdict summary>"
    blocking_items: []
    recommended_action: none | patch | human_review | revise_briefing | block_release
```

When an axis has concrete blockers, `blocking_items` must contain concise
strings:

```yaml
blocking_items:
  - "Panel C is visually redundant with Panel B and weakens the story."
```

## Validation Rules

`critique_adjudication.py scaffold` must reject v1.2 critiques when any of
these conditions is true:

- `quality_axes` is missing or is not a mapping.
- Any required axis is missing.
- Any axis is not a mapping.
- Any required common field is missing.
- `verdict`, `confidence`, or `recommended_action` has an unsupported value.
- `blocking_items` is not a list.
- `rationale` or `evidence` is empty for `pass`, `needs_patch`,
  `needs_human`, or `block`.
- `needs_patch` or `block` has an empty `blocking_items` list.
- `recommended_action` conflicts with `verdict`:
  - `pass` and `not_applicable` require `none`,
  - `needs_patch` requires `patch` or `revise_briefing`,
  - `needs_human` requires `human_review` or `revise_briefing`,
  - `block` requires `block_release` or `human_review`.
- `panel_role_coherence.panel_roles` is missing, not a list, or contains a
  non-mapping item when the axis is applicable.
- `panel_roles[].role` or `panel_roles[].role_quality` has an unsupported
  value.
- `publication_readiness.verdict` is less severe than any applicable upstream
  axis verdict.
- `publication_readiness.verdict` is `not_applicable` while any upstream axis
  is applicable.

## Readiness Summary Rule

The host LLM may emit a compact `publication_readiness` summary, but the plugin
must not collapse all axes into one opaque numeric score.

Recommended conservative rule:

- If any axis verdict is `block`, `publication_readiness.verdict` must be
  `block`.
- If any axis verdict is `needs_human`, `publication_readiness.verdict` must be
  `needs_human` unless a more severe `block` exists.
- If any axis verdict is `needs_patch`, `publication_readiness.verdict` must be
  `needs_patch` unless a more severe verdict exists.
- `pass` requires all applicable axes to be `pass`.
- `not_applicable` axes do not count as passing evidence; they only remove the
  axis from this figure's scope.
- `publication_readiness` cannot be `not_applicable` when any upstream axis is
  applicable, because it is the conservative readiness summary for the figure.

Implementation must enforce the same rule deterministically during v1.2
validation. The host LLM may explain the summary, but it must not be trusted to
calculate severity ordering correctly.

## Audit-to-Finding Rule

Every `block` and every `needs_patch` axis must be connected to at least one of:

- a top-level `findings[]` item,
- a `panels[].findings[]` item,
- a `blocking_items[]` entry whose `recommended_action` is `human_review` or
  `revise_briefing`.

The quality axes are not allowed to hide actionable problems in prose. If an
axis says `needs_patch`, the normal finding/adjudication path must be able to
see what should be patched.

For machine validation, `patch` and `block_release` actions are considered
connected only when the axis `blocking_items` text references an existing
panel/top-level finding id such as `C001 - <reason>` or `P001 - <reason>`.
Human-review and
revise-briefing actions may remain as blocking-item-only handoffs.

## Automation Boundaries

### Machine-checkable

- compile success,
- style lock,
- text collision,
- visual clash candidates,
- optional layout drift,
- export freshness,
- critique freshness,
- presence and shape of `audit_enumeration`,
- presence and shape of `quality_axes`,
- bounded enum values.

### Host-LLM audit

- message/storyline clarity,
- panel role necessity,
- component recognizability,
- reference role transfer,
- composition naturalness,
- journal polish,
- broad scientific plausibility from visible evidence.

### Human/domain gate

- new mechanism interpretation,
- theory correctness not established by `theory_guard.md`,
- reference ambiguity,
- whether simplification is acceptable for the paper claim,
- final manuscript/publication acceptance,
- accepted/golden state promotion.

The plugin aims to make human gates rarer by surfacing better evidence, but it
must not pretend that journal-level scientific judgment is fully automatic.

## Loop Integration

Issue 6B must not implement `/fig_loop` changes directly unless explicitly
scoped in a follow-up implementation plan. The design target is:

- `/fig_critique` writes `quality_axes`.
- `/fig_adjudicate` validates v1.2 shape before scaffolding.
- A follow-up issue maps `quality_axes` into `/fig_loop.axis_verdicts`.
- `story_hierarchy`, `reference_fidelity`, and `publication_safety` should stop
  being permanent placeholders once v1.2 critiques exist.

## Backward Compatibility

Legacy behavior:

- v1 critiques remain parseable as legacy.
- v1.1 critiques remain parseable and continue to require
  `audit_enumeration`.
- v1.2 critiques require both `audit_enumeration` and `quality_axes`.
- existing examples are not migrated automatically.
- rubric v1.2 intentionally marks old hash-metadata critiques stale.

## Files For Implementation

Expected implementation files:

- `scripts/critique_brief.py`
- `scripts/quality_manifest.py`
- `scripts/critique_adjudication.py`
- `commands/fig_critique.md`
- `tests/test_critique_brief.py`
- `tests/test_critique_adjudication.py`
- `tests/test_status.py`
- `tests/test_run_export.py`

Optional follow-up integration files:

- `scripts/fig_loop.py`
- `commands/fig_loop.md`
- `tests/test_fig_loop.py`

## Required Tests

Future implementation must cover:

- brief contains a top-level journal-grade quality axes section,
- brief schema/rubric strings are v1.2,
- brief output schema includes all required `quality_axes`,
- v1 and v1.1 critique files remain legacy-parseable,
- v1.2 critique with complete `quality_axes` scaffolds adjudication,
- v1.2 critique missing one required axis fails cleanly,
- v1.2 critique with invalid verdict fails cleanly,
- v1.2 critique with invalid confidence fails cleanly,
- v1.2 critique with invalid recommended action fails cleanly,
- v1.2 critique with non-list `blocking_items` fails cleanly,
- `publication_readiness` cannot pass when another applicable axis blocks,
- status/export freshness tests are updated for rubric v1.2.

## Open Risks

- The schema can force the host LLM to answer each axis, but it cannot prove the
  answer is correct. Dogfood runs and adversarial reviews are still needed.
- A long axis schema can make `critique.md` verbose. This is acceptable if it
  improves loop evidence, but the brief must keep field names stable and
  concise.
- If the host LLM overuses `pass`, the loop may become falsely optimistic. The
  prompt must require concrete evidence for each passing axis.
- If the host LLM overuses `needs_human`, automation stalls. The prompt must
  reserve `needs_human` for domain ambiguity, reference ambiguity, or
  mechanism-level uncertainty.
- If `quality_axes` are not connected to normal findings, patches will remain
  hard to select. The audit-to-finding rule is therefore mandatory.

## Next Step

Create a TDD implementation plan for Issue 6B only after this design is
accepted. The first implementation slice must update `/fig_critique` and
`/fig_adjudicate` only. `/fig_loop` ingestion should be a follow-up slice after
the v1.2 critique contract is stable.
