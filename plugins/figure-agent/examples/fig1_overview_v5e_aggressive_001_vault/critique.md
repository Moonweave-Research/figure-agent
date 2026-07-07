---
schema: figure-agent.critique.v1.17
fixture: fig1_overview_v5e_aggressive_001_vault
generated_at: '2026-07-03T13:45:32Z'
generator: critique_brief.py
generator_version: sha256:51345bad8b6bdef113dcd48ad8b73a3a99b7cf99af028b5d3b3ea4c348690946
rubric_version: figure-agent.critique-rubric.v1.17
critique_input_hash: sha256:34e97ecb090e36294cc0a1f5658e18b1da0deb1e28daece0b64cbd9194fed9b9
verdict: revise
audit_enumeration:
  structural_completeness:
    components:
    - component: Panel A sulfur-rich poly(S-r-DIB) chain, DIB rings, and S8/inverse-vulcanization cue
      mount_support: N/A
      rationale: Chemistry identity is visible on clean white with amber sulfur grammar.
      connections: Bond strokes, S ring, and dashed annotation arrow form the polymer setup.
    - component: Panel B S60/S75/S85 composition series and sulfur-content axis
      mount_support: N/A
      rationale: Three chain exemplars and the bottom axis establish composition variation.
      connections: Chain rows connect visually to the sulfur-content arrow and labels.
    - component: Panel C film plus trap energy diagram
      mount_support: 'true'
      rationale: Real-space film, shallow/deep dots, energy diagram, mobility edge, and Delta-E_t caliper are all visible.
      connections: Dashed leaders bind real-space trap sites to energy levels.
    - component: Panel D SMU/MIM apparatus and I(t) power-law plot
      mount_support: 'true'
      rationale: The apparatus and plot are recognizable and connected to the kinetic modality.
      connections: SMU wires enter the MIM stack; plot curves carry low-n/high-n/Debye semantics.
    - component: Panel E corona source, Vs probe/meter, Vs(t), and g(Et)
      mount_support: 'true'
      rationale: Corona/probe hardware and derived energy distribution are legible.
      connections: Probe-to-meter cable, vertical derive arrow, and tau_d interval connect the sub-zones.
    - component: Panel F Vactive PSU, cantilever, qtr charges, electrode, air gap, and Coulomb arrow
      mount_support: 'true'
      rationale: Mechanical mechanism is visible; the v5e trapped-charge callout is stronger than the prior qtr-only label,
        though denser than v5d.
      connections: PSU wires to electrode; Coulomb arrow points away from the electrode; air-gap caliper and trapped-charge
        callout anchor the mechanism.
    missing_from_reference:
    - element: cover-scene background wash
      status: intentional_omission
      rationale: Clean white main-text figure register is the intended Nature-style direction.
    - element: full experimental hardware detail
      status: intentional_omission
      rationale: Panels D-F use iconic apparatus abstractions rather than full lab photographs.
  label_target_matching:
  - label: Sulfur-rich polymer
    nearest_object: Panel A polymer chain and DIB rings
    intended_target: polymer identity
    matches: true
    proposed_fix: ''
  - label: shallow / deep
    nearest_object: Panel C trap levels and distributions
    intended_target: trap species
    matches: true
    proposed_fix: ''
  - label: low n / high n / Debye
    nearest_object: Panel D power-law and reference curves
    intended_target: kinetic exponent interpretation
    matches: true
    proposed_fix: ''
  - label: derive
    nearest_object: Panel E vertical derive arrow
    intended_target: Vs(t) to g(Et) transformation
    matches: true
    proposed_fix: ''
  - label: trapped charge / qtr
    nearest_object: Panel F trapped-charge markers and two-leader callout on the cantilever
    intended_target: charge marker label
    matches: true
    proposed_fix: Compare v5e density against v5d before promotion; no semantic rename is needed.
  physical_plausibility:
  - check: cable_gravity
    finding: Schematic cables are routed cleanly between devices and targets.
    verdict: convention_acceptable
  - check: floating_components
    finding: No free-floating core apparatus; detector flags are mostly crop/glyph contacts.
    verdict: convention_acceptable
  - check: spatial_proximity
    finding: Energy levels, apparatus, electrodes, and charge markers are locally plausible.
    verdict: convention_acceptable
  - check: direction_orientation
    finding: Panel F Coulomb arrow points away from the electrode as specified by the tex assertion.
    verdict: convention_acceptable
  - check: material_distinction
    finding: Amber polymer, blue shallow traps, red deep/force cues, and gray supports remain distinguishable.
    verdict: convention_acceptable
  conceptual_completeness:
  - element: bimodal trap landscape
    reference: briefing
    severity: NIT
    proposed_action: accept_simplification
  - element: three independent evidence modalities
    reference: briefing
    severity: NIT
    proposed_action: accept_simplification
  - element: mechanical Coulomb expression
    reference: briefing
    severity: MINOR
    proposed_action: expand
