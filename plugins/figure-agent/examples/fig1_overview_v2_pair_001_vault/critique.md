---
schema: figure-agent.critique.v1.16
fixture: fig1_overview_v2_pair_001_vault
generated_at: '2026-06-01T00:00:00Z'
generator: critique_brief.py
generator_version: sha256:d91a7ef6c48815fb7e9da2e5d39a1f9657fdb53e534fb4c620ff338d12380ae5
rubric_version: figure-agent.critique-rubric.v1.16
critique_input_hash: sha256:2deed84642ba6dcb52ea3ffe2bbdc2b5b7177de910d35c58bad92cf2580f04a4
verdict: ready
audit_enumeration:
  structural_completeness:
    components:
    - component: Panel A linear poly(S-r-DIB) chain + DIB rings + S8 inset + (S)x bracket + inverse-vulcanization
        annotation
      mount_support: N/A
      rationale: Chemistry-register components on clean white; chain stroke + 4 aromatic rings + S8 ring
        carry polymer identity.
      connections: Bond strokes between rings; (S)x bracket; S8 ring with diagonal annotation arrow.
    - component: Panel B three chains S60/S75/S85 + sulfur-content axis
      mount_support: N/A
      rationale: Three stacked zig-zag chains on white; bottom axis arrow carries sulfur-content scaling.
      connections: S60/S75/S85 labels at chain ends; bottom axis arrow with 'Sulfur content, wt%'.
    - component: Panel C real-space film + energy diagram + trap dots + Gaussians
      mount_support: 'true'
      rationale: Polymer-film slab + shallow/deep trap dots + energy diagram (E_C / mobility edge / E_V)
        + bimodal Gaussian DOS + Delta-E_t arrow.
      connections: Color-matched dashed leaders bind LEFT trap sites to RIGHT energy levels; Delta-E_t
        double arrow spans E_C to deep band.
    - component: Panel D SMU V/A box + MIM stack + I(t)~t^-n plot
      mount_support: 'true'
      rationale: SMU wired to a MIM stack; ground at right; frame-less log-log plot with low-n / high-n
        / Debye.
      connections: SMU -> electrode leads with contact dots; ground at MIM right edge; arrow-only plot
        axes.
    - component: Panel E corona HV+ source + needle + sample stack + V_s probe + V_s meter
      mount_support: 'true'
      rationale: HV+ source + corona needle over the polymer; induction-type V_s probe (disk-on-shaft,
        NOT Kelvin) wired to the V_s meter.
      connections: HV+ output -> needle; surface-charge markers on polymer; probe -> meter via cable.
    - component: Panel E V_s(t) decay + g(E_t) Gaussians sub-zones
      mount_support: N/A
      rationale: 'Two stacked sub-zones: V_s(t) raw -> g(E_t) derived via a ''derive'' arrow with a tau_d
        caliper.'
      connections: V_s(t) curve with markers; 'derive' arrow; tau_d caliper between shallow and deep peaks.
    - component: Panel F V_active PSU + cantilever + q_tr + electrode + air gap + force arrows
      mount_support: 'true'
      rationale: PSU with square-pulse glyph; clamped cantilever with q_tr charges; vertical electrode
        with ground; air-gap caliper.
      connections: V_active -> electrode lead; bold red Coulomb arrow (force on charge); faint gray Maxwell
        baseline; rotated 'electrode' label.
    - component: 3-spoke branching arrows from Panel C bottom to Row 2 column tops
      mount_support: N/A
      rationale: Three spokes (kinetic / ISPD / mechanical) fan from below Panel C to D/E/F with the 'convergent
        evidence' caption.
      connections: Spoke labels mid-spoke; ISPD spoke label sits in the transition zone above Row 2 (TB001).
    missing_from_reference:
    - element: Cover-scene background wash / wavy chain-hint band
      status: intentional_omission
      rationale: '2026-05-22 redirect: NC main-text Fig 1 convention is clean white; cover-scene cohesion
        cues are anti-pattern here.'
    - element: Panel E corona/ISPD scanning-motion indicator
      status: intentional_omission
      rationale: Iconic-cartoon register per briefing 3.2 abstracts the full scanning/motion system.
    - element: Panel D MIM 3D perspective + measurement electronics
      status: intentional_omission
      rationale: Schematic SMU + cross-section MIM per briefing 3.2 iconic abstraction.
    - element: Panel F bilateral actuator symmetry
      status: intentional_omission
      rationale: Theory Guard TG-G-001 forbids actuator framing; single cantilever next to a vertical
        electrode is the chosen design.
  label_target_matching:
  - label: Sulfur-rich polymer
    nearest_object: Panel A linear chain + DIB rings
    intended_target: Panel A polymer identity
    matches: true
    proposed_fix: ''
  - label: shallow / deep
    nearest_object: blue / red Gaussian + level lines
    intended_target: Panel C trap species
    matches: true
    proposed_fix: ''
  - label: low n / high n
    nearest_object: navy / maroon power-law lines
    intended_target: Panel D kinetic exponents
    matches: true
    proposed_fix: ''
  - label: ISPD / kinetic / mechanical
    nearest_object: three spokes from Panel C
    intended_target: Row 2 modality spokes
    matches: true
    proposed_fix: ''
  - label: V_s probe / V_s meter / HV+ / V_active / electrode
    nearest_object: Panel E/F apparatus boxes and bars
    intended_target: apparatus identity
    matches: true
    proposed_fix: ''
  physical_plausibility:
  - check: cable_gravity
    finding: Probe-to-meter cable and wiring route as right-angle/bezier leads consistent with schematic
      convention.
    verdict: convention_acceptable
  - check: floating_components
    finding: No disconnected floating components; the flagged 'caret' is an attached dashed leader arrowhead.
    verdict: convention_acceptable
  - check: spatial_proximity
    finding: Apparatus components and their labels sit in plausible relative positions; meter labels inside
      their boxes.
    verdict: convention_acceptable
  - check: direction_orientation
    finding: Coulomb arrow points away from the electrode (repulsion); power-law tails above Debye at
      long times.
    verdict: convention_acceptable
  - check: material_distinction
    finding: Polymer (amber), electrodes (hatched/black), substrate (gray) are visually distinct.
    verdict: convention_acceptable
  conceptual_completeness:
  - element: Bimodal trap landscape (shallow + deep)
    reference: briefing
    severity: NIT
    proposed_action: accept_simplification
  - element: Three independent evidence modalities
    reference: briefing
    severity: NIT
    proposed_action: accept_simplification
  - element: Macroscopic mechanical expression
    reference: briefing
    severity: NIT
    proposed_action: accept_simplification
quality_axes:
  message_storyline:
    verdict: pass
    confidence: high
    rationale: 'The 30-second message reads: a sulfur-rich polymer hosts a bimodal trap landscape (Panel
      C hero) that three independent evidence lines (D kinetic, E ISPD, F mechanical) all probe and a
      macroscopic bend expresses.'
    evidence: Panel C hero + three-spoke fan to D/E/F; briefing 30-second message.
    blocking_items: []
    recommended_action: none
  panel_role_coherence:
    verdict: pass
    confidence: high
    rationale: Six panels carry distinct non-redundant roles (context/setup/model/result x3) with Panel
      C as the single model hero and Row 2 as three balanced evidence results.
    evidence: panel_roles below; full_q1..q4 render.
    blocking_items: []
    recommended_action: none
    panel_roles:
    - panel_id: a
      role: context
      role_quality: clear
      rationale: 'Material identity: linear poly(S-r-DIB) chemistry sets up the system.'
    - panel_id: b
      role: setup
      role_quality: clear
      rationale: Composition heterogeneity (S60/S75/S85) as the variable axis.
    - panel_id: c
      role: model
      role_quality: clear
      rationale: HERO trap-landscape model (real-space + energy diagram), first fixation.
    - panel_id: d
      role: result
      role_quality: clear
      rationale: Kinetic evidence line (I(t)~t^-n).
    - panel_id: e
      role: result
      role_quality: clear
      rationale: 'ISPD evidence line: V_s(t) decay derived into g(E_t).'
    - panel_id: f
      role: result
      role_quality: clear
      rationale: 'Mechanical evidence line: Coulomb-driven cantilever deflection.'
  subregion_integration:
    verdict: pass
    confidence: medium
    rationale: 'Sub-regions integrate into one figure: Row 1 reads left-to-right (A->B->C) and Row 2 radiates
      from C via the three-spoke fan; the E column''s internal V_s(t)->g(E_t) ''derive'' arrow ties its
      sub-zones.'
    evidence: panel_E_q3/q4 derive arrow; three-spoke fan in full_q3/q4.
    blocking_items: []
    recommended_action: none
  component_fidelity:
    verdict: pass
    confidence: medium
    rationale: Apparatus and molecular components are concrete and role-legible (SMU+MIM, corona+induction
      probe+meter, V_active+cantilever+electrode); the polymer chains and DIB rings carry material identity.
    evidence: crop_audit_log panel_D/E/F tiles; audit crops show recognizable instruments.
    blocking_items: []
    recommended_action: none
  scientific_plausibility:
    verdict: pass
    confidence: high
    rationale: 'Theory invariants hold in the render: linear Panel A topology, same-matrix shallow(blue)/deep(red)
      traps, power-law tails above Debye at long times, Coulomb-only result zone with a lower-tier Maxwell
      baseline, and an induction-type (not Kelvin) probe.'
    evidence: Theory Guard TG-A/C/CFG/D/G-001/G-002/ROW2-001; host re-inspection of Panels C/D/E/F.
    blocking_items: []
    recommended_action: none
  composition_layout:
    verdict: pass
    confidence: high
    rationale: 'Clean white NC main-text layout: no washes, panel-letter typography carries panel identity,
      Panel C at 1.5x width anchors Row 1, Row 2 columns are width-normalized and breathable.'
    evidence: full render; briefing M2 baseline.
    blocking_items: []
    recommended_action: none
  label_annotation_semantics:
    verdict: pass
    confidence: medium
    rationale: Labels map to their intended targets (modality labels on spokes, axis/curve labels on their
      lines, apparatus labels inside their boxes); 43/43 visual-clash and 1/1 text-boundary candidates
      reviewed and accounted as conventional or false-positive.
    evidence: micro_defects (44 entries); crop_audit_log (109 entries).
    blocking_items: []
    recommended_action: none
  journal_polish:
    verdict: pass
    confidence: medium
    rationale: At the 178 mm manuscript-width proxy subscripts, math labels, arrow tips and dense regions
      stay legible; line-weight hierarchy separates foreground mechanisms from supports.
    evidence: print_178mm crop; full render.
    blocking_items: []
    recommended_action: none
  reference_fidelity:
    verdict: pass
    confidence: medium
    rationale: Matches the figure-level style reference (codex_gen_overview_v1.png) for palette restraint,
      two-row proportion, and label hierarchy without transferring the forbidden network topology or plot-grid
      equality.
    evidence: reference_pack roles; Panel A linear topology preserved.
    blocking_items: []
    recommended_action: none
  publication_readiness:
    verdict: pass
    confidence: medium
    rationale: All upstream axes pass and no open BLOCKER/MAJOR remains; the artifact is figure-ready.
      Target-journal AI/image provenance remains a separate human gate (TG-PUB-001) tracked outside this
      critique.
    evidence: axis summary above; TG-PUB-001 acceptance note.
    blocking_items: []
    recommended_action: none
top_tier_audit:
  first_glance_message:
    verdict: pass
    finding: In 3-10 s a reader sees a hero trap-landscape model (C) feeding three evidence lines; the
      central claim is legible without the caption.
    concrete_fix: accept_simplification - message reads clearly.
    blocks_high_impact: false
  target_journal_fit:
    verdict: pass
    finding: Restrained editorial illustration on clean white fits a Nature Materials / NC main-text Figure
      1.
    concrete_fix: accept_simplification - fits target register.
    blocks_high_impact: false
  novelty_claim_support:
    verdict: pass
    finding: The visual supports the central claim that one bimodal trap landscape is probed by three
      independent modalities and expressed mechanically.
    concrete_fix: accept_simplification - figure supports the claim.
    blocks_high_impact: false
  figure_caption_coupling:
    verdict: pass
    finding: The figure carries the schematic burden while leaving quantitative detail (tick values, measured
      curves) to caption/later figures, consistent with the iconic-cartoon intent.
    concrete_fix: accept_simplification - burden split is appropriate.
    blocks_high_impact: false
  visual_economy:
    verdict: pass
    finding: 'Ink is economical: no decorative wash, supports subordinate to mechanisms; every mark carries
      meaning.'
    concrete_fix: accept_simplification - economy is good.
    blocks_high_impact: false
  cross_panel_semantic_grammar:
    verdict: pass
    finding: 'Consistent grammar across panels: shallow=blue / deep=red, red charge/force cues, panel-letter
      typography, axis-arrow (frame-less) plot register shared by D/E/F.'
    concrete_fix: accept_simplification - grammar is coherent.
    blocks_high_impact: false
  reader_misinterpretation_risk:
    verdict: pass
    finding: Row 2 reads as three independent spokes from C (not a D->E->F causal chain) because of the
      fan geometry and modality labels; low misinterpretation risk.
    concrete_fix: accept_simplification - spoke geometry guards the reading.
    blocks_high_impact: false
  reduction_print_readability:
    verdict: pass
    finding: At the 178 mm proxy labels and arrow tips survive; thumbnail softening is expected and non-blocking.
    concrete_fix: accept_simplification - legible at manuscript width.
    blocks_high_impact: false
  accessibility_color_robustness:
    verdict: pass
    finding: Shallow/deep are encoded redundantly by blue/red AND vertical position AND text labels, so
      the red-blue pairing remains distinguishable under common CVD and in grayscale.
    concrete_fix: accept_simplification - redundant encoding present.
    blocks_high_impact: false
  aesthetic_coherence:
    verdict: pass
    finding: The current render holds one style authority across line weights, detail density, and depth
      cues; the six panels (a-f) read as a single series with no toy_diagram anti-pattern, satisfying
      the mature_restraint and scientific_hand_craft design principles.
    concrete_fix: accept_simplification - coherent style; no toy_diagram drift visible.
    blocks_high_impact: false
