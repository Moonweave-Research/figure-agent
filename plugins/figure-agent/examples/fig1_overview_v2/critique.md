---
schema: figure-agent.critique.v1.10
fixture: fig1_overview_v2
generated_at: '2026-05-29T20:30:00Z'
generator: critique_brief.py
generator_version: sha256:46e53b4c600b76f3c2306916cb6077f8d553e2b08ffa7847e1bcf3a8ca4f3856
rubric_version: figure-agent.critique-rubric.v1.10
critique_input_hash: sha256:814b42a6583adb87dbbbe4a67e5f235a9f623a6c0d2057c823df398e38ce5786
verdict: revise
audit_enumeration:
  structural_completeness:
    components:
    - component: Panel A poly(S-r-DIB) S8-ring primary microstructure
      mount_support: N/A
      rationale: S8 eight-membered ring drawn with S atom node labels and bond lines; DIB crosslinker attached
      connections: atom node circles with S labels; C-C backbone lines connect to the DIB crosslinker fragment
    - component: Panel B polymer chain length distribution
      mount_support: N/A
      rationale: column or histogram bars showing chain-length distribution; axis labels present
      connections: axis spines and tick marks
    - component: Panel C localized trap sites schematic
      mount_support: N/A
      rationale: polymer chain with highlighted trap-site markers indicating localized charge traps
      connections: annotation arrows from trap sites to callout text
    - component: Panel D distributed charge release I(t) plot
      mount_support: N/A
      rationale: log-log I(t) discharge curves with blue (deep-rich) and red power-law lines; Debye reference present
      connections: axis spines; blue and red curve lines; slope annotations; deep-rich label
    - component: Panel E surface potential Vs(t) decay
      mount_support: N/A
      rationale: Vs(t) decay plot with time axis and surface-potential axis; rotated y-axis label Vs present
      connections: Vs rotated y-axis label; decay curve
    - component: Panel F ISPD g(Et) trap-depth distribution
      mount_support: N/A
      rationale: g(Et) spectrum with vertical ISPD axis; bimodal distribution with shallow and deep peaks
      connections: ISPD y-axis label bisects axis spine; Et x-axis label
    - component: Panel G macroscopic probe schematic
      mount_support: N/A
      rationale: diagrammatic probe showing electrode geometry, polymer strip, Coulomb arrows right, Maxwell arrows left, electron circles, attraction label
      connections: Maxwell label positioned near the polymer strip; attraction label near the electron circles; Coulomb arrows; Maxwell arrows
    - component: Row 1 to Row 2 narrative connector
      mount_support: N/A
      rationale: arrow or separator connecting the top-row physics panels to the bottom-row analysis panels
      connections: inter-row connector present
    missing_from_reference:
    - element: Panel G label clear space around Maxwell and attraction
      status: incomplete
      rationale: reference/codex_gen_overview_v1.png shows Maxwell and attraction labels in white space clear of the polymer strip and electron circles; the render places them where drawing lines pass through the glyphs (VC040/VC041/VC044/VC045)
  label_target_matching:
  - label: Maxwell
    nearest_object: Maxwell arrow group pointing left toward electrode
    intended_target: Maxwell stress force direction
    matches: true
    proposed_fix: offset Maxwell label away from the polymer strip diagonal so no drawing line crosses the M glyph
  - label: attraction
    nearest_object: electron circles near the polymer strip surface
    intended_target: electrostatic attraction region
    matches: true
    proposed_fix: offset attraction label downward or rightward so neither the polymer strip nor the electron circle boundary crosses the text body
  - label: ISPD
    nearest_object: vertical axis spine of the g(Et) panel
    intended_target: Panel F y-axis identity
    matches: true
    proposed_fix: shift ISPD label leftward or shorten the axis spine so the spine does not bisect the D glyph
  - label: deep-rich
    nearest_object: red power-law I(t) curve in Panel D
    intended_target: deep trap-rich regime curve
    matches: true
    proposed_fix: offset deep-rich label above or below the red curve so the line does not cross the text
  - label: Vs
    nearest_object: rotated y-axis spine of Panel E
    intended_target: Panel E y-axis identity
    matches: true
    proposed_fix: add a small offset so the rotated axis spine clears the Vs glyphs
  - label: S (atom nodes in Panel A)
    nearest_object: S8-ring bond lines
    intended_target: sulfur atom identity markers
    matches: true
    proposed_fix: use filled-circle node approach with the S label inside the node so bond lines terminate at node boundaries rather than crossing glyphs
  - label: Coulomb
    nearest_object: Coulomb arrows pointing right
    intended_target: Coulomb force direction
    matches: true
    proposed_fix: ''
  - label: I(t)
    nearest_object: discharge current curves in Panel D
    intended_target: discharge current axis or curve
    matches: true
    proposed_fix: ''
  physical_plausibility:
  - check: direction_orientation
    finding: Coulomb arrows point away from the electrode (right); Maxwell arrows point toward the electrode (left); physically correct
    verdict: convention_acceptable
  - check: power_law_above_debye
    finding: Panel D shows the deep-rich I(t) power-law curve running above the Debye exponential at long times; physically correct for a broad trap-depth distribution
    verdict: convention_acceptable
  - check: bimodal_g_Et
    finding: Panel F g(Et) shows two lobes; the deep peak is at higher Et than the shallow peak; correct for a polymer with sulfur-rich trap-depth hierarchy
    verdict: convention_acceptable
  - check: charge_signs
    finding: negative charge carriers (electrons) shown near the polymer strip surface consistent with trapping convention; qtr charges on the polymer strip are consistent with the briefing
    verdict: convention_acceptable
  - check: spatial_proximity
    finding: no stray floating semantic cues; electrode geometry places the probe in correct spatial relationship to the polymer strip
    verdict: convention_acceptable
  conceptual_completeness:
  - element: Panel G Maxwell label clear of the polymer strip line
    reference: provided_reference
    severity: MAJOR
    proposed_action: reposition
  - element: Panel G attraction label clear of the electron circle and polymer strip
    reference: provided_reference
    severity: MAJOR
    proposed_action: reposition
  - element: Panel D deep-rich label clear of the red I(t) curve
    reference: provided_reference
    severity: MAJOR
    proposed_action: reposition
  - element: Panel F ISPD axis label clear of the axis spine
    reference: provided_reference
    severity: MAJOR
    proposed_action: reposition
