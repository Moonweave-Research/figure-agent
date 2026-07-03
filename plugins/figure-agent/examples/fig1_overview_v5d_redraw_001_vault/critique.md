---
schema: figure-agent.critique.v1.17
fixture: fig1_overview_v5d_redraw_001_vault
generated_at: '2026-07-03T13:15:34Z'
generator: critique_brief.py
generator_version: sha256:51345bad8b6bdef113dcd48ad8b73a3a99b7cf99af028b5d3b3ea4c348690946
rubric_version: figure-agent.critique-rubric.v1.17
critique_input_hash: sha256:7887edcc6606fa885befabc9532a0407f87d377a75556640cecf949840ff6700
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
      rationale: Mechanical mechanism is visible, though qtr notation is weak at thumbnail scale.
      connections: PSU wires to electrode; Coulomb arrow points away from the electrode; air-gap caliper anchors spacing.
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
    proposed_fix: Improve high n print-scale separation from the red line end.
  - label: derive
    nearest_object: Panel E vertical derive arrow
    intended_target: Vs(t) to g(Et) transformation
    matches: true
    proposed_fix: ''
  - label: qtr
    nearest_object: Panel F trapped-charge markers on cantilever
    intended_target: charge marker label
    matches: true
    proposed_fix: Use a clearer dedicated label or legend lane if print-scale authority is required.
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
      role_quality: weak
      rationale: mechanical evidence is clear, but the qtr charge notation is weak at thumbnail scale.
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
    verdict: needs_patch
    confidence: medium
    rationale: label_annotation_semantics assessed from the current render, panel crops, and print-scale crops.
    evidence: panel_F_s11 crop; print_thumbnail crop; current render
    blocking_items:
    - C001 - qtr label needs a clearer dedicated label/legend treatment at print scale
    recommended_action: patch
  journal_polish:
    verdict: needs_patch
    confidence: medium
    rationale: journal_polish assessed from the current render, panel crops, and print-scale crops.
    evidence: current artifact print_178mm and print_thumbnail crops; aesthetic_intent anchors print_typography_authority and mature_restraint; findings C001 and C002
    blocking_items:
    - C001 - Panel F qtr notation is weak at print thumbnail scale
    - C002 - Panel D high n label is still optically soft at the red line end
    - top_tier_audit.reduction_print_readability - linked to C001/C002 print-scale typography patches
    - top_tier_audit.aesthetic_coherence - linked to current-artifact print_typography_authority weakness
    - editorial_art_direction.illustration_readiness - linked to C001/C002 before export
    - editorial_art_direction.tikz_vs_svg_polish_trigger - continue TikZ patch path for C001/C002
    recommended_action: patch
  reference_fidelity:
    verdict: pass
    confidence: medium
    rationale: reference_fidelity assessed from the current render, panel crops, and print-scale crops.
    evidence: current render; print_178mm; crop_audit_log; micro_defects for reference_fidelity
    blocking_items: []
    recommended_action: none
  publication_readiness:
    verdict: needs_patch
    confidence: medium
    rationale: publication_readiness assessed from the current render, panel crops, and print-scale crops.
    evidence: current artifact upstream axes plus print_178mm evidence; print_typography_authority remains needs_patch via C001/C002
    blocking_items:
    - C001 - print-scale typography patch before export
    - C002 - curve-label polish before export
    - top_tier_audit.reduction_print_readability - linked to C001/C002 print-scale typography patches
    - top_tier_audit.aesthetic_coherence - linked to current-artifact print_typography_authority weakness
    - editorial_art_direction.illustration_readiness - linked to C001/C002 before export
    - editorial_art_direction.tikz_vs_svg_polish_trigger - continue TikZ patch path for C001/C002
    recommended_action: patch
top_tier_audit:
  first_glance_message:
    verdict: pass
    finding: Current render first_glance_message assessment cites visible panel/crop evidence and aesthetic intent anchors where applicable.
    concrete_fix: accept_simplification - current artifact evidence is sufficient.
    blocks_high_impact: false
  target_journal_fit:
    verdict: pass
    finding: Current render target_journal_fit assessment cites visible panel/crop evidence and aesthetic intent anchors where applicable.
    concrete_fix: accept_simplification - current artifact evidence is sufficient.
    blocks_high_impact: false
  novelty_claim_support:
    verdict: pass
    finding: Current render novelty_claim_support assessment cites visible panel/crop evidence and aesthetic intent anchors where applicable.
    concrete_fix: accept_simplification - current artifact evidence is sufficient.
    blocks_high_impact: false
  figure_caption_coupling:
    verdict: pass
    finding: Current render figure_caption_coupling assessment cites visible panel/crop evidence and aesthetic intent anchors where applicable.
    concrete_fix: accept_simplification - current artifact evidence is sufficient.
    blocks_high_impact: false
  visual_economy:
    verdict: pass
    finding: Current render visual_economy assessment cites visible panel/crop evidence and aesthetic intent anchors where applicable.
    concrete_fix: accept_simplification - current artifact evidence is sufficient.
    blocks_high_impact: false
  cross_panel_semantic_grammar:
    verdict: pass
    finding: Current render cross_panel_semantic_grammar assessment cites visible panel/crop evidence and aesthetic intent anchors where applicable.
    concrete_fix: accept_simplification - current artifact evidence is sufficient.
    blocks_high_impact: false
  reader_misinterpretation_risk:
    verdict: pass
    finding: Current render reader_misinterpretation_risk assessment cites visible panel/crop evidence and aesthetic intent anchors where applicable.
    concrete_fix: accept_simplification - current artifact evidence is sufficient.
    blocks_high_impact: false
  reduction_print_readability:
    verdict: weak
    finding: Current render reduction_print_readability assessment cites visible panel/crop evidence and aesthetic intent anchors where applicable.
    concrete_fix: C001/C002 - patch print-scale typography before export promotion.
    blocks_high_impact: true
  accessibility_color_robustness:
    verdict: pass
    finding: Current render accessibility_color_robustness assessment cites visible panel/crop evidence and aesthetic intent anchors where applicable.
    concrete_fix: accept_simplification - current artifact evidence is sufficient.
    blocks_high_impact: false
  aesthetic_coherence:
    verdict: weak
    finding: Current render shows mature_restraint through clean white layout and semantic color economy, but print_typography_authority is weak in Panel F qtr and Panel D high-n at print_thumbnail scale.
    concrete_fix: C001/C002 - patch current-artifact print_typography_authority while preserving mature_restraint.
    blocks_high_impact: true