quality_axes:
  message_storyline:
    verdict: pass
    confidence: medium
    rationale: message_storyline assessed from the current render, panel crops, and print-scale crops.
    evidence: current render; print_178mm; crop_audit_log; micro_defects for message_storyline
    blocking_items: []
    recommended_action: none
  panel_role_coherence:
    verdict: pass
    confidence: medium
    rationale: panel_role_coherence assessed from the current render, panel crops, and print-scale crops.
    evidence: current render; print_178mm; crop_audit_log; micro_defects for panel_role_coherence
    blocking_items: []
    recommended_action: none
    panel_roles:
    - panel_id: a
      role: context
      role_quality: clear
      rationale: material chemistry establishes the sulfur-rich polymer context.
    - panel_id: b
      role: setup
      role_quality: clear
      rationale: composition series sets the sulfur-content variable.
    - panel_id: c
      role: model
      role_quality: clear
      rationale: trap landscape is the visual hero and model panel.
    - panel_id: d
      role: result
      role_quality: clear
      rationale: kinetic evidence is shown as SMU/MIM plus power-law plot.
    - panel_id: e
      role: result
      role_quality: clear
      rationale: ISPD evidence is shown as corona/probe plus Vs/g(Et) relation.
    - panel_id: f
      role: result
      role_quality: clear
      rationale: mechanical evidence now has a stronger trapped-charge callout plus Coulomb/air-gap semantics.
  subregion_integration:
    verdict: pass
    confidence: medium
    rationale: subregion_integration assessed from the current render, panel crops, and print-scale crops.
    evidence: current render; print_178mm; crop_audit_log; micro_defects for subregion_integration
    blocking_items: []
    recommended_action: none
  component_fidelity:
    verdict: pass
    confidence: medium
    rationale: component_fidelity assessed from the current render, panel crops, and print-scale crops.
    evidence: current render; print_178mm; crop_audit_log; micro_defects for component_fidelity
    blocking_items: []
    recommended_action: none
  scientific_plausibility:
    verdict: pass
    confidence: medium
    rationale: scientific_plausibility assessed from the current render, panel crops, and print-scale crops.
    evidence: current render; print_178mm; crop_audit_log; micro_defects for scientific_plausibility
    blocking_items: []
    recommended_action: none
  composition_layout:
    verdict: pass
    confidence: medium
    rationale: composition_layout assessed from the current render, panel crops, and print-scale crops.
    evidence: current render; print_178mm; crop_audit_log; micro_defects for composition_layout
    blocking_items: []
    recommended_action: none
  label_annotation_semantics:
    verdict: pass
    confidence: medium
    rationale: Panel F qtr semantics are now readable through the trapped-charge callout; Panel D high n has stronger print-scale
      authority.
    evidence: panel_F_s11 crop; print_thumbnail crop; current render; Panel D crop
    blocking_items: []
    recommended_action: none
  journal_polish:
    verdict: needs_human
    confidence: medium
    rationale: v5e fixes the prior Panel F label-density typography weaknesses, but the stronger Panel F callout is visually
      denser and should be compared against v5d before promotion.
    evidence: panel_F_s11 crop; print_thumbnail crop; current render; aesthetic_intent print_typography_authority and mature_restraint
      anchors
    blocking_items:
    - top_tier_audit.aesthetic_coherence - Panel F label density needs human comparison against v5d
    - editorial_art_direction.aesthetic_risk - v5e Panel F density is comparison-gated
    - editorial_art_direction.tikz_vs_svg_polish_trigger - no SVG polish before v5d comparison
    - editorial_art_direction.human_art_direction_gate - promotion requires human comparison
    - C001 - compare the stronger v5e Panel F trapped-charge callout against v5d before export promotion
    recommended_action: human_review
  reference_fidelity:
    verdict: pass
    confidence: medium
    rationale: reference_fidelity assessed from the current render, panel crops, and print-scale crops.
    evidence: current render; print_178mm; crop_audit_log; micro_defects for reference_fidelity
    blocking_items: []
    recommended_action: none
  publication_readiness:
    verdict: needs_human
    confidence: medium
    rationale: Current artifact is render-fresh and detector-clean on collision/text-boundary/label-path checks, but this
      aggressive lane needs human art-direction comparison before export promotion.
    evidence: fresh compile; status critique gate; C001 comparison gate
    blocking_items:
    - top_tier_audit.aesthetic_coherence - Panel F label density needs human comparison against v5d
    - editorial_art_direction.aesthetic_risk - v5e Panel F density is comparison-gated
    - editorial_art_direction.tikz_vs_svg_polish_trigger - no SVG polish before v5d comparison
    - editorial_art_direction.human_art_direction_gate - promotion requires human comparison
    - C001 - compare the stronger v5e Panel F trapped-charge callout against v5d before export promotion
    recommended_action: human_review
top_tier_audit:
  first_glance_message:
    verdict: pass
    finding: Current render first_glance_message assessment cites visible panel/crop evidence and aesthetic intent anchors
      where applicable.
    concrete_fix: accept_simplification - current artifact evidence is sufficient.
    blocks_high_impact: false
  target_journal_fit:
    verdict: pass
    finding: v5e has stronger print-scale labels than v5d; aesthetic coherence now depends on comparing Panel F label density
      against the fallback lane.
    concrete_fix: accept_simplification - v5d C001 typography issues are addressed.
    blocks_high_impact: false
  novelty_claim_support:
    verdict: pass
    finding: Current render novelty_claim_support assessment cites visible panel/crop evidence and aesthetic intent anchors
      where applicable.
    concrete_fix: accept_simplification - current artifact evidence is sufficient.
    blocks_high_impact: false
  figure_caption_coupling:
    verdict: pass
    finding: Current render figure_caption_coupling assessment cites visible panel/crop evidence and aesthetic intent anchors
      where applicable.
    concrete_fix: accept_simplification - current artifact evidence is sufficient.
    blocks_high_impact: false
  visual_economy:
    verdict: pass
    finding: Current render visual_economy assessment cites visible panel/crop evidence and aesthetic intent anchors where
      applicable.
    concrete_fix: accept_simplification - current artifact evidence is sufficient.
    blocks_high_impact: false
  cross_panel_semantic_grammar:
    verdict: pass
    finding: Current render cross_panel_semantic_grammar assessment cites visible panel/crop evidence and aesthetic intent
      anchors where applicable.
    concrete_fix: accept_simplification - current artifact evidence is sufficient.
    blocks_high_impact: false
  reader_misinterpretation_risk:
    verdict: pass
    finding: Current render reader_misinterpretation_risk assessment cites visible panel/crop evidence and aesthetic intent
      anchors where applicable.
    concrete_fix: accept_simplification - current artifact evidence is sufficient.
    blocks_high_impact: false
  reduction_print_readability:
    verdict: pass
    finding: v5e has stronger print-scale labels than v5d; aesthetic coherence now depends on comparing Panel F label density
      against the fallback lane.
    concrete_fix: accept_simplification - v5d C001 typography issues are addressed.
    blocks_high_impact: false
  accessibility_color_robustness:
    verdict: pass
    finding: Current render accessibility_color_robustness assessment cites visible panel/crop evidence and aesthetic intent
      anchors where applicable.
    concrete_fix: accept_simplification - current artifact evidence is sufficient.
    blocks_high_impact: false
  aesthetic_coherence:
    verdict: needs_human
    finding: Current render, panel_F_s11, and print_thumbnail show mature_restraint and print_typography_authority improved
      relative to v5d; aesthetic coherence now depends on comparing Panel F label density against the fallback lane.
    concrete_fix: C001 - compare v5e Panel F density against v5d before promotion.
    blocks_high_impact: false
