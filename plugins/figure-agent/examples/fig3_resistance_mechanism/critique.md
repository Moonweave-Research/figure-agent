---
schema: figure-agent.critique.v1.17
fixture: fig3_resistance_mechanism
generated_at: 2026-06-22T23:28:31Z
generator: critique_brief.py
generator_version: sha256:fbc45f5352711d631b796ba6b87785ae0a7c787c8b6baaa285c85cf7286c1147
rubric_version: figure-agent.critique-rubric.v1.17
critique_input_hash: sha256:a38c8ffee637745fa525b9c1468cf5c266a73e3e683c3132126061563bb3f8f4
verdict: revise
audit_enumeration:
  structural_completeness:
    components:
      - component: electrochemical cell (electrode/film/electrode stack)
        mount_support: yes
        rationale: "Top/bottom grey electrodes bound the amber sulfur-polymer film; closed rectangle."
        connections: "+V at top electrode, − at bottom electrode; both bias labels attached to their electrode edges."
      - component: carrier multiple-trapping walk
        mount_support: N/A
        rationale: "Dispersive walk is a trajectory, not a mounted part; injected at top electrode, terminates at circled trap."
        connections: "6 segments, each endpoint lands on an × trap site; final segment ends in the red circle (caught carrier)."
      - component: I(t) decay sparkline
        mount_support: yes
        rationale: "Axes (I vs t) drawn; curve attached to origin region; I∝t^-n label inside the axes box."
        connections: "Both axis arrows from common origin; curve spans the t domain."
      - component: g(E) trap-energy distribution panel
        mount_support: yes
        rationale: "E (horizontal) and g(E) (vertical) axes from a common origin; both distribution curves seated on the E axis."
        connections: "Blue discrete spike and red dashed broad curve share the E baseline; n-breadth and ρ60s indicators attached to the plot."
    missing_from_reference:
      - element: leader line from 'sulfur polymer' label to the film
        status: intentional_omission
        rationale: "Label sits inside the film region; direct placement is unambiguous, no leader needed."
      - element: explicit time markers / t>2s absorption-current regime tick on sparkline
        status: intentional_omission
        rationale: "Sparkline is a qualitative cue (briefing: slim/compact); quantitative axis ticks belong to the composited data graph, not this schematic."
      - element: ρ60s numeric scale on the magnitude indicator
        status: intentional_omission
        rationale: "ρ60s is shown as an orthogonal magnitude reference only (briefing §3 rule 5); numbers come from the data pipeline."
  label_target_matching:
    - label: "+V"
      nearest_object: "top grey electrode"
      intended_target: "top electrode (applied bias)"
      matches: true
      proposed_fix: ""
    - label: "−"
      nearest_object: "bottom grey electrode"
      intended_target: "bottom electrode (return)"
      matches: true
      proposed_fix: ""
    - label: "sulfur polymer"
      nearest_object: "amber film region"
      intended_target: "the disordered sulfur-polymer film"
      matches: true
      proposed_fix: ""
    - label: "I ∝ t^-n"
      nearest_object: "blue decay curve in sparkline"
      intended_target: "the transient-current decay curve"
      matches: true
      proposed_fix: ""
    - label: "current decays ⇒ R↑"
      nearest_object: "sparkline / cell"
      intended_target: "consequence of the I(t) decay (briefing §3 rule 1)"
      matches: true
      proposed_fix: ""
    - label: "broader g(E) ⇒ larger n ⇒ slower decay"
      nearest_object: "bridge text between panels A and B"
      intended_target: "the A→B causal bridge (breadth→n→decay rate)"
      matches: true
      proposed_fix: ""
    - label: "S60: discrete (single deep)"
      nearest_object: "blue sharp spike"
      intended_target: "the discrete low-sulfur distribution"
      matches: true
      proposed_fix: ""
    - label: "S80: continuous broad"
      nearest_object: "red dashed broad curve"
      intended_target: "the continuous high-sulfur distribution"
      matches: true
      proposed_fix: ""
    - label: "disorder ↑ (sulfur ↑)"
      nearest_object: "evolution arrow (blue spike → broad)"
      intended_target: "the discrete→continuous evolution arrow"
      matches: true
      proposed_fix: "Label binds to the correct arrow, but one ↑ glyph overlaps the red dashed broad curve (VC012); reposition for clearance, not retarget."
    - label: "n = breadth"
      nearest_object: "red horizontal double-arrow"
      intended_target: "the breadth span of the broad distribution (briefing §3 rule 2)"
      matches: true
      proposed_fix: ""
    - label: "ρ60s"
      nearest_object: "grey vertical double-arrow"
      intended_target: "the orthogonal magnitude metric (briefing §3 rule 5)"
      matches: true
      proposed_fix: ""
  physical_plausibility:
    - check: direction_orientation
      finding: "Evolution arrow points discrete spike → broad distribution, matching disorder↑ with sulfur↑ (briefing §3 rule 4). Sparkline decays monotonically (I∝t^-n). Carrier walk descends from +V toward −."
      verdict: convention_acceptable
    - check: floating_components
      finding: "No floating parts; both g(E) curves are seated on the E axis, indicators attach to the plot, walk endpoints land on trap sites."
      verdict: convention_acceptable
    - check: spatial_proximity
      finding: "n=breadth red double-arrow visually crosses the blue spike base; this is an overlay of a measurement span on overlapping distributions, not a contradiction of separation."
      verdict: convention_acceptable
    - check: material_distinction
      finding: "Amber film vs grey electrodes are clearly distinct; blue solid (discrete) vs red dashed (continuous) encode the two regimes via colour AND line style (redundant encoding)."
      verdict: convention_acceptable
    - check: cable_gravity
      finding: "No cables/wires in this schematic; carrier walk is a trajectory and is intentionally tortuous (dispersive transport)."
      verdict: convention_acceptable
    - check: direction_orientation
      finding: "Charge carrier is drawn sign-agnostic — a tortuous multiple-trapping walk with no clean +→− ballistic drift, honoring briefing §3 rule 3."
      verdict: convention_acceptable
  conceptual_completeness:
    - element: Curie–von Schweidler power-law decay I∝t^-n
      reference: briefing
      severity: NIT
      proposed_action: accept_simplification
    - element: discrete→continuous trap-distribution evolution with sulfur
      reference: briefing
      severity: NIT
      proposed_action: accept_simplification
    - element: orthogonal breadth (n) vs magnitude (ρ60s) decomposition
      reference: briefing
      severity: NIT
      proposed_action: accept_simplification
