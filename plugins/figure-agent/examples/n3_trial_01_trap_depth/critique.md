---
schema: figure-agent.critique.v1.10
fixture: n3_trial_01_trap_depth
generated_at: 2026-05-29T16:00:00Z
generator: critique_brief.py
generator_version: sha256:f7b71b470a4bab2b0a486edb039a45f6187b3782e90db9cdd1e78b3cc05077e7
rubric_version: figure-agent.critique-rubric.v1.10
critique_input_hash: sha256:23bfe8cce73070527ef5b28e6ba5860f71da11834e32ef36be74da7ccd50fe5c
verdict: revise
audit_enumeration:
  structural_completeness:
    components:
      - component: "Row 1 Experiment log-log discharge plot"
        mount_support: "N/A"
        rationale: "blue power-law line plus dashed Debye reference in one log-log axes"
        connections: "axes ticks 10^0..10^4 horizontal, 10^-3..10^1 vertical; line annotations attached"
      - component: "Row 2 Mathematical interpretation"
        mount_support: "N/A"
        rationale: "governing equation tau_d = tau_0 exp(E_t/k_B T) plus n -> tau_d -> g(E_t) flow"
        connections: "two flow arrows connect n, tau_d, g(E_t); equation centered above chain"
      - component: "Row 3 Molecular origin polymer chain plus origin sub-boxes"
        mount_support: "N/A"
        rationale: "sulfur-rich backbone with chemical and physical origin captions"
        connections: "wavy backbone above two captioned amber/violet origin boxes"
      - component: "Convergence connector"
        mount_support: "N/A"
        rationale: "vertical green box bridging the three left rows to the right panel"
        connections: "rotated Convergence text; right-pointing arrow into band diagram"
      - component: "Right band diagram CB/VB with trap levels and g(E_t) side curves"
        mount_support: "N/A"
        rationale: "energy-axis synthesis panel; CB top, VB bottom, E_t reference, paired g(E_t) lobes"
        connections: "Energy vertical axis; dashed E_t line; amber shallow lobe upper, violet deep lobe lower"
    missing_from_reference:
      - element: "explicit sulfur (S) sites on the Row 3 polymer backbone"
        status: incomplete
        rationale: "render shows a plain sine wave; reference shows an explicit zigzag chain with S side groups"
      - element: "grouped shallow/deep trap tick segments inside the band gap"
        status: incomplete
        rationale: "reference shows two clear grouped dashed trap levels; render shows ~2 detached markers near the energy axis"
  label_target_matching:
    - label: "Experiment"
      nearest_object: "Row 1 title"
      intended_target: "Row 1 identity"
      matches: true
      proposed_fix: ""
    - label: "Discharge power-law vs. time (log-log)"
      nearest_object: "Row 1 subtitle"
      intended_target: "Row 1 plot description"
      matches: true
      proposed_fix: "shorten or reflow; subtitle currently overruns into the plot y-axis (VC001/VC002)"
    - label: "Power-law / I = I_0 t^-n"
      nearest_object: "blue power-law line"
      intended_target: "power-law curve"
      matches: true
      proposed_fix: ""
    - label: "Debye reference / I = I_0 e^-t/tau"
      nearest_object: "dashed gray curve"
      intended_target: "Debye reference curve"
      matches: true
      proposed_fix: ""
    - label: "Shallow traps"
      nearest_object: "amber band region near CB"
      intended_target: "shallow trap population"
      matches: true
      proposed_fix: ""
    - label: "Deep traps"
      nearest_object: "violet band region near VB"
      intended_target: "deep trap population"
      matches: true
      proposed_fix: ""
  physical_plausibility:
    - check: direction_orientation
      finding: "CB drawn above VB on the energy axis; Energy arrow points up"
      verdict: convention_acceptable
    - check: spatial_proximity
      finding: "trap-level markers render detached at the left of the gap rather than grouped near CB/VB"
      verdict: structural_defect
    - check: floating_components
      finding: "stray blue dot floats in Row 2 and an amber glyph floats at the far-left of Row 3"
      verdict: structural_defect
    - check: material_distinction
      finding: "shallow vs deep populations distinguished by amber vs violet g(E_t) lobes"
      verdict: convention_acceptable
  conceptual_completeness:
    - element: "sulfur sites on polymer backbone"
      reference: provided_reference
      severity: MAJOR
      proposed_action: add
    - element: "two grouped trap-level bands inside the gap"
      reference: provided_reference
      severity: MAJOR
      proposed_action: expand
    - element: "stray floating cues removed"
      reference: briefing
      severity: MINOR
      proposed_action: accept_simplification