editorial_art_direction:
  hero_focus:
    verdict: pass
    evidence: Current render and print_178mm crop show hero_focus; aesthetic intent mature_restraint and print_typography_authority
      are considered.
    rationale: hero_focus is assessed against the Nature Materials editorial target and current artifact evidence.
    concrete_fix: accept_simplification - no art-direction blocker.
    blocks_high_impact: false
  narrative_choreography:
    verdict: pass
    evidence: Current render and print_178mm crop show narrative_choreography; aesthetic intent mature_restraint and print_typography_authority
      are considered.
    rationale: narrative_choreography is assessed against the Nature Materials editorial target and current artifact evidence.
    concrete_fix: accept_simplification - no art-direction blocker.
    blocks_high_impact: false
  illustration_readiness:
    verdict: pass
    evidence: Current render and print_178mm crop show illustration_readiness; aesthetic intent mature_restraint and print_typography_authority
      are considered.
    rationale: illustration_readiness is assessed against the Nature Materials editorial target and current artifact evidence.
    concrete_fix: C001 - continue TikZ label polish before export.
    blocks_high_impact: false
  abstraction_consistency:
    verdict: pass
    evidence: Current render and print_178mm crop show abstraction_consistency; aesthetic intent mature_restraint and print_typography_authority
      are considered.
    rationale: abstraction_consistency is assessed against the Nature Materials editorial target and current artifact evidence.
    concrete_fix: accept_simplification - no art-direction blocker.
    blocks_high_impact: false
  reference_class_fit:
    verdict: pass
    evidence: Current render and print_178mm crop show reference_class_fit; aesthetic intent mature_restraint and print_typography_authority
      are considered.
    rationale: reference_class_fit is assessed against the Nature Materials editorial target and current artifact evidence.
    concrete_fix: accept_simplification - no art-direction blocker.
    blocks_high_impact: false
  visual_identity:
    verdict: pass
    evidence: Current artifact evidence from full render, print_178mm, and print_thumbnail cites mature_restraint, print_typography_authority,
      and semantic_color_economy anchors.
    rationale: visual_identity is assessed against the Nature Materials editorial target and current artifact evidence. The
      decision is anchored in aesthetic_intent.yaml v2 item ids, not generic taste prose.
    concrete_fix: accept_simplification - no art-direction blocker.
    blocks_high_impact: false
  claim_payload_fit:
    verdict: pass
    evidence: Current render and print_178mm crop show claim_payload_fit; aesthetic intent mature_restraint and print_typography_authority
      are considered.
    rationale: claim_payload_fit is assessed against the Nature Materials editorial target and current artifact evidence.
    concrete_fix: accept_simplification - no art-direction blocker.
    blocks_high_impact: false
  aesthetic_risk:
    verdict: needs_human
    evidence: Current v5e render and panel_F_s11/print_thumbnail crops show a stronger but denser trapped-charge callout;
      mature_restraint, print_typography_authority, and row2_whitespace_breathing are the active aesthetic-intent anchors.
    rationale: The remaining decision is art-direction comparison against the v5d fallback, not a deterministic detector failure;
      the concern is whether the stronger Panel F label density still satisfies mature_restraint.
    concrete_fix: Compare v5e against v5d before export promotion.
    blocks_high_impact: false
  tikz_vs_svg_polish_trigger:
    verdict: needs_human
    evidence: Current v5e render and panel_F_s11/print_thumbnail crops show a stronger but denser trapped-charge callout;
      print_typography_authority improved, while mature_restraint and row2_whitespace_breathing require comparison against
      v5d.
    rationale: The remaining decision is art-direction comparison against the v5d fallback, not a deterministic detector failure;
      if v5e over-dominates Row 2, the next adjustment remains a bounded TikZ patch.
    concrete_fix: Compare v5e against v5d before export promotion.
    blocks_high_impact: true
    recommended_path: needs_human_art_direction
    remaining_tikz_lever: ''
    svg_polish_candidate_reason: ''
    semantic_backport_reason: ''
    human_art_direction_reason: v5e is a deliberately aggressive lane; compare Panel F label density and whole-figure finish
      against v5d before export or polish.
  human_art_direction_gate:
    verdict: needs_human
    evidence: Current v5e render and panel_F_s11/print_thumbnail crops show a stronger but denser trapped-charge callout.
    rationale: The remaining decision is art-direction comparison against the v5d fallback, not a deterministic detector failure.
    concrete_fix: Compare v5e against v5d before export promotion.
    blocks_high_impact: false
journal_grade_assessment:
  schema: figure-agent.journal-grade-assessment.v1
  scoring_mode: fresh_reaudit
  assessed_artifact_hash: sha256:34e97ecb090e36294cc0a1f5658e18b1da0deb1e28daece0b64cbd9194fed9b9
  benchmark_level: needs_human_art_direction
  confidence: medium
  blockers: []
  regression_detected: false
  regressions: []
  score_is_gateable: false
  next_quality_bottleneck: human_policy
  rationale: v5e is a stronger aggressive editorial candidate than v5d on Panel F charge semantics and Panel D high-n authority,
    but promotion depends on human comparison of label density and whole-figure finish.
  overall_score: 85
  sub_scores:
    storyline: 88
    composition: 85
    component_fidelity: 83
    scientific_plausibility: 90
    label_semantics: 84
    polish: 82
    reference_fidelity: 80
    export_scale_readability: 82
  score_rationale: Scores are advisory and describe only the current artifact; v5e improves the prior local typography issues
    but remains comparison-gated before promotion.
aesthetic_lever_audit:
- lever_id: maturity_restraint
  dimension: maturity
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - current artifact uses restrained hierarchy and semantic color coding
  - panel crops show recognizable apparatus and mechanism-specific labels
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - quality_axes.journal_polish
  - editorial_art_direction.tikz_vs_svg_polish_trigger
  - top_tier_audit.aesthetic_coherence
  allowed_next_adjustment: ''
  forbidden_adjustment_guard: remove scientific components; change mechanism meaning; hide required labels
  rationale: maturity_restraint follows from current artifact evidence and the declared aesthetic intent; weak routes remain
    bounded and do not change semantics.
- lever_id: panel_c_hero_hierarchy
  dimension: hero_hierarchy
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - current artifact uses restrained hierarchy and semantic color coding
  - panel crops show recognizable apparatus and mechanism-specific labels
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - quality_axes.journal_polish
  - editorial_art_direction.tikz_vs_svg_polish_trigger
  - top_tier_audit.aesthetic_coherence
  allowed_next_adjustment: ''
  forbidden_adjustment_guard: collapse Panel C into a decorative cover scene; change the declared A-F panel roles
  rationale: panel_c_hero_hierarchy follows from current artifact evidence and the declared aesthetic intent; weak routes
    remain bounded and do not change semantics.
- lever_id: row2_whitespace_breathing
  dimension: whitespace_breathing
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - current artifact uses restrained hierarchy and semantic color coding
  - panel crops show recognizable apparatus and mechanism-specific labels
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - quality_axes.journal_polish
  - editorial_art_direction.tikz_vs_svg_polish_trigger
  - top_tier_audit.aesthetic_coherence
  allowed_next_adjustment: ''
  forbidden_adjustment_guard: move evidence between columns; delete required Row 2 instrument labels
  rationale: row2_whitespace_breathing follows from current artifact evidence and the declared aesthetic intent; weak routes
    remain bounded and do not change semantics.
- lever_id: print_typography_authority
  dimension: typography_authority
  verdict: needs_human
  confidence: medium
  observed_positive_signals:
  - Panel F trapped-charge callout is more readable than the prior qtr-only label
  - Panel D high n tag has stronger right-lane authority
  observed_anti_patterns:
  - Panel F label density is stronger and needs comparison against v5d fallback before promotion
  route: tikz_patch
  linked_evidence:
  - quality_axes.journal_polish
  - editorial_art_direction.tikz_vs_svg_polish_trigger
  - finding C001
  allowed_next_adjustment: compare Panel F label density against v5d and tune only if it over-dominates
  forbidden_adjustment_guard: rename symbols; change measured quantities; hide a mechanism-anchoring label
  rationale: print_typography_authority improved, but v5e is an aggressive lane whose denser Panel F callout should be human-compared
    before promotion.