quality_axes:
  message_storyline:
    verdict: pass
    confidence: high
    rationale: "Reads as: bias drives a carrier through a disordered trap-filled film → current decays (R↑) → trap-energy distribution broadens discrete→continuous with sulfur. Matches briefing §1."
    evidence: "Panel A (cell+walk+sparkline) → bridge text → Panel B (g(E) evolution); full_q1/q3/q2/q4 crops."
    blocking_items: []
    recommended_action: none
  panel_role_coherence:
    verdict: pass
    confidence: high
    rationale: "Two panels with distinct, ordered roles: A = mechanism setup (transport+decay), B = model (trap-energy evolution). No redundancy or misordering."
    evidence: "Panel A and Panel B crops."
    panel_roles:
      - panel_id: "A"
        role: mechanism
        role_quality: clear
        rationale: "Cell + dispersive trapping walk + I(t) decay = the conduction/decay mechanism."
      - panel_id: "B"
        role: model
        role_quality: clear
        rationale: "g(E) discrete→continuous evolution = the trap-distribution model underlying n."
    blocking_items: []
    recommended_action: none
  subregion_integration:
    verdict: pass
    confidence: medium
    rationale: "Bridge text 'broader g(E) ⇒ larger n ⇒ slower decay' links A's decay to B's breadth; no global imbalance introduced by local elements."
    evidence: "Bridge text node (line 47) between panels; full_q3 crop."
    blocking_items: []
    recommended_action: none
  component_fidelity:
    verdict: pass
    confidence: high
    rationale: "Electrodes, film, walk, sparkline, and both distributions are identifiable and correctly attached; omissions are deliberate schematic restraint."
    evidence: "structural_completeness audit; full_q1/q3 crops."
    blocking_items: []
    recommended_action: none
  scientific_plausibility:
    verdict: pass
    confidence: high
    rationale: "All briefing §3 invariants honored: I∝t^-n decay, n=breadth (not density), sign-agnostic dispersive walk, discrete→continuous evolution, no depth-encoded strength, unlabeled × traps, no 'network' claim."
    evidence: "physical_plausibility audit; briefing §3 rules 1–7."
    blocking_items: []
    recommended_action: none
  composition_layout:
    verdict: needs_patch
    confidence: medium
    rationale: "Overall balance good and thumbnail-readable, but panel B's lower-left is congested where the evolution-arrow label seats against the dashed broad curve (VC012)."
    evidence: "full_q2 crop; VC012_crop; finding C001."
    blocking_items: ["C001 - panel B evolution-label congested against the dashed broad curve"]
    recommended_action: patch
  label_annotation_semantics:
    verdict: needs_patch
    confidence: high
    rationale: "All labels bind to their intended targets, but one ↑ glyph of 'disorder ↑ (sulfur ↑)' overlaps the red dashed broad curve (VC012, dark=0.141)."
    evidence: "label_target_matching audit; VC012_crop; finding C001."
    blocking_items: ["C001 - disorder-arrow label glyph overlaps dashed broad curve"]
    recommended_action: patch
  journal_polish:
    verdict: pass
    confidence: medium
    rationale: "Sans-serif, restrained palette (blue=discrete, red=continuous/breadth, amber=film, grey=electrodes/magnitude), economical line weights, no decorative noise. Single minor label/curve touch is the only polish gap."
    evidence: "print_178mm and print_thumbnail crops; full_q2/q4."
    blocking_items: []
    recommended_action: none
  reference_fidelity:
    verdict: not_applicable
    confidence: high
    rationale: "No reference image declared; reference-free briefing-grounded mode."
    evidence: "spec.yaml has no reference_image; brief 'Reference-free briefing-grounded critique mode'."
    blocking_items: []
    recommended_action: none
  publication_readiness:
    verdict: needs_patch
    confidence: high
    rationale: "Scientifically and structurally sound; one MINOR label-clearance patch (VC012) stands between this and a clean state. Not less severe than the label/composition axes."
    evidence: "label_annotation_semantics and composition_layout = needs_patch."
    blocking_items: ["C001 - label/curve overlap"]
    recommended_action: patch
top_tier_audit:
  first_glance_message:
    verdict: pass
    finding: "3s: a cell with a charge bouncing among traps + a decaying current. 10s: current decay ⇒ R↑. 30s: trap-energy distribution broadens discrete→continuous with sulfur, n=breadth."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  target_journal_fit:
    verdict: pass
    finding: "Fits a Nature-Communications mechanism schematic: low density, sans-serif, two-panel explanatory half of a composite figure."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  novelty_claim_support:
    verdict: pass
    finding: "Visual weight is on the discrete→continuous g(E) evolution (panel B), which is the paper's mechanism claim, not on generic cell components."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  figure_caption_coupling:
    verdict: pass
    finding: "Figure carries the mechanism with in-panel annotations; caption can stay light. Not overloaded, not caption-dependent."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  visual_economy:
    verdict: pass
    finding: "After removing the redundant bottom summary caption in prior iteration, ink is economical; the breadth/ρ60s indicators each earn their place."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  cross_panel_semantic_grammar:
    verdict: pass
    finding: "Colour grammar consistent: blue=discrete/S60, red=continuous/S80 and breadth, grey=neutral magnitude/electrodes, amber=film. Arrowheads consistent."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  reader_misinterpretation_risk:
    verdict: weak
    finding: "A reader could momentarily read the taller blue spike as 'larger magnitude', but breadth is the encoded variable (n=breadth) and depth/height is explicitly not the metric (briefing §3 rule 5)."
    concrete_fix: "accept_simplification — heights are schematic; n=breadth and ρ60s labels disambiguate."
    blocks_high_impact: false
  reduction_print_readability:
    verdict: pass
    finding: "print_178mm and print_thumbnail both keep labels legible and the two-regime contrast clear."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  accessibility_color_robustness:
    verdict: pass
    finding: "Discrete vs continuous encoded redundantly by colour AND line style (solid vs dashed); survives grayscale."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  aesthetic_coherence:
    verdict: pass
    finding: "Single visual authority: consistent line weights, sans-serif type, flat editorial schematic register across both panels."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