editorial_art_direction:
  hero_focus:
    verdict: pass
    evidence: Panel C at 1.5x width with the strongest deep-red saturation is the first fixation in full_q2.
    rationale: A clear hero anchors a high-impact figure.
    concrete_fix: accept_simplification - hero is established.
    blocks_high_impact: false
  narrative_choreography:
    verdict: pass
    evidence: Row 1 left-to-right setup then a three-spoke fan into Row 2 evidence creates a guided read
      path.
    rationale: Choreography matches the convergent-evidence story.
    concrete_fix: accept_simplification - read path is guided.
    blocks_high_impact: false
  illustration_readiness:
    verdict: pass
    evidence: Instrument and molecular components are crisp and physically plausible at print scale (print_178mm).
    rationale: Illustration quality meets target-journal expectation.
    concrete_fix: accept_simplification - illustration-ready.
    blocks_high_impact: false
  abstraction_consistency:
    verdict: pass
    evidence: D/E/F share an iconic frame-less plot register; A/C are schematic-dominant; B is the declared
      hybrid - abstraction levels match declared roles.
    rationale: Abstraction is consistent with the role map.
    concrete_fix: accept_simplification - consistent abstraction.
    blocks_high_impact: false
  reference_class_fit:
    verdict: pass
    evidence: Matches the multipanel-story reference class of a Nature Materials main-text Figure 1.
    rationale: Fits the declared reference class.
    concrete_fix: accept_simplification - reference-class fit.
    blocks_high_impact: false
  visual_identity:
    verdict: pass
    evidence: In the current render the amber/blue/red/gray families map consistently to meaning with
      no toy_diagram poster saturation, giving an editorial visual identity aligned to the nature materials
      target (visible across panels a-f).
    rationale: Identity is anchored to scientific meaning, not decoration; matches the editorial maturity
      of the aesthetic intent.
    concrete_fix: accept_simplification - identity is coherent.
    blocks_high_impact: false
  claim_payload_fit:
    verdict: pass
    evidence: The visual payload (one model + three evidence spokes + mechanical expression) matches the
      manuscript claim.
    rationale: Payload fits the claim.
    concrete_fix: accept_simplification - payload fits.
    blocks_high_impact: false
  aesthetic_risk:
    verdict: pass
    evidence: The current render shows no toy_diagram anti-pattern (no oversized arrows, rounded generic
      boxes, or poster-like flat color) and no preset_macro_feel (panels a-f are editorially composed,
      not templated).
    rationale: Low aesthetic risk; stays within the mature_restraint bound.
    concrete_fix: accept_simplification - within mature_restraint bounds.
    blocks_high_impact: false
  tikz_vs_svg_polish_trigger:
    verdict: pass
    evidence: In the current render the TikZ source is semantically correct and print-scale legible (178
      mm proxy), so neither the svg_micro_polish nor the semantic_backport polish_trigger condition is
      met; the only residual item is an optional NIT (convergent-evidence caption clearance from the wt%
      axis label).
    rationale: Stay in TikZ; no svg_micro_polish or semantic_backport pending.
    concrete_fix: accept_simplification - source-correct.
    blocks_high_impact: false
    recommended_path: continue_tikz
    remaining_tikz_lever: 'Optional only: marginally increase the ''convergent evidence'' caption''s clearance
      from the ''Sulfur content, wt%'' axis label (NIT, VC018/VC019). Non-blocking; no other TikZ work
      remains.'
  human_art_direction_gate:
    verdict: pass
    evidence: No figure-level art-direction decision is unresolved; remaining gating is publication AI/image
      provenance (TG-PUB-001), which is a policy gate, not an art-direction one.
    rationale: No human art-direction escalation required.
    concrete_fix: accept_simplification - no open art-direction question.
    blocks_high_impact: false
journal_grade_assessment:
  schema: figure-agent.journal-grade-assessment.v1
  scoring_mode: fresh_reaudit
  assessed_artifact_hash: sha256:2deed84642ba6dcb52ea3ffe2bbdc2b5b7177de910d35c58bad92cf2580f04a4
  benchmark_level: high_impact_candidate
  confidence: medium
  blockers: []
  regression_detected: false
  regressions: []
  score_is_gateable: true
  next_quality_bottleneck: polish
  rationale: 'Fresh v1.16 re-audit of the current render: clean white NC main-text layout, clear Panel
    C hero, coherent cross-panel grammar, theory invariants intact, and 178 mm-legible labels. No open
    BLOCKER/MAJOR. Remaining headroom is optional micro-polish (caption clearance) and the separate publication-provenance
    gate.'
  overall_score: 88
  sub_scores:
    storyline: 90
    composition: 89
    component_fidelity: 86
    scientific_plausibility: 92
    label_semantics: 88
    polish: 85
    reference_fidelity: 86
    export_scale_readability: 88
  score_rationale: 'Numbers describe only the current artifact: storyline and scientific plausibility
    are strongest (clear convergent-evidence narrative, invariants honored); polish is the lowest sub-score
    because of minor label-crowding NITs (convergent/wt% adjacency) that do not block release.'
aesthetic_lever_audit:
- lever_id: maturity_restraint
  dimension: maturity
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - neutral hierarchy with no poster-like saturation
  - instrument boxes and labels crisp at 178 mm
  - accent color tied to scientific meaning
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - editorial_art_direction.visual_identity
  - editorial_art_direction.aesthetic_risk
  - top_tier_audit.aesthetic_coherence
  allowed_next_adjustment: ''
  forbidden_adjustment_guard: remove scientific components; change mechanism meaning; hide required labels
  rationale: The current render satisfies the declared maturity_restraint positive signals with no observed
    anti-patterns, so the lever passes and needs no route.
- lever_id: panel_c_hero_hierarchy
  dimension: hero_hierarchy
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - Panel C dominant without swallowing Row 2
  - real-space and energy halves read as one model
  - three-spoke fan routes from model to D/E/F
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - editorial_art_direction.hero_focus
  - quality_axes.panel_role_coherence
  allowed_next_adjustment: ''
  forbidden_adjustment_guard: collapse Panel C into a decorative cover scene; change the declared A-F
    panel roles
  rationale: The current render satisfies the declared panel_c_hero_hierarchy positive signals with no
    observed anti-patterns, so the lever passes and needs no route.
- lever_id: row2_whitespace_breathing
  dimension: whitespace_breathing
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - D/E/F gutters visible
  - instrument-box labels stay inside their outlines (VC028/VC029)
  - sub-zone labels have local breathing room
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - quality_axes.composition_layout
  - micro_defects.M028
  - micro_defects.M029
  allowed_next_adjustment: ''
  forbidden_adjustment_guard: move evidence between columns; delete required Row 2 instrument labels
  rationale: The current render satisfies the declared row2_whitespace_breathing positive signals with
    no observed anti-patterns, so the lever passes and needs no route.
- lever_id: print_typography_authority
  dimension: typography_authority
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - subscripts readable in the 178 mm proxy
  - math labels consistent in size/weight
  - panel letters form a controlled hierarchy
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - quality_axes.journal_polish
  - top_tier_audit.reduction_print_readability
  allowed_next_adjustment: ''
  forbidden_adjustment_guard: rename symbols; change measured quantities; hide a mechanism-anchoring label
  rationale: The current render satisfies the declared print_typography_authority positive signals with
    no observed anti-patterns, so the lever passes and needs no route.
- lever_id: semantic_color_economy
  dimension: color_harmony
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - amber/blue/red/gray families map consistently to meaning
  - background grays do not compete with accents
  - deep-trap red appears only where it carries mechanism
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - top_tier_audit.cross_panel_semantic_grammar
  - quality_axes.scientific_plausibility
  allowed_next_adjustment: ''
  forbidden_adjustment_guard: swap shallow and deep trap colors; change force-direction color semantics
  rationale: The current render satisfies the declared semantic_color_economy positive signals with no
    observed anti-patterns, so the lever passes and needs no route.
- lever_id: line_weight_rhythm
  dimension: line_weight_rhythm
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - foreground mechanism strokes distinguishable from supports
  - axes/wiring do not overpower labels
  - repeated textures subordinate
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - quality_axes.composition_layout
  allowed_next_adjustment: ''
  forbidden_adjustment_guard: change graph/data relationships; remove required wiring or axes
  rationale: The current render satisfies the declared line_weight_rhythm positive signals with no observed
    anti-patterns, so the lever passes and needs no route.
- lever_id: component_fidelity_finish
  dimension: component_fidelity
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - instrument components have recognizable roles
  - polymer/apparatus detail supports the mechanism
  - D/E/F evidence modes remain visually distinct
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - quality_axes.component_fidelity
  - editorial_art_direction.illustration_readiness
  allowed_next_adjustment: ''
  forbidden_adjustment_guard: invent unsupported apparatus; change the experiment class; add decorative
    detail implying false measurement capability
  rationale: The current render satisfies the declared component_fidelity_finish positive signals with
    no observed anti-patterns, so the lever passes and needs no route.
- lever_id: hand_craft_escape_route
  dimension: hand_craft
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - geometry is semantically correct
  - no preset-macro repetition that reads as machine-generated
  - material identity carried where needed
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - editorial_art_direction.tikz_vs_svg_polish_trigger
  allowed_next_adjustment: ''
  forbidden_adjustment_guard: use SVG polish to alter mechanism; change accepted/golden artifacts without
    an explicit gate
  rationale: The current render satisfies the declared hand_craft_escape_route positive signals with no
    observed anti-patterns, so the lever passes and needs no route.
- lever_id: cross_panel_grammar
  dimension: cross_panel_grammar
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - panel letters/title weights/icon abstractions repeat coherently
  - Row 2 panels share an apparatus-register grammar
  - A/B setup and C model prepare D/E/F
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - top_tier_audit.cross_panel_semantic_grammar
  - top_tier_audit.aesthetic_coherence
  allowed_next_adjustment: ''
  forbidden_adjustment_guard: make all panels visually identical; remove role-specific distinctions
  rationale: The current render satisfies the declared cross_panel_grammar positive signals with no observed
    anti-patterns, so the lever passes and needs no route.
aesthetic_gate_audit: []
micro_defects:
- id: M001
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC001_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC001 (text ''S''): Chemistry register: two backbone bond strokes
    terminate at the ''S'' glyph perimeter; S fully legible.'
  linked_finding_id: ''
  visual_clash_ref: VC001
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC001: Chemistry register: two backbone bond strokes terminate at
    the ''S'' glyph perimeter; S fully legible. This is not a defect (convention_acceptable).'
- id: M002
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC002_S.png
  kind: line_crosses_label
  severity: NIT
  observation: 'Visual-clash candidate VC002 (text ''S''): Chemistry register: a diagonal backbone bond
    clips the ''S'' edges but leaves the counters open; S legible.'
  linked_finding_id: ''
  visual_clash_ref: VC002
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC002: Chemistry register: a diagonal backbone bond clips the ''S''
    edges but leaves the counters open; S legible. This is not a defect (convention_acceptable).'
- id: M003
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC003_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC003 (text ''S''): Chemistry register: three bonds radiate to
    the ''S'' perimeter, none cross the interior; S legible.'
  linked_finding_id: ''
  visual_clash_ref: VC003
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC003: Chemistry register: three bonds radiate to the ''S'' perimeter,
    none cross the interior; S legible. This is not a defect (convention_acceptable).'
- id: M004
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC004_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC004 (text ''S''): Chemistry register: two bonds meet the lower
    ''S'' bowl at the perimeter; S legible.'
  linked_finding_id: ''
  visual_clash_ref: VC004
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC004: Chemistry register: two bonds meet the lower ''S'' bowl at
    the perimeter; S legible. This is not a defect (convention_acceptable).'
- id: M005
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC005_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC005 (text ''S''): Chemistry register: two bonds meet the ''S''
    shoulders at the perimeter; S legible.'
  linked_finding_id: ''
  visual_clash_ref: VC005
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC005: Chemistry register: two bonds meet the ''S'' shoulders at the
    perimeter; S legible. This is not a defect (convention_acceptable).'