- lever_id: semantic_color_economy
  dimension: color_harmony
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - current artifact uses restrained hierarchy and semantic color coding
  - panel crops show recognizable apparatus and mechanism-specific labels
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - quality_axes.journal_polish
  - editorial_art_direction.tikz_vs_svg_polish_trigger
  - top_tier_audit.aesthetic_coherence
  allowed_next_adjustment: ''
  forbidden_adjustment_guard: swap shallow and deep trap colors; change force-direction color semantics
  rationale: semantic_color_economy follows from current artifact evidence and the declared aesthetic intent; weak routes
    remain bounded and do not change semantics.
- lever_id: line_weight_rhythm
  dimension: line_weight_rhythm
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - current artifact uses restrained hierarchy and semantic color coding
  - panel crops show recognizable apparatus and mechanism-specific labels
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - quality_axes.journal_polish
  - editorial_art_direction.tikz_vs_svg_polish_trigger
  - top_tier_audit.aesthetic_coherence
  allowed_next_adjustment: ''
  forbidden_adjustment_guard: change graph/data relationships; remove required wiring or axes
  rationale: line_weight_rhythm follows from current artifact evidence and the declared aesthetic intent; weak routes remain
    bounded and do not change semantics.
- lever_id: component_fidelity_finish
  dimension: component_fidelity
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - current artifact uses restrained hierarchy and semantic color coding
  - panel crops show recognizable apparatus and mechanism-specific labels
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - quality_axes.journal_polish
  - editorial_art_direction.tikz_vs_svg_polish_trigger
  - top_tier_audit.aesthetic_coherence
  allowed_next_adjustment: ''
  forbidden_adjustment_guard: invent unsupported apparatus; change the experiment class; add decorative detail implying false
    measurement
  rationale: component_fidelity_finish follows from current artifact evidence and the declared aesthetic intent; weak routes
    remain bounded and do not change semantics.
- lever_id: hand_craft_escape_route
  dimension: hand_craft
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - current artifact uses restrained hierarchy and semantic color coding
  - panel crops show recognizable apparatus and mechanism-specific labels
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - quality_axes.journal_polish
  - editorial_art_direction.tikz_vs_svg_polish_trigger
  - top_tier_audit.aesthetic_coherence
  allowed_next_adjustment: ''
  forbidden_adjustment_guard: use SVG polish to alter mechanism; change accepted or golden artifacts without explicit gate
  rationale: Remaining issues are ordinary TikZ label-authority patches, not SVG-only hand-craft polish, so this lever does
    not open an SVG route.
- lever_id: cross_panel_grammar
  dimension: cross_panel_grammar
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - current artifact uses restrained hierarchy and semantic color coding
  - panel crops show recognizable apparatus and mechanism-specific labels
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - quality_axes.journal_polish
  - editorial_art_direction.tikz_vs_svg_polish_trigger
  - top_tier_audit.aesthetic_coherence
  allowed_next_adjustment: ''
  forbidden_adjustment_guard: make all panels visually identical; remove role-specific visual distinctions
  rationale: cross_panel_grammar follows from current artifact evidence and the declared aesthetic intent; weak routes remain
    bounded and do not change semantics.
aesthetic_antipattern_audit:
- id: childish_shape_language
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render and crops show no childish_shape_language anti-pattern at figure scale.
  rationale: No actionable anti-pattern observed in current artifact evidence.
  linked_evidence:
  - top_tier_audit.aesthetic_coherence
- id: poster_gradient_decoration
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render and crops show no poster_gradient_decoration anti-pattern at figure scale.
  rationale: No actionable anti-pattern observed in current artifact evidence.
  linked_evidence:
  - top_tier_audit.aesthetic_coherence
- id: generic_template_look
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render and crops show no generic_template_look anti-pattern at figure scale.
  rationale: No actionable anti-pattern observed in current artifact evidence.
  linked_evidence:
  - top_tier_audit.aesthetic_coherence
- id: dead_flat_vector_finish
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render and crops show no dead_flat_vector_finish anti-pattern at figure scale.
  rationale: No actionable anti-pattern observed in current artifact evidence.
  linked_evidence:
  - top_tier_audit.aesthetic_coherence
- id: uniform_line_weight_monotony
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render and crops show no uniform_line_weight_monotony anti-pattern at figure scale.
  rationale: No actionable anti-pattern observed in current artifact evidence.
  linked_evidence:
  - top_tier_audit.aesthetic_coherence
- id: weak_hero_anchor
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render and crops show no weak_hero_anchor anti-pattern at figure scale.
  rationale: No actionable anti-pattern observed in current artifact evidence.
  linked_evidence:
  - top_tier_audit.aesthetic_coherence
- id: cramped_or_dead_whitespace
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render and crops show no cramped_or_dead_whitespace anti-pattern at figure scale.
  rationale: No actionable anti-pattern observed in current artifact evidence.
  linked_evidence:
  - top_tier_audit.aesthetic_coherence
- id: low_authority_typography
  verdict: absent
  severity: MINOR
  route: none
  evidence: Current render and print_thumbnail show stronger Panel F trapped-charge and Panel D high-n typography than v5d.
  rationale: The prior low-authority typography issue was addressed; remaining concern is comparative label density, not unreadability.
  linked_evidence:
  - quality_axes.journal_polish
  - finding C001
- id: annotation_noise_competes_with_science
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render and crops show no annotation_noise_competes_with_science anti-pattern at figure scale.
  rationale: No actionable anti-pattern observed in current artifact evidence.
  linked_evidence:
  - top_tier_audit.aesthetic_coherence
- id: panel_style_mismatch
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render and crops show no panel_style_mismatch anti-pattern at figure scale.
  rationale: No actionable anti-pattern observed in current artifact evidence.
  linked_evidence:
  - top_tier_audit.aesthetic_coherence
- id: reference_overcopying
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render and crops show no reference_overcopying anti-pattern at figure scale.
  rationale: No actionable anti-pattern observed in current artifact evidence.
  linked_evidence:
  - top_tier_audit.aesthetic_coherence
- id: reference_underlearning
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render and crops show no reference_underlearning anti-pattern at figure scale.
  rationale: No actionable anti-pattern observed in current artifact evidence.
  linked_evidence:
  - top_tier_audit.aesthetic_coherence
- id: decorative_detail_without_explanatory_value
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render and crops show no decorative_detail_without_explanatory_value anti-pattern at figure scale.
  rationale: No actionable anti-pattern observed in current artifact evidence.
  linked_evidence:
  - top_tier_audit.aesthetic_coherence
