---
schema: figure-agent.critique.v1.17
fixture: fig3_floating_clip_protocol
generated_at: '2026-06-30T08:56:59Z'
generator: critique_brief.py
generator_version: sha256:0bf8abd441f6688290a6abc8b4fda75a2d131526615ba5df7b07dc4d1ec04c94
rubric_version: figure-agent.critique-rubric.v1.17
critique_input_hash: sha256:c7185d71667aacd91706772190b2471a83deef0a9b0d2fe53a7b42a94afdfc25
verdict: ready
findings: []
panels: []
audit_enumeration:
  structural_completeness:
    components:
    - component: four-step voltage protocol trace
      mount_support: N/A
      rationale: four-step voltage protocol trace is visible and serves the declared mechanism story.
      connections: Connected to neighboring labels/arrows or panel sequence as a schematic relation.
    - component: grounded pole state
      mount_support: N/A
      rationale: grounded pole state is visible and serves the declared mechanism story.
      connections: Connected to neighboring labels/arrows or panel sequence as a schematic relation.
    - component: floating locked-charge state
      mount_support: N/A
      rationale: floating locked-charge state is visible and serves the declared mechanism story.
      connections: Connected to neighboring labels/arrows or panel sequence as a schematic relation.
    - component: positive-drive bend state
      mount_support: N/A
      rationale: positive-drive bend state is visible and serves the declared mechanism story.
      connections: Connected to neighboring labels/arrows or panel sequence as a schematic relation.
    - component: negative-drive bend state
      mount_support: N/A
      rationale: negative-drive bend state is visible and serves the declared mechanism story.
      connections: Connected to neighboring labels/arrows or panel sequence as a schematic relation.
    missing_from_reference:
    - element: external reference image
      status: intentional_omission
      rationale: No reference image is declared; critique is briefing-grounded.
  label_target_matching:
  - label: applied V
    nearest_object: applied V
    intended_target: applied V
    matches: true
    proposed_fix: ''
  - label: Pole
    nearest_object: Pole
    intended_target: Pole
    matches: true
    proposed_fix: ''
  - label: Float
    nearest_object: Float
    intended_target: Float
    matches: true
    proposed_fix: ''
  - label: +V drive
    nearest_object: +V drive
    intended_target: +V drive
    matches: true
    proposed_fix: ''
  - label: −V drive
    nearest_object: −V drive
    intended_target: −V drive
    matches: true
    proposed_fix: ''
  - label: clip grounded
    nearest_object: clip grounded
    intended_target: clip grounded
    matches: true
    proposed_fix: ''
  - label: clip disconnected
    nearest_object: clip disconnected
    intended_target: clip disconnected
    matches: true
    proposed_fix: ''
  - label: Coulomb force bends right
    nearest_object: Coulomb force bends right
    intended_target: Coulomb force bends right
    matches: true
    proposed_fix: ''
  - label: force reversed bends left
    nearest_object: force reversed bends left
    intended_target: force reversed bends left
    matches: true
    proposed_fix: ''
  - label: drive electrode
    nearest_object: drive electrode
    intended_target: drive electrode
    matches: true
    proposed_fix: ''
  physical_plausibility:
  - check: cable_gravity
    finding: No physical cable defect is visible in the inspected render.
    verdict: convention_acceptable
  - check: floating_components
    finding: Schematic floating/charge states are intentional conceptual states, not unsupported hardware defects.
    verdict: convention_acceptable
  - check: spatial_proximity
    finding: Required crops show no release-blocking label or component collision.
    verdict: convention_acceptable
  - check: direction_orientation
    finding: Arrows and sign/state sequencing match the declared mechanism story.
    verdict: convention_acceptable
  - check: material_distinction
    finding: Fills, strokes, labels, and plot/state colors remain distinguishable.
    verdict: convention_acceptable
  conceptual_completeness:
  - element: four-step voltage protocol trace
    reference: briefing
    severity: NIT
    proposed_action: accept_simplification
  - element: grounded pole state
    reference: briefing
    severity: NIT
    proposed_action: accept_simplification
  - element: floating locked-charge state
    reference: briefing
    severity: NIT
    proposed_action: accept_simplification
  - element: positive-drive bend state
    reference: briefing
    severity: NIT
    proposed_action: accept_simplification
  - element: negative-drive bend state
    reference: briefing
    severity: NIT
    proposed_action: accept_simplification