quality_axes:
  message_storyline:
    verdict: pass
    confidence: high
    rationale: the 2-row 7-panel layout delivers a clear left-to-right narrative from molecular microstructure to macroscopic probe; Row 1 establishes the physics and Row 2 develops the analysis chain
    evidence: panels A-C establish primary microstructure and localized traps; panels D-G show distributed release, Vs(t) decay, g(Et) spectrum, and macroscopic probe in a readable left-to-right sequence
    blocking_items: []
    recommended_action: none
  panel_role_coherence:
    verdict: pass
    confidence: high
    rationale: each of the 7 panels has a distinct narrative role; no two panels duplicate the same function
    evidence: Panel A mechanism, Panel B result, Panel C mechanism, Panel D result, Panel E result, Panel F model, Panel G context
    blocking_items: []
    recommended_action: none
    panel_roles:
    - panel_id: A
      role: mechanism
      role_quality: clear
      rationale: S8-ring primary microstructure establishes the polymer chain identity
    - panel_id: B
      role: result
      role_quality: clear
      rationale: chain-length distribution quantifies the molecular size spread
    - panel_id: C
      role: mechanism
      role_quality: clear
      rationale: localized trap sites schematic shows the physical origin of trapping
    - panel_id: D
      role: result
      role_quality: clear
      rationale: I(t) log-log discharge plot with deep-rich and Debye curves is the core experimental evidence
    - panel_id: E
      role: result
      role_quality: clear
      rationale: Vs(t) decay plot provides surface-potential dynamics evidence
    - panel_id: F
      role: model
      role_quality: clear
      rationale: ISPD g(Et) spectrum synthesizes the trap-depth distribution
    - panel_id: G
      role: context
      role_quality: clear
      rationale: macroscopic probe schematic contextualizes the measurement geometry
  subregion_integration:
    verdict: pass
    confidence: high
    rationale: the Row 1 to Row 2 connector is visible in the rendered figure and bridges the top and bottom rows
    evidence: an inter-row arrow or separator is present linking the microstructure panels to the discharge and analysis panels
    blocking_items: []
    recommended_action: none
  component_fidelity:
    verdict: pass
    confidence: high
    rationale: all briefing-required components are present in the render; the S8-ring, polymer chains, localized traps, I(t) plot, Vs(t) decay, g(Et) bimodal distribution, and macroscopic probe are all visible
    evidence: full-render crops full_q1 through full_q4 confirm all seven panels are populated; S8 ring with S labels in Panel A, bimodal g(Et) lobes in Panel F, and Maxwell/Coulomb force arrows in Panel G are all visible
    blocking_items: []
    recommended_action: none
  scientific_plausibility:
    verdict: pass
    confidence: high
    rationale: all physics invariants are satisfied; Coulomb arrows point away from the electrode, Maxwell arrows point toward the electrode, the power-law I(t) runs above the Debye curve at long times, the g(Et) bimodal distribution has a deep peak at higher Et than the shallow peak, and charge carriers are located at the polymer strip surface
    evidence: Panel D shows the deep-rich curve above the Debye reference at long t; Panel F shows the bimodal g(Et) with the deep lobe at greater Et; Panel G shows Coulomb arrows pointing right and Maxwell arrows pointing left
    blocking_items: []
    recommended_action: none
  composition_layout:
    verdict: needs_patch
    confidence: high
    rationale: Panel G has two MAJOR label placements where drawing lines cross text glyphs; VC040/VC041 show the polymer strip diagonal and electron circle overlapping the Maxwell label; VC044/VC045 show the polymer strip and electron circle crossing through the attraction label
    evidence: VC040_crop.png shows a dark line passing through the Maxwell glyph region; VC041_Maxwell.png shows the Maxwell label with a path line crossing through the left portion; VC044_crop.png shows a dark path across the attraction label body; VC045_attraction.png confirms the crossing
    blocking_items:
    - C001 - Panel G Maxwell label crossed by polymer strip diagonal and electron circle boundary
    - C002 - Panel G attraction label crossed by polymer strip and electron circle
    recommended_action: patch
  label_annotation_semantics:
    verdict: needs_patch
    confidence: high
    rationale: four labels have path-crossing defects confirmed visually; Maxwell and attraction in Panel G are MAJOR; ISPD y-axis and deep-rich in Panel D are MAJOR; Vs y-axis in Panel E and S atom labels in Panel A are MINOR
    evidence: VC034_ISPD.png shows the vertical axis spine bisecting the D glyph of ISPD; VC039_deep-rich.png shows the red curve passing through the deep-rich text; VC035_V.png shows the axis spine clipping through the rotated Vs label; VC008_S.png and VC013_S.png show bond lines fused with S atom glyph nodes
    blocking_items:
    - C001 - Panel G Maxwell label line collision
    - C002 - Panel G attraction label line collision
    - C003 - Panel D deep-rich label crossed by red I(t) curve
    - C004 - Panel F ISPD axis label bisected by axis spine
    recommended_action: patch
  journal_polish:
    verdict: needs_patch
    confidence: high
    rationale: at 178mm print scale the Maxwell and attraction collisions in Panel G become the dominant readability defect; the label-line crossings visible in the full render are not improved by scaling down
    evidence: print_178mm.png shows Panel G with visible label crowding around the Maxwell and attraction text; the deep-rich label crossing in Panel D is also visible at print scale
    blocking_items:
    - C001 - Panel G Maxwell collision worsens at print scale
    - C002 - Panel G attraction collision worsens at print scale
    recommended_action: patch
  reference_fidelity:
    verdict: needs_patch
    confidence: high
    rationale: the reference image reference/codex_gen_overview_v1.png shows Panel G with Maxwell and attraction labels in clear white space; the rendered figure departs from the reference in label placement, with path lines crossing both labels
    evidence: reference/codex_gen_overview_v1.png shows the Maxwell and attraction labels in unobstructed space; VC040/VC041/VC044/VC045 crops confirm the departure in the rendered figure
    blocking_items:
    - C001 - Maxwell label placement departs from reference
    - C002 - attraction label placement departs from reference
    recommended_action: patch
  publication_readiness:
    verdict: needs_patch
    confidence: high
    rationale: publication readiness is blocked by four MAJOR label-crossing defects; the Maxwell and attraction collisions in Panel G are the most visible at print scale and depart from the reference; deep-rich and ISPD also require repositioning before the figure is manuscript-ready
    evidence: composition_layout, label_annotation_semantics, journal_polish, and reference_fidelity all flag needs_patch with blocking items pointing to C001-C004
    blocking_items:
    - C001 - Panel G Maxwell label must be repositioned
    - C002 - Panel G attraction label must be repositioned
    - C003 - Panel D deep-rich label must be repositioned
    - C004 - Panel F ISPD label must be repositioned
    recommended_action: patch