weakest_panel_coherence:
  panel_id: F
  subregion_id: charge-label zone
  weakness_type: typography
  route: human_art_direction
  evidence: Panel F trapped-charge callout is clear in panel_F_s11 and print_thumbnail but denser than the v5d fallback; linked
    to finding C001.
  rationale: Panel F is now readable, but it is the most changed subregion and should be compared against v5d before promotion.
  linked_evidence:
  - quality_axes.journal_polish
  - editorial_art_direction.human_art_direction_gate
  - finding C001
  - micro_defect M_PANEL_F_DENSITY
reference_learning_accountability:
  learned_principle: Use clean multipanel story structure and restrained editorial hierarchy from the reference class.
  rejected_copy_target: Did not copy reference apparatus topology or decorative background washes.
  overcopying: absent
  underlearning: absent
  route: none
  evidence: Current render keeps a white multipanel Nature-style register while preserving sulfur-polymer-specific trap semantics.
  rationale: Reference learning affects hierarchy and restraint only; it does not override the declared mechanism.
  linked_evidence:
  - top_tier_audit.target_journal_fit
  - editorial_art_direction.reference_class_fit
micro_defects:
- id: M_PANEL_F_DENSITY
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/panel_F_s11.png
  kind: print_scale_unreadable
  severity: MINOR
  observation: Panel F trapped-charge callout is now legible and semantically attached, but the bolder two-line label makes
    this aggressive lane visually denser than v5d and should be compared before promotion.
  linked_finding_id: C001
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: open
  accept_simplification_reason: ''
  accept_simplification_rationale: ''