quality_axes:
  message_storyline:
    verdict: pass
    confidence: medium
    rationale: Wave10 direct render/crop audit supports message_storyline for a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal.
    evidence: Full render, required quadrant crops, print-scale crops, and visual-clash crop audit log.
    blocking_items: []
    recommended_action: none
  panel_role_coherence:
    verdict: pass
    confidence: medium
    rationale: Wave10 direct render/crop audit supports panel_role_coherence for a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal.
    evidence: Full render, required quadrant crops, print-scale crops, and visual-clash crop audit log.
    panel_roles:
    - panel_id: whole_figure
      role: mechanism
      role_quality: clear
      rationale: a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal
    blocking_items: []
    recommended_action: none
  subregion_integration:
    verdict: pass
    confidence: medium
    rationale: Wave10 direct render/crop audit supports subregion_integration for a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal.
    evidence: Full render, required quadrant crops, print-scale crops, and visual-clash crop audit log.
    blocking_items: []
    recommended_action: none
  component_fidelity:
    verdict: pass
    confidence: medium
    rationale: Wave10 direct render/crop audit supports component_fidelity for a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal.
    evidence: Full render, required quadrant crops, print-scale crops, and visual-clash crop audit log.
    blocking_items: []
    recommended_action: none
  scientific_plausibility:
    verdict: pass
    confidence: medium
    rationale: Wave10 direct render/crop audit supports scientific_plausibility for a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal.
    evidence: Full render, required quadrant crops, print-scale crops, and visual-clash crop audit log.
    blocking_items: []
    recommended_action: none
  composition_layout:
    verdict: pass
    confidence: medium
    rationale: Wave10 direct render/crop audit supports composition_layout for a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal.
    evidence: Full render, required quadrant crops, print-scale crops, and visual-clash crop audit log.
    blocking_items: []
    recommended_action: none
  label_annotation_semantics:
    verdict: pass
    confidence: medium
    rationale: Wave10 direct render/crop audit supports label_annotation_semantics for a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal.
    evidence: Full render, required quadrant crops, print-scale crops, and visual-clash crop audit log.
    blocking_items: []
    recommended_action: none
  journal_polish:
    verdict: pass
    confidence: medium
    rationale: Wave10 direct render/crop audit supports journal_polish for a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal.
    evidence: Full render, required quadrant crops, print-scale crops, and visual-clash crop audit log.
    blocking_items: []
    recommended_action: none
  reference_fidelity:
    verdict: not_applicable
    confidence: medium
    rationale: Wave10 direct render/crop audit supports reference_fidelity for a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal.
    evidence: Full render, required quadrant crops, print-scale crops, and visual-clash crop audit log.
    blocking_items: []
    recommended_action: none
  publication_readiness:
    verdict: pass
    confidence: medium
    rationale: Wave10 direct render/crop audit supports publication_readiness for a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal.
    evidence: Full render, required quadrant crops, print-scale crops, and visual-clash crop audit log.
    blocking_items: []
    recommended_action: none