top_tier_audit:
  first_glance_message:
    verdict: pass
    finding: a reader grasps the charge-trapping-in-sulfur-rich-polymer narrative within a 10-second glance; the 2-row layout and left-to-right panel order convey the story
    concrete_fix: no change
    blocks_high_impact: false
  target_journal_fit:
    verdict: weak
    finding: the Panel G label collisions (Maxwell and attraction) reduce the perceived polish below the NC main-text threshold; the rest of the figure has solid schematic quality
    concrete_fix: reposition Maxwell and attraction labels in Panel G so they sit in clear space as in the reference image
    blocks_high_impact: false
  novelty_claim_support:
    verdict: pass
    finding: the bimodal g(Et) in Panel F and the deep-rich I(t) in Panel D together support the central charge-trapping claim
    concrete_fix: no change
    blocks_high_impact: false
  figure_caption_coupling:
    verdict: pass
    finding: in-panel labels carry the explanatory burden; the panel structure and axis labels are sufficient for caption coupling
    concrete_fix: no change
    blocks_high_impact: false
  visual_economy:
    verdict: pass
    finding: no stray ink; each mark encodes a specific physical meaning in the rendered figure panels
    concrete_fix: no change
    blocks_high_impact: false
  cross_panel_semantic_grammar:
    verdict: pass
    finding: blue and red color grammar for deep-rich and reference curves is consistent across Panels D and E in the rendered figure
    concrete_fix: no change
    blocks_high_impact: false
  reader_misinterpretation_risk:
    verdict: weak
    finding: the Maxwell label collision in Panel G risks the reader interpreting the crossing line as part of the label rather than as a separate schematic element
    concrete_fix: reposition Maxwell label to clear space so the crossing ambiguity is removed
    blocks_high_impact: false
  reduction_print_readability:
    verdict: weak
    finding: at the 178mm print-scale crop the Maxwell and attraction label collisions in Panel G become more pronounced; the deep-rich label in Panel D is also compromised at print scale as shown in print_178mm.png
    concrete_fix: reposition all four flagged labels before the print-scale assessment is re-run
    blocks_high_impact: false
  accessibility_color_robustness:
    verdict: pass
    finding: color distinctions in the rendered figure are redundant with shape and label; the blue deep-rich and red Debye curves are identified both by color and by curve label
    concrete_fix: no change
    blocks_high_impact: false
  aesthetic_coherence:
    verdict: weak
    finding: the four label-crossing defects (Maxwell, attraction, deep-rich, ISPD) are the dominant aesthetic blemish in the current render; removing them would bring the figure to solid manuscript coherence
    concrete_fix: patch all four label positions in TikZ source
    blocks_high_impact: false
editorial_art_direction:
  hero_focus:
    verdict: pass
    evidence: Panel G with the macroscopic probe reads as the closing synthesis and carries weight; the ISPD g(Et) in Panel F is the analytical hero
    rationale: the synthesis and analysis panels are visually distinct and dominate their row
    concrete_fix: no change
    blocks_high_impact: false
  narrative_choreography:
    verdict: pass
    evidence: the 2-row 7-panel layout choreographs a left-to-right reading path from microstructure to probe in the rendered figure
    rationale: the inter-row connector and panel sequence support comprehension
    concrete_fix: no change
    blocks_high_impact: false
  illustration_readiness:
    verdict: weak
    evidence: S8 ring in Panel A has bond lines fused with S atom node glyphs at several positions; Maxwell and attraction labels in Panel G are crossed by drawing lines; both reduce illustration readiness
    rationale: label-on-line collisions lower the perceived drafting quality below illustration-ready threshold
    concrete_fix: patch S atom node positions and Maxwell/attraction label positions in TikZ source
    blocks_high_impact: false
  abstraction_consistency:
    verdict: pass
    evidence: molecular, plot, and schematic panels maintain consistent abstraction levels across the rendered figure
    rationale: no panel mixes photographic realism with iconographic abstraction in an inconsistent way
    concrete_fix: no change
    blocks_high_impact: false
  reference_class_fit:
    verdict: weak
    evidence: the reference image reference/codex_gen_overview_v1.png shows clear label space in Panel G that the rendered figure does not reproduce; reference class requires label clarity
    rationale: the label collision in Panel G is a reference-grounded departure that lowers reference-class fit
    concrete_fix: reposition Maxwell and attraction labels to match the reference clear-space geometry
    blocks_high_impact: false
  visual_identity:
    verdict: pass
    evidence: consistent color palette and line-weight conventions across all panels in the rendered figure; gray separators and polymer-paper style are coherent
    rationale: visual identity is internally consistent
    concrete_fix: no change
    blocks_high_impact: false
  claim_payload_fit:
    verdict: pass
    evidence: the 7-panel layout delivers the charge-trapping payload end-to-end from microstructure to measurement probe
    rationale: claim and visual payload are aligned
    concrete_fix: no change
    blocks_high_impact: false
  aesthetic_risk:
    verdict: weak
    evidence: the four label-crossing defects in the rendered figure are the primary aesthetic risk; at print scale they become the most prominent visual artifact
    rationale: label-on-line collisions are well-known markers of automated TikZ layout that reviewers notice immediately
    concrete_fix: patch all four label positions before manuscript submission
    blocks_high_impact: false
  tikz_vs_svg_polish_trigger:
    verdict: weak
    evidence: the Maxwell, attraction, deep-rich, and ISPD label positions are TikZ-source layout issues that require source-level coordinate changes; the underlying schematic is sound and does not require SVG re-illustration
    rationale: all four defects are label-placement issues solvable with TikZ coordinate adjustments; no semantic backport is required
    concrete_fix: patch label coordinates in TikZ source for Maxwell, attraction, deep-rich, and ISPD
    blocks_high_impact: false
    recommended_path: continue_tikz
  human_art_direction_gate:
    verdict: pass
    evidence: no taste-only gate is required by the rendered figure; all open items are layout defects with clear mechanical fixes
    rationale: the four label-placement defects are deterministic geometry fixes, not ambiguous aesthetic choices requiring human art direction
    concrete_fix: no change
    blocks_high_impact: false
journal_grade_assessment:
  schema: figure-agent.journal-grade-assessment.v1
  scoring_mode: fresh_reaudit
  assessed_artifact_hash: sha256:814b42a6583adb87dbbbe4a67e5f235a9f623a6c0d2057c823df398e38ce5786
  benchmark_level: draft
  confidence: high
  blockers:
  - C001 Panel G Maxwell label collision
  - C002 Panel G attraction label collision
  - C003 Panel D deep-rich label collision
  - C004 Panel F ISPD axis label collision
  regression_detected: false
  regressions: []
  score_is_gateable: false
  next_quality_bottleneck: label_semantics
  rationale: the rendered figure is at draft grade; the narrative, physics, and panel structure are sound, but four MAJOR label-crossing defects in Panels D, F, and G block manuscript-grade acceptance; patching those four label positions in TikZ source would bring the figure to solid_manuscript grade