quality_axes:
  message_storyline:
    verdict: pass
    confidence: high
    rationale: "the left-to-right evidence -> theory -> molecular -> unified narrative reads clearly in the current render"
    evidence: "visible three numbered rows and Convergence connector into the right band diagram"
    blocking_items: []
    recommended_action: none
  panel_role_coherence:
    verdict: pass
    confidence: high
    rationale: "each region carries a distinct narrative role in the rendered figure"
    evidence: "row1 result, row2 model, row3 mechanism, right-panel model are all present and ordered"
    panel_roles:
      - panel_id: "row1_experiment"
        role: result
        role_quality: clear
        rationale: "log-log discharge observation"
      - panel_id: "row2_math"
        role: model
        role_quality: clear
        rationale: "exponent to trap-depth mapping"
      - panel_id: "row3_molecular"
        role: mechanism
        role_quality: weak
        rationale: "polymer chain lacks the sulfur detail that carries the mechanism"
      - panel_id: "right_band_diagram"
        role: model
        role_quality: weak
        rationale: "trap-level populations render detached and sparse"
    blocking_items: []
    recommended_action: none
  subregion_integration:
    verdict: pass
    confidence: medium
    rationale: "left stack and right panel are bridged by the Convergence connector in the render"
    evidence: "visible green connector with right-pointing arrow linking both halves"
    blocking_items: []
    recommended_action: none
  component_fidelity:
    verdict: needs_human
    confidence: high
    rationale: "two components diverge from the reference: the polymer backbone and the band-gap trap levels"
    evidence: "render polymer chain is a plain sine; band trap markers detached near the energy axis"
    blocking_items:
      - "C001 - Row 3 polymer chain missing sulfur sites vs reference"
      - "C002 - band trap levels render detached and sparse"
    recommended_action: human_review
  scientific_plausibility:
    verdict: needs_human
    confidence: medium
    rationale: "band ordering is correct but the two trap populations are not clearly conveyed as grouped levels"
    evidence: "only ~2 trap markers visible against the specified 3 shallow + 2 deep"
    blocking_items:
      - "C002 - trap populations not clearly two grouped levels"
    recommended_action: human_review
  composition_layout:
    verdict: needs_patch
    confidence: high
    rationale: "stray floating cues and a subtitle that overruns the plot axis hurt layout cleanliness"
    evidence: "visible stray blue dot in Row 2 and subtitle crossing the y-axis in Row 1"
    blocking_items:
      - "C003 - stray floating blue dot in Row 2"
      - "C004 - Row 1 subtitle overruns into plot y-axis"
    recommended_action: patch
  label_annotation_semantics:
    verdict: pass
    confidence: medium
    rationale: "labels bind to their intended targets; the only placement overlap is tracked under composition_layout"
    evidence: "Shallow/Deep, Power-law, Debye, and equation labels all identify the correct objects"
    blocking_items: []
    recommended_action: none
  journal_polish:
    verdict: needs_human
    confidence: medium
    rationale: "trap-level legibility at reduced scale needs a human polish/source decision"
    evidence: "print_thumbnail print-scale image shows band-gap trap markers becoming unresolvable"
    blocking_items: []
    recommended_action: human_review
  reference_fidelity:
    verdict: needs_human
    confidence: high
    rationale: "render diverges from reference on polymer-chain detail and trap-level grouping"
    evidence: "reference/codex_gen_v1.png shows explicit S sites and grouped trap dashes absent in the render"
    blocking_items:
      - "C001 - polymer chain sulfur fidelity"
      - "C002 - trap-level grouping fidelity"
    recommended_action: human_review
  publication_readiness:
    verdict: needs_human
    confidence: high
    rationale: "structural and fidelity gaps must be resolved by a human before this is manuscript-ready"
    evidence: "component_fidelity and reference_fidelity both need human review"
    blocking_items: []
    recommended_action: human_review
