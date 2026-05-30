"""Reusable rendered sections for the /fig_critique host-LLM brief."""

from __future__ import annotations

import critique_schema_vocab as vocab

PHYSICAL_CHECK_VALUES = (
    "cable_gravity | floating_components | spatial_proximity | "
    "direction_orientation | material_distinction"
)
QUALITY_VERDICT_VALUES = "pass | needs_patch | needs_human | block | not_applicable"
QUALITY_CONFIDENCE_VALUES = "low | medium | high"
QUALITY_ACTION_VALUES = "none | patch | human_review | revise_briefing | block_release"
PANEL_ROLE_VALUES = (
    "setup | mechanism | result | comparison | control | zoom | model | workflow | context"
)
PANEL_ROLE_QUALITY_VALUES = "clear | weak | missing | redundant"


def mandatory_audit_checklists() -> str:
    return """## Mandatory Audit Checklists (host LLM MUST enumerate)

The host LLM MUST fill every numbered audit family below in the resulting
`critique.md` under top-level YAML field `audit_enumeration`. Empty v1.1 audit
enumeration is invalid. Do not invent literature citations; use bounded
reference provenance values from the output schema.

### A. Structural Completeness Audit
For each instrument/component currently drawn in the figure, enumerate:
1. Component name -> mounting/support visible? (yes/no/N/A + 1-line rationale)
2. Connections (wires/cables) -- does each connection have BOTH endpoints
   visibly attached to a defined component?
3. Per the provided reference context, list 3 standard parts that exist in the
   real reference-system but are MISSING or weakly represented in the current
   rendering. For each, declare `intentional_omission` vs `incomplete`.

### B. Label-Target Matching Audit
For EVERY label/annotation in the figure (enumerate, do not summarize):
1. Label text -> visually-nearest drawn object.
2. Is that nearest object the INTENDED label target per briefing/spec/source?
3. If mismatch: propose ONE concrete fix (relocation coordinate, leader-line
   addition, OR rename).

### C. Physical Plausibility Audit
Enumerate at least 5 physical-plausibility checks specific to this figure:
1. Cables/wires -- do they follow gravity, or are they intentionally schematic?
2. Floating components -- list any drawn object with no visible support, mount,
   or frame attachment.
3. Spatial proximities -- list any two components whose drawn proximity
   contradicts real-system separation.
4. Direction/orientation -- list any arrow, modulation cue, or motion indicator
   whose direction conflicts with the labeled physics.
5. Material distinction -- verify each labeled material region is visually
   distinguishable from neighbors.

### D. Conceptual Completeness Audit
List 3 elements that SHOULD be present per provided reference/briefing context
but are weakly represented or missing entirely. For each, provide element name,
bounded reference provenance, severity, and proposed action.
    """


