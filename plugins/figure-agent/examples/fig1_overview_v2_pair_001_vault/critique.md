---
schema: figure-agent.critique.v1.17
fixture: fig1_overview_v2_pair_001_vault
generated_at: '2026-06-30T08:52:00Z'
generator: critique_brief.py
generator_version: sha256:0bf8abd441f6688290a6abc8b4fda75a2d131526615ba5df7b07dc4d1ec04c94
rubric_version: figure-agent.critique-rubric.v1.17
critique_input_hash: sha256:ac68e79690d73fdcff333c982b16a270cf6213a808cb631356a053e4e0ea30de
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
      lines, apparatus labels inside their boxes); 41/41 visual-clash, 1/1 label-path, and 95/95
      undeclared-geometry candidates reviewed and accounted as conventional, intentional structure, or
      false-positive.
    evidence: micro_defects (137 entries); crop_audit_log (108 entries).
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
    evidence: axis summary above; TG-PUB-001 acceptance note; print_178mm crop stays legible at 178 mm
      manuscript width.
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
      mm proxy), and the sole prior residual NIT (convergent-evidence caption clearance from the wt%
      axis label) was resolved in TikZ on 2026-06-04, so no TikZ source work remains and no
      semantic_backport is pending; neither the svg_micro_polish nor the semantic_backport
      polish_trigger condition is met.
    rationale: Stay in TikZ; no svg_micro_polish or semantic_backport pending. SVG polish was evaluated
      and not pursued - this fully-programmatic figure is art-direction-complete in the TikZ source
      (already at Nature-tier), so a bounded visual-only vector finish adds nothing.
    concrete_fix: accept_simplification - source-complete; remaining in TikZ.
    blocks_high_impact: false
    recommended_path: continue_tikz
    remaining_tikz_lever: 'None - the prior residual NIT (convergent-evidence caption clearance from
      the Sulfur content, wt% axis label) was resolved in TikZ on 2026-06-04. No TikZ work remains.'
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
  assessed_artifact_hash: sha256:ac68e79690d73fdcff333c982b16a270cf6213a808cb631356a053e4e0ea30de
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
aesthetic_antipattern_audit:
- id: childish_shape_language
  verdict: absent
  severity: NIT
  route: none
  evidence: In the current render the instrument boxes (SMU, V_s meter, V_active PSU) use square engineering
    bezels and the molecular rings are chemically-shaped, not rounded toy primitives.
  rationale: No rounded cartoon shape language is visible across panels a-f; the geometry reads as
    engineering/chemistry register, so the anti-pattern is absent and no route is needed.
  linked_evidence: []
- id: poster_gradient_decoration
  verdict: absent
  severity: NIT
  route: none
  evidence: The current render is on clean white with flat fills only; no poster gradient, glow, or wash
    band appears in the full_q1..q4 crops after the 2026-05-22 wash-strip redirect.
  rationale: Color is restricted to flat semantic fills (amber/blue/red/gray) with no decorative gradient,
    so this anti-pattern is absent and no route is required.
  linked_evidence: []
- id: generic_template_look
  verdict: absent
  severity: NIT
  route: none
  evidence: Panel C is hand-composed at 1.5x width with a real-space film fused to an energy diagram; the
    panels are not slotted into a uniform template grid in the rendered figure.
  rationale: The render shows role-specific bespoke composition (hero C, three-spoke fan), not a preset
    template stamp, so the generic-template anti-pattern is absent.
  linked_evidence: []
- id: dead_flat_vector_finish
  verdict: absent
  severity: NIT
  route: none
  evidence: The current render carries a line-weight hierarchy (foreground mechanism strokes heavier than
    supports) and depth cues in the MIM stack and cantilever, not a uniformly dead flat fill.
  rationale: Stroke-weight variation and layered depth are visible, so the figure is not a dead flat vector;
    this anti-pattern is absent and needs no route.
  linked_evidence: []
- id: uniform_line_weight_monotony
  verdict: absent
  severity: NIT
  route: none
  evidence: In the rendered panels mechanism strokes, wiring, axes, and label rules sit at distinct weights;
    the Coulomb arrow in Panel F is bold while the Maxwell baseline is faint gray.
  rationale: Line weights are deliberately differentiated to separate foreground from support, so the
    uniform-line-weight monotony anti-pattern is absent.
  linked_evidence: []
- id: weak_hero_anchor
  verdict: absent
  severity: NIT
  route: none
  evidence: Panel C is the unambiguous first fixation in the rendered figure - widest panel, strongest
    deep-red saturation, and the origin of the three evidence spokes feeding Row 2.
  rationale: A single strong hero is established and routes the read path, so the weak-hero-anchor
    anti-pattern is absent and no route is needed.
  linked_evidence: []
- id: cramped_or_dead_whitespace
  verdict: absent
  severity: NIT
  route: none
  evidence: The current render keeps visible gutters between D/E/F columns and local breathing room around
    sub-zone labels; instrument-box labels stay inside their outlines (VC028/VC029).
  rationale: Whitespace is balanced - neither cramped nor large dead voids - in the rendered layout, so
    this anti-pattern is absent.
  linked_evidence: []
- id: low_authority_typography
  verdict: absent
  severity: NIT
  route: none
  evidence: Panel letters form a controlled hierarchy and subscripts/math labels stay legible and
    consistent in the 178 mm print proxy crop of the current render.
  rationale: Typography reads with editorial authority and consistent sizing at print scale, so the
    low-authority-typography anti-pattern is absent.
  linked_evidence: []