top_tier_audit:
  first_glance_message:
    verdict: pass
    finding: "a reader grasps the converging-evidence-to-unified-trap-picture message within ~10 seconds"
    concrete_fix: "no change; the headline message survives a quick glance"
    blocks_high_impact: false
  target_journal_fit:
    verdict: weak
    finding: "schematic reads as a solid draft but the trap-level rendering is below top-tier band-diagram polish"
    concrete_fix: "tighten band-gap trap-level rendering before claiming top-tier fit"
    blocks_high_impact: false
  novelty_claim_support:
    verdict: pass
    finding: "the visual supports the central unified-trap-depth claim"
    concrete_fix: "no change"
    blocks_high_impact: false
  figure_caption_coupling:
    verdict: pass
    finding: "in-figure titles carry the explanatory burden a caption would otherwise need"
    concrete_fix: "no change"
    blocks_high_impact: false
  visual_economy:
    verdict: weak
    finding: "stray floating cues add ink that does not encode meaning"
    concrete_fix: "remove the stray Row 2 dot and far-left Row 3 glyph"
    blocks_high_impact: false
  cross_panel_semantic_grammar:
    verdict: pass
    finding: "amber=shallow, violet=deep color grammar is consistent across band and g(E_t) lobes"
    concrete_fix: "no change"
    blocks_high_impact: false
  reader_misinterpretation_risk:
    verdict: weak
    finding: "detached trap markers could be misread as energy levels outside the band"
    concrete_fix: "place trap levels inside the gap as grouped ticks"
    blocks_high_impact: false
  reduction_print_readability:
    verdict: weak
    finding: "trap-level detail does not survive thumbnail reduction"
    concrete_fix: "increase trap-level stroke/size for print survival"
    blocks_high_impact: false
  accessibility_color_robustness:
    verdict: pass
    finding: "amber vs violet remain distinguishable and labels are redundant to color"
    concrete_fix: "no change"
    blocks_high_impact: false
  aesthetic_coherence:
    verdict: weak
    finding: "line-weight and detail level are uneven between the polished g(E_t) lobes and the sparse band interior"
    concrete_fix: "normalize band-interior detail to match the side curves"
    blocks_high_impact: false
editorial_art_direction:
  hero_focus:
    verdict: weak
    evidence: "in the current render the right band diagram is the intended hero but reads emptier than the left stack"
    rationale: "the synthesis panel should dominate for a unified-picture figure"
    concrete_fix: "strengthen band-gap trap rendering so the hero panel carries weight"
    blocks_high_impact: false
  narrative_choreography:
    verdict: pass
    evidence: "the rendered numbered rows and connector choreograph a clear reading path"
    rationale: "ordered flow supports comprehension"
    concrete_fix: "no change"
    blocks_high_impact: false
  illustration_readiness:
    verdict: weak
    evidence: "the rendered polymer chain is schematic-plain versus the detailed reference chain"
    rationale: "illustration detail is below reference-class for the molecular row"
    concrete_fix: "add sulfur-site detail to the backbone"
    blocks_high_impact: false
  abstraction_consistency:
    verdict: weak
    evidence: "the render mixes detailed side curves with an under-detailed band interior"
    rationale: "abstraction level should be consistent across the figure"
    concrete_fix: "match band-interior abstraction to the side curves"
    blocks_high_impact: false
  reference_class_fit:
    verdict: weak
    evidence: "render falls short of the reference image on chain and trap-level detail"
    rationale: "reference class expects explicit sulfur and grouped trap levels"
    concrete_fix: "close the two reference-fidelity gaps"
    blocks_high_impact: false
  visual_identity:
    verdict: pass
    evidence: "consistent teal-framed rows and amber/violet trap palette across the render"
    rationale: "visual identity is coherent"
    concrete_fix: "no change"
    blocks_high_impact: false
  claim_payload_fit:
    verdict: pass
    evidence: "the rendered figure delivers the unified-trap-depth payload"
    rationale: "claim and visual align"
    concrete_fix: "no change"
    blocks_high_impact: false
  aesthetic_risk:
    verdict: weak
    evidence: "stray floating cues in the render are a low aesthetic risk but read as noise"
    rationale: "noise lowers perceived polish"
    concrete_fix: "remove stray cues"
    blocks_high_impact: false
  tikz_vs_svg_polish_trigger:
    verdict: pass
    evidence: "the render has open semantic/structural gaps (chain, trap levels) that must change in TikZ"
    rationale: "SVG polish would freeze unresolved semantic defects"
    concrete_fix: "continue TikZ source fixes (C001-C004) before any SVG polish"
    blocks_high_impact: false
    recommended_path: continue_tikz
  human_art_direction_gate:
    verdict: pass
    evidence: "no taste-only gate beyond the normal structural review is required by the render"
    rationale: "remaining decisions are structural, handled by quality-axes human review"
    concrete_fix: "no change"
    blocks_high_impact: false