def journal_quality_axes() -> str:
    return """## Journal-Grade Quality Axes (host LLM MUST evaluate)

After completing `audit_enumeration`, evaluate every quality axis below under
top-level YAML field `quality_axes`. Do not collapse these axes into one opaque
score. Every `pass`, `needs_patch`, `needs_human`, or `block` verdict needs
concrete visible, briefing, reference, theory-guard, or finding evidence.
Use `not_applicable` only when the figure lacks the relevant input or structure.

### 1. Message and Storyline
Evaluate the one-sentence figure message, first-read order, relation to the
manuscript claim, missing story bridges, main-conclusion prominence, and
decorative/non-explanatory content.

### 2. Panel Role Coherence
Classify every panel role as setup, mechanism, result, comparison, control,
zoom, model, workflow, or context. Flag missing, redundant, weak, or misordered
panel roles.

### 3. Sub-region Integration
If sub-region context exists, evaluate active sub-region ids, integration with
stable regions, global imbalance from local fixes, detail-level mismatch, and
callout/zoom link correctness.

### 4. Component Fidelity
Evaluate component identity, support/mount/frame/stage, material boundaries,
wire/cable/arrow endpoints, standard missing parts, and whether omissions are
acceptable schematic simplifications.

### 5. Scientific Plausibility
Evaluate arrows, fields, flows, forces, charge motion, current, energy ordering,
scale/proximity, material/interface meaning, theory-guard invariants, and
mechanism-level label/object conflicts.

### 6. Composition and Layout
Evaluate visual hierarchy, reading path, spacing, alignment, density, white
space, relative scale, thumbnail readability, and whether the figure reads as
one coherent system instead of assembled fragments.

### 7. Label and Annotation Semantics
Evaluate every label-target audit item, terminology consistency, leader-line
necessity, label density, cross-panel label grammar, and annotation usefulness
versus clutter.

### 8. Journal Polish
Evaluate typography hierarchy, line-weight economy, palette economy, semantic
color consistency, export-scale contrast, schematic restraint, and absence of
decorative noise.

### 9. Reference Fidelity
When references exist, evaluate role/topology transfer, per-panel reference
crop comparisons, preserved key relations, intentional omissions versus
incomplete drawing, hallucinated additions, and source limitations.

### 10. Publication Readiness
Conservatively summarize whether the figure passes, needs a patch, needs human
review, or blocks release. This summary cannot be less severe than any
applicable upstream quality axis.
"""


def journal_grade_assessment() -> str:
    return """## Journal-Grade Fresh Re-Audit Assessment

After completing `quality_axes`, classify the current rendered/exported figure
under top-level YAML field `journal_grade_assessment`. This is not a progress
score. Re-audit the current artifact from scratch: earlier pass states can be
downgraded when a later patch introduces a new layout, story, label, or polish
regression.

Use `high_impact_candidate` only when all applicable upstream `quality_axes`
are passing, no human gate is required, and the current artifact reads above
ordinary manuscript quality. Use `needs_human_art_direction` when the remaining
decision is taste, story framing, target-journal fit, policy, or visual
direction that should not be decided by automation.

Scores are advisory fresh re-audit diagnostics. They are optional but
recommended when the current artifact can be scored with concrete visual,
briefing, reference, or theory-guard evidence. Scores are not cumulative progress
meters. A later loop may score lower if a patch introduces a new
defect or makes an old defect visible. Scores cannot override blockers, human
gates, stale exports, final-artifact gates, accepted/golden gates,
`quality_axes` verdicts, or `benchmark_level`. Do not invent journal acceptance
probabilities. If you emit any numeric score, emit the complete
`overall_score`, `sub_scores`, and `score_rationale` block.

When a `Reference-Calibrated Top-Tier Comparison` pack is present, scores cite
the reference pack. Fill `journal_grade_assessment.reference_calibration` with
the pack hash, reference class, visual ambition, limiting trait ids, and a
short rationale that explains why the score follows from the current artifact
versus the declared pack. Do not use the pack to unlock release or bypass any
non-passing audit slot.
"""