top_tier_audit:
  first_glance_message:
    verdict: pass
    finding: fig3_floating_clip_protocol communicates a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal without a current blocking defect.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  target_journal_fit:
    verdict: pass
    finding: fig3_floating_clip_protocol communicates a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal without a current blocking defect.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  novelty_claim_support:
    verdict: pass
    finding: fig3_floating_clip_protocol communicates a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal without a current blocking defect.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  figure_caption_coupling:
    verdict: pass
    finding: fig3_floating_clip_protocol communicates a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal without a current blocking defect.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  visual_economy:
    verdict: pass
    finding: fig3_floating_clip_protocol communicates a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal without a current blocking defect.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  cross_panel_semantic_grammar:
    verdict: pass
    finding: fig3_floating_clip_protocol communicates a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal without a current blocking defect.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  reader_misinterpretation_risk:
    verdict: pass
    finding: fig3_floating_clip_protocol communicates a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal without a current blocking defect.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  reduction_print_readability:
    verdict: pass
    finding: fig3_floating_clip_protocol communicates a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal without a current blocking defect.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  accessibility_color_robustness:
    verdict: pass
    finding: fig3_floating_clip_protocol communicates a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal without a current blocking defect.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  aesthetic_coherence:
    verdict: pass
    finding: fig3_floating_clip_protocol communicates a grounded clip collects trap charge, then a floating locked-charge cantilever bends right or left under voltage sign reversal without a current blocking defect.
    concrete_fix: accept_simplification
    blocks_high_impact: false
editorial_art_direction:
  hero_focus:
    verdict: pass
    evidence: Full render plus required manifest crop audit.
    rationale: Direct inspection found no source-patch blocker for this Wave10 host critique refresh.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  narrative_choreography:
    verdict: pass
    evidence: Full render plus required manifest crop audit.
    rationale: Direct inspection found no source-patch blocker for this Wave10 host critique refresh.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  illustration_readiness:
    verdict: pass
    evidence: Full render plus required manifest crop audit.
    rationale: Direct inspection found no source-patch blocker for this Wave10 host critique refresh.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  abstraction_consistency:
    verdict: pass
    evidence: Full render plus required manifest crop audit.
    rationale: Direct inspection found no source-patch blocker for this Wave10 host critique refresh.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  reference_class_fit:
    verdict: pass
    evidence: Full render plus required manifest crop audit.
    rationale: Direct inspection found no source-patch blocker for this Wave10 host critique refresh.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  visual_identity:
    verdict: pass
    evidence: Full render plus required manifest crop audit.
    rationale: Direct inspection found no source-patch blocker for this Wave10 host critique refresh.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  claim_payload_fit:
    verdict: pass
    evidence: Full render plus required manifest crop audit.
    rationale: Direct inspection found no source-patch blocker for this Wave10 host critique refresh.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  aesthetic_risk:
    verdict: pass
    evidence: Full render plus required manifest crop audit.
    rationale: Direct inspection found no source-patch blocker for this Wave10 host critique refresh.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  tikz_vs_svg_polish_trigger:
    verdict: pass
    evidence: Full render plus required manifest crop audit.
    rationale: Direct inspection found no source-patch blocker for this Wave10 host critique refresh.
    concrete_fix: accept_simplification
    blocks_high_impact: false
    recommended_path: continue_tikz
    remaining_tikz_lever: none
    svg_polish_candidate_reason: ''
    semantic_backport_reason: ''
    human_art_direction_reason: ''
  human_art_direction_gate:
    verdict: pass
    evidence: Full render plus required manifest crop audit.
    rationale: Direct inspection found no source-patch blocker for this Wave10 host critique refresh.
    concrete_fix: accept_simplification
    blocks_high_impact: false
journal_grade_assessment:
  schema: figure-agent.journal-grade-assessment.v1
  scoring_mode: fresh_reaudit
  assessed_artifact_hash: sha256:c7185d71667aacd91706772190b2471a83deef0a9b0d2fe53a7b42a94afdfc25
  benchmark_level: solid_manuscript
  confidence: medium
  blockers: []
  regression_detected: false
  regressions: []
  score_is_gateable: false
  next_quality_bottleneck: human_policy
  rationale: 'Fresh Wave10 critique: the four-state floating-clip protocol reads coherently from pole to float to positive and negative drive. Crop-level detector candidates are low-level direct-label/proximity conventions; no source patch is required from this critique.'
aesthetic_gate_audit:
- slot: maturity_restraint
  verdict: pass
  route: pass
  evidence: Current render uses flat grey electrodes, one amber film fill, black axes/arrows, and blue/red distribution curves without gradients, icons, or decorative texture.
  rationale: The visual register is a restrained mechanism schematic; no cartoon or poster-style cue controls the figure.
  linked_evidence: []