journal_grade_assessment:
  schema: figure-agent.journal-grade-assessment.v1
  scoring_mode: fresh_reaudit
  assessed_artifact_hash: sha256:23bfe8cce73070527ef5b28e6ba5860f71da11834e32ef36be74da7ccd50fe5c
  benchmark_level: draft
  confidence: medium
  blockers: []
  regression_detected: false
  regressions: []
  score_is_gateable: false
  next_quality_bottleneck: component_fidelity
  rationale: "current render is a solid draft whose next bottleneck is component fidelity: polymer-chain sulfur detail and band-gap trap-level rendering"
micro_defects:
  - id: M001
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC001_time.png
    kind: line_crosses_label
    severity: MINOR
    observation: "the plot vertical y-axis line crosses through the word 'time' of the Row 1 subtitle, which overruns rightward into the axis"
    linked_finding_id: "C004"
    visual_clash_ref: "VC001"
    text_boundary_ref: ""
    label_path_ref: ""
    status: open
  - id: M002
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC002_log-log.png
    kind: line_crosses_label
    severity: MINOR
    observation: "the dashed Debye reference curve crosses through the '(log-log)' subtitle text near the plot top-left"
    linked_finding_id: "C004"
    visual_clash_ref: "VC002"
    text_boundary_ref: ""
    label_path_ref: ""
    status: open
  - id: M003
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC003_crop.png
    kind: label_path_near_miss
    severity: NIT
    observation: "VC003 is the right parenthesis of the (log-log) label with no path crossing it"
    linked_finding_id: ""
    visual_clash_ref: "VC003"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "VC003 is an isolated closing parenthesis glyph with no path through it; a clear false positive near-miss flag."
  - id: M004
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC004_CB.png
    kind: label_glyph_overlaps_internal_drawing
    severity: NIT
    observation: "VC004 dashed E_t reference line passes vertically between the C and B glyphs of the CB band label"
    linked_finding_id: ""
    visual_clash_ref: "VC004"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: convention_acceptable
    accept_simplification_rationale: "VC004 dashed E_t reference line runs between the CB glyphs by band-diagram convention and is acceptable, not a real collision."
  - id: M005
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC005_3.png
    kind: label_glyph_overlaps_internal_drawing
    severity: NIT
    observation: "VC005 is the white numeral 3 centered on its filled teal step circle"
    linked_finding_id: ""
    visual_clash_ref: "VC005"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: intentional_schematic
    accept_simplification_rationale: "VC005 is the intentional step-number badge glyph on its own filled circle, not a path-on-text clash."
  - id: M006
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC006_crop.png
    kind: label_path_near_miss
    severity: NIT
    observation: "VC006 is a bare flow-arrow stroke with empty detector text and no nearby label"
    linked_finding_id: ""
    visual_clash_ref: "VC006"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "VC006 is an arrow-tail stroke with no label glyph; a false positive with nothing to collide with."
  - id: M007
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC007_d.png
    kind: label_path_near_miss
    severity: NIT
    observation: "VC007 is the subscript d of tau_d sitting clear of the flow-arrow tip"
    linked_finding_id: ""
    visual_clash_ref: "VC007"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "VC007 shows the tau_d subscript as a separate glyph clear of the arrow; not an overlap, a false positive."
  - id: M008
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC008_g_E.png
    kind: label_path_near_miss
    severity: NIT
    observation: "VC008 shows the flow arrow pointing toward the g(E_t) label which is its intended target"
    linked_finding_id: ""
    visual_clash_ref: "VC008"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: convention_acceptable
    accept_simplification_rationale: "VC008 is an arrow pointing to its intended g(E_t) target label, an acceptable flow convention and not a crossing defect."
  - id: M009
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC009_crop.png
    kind: label_path_near_miss
    severity: NIT
    observation: "VC009 is the closing parenthesis of g(E_t) with no path through it"
    linked_finding_id: ""
    visual_clash_ref: "VC009"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "VC009 is an isolated parenthesis glyph, a false positive with no path crossing it."
  - id: M010
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC010_Sulfur-rich.png
    kind: label_path_near_miss
    severity: NIT
    observation: "VC010 'Sulfur-rich polymer' subtitle sits clear of the rounded row-frame corner"
    linked_finding_id: ""
    visual_clash_ref: "VC010"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: convention_acceptable
    accept_simplification_rationale: "VC010 subtitle keeps whitespace to the row-frame corner; an acceptable layout, not a clash with the frame."
  - id: M011
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC011_E.png
    kind: label_path_near_miss
    severity: NIT
    observation: "VC011 is the E_t axis label of the shallow g(E_t) side curve standing alone"
    linked_finding_id: ""
    visual_clash_ref: "VC011"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "VC011 is a standalone E_t axis label; not a path-on-text collision, a false positive."
  - id: M012
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC012_Et.png
    kind: label_path_near_miss
    severity: NIT
    observation: "VC012 rotated E_t side-axis label sits just outside the teal band-diagram box edge with a gap"
    linked_finding_id: ""
    visual_clash_ref: "VC012"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: convention_acceptable
    accept_simplification_rationale: "VC012 rotated E_t axis label sits just outside the box edge with a visible gap; acceptable axis placement, not an overlap."
  - id: M013
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC013_T.png
    kind: label_path_near_miss
    severity: NIT
    observation: "VC013 is the T of k_B T inside the governing equation under its own fraction bar"
    linked_finding_id: ""
    visual_clash_ref: "VC013"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "VC013 is equation-internal text under its fraction rule; not a stray path crossing, a false positive."
  - id: M014
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC014_crop.png
    kind: label_path_near_miss
    severity: NIT
    observation: "VC014 is a bare arrow-tail stroke with empty detector text and no nearby label"
    linked_finding_id: ""
    visual_clash_ref: "VC014"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "VC014 is an arrow-tail stroke with no label glyph; a false positive with nothing to collide with."
  - id: M015
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC015_d.png
    kind: label_path_near_miss
    severity: NIT
    observation: "VC015 is the subscript d of tau_d clear of the chain arrow"
    linked_finding_id: ""
    visual_clash_ref: "VC015"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "VC015 shows the tau_d subscript as a separate glyph clear of the arrow; not a collision, a false positive."
  - id: M016
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC016_τ.png
    kind: label_path_near_miss
    severity: NIT
    observation: "VC016 is the tau of tau_d on the light row-frame fill with ample contrast"
    linked_finding_id: ""
    visual_clash_ref: "VC016"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: convention_acceptable
    accept_simplification_rationale: "VC016 tau glyph sits on the light row-frame fill background with contrast; acceptable, not a clash."
  - id: M017
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC017_0.png
    kind: label_path_near_miss
    severity: NIT
    observation: "VC017 is the subscript 0 of tau_0 within the equation, clear of the fraction rule"
    linked_finding_id: ""
    visual_clash_ref: "VC017"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "VC017 is equation-internal subscript text clear of the fraction rule; not a defect, a false positive."
  - id: M018
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC018_2.png
    kind: label_glyph_overlaps_internal_drawing
    severity: NIT
    observation: "VC018 is the white numeral 2 on its filled teal step circle"
    linked_finding_id: ""
    visual_clash_ref: "VC018"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: intentional_schematic
    accept_simplification_rationale: "VC018 is the intentional step-number badge glyph on its own filled circle, not a text-on-path clash."
  - id: M019
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC019_Et.png
    kind: label_path_near_miss
    severity: NIT
    observation: "VC019 rotated E_t side-axis label of the deep g(E_t) curve sits just outside the teal box edge with a gap"
    linked_finding_id: ""
    visual_clash_ref: "VC019"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: convention_acceptable
    accept_simplification_rationale: "VC019 rotated E_t axis label sits just outside the box edge with a gap; acceptable axis placement, not an overlap."
  - id: M020
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC020_I.png
    kind: label_path_near_miss
    severity: NIT
    observation: "VC020 is the I of I=I_0 t^-n in the power-law annotation standing alone"
    linked_finding_id: ""
    visual_clash_ref: "VC020"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "VC020 is a standalone power-law label glyph; not a path crossing, a false positive."
  - id: M021
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC021_I.png
    kind: label_path_near_miss
    severity: NIT
    observation: "VC021 is the I of the Debye reference equation clear of the dashed curve"
    linked_finding_id: ""
    visual_clash_ref: "VC021"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "VC021 is a separate Debye-equation glyph clear of the dashed curve; not a collision, a false positive."
  - id: M022
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC022_VB.png
    kind: label_glyph_overlaps_internal_drawing
    severity: NIT
    observation: "VC022 dashed E_t reference line passes vertically between the V and B glyphs of the VB label"
    linked_finding_id: ""
    visual_clash_ref: "VC022"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: convention_acceptable
    accept_simplification_rationale: "VC022 dashed E_t line runs between the VB glyphs by band-diagram convention; acceptable, not a defect."
  - id: M023
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC023_S.png
    kind: floating_semantic_cue
    severity: MAJOR
    observation: "VC023 is an amber spiral/S glyph floating at the far-left margin of Row 3, detached from the polymer backbone and reading as a misplaced sulfur marker"
    linked_finding_id: "C001"
    visual_clash_ref: "VC023"
    text_boundary_ref: ""
    label_path_ref: ""
    status: open
  - id: M024
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC024_sulfur.png
    kind: label_path_near_miss
    severity: NIT
    observation: "VC024 'sulfur sites' text sits inside the chemical-origin caption box with margin"
    linked_finding_id: ""
    visual_clash_ref: "VC024"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "VC024 is caption-box body text with margin to the border; not a path-on-text clash, a false positive."
  - id: M025
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC025_polarizability.png
    kind: label_overflows_row_box
    severity: NIT
    observation: "VC025 '(polarizability,' wraps to the inner right edge of the chemical-origin box"
    linked_finding_id: ""
    visual_clash_ref: "VC025"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: convention_acceptable
    accept_simplification_rationale: "VC025 text reaches the box inner edge by its intended text-width wrap; acceptable, not an overflow defect."
  - id: M026
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/visual_clash/VC026_g_Et.png
    kind: label_path_near_miss
    severity: NIT
    observation: "VC026 is the g(E_t) axis label of the deep side curve standing clear"
    linked_finding_id: ""
    visual_clash_ref: "VC026"
    text_boundary_ref: ""
    label_path_ref: ""
    status: accept_simplification
    accept_simplification_reason: false_positive
    accept_simplification_rationale: "VC026 is a standalone deep-curve axis label; not a path-on-text collision, a false positive."
  - id: M027
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/full_q4.png
    kind: floating_semantic_cue
    severity: MAJOR
    observation: "band-diagram trap levels render as ~2 detached circle+line glyphs at the left of the gap near the Energy axis instead of grouped shallow/deep tick segments inside the gap"
    linked_finding_id: "C002"
    visual_clash_ref: ""
    text_boundary_ref: ""
    label_path_ref: ""
    status: open
  - id: M029
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: MINOR
    observation: "a stray blue filled circle floats in Row 2 below the n -> tau_d -> g(E_t) chain with no referent"
    linked_finding_id: "C003"
    visual_clash_ref: ""
    text_boundary_ref: ""
    label_path_ref: ""
    status: open
  - id: M030
    crop: examples/n3_trial_01_trap_depth/build/audit_crops/print_thumbnail.png
    kind: print_scale_unreadable
    severity: MINOR
    observation: "at thumbnail scale the band-gap trap levels and stray markers are not resolvable"
    linked_finding_id: "C002"
    visual_clash_ref: ""
    text_boundary_ref: ""
    label_path_ref: ""
    status: open