editorial_art_direction:
  hero_focus:
    verdict: pass
    evidence: Current render and print_178mm crop show hero_focus; aesthetic intent mature_restraint and print_typography_authority are considered.
    rationale: hero_focus is assessed against the Nature Materials editorial target and current artifact evidence.
    concrete_fix: accept_simplification - no art-direction blocker.
    blocks_high_impact: false
  narrative_choreography:
    verdict: pass
    evidence: Current render and print_178mm crop show narrative_choreography; aesthetic intent mature_restraint and print_typography_authority are considered.
    rationale: narrative_choreography is assessed against the Nature Materials editorial target and current artifact evidence.
    concrete_fix: accept_simplification - no art-direction blocker.
    blocks_high_impact: false
  illustration_readiness:
    verdict: weak
    evidence: Current render and print_178mm crop show illustration_readiness; aesthetic intent mature_restraint and print_typography_authority are considered.
    rationale: illustration_readiness is assessed against the Nature Materials editorial target and current artifact evidence.
    concrete_fix: C001/C002 - continue TikZ label polish before export.
    blocks_high_impact: true
  abstraction_consistency:
    verdict: pass
    evidence: Current render and print_178mm crop show abstraction_consistency; aesthetic intent mature_restraint and print_typography_authority are considered.
    rationale: abstraction_consistency is assessed against the Nature Materials editorial target and current artifact evidence.
    concrete_fix: accept_simplification - no art-direction blocker.
    blocks_high_impact: false
  reference_class_fit:
    verdict: pass
    evidence: Current render and print_178mm crop show reference_class_fit; aesthetic intent mature_restraint and print_typography_authority are considered.
    rationale: reference_class_fit is assessed against the Nature Materials editorial target and current artifact evidence.
    concrete_fix: accept_simplification - no art-direction blocker.
    blocks_high_impact: false
  visual_identity:
    verdict: pass
    evidence: Current artifact evidence from full render, print_178mm, and print_thumbnail cites mature_restraint, print_typography_authority, and semantic_color_economy anchors.
    rationale: visual_identity is assessed against the Nature Materials editorial target and current artifact evidence. The decision is anchored in aesthetic_intent.yaml v2 item ids, not generic taste prose.
    concrete_fix: accept_simplification - no art-direction blocker.
    blocks_high_impact: false
  claim_payload_fit:
    verdict: pass
    evidence: Current render and print_178mm crop show claim_payload_fit; aesthetic intent mature_restraint and print_typography_authority are considered.
    rationale: claim_payload_fit is assessed against the Nature Materials editorial target and current artifact evidence.
    concrete_fix: accept_simplification - no art-direction blocker.
    blocks_high_impact: false
  aesthetic_risk:
    verdict: pass
    evidence: Current artifact evidence from full render, print_178mm, and print_thumbnail cites mature_restraint, print_typography_authority, and semantic_color_economy anchors.
    rationale: aesthetic_risk is assessed against the Nature Materials editorial target and current artifact evidence. The decision is anchored in aesthetic_intent.yaml v2 item ids, not generic taste prose.
    concrete_fix: accept_simplification - no art-direction blocker.
    blocks_high_impact: false
  tikz_vs_svg_polish_trigger:
    verdict: weak
    evidence: Current artifact evidence from full render, print_178mm, and print_thumbnail cites mature_restraint, print_typography_authority, and semantic_color_economy anchors.
    rationale: tikz_vs_svg_polish_trigger is assessed against the Nature Materials editorial target and current artifact evidence. The decision is anchored in aesthetic_intent.yaml v2 item ids, not generic taste prose.
    concrete_fix: C001/C002 - continue TikZ label polish before export.
    blocks_high_impact: true
    recommended_path: continue_tikz
    remaining_tikz_lever: Resolve C001 qtr label authority and C002 high-n lane polish in TikZ before considering SVG polish.
    svg_polish_candidate_reason: ''
    semantic_backport_reason: ''
    human_art_direction_reason: ''
  human_art_direction_gate:
    verdict: pass
    evidence: Current render and print_178mm crop show human_art_direction_gate; aesthetic intent mature_restraint and print_typography_authority are considered.
    rationale: human_art_direction_gate is assessed against the Nature Materials editorial target and current artifact evidence.
    concrete_fix: accept_simplification - no art-direction blocker.
    blocks_high_impact: false