- id: annotation_noise_competes_with_science
  verdict: absent
  severity: NIT
  route: none
  evidence: In the rendered figure every annotation (modality spoke labels, axis labels, apparatus labels)
    maps to a mechanism and ink stays economical with no decorative callouts.
  rationale: Annotations support the science rather than competing with it, so the annotation-noise
    anti-pattern is absent and no route is needed.
  linked_evidence: []
- id: panel_style_mismatch
  verdict: absent
  severity: NIT
  route: none
  evidence: The six panels share one style authority in the current render - common panel-letter
    typography, shallow=blue/deep=red grammar, and a frame-less axis-arrow plot register across D/E/F.
  rationale: Panels read as a single coherent series with no off-style outlier, so the panel-style-mismatch
    anti-pattern is absent.
  linked_evidence: []
- id: reference_overcopying
  verdict: absent
  severity: NIT
  route: none
  evidence: The render preserves the reference palette restraint and two-row proportion but keeps the
    Panel A linear topology and does not transfer the reference network topology or plot-grid equality.
  rationale: Style cues were learned without copying forbidden reference content, so the
    reference-overcopying anti-pattern is absent and no route is needed.
  linked_evidence: []
- id: reference_underlearning
  verdict: absent
  severity: NIT
  route: none
  evidence: The rendered figure adopts the reference label hierarchy and clean-white editorial restraint;
    the codex_gen_overview_v1.png style anchors are visibly applied in the current artifact.
  rationale: Useful reference principles were applied rather than ignored, so the reference-underlearning
    anti-pattern is absent.
  linked_evidence: []
- id: decorative_detail_without_explanatory_value
  verdict: absent
  severity: NIT
  route: none
  evidence: In the current render every drawn detail carries meaning - charge pins mark deposition, the
    air-gap caliper marks geometry, the S8 inset marks chemistry - with no purely ornamental marks.
  rationale: No decorative detail without explanatory value is visible across panels a-f, so this
    anti-pattern is absent and no route is required.
  linked_evidence: []
weakest_panel_coherence:
  panel_id: a
  subregion_id: panel_a_molecular_chain
  weakness_type: none
  route: none
  evidence: Panel A is the most schematic sub-region - a linear poly(S-r-DIB) chain with DIB rings, S8
    inset, and (S)x bracket - but in the current render it reads as a coherent, legible molecular identity.
  rationale: The molecular schematic is intentionally abstracted per briefing 3.2 and remains internally
    coherent, so even the relatively weakest panel carries weakness_type none and needs no route.
  linked_evidence: []
reference_learning_accountability:
  learned_principle: Adopt the reference palette restraint, two-row proportion, and label hierarchy while
    keeping Panel A linear topology and a clean-white editorial register.
  rejected_copy_target: The reference network topology and plot-grid equality, which would violate the
    Panel A linear-chain invariant and the NC main-text clean-white convention.
  overcopying: absent
  underlearning: absent
  route: none
  evidence: The current render shows learned style cues (restrained palette, label hierarchy) applied
    without transferring the forbidden reference network topology, visible across panels a-f.
  rationale: Reference learning is balanced - neither overcopied nor underlearned in the rendered figure -
    so both verdicts are absent and no route is needed.
  linked_evidence: []