editorial_art_direction:
  hero_focus:
    verdict: pass
    evidence: "Panel B g(E) evolution (blue spike vs red broad) is the largest, highest-contrast element."
    rationale: "The mechanism claim should be the first fixation; it is."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  narrative_choreography:
    verdict: pass
    evidence: "Problem (bias+traps) → mechanism (decay, R↑) → model (g(E) evolution) flows left to right."
    rationale: "Reads as a sequence, not assembled fragments."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  illustration_readiness:
    verdict: pass
    evidence: "Flat vector schematic with disciplined strokes; appropriate for a main-text mechanism schematic (not a cover)."
    rationale: "Register matches target class; no depth/material rendering required here."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  abstraction_consistency:
    verdict: pass
    evidence: "Cell cartoon + sparkline data-plot + g(E) diagram are intentionally mixed and visually controlled at one detail level."
    rationale: "Mixed registers are deliberate and consistent."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  reference_class_fit:
    verdict: pass
    evidence: "Reads as nature_communications_mechanism_schematic."
    rationale: "Density, typography, and panel count fit the class."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  visual_identity:
    verdict: pass
    evidence: "Recurring motifs: × trap glyph, tortuous walk, dual-curve energy landscape, orthogonal breadth/magnitude arrows."
    rationale: "Coherent visual language specific to this trapping claim."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  claim_payload_fit:
    verdict: pass
    evidence: "The discrete→continuous evolution (the novelty) carries the most visual weight."
    rationale: "Central claim is dominant, not secondary."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  aesthetic_risk:
    verdict: weak
    evidence: "One ↑ glyph of the evolution-arrow label overlaps the dashed broad curve (VC012); a careful eye reads it as crowded text in panel B's lower-left."
    rationale: "Glyph-on-curve touches read as amateur typesetting at full scale."
    concrete_fix: "Reposition the evolution-arrow label off the dashed curve (see C001)."
    blocks_high_impact: false
  tikz_vs_svg_polish_trigger:
    verdict: pass
    evidence: "Remaining gap is a single source-level label-clearance issue (VC012), not an optical vector-cleanup problem."
    rationale: "Semantic/source work is not yet closed; one bounded TikZ edit remains, so SVG polish is premature."
    concrete_fix: "Apply the C001 label-clearance edit in TikZ."
    blocks_high_impact: false
    recommended_path: continue_tikz
    remaining_tikz_lever: "Reposition / restructure the 'disorder ↑ (sulfur ↑)' node (line 69) so no glyph overlaps the dashed broad curve (line 57)."
    svg_polish_candidate_reason: ""
    semantic_backport_reason: ""
    human_art_direction_reason: ""
  human_art_direction_gate:
    verdict: pass
    evidence: "Target class, hero panel, and register are settled; no taste fork blocks the next loop."
    rationale: "Only a bounded mechanical/layout patch remains."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
journal_grade_assessment:
  schema: figure-agent.journal-grade-assessment.v1
  scoring_mode: fresh_reaudit
  assessed_artifact_hash: sha256:a38c8ffee637745fa525b9c1468cf5c266a73e3e683c3132126061563bb3f8f4
  benchmark_level: solid_manuscript
  confidence: high
  blockers: []
  regression_detected: false
  regressions: []
  score_is_gateable: false
  next_quality_bottleneck: label_semantics
  rationale: "Briefing §3 invariants all preserved; structure and story are clear. The single remaining report-only issue is the VC012 label/curve clearance in panel B (label_semantics). Taste-level venue/register decisions are not pending, so this stays a bounded patch rather than human art direction."
aesthetic_gate_audit:
  - slot: maturity_restraint
    verdict: pass
    route: pass
    evidence: "full_q1/full_q2 crops: rectilinear cell, thin role-differentiated strokes, no juvenile/cartoon shapes visible."
    rationale: "Editorial schematic register is mature and restrained."
    linked_evidence:
      - top_tier_audit.aesthetic_coherence
  - slot: visual_hierarchy
    verdict: pass
    route: pass
    evidence: "full_q2 crop: the blue spike vs red broad curve is the dominant visible anchor in panel B."
    rationale: "First fixation lands on the mechanism claim."
    linked_evidence:
      - editorial_art_direction.hero_focus
  - slot: template_genericness
    verdict: pass
    route: pass
    evidence: "Trap walk and dual g(E) curves visible in the crops are specific to this trapping claim, not a reusable template."
    rationale: "Figure is tailored to the scientific claim."
    linked_evidence:
      - top_tier_audit.novelty_claim_support
  - slot: overdecorated_or_cartoonish
    verdict: pass
    route: pass
    evidence: "print-scale image shows flat fills only — no gradients, glows, or shadows."
    rationale: "No gradients, glows, or shadows are present; the fills stay flat and explanatory, not poster-style."
    linked_evidence:
      - editorial_art_direction.illustration_readiness
  - slot: journal_fit
    verdict: pass
    route: pass
    evidence: "print_178mm crop: density and typography fit a Nature-Communications mechanism schematic."
    rationale: "Matches target reference class."
    linked_evidence:
      - editorial_art_direction.reference_class_fit
  - slot: handcrafted_finish
    verdict: pass
    route: pass
    evidence: "Visible across panels: distribution curves (0.95pt) heavier than 0.35pt indicators — deliberate line-weight hierarchy."
    rationale: "Strokes are intentionally differentiated, not monotone."
    linked_evidence:
      - top_tier_audit.aesthetic_coherence
  - slot: semantic_preservation
    verdict: pass
    route: pass
    evidence: "Visible curve roles (blue discrete spike, red dashed broad) preserve briefing §3 invariants; no semantics altered."
    rationale: "No semantic drift in the current render."
    linked_evidence:
      - quality_axes.scientific_plausibility
  - slot: print_scale_finish
    verdict: pass
    route: pass
    evidence: "print_thumbnail crop keeps panel letters and labels legible at reduction."
    rationale: "Survives print/thumbnail reduction."
    linked_evidence:
      - top_tier_audit.reduction_print_readability
  - slot: paper_wide_coherence
    verdict: pass
    route: pass
    evidence: "Full-render png: colour grammar (blue/red/amber/grey) is consistent across both panels."
    rationale: "One coherent visual identity."
    linked_evidence:
      - editorial_art_direction.visual_identity