def top_tier_journal_audit() -> str:
    return """## Top-Tier Journal Figure Audit (host LLM MUST enumerate)

Before assigning `journal_grade_assessment`, enumerate the top-tier figure
review below under top-level YAML field `top_tier_audit`. These are not
decorative prompts. Each slot must name the concrete current-artifact weakness
or explain why the current artifact passes. If target journal is unknown, use a
generic high-impact schematic standard and mark target-specific art-direction
questions as `needs_human`.

Link rule: any `fail`, any `needs_human`, or any `weak` slot with
`blocks_high_impact: true` must be tied to downstream review evidence. Either
write a normal panel/top-level finding whose text explicitly mentions
`top_tier_audit.<slot_key>`, represent it in `quality_axes.blocking_items`
with the same `top_tier_audit.<slot_key>` reference and a human/revise/block
action, or justify the slot's `concrete_fix` with `accept_simplification`.

### 1. First-Glance Message
State what a qualified reader understands after 3 seconds, 10 seconds, and
30 seconds. Flag when the central claim is not visible without reading the full
caption.

### 2. Target-Journal Fit
Assess whether the figure fits the intended journal's schematic density,
typography, panel count, graphical-abstract flavor, and visual ambition. If the
target journal is not provided, assess against a generic high-impact materials
schematic standard.

### 3. Novelty and Claim Support
Assess whether the visual hierarchy supports the manuscript's central novelty
claim rather than merely showing components correctly.

### 4. Figure-Caption Coupling
Assess whether the figure carries the right explanatory burden: neither
overloaded with caption text nor too dependent on a future caption to be
understood.

### 5. Visual Economy
List removable ink, redundant marks, weak decorative texture, or missing marks
whose addition would reduce explanation cost.

### 6. Cross-Panel Semantic Grammar
Audit color, arrow, line, texture, icon, label, and material grammar across
panels. Same visual grammar should mean the same scientific role.

### 7. Reader Misinterpretation Risk
Name the most likely wrong interpretation a careful reader could make from the
current geometry, proximity, arrows, labels, or simplifications.

### 8. Reduction / Print Readability
Assess 1-column, 2-column, thumbnail, grayscale, projector, and print
readability. Flag labels, line weights, or contrast that fail under reduction.

### 9. Accessibility and Color Robustness
Assess colorblind safety, grayscale distinction, contrast, and redundant
encoding through shape, texture, line style, or labels.

### 10. Aesthetic Coherence
Assess whether the figure has one coherent visual authority: consistent detail
level, line-weight economy, depth cues, icon style, material rendering, and
typographic hierarchy.
"""


def editorial_art_direction_audit(*, require_route_detail: bool = False) -> str:
    route_detail = ""
    if require_route_detail:
        route_detail = """ The route is not implied by `verdict`; `verdict`
only grades whether the routing judgment is well supported. If
`recommended_path: continue_tikz`, fill `remaining_tikz_lever` with the single
bounded source-level adjustment still available. If
`recommended_path: ready_for_svg_polish`, fill `svg_polish_candidate_reason`
with the evidence that semantic/source-level work is closed and only optical
vector cleanup remains. If `semantic_backport_required`, fill
`semantic_backport_reason`. If `needs_human_art_direction`, fill
`human_art_direction_reason`."""
    return f"""## Editorial Art-Direction Audit (host LLM MUST evaluate)

After completing `top_tier_audit`, evaluate every editorial art-direction slot
below under top-level YAML field `editorial_art_direction`. This block is about
illustration register, narrative force, and the TikZ-vs-SVG polish boundary. It
does not authorize source edits or SVG edits.

Link rule: any `needs_human` slot must be tied to downstream review evidence.
Write a normal panel/top-level finding whose text explicitly mentions
`editorial_art_direction.<slot_key>`, or represent it in
`quality_axes.blocking_items` with the same `editorial_art_direction.<slot_key>`
reference and a human/revise/block action. needs_human editorial slots cannot
use accept_simplification to bypass human visibility. For `fail` or `weak` plus
`blocks_high_impact: true`, the same link paths are valid, or
`concrete_fix` may use `accept_simplification` only when the weakness is an
intentional simplification.

### 1. Hero Focus
Name the hero object, hero panel, or central visual claim. Flag weak/fail if
the reader has no obvious first fixation or every panel has equal weight.

### 2. Narrative Choreography
Assess whether the figure flows through problem, mechanism, evidence, and
implication, or whether it reads as assembled fragments.

### 3. Illustration Readiness
Assess whether the artifact reads as editorial illustration rather than a plain
schematic. Consider depth cues, material rendering, dimensionality,
highlight/shadow discipline, and target-journal register.

### 4. Abstraction Consistency
Assess whether icon, cartoon, pseudo-3D, data-plot, and diagram registers are
intentionally mixed and visually controlled.

### 5. Reference-Class Fit
Classify the current artifact and target class, e.g.
`nature_communications_mechanism_schematic`, `nature_materials_main_schematic`,
`science_conceptual_mechanism`, `graphical_abstract`, `cover_candidate`, or
`ordinary_manuscript_schematic`.

### 6. Visual Identity
Assess whether the figure has a memorable visual motif: color grammar,
material texture, charge glyph, energy landscape, trap motif, arrow grammar, or
another coherent visual language.

### 7. Claim Payload Fit
Assess whether the manuscript's central claim receives the most visual weight.
Flag weak/fail if correct components are present but the novelty is secondary.

### 8. Aesthetic Risk
Name concrete signs of amateurism or non-editorial rendering: clip-art feeling,
inconsistent stroke weights, awkward gradients, overdecorated backgrounds,
mismatched icons, crowded text, weak whitespace, or accidental color choices.

### 9. TikZ-vs-SVG Polish Trigger
Decide whether the remaining gap should stay in TikZ or move to controlled SVG
polish. This slot must include `recommended_path` with one of:
`continue_tikz`, `ready_for_svg_polish`, `needs_human_art_direction`, or
`semantic_backport_required`.{route_detail}

### 10. Human Art-Direction Gate
State whether a human should choose target-journal style, hero-panel priority,
cover-style ambition, SVG polish scope, or schematic-vs-dimensional register
before the next loop.
"""