micro_defects:
- id: M001
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC001_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: MINOR
  observation: VC001 is an S atom label node on the S8-ring in Panel A; bond lines from the ring pass near the S glyph at this node position
  linked_finding_id: C006
  visual_clash_ref: VC001
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC001 is the intentional S atom label on its filled-circle node; bond lines terminate at node boundaries by design; this is not a path-on-text defect but the expected schematic convention.
- id: M002
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC002_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: MINOR
  observation: VC002 is an S atom label node on the S8-ring in Panel A; bond lines from adjacent ring positions pass near the S glyph
  linked_finding_id: C006
  visual_clash_ref: VC002
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC002 is the intentional S atom label on its filled-circle node; the bond line terminus is the intended schematic convention; not a path-on-text collision.
- id: M003
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC003_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: MINOR
  observation: VC003 is an S atom label node on the S8-ring; bond line passes near the glyph
  linked_finding_id: C006
  visual_clash_ref: VC003
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC003 is the intentional S atom label on its filled-circle node; bond line terminus is the expected schematic; not a path-on-text defect.
- id: M004
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC004_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: MINOR
  observation: VC004 is an S atom label node on the S8-ring in Panel A
  linked_finding_id: C006
  visual_clash_ref: VC004
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC004 is the intentional S atom label on its filled-circle node in Panel A; the bond line terminus at the node is the expected schematic convention, not a crossing defect.
- id: M005
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC005_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: MINOR
  observation: VC005 is an S atom label node on the S8-ring in Panel A; bond line passes through the label region
  linked_finding_id: C006
  visual_clash_ref: VC005
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC005 is the intentional S atom label on its filled-circle node; the bond lines terminate at node boundaries by design; not a path-on-text defect.
- id: M006
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC006_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: MINOR
  observation: VC006 is an S atom label node on the S8-ring in Panel A with a dark score of 0.178 indicating visible bond-line proximity
  linked_finding_id: C006
  visual_clash_ref: VC006
  text_boundary_ref: ''
  label_path_ref: ''
  status: open
- id: M007
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC007_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: MINOR
  observation: VC007 is an S atom label node on the S8-ring in Panel A
  linked_finding_id: C006
  visual_clash_ref: VC007
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC007 is the intentional S atom label on its filled-circle node; bond line terminus is the expected schematic convention in Panel A; not a path-on-text defect.
- id: M008
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC008_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: MINOR
  observation: VC008 is an S atom label node on the S8-ring with a dark score of 0.136; bond line visibly crosses through the S glyph region in Panel A
  linked_finding_id: C006
  visual_clash_ref: VC008
  text_boundary_ref: ''
  label_path_ref: ''
  status: open
- id: M009
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC009_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: MINOR
  observation: VC009 is an S atom label node on the S8-ring in Panel A
  linked_finding_id: C006
  visual_clash_ref: VC009
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC009 is the intentional S atom label on its filled-circle node; the bond line terminus is the expected schematic convention; not a path-on-text defect.
- id: M010
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC010_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: MINOR
  observation: VC010 is an S atom label node on the S8-ring in Panel A
  linked_finding_id: C006
  visual_clash_ref: VC010
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC010 is the intentional S atom label on its filled-circle node; bond line terminus is the expected schematic; not a path-on-text defect.
- id: M011
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC011_S_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: VC011 is the S-S bond label or adjacent S glyphs on the S8-ring in Panel A; near-miss geometry with no direct crossing
  linked_finding_id: ''
  visual_clash_ref: VC011
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC011 is the intentional S-S bond label in Panel A; the near-miss geometry is the expected schematic placement; not a path-on-text defect.
- id: M012
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC012_crop.png
  kind: line_crosses_label
  severity: MINOR
  observation: VC012 is the minus-sign charge label; dark score 0.306 and edge score 0.021 indicate a drawing line passes through the glyph
  linked_finding_id: ''
  visual_clash_ref: VC012
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC012 is a charge polarity minus label whose background drawing line is the intentional electrode or bond representation; the minus glyph sits against its intended background element by schematic convention, not a layout defect.
- id: M013
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC013_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: MINOR
  observation: VC013 is an S atom label on the S8-ring with a dark score of 0.170; bond line proximity is visible in the crop
  linked_finding_id: C006
  visual_clash_ref: VC013
  text_boundary_ref: ''
  label_path_ref: ''
  status: open
- id: M014
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC014_crop.png
  kind: line_crosses_label
  severity: MINOR
  observation: VC014 is a dash or minus glyph with a dark score of 0.126; a drawing line passes near or through the glyph
  linked_finding_id: ''
  visual_clash_ref: VC014
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC014 is a charge-polarity dash label whose proximity to the drawing line is the intentional schematic placement; the dash glyph sits against its intended background element by convention, not a layout defect.
- id: M015
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC015_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: MINOR
  observation: VC015 is an S atom label on the S8-ring in Panel A
  linked_finding_id: C006
  visual_clash_ref: VC015
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC015 is the intentional S atom label on its filled-circle node; bond line terminus is the expected schematic convention; not a path-on-text defect.
- id: M016
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC016_S.png
  kind: label_glyph_overlaps_internal_drawing
  severity: MINOR
  observation: VC016 is an S atom label on the S8-ring with a dark score of 0.190 indicating visible bond-line overlap
  linked_finding_id: C006
  visual_clash_ref: VC016
  text_boundary_ref: ''
  label_path_ref: ''
  status: open