crop_audit_log:
  - crop_id: VC001_time
    path: build/audit_crops/visual_clash/VC001_time.png
    source: visual_clash:VC001
    inspected: true
    verdict: defect
    linked_micro_defect_id: "M001"
    rationale: "y-axis line crosses the word 'time'; subtitle overruns into the plot axis"
  - crop_id: VC002_log-log
    path: build/audit_crops/visual_clash/VC002_log-log.png
    source: visual_clash:VC002
    inspected: true
    verdict: defect
    linked_micro_defect_id: "M002"
    rationale: "dashed Debye curve crosses the (log-log) subtitle text"
  - crop_id: VC003_crop
    path: build/audit_crops/visual_clash/VC003_crop.png
    source: visual_clash:VC003
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "isolated parenthesis glyph; no path crossing"
  - crop_id: VC004_CB
    path: build/audit_crops/visual_clash/VC004_CB.png
    source: visual_clash:VC004
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "dashed E_t reference line between CB glyphs is band-diagram convention"
  - crop_id: VC005_3
    path: build/audit_crops/visual_clash/VC005_3.png
    source: visual_clash:VC005
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "intentional step-number badge on its filled circle"
  - crop_id: VC006_crop
    path: build/audit_crops/visual_clash/VC006_crop.png
    source: visual_clash:VC006
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "bare arrow-tail stroke with no label to collide"
  - crop_id: VC007_d
    path: build/audit_crops/visual_clash/VC007_d.png
    source: visual_clash:VC007
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "tau_d subscript clear of the arrow tip"
  - crop_id: VC008_g_E
    path: build/audit_crops/visual_clash/VC008_g_E.png
    source: visual_clash:VC008
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "arrow points to its intended g(E_t) target"
  - crop_id: VC009_crop
    path: build/audit_crops/visual_clash/VC009_crop.png
    source: visual_clash:VC009
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "isolated parenthesis glyph; no path crossing"
  - crop_id: VC010_Sulfur-rich
    path: build/audit_crops/visual_clash/VC010_Sulfur-rich.png
    source: visual_clash:VC010
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "subtitle keeps whitespace to the row-frame corner"
  - crop_id: VC011_E
    path: build/audit_crops/visual_clash/VC011_E.png
    source: visual_clash:VC011
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "standalone shallow-curve E_t axis label"
  - crop_id: VC012_Et
    path: build/audit_crops/visual_clash/VC012_Et.png
    source: visual_clash:VC012
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "rotated E_t axis label just outside the box edge with a gap"
  - crop_id: VC013_T
    path: build/audit_crops/visual_clash/VC013_T.png
    source: visual_clash:VC013
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "equation-internal T under its own fraction bar"
  - crop_id: VC014_crop
    path: build/audit_crops/visual_clash/VC014_crop.png
    source: visual_clash:VC014
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "bare arrow-tail stroke with no label to collide"
  - crop_id: VC015_d
    path: build/audit_crops/visual_clash/VC015_d.png
    source: visual_clash:VC015
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "tau_d subscript clear of the chain arrow"
  - crop_id: VC016_τ
    path: build/audit_crops/visual_clash/VC016_τ.png
    source: visual_clash:VC016
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "tau glyph on light row-frame fill with contrast"
  - crop_id: VC017_0
    path: build/audit_crops/visual_clash/VC017_0.png
    source: visual_clash:VC017
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "equation-internal subscript clear of the fraction rule"
  - crop_id: VC018_2
    path: build/audit_crops/visual_clash/VC018_2.png
    source: visual_clash:VC018
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "intentional step-number badge on its filled circle"
  - crop_id: VC019_Et
    path: build/audit_crops/visual_clash/VC019_Et.png
    source: visual_clash:VC019
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "rotated deep-curve E_t axis label just outside the box edge with a gap"
  - crop_id: VC020_I
    path: build/audit_crops/visual_clash/VC020_I.png
    source: visual_clash:VC020
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "standalone power-law label glyph"
  - crop_id: VC021_I
    path: build/audit_crops/visual_clash/VC021_I.png
    source: visual_clash:VC021
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Debye-equation glyph clear of the dashed curve"
  - crop_id: VC022_VB
    path: build/audit_crops/visual_clash/VC022_VB.png
    source: visual_clash:VC022
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "dashed E_t line between VB glyphs is band-diagram convention"
  - crop_id: VC023_S
    path: build/audit_crops/visual_clash/VC023_S.png
    source: visual_clash:VC023
    inspected: true
    verdict: defect
    linked_micro_defect_id: "M023"
    rationale: "amber spiral/S glyph floats at the far-left margin detached from the chain"
  - crop_id: VC024_sulfur
    path: build/audit_crops/visual_clash/VC024_sulfur.png
    source: visual_clash:VC024
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "caption-box body text with margin to the border"
  - crop_id: VC025_polarizability
    path: build/audit_crops/visual_clash/VC025_polarizability.png
    source: visual_clash:VC025
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "text reaches the inner box edge by intended text-width wrap"
  - crop_id: VC026_g_Et
    path: build/audit_crops/visual_clash/VC026_g_Et.png
    source: visual_clash:VC026
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "standalone deep-curve g(E_t) axis label"
  - crop_id: full_q1
    path: build/audit_crops/full_q1.png
    source: full_render
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Row 1 subtitle/axis overlap already captured under VC001/VC002; rest of the quadrant is clean"
  - crop_id: full_q2
    path: build/audit_crops/full_q2.png
    source: full_render
    inspected: true
    verdict: defect
    linked_micro_defect_id: "M027"
    rationale: "shallow trap tick segments absent from the gap below CB; trap levels detached (M027/C002)"
  - crop_id: full_q3
    path: build/audit_crops/full_q3.png
    source: full_render
    inspected: true
    verdict: defect
    linked_micro_defect_id: "M029"
    rationale: "stray blue dot in Row 2 (M029/C003); Row 3 polymer chain renders as plain sine without S sites (C001)"
  - crop_id: full_q4
    path: build/audit_crops/full_q4.png
    source: full_render
    inspected: true
    verdict: defect
    linked_micro_defect_id: "M027"
    rationale: "deep trap markers render as detached circle+line glyphs left of VB near the energy axis (M027/C002)"
  - crop_id: print_178mm
    path: build/audit_crops/print_178mm.png
    source: print_scale
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "178mm proxy keeps row titles, equation, and band labels legible; trap-level detail marginal but readable"
  - crop_id: print_thumbnail
    path: build/audit_crops/print_thumbnail.png
    source: print_scale
    inspected: true
    verdict: defect
    linked_micro_defect_id: "M030"
    rationale: "thumbnail reduction loses band-gap trap-level resolution (M030/C002)"