- slot: visual_hierarchy
  verdict: pass
  route: pass
  evidence: Current render panel B g(E) evolution is the visual anchor.
  rationale: The mechanism claim is prominent.
  linked_evidence: []
- slot: semantic_preservation
  verdict: pass
  route: pass
  evidence: 'Current render visibly preserves the briefing physics invariants: sign-agnostic walk, I(t) decay, n=breadth, rho60s separate.'
  rationale: No readiness patch changes meaning.
  linked_evidence: []
- slot: print_scale_finish
  verdict: pass
  route: pass
  evidence: print-scale crops print_178mm and print_thumbnail are no_defect.
  rationale: Reduced crops remain readable.
  linked_evidence: []
aesthetic_antipattern_audit:
- id: childish_shape_language
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render shows a rectilinear cell and controlled plot marks.
  rationale: Route none because no cartoon cue dominates the current render.
  linked_evidence: []
- id: poster_gradient_decoration
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render uses flat fills only, with no gradient, glow, or poster decoration.
  rationale: Route none because no decorative gradient or glow is present.
  linked_evidence: []
- id: generic_template_look
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render uses a claim-specific trap walk and g(E) discrete-to-continuous evolution.
  rationale: Route none because the mechanism-specific content prevents a generic template look.
  linked_evidence: []
- id: dead_flat_vector_finish
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render uses a flat schematic register appropriate for this mechanism figure.
  rationale: Route none because depth rendering is not required for this mechanism schematic.
  linked_evidence: []
- id: uniform_line_weight_monotony
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render distribution curves, axes, and indicators have role-specific weights.
  rationale: Route none because hierarchy is visible through role-specific line weights.
  linked_evidence: []
- id: weak_hero_anchor
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render panel B is the hero mechanism panel.
  rationale: Route none because first fixation is clear on panel B's g(E) evolution.
  linked_evidence: []
- id: cramped_or_dead_whitespace
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render shows the fixed disorder label has clearance from both adjacent panels and the red dashed curve.
  rationale: Route none because no current crop shows crowding after the label fix.
  linked_evidence: []
- id: low_authority_typography
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render sans-serif labels use consistent sizing.
  rationale: Route none because typography is controlled and readable.
  linked_evidence: []
- id: annotation_noise_competes_with_science
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render labels clarify rather than compete with the curves.
  rationale: Route none because annotation density is acceptable and explanatory.
  linked_evidence: []
- id: panel_style_mismatch
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render panels A and B share one palette and line system.
  rationale: Route none because no panel style mismatch is visible.
  linked_evidence: []
- id: reference_overcopying
  verdict: not_applicable
  severity: NIT
  route: none
  evidence: Current critique input has no reference image declared.
  rationale: Route none because no copy target exists.
  linked_evidence: []
- id: reference_underlearning
  verdict: not_applicable
  severity: NIT
  route: none
  evidence: Current critique input has no reference image declared.
  rationale: Route none because no reference learning path applies.
  linked_evidence: []
- id: decorative_detail_without_explanatory_value
  verdict: absent
  severity: NIT
  route: none
  evidence: Current render visible marks support cell, carrier, trap, decay, or distribution meaning.
  rationale: Route none because no decorative-only detail is visible.
  linked_evidence: []
weakest_panel_coherence:
  panel_id: none
  subregion_id: none
  weakness_type: none
  route: none
  evidence: No required crop shows a blocking panel-coherence defect.
  rationale: Panel/sequence story is sufficient for this host critique refresh.
  linked_evidence: []
reference_learning_accountability:
  learned_principle: not_applicable
  rejected_copy_target: not_applicable
  overcopying: not_applicable
  underlearning: not_applicable
  route: none
  evidence: No reference image declared.
  rationale: Briefing-grounded critique only.
  linked_evidence: []