aesthetic_antipattern_audit:
  - id: childish_shape_language
    verdict: absent
    severity: NIT
    route: none
    evidence: "full_q1/q2: rectilinear cell, thin arrows, no rounded/cartoon shapes."
    rationale: "Editorial schematic, not juvenile."
    linked_evidence:
      - top_tier_audit.aesthetic_coherence
  - id: poster_gradient_decoration
    verdict: absent
    severity: NIT
    route: none
    evidence: "Flat fills only (amber film, grey electrodes); no gradients/glows."
    rationale: "Fills are flat with no gradients, glows, or shadows, so no poster-style decoration is present; route none is correct."
    linked_evidence:
      - editorial_art_direction.illustration_readiness
  - id: generic_template_look
    verdict: absent
    severity: NIT
    route: none
    evidence: "Trap walk + dual g(E) curves are tailored to this trapping claim."
    rationale: "Specific to the scientific claim, not a reusable template."
    linked_evidence:
      - top_tier_audit.novelty_claim_support
  - id: dead_flat_vector_finish
    verdict: absent
    severity: NIT
    route: none
    evidence: "Flat finish is appropriate; no material/depth distinction is required for this mechanism schematic."
    rationale: "The flat vector finish is the intended editorial register here; no depth or material rendering is needed for this schematic."
    linked_evidence:
      - editorial_art_direction.illustration_readiness
  - id: uniform_line_weight_monotony
    verdict: absent
    severity: NIT
    route: none
    evidence: "Distribution curves (0.95pt) heavier than indicator arrows (0.35pt) and film outline (0.4pt); hierarchy present."
    rationale: "Line weights are differentiated by role."
    linked_evidence:
      - top_tier_audit.aesthetic_coherence
  - id: weak_hero_anchor
    verdict: absent
    severity: NIT
    route: none
    evidence: "Panel B's high-contrast blue spike vs red broad curve is the clear anchor."
    rationale: "First fixation is the mechanism."
    linked_evidence:
      - editorial_art_direction.hero_focus
  - id: cramped_or_dead_whitespace
    verdict: present
    severity: NIT
    route: tikz_patch
    evidence: "Panel B lower-left is locally cramped where the evolution-arrow label meets the dashed curve (VC012_crop); elsewhere whitespace is balanced."
    rationale: "Localized crowding tied to the VC012 label clearance, not global dead space."
    linked_evidence:
      - editorial_art_direction.aesthetic_risk
      - M012
  - id: low_authority_typography
    verdict: absent
    severity: NIT
    route: none
    evidence: "Consistent sans-serif sizing; panel letters bold, annotations smaller — clean hierarchy."
    rationale: "Typography reads publication-grade."
    linked_evidence:
      - top_tier_audit.aesthetic_coherence
  - id: annotation_noise_competes_with_science
    verdict: absent
    severity: NIT
    route: none
    evidence: "After removing the redundant bottom caption, annotations support rather than compete with the curves/walk."
    rationale: "Annotation density is restrained."
    linked_evidence:
      - top_tier_audit.visual_economy
  - id: panel_style_mismatch
    verdict: absent
    severity: NIT
    route: none
    evidence: "Panels A and B share line-weight, colour, and type system."
    rationale: "One coherent visual system."
    linked_evidence:
      - editorial_art_direction.abstraction_consistency
  - id: reference_overcopying
    verdict: not_applicable
    severity: NIT
    route: none
    evidence: "No reference image declared."
    rationale: "No reference image is declared for this fixture, so there is no reference structure that could be over-copied."
    linked_evidence:
      - editorial_art_direction.reference_class_fit
  - id: reference_underlearning
    verdict: not_applicable
    severity: NIT
    route: none
    evidence: "No reference image declared."
    rationale: "No reference image is declared for this fixture, so there is no reference lesson that could be under-learned."
    linked_evidence:
      - editorial_art_direction.reference_class_fit
  - id: decorative_detail_without_explanatory_value
    verdict: absent
    severity: NIT
    route: none
    evidence: "Every mark (× traps, walk, curves, arrows) carries explanatory load."
    rationale: "No decorative-only detail."
    linked_evidence:
      - top_tier_audit.visual_economy
weakest_panel_coherence:
  panel_id: "B"
  subregion_id: "evolution-arrow label region (lower-left of g(E) plot)"
  weakness_type: composition
  route: tikz_patch
  evidence: "VC012_crop and full_q2: the 'disorder ↑ (sulfur ↑)' label seats against the descending dashed broad curve; one ↑ glyph overlaps it (dark=0.141)."
  rationale: "No scientific defect, but panel B's lower-left is the limiting composition: a wide label competes with the curve in a congested pocket while panel A is clean."
  linked_evidence:
    - quality_axes.label_annotation_semantics
    - editorial_art_direction.aesthetic_risk
    - micro_defect M012
reference_learning_accountability:
  learned_principle: "not_applicable — no reference image declared; critique is briefing-grounded only."
  rejected_copy_target: "not_applicable — nothing to copy or reject from a reference."
  overcopying: not_applicable
  underlearning: not_applicable
  route: none
  evidence: "spec.yaml declares no reference_image; brief runs reference-free mode."
  rationale: "Reference fidelity is out of scope; correctness is anchored to briefing §3 rules and detector evidence."
  linked_evidence:
    - editorial_art_direction.reference_class_fit