panels: []
findings:
  - id: C001
    severity: MAJOR
    category: structural
    tex_lines: [110, 113]
    observation: "Row 3 polymer backbone renders as a plain sine wave; the WavyChain sulfur sites and trap markers do not appear on the chain and one amber S glyph floats detached at the far-left margin, unlike the explicit zigzag-with-sulfur reference chain."
    suggested_fix: "verify WavyChain S-site and trap-marker arguments render on the backbone; remove the detached far-left glyph."
    status: open
  - id: C002
    severity: MAJOR
    category: structural
    tex_lines: [172, 176]
    observation: "Right-panel BandDiagram trap levels render as ~2 detached circle+line glyphs near the energy axis instead of the specified 3 shallow + 2 deep grouped tick segments inside the gap; the two trap populations are not clearly conveyed."
    suggested_fix: "review BandDiagram trap-level arguments/placement so shallow and deep levels render as grouped ticks inside the gap."
    status: open
  - id: C003
    severity: MINOR
    category: whitespace
    tex_lines: [86, 99]
    observation: "A stray blue filled circle floats in Row 2 below the n -> tau_d -> g(E_t) chain with no referent, reading as an orphaned trap marker."
    suggested_fix: "remove the stray Row 2 marker or bind it to a defined element."
    status: open
  - id: C004
    severity: MINOR
    category: label_placement
    tex_lines: [38, 39]
    observation: "Row 1 subtitle 'Discharge power-law vs. time (log-log)' overruns rightward so the plot y-axis line crosses 'time' and the dashed Debye curve crosses '(log-log)'."
    suggested_fix: "shorten or reflow the subtitle, or shift/shrink the inset plot to clear the subtitle."
    status: open