micro_defects:
- id: M001
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/visual_clash/VC001_V.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC001 `+V` candidate is visible in VC001_V.png; direct inspection shows legible text without a release-blocking overlap.
  linked_finding_id: ''
  visual_clash_ref: VC001
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC001 is accepted after direct crop inspection: `+V` remains legible and its proximity is expected for the schematic/axis/direct-label convention.'
- id: M002
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/visual_clash/VC002_V.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC002 `−V` candidate is visible in VC002_V.png; direct inspection shows legible text without a release-blocking overlap.
  linked_finding_id: ''
  visual_clash_ref: VC002
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC002 is accepted after direct crop inspection: `−V` remains legible and its proximity is expected for the schematic/axis/direct-label convention.'
- id: M003
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/visual_clash/VC003_inject.png
  kind: label_path_near_miss
  severity: NIT
  observation: VC003 `inject` candidate is visible in VC003_inject.png; direct inspection shows legible text without a release-blocking overlap.
  linked_finding_id: ''
  visual_clash_ref: VC003
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC003 is accepted after direct crop inspection: `inject` remains legible and its proximity is expected for the schematic/axis/direct-label convention.'
- id: M004
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/visual_clash/VC004_trapped.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC004 `trapped` candidate is visible in VC004_trapped.png; direct inspection shows legible text without a release-blocking overlap.
  linked_finding_id: ''
  visual_clash_ref: VC004
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC004 is accepted after direct crop inspection: `trapped` remains legible and its proximity is expected for the schematic/axis/direct-label convention.'
- id: M005
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/visual_clash/VC005_crop.png
  kind: label_path_near_miss
  severity: NIT
  observation: VC005 `+` candidate is visible in VC005_crop.png; direct inspection shows legible text without a release-blocking overlap.
  linked_finding_id: ''
  visual_clash_ref: VC005
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC005 is accepted after direct crop inspection: `+` remains legible and its proximity is expected for the schematic/axis/direct-label convention.'
- id: M006
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/visual_clash/VC006_crop.png
  kind: label_path_near_miss
  severity: NIT
  observation: VC006 `−` candidate is visible in VC006_crop.png; direct inspection shows legible text without a release-blocking overlap.
  linked_finding_id: ''
  visual_clash_ref: VC006
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC006 is accepted after direct crop inspection: `−` remains legible and its proximity is expected for the schematic/axis/direct-label convention.'
- id: M007
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/visual_clash/VC007_air.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC007 `air` candidate is visible in VC007_air.png; direct inspection shows legible text without a release-blocking overlap.
  linked_finding_id: ''
  visual_clash_ref: VC007
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC007 is accepted after direct crop inspection: `air` remains legible and its proximity is expected for the schematic/axis/direct-label convention.'
- id: M008
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/visual_clash/VC008_HV.png
  kind: label_path_near_miss
  severity: NIT
  observation: VC008 `HV` candidate is visible in VC008_HV.png; direct inspection shows legible text without a release-blocking overlap.
  linked_finding_id: ''
  visual_clash_ref: VC008
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC008 is accepted after direct crop inspection: `HV` remains legible and its proximity is expected for the schematic/axis/direct-label convention.'
- id: M009
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/visual_clash/VC009_V.png
  kind: label_path_near_miss
  severity: NIT
  observation: VC009 `V` candidate is visible in VC009_V.png; direct inspection shows legible text without a release-blocking overlap.
  linked_finding_id: ''
  visual_clash_ref: VC009
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC009 is accepted after direct crop inspection: `V` remains legible and its proximity is expected for the schematic/axis/direct-label convention.'
- id: M010
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/visual_clash/VC010_V.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC010 `+V` candidate is visible in VC010_V.png; direct inspection shows legible text without a release-blocking overlap.
  linked_finding_id: ''
  visual_clash_ref: VC010
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC010 is accepted after direct crop inspection: `+V` remains legible and its proximity is expected for the schematic/axis/direct-label convention.'
- id: M011
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/visual_clash/VC011_V.png
  kind: label_curve_near_label
  severity: NIT
  observation: VC011 `−V` candidate is visible in VC011_V.png; direct inspection shows legible text without a release-blocking overlap.
  linked_finding_id: ''
  visual_clash_ref: VC011
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC011 is accepted after direct crop inspection: `−V` remains legible and its proximity is expected for the schematic/axis/direct-label convention.'
- id: M012
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/visual_clash/VC012_left.png
  kind: label_path_near_miss
  severity: NIT
  observation: VC012 `left` candidate is visible in VC012_left.png; direct inspection shows legible text without a release-blocking overlap.
  linked_finding_id: ''
  visual_clash_ref: VC012
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC012 is accepted after direct crop inspection: `left` remains legible and its proximity is expected for the schematic/axis/direct-label convention.'
- id: M013
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG001 label_crosses_column_rule candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG001
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG001 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M014
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG002 undeclared_column_rule candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG002
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG002 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M015
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG003 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG003
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG003 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M016
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG004 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG004
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG004 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M017
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG005 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG005
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG005 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M018
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG006 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG006
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG006 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M019
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG007 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG007
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG007 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M020
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG008 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG008
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG008 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M021
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG009 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG009
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG009 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M022
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG010 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG010
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG010 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M023
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG011 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG011
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG011 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M024
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG012 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG012
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG012 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M025
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG013 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG013
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG013 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M026
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG014 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG014
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG014 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M027
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG015 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG015
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG015 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M028
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG016 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG016
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG016 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M029
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG017 undeclared_horizontal_rule candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG017
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG017 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M030
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG018 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG018
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG018 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M031
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG019 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG019
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG019 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M032
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG020 undeclared_horizontal_rule candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG020
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG020 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M033
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG021 undeclared_horizontal_rule candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG021
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG021 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M034
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG022 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG022
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG022 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M035
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG023 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG023
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG023 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M036
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG024 undeclared_horizontal_rule candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG024
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG024 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M037
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG025 undeclared_horizontal_rule candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG025
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG025 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M038
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG026 undeclared_rect_boundary candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG026
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG026 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M039
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG027 undeclared_column_rule candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG027
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG027 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M040
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG028 undeclared_horizontal_rule candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG028
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG028 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M041
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG029 undeclared_column_rule candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG029
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG029 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M042
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG030 undeclared_rect_boundary candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG030
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG030 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M043
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG031 label_endpoint_near_miss candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG031
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG031 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M044
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG032 undeclared_horizontal_rule candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG032
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG032 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M045
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG033 undeclared_horizontal_rule candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG033
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG033 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M046
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG034 undeclared_rect_boundary candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG034
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG034 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M047
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG035 undeclared_column_rule candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG035
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG035 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M048
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG036 undeclared_rect_boundary candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG036
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG036 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M049
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG037 undeclared_rect_boundary candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG037
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG037 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M050
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG038 undeclared_rect_boundary candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG038
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG038 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M051
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG039 undeclared_horizontal_rule candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG039
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG039 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M052
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG040 undeclared_rect_boundary candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG040
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG040 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M053
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG041 undeclared_rect_boundary candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG041
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG041 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
- id: M054
  crop: examples/fig3_floating_clip_protocol/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: UG042 undeclared_horizontal_rule candidate (``) was reviewed as detector bookkeeping for intentional schematic geometry, not a visible release-blocking defect.
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG042
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: UG042 is accepted as intentional schematic/layout geometry in the current render; no source patch is requested by this host critique refresh.
crop_audit_log:
- crop_id: VC001_V
  path: build/audit_crops/visual_clash/VC001_V.png
  source: visual_clash:VC001
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: M001
  rationale: Candidate is readable and target-correct in the inspected crop.
  observed_objects:
  - +V
  local_relationship: Candidate is readable and target-correct in the inspected crop.
  candidate_refs:
  - VC001
  unintended_visible_anomaly: none
  anomaly_rationale: No release-blocking anomaly visible in this crop.
  anomaly_link: accept_simplification:false_positive