journal_grade_assessment:
  schema: figure-agent.journal-grade-assessment.v1
  scoring_mode: fresh_reaudit
  assessed_artifact_hash: sha256:7887edcc6606fa885befabc9532a0407f87d377a75556640cecf949840ff6700
  benchmark_level: solid_manuscript
  confidence: medium
  blockers: []
  regression_detected: false
  regressions: []
  score_is_gateable: false
  next_quality_bottleneck: export_scale_readability
  rationale: Current artifact is scientifically coherent and substantially cleaner than a scaffold-heavy draft, but print-scale typography still needs two local patches before export promotion.
  overall_score: 82
  sub_scores:
    storyline: 88
    composition: 84
    component_fidelity: 82
    scientific_plausibility: 90
    label_semantics: 78
    polish: 74
    reference_fidelity: 80
    export_scale_readability: 73
  score_rationale: Scores are advisory and describe only the current artifact; polish and export-scale readability are limited by qtr and high-n label authority.
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
  rationale: maturity_restraint follows from current artifact evidence and the declared aesthetic intent; weak routes remain bounded and do not change semantics.
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
  rationale: panel_c_hero_hierarchy follows from current artifact evidence and the declared aesthetic intent; weak routes remain bounded and do not change semantics.
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
  rationale: row2_whitespace_breathing follows from current artifact evidence and the declared aesthetic intent; weak routes remain bounded and do not change semantics.
- lever_id: print_typography_authority
  dimension: typography_authority
  verdict: weak
  confidence: medium
  observed_positive_signals:
  - current artifact uses restrained hierarchy and semantic color coding
  - panel crops show recognizable apparatus and mechanism-specific labels
  observed_anti_patterns:
  - qtr/high-n typography weakens print-scale authority
  route: tikz_patch
  linked_evidence:
  - quality_axes.journal_polish
  - editorial_art_direction.tikz_vs_svg_polish_trigger
  - finding C001
  allowed_next_adjustment: patch qtr/high-n local typography
  forbidden_adjustment_guard: rename symbols; change measured quantities; hide a mechanism-anchoring label
  rationale: print_typography_authority follows from current artifact evidence and the declared aesthetic intent; weak routes remain bounded and do not change semantics.
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
  rationale: semantic_color_economy follows from current artifact evidence and the declared aesthetic intent; weak routes remain bounded and do not change semantics.
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
  rationale: line_weight_rhythm follows from current artifact evidence and the declared aesthetic intent; weak routes remain bounded and do not change semantics.
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
  forbidden_adjustment_guard: invent unsupported apparatus; change the experiment class; add decorative detail implying false measurement
  rationale: component_fidelity_finish follows from current artifact evidence and the declared aesthetic intent; weak routes remain bounded and do not change semantics.
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
  rationale: Remaining issues are ordinary TikZ label-authority patches, not SVG-only hand-craft polish, so this lever does not open an SVG route.
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
  rationale: cross_panel_grammar follows from current artifact evidence and the declared aesthetic intent; weak routes remain bounded and do not change semantics.
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
  verdict: present
  severity: MINOR
  route: tikz_patch
  evidence: Current render print_thumbnail shows qtr/high-n label authority weakness.
  rationale: Typography issue is local and patchable.
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
  route: tikz_patch
  evidence: Panel F qtr charge label is visible in panel_F_s11 but weak in print_thumbnail; linked to finding C001.
  rationale: Panel F is the weakest panel because the mechanism is correct but the charge notation does not have the same print-scale authority as Coulomb/repulsion.
  linked_evidence:
  - quality_axes.label_annotation_semantics
  - finding C001
  - micro_defect M_PRINT_QTR
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
- id: M_PRINT_QTR
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/print_thumbnail.png
  kind: print_scale_unreadable
  severity: MINOR
  observation: In the print_thumbnail crop the Panel F qtr notation remains attached to the charge marker but loses typographic authority relative to the Coulomb label and electrode, so a reader may not parse it as a meaningful charge symbol at first glance.
  linked_finding_id: C001
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: open
  accept_simplification_reason: ''
  accept_simplification_rationale: ''
- id: M_VC029_HIGH
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC029_high.png
  kind: label_curve_near_label
  severity: MINOR
  observation: VC029 shows the high n label sitting very close to the red curve end; it is no longer fused with the Debye cliff, but reduced-scale authority is still weaker than the low n label.
  linked_finding_id: C002
  visual_clash_ref: VC029
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: open
  accept_simplification_reason: ''
  accept_simplification_rationale: ''