- id: M006
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC006_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC006 (text ''S''): Chemistry register: bonds graze the ''S'' perimeter
    with a hairline gap; S legible.'
  linked_finding_id: ''
  visual_clash_ref: VC006
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC006: Chemistry register: bonds graze the ''S'' perimeter with a
    hairline gap; S legible. This is not a defect (convention_acceptable).'
- id: M007
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC007_S.png
  kind: line_crosses_label
  severity: NIT
  observation: 'Visual-clash candidate VC007 (text ''S''): Chemistry register: a diagonal bond clips the
    ''S'' as in VC002; counters open, S legible.'
  linked_finding_id: ''
  visual_clash_ref: VC007
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC007: Chemistry register: a diagonal bond clips the ''S'' as in VC002;
    counters open, S legible. This is not a defect (convention_acceptable).'
- id: M008
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC008_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC008 (text ''S''): Chemistry register: bonds meet ''S'' shoulders
    with an upper-right near-touch; S legible.'
  linked_finding_id: ''
  visual_clash_ref: VC008
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC008: Chemistry register: bonds meet ''S'' shoulders with an upper-right
    near-touch; S legible. This is not a defect (convention_acceptable).'
- id: M009
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC009_C.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC009 (text ''C''): Energy-diagram ''C'' is clear; the neighbouring
    ''E''/''ob'' fragments are frame-edge truncations of adjacent labels, not contact.'
  linked_finding_id: ''
  visual_clash_ref: VC009
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC009: Energy-diagram ''C'' is clear; the neighbouring ''E''/''ob''
    fragments are frame-edge truncations of adjacent labels, not contact. This is not a defect (false_positive).'
- id: M010
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC010_mobility.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC010 (text ''mobility''): ''mobility'' is clear of any stroke;
    the dark-red Delta-E_t indicator arrow clashes with the adjacent word ''edge'' (VC011), not ''mobility''.'
  linked_finding_id: ''
  visual_clash_ref: VC010
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC010: ''mobility'' is clear of any stroke; the dark-red Delta-E_t
    indicator arrow clashes with the adjacent word ''edge'' (VC011), not ''mobility''. This is not a defect
    (false_positive).'
- id: M011
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC011_edge.png
  kind: line_crosses_label
  severity: NIT
  observation: 'Visual-clash candidate VC011 (text ''edge''): The dark-red Delta-E_t / mobility-edge indicator
    arrow runs between the ''d'' and ''g'' of ''edge''; an energy-axis annotation arrow over its own label
    is conventional and ''edge'' stays readable.'
  linked_finding_id: ''
  visual_clash_ref: VC011
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC011: The dark-red Delta-E_t / mobility-edge indicator arrow runs
    between the ''d'' and ''g'' of ''edge''; an energy-axis annotation arrow over its own label is conventional
    and ''edge'' stays readable. This is not a defect (convention_acceptable).'
- id: M012
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC012_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC012 (text ''S''): Chemistry register near-miss: ''S'' clear;
    neighbouring atom node and digit fragment are frame cuts.'
  linked_finding_id: ''
  visual_clash_ref: VC012
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC012: Chemistry register near-miss: ''S'' clear; neighbouring atom
    node and digit fragment are frame cuts. This is not a defect (convention_acceptable).'
- id: M013
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC013_shallow.png
  kind: line_crosses_label
  severity: NIT
  observation: 'Visual-clash candidate VC013 (text ''shallow''): The dark-red trap-level reference line
    crosses ''shallow'' in the inter-letter gap of the double-l; all letters readable; energy-level convention.'
  linked_finding_id: ''
  visual_clash_ref: VC013
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC013: The dark-red trap-level reference line crosses ''shallow''
    in the inter-letter gap of the double-l; all letters readable; energy-level convention. This is not
    a defect (convention_acceptable).'
- id: M014
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC014_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC014 (text ''S''): Chemistry register near-miss: ''S'' clear;
    neighbouring node/glyph fragments are frame cuts.'
  linked_finding_id: ''
  visual_clash_ref: VC014
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC014: Chemistry register near-miss: ''S'' clear; neighbouring node/glyph
    fragments are frame cuts. This is not a defect (convention_acceptable).'
- id: M015
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC015_Sulfur-rich.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC015 (text ''Sulfur-rich''): ''Sulfur-rich'' sits on clean white
    with no adjacent stroke; detector fired on background only.'
  linked_finding_id: ''
  visual_clash_ref: VC015
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC015: ''Sulfur-rich'' sits on clean white with no adjacent stroke;
    detector fired on background only. This is not a defect (false_positive).'
- id: M016
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC016_poly_S-r-DIB.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC016 (text ''poly(S-r-DIB)''): ''poly(S-r-DIB)'' sits on clean
    white with no adjacent stroke; fully legible.'
  linked_finding_id: ''
  visual_clash_ref: VC016
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC016: ''poly(S-r-DIB)'' sits on clean white with no adjacent stroke;
    fully legible. This is not a defect (false_positive).'
- id: M017
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC017_Sulfur.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC017 (text ''Sulfur''): Axis label ''Sulfur'' is clear; the faint
    tick above is separated; following ''co'' is a frame cut.'
  linked_finding_id: ''
  visual_clash_ref: VC017
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC017: Axis label ''Sulfur'' is clear; the faint tick above is separated;
    following ''co'' is a frame cut. This is not a defect (false_positive).'
- id: M018
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC018_wt.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC018 (text ''wt%''): Panel-B axis label ''Sulfur content, wt%''
    sits adjacent to the Row-1.5 ''convergent evidence'' caption on a different baseline; both labels
    remain individually legible (tight but distinct).'
  linked_finding_id: ''
  visual_clash_ref: VC018
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC018: Panel-B axis label ''Sulfur content, wt%'' sits adjacent to
    the Row-1.5 ''convergent evidence'' caption on a different baseline; both labels remain individually
    legible (tight but distinct). This is not a defect (convention_acceptable).'
- id: M019
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC019_convergent.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC019 (text ''convergent''): ''convergent evidence'' caption sits
    just below-right of the ''wt%'' axis label; the two distinct labels crowd but each is legible; host
    re-inspection confirms separable baselines.'
  linked_finding_id: ''
  visual_clash_ref: VC019
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC019: ''convergent evidence'' caption sits just below-right of the
    ''wt%'' axis label; the two distinct labels crowd but each is legible; host re-inspection confirms
    separable baselines. This is not a defect (convention_acceptable).'
- id: M020
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC020_V.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC020 (text ''V''): Energy-axis ''V'' (E_V region) glyph is clear;
    the bracketed ''E'' fragment at left is a frame cut.'
  linked_finding_id: ''
  visual_clash_ref: VC020
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC020: Energy-axis ''V'' (E_V region) glyph is clear; the bracketed
    ''E'' fragment at left is a frame cut. This is not a defect (false_positive).'
- id: M021
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC021_ISPD.png
  kind: label_stacked_on_reference_line
  severity: NIT
  observation: 'Visual-clash candidate VC021 (text ''ISPD''): ''ISPD'' is the middle spoke''s modality
    label sitting on its own thin/light spoke line with the convergence arrowhead above; all four letters
    legible; intentional spoke geometry.'
  linked_finding_id: ''
  visual_clash_ref: VC021
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC021: ''ISPD'' is the middle spoke''s modality label sitting on its
    own thin/light spoke line with the convergence arrowhead above; all four letters legible; intentional
    spoke geometry. This is not a defect (convention_acceptable).'
- id: M022
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC022_polymer.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC022 (text ''polymer''): ''polymer'' callout: a leader attaches
    at the word''s right end and runs to the film-slab corner; host re-inspection confirms the leader
    does NOT cross the glyphs.'
  linked_finding_id: ''
  visual_clash_ref: VC022
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC022: ''polymer'' callout: a leader attaches at the word''s right
    end and runs to the film-slab corner; host re-inspection confirms the leader does NOT cross the glyphs.
    This is not a defect (convention_acceptable).'
- id: M023
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC023_film.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC023 (text ''film''): ''film'' sits on an open tan gradient with
    ample clearance; no stroke crosses the glyphs.'
  linked_finding_id: ''
  visual_clash_ref: VC023
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC023: ''film'' sits on an open tan gradient with ample clearance;
    no stroke crosses the glyphs. This is not a defect (false_positive).'
- id: M024
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC024_crop.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: 'Visual-clash candidate VC024 (text ''+''): Surface-charge marker: white ''+'' knockout
    on a maroon charge disc straddling the film-surface line; iconographic charge cue, legible.'
  linked_finding_id: ''
  visual_clash_ref: VC024
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC024: Surface-charge marker: white ''+'' knockout on a maroon charge
    disc straddling the film-surface line; iconographic charge cue, legible. This is not a defect (intentional_schematic).'
- id: M025
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC025_crop.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: 'Visual-clash candidate VC025 (text ''+''): Surface-charge marker: white ''+'' knockout
    on a maroon charge disc on the surface boundary; iconographic charge cue, legible.'
  linked_finding_id: ''
  visual_clash_ref: VC025
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC025: Surface-charge marker: white ''+'' knockout on a maroon charge
    disc on the surface boundary; iconographic charge cue, legible. This is not a defect (intentional_schematic).'
- id: M026
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC026_crop.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: 'Visual-clash candidate VC026 (text ''+''): Surface-charge marker: white ''+'' knockout
    on a maroon charge disc on the surface boundary; iconographic charge cue, legible.'
  linked_finding_id: ''
  visual_clash_ref: VC026
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC026: Surface-charge marker: white ''+'' knockout on a maroon charge
    disc on the surface boundary; iconographic charge cue, legible. This is not a defect (intentional_schematic).'
- id: M027
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC027_crop.png
  kind: label_glyph_overlaps_internal_drawing
  severity: NIT
  observation: 'Visual-clash candidate VC027 (text ''+''): Surface-charge marker: white ''+'' knockout
    on a maroon charge disc on the block-top outline; iconographic charge cue, legible.'
  linked_finding_id: ''
  visual_clash_ref: VC027
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC027: Surface-charge marker: white ''+'' knockout on a maroon charge
    disc on the block-top outline; iconographic charge cue, legible. This is not a defect (intentional_schematic).'
- id: M028
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC028_Vs.png
  kind: label_backdrop_overflows_outline
  severity: NIT
  observation: 'Visual-clash candidate VC028 (text ''Vs''): ''V_s'' display label sits fully inside the
    rounded meter-box outline with margin; host re-inspection confirms no glyph/backdrop overflows or
    is clipped (closes prior finding C002).'
  linked_finding_id: ''
  visual_clash_ref: VC028
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC028: ''V_s'' display label sits fully inside the rounded meter-box
    outline with margin; host re-inspection confirms no glyph/backdrop overflows or is clipped (closes
    prior finding C002). This is not a defect (false_positive).'
- id: M029
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC029_meter.png
  kind: label_backdrop_overflows_outline
  severity: NIT
  observation: 'Visual-clash candidate VC029 (text ''meter''): ''meter'' display label sits fully inside
    the rounded meter-box outline; terminal ''r'' has clear margin to the border; no overflow/clip (closes
    prior finding C002).'
  linked_finding_id: ''
  visual_clash_ref: VC029
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC029: ''meter'' display label sits fully inside the rounded meter-box
    outline; terminal ''r'' has clear margin to the border; no overflow/clip (closes prior finding C002).
    This is not a defect (false_positive).'
- id: M030
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC030_V.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC030 (text ''V''): Electrode-region ''V'' glyph is clear within
    its panel field; horizontal panel outlines are separated from the glyph.'
  linked_finding_id: ''
  visual_clash_ref: VC030
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC030: Electrode-region ''V'' glyph is clear within its panel field;
    horizontal panel outlines are separated from the glyph. This is not a defect (false_positive).'
- id: M031
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC031_V.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC031 (text ''V''): V_s(t)-axis ''V'' label sits beside its axis;
    the axis line does not cross the glyph; conventional axis labelling.'
  linked_finding_id: ''
  visual_clash_ref: VC031
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC031: V_s(t)-axis ''V'' label sits beside its axis; the axis line
    does not cross the glyph; conventional axis labelling. This is not a defect (convention_acceptable).'
- id: M032
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC032_t.png
  kind: label_curve_near_label
  severity: NIT
  observation: 'Visual-clash candidate VC032 (text ''(t)''): Math label ''(t)'': the parenthesis arcs
    are the symbol''s own brackets; they approach but do not strike the italic ''t''.'
  linked_finding_id: ''
  visual_clash_ref: VC032
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC032: Math label ''(t)'': the parenthesis arcs are the symbol''s
    own brackets; they approach but do not strike the italic ''t''. This is not a defect (convention_acceptable).'
- id: M033
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC033_I_t.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC033 (text ''I(t)''): ''I(t) ~'' expression sits on clean white
    with full clearance; the corner wedge does not touch glyphs.'
  linked_finding_id: ''
  visual_clash_ref: VC033
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC033: ''I(t) ~'' expression sits on clean white with full clearance;
    the corner wedge does not touch glyphs. This is not a defect (false_positive).'