micro_defects:
  - id: M001
    crop: examples/fig3_resistance_mechanism/build/audit_crops/visual_clash/VC001_g_E.png
    kind: label_path_near_miss
    severity: NIT
    observation: "'g(E)' axis title and panel 'b' letter sit in clear white near the panel-B vertical axis; luma_std flag from the adjacent axis arrowhead, not an overlap."
    linked_finding_id: ""
    visual_clash_ref: "VC001"
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: ""
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "Axis title in clear space; no glyph/curve overlap on inspection of VC001 crop."
  - id: M002
    crop: examples/fig3_resistance_mechanism/build/audit_crops/visual_clash/VC002_V.png
    kind: label_path_near_miss
    severity: NIT
    observation: "'+V' bias label above the top electrode in clear white space."
    linked_finding_id: ""
    visual_clash_ref: "VC002"
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: ""
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "VC002 is not a defect: the +V label floats in clear background above the electrode with no geometry contact."
  - id: M003
    crop: examples/fig3_resistance_mechanism/build/audit_crops/visual_clash/VC003_b.png
    kind: label_path_near_miss
    severity: NIT
    observation: "Panel letter 'b' adjacent to the 'g(E)' axis title; both legible, no overlap."
    linked_finding_id: ""
    visual_clash_ref: "VC003"
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: ""
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "VC003 is not a defect: panel letter b and the g(E) axis title are distinct and legible, conventionally adjacent."
  - id: M004
    crop: examples/fig3_resistance_mechanism/build/audit_crops/visual_clash/VC004_sulfur.png
    kind: line_crosses_label
    severity: NIT
    observation: "Carrier-walk first segment originates near the 'sulfur polymer' film label; the line passes through the inter-letter gap (dark=0.062)."
    linked_finding_id: ""
    visual_clash_ref: "VC004"
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: ""
    status: accept_simplification
    accept_simplification_reason: convention_acceptable
    accept_simplification_rationale: "VC004 is not a defect: by convention the walk originates at the electrode beside the film label; only faint inter-letter ink crossing, both legible."
  - id: M005
    crop: examples/fig3_resistance_mechanism/build/audit_crops/visual_clash/VC005_crop.png
    kind: line_crosses_label
    severity: NIT
    observation: "Walk segment passes through an × trap glyph."
    linked_finding_id: ""
    visual_clash_ref: "VC005"
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: ""
    status: accept_simplification
    accept_simplification_reason: intentional_schematic
    accept_simplification_rationale: "VC005 is intentional, not a defect: the carrier walk crossing an x trap site is the repeatedly-trapped message (briefing §1, §6)."
  - id: M006
    crop: examples/fig3_resistance_mechanism/build/audit_crops/visual_clash/VC006_crop.png
    kind: line_crosses_label
    severity: NIT
    observation: "Walk segment passes through an × trap glyph."
    linked_finding_id: ""
    visual_clash_ref: "VC006"
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: ""
    status: accept_simplification
    accept_simplification_reason: intentional_schematic
    accept_simplification_rationale: "VC006 is intentional, not a defect: the walk passing through an x trap is the designed multiple-trapping geometry (briefing §6)."
  - id: M007
    crop: examples/fig3_resistance_mechanism/build/audit_crops/visual_clash/VC007_S60.png
    kind: label_path_near_miss
    severity: NIT
    observation: "'S60:' curve label near the blue spike; near_miss with low ink (dark=0.019)."
    linked_finding_id: ""
    visual_clash_ref: "VC007"
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: ""
    status: accept_simplification
    accept_simplification_reason: convention_acceptable
    accept_simplification_rationale: "VC007 is not a defect: the S60 label is a direct curve label above the spike, separate from the line by clear space."
  - id: M008
    crop: examples/fig3_resistance_mechanism/build/audit_crops/visual_clash/VC008_S80.png
    kind: label_path_near_miss
    severity: NIT
    observation: "'S80:' curve label upper-left near the broad curve; near_miss low ink (dark=0.018)."
    linked_finding_id: ""
    visual_clash_ref: "VC008"
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: ""
    status: accept_simplification
    accept_simplification_reason: convention_acceptable
    accept_simplification_rationale: "VC008 is not a defect: the S80 label is a direct curve label in clear space upper-left, separate from the broad curve flank."
  - id: M009
    crop: examples/fig3_resistance_mechanism/build/audit_crops/visual_clash/VC009_continuous.png
    kind: label_curve_near_label
    severity: NIT
    observation: "'continuous' (S80 label) sits near the broad curve's far-left flank; dark=0.093 but the crop shows clear white between text and dash."
    linked_finding_id: ""
    visual_clash_ref: "VC009"
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: ""
    status: accept_simplification
    accept_simplification_reason: convention_acceptable
    accept_simplification_rationale: "VC009 is not a defect: 'continuous' is a direct S80 curve label; white space separates the glyphs from the dashes."
  - id: M010
    crop: examples/fig3_resistance_mechanism/build/audit_crops/visual_clash/VC010_crop.png
    kind: line_crosses_label
    severity: NIT
    observation: "Walk segment passes through an × trap glyph."
    linked_finding_id: ""
    visual_clash_ref: "VC010"
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: ""
    status: accept_simplification
    accept_simplification_reason: intentional_schematic
    accept_simplification_rationale: "VC010 is intentional, not a defect: the walk crossing an x trap site is the designed trap-visit geometry (briefing §6)."
  - id: M011
    crop: examples/fig3_resistance_mechanism/build/audit_crops/visual_clash/VC011_crop.png
    kind: line_crosses_label
    severity: NIT
    observation: "Walk arrowhead lands at an × trap glyph."
    linked_finding_id: ""
    visual_clash_ref: "VC011"
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: ""
    status: accept_simplification
    accept_simplification_reason: intentional_schematic
    accept_simplification_rationale: "VC011 is intentional, not a defect: the walk arrowhead at an x trap is the designed trap-visit geometry (briefing §6)."
  - id: M012
    crop: examples/fig3_resistance_mechanism/build/audit_crops/visual_clash/VC012_crop.png
    kind: label_curve_near_label
    severity: MINOR
    observation: "One ↑ glyph of the 'disorder ↑ (sulfur ↑)' evolution-arrow label is overlapped by the red dashed broad curve's descending flank (dark=0.141, highest of all candidates)."
    linked_finding_id: "C001"
    visual_clash_ref: "VC012"
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: ""
    status: open
    accept_simplification_reason: ""
    accept_simplification_rationale: ""
  - id: M013
    crop: examples/fig3_resistance_mechanism/build/audit_crops/visual_clash/VC013_crop.png
    kind: line_crosses_label
    severity: NIT
    observation: "Walk segment passes through an × trap glyph."
    linked_finding_id: ""
    visual_clash_ref: "VC013"
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: ""
    status: accept_simplification
    accept_simplification_reason: intentional_schematic
    accept_simplification_rationale: "VC013 is intentional, not a defect: the walk crossing an x trap site is the designed multiple-trapping geometry (briefing §6)."
  - id: M014
    crop: examples/fig3_resistance_mechanism/build/audit_crops/visual_clash/VC014_crop.png
    kind: line_crosses_label
    severity: NIT
    observation: "Walk's final arrowhead reaches the circled × — the caught carrier (red circle around the trap)."
    linked_finding_id: ""
    visual_clash_ref: "VC014"
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: ""
    status: accept_simplification
    accept_simplification_reason: intentional_schematic
    accept_simplification_rationale: "VC014 is intentional, not a defect: the final arrowhead inside the circled x is the caught-carrier payload of panel A."
  - id: M015
    crop: examples/fig3_resistance_mechanism/build/audit_crops/visual_clash/VC015_ρ.png
    kind: label_path_near_miss
    severity: NIT
    observation: "'ρ' of the ρ60s label sits in clear white beside its magnitude double-arrow."
    linked_finding_id: ""
    visual_clash_ref: "VC015"
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: ""
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "VC015 is not a defect: the rho60s label sits beside its own arrow on clear background, separate from any curve."
  - id: M016
    crop: examples/fig3_resistance_mechanism/build/audit_crops/visual_clash/VC016_g_E.png
    kind: label_path_near_miss
    severity: NIT
    observation: "'g(E)' inside the panel-A bridge text 'broader g(E) ⇒ larger n'; near_miss low ink (dark=0.016)."
    linked_finding_id: ""
    visual_clash_ref: "VC016"
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: ""
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "VC016 is not a defect: g(E) is inline math in the panel-A bridge text, outside any curve or axis geometry."
  - id: M017
    crop: examples/fig3_resistance_mechanism/build/audit_crops/full_q4.png
    kind: label_path_near_miss
    severity: NIT
    observation: "UG009 reports a label_endpoint_near_miss (×, 3.55pt) for line 59, the n=breadth double-arrow; but that arrow is inside panel B's shifted scope while the only × glyphs are in panel A. The two never co-locate in the render (full_q4 shows no × in panel B)."
    linked_finding_id: ""
    visual_clash_ref: ""
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: "UG009"
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "Detector scope-transform artifact: pre-transform arrow coordinates are matched against panel-A trap coordinates; no real clash exists in the rendered figure."
  - id: M018
    crop: examples/fig3_resistance_mechanism/build/audit_crops/full_q1.png
    kind: label_path_near_miss
    severity: NIT
    observation: "UG001 (line 20): top grey electrode fill rectangle — intended cell electrode, visible at the top of panel A."
    linked_finding_id: ""
    visual_clash_ref: ""
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: "UG001"
    status: accept_simplification
    accept_simplification_reason: intentional_schematic
    accept_simplification_rationale: "Top electrode is a required cell component; recommended_action add_spec_check, no figure edit."
  - id: M019
    crop: examples/fig3_resistance_mechanism/build/audit_crops/full_q3.png
    kind: label_path_near_miss
    severity: NIT
    observation: "UG002 (line 21): bottom grey electrode fill rectangle — intended cell electrode, visible at the bottom of panel A."
    linked_finding_id: ""
    visual_clash_ref: ""
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: "UG002"
    status: accept_simplification
    accept_simplification_reason: intentional_schematic
    accept_simplification_rationale: "Bottom electrode is a required cell component; declare via spec, no figure edit."
  - id: M020
    crop: examples/fig3_resistance_mechanism/build/audit_crops/full_q1.png
    kind: label_path_near_miss
    severity: NIT
    observation: "UG003 (line 22): amber sulfur-polymer film fill rectangle — intended film region, visible between the electrodes."
    linked_finding_id: ""
    visual_clash_ref: ""
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: "UG003"
    status: accept_simplification
    accept_simplification_reason: intentional_schematic
    accept_simplification_rationale: "Film region is the active material; declare via spec, no figure edit."
  - id: M021
    crop: examples/fig3_resistance_mechanism/build/audit_crops/full_q1.png
    kind: label_path_near_miss
    severity: NIT
    observation: "UG004 (line 23): film outline rectangle — intended boundary of the film region, visible as the amber border."
    linked_finding_id: ""
    visual_clash_ref: ""
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: "UG004"
    status: accept_simplification
    accept_simplification_reason: intentional_schematic
    accept_simplification_rationale: "Film outline frames the active region; declare via spec, no figure edit."
  - id: M022
    crop: examples/fig3_resistance_mechanism/build/audit_crops/full_q1.png
    kind: label_path_near_miss
    severity: NIT
    observation: "UG005 (line 41): I(t) sparkline t-axis rule — intended axis, visible in the decay sparkline."
    linked_finding_id: ""
    visual_clash_ref: ""
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: "UG005"
    status: accept_simplification
    accept_simplification_reason: intentional_schematic
    accept_simplification_rationale: "Sparkline axis is intended scaffolding; declare via spec, no figure edit."
  - id: M023
    crop: examples/fig3_resistance_mechanism/build/audit_crops/full_q1.png
    kind: label_path_near_miss
    severity: NIT
    observation: "UG006 (line 42): I(t) sparkline I-axis rule — intended axis, visible in the decay sparkline."
    linked_finding_id: ""
    visual_clash_ref: ""
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: "UG006"
    status: accept_simplification
    accept_simplification_reason: intentional_schematic
    accept_simplification_rationale: "Sparkline axis is intended scaffolding; declare via spec, no figure edit."
  - id: M024
    crop: examples/fig3_resistance_mechanism/build/audit_crops/full_q4.png
    kind: label_path_near_miss
    severity: NIT
    observation: "UG007 (line 52): panel B E-axis rule — intended trap-energy axis, visible as the horizontal g(E) baseline."
    linked_finding_id: ""
    visual_clash_ref: ""
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: "UG007"
    status: accept_simplification
    accept_simplification_reason: intentional_schematic
    accept_simplification_rationale: "Energy axis is a required plot scaffold; declare via spec, no figure edit."
  - id: M025
    crop: examples/fig3_resistance_mechanism/build/audit_crops/full_q2.png
    kind: label_path_near_miss
    severity: NIT
    observation: "UG008 (line 53): panel B g(E)-axis rule — intended density axis, visible as the vertical g(E) axis."
    linked_finding_id: ""
    visual_clash_ref: ""
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: "UG008"
    status: accept_simplification
    accept_simplification_reason: intentional_schematic
    accept_simplification_rationale: "Density axis is a required plot scaffold; declare via spec, no figure edit."
  - id: M026
    crop: examples/fig3_resistance_mechanism/build/audit_crops/full_q4.png
    kind: label_path_near_miss
    severity: NIT
    observation: "UG010 (line 59): n=breadth horizontal double-arrow — intended breadth indicator, visible spanning the broad distribution."
    linked_finding_id: ""
    visual_clash_ref: ""
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: "UG010"
    status: accept_simplification
    accept_simplification_reason: intentional_schematic
    accept_simplification_rationale: "Breadth double-arrow encodes n (briefing §3 rule 2); declare via spec, no figure edit."
  - id: M027
    crop: examples/fig3_resistance_mechanism/build/audit_crops/full_q4.png
    kind: label_path_near_miss
    severity: NIT
    observation: "UG011 (line 62): ρ60s vertical double-arrow — intended orthogonal magnitude indicator, visible at the right of panel B."
    linked_finding_id: ""
    visual_clash_ref: ""
    text_boundary_ref: ""
    label_path_ref: ""
    undeclared_geometry_ref: "UG011"
    status: accept_simplification
    accept_simplification_reason: intentional_schematic
    accept_simplification_rationale: "Magnitude double-arrow encodes ρ60s (briefing §3 rule 5); declare via spec, no figure edit."