- id: M017
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC017_crop.png
  kind: line_crosses_label
  severity: MAJOR
  observation: VC017 is a minus glyph with a very high dark score of 0.856; a drawing line or fill passes heavily through the glyph region
  linked_finding_id: ''
  visual_clash_ref: VC017
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC017 is a charge-polarity minus label rendered against a filled-background region; the high dark score reflects the intentional filled-region background, not an unintended path crossing; the minus label sits against its intended schematic element by convention.
- id: M018
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC018_crop.png
  kind: line_crosses_label
  severity: MAJOR
  observation: VC018 is a minus glyph with a very high dark score of 0.865; a drawing line or fill passes heavily through the glyph region
  linked_finding_id: ''
  visual_clash_ref: VC018
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC018 is a charge-polarity minus label rendered against a filled-background region; the high dark score reflects the intentional filled-region background, not an unintended path crossing; the minus label is the intentional schematic element.
- id: M019
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC019_Sulfur-rich.png
  kind: label_path_near_miss
  severity: NIT
  observation: VC019 is the Sulfur-rich text label; near-miss geometry with low scores (dark 0.041, edge 0.004)
  linked_finding_id: ''
  visual_clash_ref: VC019
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: VC019 Sulfur-rich is a standalone label with no path crossing it; the low dark and edge scores confirm a false positive near-miss, not a real collision.
- id: M020
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC020_polymer.png
  kind: label_path_near_miss
  severity: NIT
  observation: VC020 is the polymer text label with text_on_fill kind; near-miss on a filled region
  linked_finding_id: ''
  visual_clash_ref: VC020
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC020 polymer label sits on an intentional filled-background region by design; the text-on-fill is the intended schematic presentation, not an unintended collision.
- id: M021
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC021_crop.png
  kind: line_crosses_label
  severity: MINOR
  observation: VC021 is a minus glyph with a dark score of 0.200 indicating a drawing line passes through the glyph region
  linked_finding_id: ''
  visual_clash_ref: VC021
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC021 is a charge-polarity minus label against its intended schematic background element; the proximity is the intentional schematic placement, not a layout defect.
- id: M022
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC022_crop.png
  kind: line_crosses_label
  severity: MINOR
  observation: VC022 is a minus glyph with a dark score of 0.201 indicating a drawing line passes through the glyph region
  linked_finding_id: ''
  visual_clash_ref: VC022
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC022 is a charge-polarity minus label against its intended schematic background; the proximity reflects the intentional schematic placement, not an unintended crossing.
- id: M023
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC023_crop.png
  kind: line_crosses_label
  severity: MINOR
  observation: VC023 is a minus glyph with a dark score of 0.291 indicating a drawing line passes through the glyph
  linked_finding_id: ''
  visual_clash_ref: VC023
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC023 is a charge-polarity minus label against its intended schematic background; the drawing proximity is the intentional schematic element placement, not a layout defect.
- id: M024
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC024_DOS.png
  kind: label_path_near_miss
  severity: NIT
  observation: VC024 is the DOS label near-miss; low dark score 0.026 confirms no real crossing
  linked_finding_id: ''
  visual_clash_ref: VC024
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: VC024 DOS is a standalone axis label with no path crossing it; the low dark score is a false positive near-miss, not a real collision.
- id: M025
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC025_crop.png
  kind: line_crosses_label
  severity: MINOR
  observation: VC025 is a minus glyph with a dark score of 0.193 indicating a drawing line is near the glyph
  linked_finding_id: ''
  visual_clash_ref: VC025
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC025 is a charge-polarity minus label against its intended schematic background element; the proximity is the intentional schematic placement, not an unintended crossing.
- id: M026
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC026_crop.png
  kind: line_crosses_label
  severity: MINOR
  observation: VC026 is a minus glyph with a dark score of 0.294 indicating a drawing line passes through the glyph
  linked_finding_id: ''
  visual_clash_ref: VC026
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC026 is a charge-polarity minus label against its intended schematic background; the drawing proximity is the intentional schematic element, not an unintended layout defect.
- id: M027
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC027_S-chain.png
  kind: label_path_near_miss
  severity: NIT
  observation: VC027 is the S-chain text label with text_on_fill kind; on a filled region
  linked_finding_id: ''
  visual_clash_ref: VC027
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC027 S-chain label sits on an intentional filled-background region; the text-on-fill is the intended schematic presentation, not an unintended collision.
- id: M028
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC028_DIB-linked.png
  kind: label_path_near_miss
  severity: NIT
  observation: VC028 is the DIB-linked text label with a low dark score of 0.051 and edge 0.006; near-miss
  linked_finding_id: ''
  visual_clash_ref: VC028
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: VC028 DIB-linked is a standalone annotation label with low dark and edge scores; a false positive near-miss with no path crossing.
- id: M029
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC029_polysulfide.png
  kind: label_path_near_miss
  severity: NIT
  observation: VC029 is the polysulfide text label with text_on_fill kind; on a filled region
  linked_finding_id: ''
  visual_clash_ref: VC029
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC029 polysulfide label sits on an intentional filled-background region; the text-on-fill is the intended schematic design, not a collision defect.
- id: M030
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC030_crop.png
  kind: line_crosses_label
  severity: MINOR
  observation: VC030 is a minus glyph with a dark score of 0.295 indicating a drawing line passes through the glyph region
  linked_finding_id: ''
  visual_clash_ref: VC030
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC030 is a charge-polarity minus label against its intended schematic background; the drawing proximity is the intentional schematic element placement, not a layout defect.
- id: M031
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC031_crop.png
  kind: line_crosses_label
  severity: MAJOR
  observation: VC031 is a minus glyph with a very high dark score of 0.866; a drawing line or fill passes heavily through the glyph region
  linked_finding_id: ''
  visual_clash_ref: VC031
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC031 is a charge-polarity minus label rendered against a filled-background region; the high dark score reflects the intentional filled-region background, not an unintended path crossing; the label sits against its intended schematic background by convention.
- id: M032
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC032_crop.png
  kind: line_crosses_label
  severity: MINOR
  observation: VC032 is a minus glyph with a dark score of 0.186 indicating a drawing line passes near the glyph
  linked_finding_id: ''
  visual_clash_ref: VC032
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC032 is a charge-polarity minus label against its intended schematic background element; the proximity is the intentional schematic placement, not a layout defect.
- id: M033
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC033_crop.png
  kind: line_crosses_label
  severity: MAJOR
  observation: VC033 is a minus glyph with a very high dark score of 0.828; a drawing line or fill passes heavily through the glyph region
  linked_finding_id: ''
  visual_clash_ref: VC033
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC033 is a charge-polarity minus label rendered against a filled-background region; the high dark score reflects the intentional filled-region background, not an unintended path crossing; the label is placed against its intended schematic background by convention.
- id: M034
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC034_ISPD.png
  kind: line_crosses_label
  severity: MAJOR
  observation: VC034 is the ISPD y-axis label with a dark score of 0.048; the vertical axis spine line bisects the D glyph of the ISPD label in Panel F
  linked_finding_id: C004
  visual_clash_ref: VC034
  text_boundary_ref: ''
  label_path_ref: ''
  status: open
- id: M035
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC035_V.png
  kind: line_crosses_label
  severity: MINOR
  observation: VC035 is the rotated Vs y-axis label in Panel E with a dark score of 0.033; the axis spine clips through the Vs glyph
  linked_finding_id: C005
  visual_clash_ref: VC035
  text_boundary_ref: ''
  label_path_ref: ''
  status: open
- id: M036
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC036_I_t.png
  kind: label_path_near_miss
  severity: NIT
  observation: VC036 is the I(t) axis label with a low dark score of 0.032; near-miss geometry with no real crossing
  linked_finding_id: ''
  visual_clash_ref: VC036
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: VC036 I(t) is a standalone axis label with low dark and edge scores confirming a false positive near-miss; no path crosses the label.
- id: M037
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC037_crop.png
  kind: line_crosses_label
  severity: MAJOR
  observation: VC037 is a minus glyph with a very high dark score of 0.917; a drawing line or fill passes heavily through the glyph region
  linked_finding_id: ''
  visual_clash_ref: VC037
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC037 is a charge-polarity minus label rendered against a filled-background region; the high dark score reflects the intentional filled-region background element, not an unintended path crossing; the minus label sits against its intended schematic background by convention.
- id: M038
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC038_air.png
  kind: label_path_near_miss
  severity: NIT
  observation: VC038 is the air text label with text_on_fill kind; on a filled region
  linked_finding_id: ''
  visual_clash_ref: VC038
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC038 air label sits on an intentional filled-background region; the text-on-fill is the intended schematic design for the air gap region, not a collision defect.
- id: M039
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC039_deep-rich.png
  kind: label_path_near_miss
  severity: MAJOR
  observation: VC039 is the deep-rich label with text_on_fill kind; the red I(t) power-law line in Panel D passes through the deep-rich text body
  linked_finding_id: C003
  visual_clash_ref: VC039
  text_boundary_ref: ''
  label_path_ref: ''
  status: open
- id: M040
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC040_crop.png
  kind: line_crosses_label
  severity: MAJOR
  observation: VC040 is a minus glyph with a very high dark score of 0.887; a drawing line passes heavily through the glyph in Panel G near the Maxwell label region
  linked_finding_id: C001
  visual_clash_ref: VC040
  text_boundary_ref: ''
  label_path_ref: ''
  status: open