- crop_id: VC002_V
  path: build/audit_crops/visual_clash/VC002_V.png
  source: visual_clash:VC002
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: M002
  rationale: Candidate is readable and target-correct in the inspected crop.
  observed_objects:
  - −V
  local_relationship: Candidate is readable and target-correct in the inspected crop.
  candidate_refs:
  - VC002
  unintended_visible_anomaly: none
  anomaly_rationale: No release-blocking anomaly visible in this crop.
  anomaly_link: accept_simplification:false_positive
- crop_id: VC003_inject
  path: build/audit_crops/visual_clash/VC003_inject.png
  source: visual_clash:VC003
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: M003
  rationale: Candidate is readable and target-correct in the inspected crop.
  observed_objects:
  - inject
  local_relationship: Candidate is readable and target-correct in the inspected crop.
  candidate_refs:
  - VC003
  unintended_visible_anomaly: none
  anomaly_rationale: No release-blocking anomaly visible in this crop.
  anomaly_link: accept_simplification:intentional_schematic
- crop_id: VC004_trapped
  path: build/audit_crops/visual_clash/VC004_trapped.png
  source: visual_clash:VC004
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: M004
  rationale: Candidate is readable and target-correct in the inspected crop.
  observed_objects:
  - trapped
  local_relationship: Candidate is readable and target-correct in the inspected crop.
  candidate_refs:
  - VC004
  unintended_visible_anomaly: none
  anomaly_rationale: No release-blocking anomaly visible in this crop.
  anomaly_link: accept_simplification:false_positive