crop_audit_log:
  - crop_id: VC001_g_E
    path: build/audit_crops/visual_clash/VC001_g_E.png
    source: visual_clash:VC001
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Axis title 'g(E)' and panel 'b' in clear white; no overlap."
    observed_objects: ["g(E) axis title", "panel letter b", "axis arrowhead"]
    local_relationship: "Title sits just right of the vertical axis arrowhead, no contact."
    candidate_refs: ["VC001"]
    unintended_visible_anomaly: none
    anomaly_rationale: "No stray ink."
    anomaly_link: ""
  - crop_id: VC002_V
    path: build/audit_crops/visual_clash/VC002_V.png
    source: visual_clash:VC002
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "'+V' label isolated in white above the electrode."
    observed_objects: ["+V label"]
    local_relationship: "Free-floating label, no adjacent geometry."
    candidate_refs: ["VC002"]
    unintended_visible_anomaly: none
    anomaly_rationale: "Clean."
    anomaly_link: ""
  - crop_id: VC003_b
    path: build/audit_crops/visual_clash/VC003_b.png
    source: visual_clash:VC003
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel 'b' beside 'g(E)' title; both legible."
    observed_objects: ["panel letter b", "g of g(E)"]
    local_relationship: "Adjacent, non-overlapping."
    candidate_refs: ["VC003"]
    unintended_visible_anomaly: none
    anomaly_rationale: "Clean."
    anomaly_link: ""
  - crop_id: VC004_sulfur
    path: build/audit_crops/visual_clash/VC004_sulfur.png
    source: visual_clash:VC004
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Walk's first arrow passes through the gap in 'sulfur'; faint, both legible."
    observed_objects: ["sulfur polymer label", "walk segment 1", "film outline"]
    local_relationship: "Arrow descends across the inter-letter gap below 'sulfur'."
    candidate_refs: ["VC004"]
    unintended_visible_anomaly: none
    anomaly_rationale: "No spurious marks; faint expected crossing only."
    anomaly_link: "accept_simplification:convention_acceptable"
  - crop_id: VC005_crop
    path: build/audit_crops/visual_clash/VC005_crop.png
    source: visual_clash:VC005
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Walk line crosses an × trap — intended."
    observed_objects: ["walk segment", "× trap"]
    local_relationship: "Line passes over the trap glyph."
    candidate_refs: ["VC005"]
    unintended_visible_anomaly: none
    anomaly_rationale: "Expected trap-visit geometry."
    anomaly_link: "accept_simplification:intentional_schematic"
  - crop_id: VC006_crop
    path: build/audit_crops/visual_clash/VC006_crop.png
    source: visual_clash:VC006
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Walk line crosses an × trap — intended."
    observed_objects: ["walk segment", "× trap"]
    local_relationship: "Line passes over the trap glyph."
    candidate_refs: ["VC006"]
    unintended_visible_anomaly: none
    anomaly_rationale: "Expected trap-visit geometry."
    anomaly_link: "accept_simplification:intentional_schematic"
  - crop_id: VC007_S60
    path: build/audit_crops/visual_clash/VC007_S60.png
    source: visual_clash:VC007
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "'S60:' label above the blue spike; clear separation."
    observed_objects: ["S60 label", "blue spike top"]
    local_relationship: "Label sits above and right of the spike apex."
    candidate_refs: ["VC007"]
    unintended_visible_anomaly: none
    anomaly_rationale: "Clean."
    anomaly_link: ""
  - crop_id: VC008_S80
    path: build/audit_crops/visual_clash/VC008_S80.png
    source: visual_clash:VC008
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "'S80:' label upper-left; clear of the broad curve."
    observed_objects: ["S80 label", "broad curve left flank"]
    local_relationship: "Label above-left of the descending dashed flank."
    candidate_refs: ["VC008"]
    unintended_visible_anomaly: none
    anomaly_rationale: "Clean."
    anomaly_link: ""
  - crop_id: VC009_continuous
    path: build/audit_crops/visual_clash/VC009_continuous.png
    source: visual_clash:VC009
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "'continuous' text with white gap to the dashed curve; direct S80 label."
    observed_objects: ["continuous (S80 label)", "g(E) axis", "broad curve"]
    local_relationship: "Text left of axis-adjacent space, dashes well below."
    candidate_refs: ["VC009"]
    unintended_visible_anomaly: none
    anomaly_rationale: "No glyph overlap."
    anomaly_link: "accept_simplification:convention_acceptable"
  - crop_id: VC010_crop
    path: build/audit_crops/visual_clash/VC010_crop.png
    source: visual_clash:VC010
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Walk line crosses an × trap — intended."
    observed_objects: ["walk segment", "× trap"]
    local_relationship: "Arrow approaches and crosses the trap."
    candidate_refs: ["VC010"]
    unintended_visible_anomaly: none
    anomaly_rationale: "Expected trap-visit geometry."
    anomaly_link: "accept_simplification:intentional_schematic"
  - crop_id: VC011_crop
    path: build/audit_crops/visual_clash/VC011_crop.png
    source: visual_clash:VC011
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Walk arrowhead at an × trap — intended."
    observed_objects: ["walk arrowhead", "× trap"]
    local_relationship: "Arrowhead meets the trap glyph."
    candidate_refs: ["VC011"]
    unintended_visible_anomaly: none
    anomaly_rationale: "Expected trap-visit geometry."
    anomaly_link: "accept_simplification:intentional_schematic"
  - crop_id: VC012_crop
    path: build/audit_crops/visual_clash/VC012_crop.png
    source: visual_clash:VC012
    inspected: true
    verdict: defect
    linked_micro_defect_id: "M012"
    rationale: "A black ↑ glyph is overlapped by the red dashed broad curve's descending dashes; clear ink-on-glyph contact."
    observed_objects: ["↑ glyph of evolution-arrow label", "red dashed broad curve"]
    local_relationship: "Dashed curve crosses diagonally through the ↑ glyph."
    candidate_refs: ["VC012"]
    unintended_visible_anomaly: none
    anomaly_rationale: "The overlap itself is the defect; no other stray ink."
    anomaly_link: ""
  - crop_id: VC013_crop
    path: build/audit_crops/visual_clash/VC013_crop.png
    source: visual_clash:VC013
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Walk line crosses an × trap — intended."
    observed_objects: ["walk segment", "× trap"]
    local_relationship: "Line passes over the trap glyph."
    candidate_refs: ["VC013"]
    unintended_visible_anomaly: none
    anomaly_rationale: "Expected trap-visit geometry."
    anomaly_link: "accept_simplification:intentional_schematic"
  - crop_id: VC014_crop
    path: build/audit_crops/visual_clash/VC014_crop.png
    source: visual_clash:VC014
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Final walk arrowhead reaches the circled × (caught carrier)."
    observed_objects: ["walk arrowhead", "circled × trap", "red circle"]
    local_relationship: "Arrowhead enters the red circle around the trap."
    candidate_refs: ["VC014"]
    unintended_visible_anomaly: none
    anomaly_rationale: "Payload geometry of panel A."
    anomaly_link: "accept_simplification:intentional_schematic"
  - crop_id: VC015_ρ
    path: build/audit_crops/visual_clash/VC015_ρ.png
    source: visual_clash:VC015
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "'ρ' of ρ60s in clear white beside its arrow."
    observed_objects: ["ρ60s label"]
    local_relationship: "Label adjacent to its magnitude double-arrow, no overlap."
    candidate_refs: ["VC015"]
    unintended_visible_anomaly: none
    anomaly_rationale: "Clean."
    anomaly_link: ""
  - crop_id: VC016_g_E
    path: build/audit_crops/visual_clash/VC016_g_E.png
    source: visual_clash:VC016
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "'g(E)' inside panel-A bridge text; clear."
    observed_objects: ["bridge text g(E)"]
    local_relationship: "Inline math within a text line, clear of geometry."
    candidate_refs: ["VC016"]
    unintended_visible_anomaly: none
    anomaly_rationale: "Clean."
    anomaly_link: ""
  - crop_id: full_q1
    path: build/audit_crops/full_q1.png
    source: full_render
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Top-left: cell top, +V, sulfur-polymer label, upper walk, sparkline — all clean."
    observed_objects: ["cell top electrode", "+V", "sulfur polymer", "walk", "I(t) sparkline"]
    local_relationship: "Walk descends from the label area; sparkline isolated right of the cell."
    candidate_refs: ["VC004"]
    unintended_visible_anomaly: none
    anomaly_rationale: "No stray geometry."
    anomaly_link: ""
  - crop_id: full_q2
    path: build/audit_crops/full_q2.png
    source: full_render
    inspected: true
    verdict: defect
    linked_micro_defect_id: "M012"
    rationale: "Top-right (panel B upper): evolution arrow spans spike→broad; the 'disorder ↑ (sulfur ↑)' label's ↑ touches the dashed curve flank."
    observed_objects: ["blue spike", "red broad curve", "evolution arrow", "disorder label", "S60/S80 labels", "ρ60s arrow"]
    local_relationship: "Label seated in the lower-left pocket where the dashed flank descends into it."
    candidate_refs: ["VC012", "VC007", "VC008"]
    unintended_visible_anomaly: none
    anomaly_rationale: "Only the VC012 overlap; evolution-arrow-crosses-spike is intended discrete→broad connection."
    anomaly_link: ""
  - crop_id: full_q3
    path: build/audit_crops/full_q3.png
    source: full_render
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Bottom-left: circled carrier, lower traps, − electrode, carrier caption, bridge text — clean."
    observed_objects: ["circled carrier", "× traps", "− electrode", "carrier caption", "bridge text"]
    local_relationship: "Caption centered below the cell; bridge text right of the cell."
    candidate_refs: ["VC013", "VC014", "VC016"]
    unintended_visible_anomaly: none
    anomaly_rationale: "No stray geometry."
    anomaly_link: ""
  - crop_id: full_q4
    path: build/audit_crops/full_q4.png
    source: full_render
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Bottom-right (panel B lower): E axis, spike base, n=breadth arrow, ρ60s arrow, 'n = breadth' — clean; confirms no × in panel B (UG009 false positive)."
    observed_objects: ["E axis", "blue spike base", "n=breadth double-arrow", "ρ60s arrow", "n=breadth label"]
    local_relationship: "Breadth arrow spans under the curves; ρ60s vertical at right; no trap glyphs present."
    candidate_refs: ["UG009"]
    unintended_visible_anomaly: none
    anomaly_rationale: "n=breadth arrow crossing the spike base is an intended measurement overlay."
    anomaly_link: ""
  - crop_id: print_178mm
    path: build/audit_crops/print_178mm.png
    source: print_scale
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "At 178mm-equivalent width all labels stay legible and the two-regime contrast is clear; VC012 overlap is barely perceptible at this scale."
    observed_objects: ["full figure reduced"]
    local_relationship: "Both panels balanced; no label collapses at reduction."
    candidate_refs: []
    unintended_visible_anomaly: none
    anomaly_rationale: "No reduction failures."
    anomaly_link: ""
  - crop_id: print_thumbnail
    path: build/audit_crops/print_thumbnail.png
    source: print_scale
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Thumbnail keeps panel structure, blue-spike-vs-red-broad contrast, and panel letters readable."
    observed_objects: ["full figure thumbnail"]
    local_relationship: "Two-panel composition holds at thumbnail size."
    candidate_refs: []
    unintended_visible_anomaly: none
    anomaly_rationale: "No thumbnail failures."
    anomaly_link: ""