- id: M034
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC034_low.png
  kind: label_stacked_on_reference_line
  severity: NIT
  observation: 'Visual-clash candidate VC034 (text ''low''): Plot curve label ''low n'' (navy) sits on
    its own navy power-law line; conventional curve labelling, legible.'
  linked_finding_id: ''
  visual_clash_ref: VC034
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC034: Plot curve label ''low n'' (navy) sits on its own navy power-law
    line; conventional curve labelling, legible. This is not a defect (convention_acceptable).'
- id: M035
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC035_crop.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC035 (text '')''): The auto-crop window clipped the '')'' glyph
    (mostly out of frame); the parenthesis belongs to the g(E_t)/(t) axis label and is legible in full
    context; crop-window artefact, not a figure defect.'
  linked_finding_id: ''
  visual_clash_ref: VC035
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC035: The auto-crop window clipped the '')'' glyph (mostly out of
    frame); the parenthesis belongs to the g(E_t)/(t) axis label and is legible in full context; crop-window
    artefact, not a figure defect. This is not a defect (false_positive).'
- id: M036
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC036_hig.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC036 (text ''hig''): Rotated curve label ''high n'' (maroon) sits
    along its maroon power-law line; the navy line skims the ascender tops as a near-miss; both labels
    legible.'
  linked_finding_id: ''
  visual_clash_ref: VC036
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC036: Rotated curve label ''high n'' (maroon) sits along its maroon
    power-law line; the navy line skims the ascender tops as a near-miss; both labels legible. This is
    not a defect (convention_acceptable).'
- id: M037
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC037_h.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC037 (text ''h''): ''high n'' fragment ''h'' near the navy line;
    near-miss with white separation; legible.'
  linked_finding_id: ''
  visual_clash_ref: VC037
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC037: ''high n'' fragment ''h'' near the navy line; near-miss with
    white separation; legible. This is not a defect (convention_acceptable).'
- id: M038
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC038_n.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC038 (text ''n''): ''high n'' subscript ''n'' sits in clear space
    below its line; near-miss only; legible.'
  linked_finding_id: ''
  visual_clash_ref: VC038
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC038: ''high n'' subscript ''n'' sits in clear space below its line;
    near-miss only; legible. This is not a defect (convention_acceptable).'
- id: M039
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC039_d.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC039 (text ''d''): Energy-axis ''d'' glyph sits clear above the
    thin baseline rule; no contact.'
  linked_finding_id: ''
  visual_clash_ref: VC039
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC039: Energy-axis ''d'' glyph sits clear above the thin baseline
    rule; no contact. This is not a defect (false_positive).'
- id: M040
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC040_log.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC040 (text ''log''): Rotated axis label ''log I'': the ''g'' descender
    lands at the vertical axis line; conventional rotated axis label, legible.'
  linked_finding_id: ''
  visual_clash_ref: VC040
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC040: Rotated axis label ''log I'': the ''g'' descender lands at
    the vertical axis line; conventional rotated axis label, legible. This is not a defect (convention_acceptable).'
- id: M041
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC041_I.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC041 (text ''I''): Axis label ''I'' near the vertical axis line
    with a thin white gap; near-miss, conventional axis labelling.'
  linked_finding_id: ''
  visual_clash_ref: VC041
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC041: Axis label ''I'' near the vertical axis line with a thin white
    gap; near-miss, conventional axis labelling. This is not a defect (convention_acceptable).'
- id: M042
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC042_f.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC042 (text ''f''): g(E_t)-region ''f'' glyph sits clear on white;
    the thin top rule is separated.'
  linked_finding_id: ''
  visual_clash_ref: VC042
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC042: g(E_t)-region ''f'' glyph sits clear on white; the thin top
    rule is separated. This is not a defect (false_positive).'
- id: M043
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC043_HV.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC043 (text ''HV+''): ''HV+'' source-box label sits on white with
    clear space; the adjacent rounded box corner does not touch the glyphs.'
  linked_finding_id: ''
  visual_clash_ref: VC043
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC043: ''HV+'' source-box label sits on white with clear space; the
    adjacent rounded box corner does not touch the glyphs. This is not a defect (false_positive).'
- id: M044
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_overflows_row_box
  severity: NIT
  observation: 'Text-boundary candidate TB001: the ''ISPD'' spoke modality label sits at the top edge
    of the row2_contain_text box (clearance 0.0pt).'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: TB001
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'TB001: ''ISPD'' is the middle spoke''s modality label placed in the
    Row-1-to-Row-2 transition (spoke) zone by design; host re-inspection confirms ISPD sits above the
    row divider rule, clearly separated from the V_s probe apparatus label below. The 0.0pt clearance
    is the intended spoke-zone placement, not a row-box overflow defect.'