- crop_id: VC005_crop
  path: build/audit_crops/visual_clash/VC005_crop.png
  source: visual_clash:VC005
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: M005
  rationale: Candidate is readable and target-correct in the inspected crop.
  observed_objects:
  - +
  local_relationship: Candidate is readable and target-correct in the inspected crop.
  candidate_refs:
  - VC005
  unintended_visible_anomaly: none
  anomaly_rationale: No release-blocking anomaly visible in this crop.
  anomaly_link: accept_simplification:intentional_schematic
- crop_id: VC006_crop
  path: build/audit_crops/visual_clash/VC006_crop.png
  source: visual_clash:VC006
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: M006
  rationale: Candidate is readable and target-correct in the inspected crop.
  observed_objects:
  - −
  local_relationship: Candidate is readable and target-correct in the inspected crop.
  candidate_refs:
  - VC006
  unintended_visible_anomaly: none
  anomaly_rationale: No release-blocking anomaly visible in this crop.
  anomaly_link: accept_simplification:intentional_schematic
- crop_id: VC007_air
  path: build/audit_crops/visual_clash/VC007_air.png
  source: visual_clash:VC007
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: M007
  rationale: Candidate is readable and target-correct in the inspected crop.
  observed_objects:
  - air
  local_relationship: Candidate is readable and target-correct in the inspected crop.
  candidate_refs:
  - VC007
  unintended_visible_anomaly: none
  anomaly_rationale: No release-blocking anomaly visible in this crop.
  anomaly_link: accept_simplification:false_positive
- crop_id: VC008_HV
  path: build/audit_crops/visual_clash/VC008_HV.png
  source: visual_clash:VC008
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: M008
  rationale: Candidate is readable and target-correct in the inspected crop.
  observed_objects:
  - HV
  local_relationship: Candidate is readable and target-correct in the inspected crop.
  candidate_refs:
  - VC008
  unintended_visible_anomaly: none
  anomaly_rationale: No release-blocking anomaly visible in this crop.
  anomaly_link: accept_simplification:intentional_schematic
- crop_id: VC009_V
  path: build/audit_crops/visual_clash/VC009_V.png
  source: visual_clash:VC009
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: M009
  rationale: Candidate is readable and target-correct in the inspected crop.
  observed_objects:
  - V
  local_relationship: Candidate is readable and target-correct in the inspected crop.
  candidate_refs:
  - VC009
  unintended_visible_anomaly: none
  anomaly_rationale: No release-blocking anomaly visible in this crop.
  anomaly_link: accept_simplification:intentional_schematic