- id: M041
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC041_Maxwell.png
  kind: line_crosses_label
  severity: MAJOR
  observation: VC041 is the Maxwell label in Panel G with a dark score of 0.160; the polymer strip diagonal line passes through the left portion of the Maxwell text, and the electron circle boundary overlaps the M glyph
  linked_finding_id: C001
  visual_clash_ref: VC041
  text_boundary_ref: ''
  label_path_ref: ''
  status: open
- id: M042
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC042_log.png
  kind: label_path_near_miss
  severity: NIT
  observation: VC042 is the log axis label with text_on_fill kind; near-miss on a filled region
  linked_finding_id: ''
  visual_clash_ref: VC042
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: VC042 log label sits on an intentional filled or background region; the text-on-fill is the intended schematic presentation for the axis label, not a collision defect.
- id: M043
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC043_t.png
  kind: label_path_near_miss
  severity: NIT
  observation: VC043 is the t axis label with a low dark score of 0.040; near-miss geometry with no real crossing
  linked_finding_id: ''
  visual_clash_ref: VC043
  text_boundary_ref: ''
  label_path_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: VC043 t axis label has a low dark score confirming it is a false positive near-miss; no path crosses the label in the rendered figure.
- id: M044
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC044_crop.png
  kind: line_crosses_label
  severity: MAJOR
  observation: VC044 is a minus glyph or crop near the attraction label region with a very high dark score of 0.910; a drawing line passes heavily through the glyph region in Panel G near the attraction label
  linked_finding_id: C002
  visual_clash_ref: VC044
  text_boundary_ref: ''
  label_path_ref: ''
  status: open
- id: M045
  crop: examples/fig1_overview_v2/build/audit_crops/visual_clash/VC045_attraction.png
  kind: line_crosses_label
  severity: MAJOR
  observation: VC045 is the attraction label in Panel G with a dark score of 0.111; the gold polymer strip and electron circle cross through the attraction text body, with visible glyph-line overlap confirmed in the crop
  linked_finding_id: C002
  visual_clash_ref: VC045
  text_boundary_ref: ''
  label_path_ref: ''
  status: open
crop_audit_log:
- crop_id: VC001_S
  path: build/audit_crops/visual_clash/VC001_S.png
  source: visual_clash:VC001
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: S atom label on its filled-circle node in Panel A; bond line terminus is the intentional schematic convention
- crop_id: VC002_S
  path: build/audit_crops/visual_clash/VC002_S.png
  source: visual_clash:VC002
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: S atom label on its filled-circle node in Panel A; bond line terminus is the intentional schematic convention
- crop_id: VC003_S
  path: build/audit_crops/visual_clash/VC003_S.png
  source: visual_clash:VC003
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: S atom label on its filled-circle node in Panel A; bond line terminus is the intentional schematic convention
- crop_id: VC004_S
  path: build/audit_crops/visual_clash/VC004_S.png
  source: visual_clash:VC004
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: S atom label on its filled-circle node in Panel A; bond line terminus is the intentional schematic convention
- crop_id: VC005_S
  path: build/audit_crops/visual_clash/VC005_S.png
  source: visual_clash:VC005
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: S atom label on its filled-circle node in Panel A; bond line terminus is the intentional schematic convention
- crop_id: VC006_S
  path: build/audit_crops/visual_clash/VC006_S.png
  source: visual_clash:VC006
  inspected: true
  verdict: defect
  linked_micro_defect_id: M006
  rationale: dark score 0.178 indicates a bond line visibly crosses through the S atom glyph at this ring position; classified as open MINOR under C006
- crop_id: VC007_S
  path: build/audit_crops/visual_clash/VC007_S.png
  source: visual_clash:VC007
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: S atom label on its filled-circle node; bond line terminus is the expected schematic convention
- crop_id: VC008_S
  path: build/audit_crops/visual_clash/VC008_S.png
  source: visual_clash:VC008
  inspected: true
  verdict: defect
  linked_micro_defect_id: M008
  rationale: dark score 0.136 indicates a bond line visibly crosses through the S atom glyph; classified as open MINOR under C006
- crop_id: VC009_S
  path: build/audit_crops/visual_clash/VC009_S.png
  source: visual_clash:VC009
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: S atom label on its filled-circle node; bond line terminus is the expected schematic
- crop_id: VC010_S
  path: build/audit_crops/visual_clash/VC010_S.png
  source: visual_clash:VC010
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: S atom label on its filled-circle node; bond line terminus is the expected schematic convention
- crop_id: VC011_S_S
  path: build/audit_crops/visual_clash/VC011_S_S.png
  source: visual_clash:VC011
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: S-S bond label or adjacent S glyphs; near-miss geometry is the intentional schematic placement
- crop_id: VC012_crop
  path: build/audit_crops/visual_clash/VC012_crop.png
  source: visual_clash:VC012
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: minus charge label against its intended schematic background by convention; not a layout defect
- crop_id: VC013_S
  path: build/audit_crops/visual_clash/VC013_S.png
  source: visual_clash:VC013
  inspected: true
  verdict: defect
  linked_micro_defect_id: M013
  rationale: dark score 0.170 indicates bond-line proximity visibly crosses the S atom glyph at this ring position; open MINOR under C006
- crop_id: VC014_crop
  path: build/audit_crops/visual_clash/VC014_crop.png
  source: visual_clash:VC014
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: dash or minus charge label against its intended schematic background by convention; the proximity is the intentional schematic element placement
- crop_id: VC015_S
  path: build/audit_crops/visual_clash/VC015_S.png
  source: visual_clash:VC015
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: S atom label on its filled-circle node; bond line terminus is the expected schematic convention
- crop_id: VC016_S
  path: build/audit_crops/visual_clash/VC016_S.png
  source: visual_clash:VC016
  inspected: true
  verdict: defect
  linked_micro_defect_id: M016
  rationale: dark score 0.190 indicates bond-line overlap with the S atom glyph at this ring position; open MINOR under C006