crop_audit_log:
- crop_id: VC001_S
  path: build/audit_crops/visual_clash/VC001_S.png
  source: visual_clash:VC001
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Chemistry register: two backbone bond strokes terminate at the ''S'' glyph perimeter; S
    fully legible.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Chemistry register: two backbone bond strokes terminate at the ''S'' glyph perimeter;
    S fully legible.'
  candidate_refs:
  - VC001
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC002_S
  path: build/audit_crops/visual_clash/VC002_S.png
  source: visual_clash:VC002
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Chemistry register: a diagonal backbone bond clips the ''S'' edges but leaves the counters
    open; S legible.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Chemistry register: a diagonal backbone bond clips the ''S'' edges but leaves the
    counters open; S legible.'
  candidate_refs:
  - VC002
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC003_S
  path: build/audit_crops/visual_clash/VC003_S.png
  source: visual_clash:VC003
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Chemistry register: three bonds radiate to the ''S'' perimeter, none cross the interior;
    S legible.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Chemistry register: three bonds radiate to the ''S'' perimeter, none cross the
    interior; S legible.'
  candidate_refs:
  - VC003
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC004_S
  path: build/audit_crops/visual_clash/VC004_S.png
  source: visual_clash:VC004
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Chemistry register: two bonds meet the lower ''S'' bowl at the perimeter; S legible.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Chemistry register: two bonds meet the lower ''S'' bowl at the perimeter; S legible.'
  candidate_refs:
  - VC004
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC005_S
  path: build/audit_crops/visual_clash/VC005_S.png
  source: visual_clash:VC005
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Chemistry register: two bonds meet the ''S'' shoulders at the perimeter; S legible.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Chemistry register: two bonds meet the ''S'' shoulders at the perimeter; S legible.'
  candidate_refs:
  - VC005
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC006_S
  path: build/audit_crops/visual_clash/VC006_S.png
  source: visual_clash:VC006
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Chemistry register: bonds graze the ''S'' perimeter with a hairline gap; S legible.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Chemistry register: bonds graze the ''S'' perimeter with a hairline gap; S legible.'
  candidate_refs:
  - VC006
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC007_S
  path: build/audit_crops/visual_clash/VC007_S.png
  source: visual_clash:VC007
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Chemistry register: a diagonal bond clips the ''S'' as in VC002; counters open, S legible.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Chemistry register: a diagonal bond clips the ''S'' as in VC002; counters open,
    S legible.'
  candidate_refs:
  - VC007
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC008_S
  path: build/audit_crops/visual_clash/VC008_S.png
  source: visual_clash:VC008
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Chemistry register: bonds meet ''S'' shoulders with an upper-right near-touch; S legible.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Chemistry register: bonds meet ''S'' shoulders with an upper-right near-touch;
    S legible.'
  candidate_refs:
  - VC008
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC009_C
  path: build/audit_crops/visual_clash/VC009_C.png
  source: visual_clash:VC009
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Energy-diagram 'C' is clear; the neighbouring 'E'/'ob' fragments are frame-edge truncations
    of adjacent labels, not contact.
  observed_objects:
  - label 'C'
  - the stroke or fill flagged by the clash detector
  local_relationship: Energy-diagram 'C' is clear; the neighbouring 'E'/'ob' fragments are frame-edge
    truncations of adjacent labels, not contact.
  candidate_refs:
  - VC009
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC010_mobility
  path: build/audit_crops/visual_clash/VC010_mobility.png
  source: visual_clash:VC010
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: '''mobility'' is clear of any stroke; the dark-red Delta-E_t indicator arrow clashes with
    the adjacent word ''edge'' (VC011), not ''mobility''.'
  observed_objects:
  - label 'mobility'
  - the stroke or fill flagged by the clash detector
  local_relationship: '''mobility'' is clear of any stroke; the dark-red Delta-E_t indicator arrow clashes
    with the adjacent word ''edge'' (VC011), not ''mobility''.'
  candidate_refs:
  - VC010
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC011_edge
  path: build/audit_crops/visual_clash/VC011_edge.png
  source: visual_clash:VC011
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The dark-red Delta-E_t / mobility-edge indicator arrow runs between the 'd' and 'g' of 'edge';
    an energy-axis annotation arrow over its own label is conventional and 'edge' stays readable.
  observed_objects:
  - label 'edge'
  - the stroke or fill flagged by the clash detector
  local_relationship: The dark-red Delta-E_t / mobility-edge indicator arrow runs between the 'd' and
    'g' of 'edge'; an energy-axis annotation arrow over its own label is conventional and 'edge' stays
    readable.
  candidate_refs:
  - VC011
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC012_S
  path: build/audit_crops/visual_clash/VC012_S.png
  source: visual_clash:VC012
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Chemistry register near-miss: ''S'' clear; neighbouring atom node and digit fragment are
    frame cuts.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Chemistry register near-miss: ''S'' clear; neighbouring atom node and digit fragment
    are frame cuts.'
  candidate_refs:
  - VC012
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC013_shallow
  path: build/audit_crops/visual_clash/VC013_shallow.png
  source: visual_clash:VC013
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The dark-red trap-level reference line crosses 'shallow' in the inter-letter gap of the double-l;
    all letters readable; energy-level convention.
  observed_objects:
  - label 'shallow'
  - the stroke or fill flagged by the clash detector
  local_relationship: The dark-red trap-level reference line crosses 'shallow' in the inter-letter gap
    of the double-l; all letters readable; energy-level convention.
  candidate_refs:
  - VC013
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC014_S
  path: build/audit_crops/visual_clash/VC014_S.png
  source: visual_clash:VC014
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Chemistry register near-miss: ''S'' clear; neighbouring node/glyph fragments are frame cuts.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Chemistry register near-miss: ''S'' clear; neighbouring node/glyph fragments are
    frame cuts.'
  candidate_refs:
  - VC014
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC015_Sulfur-rich
  path: build/audit_crops/visual_clash/VC015_Sulfur-rich.png
  source: visual_clash:VC015
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: '''Sulfur-rich'' sits on clean white with no adjacent stroke; detector fired on background
    only.'
  observed_objects:
  - label 'Sulfur-rich'
  - the stroke or fill flagged by the clash detector
  local_relationship: '''Sulfur-rich'' sits on clean white with no adjacent stroke; detector fired on
    background only.'
  candidate_refs:
  - VC015
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC016_poly_S-r-DIB
  path: build/audit_crops/visual_clash/VC016_poly_S-r-DIB.png
  source: visual_clash:VC016
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: '''poly(S-r-DIB)'' sits on clean white with no adjacent stroke; fully legible.'
  observed_objects:
  - label 'poly(S-r-DIB)'
  - the stroke or fill flagged by the clash detector
  local_relationship: '''poly(S-r-DIB)'' sits on clean white with no adjacent stroke; fully legible.'
  candidate_refs:
  - VC016
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC017_Sulfur
  path: build/audit_crops/visual_clash/VC017_Sulfur.png
  source: visual_clash:VC017
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Axis label 'Sulfur' is clear; the faint tick above is separated; following 'co' is a frame
    cut.
  observed_objects:
  - label 'Sulfur'
  - the stroke or fill flagged by the clash detector
  local_relationship: Axis label 'Sulfur' is clear; the faint tick above is separated; following 'co'
    is a frame cut.
  candidate_refs:
  - VC017
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC018_wt
  path: build/audit_crops/visual_clash/VC018_wt.png
  source: visual_clash:VC018
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel-B axis label 'Sulfur content, wt%' sits adjacent to the Row-1.5 'convergent evidence'
    caption on a different baseline; both labels remain individually legible (tight but distinct).
  observed_objects:
  - label 'wt%'
  - the stroke or fill flagged by the clash detector
  local_relationship: Panel-B axis label 'Sulfur content, wt%' sits adjacent to the Row-1.5 'convergent
    evidence' caption on a different baseline; both labels remain individually legible (tight but distinct).
  candidate_refs:
  - VC018
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC019_convergent
  path: build/audit_crops/visual_clash/VC019_convergent.png
  source: visual_clash:VC019
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: '''convergent evidence'' caption sits just below-right of the ''wt%'' axis label; the two
    distinct labels crowd but each is legible; host re-inspection confirms separable baselines.'
  observed_objects:
  - label 'convergent'
  - the stroke or fill flagged by the clash detector
  local_relationship: '''convergent evidence'' caption sits just below-right of the ''wt%'' axis label;
    the two distinct labels crowd but each is legible; host re-inspection confirms separable baselines.'
  candidate_refs:
  - VC019
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC020_V
  path: build/audit_crops/visual_clash/VC020_V.png
  source: visual_clash:VC020
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Energy-axis 'V' (E_V region) glyph is clear; the bracketed 'E' fragment at left is a frame
    cut.
  observed_objects:
  - label 'V'
  - the stroke or fill flagged by the clash detector
  local_relationship: Energy-axis 'V' (E_V region) glyph is clear; the bracketed 'E' fragment at left
    is a frame cut.
  candidate_refs:
  - VC020
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC021_ISPD
  path: build/audit_crops/visual_clash/VC021_ISPD.png
  source: visual_clash:VC021
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: '''ISPD'' is the middle spoke''s modality label sitting on its own thin/light spoke line
    with the convergence arrowhead above; all four letters legible; intentional spoke geometry.'
  observed_objects:
  - label 'ISPD'
  - the stroke or fill flagged by the clash detector
  local_relationship: '''ISPD'' is the middle spoke''s modality label sitting on its own thin/light spoke
    line with the convergence arrowhead above; all four letters legible; intentional spoke geometry.'
  candidate_refs:
  - VC021
  - TB001
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC022_polymer
  path: build/audit_crops/visual_clash/VC022_polymer.png
  source: visual_clash:VC022
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: '''polymer'' callout: a leader attaches at the word''s right end and runs to the film-slab
    corner; host re-inspection confirms the leader does NOT cross the glyphs.'
  observed_objects:
  - label 'polymer'
  - the stroke or fill flagged by the clash detector
  local_relationship: '''polymer'' callout: a leader attaches at the word''s right end and runs to the
    film-slab corner; host re-inspection confirms the leader does NOT cross the glyphs.'
  candidate_refs:
  - VC022
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC023_film
  path: build/audit_crops/visual_clash/VC023_film.png
  source: visual_clash:VC023
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: '''film'' sits on an open tan gradient with ample clearance; no stroke crosses the glyphs.'
  observed_objects:
  - label 'film'
  - the stroke or fill flagged by the clash detector
  local_relationship: '''film'' sits on an open tan gradient with ample clearance; no stroke crosses the
    glyphs.'
  candidate_refs:
  - VC023
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC024_crop
  path: build/audit_crops/visual_clash/VC024_crop.png
  source: visual_clash:VC024
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Surface-charge marker: white ''+'' knockout on a maroon charge disc straddling the film-surface
    line; iconographic charge cue, legible.'
  observed_objects:
  - label '+'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Surface-charge marker: white ''+'' knockout on a maroon charge disc straddling
    the film-surface line; iconographic charge cue, legible.'
  candidate_refs:
  - VC024
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC025_crop
  path: build/audit_crops/visual_clash/VC025_crop.png
  source: visual_clash:VC025
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Surface-charge marker: white ''+'' knockout on a maroon charge disc on the surface boundary;
    iconographic charge cue, legible.'
  observed_objects:
  - label '+'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Surface-charge marker: white ''+'' knockout on a maroon charge disc on the surface
    boundary; iconographic charge cue, legible.'
  candidate_refs:
  - VC025
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC026_crop
  path: build/audit_crops/visual_clash/VC026_crop.png
  source: visual_clash:VC026
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Surface-charge marker: white ''+'' knockout on a maroon charge disc on the surface boundary;
    iconographic charge cue, legible.'
  observed_objects:
  - label '+'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Surface-charge marker: white ''+'' knockout on a maroon charge disc on the surface
    boundary; iconographic charge cue, legible.'
  candidate_refs:
  - VC026
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC027_crop
  path: build/audit_crops/visual_clash/VC027_crop.png
  source: visual_clash:VC027
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Surface-charge marker: white ''+'' knockout on a maroon charge disc on the block-top outline;
    iconographic charge cue, legible.'
  observed_objects:
  - label '+'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Surface-charge marker: white ''+'' knockout on a maroon charge disc on the block-top
    outline; iconographic charge cue, legible.'
  candidate_refs:
  - VC027
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC028_Vs
  path: build/audit_crops/visual_clash/VC028_Vs.png
  source: visual_clash:VC028
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: '''V_s'' display label sits fully inside the rounded meter-box outline with margin; host
    re-inspection confirms no glyph/backdrop overflows or is clipped (closes prior finding C002).'
  observed_objects:
  - label 'Vs'
  - the stroke or fill flagged by the clash detector
  local_relationship: '''V_s'' display label sits fully inside the rounded meter-box outline with margin;
    host re-inspection confirms no glyph/backdrop overflows or is clipped (closes prior finding C002).'
  candidate_refs:
  - VC028
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC029_meter
  path: build/audit_crops/visual_clash/VC029_meter.png
  source: visual_clash:VC029
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: '''meter'' display label sits fully inside the rounded meter-box outline; terminal ''r''
    has clear margin to the border; no overflow/clip (closes prior finding C002).'
  observed_objects:
  - label 'meter'
  - the stroke or fill flagged by the clash detector
  local_relationship: '''meter'' display label sits fully inside the rounded meter-box outline; terminal
    ''r'' has clear margin to the border; no overflow/clip (closes prior finding C002).'
  candidate_refs:
  - VC029
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC030_V
  path: build/audit_crops/visual_clash/VC030_V.png
  source: visual_clash:VC030
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Electrode-region 'V' glyph is clear within its panel field; horizontal panel outlines are
    separated from the glyph.
  observed_objects:
  - label 'V'
  - the stroke or fill flagged by the clash detector
  local_relationship: Electrode-region 'V' glyph is clear within its panel field; horizontal panel outlines
    are separated from the glyph.
  candidate_refs:
  - VC030
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC031_V
  path: build/audit_crops/visual_clash/VC031_V.png
  source: visual_clash:VC031
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: V_s(t)-axis 'V' label sits beside its axis; the axis line does not cross the glyph; conventional
    axis labelling.
  observed_objects:
  - label 'V'
  - the stroke or fill flagged by the clash detector
  local_relationship: V_s(t)-axis 'V' label sits beside its axis; the axis line does not cross the glyph;
    conventional axis labelling.
  candidate_refs:
  - VC031
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC032_t
  path: build/audit_crops/visual_clash/VC032_t.png
  source: visual_clash:VC032
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Math label ''(t)'': the parenthesis arcs are the symbol''s own brackets; they approach but
    do not strike the italic ''t''.'
  observed_objects:
  - label '(t)'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Math label ''(t)'': the parenthesis arcs are the symbol''s own brackets; they approach
    but do not strike the italic ''t''.'
  candidate_refs:
  - VC032
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC033_I_t
  path: build/audit_crops/visual_clash/VC033_I_t.png
  source: visual_clash:VC033
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: '''I(t) ~'' expression sits on clean white with full clearance; the corner wedge does not
    touch glyphs.'
  observed_objects:
  - label 'I(t)'
  - the stroke or fill flagged by the clash detector
  local_relationship: '''I(t) ~'' expression sits on clean white with full clearance; the corner wedge
    does not touch glyphs.'
  candidate_refs:
  - VC033
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC034_low
  path: build/audit_crops/visual_clash/VC034_low.png
  source: visual_clash:VC034
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Plot curve label 'low n' (navy) sits on its own navy power-law line; conventional curve labelling,
    legible.
  observed_objects:
  - label 'low'
  - the stroke or fill flagged by the clash detector
  local_relationship: Plot curve label 'low n' (navy) sits on its own navy power-law line; conventional
    curve labelling, legible.
  candidate_refs:
  - VC034
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC035_crop
  path: build/audit_crops/visual_clash/VC035_crop.png
  source: visual_clash:VC035
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The auto-crop window clipped the ')' glyph (mostly out of frame); the parenthesis belongs
    to the g(E_t)/(t) axis label and is legible in full context; crop-window artefact, not a figure defect.
  observed_objects:
  - label ')'
  - the stroke or fill flagged by the clash detector
  local_relationship: The auto-crop window clipped the ')' glyph (mostly out of frame); the parenthesis
    belongs to the g(E_t)/(t) axis label and is legible in full context; crop-window artefact, not a figure
    defect.
  candidate_refs:
  - VC035
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC036_hig
  path: build/audit_crops/visual_clash/VC036_hig.png
  source: visual_clash:VC036
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Rotated curve label 'high n' (maroon) sits along its maroon power-law line; the navy line
    skims the ascender tops as a near-miss; both labels legible.
  observed_objects:
  - label 'hig'
  - the stroke or fill flagged by the clash detector
  local_relationship: Rotated curve label 'high n' (maroon) sits along its maroon power-law line; the
    navy line skims the ascender tops as a near-miss; both labels legible.
  candidate_refs:
  - VC036
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC037_h
  path: build/audit_crops/visual_clash/VC037_h.png
  source: visual_clash:VC037
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: '''high n'' fragment ''h'' near the navy line; near-miss with white separation; legible.'
  observed_objects:
  - label 'h'
  - the stroke or fill flagged by the clash detector
  local_relationship: '''high n'' fragment ''h'' near the navy line; near-miss with white separation;
    legible.'
  candidate_refs:
  - VC037
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC038_n
  path: build/audit_crops/visual_clash/VC038_n.png
  source: visual_clash:VC038
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: '''high n'' subscript ''n'' sits in clear space below its line; near-miss only; legible.'
  observed_objects:
  - label 'n'
  - the stroke or fill flagged by the clash detector
  local_relationship: '''high n'' subscript ''n'' sits in clear space below its line; near-miss only;
    legible.'
  candidate_refs:
  - VC038
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC039_d
  path: build/audit_crops/visual_clash/VC039_d.png
  source: visual_clash:VC039
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Energy-axis 'd' glyph sits clear above the thin baseline rule; no contact.
  observed_objects:
  - label 'd'
  - the stroke or fill flagged by the clash detector
  local_relationship: Energy-axis 'd' glyph sits clear above the thin baseline rule; no contact.
  candidate_refs:
  - VC039
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC040_log
  path: build/audit_crops/visual_clash/VC040_log.png
  source: visual_clash:VC040
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Rotated axis label ''log I'': the ''g'' descender lands at the vertical axis line; conventional
    rotated axis label, legible.'
  observed_objects:
  - label 'log'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Rotated axis label ''log I'': the ''g'' descender lands at the vertical axis line;
    conventional rotated axis label, legible.'
  candidate_refs:
  - VC040
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC041_I
  path: build/audit_crops/visual_clash/VC041_I.png
  source: visual_clash:VC041
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Axis label 'I' near the vertical axis line with a thin white gap; near-miss, conventional
    axis labelling.
  observed_objects:
  - label 'I'
  - the stroke or fill flagged by the clash detector
  local_relationship: Axis label 'I' near the vertical axis line with a thin white gap; near-miss, conventional
    axis labelling.
  candidate_refs:
  - VC041
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC042_f
  path: build/audit_crops/visual_clash/VC042_f.png
  source: visual_clash:VC042
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: g(E_t)-region 'f' glyph sits clear on white; the thin top rule is separated.
  observed_objects:
  - label 'f'
  - the stroke or fill flagged by the clash detector
  local_relationship: g(E_t)-region 'f' glyph sits clear on white; the thin top rule is separated.
  candidate_refs:
  - VC042
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC043_HV
  path: build/audit_crops/visual_clash/VC043_HV.png
  source: visual_clash:VC043
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: '''HV+'' source-box label sits on white with clear space; the adjacent rounded box corner
    does not touch the glyphs.'
  observed_objects:
  - label 'HV+'
  - the stroke or fill flagged by the clash detector
  local_relationship: '''HV+'' source-box label sits on white with clear space; the adjacent rounded box
    corner does not touch the glyphs.'
  candidate_refs:
  - VC043
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are
    present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: full_q1
  path: build/audit_crops/full_q1.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Row-1 chemistry+composition: the S8 ring leads via a dashed arrow into the backbone (a);
    three labelled chains stack over the wt% axis (b); the ''convergent'' caption tucks below-right.'
  observed_objects:
  - panel a/b letters
  - '''inverse vulcanization'' text'
  - -(S)x- formula
  - S8 sulfur ring
  - dashed leader arrow
  - benzene-ring backbone
  - three S60/S75/S85 zig-zag chains
  - '''Sulfur content, wt%'' axis arrow'
  - '''convergent'' caption'
  - partial 'ISP'
  local_relationship: 'Row-1 chemistry+composition: the S8 ring leads via a dashed arrow into the backbone
    (a); three labelled chains stack over the wt% axis (b); the ''convergent'' caption tucks below-right.'
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host: the dashed inverse-vulcanization leader lands cleanly on the backbone; ''convergent''
    sits adjacent to the wt% axis label but both stay legible (see VC018/VC019); no stray mark.'
  anomaly_link: ''
- crop_id: full_q2
  path: build/audit_crops/full_q2.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Panel C model: the real-space film (left) is bound by dashed leaders to the energy diagram
    (right); shallow (blue) sits below the mobility edge, deep (red) near E_V, with Delta-E_t spanning.'
  observed_objects:
  - panel c + titles (real space / energy diagram / localized traps)
  - tan film box with wavy chains and blue+red dots
  - '''d ~ 1 um'''
  - dashed leaders
  - blue shallow gaussian + level lines + dot
  - red deep gaussian + level lines + dot
  - vertical 'Energy' axis
  - vacuum/E_C/mobility-edge lines
  - shallow/deep labels
  - dashed red leader arrow
  - Delta-E_t double arrow
  - E_V
  local_relationship: 'Panel C model: the real-space film (left) is bound by dashed leaders to the energy
    diagram (right); shallow (blue) sits below the mobility edge, deep (red) near E_V, with Delta-E_t
    spanning.'
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host re-inspection at 6x: the mark the screen flagged as a ''floating caret'' above
    the upper blue level is the ARROWHEAD of an intended dashed red leader arrow (a dashed tail descends
    to the lower-left) that binds a trap site to its energy level. Not a stray glyph.'
  anomaly_link: ''
- crop_id: full_q3
  path: build/audit_crops/full_q3.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Panel D kinetic plot: navy ''low n'' (shallower) and red ''high n'' (steeper) power laws
    emerge from a shared origin with the dashed Debye crossing; each label sits on its own line.'
  observed_objects:
  - panel d + 'kinetic'
  - '''MIM stack'''
  - SMU V/A box
  - polymer-film box + ground
  - I(t)~t^-n formula
  - log-log axes (log I / log t)
  - navy 'low n' power-law + dots
  - red 'high n' power-law + dots
  - dashed Debye line
  - partial panel e
  local_relationship: 'Panel D kinetic plot: navy ''low n'' (shallower) and red ''high n'' (steeper) power
    laws emerge from a shared origin with the dashed Debye crossing; each label sits on its own line.'
  candidate_refs:
  - TB001
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host re-inspection: ''low n''/''high n'' labels are colour-matched to their own
    power-law lines (plot convention); the power-law tails stay above the steep dashed Debye at long times
    (TG-D-001); no stray mark.'
  anomaly_link: ''
- crop_id: full_q4
  path: build/audit_crops/full_q4.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Panel F mechanical: V_active wires to the vertical electrode; the clamped cantilever bends
    left carrying q_tr charges; the red Coulomb arrow points left; the air-gap caliper spans the base.'
  observed_objects:
  - partial probe / V_s meter box
  - sample stack + '+' marker + ground
  - panel f + 'mechanical'
  - V_active pulse box
  - clamp + cantilever + three q_tr dots
  - q_tr leader label
  - red Coulomb-repulsion arrow
  - electrode bar + ground
  - rotated 'electrode' label
  - air-gap caliper
  - partial g(E_t)
  local_relationship: 'Panel F mechanical: V_active wires to the vertical electrode; the clamped cantilever
    bends left carrying q_tr charges; the red Coulomb arrow points left; the air-gap caliper spans the
    base.'
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host re-inspection at 5x: the V_active lead routes cleanly to the electrode top;
    the rotated ''electrode'' label sits in the right margin clear of the bar; the Coulomb arrowhead is
    clear of its label; no stray mark.'
  anomaly_link: ''
- crop_id: panel_D_q1
  path: build/audit_crops/panel_D_q1.png
  source: panel:D
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: SMU box (left) links via two right-angle wires to contact dots on the amber MIM stack.
  observed_objects:
  - '''d'' letter'
  - '''MIM stack'' title'
  - SMU V/A box + highlight + shadow
  - two right-angle wires + contact dots
  - hatched top electrode
  - amber film 'poly'
  - partial 'kine' header
  local_relationship: SMU box (left) links via two right-angle wires to contact dots on the amber MIM
    stack.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Wires terminate on the dots cleanly; edge cuts are normal tiling; no stray geometry.
  anomaly_link: ''
- crop_id: panel_D_q2
  path: build/audit_crops/panel_D_q2.png
  source: panel:D
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The stack's lower contact dot is wired down to a ground symbol.
  observed_objects:
  - '''etic'' header'
  - hatched electrodes
  - amber film 'ymer film'
  - contact dot
  - ground wire + ground symbol
  local_relationship: The stack's lower contact dot is wired down to a ground symbol.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Ground wire runs cleanly to the bars; no stray mark.
  anomaly_link: ''