micro_defects:
- id: M001
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC001_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC001 (detector text_on_path, text ''S''): Sulfur node glyph on chain bonds (intentional molecular skeleton); fully legible. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC001
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC001: Sulfur node glyph on chain bonds (intentional molecular skeleton); fully legible. This is not a defect (convention_acceptable); the ''S'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M002
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC002_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC002 (detector text_on_path, text ''S''): Sulfur node on poly(S-r-DIB) backbone; on-path by design, crisp. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC002
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC002: Sulfur node on poly(S-r-DIB) backbone; on-path by design, crisp. This is not a defect (convention_acceptable); the ''S'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M003
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC003_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC003 (detector text_on_path, text ''S''): Sulfur node on chain; low dark metric, no glyph-line merge. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC003
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC003: Sulfur node on chain; low dark metric, no glyph-line merge. This is not a defect (convention_acceptable); the ''S'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M004
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC004_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC004 (detector text_on_path, text ''S''): Sulfur node on bond crossing; intentional structure, legible. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC004
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC004: Sulfur node on bond crossing; intentional structure, legible. This is not a defect (convention_acceptable); the ''S'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M005
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC005_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC005 (detector text_on_path, text ''S''): Sulfur node on backbone; clean separation. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC005
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC005: Sulfur node on backbone; clean separation. This is not a defect (convention_acceptable); the ''S'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M006
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC006_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC006 (detector text_on_path, text ''S''): Sulfur node on chain bonds; intentional molecular label. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC006
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC006: Sulfur node on chain bonds; intentional molecular label. This is not a defect (convention_acceptable); the ''S'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M007
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC007_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC007 (detector text_on_path, text ''S''): Sulfur node on backbone segment; readable. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC007
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC007: Sulfur node on backbone segment; readable. This is not a defect (convention_acceptable); the ''S'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M008
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC008_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC008 (detector text_on_path, text ''S''): Sulfur node on chain; on-path by design. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC008
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC008: Sulfur node on chain; on-path by design. This is not a defect (convention_acceptable); the ''S'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M009
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC009_C.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC009 (detector near_miss, text ''C''): Italic math C variable near E glyph; metric tiny (dark 0.015), no overlap. Host crop verdict: false_positive; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC009
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC009: Italic math C variable near E glyph; metric tiny (dark 0.015), no overlap. This is not a defect (false_positive); the ''C'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M010
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC010_edge.png
  kind: label_curve_near_label
  severity: NIT
  observation: 'Visual-clash candidate VC010 (detector text_on_fill, text ''edge''): Band-diagram "edge" label on tinted fill; high contrast, legible. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC010
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC010: Band-diagram "edge" label on tinted fill; high contrast, legible. This is not a defect (convention_acceptable); the ''edge'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M011
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC011_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC011 (detector near_miss, text ''S''): Sulfur node with subscript + bonded atom dot; intentional formula, no clash. Host crop verdict: false_positive; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC011
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC011: Sulfur node with subscript + bonded atom dot; intentional formula, no clash. This is not a defect (false_positive); the ''S'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M012
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC012_shallow.png
  kind: label_curve_near_label
  severity: NIT
  observation: 'Visual-clash candidate VC012 (detector text_on_fill, text ''shallow''): "shallow" trap label on fill; crisp. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC012
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC012: "shallow" trap label on fill; crisp. This is not a defect (convention_acceptable); the ''shallow'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M013
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC013_S.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC013 (detector near_miss, text ''S''): Sulfur glyph near bond; dark 0.03, no real collision. Host crop verdict: false_positive; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC013
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: false_positive
  accept_simplification_rationale: 'VC013: Sulfur glyph near bond; dark 0.03, no real collision. This is not a defect (false_positive); the ''S'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M014
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC014_poly_S-r-DIB.png
  kind: label_curve_near_label
  severity: NIT
  observation: 'Visual-clash candidate VC014 (detector text_on_fill, text ''poly(S-r-DIB)''): "poly(S-r-DIB) thin film" italic on white; sharp, fully readable. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC014
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC014: "poly(S-r-DIB) thin film" italic on white; sharp, fully readable. This is not a defect (convention_acceptable); the ''poly(S-r-DIB)'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M015
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC015_film.png
  kind: label_curve_near_label
  severity: NIT
  observation: 'Visual-clash candidate VC015 (detector text_on_fill, text ''film''): Tail of "thin film" caption on fill; legible. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC015
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC015: Tail of "thin film" caption on fill; legible. This is not a defect (convention_acceptable); the ''film'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M016
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC016_Sulfur-rich.png
  kind: label_curve_near_label
  severity: NIT
  observation: 'Visual-clash candidate VC016 (detector text_on_fill, text ''Sulfur-rich''): "Sulfur-rich" panel label on fill; clean. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC016
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC016: "Sulfur-rich" panel label on fill; clean. This is not a defect (convention_acceptable); the ''Sulfur-rich'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M017
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC017_poly_S-r-DIB.png
  kind: label_curve_near_label
  severity: NIT
  observation: 'Visual-clash candidate VC017 (detector text_on_fill, text ''poly(S-r-DIB)''): "poly(S-r-DIB)" stacked label on fill; readable. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC017
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC017: "poly(S-r-DIB)" stacked label on fill; readable. This is not a defect (convention_acceptable); the ''poly(S-r-DIB)'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M018
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC018_Sulfur.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC018 (detector text_on_path, text ''Sulfur''): "Sulfur" annotation near guide line; low metric, no merge. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC018
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC018: "Sulfur" annotation near guide line; low metric, no merge. This is not a defect (convention_acceptable); the ''Sulfur'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M019
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC019_V.png
  kind: label_curve_near_label
  severity: NIT
  observation: 'Visual-clash candidate VC019 (detector text_on_fill, text ''V''): Subscript V of E_V (valence band edge); italic, clean separation from E. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC019
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC019: Subscript V of E_V (valence band edge); italic, clean separation from E. This is not a defect (convention_acceptable); the ''V'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M020
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC020_ISPD.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC020 (detector text_on_path, text ''ISPD''): "ISPD" probe label sits below frame rule; no collision with rule. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC020
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC020: "ISPD" probe label sits below frame rule; no collision with rule. This is not a defect (convention_acceptable); the ''ISPD'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M021
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC021_MIM.png
  kind: label_curve_near_label
  severity: NIT
  observation: 'Visual-clash candidate VC021 (detector text_on_fill, text ''MIM''): "MIM" device label on fill; high luma_std, legible. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC021
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC021: "MIM" device label on fill; high luma_std, legible. This is not a defect (convention_acceptable); the ''MIM'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M022
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC022_V_A.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC022 (detector text_on_path, text ''V/A''): "V/A" axis/unit label near rule; readable, no overlap. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC022
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC022: "V/A" axis/unit label near rule; readable, no overlap. This is not a defect (convention_acceptable); the ''V/A'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M023
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC023_Vs.png
  kind: label_curve_near_label
  severity: NIT
  observation: 'Visual-clash candidate VC023 (detector text_on_fill, text ''Vs''): "Vs" (surface voltage) label on fill; crisp. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC023
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC023: "Vs" (surface voltage) label on fill; crisp. This is not a defect (convention_acceptable); the ''Vs'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M024
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC024_crop.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC024 (detector text_on_path, text ''+''): Charge-deposition "+" pin glyph on surface interface line; intentional ISPD marker. Host crop verdict: accept_simplification; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC024
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC024: Charge-deposition "+" pin glyph on surface interface line; intentional ISPD marker. This is not a defect (intentional_schematic); the ''+'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M025
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC025_crop.png
  kind: label_curve_near_label
  severity: NIT
  observation: 'Visual-clash candidate VC025 (detector text_on_fill, text ''+''): "+" charge pin on surface; intentional deposition glyph, by design. Host crop verdict: accept_simplification; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC025
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC025: "+" charge pin on surface; intentional deposition glyph, by design. This is not a defect (intentional_schematic); the ''+'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M026
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC026_crop.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC026 (detector text_on_path, text ''+''): "+" charge pin on interface line; intentional marker. Host crop verdict: accept_simplification; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC026
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC026: "+" charge pin on interface line; intentional marker. This is not a defect (intentional_schematic); the ''+'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M027
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC027_crop.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC027 (detector text_on_path, text ''+''): "+" charge pin on interface line; intentional marker. Host crop verdict: accept_simplification; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC027
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC027: "+" charge pin on interface line; intentional marker. This is not a defect (intentional_schematic); the ''+'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M028
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC028_V.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC028 (detector text_on_path, text ''V''): Italic V near guide line; low dark metric, legible. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC028
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC028: Italic V near guide line; low dark metric, legible. This is not a defect (convention_acceptable); the ''V'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M029
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC029_V.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC029 (detector text_on_path, text ''V''): "V" label near axis rule; no merge. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC029
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC029: "V" label near axis rule; no merge. This is not a defect (convention_acceptable); the ''V'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M030
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC030_t.png
  kind: label_curve_near_label
  severity: NIT
  observation: 'Visual-clash candidate VC030 (detector text_on_fill, text ''(t)''): "(t)" of V(t) time-dependence label on fill; readable. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC030
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC030: "(t)" of V(t) time-dependence label on fill; readable. This is not a defect (convention_acceptable); the ''(t)'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M031
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC031_I_t.png
  kind: label_curve_near_label
  severity: NIT
  observation: 'Visual-clash candidate VC031 (detector text_on_fill, text ''I(t)''): "I(t) ~" current-vs-time math on fill; crisp italic. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC031
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC031: "I(t) ~" current-vs-time math on fill; crisp italic. This is not a defect (convention_acceptable); the ''I(t)'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M032
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC032_low.png
  kind: label_curve_near_label
  severity: NIT
  observation: 'Visual-clash candidate VC032 (detector text_on_fill, text ''low''): "low" trap-depth label on fill; legible. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC032
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC032: "low" trap-depth label on fill; legible. This is not a defect (convention_acceptable); the ''low'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M033
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC033_crop.png
  kind: label_curve_near_label
  severity: NIT
  observation: 'Visual-clash candidate VC033 (detector text_on_fill, text '')''): Closing paren of a label fragment on fill; clean. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC033
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC033: Closing paren of a label fragment on fill; clean. This is not a defect (convention_acceptable); the '')'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M034
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC034_hig.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC034 (detector text_on_path, text ''hig''): Rotated rose "high" along sloped trend line crossed by dashed guide; word stays readable, intentional angled annotation. Host crop verdict: accept_simplification; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC034
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC034: Rotated rose "high" along sloped trend line crossed by dashed guide; word stays readable, intentional angled annotation. This is not a defect (intentional_schematic); the ''hig'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M035
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC035_h.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC035 (detector text_on_path, text ''h''): Continuation of rotated "high" on trend line; intentional, legible. Host crop verdict: accept_simplification; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC035
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC035: Continuation of rotated "high" on trend line; intentional, legible. This is not a defect (intentional_schematic); the ''h'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M036
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC036_n.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC036 (detector text_on_path, text ''n''): Tail glyph of the same rotated "high" annotation on trend line; intentional angled label, readable. Host crop verdict: accept_simplification; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC036
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'VC036: Tail glyph of the same rotated "high" annotation on trend line; intentional angled label, readable. This is not a defect (intentional_schematic); the ''n'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M037
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC037_d.png
  kind: label_curve_near_label
  severity: NIT
  observation: 'Visual-clash candidate VC037 (detector text_on_fill, text ''d''): Subscript d of tau_d (trap-depth time constant); italic, separated from tau and axis rule. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC037
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC037: Subscript d of tau_d (trap-depth time constant); italic, separated from tau and axis rule. This is not a defect (convention_acceptable); the ''d'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M038
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC038_Shallow.png
  kind: label_curve_near_label
  severity: NIT
  observation: 'Visual-clash candidate VC038 (detector text_on_fill, text ''Shallow''): "Shallow" trap-depth label on fill; crisp. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC038
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC038: "Shallow" trap-depth label on fill; crisp. This is not a defect (convention_acceptable); the ''Shallow'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M039
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC039_log.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC039 (detector text_on_path, text ''log''): "log" axis-scale label near axis rule; low edge metric, no merge. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC039
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC039: "log" axis-scale label near axis rule; low edge metric, no merge. This is not a defect (convention_acceptable); the ''log'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M040
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC040_I.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Visual-clash candidate VC040 (detector text_on_path, text ''I''): Axis label "I" near rule; legible. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC040
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC040: Axis label "I" near rule; legible. This is not a defect (convention_acceptable); the ''I'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M041
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC041_f.png
  kind: label_curve_near_label
  severity: NIT
  observation: 'Visual-clash candidate VC041 (detector text_on_fill, text ''f''): Italic f label fragment on fill; clean. Host crop verdict: no_defect; label stays legible, not a real collision.'
  linked_finding_id: ''
  visual_clash_ref: VC041
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC041: Italic f label fragment on fill; clean. This is not a defect (convention_acceptable); the ''f'' glyph is legible and the flagged stroke/fill is intentional schematic register.'
- id: M042
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/label_path/LP001_mobility_edge.png
  kind: label_stacked_on_reference_line
  severity: NIT
  observation: 'Label-path candidate LP001 (text ''mobility edge''): the ''mobility edge'' annotation sits on its own Panel C mobility-edge reference line; sub-threshold separation (3.36 pt < 4.0 pt clearance) is intentional reference-line annotation, not a clash.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: LP001
  undeclared_geometry_ref: ''
  status: accept_simplification
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'LP001: ''mobility edge'' is stacked on the panel_c_mobility_edge_reference line by design (separation 3.36 pt < 4.0 pt clearance); this is an intentional reference-line annotation, not a defect (convention_acceptable).'
- id: M043
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG001 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG001
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG001: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M044
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Undeclared-geometry candidate UG002 (detector kind label_endpoint_near_miss near ''copolymer'' (2.03 pt)): conventional axis/structure label endpoint resting near its target; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG002
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG002: detector-flagged label_endpoint_near_miss near ''copolymer'' is a conventional axis/structure label endpoint resting near its target drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M045
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG003 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG003
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG003: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M046
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Undeclared-geometry candidate UG004 (detector kind label_endpoint_near_miss near ''HV+'' (0.95 pt)): conventional axis/structure label endpoint resting near its target; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG004
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG004: detector-flagged label_endpoint_near_miss near ''HV+'' is a conventional axis/structure label endpoint resting near its target drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M047
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG005 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG005
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG005: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M048
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG006 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG006
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG006: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M049
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG007 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG007
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG007: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M050
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG008 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG008
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG008: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M051
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG009 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG009
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG009: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M052
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Undeclared-geometry candidate UG010 (detector kind label_endpoint_near_miss near ''Vs'' (2.25 pt)): conventional axis/structure label endpoint resting near its target; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG010
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG010: detector-flagged label_endpoint_near_miss near ''Vs'' is a conventional axis/structure label endpoint resting near its target drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M053
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
  kind: label_crosses_column_rule
  severity: NIT
  observation: 'Undeclared-geometry candidate UG011 (detector kind undeclared_column_rule): intentional vertical axis / column divider / panel separator rule; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG011
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG011: detector-flagged undeclared_column_rule is a intentional vertical axis / column divider / panel separator rule drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M054
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Undeclared-geometry candidate UG012 (detector kind label_endpoint_near_miss near ''ISPD'' (2.58 pt)): conventional axis/structure label endpoint resting near its target; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG012
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG012: detector-flagged label_endpoint_near_miss near ''ISPD'' is a conventional axis/structure label endpoint resting near its target drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M055
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG013 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG013
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG013: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M056
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
  kind: label_crosses_column_rule
  severity: NIT
  observation: 'Undeclared-geometry candidate UG014 (detector kind undeclared_column_rule): intentional vertical axis / column divider / panel separator rule; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG014
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG014: detector-flagged undeclared_column_rule is a intentional vertical axis / column divider / panel separator rule drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M057
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q2.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG015 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG015
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG015: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M058
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q2.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG016 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG016
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG016: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M059
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q2.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG017 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG017
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG017: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M060
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q2.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG018 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG018
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG018: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M061
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q2.png
  kind: label_crosses_column_rule
  severity: NIT
  observation: 'Undeclared-geometry candidate UG019 (detector kind undeclared_column_rule): intentional vertical axis / column divider / panel separator rule; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG019
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG019: detector-flagged undeclared_column_rule is a intentional vertical axis / column divider / panel separator rule drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M062
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q2.png
  kind: label_crosses_column_rule
  severity: NIT
  observation: 'Undeclared-geometry candidate UG020 (detector kind undeclared_column_rule): intentional vertical axis / column divider / panel separator rule; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG020
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG020: detector-flagged undeclared_column_rule is a intentional vertical axis / column divider / panel separator rule drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M063
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q2.png
  kind: label_crosses_column_rule
  severity: NIT
  observation: 'Undeclared-geometry candidate UG021 (detector kind undeclared_column_rule): intentional vertical axis / column divider / panel separator rule; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG021
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG021: detector-flagged undeclared_column_rule is a intentional vertical axis / column divider / panel separator rule drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M064
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q2.png
  kind: label_crosses_column_rule
  severity: NIT
  observation: 'Undeclared-geometry candidate UG022 (detector kind undeclared_column_rule): intentional vertical axis / column divider / panel separator rule; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG022
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG022: detector-flagged undeclared_column_rule is a intentional vertical axis / column divider / panel separator rule drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M065
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
  kind: label_crosses_column_rule
  severity: NIT
  observation: 'Undeclared-geometry candidate UG023 (detector kind undeclared_column_rule): intentional vertical axis / column divider / panel separator rule; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG023
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG023: detector-flagged undeclared_column_rule is a intentional vertical axis / column divider / panel separator rule drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M066
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q2.png
  kind: label_crosses_column_rule
  severity: NIT
  observation: 'Undeclared-geometry candidate UG024 (detector kind undeclared_column_rule): intentional vertical axis / column divider / panel separator rule; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG024
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG024: detector-flagged undeclared_column_rule is a intentional vertical axis / column divider / panel separator rule drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M067
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Undeclared-geometry candidate UG025 (detector kind label_endpoint_near_miss near ''poly(S-r-DIB)'' (1.87 pt)): conventional axis/structure label endpoint resting near its target; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG025
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG025: detector-flagged label_endpoint_near_miss near ''poly(S-r-DIB)'' is a conventional axis/structure label endpoint resting near its target drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M068
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Undeclared-geometry candidate UG026 (detector kind label_endpoint_near_miss near ''thin'' (1.87 pt)): conventional axis/structure label endpoint resting near its target; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG026
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG026: detector-flagged label_endpoint_near_miss near ''thin'' is a conventional axis/structure label endpoint resting near its target drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M069
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG027 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG027
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG027: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M070
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG028 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG028
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG028: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M071
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Undeclared-geometry candidate UG029 (detector kind label_endpoint_near_miss near ''S'' (1.35 pt)): conventional axis/structure label endpoint resting near its target; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG029
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG029: detector-flagged label_endpoint_near_miss near ''S'' is a conventional axis/structure label endpoint resting near its target drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M072
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_column_rule
  severity: NIT
  observation: 'Undeclared-geometry candidate UG030 (detector kind undeclared_column_rule): intentional vertical axis / column divider / panel separator rule; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG030
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG030: detector-flagged undeclared_column_rule is a intentional vertical axis / column divider / panel separator rule drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M073
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_column_rule
  severity: NIT
  observation: 'Undeclared-geometry candidate UG031 (detector kind undeclared_column_rule): intentional vertical axis / column divider / panel separator rule; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG031
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG031: detector-flagged undeclared_column_rule is a intentional vertical axis / column divider / panel separator rule drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M074
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG032 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG032
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG032: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M075
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG033 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG033
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG033: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M076
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG034 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG034
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG034: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M077
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG035 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG035
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG035: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M078
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG036 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG036
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG036: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M079
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG037 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG037
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG037: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M080
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG038 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG038
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG038: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M081
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG039 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG039
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG039: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M082
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG040 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG040
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG040: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M083
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG041 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG041
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG041: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M084
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG042 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG042
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG042: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M085
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG043 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG043
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG043: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M086
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_column_rule
  severity: NIT
  observation: 'Undeclared-geometry candidate UG044 (detector kind undeclared_column_rule): intentional vertical axis / column divider / panel separator rule; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG044
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG044: detector-flagged undeclared_column_rule is a intentional vertical axis / column divider / panel separator rule drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M087
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Undeclared-geometry candidate UG045 (detector kind label_endpoint_near_miss near ''S'' (3.74 pt)): conventional axis/structure label endpoint resting near its target; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG045
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG045: detector-flagged label_endpoint_near_miss near ''S'' is a conventional axis/structure label endpoint resting near its target drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M088
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG046 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG046
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG046: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M089
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Undeclared-geometry candidate UG047 (detector kind label_endpoint_near_miss near ''−(S)'' (0.23 pt)): conventional axis/structure label endpoint resting near its target; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG047
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG047: detector-flagged label_endpoint_near_miss near ''−(S)'' is a conventional axis/structure label endpoint resting near its target drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M090
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG048 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG048
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG048: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M091
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG049 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG049
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG049: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M092
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG050 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG050
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG050: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M093
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG051 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG051
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG051: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M094
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG052 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG052
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG052: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M095
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG053 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG053
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG053: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M096
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG054 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG054
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG054: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M097
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG055 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG055
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG055: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M098
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG056 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG056
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG056: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M099
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG057 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG057
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG057: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M100
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG058 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG058
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG058: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M101
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG059 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG059
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG059: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M102
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG060 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG060
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG060: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M103
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG061 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG061
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG061: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M104
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG062 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG062
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG062: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M105
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG063 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG063
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG063: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M106
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG064 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG064
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG064: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M107
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG065 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG065
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG065: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M108
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG066 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG066
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG066: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M109
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG067 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG067
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG067: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M110
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG068 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG068
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG068: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M111
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG069 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG069
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG069: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M112
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG070 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG070
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG070: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M113
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG071 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG071
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG071: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M114
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG072 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG072
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG072: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M115
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_column_rule
  severity: NIT
  observation: 'Undeclared-geometry candidate UG073 (detector kind undeclared_column_rule): intentional vertical axis / column divider / panel separator rule; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG073
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG073: detector-flagged undeclared_column_rule is a intentional vertical axis / column divider / panel separator rule drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M116
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG074 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG074
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG074: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M117
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_column_rule
  severity: NIT
  observation: 'Undeclared-geometry candidate UG075 (detector kind undeclared_column_rule): intentional vertical axis / column divider / panel separator rule; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG075
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG075: detector-flagged undeclared_column_rule is a intentional vertical axis / column divider / panel separator rule drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M118
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Undeclared-geometry candidate UG076 (detector kind label_endpoint_near_miss near ''b'' (3.59 pt)): conventional axis/structure label endpoint resting near its target; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG076
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG076: detector-flagged label_endpoint_near_miss near ''b'' is a conventional axis/structure label endpoint resting near its target drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M119
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_column_rule
  severity: NIT
  observation: 'Undeclared-geometry candidate UG077 (detector kind undeclared_column_rule): intentional vertical axis / column divider / panel separator rule; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG077
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG077: detector-flagged undeclared_column_rule is a intentional vertical axis / column divider / panel separator rule drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M120
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG078 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG078
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG078: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M121
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG079 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG079
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG079: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M122
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG080 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG080
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG080: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M123
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG081 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG081
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG081: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M124
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG082 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG082
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG082: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M125
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG083 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG083
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG083: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M126
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG084 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG084
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG084: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M127
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Undeclared-geometry candidate UG085 (detector kind label_endpoint_near_miss near ''Energy'' (0.73 pt)): conventional axis/structure label endpoint resting near its target; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG085
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG085: detector-flagged label_endpoint_near_miss near ''Energy'' is a conventional axis/structure label endpoint resting near its target drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M128
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG086 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG086
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG086: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M129
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG087 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG087
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG087: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M130
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG088 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG088
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG088: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M131
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG089 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG089
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG089: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M132
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG090 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG090
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG090: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M133
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG091 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG091
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG091: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M134
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG092 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG092
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG092: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M135
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG093 (detector kind undeclared_rect_boundary): intentional panel frame / instrument bezel / schematic box; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG093
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG093: detector-flagged undeclared_rect_boundary is a intentional panel frame / instrument bezel / schematic box drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M136
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
  kind: label_path_near_miss
  severity: NIT
  observation: 'Undeclared-geometry candidate UG094 (detector kind label_endpoint_near_miss near ''localized'' (0.38 pt)): conventional axis/structure label endpoint resting near its target; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG094
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG094: detector-flagged label_endpoint_near_miss near ''localized'' is a conventional axis/structure label endpoint resting near its target drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
- id: M137
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
  kind: label_crosses_panel_boundary
  severity: NIT
  observation: 'Undeclared-geometry candidate UG095 (detector kind undeclared_horizontal_rule): intentional axis baseline / band rule / panel divider strip; accepted as intentional structure, not an accidental mark.'
  linked_finding_id: ''
  visual_clash_ref: ''
  text_boundary_ref: ''
  label_path_ref: ''
  undeclared_geometry_ref: UG095
  status: accept_simplification
  accept_simplification_reason: intentional_schematic
  accept_simplification_rationale: 'UG095: detector-flagged undeclared_horizontal_rule is a intentional axis baseline / band rule / panel divider strip drawn in the .tex; the figure is Nature-tier with no real defect here, so this is accepted intentional structure (intentional_schematic), not a defect.'