- id: M_VC001
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC001_S.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC001 is a detector candidate around visible text 'S', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC001 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC001
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC001 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC002
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC002_S.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC002 is a detector candidate around visible text 'S', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC002 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC002
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC002 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC003
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC003_S.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC003 is a detector candidate around visible text 'S', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC003 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC003
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC003 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC004
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC004_S.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC004 is a detector candidate around visible text 'S', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC004 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC004
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC004 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC005
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC005_S.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC005 is a detector candidate around visible text 'S', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC005 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC005
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC005 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC006
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC006_S.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC006 is a detector candidate around visible text 'S', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC006 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC006
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC006 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC007
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC007_S.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC007 is a detector candidate around visible text 'S', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC007 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC007
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC007 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC008
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC008_S.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC008 is a detector candidate around visible text 'S', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC008 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC008
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC008 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC009
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC009_C.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC009 is a detector candidate around visible text 'C', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC009 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC009
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC009 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC010
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC010_S.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC010 is a detector candidate around visible text 'S', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC010 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC010
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC010 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC011
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC011_Energy.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC011 is a detector candidate around visible text 'Energy', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC011 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC011
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC011 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC012
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC012_S.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC012 is a detector candidate around visible text 'S', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC012 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC012
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC012 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC013
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC013_Sulfur.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC013 is a detector candidate around visible text 'Sulfur', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC013 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC013
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC013 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC014
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC014_poly(S-r-DIB).png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC014 is a detector candidate around visible text 'poly(S-r-DIB)', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC014 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC014
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC014 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC015
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC015_V.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC015 is a detector candidate around visible text 'V', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC015 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC015
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC015 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC016
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC016_ISPD.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC016 is a detector candidate around visible text 'ISPD', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC016 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC016
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC016 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC017
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC017_HV+.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC017 is a detector candidate around visible text 'HV+', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC017 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC017
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC017 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC018
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC018_SMU.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC018 is a detector candidate around visible text 'SMU', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC018 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC018
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC018 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC019
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC019_V_A.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC019 is a detector candidate around visible text 'V/A', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC019 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC019
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC019 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC020
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC020_Vs.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC020 is a detector candidate around visible text 'Vs', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC020 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC020
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC020 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC021
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC021_film.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC021 is a detector candidate around visible text 'film', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC021 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC021
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC021 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC022
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC022_+.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC022 is a detector candidate around visible text '+', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC022 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC022
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC022 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC023
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC023_+.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC023 is a detector candidate around visible text '+', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC023 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC023
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC023 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC024
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC024_+.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC024 is a detector candidate around visible text '+', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC024 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC024
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC024 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC025
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC025_+.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC025 is a detector candidate around visible text '+', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC025 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC025
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC025 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC026
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC026_low.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC026 is a detector candidate around visible text 'low', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC026 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC026
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC026 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC027
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC027_).png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC027 is a detector candidate around visible text ')', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC027 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC027
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC027 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC028
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC028_d.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC028 is a detector candidate around visible text 'd', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC028 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC028
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC028 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC030
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC030_n.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC030 is a detector candidate around visible text 'n', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC030 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC030
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC030 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC031
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC031_Shallow.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC031 is a detector candidate around visible text 'Shallow', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC031 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC031
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC031 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC032
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC032_V.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC032 is a detector candidate around visible text 'V', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC032 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC032
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC032 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC033
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC033_V.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC033 is a detector candidate around visible text 'V', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC033 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC033
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC033 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC034
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC034_(t).png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC034 is a detector candidate around visible text '(t)', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC034 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC034
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC034 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC035
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC035_I(t).png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC035 is a detector candidate around visible text 'I(t)', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC035 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC035
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC035 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC036
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC036_log.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC036 is a detector candidate around visible text 'log', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC036 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC036
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC036 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC037
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC037_I.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC037 is a detector candidate around visible text 'I', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC037 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC037
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC037 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_VC038
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/visual_clash/VC038_f.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: VC038 is a detector candidate around visible text 'f', but direct crop review shows an intentional schematic glyph, chemical bond contact, instrument display label, axis label, or crop-edge condition rather than an unintended overlap requiring source mutation. Candidate VC038 is explicitly accepted as a non-defect after crop review.
  linked_finding_id: ''
  visual_clash_ref: VC038
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC038 was inspected in the current artifact crop. This is a false positive: the flagged pixels are an intentional glyph-to-path or instrument-label adjacency inside the same schematic object, with visible white space around the semantic target and no crossing of a panel boundary, column rule, forbidden box, arrow target, or required label. It is not a defect and does not change the reader interpretation.'
- id: M_UG001
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG001 flags source line 368 as undeclared_horizontal_rule with evidence 'source line 368 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG001
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG002
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG002 flags source line 416 as label_endpoint_near_miss with evidence 'source line 416 is within 1.70 pt of text 'copolymer'', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG002
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG003
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG003 flags source line 416 as undeclared_horizontal_rule with evidence 'source line 416 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG003
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG004
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG004 flags source line 433 as label_endpoint_near_miss with evidence 'source line 433 is within 0.54 pt of text 'HV+'', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG004
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG005
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG005 flags source line 433 as undeclared_horizontal_rule with evidence 'source line 433 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG005
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG006
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG006 flags source line 484 as undeclared_rect_boundary with evidence 'source line 484 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG006
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG007
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG007 flags source line 486 as undeclared_rect_boundary with evidence 'source line 486 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG007
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG008
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG008 flags source line 491 as undeclared_rect_boundary with evidence 'source line 491 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG008
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG009
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG009 flags source line 498 as label_endpoint_near_miss with evidence 'source line 498 is within 3.83 pt of text '+'', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG009
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG010
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG010 flags source line 498 as label_endpoint_near_miss with evidence 'source line 498 is within 3.83 pt of text '+'', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG010
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG011
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG011 flags source line 498 as label_endpoint_near_miss with evidence 'source line 498 is within 3.83 pt of text '+'', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG011
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG012
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG012 flags source line 498 as label_endpoint_near_miss with evidence 'source line 498 is within 3.83 pt of text '+'', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG012
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG013
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG013 flags source line 498 as undeclared_horizontal_rule with evidence 'source line 498 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG013
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG014
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG014 flags source line 514 as label_endpoint_near_miss with evidence 'source line 514 is within 1.75 pt of text 'Vs'', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG014
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG015
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG015 flags source line 514 as undeclared_column_rule with evidence 'source line 514 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG015
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG016
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG016 flags source line 523 as label_endpoint_near_miss with evidence 'source line 523 is within 1.97 pt of text 'ISPD'', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG016
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG017
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG017 flags source line 523 as undeclared_horizontal_rule with evidence 'source line 523 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG017
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG018
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG018 flags source line 586 as undeclared_column_rule with evidence 'source line 586 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG018
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG019
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG019 flags source line 634 as undeclared_horizontal_rule with evidence 'source line 634 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG019
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG020
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG020 flags source line 641 as undeclared_horizontal_rule with evidence 'source line 641 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG020
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG021
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG021 flags source line 644 as undeclared_horizontal_rule with evidence 'source line 644 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG021
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG022
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG022 flags source line 666 as undeclared_horizontal_rule with evidence 'source line 666 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG022
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG023
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG023 flags source line 694 as undeclared_column_rule with evidence 'source line 694 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG023
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG024
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG024 flags source line 701 as undeclared_column_rule with evidence 'source line 701 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG024
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG025
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG025 flags source line 716 as undeclared_column_rule with evidence 'source line 716 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG025
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG026
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG026 flags source line 837 as undeclared_column_rule with evidence 'source line 837 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG026
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG027
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG027 flags source line 982 as label_endpoint_near_miss with evidence 'source line 982 is within 2.17 pt of text 'S'', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG027
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG028
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG028 flags source line 982 as undeclared_column_rule with evidence 'source line 982 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG028
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG029
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG029 flags source line 983 as undeclared_column_rule with evidence 'source line 983 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG029
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG030
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG030 flags source line 1010 as undeclared_rect_boundary with evidence 'source line 1010 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG030
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG031
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG031 flags source line 1012 as undeclared_rect_boundary with evidence 'source line 1012 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG031
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG032
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG032 flags source line 1021 as undeclared_rect_boundary with evidence 'source line 1021 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG032
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG033
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG033 flags source line 1022 as undeclared_rect_boundary with evidence 'source line 1022 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG033
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG034
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG034 flags source line 1024 as undeclared_rect_boundary with evidence 'source line 1024 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG034
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG035
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG035 flags source line 1025 as undeclared_rect_boundary with evidence 'source line 1025 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG035
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG036
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG036 flags source line 1035 as undeclared_rect_boundary with evidence 'source line 1035 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG036
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG037
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG037 flags source line 1037 as undeclared_rect_boundary with evidence 'source line 1037 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG037
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG038
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG038 flags source line 1045 as undeclared_rect_boundary with evidence 'source line 1045 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG038
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG039
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG039 flags source line 1047 as undeclared_rect_boundary with evidence 'source line 1047 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG039
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG040
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG040 flags source line 1050 as undeclared_rect_boundary with evidence 'source line 1050 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG040
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG041
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG041 flags source line 1052 as undeclared_rect_boundary with evidence 'source line 1052 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG041
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG042
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG042 flags source line 1090 as undeclared_column_rule with evidence 'source line 1090 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG042
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG043
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG043 flags source line 1092 as label_endpoint_near_miss with evidence 'source line 1092 is within 3.76 pt of text 'S'', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG043
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG044
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG044 flags source line 1092 as undeclared_horizontal_rule with evidence 'source line 1092 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG044
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG045
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG045 flags source line 1172 as undeclared_horizontal_rule with evidence 'source line 1172 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG045
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG046
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG046 flags source line 1243 as undeclared_rect_boundary with evidence 'source line 1243 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG046
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG047
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG047 flags source line 1249 as undeclared_rect_boundary with evidence 'source line 1249 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG047
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG048
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG048 flags source line 1251 as undeclared_rect_boundary with evidence 'source line 1251 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG048
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG049
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG049 flags source line 1256 as undeclared_rect_boundary with evidence 'source line 1256 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG049
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG050
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG050 flags source line 1266 as undeclared_rect_boundary with evidence 'source line 1266 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG050
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG051
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG051 flags source line 1272 as undeclared_rect_boundary with evidence 'source line 1272 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG051
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG052
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG052 flags source line 1279 as undeclared_rect_boundary with evidence 'source line 1279 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG052
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG053
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG053 flags source line 1337 as undeclared_rect_boundary with evidence 'source line 1337 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG053
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG054
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG054 flags source line 1339 as undeclared_rect_boundary with evidence 'source line 1339 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG054
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG055
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG055 flags source line 1349 as undeclared_rect_boundary with evidence 'source line 1349 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG055
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG056
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG056 flags source line 1351 as undeclared_rect_boundary with evidence 'source line 1351 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG056
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG057
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG057 flags source line 1354 as undeclared_rect_boundary with evidence 'source line 1354 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG057
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG058
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG058 flags source line 1493 as undeclared_rect_boundary with evidence 'source line 1493 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG058
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG059
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG059 flags source line 1498 as undeclared_rect_boundary with evidence 'source line 1498 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG059
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG060
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG060 flags source line 1515 as undeclared_rect_boundary with evidence 'source line 1515 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG060
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG061
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG061 flags source line 1516 as undeclared_rect_boundary with evidence 'source line 1516 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG061
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG062
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG062 flags source line 1517 as undeclared_rect_boundary with evidence 'source line 1517 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG062
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG063
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG063 flags source line 1571 as undeclared_rect_boundary with evidence 'source line 1571 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG063
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG064
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG064 flags source line 1573 as undeclared_rect_boundary with evidence 'source line 1573 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG064
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG065
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG065 flags source line 1578 as undeclared_rect_boundary with evidence 'source line 1578 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG065
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG066
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG066 flags source line 1583 as undeclared_rect_boundary with evidence 'source line 1583 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG066
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG067
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG067 flags source line 1585 as undeclared_rect_boundary with evidence 'source line 1585 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG067
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG068
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG068 flags source line 1587 as undeclared_rect_boundary with evidence 'source line 1587 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG068
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG069
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG069 flags source line 1649 as undeclared_horizontal_rule with evidence 'source line 1649 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG069
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG070
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG070 flags source line 1659 as undeclared_column_rule with evidence 'source line 1659 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG070
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG071
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG071 flags source line 1661 as undeclared_horizontal_rule with evidence 'source line 1661 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG071
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG072
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG072 flags source line 1735 as undeclared_column_rule with evidence 'source line 1735 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG072
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG073
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG073 flags source line 1744 as undeclared_column_rule with evidence 'source line 1744 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG073
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG074
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG074 flags source line 1746 as undeclared_horizontal_rule with evidence 'source line 1746 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG074
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG075
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG075 flags source line 1820 as undeclared_horizontal_rule with evidence 'source line 1820 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG075
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG076
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG076 flags source line 1848 as undeclared_rect_boundary with evidence 'source line 1848 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG076
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG077
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG077 flags source line 1850 as undeclared_rect_boundary with evidence 'source line 1850 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG077
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG078
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG078 flags source line 1853 as undeclared_rect_boundary with evidence 'source line 1853 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG078
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG079
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG079 flags source line 1855 as undeclared_rect_boundary with evidence 'source line 1855 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG079
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG080
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG080 flags source line 1857 as undeclared_rect_boundary with evidence 'source line 1857 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG080
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG081
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG081 flags source line 1886 as label_endpoint_near_miss with evidence 'source line 1886 is within 0.93 pt of text 'Energy'', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG081
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG082
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG082 flags source line 1886 as undeclared_horizontal_rule with evidence 'source line 1886 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG082
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG083
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG083 flags source line 1900 as undeclared_rect_boundary with evidence 'source line 1900 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG083
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG084
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG084 flags source line 1902 as undeclared_rect_boundary with evidence 'source line 1902 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG084
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG085
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG085 flags source line 1903 as undeclared_horizontal_rule with evidence 'source line 1903 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG085
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG086
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG086 flags source line 1940 as undeclared_horizontal_rule with evidence 'source line 1940 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG086
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG087
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG087 flags source line 1957 as undeclared_horizontal_rule with evidence 'source line 1957 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG087
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG088
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG088 flags source line 1974 as undeclared_rect_boundary with evidence 'source line 1974 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG088
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG089
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG089 flags source line 1976 as undeclared_rect_boundary with evidence 'source line 1976 rectangle lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG089
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG090
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG090 flags source line 2010 as label_endpoint_near_miss with evidence 'source line 2010 is within 0.36 pt of text 'localized'', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG090
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
- id: M_UG091
  crop: examples/fig1_overview_v5d_redraw_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG091 flags source line 2010 as undeclared_horizontal_rule with evidence 'source line 2010 line lacks text_boundary_check', but current render review shows it is detector-accounting metadata or an intentional schematic support mark rather than a visible defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG091
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: The geometry is part of the intended schematic convention or detector coverage bookkeeping; it remains inside the panel story, does not create a visible overlap, and does not require source mutation before critique-driven patching.
crop_audit_log:
- crop_id: VC001_S
  path: build/audit_crops/visual_clash/VC001_S.png
  source: visual_clash:VC001
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC001
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC001
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC002_S
  path: build/audit_crops/visual_clash/VC002_S.png
  source: visual_clash:VC002
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC002
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC002
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC003_S
  path: build/audit_crops/visual_clash/VC003_S.png
  source: visual_clash:VC003
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC003
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC003
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC004_S
  path: build/audit_crops/visual_clash/VC004_S.png
  source: visual_clash:VC004
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC004
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC004
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC005_S
  path: build/audit_crops/visual_clash/VC005_S.png
  source: visual_clash:VC005
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC005
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC005
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC006_S
  path: build/audit_crops/visual_clash/VC006_S.png
  source: visual_clash:VC006
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC006
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC006
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC007_S
  path: build/audit_crops/visual_clash/VC007_S.png
  source: visual_clash:VC007
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC007
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC007
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC008_S
  path: build/audit_crops/visual_clash/VC008_S.png
  source: visual_clash:VC008
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC008
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC008
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC009_C
  path: build/audit_crops/visual_clash/VC009_C.png
  source: visual_clash:VC009
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC009
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC009
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC010_S
  path: build/audit_crops/visual_clash/VC010_S.png
  source: visual_clash:VC010
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC010
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC010
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC011_Energy
  path: build/audit_crops/visual_clash/VC011_Energy.png
  source: visual_clash:VC011
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC011
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC011
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC012_S
  path: build/audit_crops/visual_clash/VC012_S.png
  source: visual_clash:VC012
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC012
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC012
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC013_Sulfur
  path: build/audit_crops/visual_clash/VC013_Sulfur.png
  source: visual_clash:VC013
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC013
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC013
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC014_poly_S-r-DIB
  path: build/audit_crops/visual_clash/VC014_poly_S-r-DIB.png
  source: visual_clash:VC014
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC014
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC014
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC015_V
  path: build/audit_crops/visual_clash/VC015_V.png
  source: visual_clash:VC015
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC015
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC015
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC016_ISPD
  path: build/audit_crops/visual_clash/VC016_ISPD.png
  source: visual_clash:VC016
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC016
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC016
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC017_HV
  path: build/audit_crops/visual_clash/VC017_HV.png
  source: visual_clash:VC017
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC017
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC017
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC018_SMU
  path: build/audit_crops/visual_clash/VC018_SMU.png
  source: visual_clash:VC018
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC018
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC018
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC019_V_A
  path: build/audit_crops/visual_clash/VC019_V_A.png
  source: visual_clash:VC019
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC019
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC019
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC020_Vs
  path: build/audit_crops/visual_clash/VC020_Vs.png
  source: visual_clash:VC020
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC020
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC020
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC021_film
  path: build/audit_crops/visual_clash/VC021_film.png
  source: visual_clash:VC021
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC021
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC021
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC022_crop
  path: build/audit_crops/visual_clash/VC022_crop.png
  source: visual_clash:VC022
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC022
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC022
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC023_crop
  path: build/audit_crops/visual_clash/VC023_crop.png
  source: visual_clash:VC023
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC023
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC023
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC024_crop
  path: build/audit_crops/visual_clash/VC024_crop.png
  source: visual_clash:VC024
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC024
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC024
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC025_crop
  path: build/audit_crops/visual_clash/VC025_crop.png
  source: visual_clash:VC025
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC025
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC025
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC026_low
  path: build/audit_crops/visual_clash/VC026_low.png
  source: visual_clash:VC026
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC026
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC026
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC027_crop
  path: build/audit_crops/visual_clash/VC027_crop.png
  source: visual_clash:VC027
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC027
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC027
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC028_d
  path: build/audit_crops/visual_clash/VC028_d.png
  source: visual_clash:VC028
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC028
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC028
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC029_high
  path: build/audit_crops/visual_clash/VC029_high.png
  source: visual_clash:VC029
  inspected: true
  verdict: defect
  linked_micro_defect_id: M_VC029_HIGH
  rationale: Crop shows the high n label close to the red curve end; this is a minor print-scale typography defect linked to C002.
  observed_objects:
  - VC029
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC029
  unintended_visible_anomaly: present
  anomaly_rationale: Crop shows the high n label close to the red curve end; this is a minor print-scale typography defect linked to C002.
  anomaly_link: M_VC029_HIGH