- crop_id: panel_D_q3
  path: build/audit_crops/panel_D_q3.png
  source: panel:D
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Axis at left; navy and maroon curves fan from a shared origin dot with the dashed Debye crossing;
    'low n' upper-right.
  observed_objects:
  - I(t) formula
  - vertical axis + 'log I'
  - ticks
  - origin dot
  - dashed Debye line
  - navy curve + dots
  - maroon curve + dots
  - '''low n'' label'
  local_relationship: Axis at left; navy and maroon curves fan from a shared origin dot with the dashed
    Debye crossing; 'low n' upper-right.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host: the dashed Debye and navy curve pass beneath ''low n'' without striking the
    glyph strokes; labels colour-match their lines (convention).'
  anomaly_link: ''
- crop_id: panel_D_q4
  path: build/audit_crops/panel_D_q4.png
  source: panel:D
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: '''high n'' label sits above the curves; the navy line is nearest in this tile because the
    two lines converge here.'
  observed_objects:
  - '''high n'' label'
  - navy curve + dots
  - maroon curve + dot
  local_relationship: '''high n'' label sits above the curves; the navy line is nearest in this tile because
    the two lines converge here.'
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host: ''high n'' (maroon) is colour-matched to the maroon steep line; the navy line
    merely passes nearby where the lines are close; glyphs intact (convention).'
  anomaly_link: ''
- crop_id: panel_D_s01
  path: build/audit_crops/panel_D_s01.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel letter under the border with the title beginning.
  observed_objects:
  - '''d'' letter'
  - '''MIM stack'' fragment'
  - border
  local_relationship: Panel letter under the border with the title beginning.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Clean glyphs; no stray geometry.
  anomaly_link: ''
- crop_id: panel_D_s02
  path: build/audit_crops/panel_D_s02.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Header under the border; a vertical divider rule at the top-right.
  observed_objects:
  - border
  - vertical divider rule
  - '''kine'' header'
  - small stroke fragment
  local_relationship: Header under the border; a vertical divider rule at the top-right.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Divider and edge-cut fragment are normal; no stray mark.
  anomaly_link: ''
- crop_id: panel_D_s03
  path: build/audit_crops/panel_D_s03.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Header fragment under the border.
  observed_objects:
  - border
  - '''etic'' header'
  local_relationship: Header fragment under the border.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Edge-cut header; clean.
  anomaly_link: ''
- crop_id: panel_D_s04
  path: build/audit_crops/panel_D_s04.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Near-blank tile with a faint border.
  observed_objects:
  - border line
  local_relationship: Near-blank tile with a faint border.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Blank apart from the border; nothing to evaluate.
  anomaly_link: ''
- crop_id: panel_D_s05
  path: build/audit_crops/panel_D_s05.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The SMU box fills the tile with its glyphs centred.
  observed_objects:
  - SMU box
  - SMU / V/A glyphs
  - highlight
  - shadow
  - I(t) fragment
  local_relationship: The SMU box fills the tile with its glyphs centred.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Box, glyphs, highlight, shadow clean; formula fragment is an edge cut.
  anomaly_link: ''
- crop_id: panel_D_s06
  path: build/audit_crops/panel_D_s06.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Two wires leave the SMU box to contact dots on the stack; the lower wire shows a small hop
    near its dot.
  observed_objects:
  - SMU box right edge
  - two wires
  - contact dots
  - hatched electrode
  - amber 'poly'
  - small loop on lower wire
  local_relationship: Two wires leave the SMU box to contact dots on the stack; the lower wire shows a
    small hop near its dot.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host: the small loop on the lower SMU wire is a conventional wire-hop/turn detail;
    tiny and legible, it does not affect the schematic (NIT, not a defect).'
  anomaly_link: ''
- crop_id: panel_D_s07
  path: build/audit_crops/panel_D_s07.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The amber film with its label sits between the hatched electrodes.
  observed_objects:
  - hatched electrodes
  - amber film 'ymer film'
  - thin amber border
  local_relationship: The amber film with its label sits between the hatched electrodes.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Hatching regular, label intact; no stray geometry.
  anomaly_link: ''
- crop_id: panel_D_s08
  path: build/audit_crops/panel_D_s08.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: A contact dot on the stack's lower edge is wired to the ground symbol.
  observed_objects:
  - hatched electrode edge
  - amber outline
  - contact dot
  - ground wire
  - ground symbol
  local_relationship: A contact dot on the stack's lower edge is wired to the ground symbol.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Wire runs cleanly to evenly-spaced ground bars; no stray mark.
  anomaly_link: ''
- crop_id: panel_D_s09
  path: build/audit_crops/panel_D_s09.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The axis and label sit left; both curves originate at a shared dot with the dashed line beginning
    between them.
  observed_objects:
  - I(t) fragment
  - axis + 'log I'
  - origin dot
  - navy/maroon curve starts
  - dashed-line start
  local_relationship: The axis and label sit left; both curves originate at a shared dot with the dashed
    line beginning between them.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Curves originate cleanly at the shared dot; no stray strokes.
  anomaly_link: ''
- crop_id: panel_D_s10
  path: build/audit_crops/panel_D_s10.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The dashed line runs just beneath 'low n'; a navy data dot overlaps a dashed segment.
  observed_objects:
  - dashed Debye segments
  - '''low n'' label'
  - navy curve + dot
  local_relationship: The dashed line runs just beneath 'low n'; a navy data dot overlaps a dashed segment.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host: dashes pass under the glyphs without striking them and a data dot sits on
    a dashed segment (near-miss / stacked convention); legible.'
  anomaly_link: ''
- crop_id: panel_D_s11
  path: build/audit_crops/panel_D_s11.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Edge-cut curve fragments enter the corner; the rest is empty.
  observed_objects:
  - maroon curve fragment
  - navy curve fragment + dot
  local_relationship: Edge-cut curve fragments enter the corner; the rest is empty.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Normal tiling cuts; no stray geometry.
  anomaly_link: ''
- crop_id: panel_D_s12
  path: build/audit_crops/panel_D_s12.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Empty white sub-quadrant with no drawn elements in this tile.
  observed_objects:
  - white background only (blank tile)
  local_relationship: Empty white sub-quadrant with no drawn elements in this tile.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No marks present to evaluate.
  anomaly_link: ''
- crop_id: panel_D_s13
  path: build/audit_crops/panel_D_s13.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: A vertical axis line with ticks projecting right.
  observed_objects:
  - vertical axis line
  - two ticks
  local_relationship: A vertical axis line with ticks projecting right.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Ticks attach cleanly to the axis; no stray strokes.
  anomaly_link: ''
- crop_id: panel_D_s14
  path: build/audit_crops/panel_D_s14.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The maroon curve crosses the dashed line with a data dot at the intersection.
  observed_objects:
  - maroon curve
  - maroon dot at crossing
  - dashed Debye segments
  - exponent fragment
  local_relationship: The maroon curve crosses the dashed line with a data dot at the intersection.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: A data point at a curve/reference crossing is normal plot geometry; dashes even;
    no stray mark.
  anomaly_link: ''
- crop_id: panel_D_s15
  path: build/audit_crops/panel_D_s15.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: '''high n'' sits upper-left; the navy line is nearest in this tile while the maroon line
    runs lower.'
  observed_objects:
  - '''high n'' label + subscript'
  - navy curve + dot
  - maroon curve + dot
  local_relationship: '''high n'' sits upper-left; the navy line is nearest in this tile while the maroon
    line runs lower.'
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host: colour-match is correct (maroon label to maroon line); glyphs intact; convention
    call, not a defect.'
  anomaly_link: ''
- crop_id: panel_D_s16
  path: build/audit_crops/panel_D_s16.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: An edge-cut navy segment enters the corner.
  observed_objects:
  - navy curve fragment + dot
  local_relationship: An edge-cut navy segment enters the corner.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Normal tiling cut; no stray geometry.
  anomaly_link: ''
- crop_id: panel_E_q1
  path: build/audit_crops/panel_E_q1.png
  source: panel:E
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: HV+ box upper-left; the corona needle drops to the polymer surface with '+' markers; the
    'polymer' label leads to the slab corner.
  observed_objects:
  - '''e'' letter'
  - ISP fragment
  - HV+ label
  - source box + dot
  - corona needle + wire
  - tan polymer slab
  - grey substrate
  - three '+' charge markers
  - '''polymer'' label + leader'
  - '''V_s p'' fragment'
  - probe disk-on-shaft fragment
  local_relationship: HV+ box upper-left; the corona needle drops to the polymer surface with '+' markers;
    the 'polymer' label leads to the slab corner.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host re-inspection at 6x: the corona-needle wire is well right of the HV+ glyphs
    (no crossing); the probe is a disk-on-shaft with NO vibration arcs (induction-type, correct); the
    ''polymer'' leader attaches at the word''s right end and runs to the slab — it does NOT cross the
    ''e''/''r'' glyphs (the screen flag was an upscaled-tile false positive).'
  anomaly_link: ''
- crop_id: panel_E_q2
  path: build/audit_crops/panel_E_q2.png
  source: panel:E
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: A leader runs to a dot on the meter-box edge; the meter box is centre-right; the ground symbol
    sits lower-left.
  observed_objects:
  - '''D'' fragment'
  - '''probe'' fragment'
  - leader + dot
  - V_s meter box
  - '''V_s meter'' label'
  - grey bar
  - '''+'' marker'
  - substrate
  - ground wire + symbol
  local_relationship: A leader runs to a dot on the meter-box edge; the meter box is centre-right; the
    ground symbol sits lower-left.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host: ''V_s meter'' sits fully inside the bezel (no clip/overflow, closing prior
    C002); the leader ends at the box edge without crossing the label.'
  anomaly_link: ''
- crop_id: panel_E_q3
  path: build/audit_crops/panel_E_q3.png
  source: panel:E
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: An upper decay plot sits over the lower g(E_t) plot; the tau_d caliper spans between the
    two gaussian peaks.
  observed_objects:
  - '''V_s(t)'' axis label'
  - axis + ticks + arrow
  - start dot
  - maroon decay curve
  - three sphere markers
  - '''g(E_t)'' axis label'
  - lower axis
  - '''tau_d'' caliper'
  - blue gaussian
  - red gaussian + marker
  local_relationship: An upper decay plot sits over the lower g(E_t) plot; the tau_d caliper spans between
    the two gaussian peaks.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Axis labels sit clear of their lines; markers sit on the curve/peaks; no stray mark.
  anomaly_link: ''