def _quality_axis_schema(axis_name: str, *, evidence: str, rationale: str) -> str:
    return "\n".join(
        [
            f"  {axis_name}:",
            f"    verdict: {QUALITY_VERDICT_VALUES}",
            f"    confidence: {QUALITY_CONFIDENCE_VALUES}",
            f"    rationale: \"<{rationale}>\"",
            f"    evidence: \"<{evidence}>\"",
            "    blocking_items: []",
            f"    recommended_action: {QUALITY_ACTION_VALUES}",
        ]
    )


def quality_axes_schema() -> str:
    axis_schema = {
        "message_storyline": _quality_axis_schema(
            "message_storyline",
            rationale="message/story verdict rationale",
            evidence="visible evidence, briefing/spec reference, or finding id",
        ),
        "panel_role_coherence": "\n".join(
            [
                "  panel_role_coherence:",
                f"    verdict: {QUALITY_VERDICT_VALUES}",
                f"    confidence: {QUALITY_CONFIDENCE_VALUES}",
                "    rationale: \"<panel role coherence summary>\"",
                "    evidence: \"<panel ids and visual evidence>\"",
                "    panel_roles:",
                "      - panel_id: \"<id>\"",
                f"        role: {PANEL_ROLE_VALUES}",
                f"        role_quality: {PANEL_ROLE_QUALITY_VALUES}",
                "        rationale: \"<one-line>\"",
                "    blocking_items: []",
                f"    recommended_action: {QUALITY_ACTION_VALUES}",
            ]
        ),
        "subregion_integration": _quality_axis_schema(
            "subregion_integration",
            rationale="sub-region/global integration summary",
            evidence="subregion id, log evidence, or visible evidence",
        ),
        "component_fidelity": _quality_axis_schema(
            "component_fidelity",
            rationale="component fidelity summary",
            evidence="component audit ids or visible evidence",
        ),
        "scientific_plausibility": _quality_axis_schema(
            "scientific_plausibility",
            rationale="scientific plausibility summary",
            evidence="theory guard, briefing invariant, or visible evidence",
        ),
        "composition_layout": _quality_axis_schema(
            "composition_layout",
            rationale="layout/composition summary",
            evidence="visible evidence, checker output, or finding id",
        ),
        "label_annotation_semantics": _quality_axis_schema(
            "label_annotation_semantics",
            rationale="label semantics summary",
            evidence="label-target audit ids or visible evidence",
        ),
        "journal_polish": _quality_axis_schema(
            "journal_polish",
            rationale="polish summary",
            evidence="visible evidence or export-scale issue",
        ),
        "reference_fidelity": _quality_axis_schema(
            "reference_fidelity",
            rationale="reference fidelity summary",
            evidence="reference path, panel id, or reference_pack note",
        ),
        "publication_readiness": _quality_axis_schema(
            "publication_readiness",
            rationale="conservative readiness summary",
            evidence="axis verdict summary",
        ),
    }
    return "quality_axes:\n" + "\n".join(
        axis_schema[axis_name] for axis_name in vocab.QUALITY_AXIS_NAMES
    )