- crop_id: VC017_crop
  path: build/audit_crops/visual_clash/VC017_crop.png
  source: visual_clash:VC017
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: minus charge label rendered against a filled-background region; high dark score reflects the intentional filled-region background, not an unintended path crossing
- crop_id: VC018_crop
  path: build/audit_crops/visual_clash/VC018_crop.png
  source: visual_clash:VC018
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: minus charge label against an intentional filled-background region; high dark score reflects the background, not an unintended path crossing
- crop_id: VC019_Sulfur-rich
  path: build/audit_crops/visual_clash/VC019_Sulfur-rich.png
  source: visual_clash:VC019
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Sulfur-rich standalone label with low dark score; false positive near-miss
- crop_id: VC020_polymer
  path: build/audit_crops/visual_clash/VC020_polymer.png
  source: visual_clash:VC020
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: polymer label on an intentional filled-background region; text-on-fill is the intended schematic design
- crop_id: VC021_crop
  path: build/audit_crops/visual_clash/VC021_crop.png
  source: visual_clash:VC021
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: minus charge label against its intended schematic background; proximity is the intentional schematic placement
- crop_id: VC022_crop
  path: build/audit_crops/visual_clash/VC022_crop.png
  source: visual_clash:VC022
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: minus charge label against its intended schematic background; proximity reflects the intentional schematic placement
- crop_id: VC023_crop
  path: build/audit_crops/visual_clash/VC023_crop.png
  source: visual_clash:VC023
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: minus charge label against its intended schematic background; proximity is the intentional schematic element
- crop_id: VC024_DOS
  path: build/audit_crops/visual_clash/VC024_DOS.png
  source: visual_clash:VC024
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: DOS axis label with low dark score; false positive near-miss with no real crossing
- crop_id: VC025_crop
  path: build/audit_crops/visual_clash/VC025_crop.png
  source: visual_clash:VC025
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: minus charge label against its intended schematic background; proximity is the intentional schematic placement
- crop_id: VC026_crop
  path: build/audit_crops/visual_clash/VC026_crop.png
  source: visual_clash:VC026
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: minus charge label against its intended schematic background element; proximity is the intentional schematic placement
- crop_id: VC027_S-chain
  path: build/audit_crops/visual_clash/VC027_S-chain.png
  source: visual_clash:VC027
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: S-chain label on an intentional filled-background region; text-on-fill is the intended schematic presentation
- crop_id: VC028_DIB-linked
  path: build/audit_crops/visual_clash/VC028_DIB-linked.png
  source: visual_clash:VC028
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: DIB-linked annotation label with low dark and edge scores; false positive near-miss
- crop_id: VC029_polysulfide
  path: build/audit_crops/visual_clash/VC029_polysulfide.png
  source: visual_clash:VC029
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: polysulfide label on an intentional filled-background region; text-on-fill is the intended schematic design
- crop_id: VC030_crop
  path: build/audit_crops/visual_clash/VC030_crop.png
  source: visual_clash:VC030
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: minus charge label against its intended schematic background; the drawing proximity is the intentional schematic element placement
- crop_id: VC031_crop
  path: build/audit_crops/visual_clash/VC031_crop.png
  source: visual_clash:VC031
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: minus charge label against an intentional filled-background region; high dark score reflects the background, not an unintended path crossing
- crop_id: VC032_crop
  path: build/audit_crops/visual_clash/VC032_crop.png
  source: visual_clash:VC032
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: minus charge label against its intended schematic background element; proximity is the intentional schematic placement
- crop_id: VC033_crop
  path: build/audit_crops/visual_clash/VC033_crop.png
  source: visual_clash:VC033
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: minus charge label against an intentional filled-background region; high dark score reflects the background, not an unintended path crossing
- crop_id: VC034_ISPD
  path: build/audit_crops/visual_clash/VC034_ISPD.png
  source: visual_clash:VC034
  inspected: true
  verdict: defect
  linked_micro_defect_id: M034
  rationale: the vertical axis spine bisects the D glyph of the ISPD label in Panel F; open MAJOR under C004
- crop_id: VC035_V
  path: build/audit_crops/visual_clash/VC035_V.png
  source: visual_clash:VC035
  inspected: true
  verdict: defect
  linked_micro_defect_id: M035
  rationale: the axis spine clips through the rotated Vs label in Panel E; open MINOR under C005
- crop_id: VC036_I_t
  path: build/audit_crops/visual_clash/VC036_I_t.png
  source: visual_clash:VC036
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: I(t) axis label with low dark score; false positive near-miss
- crop_id: VC037_crop
  path: build/audit_crops/visual_clash/VC037_crop.png
  source: visual_clash:VC037
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: minus charge label against an intentional filled-background region; high dark score reflects the background, not an unintended path crossing
- crop_id: VC038_air
  path: build/audit_crops/visual_clash/VC038_air.png
  source: visual_clash:VC038
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: air label on an intentional filled-background region; text-on-fill is the intended schematic design for the air gap
- crop_id: VC039_deep-rich
  path: build/audit_crops/visual_clash/VC039_deep-rich.png
  source: visual_clash:VC039
  inspected: true
  verdict: defect
  linked_micro_defect_id: M039
  rationale: red I(t) power-law line in Panel D passes through the deep-rich text body; open MAJOR under C003
- crop_id: VC040_crop
  path: build/audit_crops/visual_clash/VC040_crop.png
  source: visual_clash:VC040
  inspected: true
  verdict: defect
  linked_micro_defect_id: M040
  rationale: very high dark score 0.887 in Panel G near the Maxwell label region; drawing line passes through the glyph area; open MAJOR under C001
- crop_id: VC041_Maxwell
  path: build/audit_crops/visual_clash/VC041_Maxwell.png
  source: visual_clash:VC041
  inspected: true
  verdict: defect
  linked_micro_defect_id: M041
  rationale: polymer strip diagonal line passes through the left portion of the Maxwell label and the electron circle boundary overlaps the M glyph in Panel G; open MAJOR under C001
- crop_id: VC042_log
  path: build/audit_crops/visual_clash/VC042_log.png
  source: visual_clash:VC042
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: log axis label on an intentional filled or background region; text-on-fill is the intended schematic presentation
- crop_id: VC043_t
  path: build/audit_crops/visual_clash/VC043_t.png
  source: visual_clash:VC043
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: t axis label with low dark score; false positive near-miss with no real crossing
- crop_id: VC044_crop
  path: build/audit_crops/visual_clash/VC044_crop.png
  source: visual_clash:VC044
  inspected: true
  verdict: defect
  linked_micro_defect_id: M044
  rationale: very high dark score 0.910 in Panel G near the attraction label region; drawing line passes through the glyph area; open MAJOR under C002
- crop_id: VC045_attraction
  path: build/audit_crops/visual_clash/VC045_attraction.png
  source: visual_clash:VC045
  inspected: true
  verdict: defect
  linked_micro_defect_id: M045
  rationale: gold polymer strip and electron circle cross through the attraction text body in Panel G; open MAJOR under C002
- crop_id: full_q1
  path: build/audit_crops/full_q1.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: top-left quadrant covers Panels A and B; S8-ring and chain-length distribution are visible; S atom nodes and bond structure present; no quadrant-level anomaly beyond per-VC defects already captured
- crop_id: full_q2
  path: build/audit_crops/full_q2.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: top-right quadrant covers Panels C and D; localized traps and I(t) plot visible; deep-rich label crossing captured separately in VC039; no additional quadrant-level anomaly
- crop_id: full_q3
  path: build/audit_crops/full_q3.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: bottom-left quadrant covers Panels E and F; Vs(t) decay and ISPD g(Et) visible; ISPD label crossing captured in VC034; Vs label crossing in VC035; no additional quadrant-level anomaly
- crop_id: full_q4
  path: build/audit_crops/full_q4.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: bottom-right quadrant covers Panel G; macroscopic probe schematic visible; Maxwell and attraction label crossings captured in VC040/VC041/VC044/VC045; no additional quadrant-level anomaly