panels:
  - id: A
    findings: []
  - id: B
    findings: []
findings:
  - id: C001
    severity: MINOR
    category: label_placement
    tex_lines: [69, 69]
    grounded_in_rule: "detector VC012 (dark=0.141); briefing §2(b) label clarity for the g(E) evolution annotation"
    observation: "The evolution-arrow label 'disorder ↑ (sulfur ↑)' (line 69) seats in panel B's lower-left pocket where the red dashed broad curve (line 57) descends; one ↑ glyph is overlapped by the dashed flank (VC012_crop, full_q2). Label binds to the correct arrow — this is a clearance defect, not a targeting defect."
    suggested_fix: "Reposition the line-69 node so no glyph crosses the dashed curve: the label is wider than the clear gap at its current y, so a small downward/left coordinate nudge alone is insufficient. Prefer either (a) stacking it to two short lines 'disorder ↑' / '(sulfur ↑)' seated lower-left clear of the flank, or (b) shortening to a single short line near the arrowhead. Keep it visually attached to the evolution arrow."
    status: open
---

# Vision Critique — fig3_resistance_mechanism

**Verdict: revise (one MINOR label-clearance patch).** The figure is scientifically and structurally sound: every binding physics rule in briefing §3 is honored — the transient-current decay reads as I∝t⁻ⁿ with R↑, n is encoded as the *breadth* of g(E) (not density or depth), ρ60s is a separate orthogonal magnitude indicator, the carrier is a sign-agnostic tortuous multiple-trapping walk (no clean +→− drift), the trap distribution evolves discrete (S60, single deep spike) → continuous broad (S80), trap sites are unlabeled ×, and nothing asserts a trap "network". Story, panel roles, cross-panel colour grammar, reduction/print readability, and accessibility (colour + line-style redundancy) all pass.