- crop_id: panel_E_q4
  path: build/audit_crops/panel_E_q4.png
  source: panel:E
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The time axis terminates in an arrowhead labelled 't'; the 'derive' arrow links the two plots.
  observed_objects:
  - red gaussian flank + marker
  - down 'derive' arrow
  - '''derive'' word'
  - time axis + arrowhead
  - '''t'' label'
  local_relationship: The time axis terminates in an arrowhead labelled 't'; the 'derive' arrow links
    the two plots.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: '''derive'' sits clear of the arrow and axis; clean.'
  anomaly_link: ''
- crop_id: panel_E_s01
  path: build/audit_crops/panel_E_s01.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel letter 'e' and 'HV+' below the rule.
  observed_objects:
  - rule
  - '''e'' letter'
  - HV+ label
  - box corner
  local_relationship: Panel letter 'e' and 'HV+' below the rule.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: No wire crosses the HV+ glyphs here; box corner is an edge cut.
  anomaly_link: ''
- crop_id: panel_E_s02
  path: build/audit_crops/panel_E_s02.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The source box with the needle descending on a thin wire.
  observed_objects:
  - ISP fragment
  - rule
  - source box + dot
  - corona needle + wire + bead
  - '''V_s p'' fragment'
  local_relationship: The source box with the needle descending on a thin wire.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: The needle wire descends from the box centre, clear of labels; clean.
  anomaly_link: ''
- crop_id: panel_E_s03
  path: build/audit_crops/panel_E_s03.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: A leader descends to a dot at the meter-box corner; 'probe' sits above the line.
  observed_objects:
  - '''D'' fragment'
  - rule
  - '''probe'' fragment'
  - leader + dot
  - meter-box corner
  - grey bar
  local_relationship: A leader descends to a dot at the meter-box corner; 'probe' sits above the line.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: The leader runs below 'probe' without crossing it; clean.
  anomaly_link: ''
- crop_id: panel_E_s04
  path: build/audit_crops/panel_E_s04.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Near-blank tile; only the meter-box corner enters at lower-left.
  observed_objects:
  - rule
  - meter-box corner
  local_relationship: Near-blank tile; only the meter-box corner enters at lower-left.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Box corner is a normal edge cut; otherwise empty.
  anomaly_link: ''
- crop_id: panel_E_s05
  path: build/audit_crops/panel_E_s05.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: '''polymer'' with a leader continuing to the slab off-tile.'
  observed_objects:
  - '''polymer'' word'
  - leader line
  local_relationship: '''polymer'' with a leader continuing to the slab off-tile.'
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host: the leader starts at the word''s right end and runs to the slab — it does
    NOT cross the ''e''/''r'' glyphs (confirmed against the parent render); the screen ''present'' flag
    was an upscaled-tile artefact.'
  anomaly_link: ''
- crop_id: panel_E_s06
  path: build/audit_crops/panel_E_s06.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The needle tip points at the slab where the '+' markers sit on the surface.
  observed_objects:
  - needle tip
  - corona spray
  - polymer slab
  - substrate
  - three '+' markers
  - leader anchor dot
  local_relationship: The needle tip points at the slab where the '+' markers sit on the surface.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: The '+' markers sit on the surface; the black dot is the leader anchor (not stray);
    no vibration arcs; clean.
  anomaly_link: ''
- crop_id: panel_E_s07
  path: build/audit_crops/panel_E_s07.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The grounded substrate is wired down to a ground symbol; a meter-label fragment at the right.
  observed_objects:
  - grey box fragment
  - '''+'' marker'
  - polymer slab corner
  - substrate
  - ground wire + symbol
  - '''V_s m'' fragment'
  local_relationship: The grounded substrate is wired down to a ground symbol; a meter-label fragment
    at the right.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Ground wire routes cleanly without crossing labels; clean.
  anomaly_link: ''
- crop_id: panel_E_s08
  path: build/audit_crops/panel_E_s08.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The lower-right of the meter box with the trailing 'eter'.
  observed_objects:
  - '''eter'' fragment'
  - meter-box corner
  local_relationship: The lower-right of the meter box with the trailing 'eter'.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: '''eter'' sits inside the bezel, not clipped; clean.'
  anomaly_link: ''
- crop_id: panel_E_s09
  path: build/audit_crops/panel_E_s09.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The y-axis rises with its label left; the decay curve starts at a dot and falls right.
  observed_objects:
  - '''V_s(t)'' axis label'
  - axis + arrow
  - ticks
  - start dot
  - decay-curve top + sphere
  local_relationship: The y-axis rises with its label left; the decay curve starts at a dot and falls
    right.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Label sits left of the axis; curve and marker intact; clean.
  anomaly_link: ''
- crop_id: panel_E_s10
  path: build/audit_crops/panel_E_s10.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: A descending curve through two markers.
  observed_objects:
  - decay curve
  - two spheres
  local_relationship: A descending curve through two markers.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Spheres sit on the curve; otherwise empty; clean.
  anomaly_link: ''
- crop_id: panel_E_s11
  path: build/audit_crops/panel_E_s11.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Empty white sub-quadrant with no drawn elements in this tile.
  observed_objects:
  - white background only (blank tile)
  local_relationship: Empty white sub-quadrant with no drawn elements in this tile.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Empty; no marks to evaluate.
  anomaly_link: ''
- crop_id: panel_E_s12
  path: build/audit_crops/panel_E_s12.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Empty white sub-quadrant with no drawn elements in this tile.
  observed_objects:
  - white background only (blank tile)
  local_relationship: Empty white sub-quadrant with no drawn elements in this tile.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Empty; no marks to evaluate.
  anomaly_link: ''
- crop_id: panel_E_s13
  path: build/audit_crops/panel_E_s13.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The g(E_t) axis rises with its label left; the blue peak enters lower-right.
  observed_objects:
  - '''g(E_t)'' axis label'
  - lower axis + arrow
  - tick
  - frame line
  - blue gaussian fragment
  local_relationship: The g(E_t) axis rises with its label left; the blue peak enters lower-right.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Label sits left of the axis; blue peak entering is an edge cut; clean.
  anomaly_link: ''
- crop_id: panel_E_s14
  path: build/audit_crops/panel_E_s14.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The tau_d caliper bar spans between the two gaussian peaks.
  observed_objects:
  - decay tail + sphere + tick
  - axis fragment
  - '''tau_d'' label'
  - caliper bar + end ticks
  - blue gaussian fragment
  - red gaussian + two spheres
  local_relationship: The tau_d caliper bar spans between the two gaussian peaks.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: '''tau_d'' sits above the bar (no glyph-on-line overlap); peaks at edges are tile
    cuts; clean.'
  anomaly_link: ''
- crop_id: panel_E_s15
  path: build/audit_crops/panel_E_s15.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The 'derive' arrow points down to the g(E_t) gaussian; 'derive' sits to its right.
  observed_objects:
  - axis fragment + tick
  - down 'derive' arrow
  - '''derive'' word'
  - red gaussian flank + sphere
  local_relationship: The 'derive' arrow points down to the g(E_t) gaussian; 'derive' sits to its right.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: '''derive'' is clear of the arrow and the line above; clean.'
  anomaly_link: ''
- crop_id: panel_E_s16
  path: build/audit_crops/panel_E_s16.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The time axis terminates at an arrowhead with the 't' label below.
  observed_objects:
  - time axis + arrowhead
  - '''t'' label'
  local_relationship: The time axis terminates at an arrowhead with the 't' label below.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Label clear of the arrowhead; otherwise empty; clean.
  anomaly_link: ''
- crop_id: panel_F_q1
  path: build/audit_crops/panel_F_q1.png
  source: panel:F
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel tag and title fragment along the top; the rest is empty.
  observed_objects:
  - '''f'' letter'
  - '''mecha'' fragment'
  - vertical rule stub
  - horizontal rule
  local_relationship: Panel tag and title fragment along the top; the rest is empty.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Single clean glyphs; the vertical stub is a tile-edge cut; no stray geometry.
  anomaly_link: ''
- crop_id: panel_F_q2
  path: build/audit_crops/panel_F_q2.png
  source: panel:F
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The V_active box sits lower-left with the pulse glyph above its label; a node dot launches
    a lead to the right.
  observed_objects:
  - '''nical'' fragment'
  - panel border corner
  - V_active box
  - internal pulse glyph
  - '''V_active'' label'
  - node dot
  - lead
  local_relationship: The V_active box sits lower-left with the pulse glyph above its label; a node dot
    launches a lead to the right.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: The square-pulse glyph is contained inside its inner frame; the label is within the
    box outline; clean.
  anomaly_link: ''
- crop_id: panel_F_q3
  path: build/audit_crops/panel_F_q3.png
  source: panel:F
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: '''Coulomb/repulsion'' at left; the red arrow points left from the beam; the beam with charges
    runs down the right.'
  observed_objects:
  - '''Coulomb'' / ''repulsion'' text'
  - red left arrow
  - tan cantilever beam
  - three q_tr dots
  - faint gray Maxwell baseline
  - beam outline
  - bent stroke fragment
  local_relationship: '''Coulomb/repulsion'' at left; the red arrow points left from the beam; the beam
    with charges runs down the right.'
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host re-inspection at 5x: the ''black vertical stroke crossing the red arrow'' is
    the cantilever beam''s own outline at the arrow tail — the Coulomb arrow emanates from a q_tr charge
    on the beam (force on charge), so passing the beam edge is expected; the arrowhead is clear of the
    label; the faint gray line is the lower-tier F_Maxwell baseline (TG-G-002). No stray geometry.'
  anomaly_link: ''
- crop_id: panel_F_q4
  path: build/audit_crops/panel_F_q4.png
  source: panel:F
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The mount/clamp hold the beam; a q_tr leader points to a charge; the electrode bar at right
    carries the rotated label.
  observed_objects:
  - hatched mount
  - clamp block
  - cantilever + charges
  - '''q_tr'' label + leader'
  - electrode bar + cap + hatch ticks
  - rotated 'electrode' label
  local_relationship: The mount/clamp hold the beam; a q_tr leader points to a charge; the electrode bar
    at right carries the rotated label.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: The rotated 'electrode' label sits in the right margin clear of the bar (no collision/overflow);
    the q_tr leader connects to a charge dot; clean.
  anomaly_link: ''
- crop_id: panel_F_s01
  path: build/audit_crops/panel_F_s01.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The panel tag below a thin rule.
  observed_objects:
  - '''f'' letter'
  - horizontal rule
  local_relationship: The panel tag below a thin rule.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Single clean glyph; the rule is a normal divider; nothing to collide.
  anomaly_link: ''
- crop_id: panel_F_s02
  path: build/audit_crops/panel_F_s02.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: A title fragment below the rule with a vertical stub at the top-right.
  observed_objects:
  - '''mecha'' fragment'
  - vertical rule stub
  - horizontal rule
  local_relationship: A title fragment below the rule with a vertical stub at the top-right.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Edge-cut text and rules; no stray geometry.
  anomaly_link: ''
- crop_id: panel_F_s03
  path: build/audit_crops/panel_F_s03.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The title fragment at upper-left; the box top line at the bottom edge.
  observed_objects:
  - '''nical'' fragment'
  - rule
  - V_active box top edge
  local_relationship: The title fragment at upper-left; the box top line at the bottom edge.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Title completes cleanly; the box-top line is an edge cut; no stray mark.
  anomaly_link: ''
- crop_id: panel_F_s04
  path: build/audit_crops/panel_F_s04.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The rounded panel-frame corner continuing as a vertical edge.
  observed_objects:
  - panel border corner
  - vertical border
  local_relationship: The rounded panel-frame corner continuing as a vertical edge.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Only the panel border, cut by tile edges (normal); nothing to collide.
  anomaly_link: ''
- crop_id: panel_F_s05
  path: build/audit_crops/panel_F_s05.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Empty white sub-quadrant with no drawn elements in this tile.
  observed_objects:
  - white background only (blank tile)
  local_relationship: Empty white sub-quadrant with no drawn elements in this tile.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Uniformly white; no marks to evaluate.
  anomaly_link: ''
- crop_id: panel_F_s06
  path: build/audit_crops/panel_F_s06.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Near-blank tile with a faint edge line at the right.
  observed_objects:
  - vertical rule stub
  local_relationship: Near-blank tile with a faint edge line at the right.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Only a faint edge-cut vertical line; no content.
  anomaly_link: ''