- id: M_VC001
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC001_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC001 flags detector proximity for text/glyph 'S', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC001
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC001 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC003
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC003_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC003 flags detector proximity for text/glyph 'S', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC003
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC003 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC004
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC004_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC004 flags detector proximity for text/glyph 'S', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC004
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC004 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC005
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC005_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC005 flags detector proximity for text/glyph 'S', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC005
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC005 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC006
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC006_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC006 flags detector proximity for text/glyph 'S', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC006
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC006 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC007
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC007_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC007 flags detector proximity for text/glyph 'S', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC007
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC007 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC008
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC008_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC008 flags detector proximity for text/glyph 'S', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC008
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC008 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC009
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC009_C.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC009 flags detector proximity for text/glyph 'C', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC009
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC009 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC010
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC010_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC010 flags detector proximity for text/glyph 'S', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC010
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC010 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC011
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC011_Energy.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC011 flags detector proximity for text/glyph 'Energy', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC011
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC011 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC012
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC012_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC012 flags detector proximity for text/glyph 'S', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC012
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC012 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC013
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC013_poly_S-r-DIB.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC013 flags detector proximity for text/glyph 'poly(S-r-DIB)', but crop review shows an intentional schematic
    or chemical/instrument glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC013
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC013 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC014
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC014_Sulfur.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC014 flags detector proximity for text/glyph 'Sulfur', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC014
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC014 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC015
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC015_V.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC015 flags detector proximity for text/glyph 'V', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC015
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC015 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC016
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC016_ISPD.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC016 flags detector proximity for text/glyph 'ISPD', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC016
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC016 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC017
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC017_HV.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC017 flags detector proximity for text/glyph 'HV+', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC017
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC017 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC018
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC018_SMU.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC018 flags detector proximity for text/glyph 'SMU', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC018
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC018 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC019
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC019_V_A.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC019 flags detector proximity for text/glyph 'V/A', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC019
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC019 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC020
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC020_Vs.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC020 flags detector proximity for text/glyph 'Vs', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC020
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC020 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC021
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC021_film.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC021 flags detector proximity for text/glyph 'film', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC021
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC021 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC022
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC022_crop.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC022 flags detector proximity for text/glyph '+', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC022
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC022 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC023
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC023_crop.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC023 flags detector proximity for text/glyph '+', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC023
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC023 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC024
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC024_crop.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC024 flags detector proximity for text/glyph '+', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC024
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC024 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC025
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC025_crop.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC025 flags detector proximity for text/glyph '+', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC025
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC025 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC026
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC026_V.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC026 flags detector proximity for text/glyph 'V', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC026
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC026 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC027
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC027_V.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC027 flags detector proximity for text/glyph 'V', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC027
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC027 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC028
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC028_t.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC028 flags detector proximity for text/glyph '(t)', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC028
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC028 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC029
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC029_I_t.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC029 flags detector proximity for text/glyph 'I(t)', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC029
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC029 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC030
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC030_q.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC030 flags detector proximity for text/glyph 'q', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC030
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC030 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC031
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC031_crop.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC031 flags detector proximity for text/glyph ')', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC031
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC031 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC032
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC032_low.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC032 flags detector proximity for text/glyph 'low', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC032
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC032 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC033
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC033_d.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC033 flags detector proximity for text/glyph 'd', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC033
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC033 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC034
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC034_Shallow.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC034 flags detector proximity for text/glyph 'Shallow', but crop review shows an intentional schematic or
    chemical/instrument glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC034
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC034 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC035
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC035_log.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC035 flags detector proximity for text/glyph 'log', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC035
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC035 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC036
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC036_I.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC036 flags detector proximity for text/glyph 'I', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC036
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC036 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_VC037
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC037_f.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC037 flags detector proximity for text/glyph 'f', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC037
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC037 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
- id: M_UG001
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG001 flags undeclared_horizontal_rule with evidence 'source line 368 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG001
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG001 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG002
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG002 flags label_endpoint_near_miss with evidence 'source line 416 is within 1.70 pt of text 'copolymer''
    near 'copolymer', but current render review shows detector-accounting metadata or an intentional schematic support mark
    rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG002
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG002 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG003
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG003 flags undeclared_horizontal_rule with evidence 'source line 416 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG003
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG003 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG004
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG004 flags label_endpoint_near_miss with evidence 'source line 433 is within 0.54 pt of text 'HV+'' near 'HV+',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG004
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG004 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG005
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG005 flags undeclared_horizontal_rule with evidence 'source line 433 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG005
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG005 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG006
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG006 flags undeclared_rect_boundary with evidence 'source line 484 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG006
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG006 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG007
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG007 flags undeclared_rect_boundary with evidence 'source line 486 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG007
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG007 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG008
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG008 flags undeclared_rect_boundary with evidence 'source line 491 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG008
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG008 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG009
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG009 flags label_endpoint_near_miss with evidence 'source line 498 is within 3.83 pt of text '+'' near '+',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG009
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG009 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG010
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG010 flags label_endpoint_near_miss with evidence 'source line 498 is within 3.83 pt of text '+'' near '+',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG010
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG010 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG011
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG011 flags label_endpoint_near_miss with evidence 'source line 498 is within 3.83 pt of text '+'' near '+',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG011
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG011 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG012
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG012 flags label_endpoint_near_miss with evidence 'source line 498 is within 3.83 pt of text '+'' near '+',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG012
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG012 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG013
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG013 flags undeclared_horizontal_rule with evidence 'source line 498 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG013
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG013 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG014
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG014 flags label_endpoint_near_miss with evidence 'source line 514 is within 1.75 pt of text 'Vs'' near 'Vs',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG014
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG014 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG015
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG015 flags undeclared_column_rule with evidence 'source line 514 line lacks text_boundary_check' near '',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG015
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG015 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG016
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG016 flags label_endpoint_near_miss with evidence 'source line 523 is within 1.97 pt of text 'ISPD'' near
    'ISPD', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG016
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG016 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG017
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG017 flags undeclared_horizontal_rule with evidence 'source line 523 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG017
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG017 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG018
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG018 flags undeclared_column_rule with evidence 'source line 586 line lacks text_boundary_check' near '',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG018
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG018 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG019
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG019 flags undeclared_horizontal_rule with evidence 'source line 634 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG019
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG019 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG020
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG020 flags undeclared_horizontal_rule with evidence 'source line 641 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG020
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG020 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG021
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG021 flags undeclared_horizontal_rule with evidence 'source line 644 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG021
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG021 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG022
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG022 flags undeclared_horizontal_rule with evidence 'source line 666 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG022
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG022 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG023
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG023 flags undeclared_column_rule with evidence 'source line 694 line lacks text_boundary_check' near '',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG023
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG023 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG024
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG024 flags undeclared_column_rule with evidence 'source line 701 line lacks text_boundary_check' near '',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG024
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG024 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG025
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG025 flags undeclared_column_rule with evidence 'source line 716 line lacks text_boundary_check' near '',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG025
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG025 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG026
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG026 flags undeclared_column_rule with evidence 'source line 837 line lacks text_boundary_check' near '',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG026
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG026 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG027
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG027 flags label_endpoint_near_miss with evidence 'source line 982 is within 2.17 pt of text 'S'' near 'S',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG027
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG027 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG028
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG028 flags undeclared_column_rule with evidence 'source line 982 line lacks text_boundary_check' near '',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG028
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG028 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG029
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG029 flags undeclared_column_rule with evidence 'source line 983 line lacks text_boundary_check' near '',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG029
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG029 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG030
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG030 flags undeclared_rect_boundary with evidence 'source line 1010 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG030
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG030 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG031
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG031 flags undeclared_rect_boundary with evidence 'source line 1012 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG031
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG031 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG032
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG032 flags undeclared_rect_boundary with evidence 'source line 1021 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG032
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG032 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG033
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG033 flags undeclared_rect_boundary with evidence 'source line 1022 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG033
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG033 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG034
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG034 flags undeclared_rect_boundary with evidence 'source line 1024 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG034
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG034 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG035
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG035 flags undeclared_rect_boundary with evidence 'source line 1025 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG035
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG035 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG036
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG036 flags undeclared_rect_boundary with evidence 'source line 1035 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG036
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG036 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG037
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG037 flags undeclared_rect_boundary with evidence 'source line 1037 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG037
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG037 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG038
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG038 flags undeclared_rect_boundary with evidence 'source line 1045 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG038
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG038 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG039
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG039 flags undeclared_rect_boundary with evidence 'source line 1047 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG039
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG039 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG040
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG040 flags undeclared_rect_boundary with evidence 'source line 1050 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG040
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG040 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG041
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG041 flags undeclared_rect_boundary with evidence 'source line 1052 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG041
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG041 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG042
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG042 flags undeclared_column_rule with evidence 'source line 1090 line lacks text_boundary_check' near '',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG042
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG042 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG043
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG043 flags label_endpoint_near_miss with evidence 'source line 1092 is within 3.76 pt of text 'S'' near 'S',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG043
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG043 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG044
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG044 flags undeclared_horizontal_rule with evidence 'source line 1092 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG044
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG044 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG045
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG045 flags undeclared_horizontal_rule with evidence 'source line 1172 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG045
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG045 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG046
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG046 flags undeclared_rect_boundary with evidence 'source line 1242 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG046
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG046 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG047
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG047 flags undeclared_rect_boundary with evidence 'source line 1248 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG047
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG047 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG048
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG048 flags undeclared_rect_boundary with evidence 'source line 1250 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG048
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG048 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG049
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG049 flags undeclared_rect_boundary with evidence 'source line 1255 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG049
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG049 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG050
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG050 flags undeclared_rect_boundary with evidence 'source line 1265 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG050
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG050 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG051
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG051 flags undeclared_rect_boundary with evidence 'source line 1271 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG051
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG051 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG052
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG052 flags undeclared_rect_boundary with evidence 'source line 1278 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG052
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG052 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG053
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG053 flags undeclared_rect_boundary with evidence 'source line 1336 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG053
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG053 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG054
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG054 flags undeclared_rect_boundary with evidence 'source line 1338 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG054
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG054 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG055
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG055 flags undeclared_rect_boundary with evidence 'source line 1348 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG055
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG055 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG056
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG056 flags undeclared_rect_boundary with evidence 'source line 1350 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG056
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG056 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG057
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG057 flags undeclared_rect_boundary with evidence 'source line 1353 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG057
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG057 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG058
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG058 flags undeclared_rect_boundary with evidence 'source line 1492 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG058
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG058 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG059
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG059 flags undeclared_rect_boundary with evidence 'source line 1497 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG059
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG059 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG060
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG060 flags undeclared_rect_boundary with evidence 'source line 1514 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG060
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG060 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG061
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG061 flags undeclared_rect_boundary with evidence 'source line 1515 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG061
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG061 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG062
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG062 flags undeclared_rect_boundary with evidence 'source line 1516 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG062
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG062 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG063
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG063 flags undeclared_rect_boundary with evidence 'source line 1570 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG063
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG063 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG064
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG064 flags undeclared_rect_boundary with evidence 'source line 1572 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG064
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG064 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG065
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG065 flags undeclared_rect_boundary with evidence 'source line 1577 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG065
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG065 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG066
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG066 flags undeclared_rect_boundary with evidence 'source line 1582 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG066
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG066 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG067
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG067 flags undeclared_rect_boundary with evidence 'source line 1584 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG067
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG067 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG068
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG068 flags undeclared_rect_boundary with evidence 'source line 1586 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG068
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG068 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG069
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG069 flags undeclared_horizontal_rule with evidence 'source line 1648 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG069
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG069 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG070
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG070 flags undeclared_column_rule with evidence 'source line 1658 line lacks text_boundary_check' near '',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG070
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG070 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG071
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG071 flags undeclared_horizontal_rule with evidence 'source line 1660 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG071
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG071 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG072
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG072 flags undeclared_column_rule with evidence 'source line 1734 line lacks text_boundary_check' near '',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG072
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG072 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG073
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG073 flags undeclared_column_rule with evidence 'source line 1743 line lacks text_boundary_check' near '',
    but current render review shows detector-accounting metadata or an intentional schematic support mark rather than a visible
    defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG073
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG073 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG074
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG074 flags undeclared_horizontal_rule with evidence 'source line 1745 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG074
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG074 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG075
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG075 flags undeclared_horizontal_rule with evidence 'source line 1819 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG075
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG075 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG076
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG076 flags undeclared_rect_boundary with evidence 'source line 1847 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG076
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG076 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG077
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG077 flags undeclared_rect_boundary with evidence 'source line 1849 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG077
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG077 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG078
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG078 flags undeclared_rect_boundary with evidence 'source line 1852 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG078
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG078 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG079
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG079 flags undeclared_rect_boundary with evidence 'source line 1854 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG079
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG079 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG080
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG080 flags undeclared_rect_boundary with evidence 'source line 1856 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG080
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG080 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG081
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG081 flags label_endpoint_near_miss with evidence 'source line 1885 is within 0.93 pt of text 'Energy'' near
    'Energy', but current render review shows detector-accounting metadata or an intentional schematic support mark rather
    than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG081
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG081 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG082
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG082 flags undeclared_horizontal_rule with evidence 'source line 1885 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG082
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG082 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG083
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG083 flags undeclared_rect_boundary with evidence 'source line 1899 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG083
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG083 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG084
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG084 flags undeclared_rect_boundary with evidence 'source line 1901 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG084
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG084 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG085
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG085 flags undeclared_horizontal_rule with evidence 'source line 1902 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG085
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG085 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG086
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG086 flags undeclared_horizontal_rule with evidence 'source line 1959 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG086
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG086 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG087
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG087 flags undeclared_rect_boundary with evidence 'source line 1976 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG087
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG087 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG088
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG088 flags undeclared_rect_boundary with evidence 'source line 1978 rectangle lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG088
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG088 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG089
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG089 flags label_endpoint_near_miss with evidence 'source line 2012 is within 0.36 pt of text 'localized''
    near 'localized', but current render review shows detector-accounting metadata or an intentional schematic support mark
    rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG089
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG089 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_UG090
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG090 flags undeclared_horizontal_rule with evidence 'source line 2012 line lacks text_boundary_check' near
    '', but current render review shows detector-accounting metadata or an intentional schematic support mark rather than
    a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG090
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'UG090 is convention acceptable: the flagged geometry is part of the intended schematic
    convention or detector coverage bookkeeping, remains separate from labels, and does not require source mutation before
    comparison review.'