crop_audit_log:
- crop_id: LP001_mobility_edge
  path: build/audit_crops/label_path/LP001_mobility_edge.png
  source: label_path:LP001
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Label-path candidate LP001: ''mobility edge'' rests on its Panel C mobility-edge reference line; sub-threshold separation is intentional reference-line annotation, fully legible.'
  observed_objects:
  - label 'mobility edge'
  - the Panel C mobility-edge reference line
  local_relationship: 'Label-path candidate LP001: ''mobility edge'' rests on its Panel C mobility-edge reference line; sub-threshold separation is intentional reference-line annotation, fully legible.'
  candidate_refs:
  - LP001
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label and its reference line are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC001_S
  path: build/audit_crops/visual_clash/VC001_S.png
  source: visual_clash:VC001
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC001 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC001 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC001
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC002_S
  path: build/audit_crops/visual_clash/VC002_S.png
  source: visual_clash:VC002
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC002 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC002 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC002
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC003_S
  path: build/audit_crops/visual_clash/VC003_S.png
  source: visual_clash:VC003
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC003 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC003 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC003
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC004_S
  path: build/audit_crops/visual_clash/VC004_S.png
  source: visual_clash:VC004
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC004 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC004 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC004
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC005_S
  path: build/audit_crops/visual_clash/VC005_S.png
  source: visual_clash:VC005
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC005 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC005 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC005
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC006_S
  path: build/audit_crops/visual_clash/VC006_S.png
  source: visual_clash:VC006
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC006 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC006 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC006
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC007_S
  path: build/audit_crops/visual_clash/VC007_S.png
  source: visual_clash:VC007
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC007 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC007 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC007
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC008_S
  path: build/audit_crops/visual_clash/VC008_S.png
  source: visual_clash:VC008
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC008 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC008 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC008
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC009_C
  path: build/audit_crops/visual_clash/VC009_C.png
  source: visual_clash:VC009
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC009 (text ''C''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'C'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC009 (text ''C''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC009
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC010_edge
  path: build/audit_crops/visual_clash/VC010_edge.png
  source: visual_clash:VC010
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC010 (text ''edge''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'edge'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC010 (text ''edge''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC010
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC011_S
  path: build/audit_crops/visual_clash/VC011_S.png
  source: visual_clash:VC011
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC011 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC011 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC011
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC012_shallow
  path: build/audit_crops/visual_clash/VC012_shallow.png
  source: visual_clash:VC012
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC012 (text ''shallow''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'shallow'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC012 (text ''shallow''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC012
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC013_S
  path: build/audit_crops/visual_clash/VC013_S.png
  source: visual_clash:VC013
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC013 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'S'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC013 (text ''S''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC013
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC014_poly_S-r-DIB
  path: build/audit_crops/visual_clash/VC014_poly_S-r-DIB.png
  source: visual_clash:VC014
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC014 (text ''poly(S-r-DIB)''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'poly(S-r-DIB)'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC014 (text ''poly(S-r-DIB)''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC014
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC015_film
  path: build/audit_crops/visual_clash/VC015_film.png
  source: visual_clash:VC015
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC015 (text ''film''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'film'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC015 (text ''film''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC015
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC016_Sulfur-rich
  path: build/audit_crops/visual_clash/VC016_Sulfur-rich.png
  source: visual_clash:VC016
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC016 (text ''Sulfur-rich''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'Sulfur-rich'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC016 (text ''Sulfur-rich''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC016
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC017_poly_S-r-DIB
  path: build/audit_crops/visual_clash/VC017_poly_S-r-DIB.png
  source: visual_clash:VC017
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC017 (text ''poly(S-r-DIB)''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'poly(S-r-DIB)'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC017 (text ''poly(S-r-DIB)''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC017
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC018_Sulfur
  path: build/audit_crops/visual_clash/VC018_Sulfur.png
  source: visual_clash:VC018
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC018 (text ''Sulfur''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'Sulfur'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC018 (text ''Sulfur''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC018
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC019_V
  path: build/audit_crops/visual_clash/VC019_V.png
  source: visual_clash:VC019
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC019 (text ''V''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'V'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC019 (text ''V''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC019
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC020_ISPD
  path: build/audit_crops/visual_clash/VC020_ISPD.png
  source: visual_clash:VC020
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC020 (text ''ISPD''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'ISPD'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC020 (text ''ISPD''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC020
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC021_MIM
  path: build/audit_crops/visual_clash/VC021_MIM.png
  source: visual_clash:VC021
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC021 (text ''MIM''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'MIM'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC021 (text ''MIM''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC021
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC022_V_A
  path: build/audit_crops/visual_clash/VC022_V_A.png
  source: visual_clash:VC022
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC022 (text ''V/A''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'V/A'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC022 (text ''V/A''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC022
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC023_Vs
  path: build/audit_crops/visual_clash/VC023_Vs.png
  source: visual_clash:VC023
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC023 (text ''Vs''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'Vs'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC023 (text ''Vs''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC023
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC024_crop
  path: build/audit_crops/visual_clash/VC024_crop.png
  source: visual_clash:VC024
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC024 (text ''+''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label '+'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC024 (text ''+''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC024
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC025_crop
  path: build/audit_crops/visual_clash/VC025_crop.png
  source: visual_clash:VC025
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC025 (text ''+''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label '+'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC025 (text ''+''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC025
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC026_crop
  path: build/audit_crops/visual_clash/VC026_crop.png
  source: visual_clash:VC026
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC026 (text ''+''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label '+'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC026 (text ''+''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC026
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC027_crop
  path: build/audit_crops/visual_clash/VC027_crop.png
  source: visual_clash:VC027
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC027 (text ''+''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label '+'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC027 (text ''+''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC027
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC028_V
  path: build/audit_crops/visual_clash/VC028_V.png
  source: visual_clash:VC028
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC028 (text ''V''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'V'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC028 (text ''V''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC028
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC029_V
  path: build/audit_crops/visual_clash/VC029_V.png
  source: visual_clash:VC029
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC029 (text ''V''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'V'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC029 (text ''V''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC029
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC030_t
  path: build/audit_crops/visual_clash/VC030_t.png
  source: visual_clash:VC030
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC030 (text ''(t)''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label '(t)'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC030 (text ''(t)''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC030
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC031_I_t
  path: build/audit_crops/visual_clash/VC031_I_t.png
  source: visual_clash:VC031
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC031 (text ''I(t)''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'I(t)'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC031 (text ''I(t)''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC031
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC032_low
  path: build/audit_crops/visual_clash/VC032_low.png
  source: visual_clash:VC032
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC032 (text ''low''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'low'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC032 (text ''low''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC032
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC033_crop
  path: build/audit_crops/visual_clash/VC033_crop.png
  source: visual_clash:VC033
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC033 (text '')''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label ')'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC033 (text '')''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC033
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC034_hig
  path: build/audit_crops/visual_clash/VC034_hig.png
  source: visual_clash:VC034
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC034 (text ''hig''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'hig'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC034 (text ''hig''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC034
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC035_h
  path: build/audit_crops/visual_clash/VC035_h.png
  source: visual_clash:VC035
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC035 (text ''h''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'h'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC035 (text ''h''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC035
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC036_n
  path: build/audit_crops/visual_clash/VC036_n.png
  source: visual_clash:VC036
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC036 (text ''n''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'n'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC036 (text ''n''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC036
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC037_d
  path: build/audit_crops/visual_clash/VC037_d.png
  source: visual_clash:VC037
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC037 (text ''d''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'd'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC037 (text ''d''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC037
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC038_Shallow
  path: build/audit_crops/visual_clash/VC038_Shallow.png
  source: visual_clash:VC038
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC038 (text ''Shallow''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'Shallow'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC038 (text ''Shallow''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC038
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC039_log
  path: build/audit_crops/visual_clash/VC039_log.png
  source: visual_clash:VC039
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC039 (text ''log''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'log'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC039 (text ''log''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC039
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC040_I
  path: build/audit_crops/visual_clash/VC040_I.png
  source: visual_clash:VC040
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC040 (text ''I''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'I'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC040 (text ''I''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC040
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
  anomaly_link: ''
- crop_id: VC041_f
  path: build/audit_crops/visual_clash/VC041_f.png
  source: visual_clash:VC041
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: 'Visual-clash candidate VC041 (text ''f''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  observed_objects:
  - label 'f'
  - the stroke or fill flagged by the clash detector
  local_relationship: 'Visual-clash candidate VC041 (text ''f''): label/glyph sits on its flagged stroke or fill but stays fully legible; intentional schematic register, not a collision.'
  candidate_refs:
  - VC041
  unintended_visible_anomaly: none
  anomaly_rationale: 'Host inspection: only the expected label glyph(s) and the flagged stroke/fill are present; no stray, doubled, or clipped mark beyond the candidate.'
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
directly (full render, Panel E, ISPD/probe convention, print-scale) and screened all 108
audit crops, the 41 visual-clash candidates, the 1 label-path candidate, and the 95
undeclared-geometry candidates via six parallel inspections, then personally re-inspected
every region flagged `present`/`uncertain`.

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