- crop_id: panel_F_s07
  path: build/audit_crops/panel_F_s07.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The V_active box with the pulse glyph above its label; a node dot starts a lead.
  observed_objects:
  - V_active box
  - internal pulse glyph
  - '''V_active'' label'
  - node dot
  - lead
  local_relationship: The V_active box with the pulse glyph above its label; a node dot starts a lead.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: The pulse glyph is inside its inner frame; the label is within the box; the soft
    shadow is uniform; clean.
  anomaly_link: ''
- crop_id: panel_F_s08
  path: build/audit_crops/panel_F_s08.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The V_active output lead makes a right-angle turn.
  observed_objects:
  - right-angle black lead
  - vertical border
  local_relationship: The V_active output lead makes a right-angle turn.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: A continuous lead with a clean turn, cut at tile edges; no doubled strokes.
  anomaly_link: ''
- crop_id: panel_F_s09
  path: build/audit_crops/panel_F_s09.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Empty white sub-quadrant with no drawn elements in this tile.
  observed_objects:
  - white background only (blank tile)
  local_relationship: Empty white sub-quadrant with no drawn elements in this tile.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Uniformly white; no content.
  anomaly_link: ''
- crop_id: panel_F_s10
  path: build/audit_crops/panel_F_s10.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: A bent stroke at the top-right; a charge-dot fragment at the bottom-right.
  observed_objects:
  - bent black stroke
  - partial charge dot + stem
  local_relationship: A bent stroke at the top-right; a charge-dot fragment at the bottom-right.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host: the bent stroke is the Maxwell-baseline / upper-lead routing corner running
    off-tile (connected in the parent render); edge cut, not stray.'
  anomaly_link: ''
- crop_id: panel_F_s11
  path: build/audit_crops/panel_F_s11.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Mount to clamp to beam; a q_tr leader runs to a charge dot on the beam.
  observed_objects:
  - hatched mount
  - stem
  - clamp block
  - cantilever + striations
  - charge dot
  - '''q_tr'' leader + label'
  local_relationship: Mount to clamp to beam; a q_tr leader runs to a charge dot on the beam.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: The leader meets the dot (properly attached); clamp connections continuous; no stray
    strokes.
  anomaly_link: ''
- crop_id: panel_F_s12
  path: build/audit_crops/panel_F_s12.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The electrode bar with a lead into its top and ground at its base.
  observed_objects:
  - electrode bar + cap + highlight
  - lead into top
  - hatch ticks
  - ground symbol
  - vertical border
  local_relationship: The electrode bar with a lead into its top and ground at its base.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: The ground glyph sits at the electrode foot; cap, lead and ticks connected; clean.
  anomaly_link: ''
- crop_id: panel_F_s13
  path: build/audit_crops/panel_F_s13.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The two-line 'Coulomb / repulsion' label in the upper-left.
  observed_objects:
  - '''Coulomb'' text'
  - '''repulsion'' text'
  local_relationship: The two-line 'Coulomb / repulsion' label in the upper-left.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Clean unbroken glyphs; no nearby lines to collide; no stray marks.
  anomaly_link: ''
- crop_id: panel_F_s14
  path: build/audit_crops/panel_F_s14.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The red arrow spans from its tail on the beam left toward the off-tile label; the beam with
    charges is at right.
  observed_objects:
  - red left arrow
  - tan cantilever beam
  - two q_tr dots
  - faint gray Maxwell baseline
  - beam outline
  - red 'C' fragment
  local_relationship: The red arrow spans from its tail on the beam left toward the off-tile label; the
    beam with charges is at right.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host: as in q3, the line crossing the red arrow is the beam outline at the force-on-charge
    tail; the arrowhead ends in open space; the faint gray line is the Maxwell baseline. No defect.'
  anomaly_link: ''
- crop_id: panel_F_s15
  path: build/audit_crops/panel_F_s15.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The beam's lower tip with its gray baseline companion and a partial charge dot.
  observed_objects:
  - cantilever tip
  - striations
  - faint gray baseline
  - partial charge dot
  local_relationship: The beam's lower tip with its gray baseline companion and a partial charge dot.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: Edge-cut continuations (normal tiling); no floating marks.
  anomaly_link: ''
- crop_id: panel_F_s16
  path: build/audit_crops/panel_F_s16.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The electrode bar with hatch ticks; the rotated 'electrode' label fragment in the right margin.
  observed_objects:
  - electrode bar + highlight
  - hatch ticks
  - rotated 'ectrode' fragment
  - vertical border
  local_relationship: The electrode bar with hatch ticks; the rotated 'electrode' label fragment in the
    right margin.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: The label sits in the margin clear of the bar (no collision/overflow); the fragment
    is a normal edge cut; clean.
  anomaly_link: ''
- crop_id: print_178mm
  path: build/audit_crops/print_178mm.png
  source: print_scale
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Two-row six-panel mosaic (a/b/c over d/e/f) with the central ISPD / convergent-evidence connector;
    panel dividers stay distinct.
  observed_objects:
  - full six-panel layout at 178 mm-equivalent proxy
  local_relationship: Two-row six-panel mosaic (a/b/c over d/e/f) with the central ISPD / convergent-evidence
    connector; panel dividers stay distinct.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: 'At the 178 mm manuscript-width proxy all labels stay legible: S60/S75/S85 subscripts
    separate, the Panel-C blue/red gaussians stay distinct from the level lines, and ''convergent evidence''
    is readable; the centre of Panel C is dense but nothing collapses.'
  anomaly_link: ''
- crop_id: print_thumbnail
  path: build/audit_crops/print_thumbnail.png
  source: print_scale
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: The six colour-coded panel blocks and the two-row structure remain discernible; fine text
    and thin leaders fall toward sub-pixel.
  observed_objects:
  - whole figure at thumbnail scale
  local_relationship: The six colour-coded panel blocks and the two-row structure remain discernible;
    fine text and thin leaders fall toward sub-pixel.
  candidate_refs: []
  unintended_visible_anomaly: none
  anomaly_rationale: 'Thumbnail proxy: fine labels and thin leaders soften toward sub-pixel as expected
    at extreme reduction; this is universal thumbnail behaviour, not an artefact of this figure. journal_polish/publication_readiness
    are judged at the operative 178 mm proxy (print_178mm), which stays legible.'
  anomaly_link: ''
panels:
- id: D
  findings:
  - id: P001
    severity: MINOR
    category: style
    tex_lines:
    - 820
    - 980
    observation: Panel D SMU + MIM + I(t) plot is an iconic-cartoon abstraction of the kinetic measurement
      rather than a literal instrument rendering.
    suggested_fix: accept_simplification - iconic-cartoon register is the briefing 3.2 intent for Row
      2 evidence panels.
    status: open
- id: E
  findings:
  - id: P002
    severity: MINOR
    category: style
    tex_lines:
    - 1207
    - 1460
    observation: Panel E corona/ISPD apparatus is an iconic abstraction of the surface-charge measurement
      (induction-type probe), not a literal instrument.
    suggested_fix: accept_simplification - iconic abstraction is briefing 3.2 intent; induction-probe
      convention is correct.
    status: open
- id: F
  findings:
  - id: P003
    severity: MINOR
    category: style
    tex_lines:
    - 1146
    - 1320
    observation: Panel F cantilever + electrode + air gap is an iconic abstraction; Coulomb-wins-Maxwell
      weight asymmetry is preserved.
    suggested_fix: accept_simplification - actuator framing transfer is forbidden by TG-G-001; single
      cantilever next to a vertical electrode is the chosen design.
    status: open
findings:
- id: C001
  severity: MAJOR
  category: label_placement
  tex_lines: []
  observation: Panel E HV+ source-box label was previously bisected by the corona-needle wire (label_glyph_overlaps_internal_drawing).
  suggested_fix: Offset the corona-needle wire exit so it clears the HV+ glyph.
  status: resolved
  resolution_evidence: 'Host re-inspection of panel_E_q1/s01/s02 in the current render: the corona-needle
    wire descends well right of the ''HV+'' glyphs; no bisection.'
- id: C002
  severity: MAJOR
  category: label_placement
  tex_lines: []
  observation: Panel E V_s meter label 'meter' was previously clipped by the meter-box right edge (label_backdrop_overflows_outline).
  suggested_fix: Widen the meter box or relabel so the caption fits inside the outline.
  status: resolved
  resolution_evidence: 'Host re-inspection of panel_E_q2/s08 and VC028/VC029: ''V_s meter'' sits fully
    inside the rounded bezel with margin; no clip/overflow.'
- id: C003
  severity: MAJOR
  category: label_placement
  tex_lines: []
  observation: Panel E V_s probe 'V' glyph previously crossed the adjacent meter-box corner (label_glyph_overlaps_internal_drawing).
  suggested_fix: Shift the V_s probe label so the glyph clears the meter corner.
  status: resolved
  resolution_evidence: 'Host re-inspection of panel_E_q1/q2: the V_s probe label and the meter box are
    well separated; no glyph crosses the meter corner.'
- id: C004
  severity: MINOR
  category: label_placement
  tex_lines:
  - 491
  - 492
  observation: Panel C rotated 'Energy' axis label glyphs previously crossed the polymer-film slab right-edge
    stroke (cAmber).
  suggested_fix: Shift the Energy axis label right of the film edge to clear the amber stroke.
  status: resolved
  resolution_evidence: 2026-05-25 patch moved the anchor (10.15->10.35, 6.30); host re-inspection of full_q2
    confirms the rotated label clears the amber stroke and the energy axis.
---

# Vision Critique — fig1_overview_v2_pair_001_vault (v1.16 fresh re-audit)

## Summary

Fresh v1.16 re-audit of the current render (`build/fig1_overview_v2_pair_001_vault.pdf`,
unchanged inputs; `critique_input_hash` matches). The figure reads as a clean Nature
Communications / Nature Materials main-text Figure 1: six self-contained panels on white,
Panel C the HERO trap-landscape model at 1.5x width, and a three-spoke evidence fan from
Panel C into Row 2 (D kinetic, E ISPD, F mechanical). **Verdict: ready** — zero open
BLOCKER and zero open MAJOR findings.

This re-audit was driven by the Issue 91 rubric bump (v1.14 -> v1.16), which adds per-crop
`observed_objects` / `local_relationship` / `unintended_visible_anomaly` accounting. The
figure pixels are identical to the prior v1.14 critique; the host re-inspected the artifact
directly (full render, Panel E, ISPD/probe convention, print-scale) and screened all 109
audit crops, the 43 visual-clash candidates, and the 1 text-boundary candidate via six
parallel inspections, then personally re-inspected every region flagged `present`/`uncertain`.

## Anomaly adjudication (Issue 91 near-miss pass)

Six crops were screened as `present`/`uncertain`; host re-inspection at 5-6x cleared every
one as a non-defect:

- **full_q2 "floating caret"** -> the arrowhead of an intended dashed red leader arrow
  binding a trap site to its energy level (dashed tail visible). Not a stray glyph.
- **panel_E "polymer" leader crossing glyphs** -> the leader attaches at the word's right
  end and runs to the slab; it does NOT cross the 'e'/'r'. Upscaled-tile false positive.
- **panel_F black stroke crossing the Coulomb arrow** -> the cantilever beam's own outline at
  the force-on-charge arrow tail; the arrowhead is clear of the label. The faint gray line is
  the lower-tier F_Maxwell baseline (TG-G-002). Expected geometry.
- **wt% / convergent adjacency (VC018/VC019)** -> two distinct labels on different baselines,
  both legible (tight NIT only).
- **panel_D lower SMU wire loop (s06)** -> conventional wire-hop detail; legible NIT.
- **low n / high n on their lines (s10/q3/q4/s15)** -> color-matched plot-curve labels on
  their own lines; convention.

## Resolved prior findings (re-verified in the current render)

- **C001/C002/C003 (Panel E label placement, MAJOR)** — HV+ wire clears the label, the
  'V_s meter' caption sits inside its bezel, and the V_s probe label clears the meter corner.
- **C004 (Panel C energy-axis label, MINOR)** — the rotated 'Energy' label clears the amber
  film-edge stroke.

## Theory invariants

All Theory Guard BLOCKER items hold in the render: linear Panel A topology (TG-A-001),
same-matrix shallow(blue)/deep(red) traps (TG-C/CFG-001), power-law tails above Debye
(TG-D-001), Coulomb-only result zone with a lower-tier Maxwell baseline (TG-G-001/G-002),
three independent Row 2 spokes (TG-ROW2-001), and an induction-type V_s probe (Keyence-SK
ESVM register, not a Kelvin probe).

## Residual / non-blocking

- One optional NIT: tighten the 'convergent evidence' caption clearance from the
  'Sulfur content, wt%' axis label (VC018/VC019). Non-blocking.
- Panel-level P001/P002/P003 are intentional iconic-cartoon simplifications (briefing 3.2 /
  TG-G-001), recorded as accept_simplification.
- Publication AI/image provenance (TG-PUB-001) remains a separate human gate; it does not
  affect the figure-readiness verdict.