- id: M_VC002
  crop: examples/fig1_overview_v5e_aggressive_001_vault/build/audit_crops/visual_clash/VC002_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC002 flags detector proximity for text/glyph 'S', but crop review shows an intentional schematic or chemical/instrument
    glyph relationship rather than a source defect.
  linked_finding_id: ''
  visual_clash_ref: VC002
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC002 is not a defect: it is an intentional schematic/glyph adjacency in the current render,
    remains visually distinct in its crop, and does not obscure the panel story.'
crop_audit_log:
- crop_id: VC001_S
  path: build/audit_crops/visual_clash/VC001_S.png
  source: visual_clash:VC001
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC001
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC003_S
  path: build/audit_crops/visual_clash/VC003_S.png
  source: visual_clash:VC003
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC003
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC004_S
  path: build/audit_crops/visual_clash/VC004_S.png
  source: visual_clash:VC004
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC004
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC005_S
  path: build/audit_crops/visual_clash/VC005_S.png
  source: visual_clash:VC005
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC005
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC006_S
  path: build/audit_crops/visual_clash/VC006_S.png
  source: visual_clash:VC006
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC006
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC007_S
  path: build/audit_crops/visual_clash/VC007_S.png
  source: visual_clash:VC007
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC007
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC008_S
  path: build/audit_crops/visual_clash/VC008_S.png
  source: visual_clash:VC008
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC008
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC009_C
  path: build/audit_crops/visual_clash/VC009_C.png
  source: visual_clash:VC009
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC009
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC010_S
  path: build/audit_crops/visual_clash/VC010_S.png
  source: visual_clash:VC010
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC010
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC011_Energy
  path: build/audit_crops/visual_clash/VC011_Energy.png
  source: visual_clash:VC011
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC011
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC012_S
  path: build/audit_crops/visual_clash/VC012_S.png
  source: visual_clash:VC012
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC012
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC013_poly_S-r-DIB
  path: build/audit_crops/visual_clash/VC013_poly_S-r-DIB.png
  source: visual_clash:VC013
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC013
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC014_Sulfur
  path: build/audit_crops/visual_clash/VC014_Sulfur.png
  source: visual_clash:VC014
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC014
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC015_V
  path: build/audit_crops/visual_clash/VC015_V.png
  source: visual_clash:VC015
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC015
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC016_ISPD
  path: build/audit_crops/visual_clash/VC016_ISPD.png
  source: visual_clash:VC016
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC016
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC017_HV
  path: build/audit_crops/visual_clash/VC017_HV.png
  source: visual_clash:VC017
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC017
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC018_SMU
  path: build/audit_crops/visual_clash/VC018_SMU.png
  source: visual_clash:VC018
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC018
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC019_V_A
  path: build/audit_crops/visual_clash/VC019_V_A.png
  source: visual_clash:VC019
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC019
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC020_Vs
  path: build/audit_crops/visual_clash/VC020_Vs.png
  source: visual_clash:VC020
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC020
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC021_film
  path: build/audit_crops/visual_clash/VC021_film.png
  source: visual_clash:VC021
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC021
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC022_crop
  path: build/audit_crops/visual_clash/VC022_crop.png
  source: visual_clash:VC022
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC022
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC023_crop
  path: build/audit_crops/visual_clash/VC023_crop.png
  source: visual_clash:VC023
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC023
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC024_crop
  path: build/audit_crops/visual_clash/VC024_crop.png
  source: visual_clash:VC024
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC024
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC025_crop
  path: build/audit_crops/visual_clash/VC025_crop.png
  source: visual_clash:VC025
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC025
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC026_V
  path: build/audit_crops/visual_clash/VC026_V.png
  source: visual_clash:VC026
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC026
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC027_V
  path: build/audit_crops/visual_clash/VC027_V.png
  source: visual_clash:VC027
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC027
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC028_t
  path: build/audit_crops/visual_clash/VC028_t.png
  source: visual_clash:VC028
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC028
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC029_I_t
  path: build/audit_crops/visual_clash/VC029_I_t.png
  source: visual_clash:VC029
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC029
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC030_q
  path: build/audit_crops/visual_clash/VC030_q.png
  source: visual_clash:VC030
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC030
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC031_crop
  path: build/audit_crops/visual_clash/VC031_crop.png
  source: visual_clash:VC031
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC031
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC032_low
  path: build/audit_crops/visual_clash/VC032_low.png
  source: visual_clash:VC032
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC032
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC033_d
  path: build/audit_crops/visual_clash/VC033_d.png
  source: visual_clash:VC033
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC033
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC034_Shallow
  path: build/audit_crops/visual_clash/VC034_Shallow.png
  source: visual_clash:VC034
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC034
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC035_log
  path: build/audit_crops/visual_clash/VC035_log.png
  source: visual_clash:VC035
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC035
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC036_I
  path: build/audit_crops/visual_clash/VC036_I.png
  source: visual_clash:VC036
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC036
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC037_f
  path: build/audit_crops/visual_clash/VC037_f.png
  source: visual_clash:VC037
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC037
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: full_q1
  path: build/audit_crops/full_q1.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: full_q2
  path: build/audit_crops/full_q2.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: full_q3
  path: build/audit_crops/full_q3.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: full_q4
  path: build/audit_crops/full_q4.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_q1
  path: build/audit_crops/panel_D_q1.png
  source: panel:D
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_q2
  path: build/audit_crops/panel_D_q2.png
  source: panel:D
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_q3
  path: build/audit_crops/panel_D_q3.png
  source: panel:D
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_q4
  path: build/audit_crops/panel_D_q4.png
  source: panel:D
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_s01
  path: build/audit_crops/panel_D_s01.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_s02
  path: build/audit_crops/panel_D_s02.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_s03
  path: build/audit_crops/panel_D_s03.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_s04
  path: build/audit_crops/panel_D_s04.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_s05
  path: build/audit_crops/panel_D_s05.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_s06
  path: build/audit_crops/panel_D_s06.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_s07
  path: build/audit_crops/panel_D_s07.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_s08
  path: build/audit_crops/panel_D_s08.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_s09
  path: build/audit_crops/panel_D_s09.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_s10
  path: build/audit_crops/panel_D_s10.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_s11
  path: build/audit_crops/panel_D_s11.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_s12
  path: build/audit_crops/panel_D_s12.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_s13
  path: build/audit_crops/panel_D_s13.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_s14
  path: build/audit_crops/panel_D_s14.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_s15
  path: build/audit_crops/panel_D_s15.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_D_s16
  path: build/audit_crops/panel_D_s16.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_q1
  path: build/audit_crops/panel_E_q1.png
  source: panel:E
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_q2
  path: build/audit_crops/panel_E_q2.png
  source: panel:E
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_q3
  path: build/audit_crops/panel_E_q3.png
  source: panel:E
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_q4
  path: build/audit_crops/panel_E_q4.png
  source: panel:E
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_s01
  path: build/audit_crops/panel_E_s01.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_s02
  path: build/audit_crops/panel_E_s02.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_s03
  path: build/audit_crops/panel_E_s03.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_s04
  path: build/audit_crops/panel_E_s04.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_s05
  path: build/audit_crops/panel_E_s05.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_s06
  path: build/audit_crops/panel_E_s06.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_s07
  path: build/audit_crops/panel_E_s07.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_s08
  path: build/audit_crops/panel_E_s08.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_s09
  path: build/audit_crops/panel_E_s09.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_s10
  path: build/audit_crops/panel_E_s10.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_s11
  path: build/audit_crops/panel_E_s11.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_s12
  path: build/audit_crops/panel_E_s12.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_s13
  path: build/audit_crops/panel_E_s13.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_s14
  path: build/audit_crops/panel_E_s14.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_s15
  path: build/audit_crops/panel_E_s15.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_E_s16
  path: build/audit_crops/panel_E_s16.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_q1
  path: build/audit_crops/panel_F_q1.png
  source: panel:F
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_q2
  path: build/audit_crops/panel_F_q2.png
  source: panel:F
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_q3
  path: build/audit_crops/panel_F_q3.png
  source: panel:F
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_q4
  path: build/audit_crops/panel_F_q4.png
  source: panel:F
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_s01
  path: build/audit_crops/panel_F_s01.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_s02
  path: build/audit_crops/panel_F_s02.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_s03
  path: build/audit_crops/panel_F_s03.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_s04
  path: build/audit_crops/panel_F_s04.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_s05
  path: build/audit_crops/panel_F_s05.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_s06
  path: build/audit_crops/panel_F_s06.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_s07
  path: build/audit_crops/panel_F_s07.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_s08
  path: build/audit_crops/panel_F_s08.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_s09
  path: build/audit_crops/panel_F_s09.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_s10
  path: build/audit_crops/panel_F_s10.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_s11
  path: build/audit_crops/panel_F_s11.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - C001
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_s12
  path: build/audit_crops/panel_F_s12.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_s13
  path: build/audit_crops/panel_F_s13.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_s14
  path: build/audit_crops/panel_F_s14.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_s15
  path: build/audit_crops/panel_F_s15.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: panel_F_s16
  path: build/audit_crops/panel_F_s16.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: print_178mm
  path: build/audit_crops/print_178mm.png
  source: print_scale
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - print_scale
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: print_thumbnail
  path: build/audit_crops/print_thumbnail.png
  source: print_scale
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - print_scale
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
- crop_id: VC002_S
  path: build/audit_crops/visual_clash/VC002_S.png
  source: visual_clash:VC002
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly; any related detector candidate is accounted as an accepted
    schematic simplification unless separately linked.
  observed_objects:
  - panel
  - visual_clash_crop
  local_relationship: Visible marks remain in their intended panel/subregion with readable local relationships.
  candidate_refs:
  - VC002
  unintended_visible_anomaly: none
  anomaly_rationale: No unintended visible artifact is present in this crop after the v5e source pass.
  anomaly_link: ''
panels: []
findings:
- id: C001
  severity: MINOR
  category: hierarchy
  tex_lines:
  - 1943
  - 1952
  grounded_in_rule: aesthetic_intent.print_typography_authority; panel_F_s11 crop; print_thumbnail crop
  observation: v5e fixes the prior weak qtr label by using a clearer trapped-charge callout, and Panel D high n is stronger;
    the remaining issue is that Panel F is now visually denser than v5d and needs human comparison before export promotion.
  suggested_fix: Compare v5e against v5d at full render and print_thumbnail scale; keep v5e if the stronger charge story outweighs
    the added label density, otherwise tune the callout size or fall back to v5d.
  status: open
---

# Vision Critique — fig1_overview_v5e_aggressive_001_vault

The current v5e render is an aggressive editorial candidate, not an accepted replacement for v5d. The source pass addresses the two v5d local weaknesses: Panel F now reads as a trapped-charge mechanism rather than a tiny qtr mark, and Panel D high n has stronger print-scale authority. The remaining decision is art-directional: Panel F is clearer but denser, so promotion should compare v5e against the v5d fallback at full-render and print-thumbnail scale before export or acceptance.