The single open finding is **C001 / VC012**: after the prior hand-iteration moved the "disorder ↑ (sulfur ↑)" label off the blue S60 spike, one ↑ glyph now overlaps the red dashed broad curve's descending flank (dark = 0.141, the highest-ink candidate). It is a clearance issue in panel B's congested lower-left pocket, not a mislabeling — the label correctly belongs to the evolution arrow. Because the label is wider than the clear gap at its current height, a bounded coordinate nudge alone will not fully clear it; the concrete fix is to stack it into two short lines or shorten it while keeping it attached to the arrow.

Everything else flagged by the detectors is adjudicated as intended schematic or false positive:
- **× crossings (VC005/006/010/011/013/014)** are the carrier walk visiting trap sites and the final caught carrier in the red circle — the literal payload of panel A (briefing §1, §6).
- **text-on-fill / near-miss labels (VC001/002/003/007/008/009/015/016)** are direct labels in clear space; their luma/near-miss flags come from adjacent axis lines or their own curves, with no glyph overlap on crop inspection.
- **VC004** is the faint walk-origin crossing under the "sulfur polymer" film label at the injection electrode — convention-acceptable, low ink.
- **UG009** (the QD001 ledger evidence) is a detector scope-transform artifact: line 59's n=breadth double-arrow lives inside panel B's shifted scope, while the only × glyphs are in panel A; full_q4 confirms there is no × in panel B, so the 3.55 pt "near-miss" is a coordinate-frame false positive. The structured candidate path was correct to refuse it as `unknown_panel`.
- **UG001–008/010/011** are the intended cell rectangles, electrode fills, and axis/indicator rules; their recommended action is `add_spec_check` (declare in spec), not a figure edit.

Routing: `continue_tikz` — one bounded source-level label-clearance edit (C001) remains; SVG polish is premature. Weakest panel is **B**'s evolution-label pocket (composition), routed to `tikz_patch`. Report-only, human-gated; no auto-apply.