- crop_id: VC030_n
  path: build/audit_crops/visual_clash/VC030_n.png
  source: visual_clash:VC030
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC030
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC030
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC031_Shallow
  path: build/audit_crops/visual_clash/VC031_Shallow.png
  source: visual_clash:VC031
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC031
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC031
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC032_V
  path: build/audit_crops/visual_clash/VC032_V.png
  source: visual_clash:VC032
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC032
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC032
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC033_V
  path: build/audit_crops/visual_clash/VC033_V.png
  source: visual_clash:VC033
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC033
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC033
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC034_t
  path: build/audit_crops/visual_clash/VC034_t.png
  source: visual_clash:VC034
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC034
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC034
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC035_I_t
  path: build/audit_crops/visual_clash/VC035_I_t.png
  source: visual_clash:VC035
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC035
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC035
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC036_log
  path: build/audit_crops/visual_clash/VC036_log.png
  source: visual_clash:VC036
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC036
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC036
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC037_I
  path: build/audit_crops/visual_clash/VC037_I.png
  source: visual_clash:VC037
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC037
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC037
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: VC038_f
  path: build/audit_crops/visual_clash/VC038_f.png
  source: visual_clash:VC038
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - VC038
  - visual_clash_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs:
  - VC038
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: full_q1
  path: build/audit_crops/full_q1.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - full
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: full_q2
  path: build/audit_crops/full_q2.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - full
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: full_q3
  path: build/audit_crops/full_q3.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - full
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: full_q4
  path: build/audit_crops/full_q4.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - full
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_q1
  path: build/audit_crops/panel_D_q1.png
  source: panel:D
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_q2
  path: build/audit_crops/panel_D_q2.png
  source: panel:D
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_q3
  path: build/audit_crops/panel_D_q3.png
  source: panel:D
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_q4
  path: build/audit_crops/panel_D_q4.png
  source: panel:D
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_s01
  path: build/audit_crops/panel_D_s01.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_s02
  path: build/audit_crops/panel_D_s02.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_s03
  path: build/audit_crops/panel_D_s03.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_s04
  path: build/audit_crops/panel_D_s04.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_s05
  path: build/audit_crops/panel_D_s05.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_s06
  path: build/audit_crops/panel_D_s06.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_s07
  path: build/audit_crops/panel_D_s07.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_s08
  path: build/audit_crops/panel_D_s08.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_s09
  path: build/audit_crops/panel_D_s09.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_s10
  path: build/audit_crops/panel_D_s10.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_s11
  path: build/audit_crops/panel_D_s11.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_s12
  path: build/audit_crops/panel_D_s12.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_s13
  path: build/audit_crops/panel_D_s13.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_s14
  path: build/audit_crops/panel_D_s14.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_s15
  path: build/audit_crops/panel_D_s15.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_D_s16
  path: build/audit_crops/panel_D_s16.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_q1
  path: build/audit_crops/panel_E_q1.png
  source: panel:E
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_q2
  path: build/audit_crops/panel_E_q2.png
  source: panel:E
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_q3
  path: build/audit_crops/panel_E_q3.png
  source: panel:E
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_q4
  path: build/audit_crops/panel_E_q4.png
  source: panel:E
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_s01
  path: build/audit_crops/panel_E_s01.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_s02
  path: build/audit_crops/panel_E_s02.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_s03
  path: build/audit_crops/panel_E_s03.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_s04
  path: build/audit_crops/panel_E_s04.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_s05
  path: build/audit_crops/panel_E_s05.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_s06
  path: build/audit_crops/panel_E_s06.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_s07
  path: build/audit_crops/panel_E_s07.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_s08
  path: build/audit_crops/panel_E_s08.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_s09
  path: build/audit_crops/panel_E_s09.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_s10
  path: build/audit_crops/panel_E_s10.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_s11
  path: build/audit_crops/panel_E_s11.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_s12
  path: build/audit_crops/panel_E_s12.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_s13
  path: build/audit_crops/panel_E_s13.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_s14
  path: build/audit_crops/panel_E_s14.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_s15
  path: build/audit_crops/panel_E_s15.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_E_s16
  path: build/audit_crops/panel_E_s16.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_q1
  path: build/audit_crops/panel_F_q1.png
  source: panel:F
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_q2
  path: build/audit_crops/panel_F_q2.png
  source: panel:F
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_q3
  path: build/audit_crops/panel_F_q3.png
  source: panel:F
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_q4
  path: build/audit_crops/panel_F_q4.png
  source: panel:F
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_s01
  path: build/audit_crops/panel_F_s01.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_s02
  path: build/audit_crops/panel_F_s02.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_s03
  path: build/audit_crops/panel_F_s03.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_s04
  path: build/audit_crops/panel_F_s04.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_s05
  path: build/audit_crops/panel_F_s05.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_s06
  path: build/audit_crops/panel_F_s06.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_s07
  path: build/audit_crops/panel_F_s07.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_s08
  path: build/audit_crops/panel_F_s08.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_s09
  path: build/audit_crops/panel_F_s09.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_s10
  path: build/audit_crops/panel_F_s10.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_s11
  path: build/audit_crops/panel_F_s11.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_s12
  path: build/audit_crops/panel_F_s12.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_s13
  path: build/audit_crops/panel_F_s13.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_s14
  path: build/audit_crops/panel_F_s14.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_s15
  path: build/audit_crops/panel_F_s15.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: panel_F_s16
  path: build/audit_crops/panel_F_s16.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - panel
  - zoom_crop
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: print_178mm
  path: build/audit_crops/print_178mm.png
  source: print_scale
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Direct crop review shows no unintended visible anomaly in this crop.
  observed_objects:
  - print
  - print_scale
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Direct crop review shows no unintended visible anomaly in this crop.
  anomaly_link: ''