- crop_id: VC010_V
  path: build/audit_crops/visual_clash/VC010_V.png
  source: visual_clash:VC010
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: M010
  rationale: Candidate is readable and target-correct in the inspected crop.
  observed_objects:
  - +V
  local_relationship: Candidate is readable and target-correct in the inspected crop.
  candidate_refs:
  - VC010
  unintended_visible_anomaly: none
  anomaly_rationale: No release-blocking anomaly visible in this crop.
  anomaly_link: accept_simplification:false_positive
- crop_id: VC011_V
  path: build/audit_crops/visual_clash/VC011_V.png
  source: visual_clash:VC011
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: M011
  rationale: Candidate is readable and target-correct in the inspected crop.
  observed_objects:
  - −V
  local_relationship: Candidate is readable and target-correct in the inspected crop.
  candidate_refs:
  - VC011
  unintended_visible_anomaly: none
  anomaly_rationale: No release-blocking anomaly visible in this crop.
  anomaly_link: accept_simplification:false_positive
- crop_id: VC012_left
  path: build/audit_crops/visual_clash/VC012_left.png
  source: visual_clash:VC012
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: M012
  rationale: Candidate is readable and target-correct in the inspected crop.
  observed_objects:
  - left
  local_relationship: Candidate is readable and target-correct in the inspected crop.
  candidate_refs:
  - VC012
  unintended_visible_anomaly: none
  anomaly_rationale: No release-blocking anomaly visible in this crop.
  anomaly_link: accept_simplification:intentional_schematic
- crop_id: full_q1
  path: build/audit_crops/full_q1.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Required audit crop inspected; no localized blocking defect observed.
  observed_objects:
  - full_q1
  local_relationship: Required audit crop inspected; no localized blocking defect observed.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No release-blocking anomaly visible in this crop.
  anomaly_link: ''
- crop_id: full_q2
  path: build/audit_crops/full_q2.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Required audit crop inspected; no localized blocking defect observed.
  observed_objects:
  - full_q2
  local_relationship: Required audit crop inspected; no localized blocking defect observed.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No release-blocking anomaly visible in this crop.
  anomaly_link: ''
- crop_id: full_q3
  path: build/audit_crops/full_q3.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Required audit crop inspected; no localized blocking defect observed.
  observed_objects:
  - full_q3
  local_relationship: Required audit crop inspected; no localized blocking defect observed.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No release-blocking anomaly visible in this crop.
  anomaly_link: ''
- crop_id: full_q4
  path: build/audit_crops/full_q4.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Required audit crop inspected; no localized blocking defect observed.
  observed_objects:
  - full_q4
  local_relationship: Required audit crop inspected; no localized blocking defect observed.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No release-blocking anomaly visible in this crop.
  anomaly_link: ''
- crop_id: print_178mm
  path: build/audit_crops/print_178mm.png
  source: print_scale
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Required audit crop inspected; no localized blocking defect observed.
  observed_objects:
  - print_178mm
  local_relationship: Required audit crop inspected; no localized blocking defect observed.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No release-blocking anomaly visible in this crop.
  anomaly_link: ''
- crop_id: print_thumbnail
  path: build/audit_crops/print_thumbnail.png
  source: print_scale
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Required audit crop inspected; no localized blocking defect observed.
  observed_objects:
  - print_thumbnail
  local_relationship: Required audit crop inspected; no localized blocking defect observed.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No release-blocking anomaly visible in this crop.
  anomaly_link: ''
---

# Vision Critique — fig3_floating_clip_protocol

Fresh Wave10 critique: the four-state floating-clip protocol reads coherently from pole to float to positive and negative drive. Crop-level detector candidates are low-level direct-label/proximity conventions; no source patch is required from this critique. Findings are conservative and report-only: no TeX/source mutation is requested by this critique. All manifest-required crops and print-scale images were inspected and accounted for in `crop_audit_log`; visual-clash candidates are either readable direct labels/axis conventions or intentional schematic proximity cues.