---

# Vision Critique — n3_trial_01_trap_depth

Overall verdict: **revise**. The figure communicates its three-row evidence to theory to molecular to unified-trap-depth story clearly, and the CB-above-VB band ordering with paired amber/violet g(E_t) lobes is physically sound. However, fresh reference-grounded inspection of the current render surfaces two MAJOR structural/fidelity gaps and two MINOR layout defects that keep it from manuscript readiness.

The two MAJOR findings are reference-fidelity failures that need a human/source decision rather than an automatic patch:

- **C001 — polymer chain:** Row 3 renders as a featureless sine wave. The reference image (`reference/codex_gen_v1.png`) shows an explicit zigzag backbone with sulfur (S) side groups, and the `\WavyChain` call declares S sites and trap markers that are not visible on the chain. A single amber S-like glyph floats detached at the far-left margin (VC023/M023), suggesting the sulfur markers are being placed off-chain.
- **C002 — band-gap trap levels:** The right panel should show three shallow ticks near CB and two deep ticks near VB as grouped levels inside the gap. The render instead shows roughly two detached circle+line markers at the left of the gap near the Energy axis (M027), so the "two distinct trap populations" invariant is weakly conveyed. This also fails to survive print-scale reduction (M030, `print_thumbnail`).

The two MINOR findings are local layout patches:

- **C003 —** a stray blue dot floats in Row 2 with no referent (M029).
- **C004 —** the Row 1 subtitle overruns into the plot, so the y-axis line crosses "time" and the dashed Debye curve crosses "(log-log)" (VC001/VC002).

All 26 visual-clash candidates were inspected; only VC001, VC002, and VC023 are real defects. The remaining 23 are axis labels, equation-internal glyphs, badge numerals, arrow-to-target flows, band-diagram reference-line conventions, or empty-text false positives, each accepted as a simplification with a per-candidate rationale.

This critique is report-only. Adjudication scaffolds every finding as `needs_human`; the band-diagram and polymer-chain decisions in particular require domain review and likely relate to known `\BandDiagram`/`\WavyChain` macro-API gaps rather than ad-hoc source tweaks.