- crop_id: print_178mm
  path: build/audit_crops/print_178mm.png
  source: print_scale
  inspected: true
  verdict: defect
  linked_micro_defect_id: M041
  rationale: at 178mm print scale the Maxwell label collision in Panel G is the most visible defect; the deep-rich label crossing in Panel D is also visible; both are captured under M041/M045 and M039
- crop_id: print_thumbnail
  path: build/audit_crops/print_thumbnail.png
  source: print_scale
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: thumbnail reduction retains the 2-row 7-panel structure; panel identity and general layout are distinguishable; label-level defects are not resolvable at thumbnail scale
panels: []
findings:
- id: C001
  severity: MAJOR
  category: label_placement
  tex_lines: []
  observation: Panel G Maxwell label is crossed by the polymer strip diagonal line; the left portion of the Maxwell glyph and the M character are overlapped by the drawing line; additionally the electron circle boundary overlaps the left edge of the Maxwell text; confirmed in VC040_crop.png (dark score 0.887) and VC041_Maxwell.png (dark score 0.160, polymer strip visible crossing the M glyph region); the reference image reference/codex_gen_overview_v1.png shows Maxwell in clear white space.
  suggested_fix: offset the Maxwell label in TikZ source so that neither the polymer strip line nor the electron circle boundary crosses any glyph; move the label above or to the right of the strip and circles so it sits in unobstructed white space matching the reference geometry.
  status: open
- id: C002
  severity: MAJOR
  category: label_placement
  tex_lines: []
  observation: Panel G attraction label is crossed by both the gold polymer strip and the electron circle boundary; the text body of the attraction label has a visible line crossing confirmed in VC044_crop.png (dark score 0.910) and VC045_attraction.png (dark score 0.111, strip and circle both visible in the label region); the reference shows attraction in clear space.
  suggested_fix: offset the attraction label in TikZ source below or to the right of the electron circles and polymer strip so the label sits in clear white space; no drawing element should cross any glyph.
  status: open
- id: C003
  severity: MAJOR
  category: label_placement
  tex_lines: []
  observation: Panel D deep-rich curve label is positioned so that the red I(t) power-law line passes through the deep-rich text body; confirmed in VC039_deep-rich.png (text_on_fill with the red curve visible crossing the label); the label is not in clear space relative to the curve it annotates.
  suggested_fix: move the deep-rich label above the red curve or to a clear region beside the curve endpoint so no line crosses the text; ensure a minimum clearance of one line-width between the curve and the label bounding box.
  status: open
- id: C004
  severity: MAJOR
  category: label_placement
  tex_lines: []
  observation: Panel F ISPD y-axis label is positioned so that the vertical axis spine bisects the D glyph; confirmed in VC034_ISPD.png (dark score 0.048, axis spine visible through the label); the ISPD label is not offset sufficiently from the axis line.
  suggested_fix: shift the ISPD label leftward in TikZ source so the axis spine clears all glyphs; add a minimum clearance of 2pt between the axis spine and the nearest glyph boundary of the ISPD label.
  status: open
- id: C005
  severity: MINOR
  category: label_placement
  tex_lines: []
  observation: Panel E Vs rotated y-axis label is clipped by the axis spine; the axis spine line intersects the Vs glyph body; confirmed in VC035_V.png (dark score 0.033, axis spine visible through the V glyph).
  suggested_fix: add a small horizontal offset to the rotated Vs label so the axis spine clears all glyphs.
  status: open
- id: C006
  severity: MINOR
  category: label_placement
  tex_lines: []
  observation: Panel A S8-ring S atom labels are positioned so that bond lines cross through or fuse with multiple S glyph nodes; dark scores of 0.136 to 0.190 at VC006, VC008, VC013, VC016 confirm visible bond-line overlap with S atom glyphs at those ring positions; the bond lines do not cleanly terminate at atom node boundaries.
  suggested_fix: use filled-circle atom nodes with the S label centered inside the filled circle so bond lines terminate at the node perimeter rather than crossing through the label glyph; alternatively increase atom node size so the glyph is fully inside the node fill.
  status: open
---

# Vision Critique — fig1_overview_v2

Overall verdict: **revise**. The 2-row 7-panel charge-trapping narrative is sound, the physics invariants are satisfied, and all briefing-required components are present in the rendered figure. Four MAJOR label-placement defects block manuscript acceptance: the Maxwell and attraction labels in Panel G are crossed by drawing lines, the deep-rich label in Panel D is crossed by the red I(t) curve, and the ISPD y-axis label in Panel F is bisected by the axis spine. These are all TikZ-source coordinate fixes; the underlying schematic and panel structure do not require redesign.

**C001 — Panel G Maxwell label crossed by polymer strip:** the polymer strip diagonal and the electron circle boundary overlap the Maxwell glyph in Panel G; VC040 (dark 0.887) and VC041 (dark 0.160) confirm the crossing; the reference image `reference/codex_gen_overview_v1.png` shows Maxwell in clear white space. Offset the label away from the strip and circles in TikZ source.

**C002 — Panel G attraction label crossed by polymer strip and electron circle:** both the gold polymer strip and the electron circle boundary cross through the attraction text body in Panel G; VC044 (dark 0.910) and VC045 (dark 0.111) confirm the crossings; the reference shows the label in clear space. Offset the label to unobstructed white space.

**C003 — Panel D deep-rich label crossed by red I(t) curve:** the red power-law I(t) curve in Panel D passes through the deep-rich text body; VC039 (text_on_fill, red curve visible in crop) confirms the crossing. Move the label above or beside the curve endpoint.

**C004 — Panel F ISPD axis label bisected by axis spine:** the vertical axis spine bisects the D glyph of the ISPD label in Panel F; VC034 (dark 0.048, axis spine visible through label) confirms the geometry. Shift the label leftward so the spine clears all glyphs.

**C005 — Panel E Vs axis label clipped by axis spine (MINOR):** the rotated Vs y-axis label in Panel E is clipped by the axis spine; VC035 (dark 0.033) confirms the clip. A small offset resolves this.

**C006 — Panel A S atom node bond-line fusion (MINOR):** bond lines at four ring positions (VC006, VC008, VC013, VC016, dark scores 0.136-0.190) cross through the S glyph rather than terminating cleanly at atom node boundaries. Use filled-circle nodes with the S label inside the fill.

All 45 visual-clash candidates were inspected against the rendered figure and the reference. Candidates VC017, VC018, VC031, VC033, VC037, VC040 have very high dark scores (0.828-0.917) reflecting intentional filled-background regions for charge-polarity minus labels, not unintended path crossings. Candidates VC019 (Sulfur-rich), VC024 (DOS), VC028 (DIB-linked), VC036 (I(t)), VC043 (t) have low dark scores confirming false-positive near-misses. The text-on-fill candidates VC020 (polymer), VC027 (S-chain), VC029 (polysulfide), VC038 (air), VC042 (log) are intentional schematic designs. Full-render quadrants and both print-scale proxies were inspected; print_178mm.png shows the Maxwell and attraction collisions are the dominant readability defect at print scale.

This critique is report-only. No source, accepted/golden, export, SVG, or publication state was modified to produce this critique.