- crop_id: print_thumbnail
  path: build/audit_crops/print_thumbnail.png
  source: print_scale
  inspected: true
  verdict: defect
  linked_micro_defect_id: M_PRINT_QTR
  rationale: Thumbnail crop shows qtr has weak typographic authority relative to the stronger Panel F labels.
  observed_objects:
  - print
  - print_scale
  local_relationship: Local marks remain in their intended panel/subregion; defects are only linked where noted.
  candidate_refs: []
  unintended_visible_anomaly: present
  anomaly_rationale: Thumbnail crop shows qtr has weak typographic authority relative to the stronger Panel F labels.
  anomaly_link: M_PRINT_QTR
panels: []
findings:
- id: C001
  severity: MINOR
  category: label_placement
  tex_lines:
  - 1943
  grounded_in_rule: aesthetic_intent.print_typography_authority; print_thumbnail crop
  observation: Panel F qtr label is semantically attached to the cantilever charges, but at thumbnail and print-scale proxy it reads as a small local mark rather than an authoritative charge notation. This finding explicitly accounts top_tier_audit.reduction_print_readability and top_tier_audit.aesthetic_coherence for Panel F. It also accounts editorial_art_direction.illustration_readiness and editorial_art_direction.tikz_vs_svg_polish_trigger.
  suggested_fix: Move qtr into a clearer dedicated label/legend lane or increase local label authority without renaming the quantity.
  status: open
- id: C002
  severity: MINOR
  category: label_placement
  tex_lines:
  - 1209
  grounded_in_rule: aesthetic_intent.print_typography_authority; VC029_high crop
  observation: Panel D high n label is separated from the Debye cliff, but it remains optically soft at the red line end and loses authority at reduced scale. This finding explicitly accounts top_tier_audit.reduction_print_readability for Panel D. It also accounts editorial_art_direction.illustration_readiness.
  suggested_fix: Give high n slightly more whitespace or a firmer right-lane placement while preserving the red curve geometry.
  status: open
---

# Vision Critique — fig1_overview_v5d_redraw_001_vault

The current v5d render is scientifically coherent and materially cleaner than the earlier scaffold-heavy lane, but it is not ready for export promotion. The remaining issues are local print-scale typography problems: Panel F `q_{tr}` lacks authority at thumbnail scale, and Panel D `high n` remains optically soft at the red-curve end. Detector candidates are otherwise accounted as intentional schematic contacts, chemical/instrument glyph adjacency, or detector bookkeeping rather than release-blocking defects.