def editorial_art_direction_schema(*, require_route_detail: bool = False) -> str:
    lines = ["editorial_art_direction:"]
    for key in vocab.EDITORIAL_AUDIT_KEYS:
        lines.extend(
            [
                f"  {key}:",
                "    verdict: pass | weak | fail | needs_human",
                '    evidence: "<specific current-artifact evidence>"',
                '    rationale: "<why this matters for target-journal illustration quality>"',
                '    concrete_fix: "<specific edit, polish handoff, or accept_simplification>"',
                "    blocks_high_impact: true | false",
            ]
        )
        if key == "tikz_vs_svg_polish_trigger":
            lines.extend(
                [
                    "    recommended_path: continue_tikz | ready_for_svg_polish | "
                    "needs_human_art_direction | semantic_backport_required",
                ]
            )
            if require_route_detail:
                lines.extend(
                    [
                        (
                            '    remaining_tikz_lever: "<required when '
                            'recommended_path=continue_tikz>"'
                        ),
                        (
                            '    svg_polish_candidate_reason: "<required when '
                            'recommended_path=ready_for_svg_polish>"'
                        ),
                        (
                            '    semantic_backport_reason: "<required when '
                            'recommended_path=semantic_backport_required>"'
                        ),
                        (
                            '    human_art_direction_reason: "<required when '
                            'recommended_path=needs_human_art_direction>"'
                        ),
                    ]
                )
    return "\n".join(lines)


def journal_grade_assessment_schema(
    critique_input_hash: str,
    reference_calibration: dict[str, str] | None = None,
) -> str:
    lines = [
        "journal_grade_assessment:",
        "  schema: figure-agent.journal-grade-assessment.v1",
        "  scoring_mode: fresh_reaudit",
        f"  assessed_artifact_hash: {critique_input_hash}",
        (
            "  benchmark_level: draft | solid_manuscript | "
            "high_impact_candidate | needs_human_art_direction | blocked"
        ),
        f"  confidence: {QUALITY_CONFIDENCE_VALUES}",
        "  blockers: []",
        "  regression_detected: true | false",
        "  regressions: []",
        "  score_is_gateable: true | false",
        (
            "  next_quality_bottleneck: storyline | composition | "
            "component_fidelity | scientific_plausibility | label_semantics | "
            "polish | reference_fidelity | export_scale_readability | human_policy"
        ),
        '  rationale: "<current artifact-only quality rationale>"',
        "  overall_score: 0-100",
        "  sub_scores:",
        "    storyline: 0-100",
        "    composition: 0-100",
        "    component_fidelity: 0-100",
        "    scientific_plausibility: 0-100",
        "    label_semantics: 0-100",
        "    polish: 0-100",
        "    reference_fidelity: 0-100",
        "    export_scale_readability: 0-100",
        '  score_rationale: "<why these numbers describe only the current artifact>"',
    ]
    if reference_calibration is not None:
        lines.extend(
            [
                "  reference_calibration:",
                f"    reference_pack_hash: {reference_calibration['reference_pack_hash']}",
                f"    reference_class: {reference_calibration['reference_class']}",
                f"    visual_ambition: {reference_calibration['visual_ambition']}",
                "    score_basis: current_artifact_vs_pack",
                "    limiting_reference_traits:",
                "      - <trait id from critique_reference_pack.yaml>",
                '    rationale: "<why scores cite the reference pack>"',
            ]
        )
    return "\n".join(lines)
