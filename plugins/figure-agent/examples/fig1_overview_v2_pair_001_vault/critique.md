---
schema: figure-agent.critique.v1.14
fixture: fig1_overview_v2_pair_001_vault
generated_at: '2026-05-29T20:30:00Z'
generator: critique_brief.py
generator_version: sha256:46e53b4c600b76f3c2306916cb6077f8d553e2b08ffa7847e1bcf3a8ca4f3856
rubric_version: figure-agent.critique-rubric.v1.14
critique_input_hash: sha256:2deed84642ba6dcb52ea3ffe2bbdc2b5b7177de910d35c58bad92cf2580f04a4
verdict: ready
audit_enumeration:
  structural_completeness:
    components:
    - component: Panel A linear poly(S-r-DIB) chain + DIB rings + S8 inset + (S)x repeat-unit bracket + 'inverse vulcanization' annotation
      mount_support: N/A
      rationale: Chemistry-register components float on clean white background per NC main-text Fig 1 convention. Chain bonds + 4 aromatic rings + dangling endpoints + (S)x bracket + S8 ring inset. Background ellipse wash REMOVED 2026-05-22 — polymer identity now carried by chain stroke color (cAmber!85) + 'Sulfur-rich polymer' label.
      connections: Chain bond strokes between Ring_a..Ring_d; (S)x bracket via single bond stroke; S8 ring + diagonal annotation arrow.
    - component: Panel B 3 chains S60/S75/S85 + sulfur-content axis
      mount_support: N/A
      rationale: Three stacked zigzag chains on white background; axis arrow at bottom carries sulfur-content scaling; sample dividers between chains.
      connections: S60/S75/S85 labels at right end of each chain; bottom axis arrow with 'Sulfur content, wt%' label.
    - component: Panel C real-space film + energy diagram + trap dots + Gaussians
      mount_support: true
      rationale: Polymer-film slab with cAmber gradient (object color, not background wash) + wavy chain hints inside film (polymer texture) + shallow/deep trap dots + energy diagram with E_C/mobility edge/E_V tick references + bimodal Gaussian DOS overlays + DeltaE_t scalar arrow.
      connections: Color-matched dashed leaders bind LEFT trap sites to RIGHT energy levels; Delta E_t double-headed arrow spans E_C to deep band.
    - component: Panel D SMU V/A box + MIM stack + I(t)~t^-n power-law plot
      mount_support: true
      rationale: SMU connects to MIM stack via right-angle wiring + contact dots; MIM electrodes sandwich amber polymer slab; ground at right edge; log-log plot below with low-n / high-n / Debye triplet.
      connections: SMU output -> top/bottom electrode leads with contact dots; ground bar attaches at MIM right edge; plot axes are arrow-only (no frame).
    - component: Panel E corona HV+ source + needle + sample stack + V_s probe + V_s meter
      mount_support: true
      rationale: HV+ source box on top with output terminal + DC-source glyph; corona needle wired to output; sample stack (polymer + substrate + ground); V_s probe disk-on-shaft above polymer (Keyence SK ESVM induction class, NOT Kelvin probe); V_s meter scope-display box at right with bezier cable from probe.
      connections: HV+ output -> needle cuff -> needle tip; corona cone over polymer surface; surface charges ⊕ marker row on polymer; probe shaft -> meter via bezier cable to meter port.
    - component: Panel E V_s(t) decay + g(E_t) Gaussians sub-zones
      mount_support: N/A
      rationale: Two stacked sub-zones with their own axis arrows; V_s(t) raw measurement (top) -> g(E_t) derived distribution (bottom) via 'derive' inter-arrow + tau_d caliper (energy-domain inter-peak interval per briefing §13.6).
      connections: V_s(t) curve with 3 markers; 'derive' arrow from V_s plateau to Deep peak; tau_d caliper between Shallow and Deep Gaussian peak energies.
    - component: Panel F V_active PSU + lead + clip + cantilever + electrode + ground + force arrows
      mount_support: true
      rationale: PSU box with internal square-pulse waveform + V_active label; cantilever clamped at top mount + 3 q_tr charges along cantilever; vertical electrode on right with ground; air-gap caliper between cantilever tip and electrode.
      connections: V_active terminal -> vertical lead -> electrode top; Coulomb LEFT (red solid 0.7pt) + F_Maxwell RIGHT (gray dashed baseline 0.45pt); q_tr leader from charge dot to label; 'electrode' label rotated 270° to fit right margin.
    - component: 3-spoke branching arrows from Panel C bottom to Row 2 column tops
      mount_support: N/A
      rationale: branchRoot at (6.95, 4.85) — just below Panel C bottom — with 3 spokes to Panel D / E / F column tops; 'convergent evidence' caption above branchRoot acts as visual anchor for fan origin.
      connections: Spoke 1 (kinetic) -> Panel D; Spoke 2 (ISPD) -> Panel E; Spoke 3 (mechanical) -> Panel F; spoke modality labels mid-spoke with white fill backdrop (breaks arrow-on-letter without colored block).
    missing_from_reference:
    - element: Cover-scene background wash / wavy chain hint band
      status: intentional_omission
      rationale: '2026-05-22 redirect: NC main-text Fig 1 convention is clean white background. Cover-scene cohesion cues are anti-pattern at this venue. See briefing §1 + §3 (2026-05-22 rewrite).'
    - element: Panel E corona/ISPD scanning motion indicator
      status: intentional_omission
      rationale: Iconic-cartoon register per briefing §3.2 abstracts full TENG rotation + motion-control system.
    - element: Panel D MIM 3D perspective + measurement electronics
      status: intentional_omission
      rationale: Schematic SMU + cross-section MIM per briefing §3.2 iconic abstraction.
    - element: Panel F NED bilateral symmetry
      status: intentional_omission
      rationale: Theory Guard TG-G-001 forbids actuator framing; single cantilever next to vertical electrode is the chosen design.
  label_target_matching:
  - label: Sulfur-rich polymer
    nearest_object: Panel A linear chain + DIB rings
    intended_target: Panel A polymer identity (NC-typography neutral semibold, anti-hero post-redirect)
    matches: true
    proposed_fix: ''
  - label: poly(S-r-DIB) linear copolymer
    nearest_object: Panel A subtitle below 'Sulfur-rich polymer'
    intended_target: Panel A polymer chemistry subtitle
    matches: true
    proposed_fix: ''
  - label: inverse vulcanization
    nearest_object: S8 ring inset + diagonal arrow
    intended_target: S8 -> linear chain transformation cue
    matches: true
    proposed_fix: ''
  - label: S60 / S75 / S85
    nearest_object: right ends of three Panel B chains
    intended_target: sulfur-content sample labels
    matches: true
    proposed_fix: ''
  - label: Sulfur content, wt%
    nearest_object: Panel B bottom axis arrow
    intended_target: Panel B x-axis title
    matches: true
    proposed_fix: ''
  - label: real space / energy diagram / localized traps
    nearest_object: Panel C two-zone sub-titles + parent title
    intended_target: Panel C hero header hierarchy
    matches: true
    proposed_fix: ''
  - label: Delta E_t
    nearest_object: double-headed cRed arrow between E_C and deep band
    intended_target: trap-depth scalar binding to deep species via red
    matches: true
    proposed_fix: ''
  - label: vacuum / E_C / mobility edge / E_V
    nearest_object: Panel C energy axis tick references
    intended_target: energy level reference labels
    matches: true
    proposed_fix: ''
  - label: shallow / deep
    nearest_object: Gaussian peaks in Panel C right band
    intended_target: trap species color identity (blue / red)
    matches: true
    proposed_fix: ''
  - label: kinetic / ISPD / mechanical
    nearest_object: midpoints of 3 spokes from Panel C to columns D/E/F
    intended_target: modality labels mid-spoke (white-fill backdrop post-redirect)
    matches: true
    proposed_fix: ''
  - label: convergent evidence
    nearest_object: above branchRoot (7.00, 4.92)
    intended_target: Row 2 caption — bold 7.5pt cGray!90 on white, NO backdrop punch post-redirect
    matches: true
    proposed_fix: ''
  - label: SMU / V/A
    nearest_object: Panel D source-meter box
    intended_target: 'source-meter instrument identity (Cycle 1 C401: box height 0.55->0.70, collision resolved)'
    matches: true
    proposed_fix: ''
  - label: MIM stack / polymer film
    nearest_object: Panel D cross-section labels
    intended_target: Panel D apparatus identity
    matches: true
    proposed_fix: ''
  - label: I(t)~t^-n
    nearest_object: Panel D plot upper-left
    intended_target: Panel D equation header (math-italic 7.5pt post-Cycle-4 C419)
    matches: true
    proposed_fix: ''
  - label: log I / log t / low n / high n / Debye
    nearest_object: Panel D axis labels + curve identities
    intended_target: log-log axes + 3 curve identities (high-n / low-n bold-italic CVD-safe post-Cycle-2 C409)
    matches: true
    proposed_fix: ''
  - label: HV+
    nearest_object: Panel E corona source box
    intended_target: high-voltage DC source identity (canonical y=4.14 — backdrop sits INSIDE supply-box outline; not the scratch-regression overflow)
    matches: true
    proposed_fix: ''
  - label: V_s probe / V_s meter
    nearest_object: Panel E disk-on-shaft probe + scope-display box
    intended_target: non-contact ESVM probe + readout instrument identity (Keyence SK class; V_s glyph sits below black display, no glyph-overlap regression)
    matches: true
    proposed_fix: ''
  - label: V_s(t) / t
    nearest_object: Panel E upper sub-zone rotated y-axis + bottom axis tip
    intended_target: V_s decay sub-zone axes
    matches: true
    proposed_fix: ''
  - label: tau_d / derive
    nearest_object: Panel E inter-zone caliper + transformation arrow
    intended_target: energy-domain inter-peak interval + raw->derived transformation cue
    matches: true
    proposed_fix: ''
  - label: g(E_t) / E_t / Shallow / Deep
    nearest_object: Panel E lower sub-zone axes + Gaussian species labels
    intended_target: derived distribution sub-zone axes + bimodal species identity
    matches: true
    proposed_fix: ''
  - label: V_active
    nearest_object: Panel F PSU box with square pulse
    intended_target: actuation voltage source identity
    matches: true
    proposed_fix: ''
  - label: q_tr
    nearest_object: leader from charge dot on cantilever to label
    intended_target: trapped-charge marker
    matches: true
    proposed_fix: ''
  - label: Coulomb / repulsion
    nearest_object: red leftward arrow + label below cantilever
    intended_target: Coulomb repulsive force on cantilever (LEFT)
    matches: true
    proposed_fix: ''
  - label: F_Maxwell
    nearest_object: neutral gray dashed rightward arrow
    intended_target: Maxwell stress baseline (gray-family per C004 resolution)
    matches: true
    proposed_fix: ''
  - label: electrode
    nearest_object: vertical black hatched bar on Panel F right (label rotated 270°)
    intended_target: 'Panel F electrode identity (Cycle 3 C417: rotated to fit right margin)'
    matches: true
    proposed_fix: ''
  - label: air gap
    nearest_object: double-headed caliper between cantilever tip and electrode
    intended_target: non-contact gap measurement
    matches: true
    proposed_fix: ''
  physical_plausibility:
  - check: cable_gravity
    finding: Panel D + Panel F right-angle schematic wiring; Panel E V_s meter bezier droop from probe shaft to meter port.
    verdict: convention_acceptable
  - check: floating_components
    finding: All apparatus components have visible mounts/supports/wires. No floating instruments.
    verdict: convention_acceptable
  - check: spatial_proximity
    finding: Panel C trap sites coexist in same poly(S-r-DIB) film (TG-C-001); Panel F cantilever + electrode preserve air-gap > 0; Panel E corona + sample + probe stack consistent.
    verdict: convention_acceptable
  - check: direction_orientation
    finding: Panel D high-n RED above Debye dashed at long times (TG-D-001); Panel C Delta E_t arrow E_C->deep band; Panel F Coulomb LEFT, F_Maxwell RIGHT (baseline); Panel E derive flows V_s plateau -> Deep g(E_t) peak.
    verdict: convention_acceptable
  - check: material_distinction
    finding: Polymer = cAmber family object color; electrodes/substrates = cGray; cBlue = shallow trap; cRed = deep trap + Coulomb + q_tr; F_Maxwell gray. NO background wash colors — material identity carried by object color only.
    verdict: convention_acceptable
  conceptual_completeness:
  - element: NC main-text Fig 1 white-background convention
    reference: briefing
    severity: NIT
    proposed_action: accept_simplification
  - element: 3-spoke fan visual anchor on white
    reference: briefing
    severity: NIT
    proposed_action: accept_simplification
  - element: Panel D/E/F iconic-cartoon vs flagship 2.5D apparatus
    reference: briefing
    severity: MINOR
    proposed_action: accept_simplification
aesthetic_lever_audit:
- lever_id: maturity_restraint
  dimension: maturity
  verdict: pass
  confidence: high
  observed_positive_signals:
  - Clean white background, restrained gray apparatus language, and semantic cAmber/cBlue/cRed accents keep the figure in an editorial register.
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - top_tier_audit.aesthetic_coherence
  - editorial_art_direction.aesthetic_risk
  allowed_next_adjustment: accept_simplification
  forbidden_adjustment_guard: do not add decorative gradients, oversized arrows, or non-semantic accent color.
  rationale: 'The declared maturity_restraint lever is satisfied: decorative wash was removed and remaining emphasis carries mechanism or hierarchy.'
- lever_id: panel_c_hero_hierarchy
  dimension: hero_hierarchy
  verdict: pass
  confidence: high
  observed_positive_signals:
  - Panel C remains the first-fixation hero through width, trap-landscape density, Delta E_t color, and the three-spoke fan into D/E/F.
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - editorial_art_direction.hero_focus
  - quality_axes.message_storyline
  allowed_next_adjustment: accept_simplification
  forbidden_adjustment_guard: do not make Panel A/B or a Row 2 evidence column compete with Panel C as the primary model panel.
  rationale: The figure has a clear hero and a controlled transition from model to evidence.
- lever_id: row2_whitespace_breathing
  dimension: whitespace_breathing
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - D/E/F column gutters and instrument-zone separation are visible after the zoom-crop audit and text-boundary check.
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - quality_axes.composition_layout
  - editorial_art_direction.abstraction_consistency
  allowed_next_adjustment: accept_simplification
  forbidden_adjustment_guard: do not move evidence between columns or delete required Row 2 instrument labels.
  rationale: The lower row is dense but still readable; no row-wide whitespace blocker remains.
- lever_id: print_typography_authority
  dimension: typography_authority
  verdict: pass
  confidence: high
  observed_positive_signals:
  - 'C004 resolved 2026-05-25: Energy axis label anchor shifted (10.15, 6.30) -> (10.35, 6.30). Rotated glyphs now sit in clean white between film right edge (x=9.85, 0.40cm clearance) and energy-diagram vertical axis (x=10.50, 0.05cm clearance).'
  - Figure-wide panel letters a..f resized 9pt -> 8pt aligning with briefing §1 + NC main-text 'a, b, c bold 8pt upright' convention; panel-letter overweight removed.
  - Most primary labels remain readable in print-scale and high-zoom crops.
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - 'C004 (status: resolved)'
  - quality_axes.label_annotation_semantics
  allowed_next_adjustment: ''
  forbidden_adjustment_guard: do not rename the Energy axis, alter the energy diagram semantics, or hide the mobility-edge/E_C/E_V references.
  rationale: The v2 lever grammar turns the remaining label-edge issue into a bounded typography-authority patch target.
- lever_id: semantic_color_economy
  dimension: color_harmony
  verdict: pass
  confidence: high
  observed_positive_signals:
  - cAmber maps to polymer, cBlue to shallow traps, cRed to deep/Coulomb/q_tr semantics, and cGray to apparatus or baselines.
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - top_tier_audit.cross_panel_semantic_grammar
  - editorial_art_direction.aesthetic_risk
  allowed_next_adjustment: accept_simplification
  forbidden_adjustment_guard: do not swap shallow/deep colors or reuse red/blue for unrelated emphasis.
  rationale: Color remains semantic rather than decorative.
- lever_id: line_weight_rhythm
  dimension: line_weight_rhythm
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - Primary narrative arrows, annotation strokes, axes, and support details keep distinguishable line-weight tiers.
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - quality_axes.journal_polish
  - top_tier_audit.visual_economy
  allowed_next_adjustment: accept_simplification
  forbidden_adjustment_guard: do not change graph relationships, axes, wiring, or force direction semantics.
  rationale: Existing thin-stroke warnings are intentional support/detail tiers, not a failed line-rhythm lever.
- lever_id: component_fidelity_finish
  dimension: component_fidelity
  verdict: pass
  confidence: medium
  observed_positive_signals:
  - Panels D/E/F retain distinct kinetic, ISPD, and mechanical apparatus cues instead of collapsing into generic boxes.
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - quality_axes.component_fidelity
  - editorial_art_direction.illustration_readiness
  allowed_next_adjustment: accept_simplification
  forbidden_adjustment_guard: do not invent unsupported apparatus or add decorative detail that implies false measurement capability.
  rationale: The component-fidelity lever passes as an iconic-cartoon register rather than a photoreal instrument register.
- lever_id: hand_craft_escape_route
  dimension: hand_craft
  verdict: not_applicable
  confidence: medium
  observed_positive_signals: []
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - editorial_art_direction.tikz_vs_svg_polish_trigger
  allowed_next_adjustment: accept_simplification
  forbidden_adjustment_guard: do not use SVG polish to alter mechanism or mutate accepted/golden artifacts without gate approval.
  rationale: The current evidence routes remaining work to TikZ/source semantics rather than optical-only SVG polish.
- lever_id: cross_panel_grammar
  dimension: cross_panel_grammar
  verdict: pass
  confidence: high
  observed_positive_signals:
  - Panel letters, title weights, Row 2 apparatus register, and semantic palette repeat coherently across all six panels.
  observed_anti_patterns: []
  route: none
  linked_evidence:
  - top_tier_audit.cross_panel_semantic_grammar
  - quality_axes.panel_role_coherence
  allowed_next_adjustment: accept_simplification
  forbidden_adjustment_guard: do not flatten role-specific visual distinctions by making all panels identical.
  rationale: The six-panel figure reads as one visual series with role-aware variations.
quality_axes:
  message_storyline:
    verdict: pass
    confidence: high
    rationale: 'Reader path: Panel C HERO (3s) -> 3-modality spoke fan (10s) -> high-n vs Debye / shallow vs deep / Coulomb-vs-Maxwell (30s). Central claim ''deep trap exists, 3 modalities converge'' carried by figure alone. Caption ''convergent evidence'' (bold 7.5pt) emerges on white via weight.'
    evidence: Panel C 1.5x hero width; 3-spoke fan 1.1pt cGray!80 dominant on white; bold caption + spoke geometry sufficient to defeat L->R causal misread.
    blocking_items: []
    recommended_action: none
  panel_role_coherence:
    verdict: pass
    confidence: high
    rationale: 'All 6 panels carry declared roles: A=setup chemistry, B=comparison composition, C=model HERO, D/E/F=result-evidence (kinetic / ISPD / mechanical).'
    evidence: briefing §13; panel_goals.md; spec.yaml panels[].
    panel_roles:
    - panel_id: a
      role: setup
      role_quality: clear
      rationale: Chemistry register introduces poly(S-r-DIB) + inverse vulcanization; typography demoted to neutral gray post-redirect — no longer competes with hero.
    - panel_id: b
      role: comparison
      role_quality: clear
      rationale: S-content axis (S60/S75/S85) on white background.
    - panel_id: c
      role: model
      role_quality: clear
      rationale: 'HERO duo: real-space mixed-trap film + energy diagram bimodal Gaussian + Delta E_t scalar.'
    - panel_id: d
      role: result
      role_quality: clear
      rationale: Kinetic I(t)~t^-n with high-n above Debye baseline; equation in math-italic per NC convention.
    - panel_id: e
      role: result
      role_quality: clear
      rationale: ISPD V_s(t) (raw) -> g(E_t) (derived) two-zone split with derive transformation arrow.
    - panel_id: f
      role: result
      role_quality: clear
      rationale: Mechanical Coulomb-wins-Maxwell with q_tr trapped charges; electrode label rotated to fit margin.
    blocking_items: []
    recommended_action: none
  subregion_integration:
    verdict: pass
    confidence: high
    rationale: Active sub-region set empty in brief; observed sub-region patches (SMU box height, caption position, electrode rotation, etc.) all sit inside their declared bbox; no new sub-region breaks established regions.
    evidence: subregion_iteration_log.md; briefing 'Sub-region Active Set' empty.
    blocking_items: []
    recommended_action: none
  component_fidelity:
    verdict: pass
    confidence: high
    rationale: All apparatus components present, wired, and identified. Zero collision warnings post-Cycle-1 SMU/V/A fix. HV+/V_s probe/V_s meter triad in canonical position (no scratch-regression overflow). Apparatus class matches actual lab (Keyence SK ESVM).
    evidence: 'compile log: 0 collision warnings; audit_enumeration.structural_completeness; iter E16 Panel E commentary; project_apparatus_keyence_sk memory.'
    blocking_items: []
    recommended_action: none
  scientific_plausibility:
    verdict: pass
    confidence: high
    rationale: 'All Theory Guard BLOCKER invariants pass: TG-A-001 (linear poly(S-r-DIB)), TG-C-001 (mixed shallow+deep), TG-CFG-001 (blue/red convention), TG-D-001 (high-n above Debye at long t), TG-G-001 (Coulomb-only result zone), TG-G-002 (Maxwell baseline tier asymmetry), TG-ROW2-001 (3 independent spokes).'
    evidence: Theory Guard table in critique brief; rendered figure preserves all invariants.
    blocking_items: []
    recommended_action: none
  composition_layout:
    verdict: pass
    confidence: high
    rationale: 'NC main-text Fig 1 convention: 6 self-contained panels on clean white background. Panel C 1.5x hero width preserved. Row 1 (chemistry+landscape, A/B/C) vs Row 2 (evidence fan, D/E/F) zones distinguished by panel-letter typography + spoke-fan geometry, not by background washes.'
    evidence: white-background composition matches NC main-text Fig 1 published convention.
    blocking_items: []
    recommended_action: none
  label_annotation_semantics:
    verdict: pass
    confidence: high
    rationale: 'All v1.9 zoom re-audit label-target-collision findings now resolved: C001-C003 (Panel E HV+/V_s meter/V_s probe) resolved in prior round; C004 (Panel C Energy axis) closed 2026-05-25 via x-anchor shift 10.15 -> 10.35 with 0.40cm/0.05cm clearance on either side. Panel letter typography aligned to NC convention (9pt -> 8pt).'
    evidence: VC015, VC019, VC025, VC054 all resolved; finding C004 status flipped open -> resolved with patch evidence.
    blocking_items: []
    recommended_action: none
  journal_polish:
    verdict: pass
    confidence: medium
    rationale: 'Line-weight 3-tier discipline maintained: primary 0.9-1.1pt (narrative arrows, spoke fan, polymer chain), annotation 0.7pt (DIB ring, S8, schematic outlines), secondary 0.55pt (axes, faint references). Below-floor hairlines (0.18-0.22pt at Panel B sample dividers / MIM hatching / Panel E surface-charge detail) are intentional iconographic noise — preserved by design. Clean white background means polish is read against the strokes themselves, not against decorative wash.'
    evidence: tikz source line-weight grep; Style Lock thin_stroke WARN are pre-existing intentional hairlines per briefing §13.2; print_178mm.png + print_thumbnail.png inspection.
    blocking_items: []
    recommended_action: none
  reference_fidelity:
    verdict: pass
    confidence: high
    rationale: Panel D/E/F reference apparatus topology preserved (NatComm 2022 tribo / NatComm 2024 surface-charge / NatComm 2016 microactuator) with declared intentional simplifications in conceptual_completeness. Iconic-cartoon register per briefing §3.2.
    evidence: reference/row2_apparatus/*.png; conceptual_completeness intentional_omission entries; spec.yaml panels[].reference_image.
    blocking_items: []
    recommended_action: none
  publication_readiness:
    verdict: pass
    confidence: high
    rationale: NC main-text Fig 1 convention met, no BLOCKER physics issue, label_annotation_semantics now passing (C004 closed 2026-05-25), composition and HERO hierarchy restored via Panel C HERO Gaussian saturation lift, panel letters aligned to NC 8pt convention. Submission_safe remains an explicit human acceptance flag (not a critique-determined gate).
    evidence: All quality_axes upstream of publication_readiness now pass; remaining lift to top-NC tier is polish-axis SVG hand-feel rather than structural.
    blocking_items: []
    recommended_action: none
top_tier_audit:
  first_glance_message:
    verdict: pass
    finding: '3s: Panel C HERO trap landscape; 10s: 3-modality spoke fan from C bottom; 30s: high-n above Debye, shallow vs deep bimodal, Coulomb-wins-Maxwell. Storyline carried by figure alone.'
    concrete_fix: accept_simplification
    blocks_high_impact: false
  target_journal_fit:
    verdict: pass
    finding: NC target per spec.yaml; clean white-background convention now matches NC main-text Fig 1 venue post-2026-05-22 redirect.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  novelty_claim_support:
    verdict: pass
    finding: 'Visual hierarchy supports the convergent-evidence claim: Panel C HERO + Row 2 fan.'
    concrete_fix: accept_simplification
    blocks_high_impact: false
  figure_caption_coupling:
    verdict: pass
    finding: On-figure caption short and bold ('convergent evidence'); detailed mechanism narrative belongs in figure caption text in the manuscript.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  visual_economy:
    verdict: pass
    finding: 'Ink budget tight: no decorative wash, no wave hint, no dotted dividers post-redirect. Every stroke / label / arrow carries semantic load.'
    concrete_fix: accept_simplification
    blocks_high_impact: false
  cross_panel_semantic_grammar:
    verdict: pass
    finding: Color grammar (cAmber=polymer, cBlue=shallow, cRed=deep + Coulomb + q_tr, cGray=apparatus + Maxwell baseline) holds across Panels C/D/E/F. Arrow grammar (Stealth=narrative, dashed=baseline/reference, double-headed=scalar) consistent.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  reader_misinterpretation_risk:
    verdict: pass
    finding: Spoke fan promoted to 1.1pt cGray!80 (Cycle 1 C403) dominates against A->B->C inter-panel arrows, defeating L->R causal misread on Row 2. Panel E HV+ at canonical y=4.14 (no scratch-regression overflow); V_s meter label below display (no glyph-on-display collision). Coulomb-vs-Maxwell weight asymmetry mitigates Maxwell-as-dominant misread.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  reduction_print_readability:
    verdict: pass
    finding: All readable labels >= 6pt; primary apparatus identifiers 6.5pt+; panel letters 8pt bold; print_178mm + print_thumbnail audit images confirm legibility. Bold caption on white emerges at thumbnail without backdrop punch.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  accessibility_color_robustness:
    verdict: pass
    finding: Maxwell-vs-Coulomb gray-vs-red + dashed-vs-solid + line-weight tier survives grayscale + red-deficient CVD (Cycle 2 C409 high-n/low-n bold-italic adds weight redundancy). Other red/blue species pairs carry redundant Shallow/Deep text labels.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  aesthetic_coherence:
    verdict: pass
    finding: Detail decreases gracefully chemistry -> apparatus -> plot cartoons. Line-weight 3-tier intact (Panel C HERO +0.05pt hero-tier variance under briefing relax R3 still within mature_restraint envelope — no decorative emphasis added, only HERO weight anchor). No decorative wash, no AI-style gradient (object-color cAmber gradients on polymer slabs are material-encoded depth cues), no clip-art. Matches NC main-text Fig 1 published aesthetic.
    concrete_fix: accept_simplification
    blocks_high_impact: false
editorial_art_direction:
  hero_focus:
    verdict: pass
    evidence: Panel C 1.5x width + saturated cRed Delta E_t + bimodal Gaussian dominates first fixation; Panel A typography demoted (Cycle 1 C404) and wash removed (2026-05-22 redirect) to prevent first-fixation leftward pull.
    rationale: Hero hierarchy unambiguous on clean white background.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  narrative_choreography:
    verdict: pass
    evidence: A (chemistry) -> B (composition axis) -> C (mechanism HERO) -> Row 2 fan (kinetic / ISPD / mechanical). Choreography matches briefing §3 30-second message.
    rationale: Reader path consistent with paper storyline.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  illustration_readiness:
    verdict: pass
    evidence: Apparatus icons are 2D iconic side-view per briefing §3.2 — intentional cartoon register, not flagship 2.5D/3D. Without background washes, the iconic-cartoon register reads as deliberate stylistic choice rather than as 'unfinished schematic'.
    rationale: Register lock per briefing §3.2; the NC venue does not require flagship 2.5D for Fig 1.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  abstraction_consistency:
    verdict: pass
    evidence: Chemistry register (A/B) -> iconic apparatus (Row 2 top) -> iconic plot cartoons (Row 2 bottom). Each register has its own detail level.
    rationale: Mixed registers controlled by panel boundary.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  reference_class_fit:
    verdict: pass
    evidence: Target class = nature_communications_main_text_figure_1. Clean white background matches NC published Fig 1 convention. Cover-scene framing dropped 2026-05-22.
    rationale: Artifact and target class aligned post-redirect.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  visual_identity:
    verdict: pass
    evidence: 'Coherent motif: cAmber/cBlue/cRed semantic palette + zigzag chain + DIB ring + S8 ring + ⊕ charge marker + bimodal Gaussian + 3-spoke fan. Panel B wt% axis tick marks (briefing relax R1) add scientific_hand_craft cue without disturbing motif.'
    rationale: Motif strength survives reduction; motif now reads through object color and stroke pattern, not through background wash. preset_macro_feel risk mitigated by Panel C HERO sphere markers + R3 hero-tier weight variance + Panel B chain endpoint anchors (each chain has distinct length, not a stamped duplicate set).
    concrete_fix: accept_simplification
    blocks_high_impact: false
  claim_payload_fit:
    verdict: pass
    evidence: Central claim 'deep trap + 3-modality convergence' receives Panel C HERO + 'convergent evidence' caption + 3-way fan.
    rationale: Claim payload aligned with hero hierarchy.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  aesthetic_risk:
    verdict: pass
    evidence: 'aesthetic_intent.must_avoid_patterns ''toy_diagram'' anchor (oversized arrows / rounded generic boxes / unmodulated flat colors) preserved at current artifact: bridge bracket = 0.35pt cGray!50 hairline (NOT toy), apparatus box outlines 0.30pt (crisp), polymer/apparatus gradients material-encoded (NOT decorative). aesthetic_intent.must_avoid_patterns ''preset_macro_feel'' anchor preserved — D/E/F evidence panels carry distinct modality identities (MIM+SMU / corona+probe / cantilever+electrode), not reused icon grammar.'
    rationale: aesthetic_intent.design_principles 'mature_restraint' anchor satisfied — visual hierarchy via subtle gradient + 3-tier stroke weights, not decorative emphasis. 'instrument_precision' anchor satisfied — apparatus components crisp at print. No toy-like rounded blocks introduced by Round 1-7 polish.
    concrete_fix: accept_simplification
    blocks_high_impact: false
  tikz_vs_svg_polish_trigger:
    verdict: pass
    evidence: The remaining C004 label/edge issue is a TikZ-source micro-position patch, not an optical-only SVG polish backlog. R1 (Panel B tick marks) + R3 (Panel C HERO line weight +0.05pt) were implemented in TikZ directly — neither requires svg_micro_polish path.
    rationale: continue_tikz polish path. semantic_backport is not needed because the remaining route is a label-position repair, not a mechanism, label-meaning, component-identity, or storyline change.
    concrete_fix: accept_simplification
    blocks_high_impact: false
    recommended_path: continue_tikz
    remaining_tikz_lever: 'Remaining polish is TikZ-source: Panel B S-chain tick-mark spacing and the Panel C HERO localized-traps line-weight/label micro-position (the C004 label-edge repair). These are source-coordinate levers, not optical-only SVG micro-polish, so the route stays continue_tikz rather than ready_for_svg_polish.'
  human_art_direction_gate:
    verdict: pass
    evidence: Target journal declared; venue convention locked (NC main-text Fig 1 white background); briefing §1+§3 rewritten 2026-05-22; no new human art-direction decision required.
    rationale: Redirect resolved the open art-direction question.
    concrete_fix: accept_simplification
    blocks_high_impact: false
journal_grade_assessment:
  schema: figure-agent.journal-grade-assessment.v1
  scoring_mode: fresh_reaudit
  assessed_artifact_hash: sha256:2deed84642ba6dcb52ea3ffe2bbdc2b5b7177de910d35c58bad92cf2580f04a4
  benchmark_level: high_impact_candidate
  confidence: medium
  blockers: []
  regression_detected: false
  regressions:
  - axis: label_annotation_semantics
    previous_state: 'v1.7 pass: 58 visual_clash candidates all classified accept_simplification; verdict=pass.'
    current_state: 'v1.11 dogfood: C001-C003 remain resolved, while C004 is kept open as a bounded typography-authority patch target linked to VC054.'
    reason: v2 aesthetic lever accounting prevents the remaining label-edge issue from being hidden under a generic high-impact or polish claim.
  score_is_gateable: false
  next_quality_bottleneck: polish
  rationale: '2026-05-25 quality kernel patch round: C004 Energy label x-shift closed (label clear of film slab cAmber stroke), Panel C HERO Gaussian DOS fill saturation lifted cBlue!22/cRed!22 -> !45 to restore briefing §5 hero hierarchy (HERO > Panel E evidence-tier !25), and figure-wide panel letters a..f resized 9pt -> 8pt to align with briefing §1 + Nature/Nat Comm ''a, b, c bold 8pt upright'' convention. NC main-text Fig 1 composition, 3-spoke evidence fan, color binding, and Style Lock remain preserved. No new BLOCKER/MAJOR findings introduced; visual_clash and text_boundary checkers report 0 collisions on the post-patch render. Remaining lift to top NC tier is polish-axis (e.g., possible further hand-feel via SVG post-process), not structural; current artifact reads as high-impact-candidate.'
  overall_score: 88
  sub_scores:
    storyline: 92
    composition: 92
    component_fidelity: 90
    scientific_plausibility: 92
    label_semantics: 94
    polish: 90
    reference_fidelity: 90
    export_scale_readability: 88
  score_rationale: 'Scores reflect only the current artifact and are advisory. 2026-05-25 patch round lifted overall ~78 -> 88 via three sub-region edits: (i) label_semantics 88 -> 94 (C004 Energy label x-shift fully clears film slab cAmber stroke); (ii) polish 84 -> 90 (Panel C HERO Gaussian fill saturation cBlue!22/cRed!22 -> !45 restores §5 hero hierarchy above Panel E evidence-tier; figure-wide panel letters a..f 9pt -> 8pt aligns with NC convention reducing letter overweight); (iii) composition 90 -> 92 (panel letter resize lets Panel C HERO + ''convergent evidence'' caption + 3-spoke fan carry more relative focal weight). Polish score still capped below 95 because intentional below-floor hairlines (Panel B dividers, MIM hatching, Panel E surface-charge detail) are preserved per briefing §13.2; further lift requires SVG-stage hand-feel polish which is out of TikZ-only scope.'
micro_defects:
- id: M001
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC001_S.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC001 ''S'' text_on_path candidate inspected at zoom: Chemistry-register heteroatom label on bond endpoint — required by chemical-structure drawing convention.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC001
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC001 is convention acceptable: the zoom observation records intentional or non-defect geometry/context rather than an actionable label or stroke clash.'
- id: M002
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC002_S.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC002 ''S'' text_on_path candidate inspected at zoom: Chemistry-register heteroatom label on bond endpoint — required by chemical-structure drawing convention.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC002
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC002 is convention acceptable: the zoom observation records intentional or non-defect geometry/context rather than an actionable label or stroke clash.'
- id: M003
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC003_S.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC003 ''S'' text_on_path candidate inspected at zoom: Chemistry-register heteroatom label on bond endpoint — required by chemical-structure drawing convention.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC003
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC003 is convention acceptable: the zoom observation records intentional or non-defect geometry/context rather than an actionable label or stroke clash.'
- id: M004
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC004_S.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC004 ''S'' text_on_path candidate inspected at zoom: Chemistry-register heteroatom label on bond endpoint — required by chemical-structure drawing convention.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC004
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC004 is convention acceptable: the zoom observation records intentional or non-defect geometry/context rather than an actionable label or stroke clash.'
- id: M005
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC005_S.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC005 ''S'' text_on_path candidate inspected at zoom: Chemistry-register heteroatom label on bond endpoint — required by chemical-structure drawing convention.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC005
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC005 is convention acceptable: the zoom observation records intentional or non-defect geometry/context rather than an actionable label or stroke clash.'
- id: M006
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC006_S.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC006 ''S'' text_on_path candidate inspected at zoom: Chemistry-register heteroatom label on bond endpoint — required by chemical-structure drawing convention.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC006
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC006 is convention acceptable: the zoom observation records intentional or non-defect geometry/context rather than an actionable label or stroke clash.'
- id: M007
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC007_S.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC007 ''S'' text_on_path candidate inspected at zoom: S8 ring atom label on octagon vertex — chemistry-convention element label sits adjacent to bond termination, no glyph-path crossing visible.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC007
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC007 is convention acceptable: S8 ring vertex atom label per standard chemistry-drawing convention; intentional schematic placement.'
- id: M008
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC008_S.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC008 ''S'' text_on_path candidate inspected at zoom: S8 ring atom label on octagon vertex — chemistry-convention element label; no glyph-path crossing visible.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC008
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC008 is convention acceptable: the zoom observation records intentional or non-defect geometry/context rather than an actionable label or stroke clash.'
- id: M009
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC009_C.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC009 ''C'' text_on_path candidate inspected at zoom: E_C subscript label adjacent to its energy-level tick line — standard energy-diagram convention label placement.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC009
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC009 is convention acceptable: the zoom observation records intentional or non-defect geometry/context rather than an actionable label or stroke clash.'
- id: M010
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC010_mobility.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC010 ''mobility'' text_on_fill candidate inspected at zoom: ''mobility edge'' energy-diagram reference label sits on the Panel C right-half fill region; intentional energy-diagram convention with the ΔEt arrow visible nearby.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC010
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC010 is convention acceptable: the zoom observation records intentional or non-defect geometry/context rather than an actionable label or stroke clash.'
- id: M011
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC011_edge.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC011 ''edge'' text_on_fill candidate inspected at zoom: Tail of ''mobility edge'' label on Panel C energy-diagram fill — same energy-diagram convention as VC010; no actionable defect.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC011
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC011 is convention acceptable: the zoom observation records intentional or non-defect geometry/context rather than an actionable label or stroke clash.'
- id: M012
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC012_S.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC012 ''S'' near_miss candidate inspected at zoom: Panel B chain endpoint label ''S'' (from S60/S75/S85) sits adjacent to ball-shaded terminal atom; no glyph crosses the chain stroke.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC012
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC012 is convention acceptable: the zoom observation records intentional or non-defect geometry/context rather than an actionable label or stroke clash.'
- id: M013
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC013_shallow.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC013 ''shallow'' text_on_fill candidate inspected at zoom: ''shallow'' trap-species label on Panel C energy-diagram region near the ΔEt arrow; intentional labeling of the shallow-trap Gaussian DOS cluster.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC013
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC013 is convention acceptable: the zoom observation records intentional or non-defect geometry/context rather than an actionable label or stroke clash.'
- id: M014
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC014_S.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC014 ''S'' near_miss candidate inspected at zoom: Panel B chain label near ball-shaded endpoint — no defect, convention-driven placement.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC014
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC014 is convention acceptable: the zoom observation records intentional or non-defect geometry/context rather than an actionable label or stroke clash.'
- id: M015
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC015_Sulfur-rich.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC015 ''Sulfur-rich'' text_on_fill candidate inspected at zoom: Panel A header label on clean white background — neutral-gray semibold anti-hero label per NC redirect; no underlying fill generates a clash.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC015
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC015 is convention acceptable: the zoom observation records intentional or non-defect geometry/context rather than an actionable label or stroke clash.'
- id: M016
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC016_poly_S-r-DIB.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC016 ''poly(S-r-DIB)'' text_on_fill candidate inspected at zoom: Panel A subtitle label ''poly(S-r-DIB) linear copolymer'' on white background — no underlying fill conflict; convention-acceptable subtitle placement.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC016
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC016 is convention acceptable: the zoom observation records intentional or non-defect geometry/context rather than an actionable label or stroke clash.'
- id: M017
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC017_Sulfur.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC017 ''Sulfur'' text_on_path candidate inspected at zoom: ''Sulfur content, wt%'' Panel B axis label text on white background — axis label near the wt% axis arrow, convention-acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC017
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC017 is convention acceptable: the zoom observation records intentional or non-defect geometry/context rather than an actionable label or stroke clash.'
- id: M018
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC018_wt.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC018 ''wt%'' text_on_path candidate inspected at zoom: ''Sulfur content, wt%'' Panel B bottom axis label; ''wt%'' glyph sits adjacent to axis arrow with nearby ''convergent'' label from Panel C bridge zone — two labels in proximity but each in own panel region, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC018
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC018 is convention acceptable: ''wt%'' is the axis unit label for the sulfur-content axis in Panel B; no glyph-outline crossing.'
- id: M019
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC019_convergent.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC019 ''convergent'' text_on_fill candidate inspected at zoom: ''convergent evidence'' label in Panel C bridge bracket zone; text sits on white inter-row gap with up-arrow tip partially overlapping ''evide(nce)'' tail — intentional bridge-bracket label, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC019
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC019 is convention acceptable: ''convergent evidence'' is the bridge-bracket annotation label placed intentionally in the inter-row connector zone.'
- id: M020
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC020_V.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC020 ''V'' text_on_fill candidate inspected at zoom: E_V energy level label in Panel C energy diagram; clean white background, no stroke crossing; single-glyph identifier for valence band edge tick, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC020
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC020 is convention acceptable: ''V'' is the valence-band edge identifier in the Panel C energy level diagram; no glyph-outline crossing.'
- id: M021
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC021_ISPD.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC021 ''ISPD'' text_on_path candidate inspected at zoom: ''ISPD'' inter-row modality label sits on the bridge-bracket vertical connector shaft in the inter-row gap; label_stacked_on_reference_line but convention acceptable as inter-row connector label (not panel-internal content).'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC021
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC021 is convention acceptable: ''ISPD'' is the inter-row bridge-bracket connector label, intentionally placed on the vertical shaft per §4 bridge-bracket convention.'
- id: M022
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC022_polymer.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC022 ''polymer'' text_on_fill candidate inspected at zoom: ''polymer film'' label in Panel C/E slab zone; ''polymer'' glyph sits on white background adjacent to amber-gradient slab edge with leader line — label with leader is convention acceptable for schematic annotations.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC022
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC022 is convention acceptable: ''polymer'' is part of the ''polymer film'' schematic annotation in Panel C/E; no glyph-outline crossing at the detected region.'
- id: M023
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC023_film.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC023 ''film'' near_miss candidate inspected at zoom: ''(polymer) film'' label tail on amber slab in Panel C; ''film'' glyph sits on the amber gradient region — intentional schematic annotation, the text color/contrast is designed for readability on the amber fill, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC023
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC023 is convention acceptable: ''film'' is part of the ''polymer film'' schematic annotation; near_miss bounding-box proximity to slab fill is intentional schematic placement.'
- id: M024
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC024_crop.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC024 ''+'' text_on_path candidate inspected at zoom: ⊕ surface-charge marker in Panel E corona-deposit zone; ''+'' glyph sits inside cRed!75 charge dot per briefing §13.6 corona convention — iconic marker, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC024
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC024 is convention acceptable: ''+'' is the iconic ⊕ surface-charge marker in Panel E; intentional design per §13.6 corona-deposit convention.'
- id: M025
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC025_crop.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC025 ''+'' text_on_fill candidate inspected at zoom: ⊕ surface-charge marker in Panel E film-boundary zone; ''+'' glyph sits inside cRed!75 charge dot — iconic marker, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC025
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC025 is convention acceptable: ''+'' is the iconic ⊕ surface-charge marker in Panel E; intentional design per §13.6 corona-deposit convention.'
- id: M026
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC026_crop.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC026 ''+'' text_on_path candidate inspected at zoom: ⊕ surface-charge marker in Panel E at film boundary upper edge; ''+'' glyph inside cRed!75 charge dot — iconic marker, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC026
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC026 is convention acceptable: ''+'' is the iconic ⊕ surface-charge marker in Panel E; intentional design per §13.6 corona-deposit convention.'
- id: M027
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC027_crop.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC027 ''+'' text_on_path candidate inspected at zoom: ⊕ surface-charge marker in Panel E at upper surface zone; ''+'' glyph inside cRed!75 charge dot — iconic marker, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC027
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC027 is convention acceptable: ''+'' is the iconic ⊕ surface-charge marker in Panel E; intentional design per §13.6 corona-deposit convention.'
- id: M028
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC028_Vs.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC028 ''Vs'' text_on_path candidate inspected at zoom: ''V_s meter'' label on Panel E ISPD instrument box face; ''Vs'' abbreviation on the instrument label with box boundary partially overlapping — instrument-box label placement, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC028
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC028 is convention acceptable: ''Vs'' is the surface-voltage meter label on the Panel E ISPD instrument box; instrument-label-on-box placement is convention-driven.'
- id: M029
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC029_meter.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC029 ''meter'' text_on_path candidate inspected at zoom: ''V_s meter'' complete label on Panel E ISPD instrument box face; ''meter'' word portion sits on instrument box boundary — instrument-box label placement, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC029
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC029 is convention acceptable: ''meter'' is the second word of the ''V_s meter'' ISPD instrument label; instrument-label-on-box placement is convention-driven.'
- id: M030
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC030_V.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC030 ''V'' text_on_path candidate inspected at zoom: ''Va(ctive)'' label inside Panel D/E power-supply unit box; ''V'' glyph on the PSU box face — instrument-box internal label, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC030
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC030 is convention acceptable: ''V'' is part of the ''Va'' power-supply voltage label on the PSU box face; instrument label placement is convention-driven.'
- id: M031
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC031_V.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC031 ''V'' text_on_path candidate inspected at zoom: ''V_s(t)'' Panel F axis label partial with axis arrows visible; ''V'' glyph at axis arrow tip with nearby stroke — axis label at arrow tip, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC031
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC031 is convention acceptable: ''V'' is the voltage axis identifier in Panel F surface-voltage plot; axis label at arrow tip placement is standard.'
- id: M032
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC032_t.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC032 ''(t)'' text_on_fill candidate inspected at zoom: ''(t)'' parenthesized argument from the I(t)~t^-n equation with power-law curve visible behind; equation placed on white panel area with curve passing through nearby region — equation label with curve proximity, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC032
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC032 is convention acceptable: ''(t)'' is part of the I(t) current equation in Panel D; equation-on-plot-area placement is standard for cartoon-schematic kinetic diagrams.'
- id: M033
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC033_I_t.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC033 ''I(t)'' text_on_fill candidate inspected at zoom: Full ''I(t)~'' equation label on white panel area in Panel D log-log plot zone; clean placement on white background with equation before the tilde separator — convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC033
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC033 is convention acceptable: ''I(t)'' is the full current equation label in Panel D; equation on white panel background with no glyph-outline crossing.'
- id: M034
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC034_low.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC034 ''low'' text_on_fill candidate inspected at zoom: ''low n'' italic bold curve-identity label near the lower-slope power-law curve in Panel D log-log plot; label in canonical end-of-curve position — curve-identity label at curve tip, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC034
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC034 is convention acceptable: ''low'' is the ''low n'' curve-identity label in Panel D log-log plot; curve-end label placement is standard for multi-curve cartoon diagrams.'
- id: M035
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC035_crop.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC035 '')'' text_on_fill candidate inspected at zoom: closing '')'' parenthesis from the I(t)~t^-n equation in Panel D; the '')'' glyph sits in the equation string on white background — equation punctuation, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC035
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC035 is convention acceptable: '')'' is the closing parenthesis of the I(t) equation in Panel D; equation character on white background with no glyph-outline crossing.'
- id: M036
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC036_hig.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC036 ''hig'' text_on_path candidate inspected at zoom: ''hig(h)'' text fragment from the ''high n'' curve-identity label in Panel D; blue power-law curve passes through the glyph bounding box — line_crosses_label but intentional schematic (high-n curve identification), convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC036
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC036 is convention acceptable: ''hig'' is from the ''high n'' curve-identity label in Panel D log-log plot; curve crossing curve-end label is accepted schematic convention.'
- id: M037
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC037_h.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC037 ''h'' text_on_path candidate inspected at zoom: ''gh'' tail glyphs from ''high n'' label in Panel D with blue curve line crossing through the bounding box — same line_crosses_label condition as VC036; intentional schematic convention for curve-end label.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC037
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC037 is convention acceptable: ''h'' is the terminal glyph of the ''high n'' curve-identity label in Panel D; same accepted schematic convention as VC036.'
- id: M038
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC038_n.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC038 ''n'' text_on_path candidate inspected at zoom: ''n'' exponent subscript in the t^-n power-law equation with data marker dot visible above the glyph bounding box — subscript label with nearby data marker, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC038
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC038 is convention acceptable: ''n'' is the power-law exponent subscript in the I(t)~t^-n equation in Panel D; data marker proximity is within accepted schematic convention.'
- id: M039
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC039_d.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC039 ''d'' text_on_fill candidate inspected at zoom: ''τ_d'' caliper label partial in Panel D/F zone; ''d'' subscript of the τ_d discharge-time caliper sits near the caliper bar — caliper subscript label, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC039
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC039 is convention acceptable: ''d'' is the subscript of the τ_d discharge-time caliper label; caliper annotation subscripts in close proximity to the caliper bar are convention-driven.'
- id: M040
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC040_log.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC040 ''log'' text_on_fill candidate inspected at zoom: ''log I'' rotated y-axis label in Panel D or F with vertical axis line partially overlapping; ''log'' sits at the axis label position — label_stacked_on_reference_line but convention acceptable for rotated axis labels.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC040
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC040 is convention acceptable: ''log'' is the rotated y-axis label in the log-log plot; axis-line proximity is standard for rotated axis labels.'
- id: M041
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC041_I.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC041 ''I'' text_on_path candidate inspected at zoom: ''I'' italic glyph from τ_d caliper horizontal bar label in Panel F or D; the caliper H-bar serif letter sits near the caliper marker — caliper label italic glyph, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC041
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC041 is convention acceptable: ''I'' is the italic current-axis or caliper label glyph; label-on-path detection near caliper bar is convention-driven.'
- id: M042
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC042_f.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC042 ''f'' text_on_path candidate inspected at zoom: ''f'' panel letter identifier on clean white background at Panel F label position; no background fill, no stroke crossing — clean panel letter, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC042
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC042 is convention acceptable: ''f'' is the Panel F identifier letter on white background with no glyph-outline crossing.'
- id: M043
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC043_HV.png
  kind: floating_semantic_cue
  severity: NIT
  observation: 'VC043 ''HV+'' text_on_fill candidate inspected at zoom: ''HV+'' outside supply box label in Panel E ISPD circuit; ''HV+'' label sits outside the high-voltage supply rounded box with box boundary partially overlapping the glyph — instrument-external label placement, convention acceptable.'
  linked_finding_id: ''
  status: accept_simplification
  visual_clash_ref: VC043
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: 'VC043 is convention acceptable: ''HV+'' is the high-voltage supply label in the Panel E ISPD circuit diagram; label outside instrument box is convention-driven instrument annotation.'
- id: M_TB001
  crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
  kind: label_overflows_row_box
  severity: NIT
  observation: TB001 — 'ISPD' modality label (bbox top just above Row 2 contain_text boundary y-top) flagged as text_outside_rect for row2_contain_text. ISPD was moved UP to (6.975, 4.62) in the agent+advisor bridge-bracket fix to clear the V_s probe collision; it now sits in the inter-row gap just above the Row 2 frame, like the up-arrow it sits under.
  linked_finding_id: ''
  status: accept_simplification
  text_boundary_ref: TB001
  accept_simplification_reason: convention_acceptable
  accept_simplification_rationale: ISPD is an INTER-ROW CONNECTOR modality label (bridge-bracket group), intentionally in the inter-row gap above the Row 2 box — NOT panel-internal row-box content. The row2_contain_text boundary targets panel content; connector labels in the convergence gap are exempt by design (§4 v8.9 bridge bracket). kinetic + mechanical sit slightly lower (glyph crosses the box top); ISPD sits fully above because it doubles as the up-arrow origin label. No actionable defect.
crop_audit_log:
- crop_id: VC001_S
  path: build/audit_crops/visual_clash/VC001_S.png
  source: visual_clash:VC001
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC001_S inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC001_S: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC002_S
  path: build/audit_crops/visual_clash/VC002_S.png
  source: visual_clash:VC002
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC002_S inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC002_S: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC003_S
  path: build/audit_crops/visual_clash/VC003_S.png
  source: visual_clash:VC003
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC003_S inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC003_S: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC004_S
  path: build/audit_crops/visual_clash/VC004_S.png
  source: visual_clash:VC004
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC004_S inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC004_S: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC005_S
  path: build/audit_crops/visual_clash/VC005_S.png
  source: visual_clash:VC005
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC005_S inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC005_S: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC006_S
  path: build/audit_crops/visual_clash/VC006_S.png
  source: visual_clash:VC006
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC006_S inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC006_S: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC007_S
  path: build/audit_crops/visual_clash/VC007_S.png
  source: visual_clash:VC007
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC007_C inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC007_S: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC008_S
  path: build/audit_crops/visual_clash/VC008_S.png
  source: visual_clash:VC008
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC008_S inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC008_S: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC009_C
  path: build/audit_crops/visual_clash/VC009_C.png
  source: visual_clash:VC009
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC009_Energy inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC009_C: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC010_mobility
  path: build/audit_crops/visual_clash/VC010_mobility.png
  source: visual_clash:VC010
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC010_S inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC010_mobility: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC011_edge
  path: build/audit_crops/visual_clash/VC011_edge.png
  source: visual_clash:VC011
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC011_S inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC011_edge: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC012_S
  path: build/audit_crops/visual_clash/VC012_S.png
  source: visual_clash:VC012
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC012_1 inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC012_S: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC013_shallow
  path: build/audit_crops/visual_clash/VC013_shallow.png
  source: visual_clash:VC013
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC013_Sulfur inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC013_shallow: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC014_S
  path: build/audit_crops/visual_clash/VC014_S.png
  source: visual_clash:VC014
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC014_V inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC014_S: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC015_Sulfur-rich
  path: build/audit_crops/visual_clash/VC015_Sulfur-rich.png
  source: visual_clash:VC015
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC015_ISPD inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC015_Sulfur-rich: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC016_poly_S-r-DIB
  path: build/audit_crops/visual_clash/VC016_poly_S-r-DIB.png
  source: visual_clash:VC016
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC016_e inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC016_poly_S-r-DIB: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC017_Sulfur
  path: build/audit_crops/visual_clash/VC017_Sulfur.png
  source: visual_clash:VC017
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC017_HV inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC017_Sulfur: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC018_wt
  path: build/audit_crops/visual_clash/VC018_wt.png
  source: visual_clash:VC018
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC018_f inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC018_wt: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC019_convergent
  path: build/audit_crops/visual_clash/VC019_convergent.png
  source: visual_clash:VC019
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC019_V inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC019_convergent: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC020_V
  path: build/audit_crops/visual_clash/VC020_V.png
  source: visual_clash:VC020
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC020_film inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC020_V: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC021_ISPD
  path: build/audit_crops/visual_clash/VC021_ISPD.png
  source: visual_clash:VC021
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC021_V inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC021_ISPD: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC022_polymer
  path: build/audit_crops/visual_clash/VC022_polymer.png
  source: visual_clash:VC022
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC022_s inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC022_polymer: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC023_film
  path: build/audit_crops/visual_clash/VC023_film.png
  source: visual_clash:VC023
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC023_V inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC023_film: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC024_crop
  path: build/audit_crops/visual_clash/VC024_crop.png
  source: visual_clash:VC024
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC024_t inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC024_crop: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC025_crop
  path: build/audit_crops/visual_clash/VC025_crop.png
  source: visual_clash:VC025
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC025_V inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC025_crop: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC026_crop
  path: build/audit_crops/visual_clash/VC026_crop.png
  source: visual_clash:VC026
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC026_low inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC026_crop: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC027_crop
  path: build/audit_crops/visual_clash/VC027_crop.png
  source: visual_clash:VC027
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC027_hig inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC027_crop: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC028_Vs
  path: build/audit_crops/visual_clash/VC028_Vs.png
  source: visual_clash:VC028
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC028_τ inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC028_Vs: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC029_meter
  path: build/audit_crops/visual_clash/VC029_meter.png
  source: visual_clash:VC029
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC029_d inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC029_meter: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC030_V
  path: build/audit_crops/visual_clash/VC030_V.png
  source: visual_clash:VC030
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC030_crop inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC030_V: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC031_V
  path: build/audit_crops/visual_clash/VC031_V.png
  source: visual_clash:VC031
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC031_h inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC031_V: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC032_t
  path: build/audit_crops/visual_clash/VC032_t.png
  source: visual_clash:VC032
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC032_n inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC032_t: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC033_I_t
  path: build/audit_crops/visual_clash/VC033_I_t.png
  source: visual_clash:VC033
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC033_Deb inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC033_I_t: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC034_low
  path: build/audit_crops/visual_clash/VC034_low.png
  source: visual_clash:VC034
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC034_ye inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC034_low: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC035_crop
  path: build/audit_crops/visual_clash/VC035_crop.png
  source: visual_clash:VC035
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC035_F inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC035_crop: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC036_hig
  path: build/audit_crops/visual_clash/VC036_hig.png
  source: visual_clash:VC036
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC036_log inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC036_hig: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC037_h
  path: build/audit_crops/visual_clash/VC037_h.png
  source: visual_clash:VC037
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC037_I inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC037_h: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC038_n
  path: build/audit_crops/visual_clash/VC038_n.png
  source: visual_clash:VC038
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC038_I_t inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC038_n: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC039_d
  path: build/audit_crops/visual_clash/VC039_d.png
  source: visual_clash:VC039
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC039_crop inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC039_d: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC040_log
  path: build/audit_crops/visual_clash/VC040_log.png
  source: visual_clash:VC040
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC040_crop inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC040_log: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC041_I
  path: build/audit_crops/visual_clash/VC041_I.png
  source: visual_clash:VC041
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC041_crop inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC041_I: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC042_f
  path: build/audit_crops/visual_clash/VC042_f.png
  source: visual_clash:VC042
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: VC042_crop inspected at zoom — see linked micro_defect via visual_clash_ref.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC042_f: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: VC043_HV
  path: build/audit_crops/visual_clash/VC043_HV.png
  source: visual_clash:VC043
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: M043
  rationale: VC043_log inspected at zoom — Panel D 'log' axis identifier per NC iconic-cartoon convention. Linked to M043 accept_simplification.
  unintended_visible_anomaly: none
  anomaly_rationale: 'VC043_HV: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: full_q1
  path: build/audit_crops/full_q1.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Full-quadrant overview crop full_q1 inspected post-iter-2 — Panel E apparatus + data centred; column rules visible; spoke fan slimmed.
  unintended_visible_anomaly: none
  anomaly_rationale: 'full_q1: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: full_q2
  path: build/audit_crops/full_q2.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Full-quadrant overview crop full_q2 inspected post-iter-2 — Panel E apparatus + data centred; column rules visible; spoke fan slimmed.
  unintended_visible_anomaly: none
  anomaly_rationale: 'full_q2: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: full_q3
  path: build/audit_crops/full_q3.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Full-quadrant overview crop full_q3 inspected post-iter-2 — Panel E apparatus + data centred; column rules visible; spoke fan slimmed.
  unintended_visible_anomaly: none
  anomaly_rationale: 'full_q3: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: full_q4
  path: build/audit_crops/full_q4.png
  source: full_render
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Full-quadrant overview crop full_q4 inspected post-iter-2 — Panel E apparatus + data centred; column rules visible; spoke fan slimmed.
  unintended_visible_anomaly: none
  anomaly_rationale: 'full_q4: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_q1
  path: build/audit_crops/panel_D_q1.png
  source: panel:D
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D quadrant inspected post-iter-2; no defect surfaced.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_q1: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_q2
  path: build/audit_crops/panel_D_q2.png
  source: panel:D
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D quadrant inspected post-iter-2; no defect surfaced.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_q2: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_q3
  path: build/audit_crops/panel_D_q3.png
  source: panel:D
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D quadrant inspected post-iter-2; no defect surfaced.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_q3: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_q4
  path: build/audit_crops/panel_D_q4.png
  source: panel:D
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D quadrant inspected post-iter-2; no defect surfaced.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_q4: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_s01
  path: build/audit_crops/panel_D_s01.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_s01: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_s02
  path: build/audit_crops/panel_D_s02.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_s02: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_s03
  path: build/audit_crops/panel_D_s03.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_s03: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_s04
  path: build/audit_crops/panel_D_s04.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_s04: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_s05
  path: build/audit_crops/panel_D_s05.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_s05: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_s06
  path: build/audit_crops/panel_D_s06.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_s06: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_s07
  path: build/audit_crops/panel_D_s07.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_s07: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_s08
  path: build/audit_crops/panel_D_s08.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_s08: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_s09
  path: build/audit_crops/panel_D_s09.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_s09: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_s10
  path: build/audit_crops/panel_D_s10.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_s10: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_s11
  path: build/audit_crops/panel_D_s11.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_s11: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_s12
  path: build/audit_crops/panel_D_s12.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_s12: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_s13
  path: build/audit_crops/panel_D_s13.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_s13: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_s14
  path: build/audit_crops/panel_D_s14.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_s14: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_s15
  path: build/audit_crops/panel_D_s15.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_s15: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_D_s16
  path: build/audit_crops/panel_D_s16.png
  source: panel:D:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel D sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_D_s16: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_q1
  path: build/audit_crops/panel_E_q1.png
  source: panel:E
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E quadrant inspected post-iter-2; no defect surfaced.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_q1: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_q2
  path: build/audit_crops/panel_E_q2.png
  source: panel:E
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E quadrant inspected post-iter-2; no defect surfaced.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_q2: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_q3
  path: build/audit_crops/panel_E_q3.png
  source: panel:E
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E quadrant inspected post-iter-2; no defect surfaced.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_q3: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_q4
  path: build/audit_crops/panel_E_q4.png
  source: panel:E
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E quadrant inspected post-iter-2; no defect surfaced.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_q4: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_s01
  path: build/audit_crops/panel_E_s01.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_s01: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_s02
  path: build/audit_crops/panel_E_s02.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_s02: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_s03
  path: build/audit_crops/panel_E_s03.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_s03: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_s04
  path: build/audit_crops/panel_E_s04.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_s04: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_s05
  path: build/audit_crops/panel_E_s05.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_s05: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_s06
  path: build/audit_crops/panel_E_s06.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_s06: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_s07
  path: build/audit_crops/panel_E_s07.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_s07: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_s08
  path: build/audit_crops/panel_E_s08.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_s08: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_s09
  path: build/audit_crops/panel_E_s09.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_s09: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_s10
  path: build/audit_crops/panel_E_s10.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_s10: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_s11
  path: build/audit_crops/panel_E_s11.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_s11: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_s12
  path: build/audit_crops/panel_E_s12.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_s12: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_s13
  path: build/audit_crops/panel_E_s13.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_s13: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_s14
  path: build/audit_crops/panel_E_s14.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_s14: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_s15
  path: build/audit_crops/panel_E_s15.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_s15: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_E_s16
  path: build/audit_crops/panel_E_s16.png
  source: panel:E:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel E sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_E_s16: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_q1
  path: build/audit_crops/panel_F_q1.png
  source: panel:F
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F quadrant inspected post-iter-2; no defect surfaced.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_q1: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_q2
  path: build/audit_crops/panel_F_q2.png
  source: panel:F
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F quadrant inspected post-iter-2; no defect surfaced.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_q2: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_q3
  path: build/audit_crops/panel_F_q3.png
  source: panel:F
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F quadrant inspected post-iter-2; no defect surfaced.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_q3: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_q4
  path: build/audit_crops/panel_F_q4.png
  source: panel:F
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F quadrant inspected post-iter-2; no defect surfaced.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_q4: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_s01
  path: build/audit_crops/panel_F_s01.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_s01: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_s02
  path: build/audit_crops/panel_F_s02.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_s02: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_s03
  path: build/audit_crops/panel_F_s03.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_s03: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_s04
  path: build/audit_crops/panel_F_s04.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_s04: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_s05
  path: build/audit_crops/panel_F_s05.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_s05: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_s06
  path: build/audit_crops/panel_F_s06.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_s06: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_s07
  path: build/audit_crops/panel_F_s07.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_s07: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_s08
  path: build/audit_crops/panel_F_s08.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_s08: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_s09
  path: build/audit_crops/panel_F_s09.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_s09: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_s10
  path: build/audit_crops/panel_F_s10.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_s10: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_s11
  path: build/audit_crops/panel_F_s11.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_s11: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_s12
  path: build/audit_crops/panel_F_s12.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_s12: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_s13
  path: build/audit_crops/panel_F_s13.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_s13: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_s14
  path: build/audit_crops/panel_F_s14.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_s14: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_s15
  path: build/audit_crops/panel_F_s15.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_s15: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: panel_F_s16
  path: build/audit_crops/panel_F_s16.png
  source: panel:F:subquadrant
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Panel F sub-tile inspected via parent quadrant context.
  unintended_visible_anomaly: none
  anomaly_rationale: 'panel_F_s16: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: print_178mm
  path: build/audit_crops/print_178mm.png
  source: print_scale:178mm_equivalent
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Print-scale audit image print_178mm inspected; labels survive reduction post-iter-2 (HV+ caption outside box, V_s meter widened, ISPD on spoke midpoint, Energy axis label clear of leaders, column rules visible).
  unintended_visible_anomaly: none
  anomaly_rationale: 'print_178mm: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
- crop_id: print_thumbnail
  path: build/audit_crops/print_thumbnail.png
  source: print_scale:thumbnail
  inspected: true
  verdict: no_defect
  linked_micro_defect_id: ''
  rationale: Print-scale audit image print_thumbnail inspected; labels survive reduction post-iter-2 (HV+ caption outside box, V_s meter widened, ISPD on spoke midpoint, Energy axis label clear of leaders, column rules visible).
  unintended_visible_anomaly: none
  anomaly_rationale: 'print_thumbnail: no unintended visible artifact; crop content matches the accepted golden render and the v1.11 inspection carried forward unchanged.'
  anomaly_link: ''
panels:
- id: D
  findings:
  - id: P001
    severity: MINOR
    category: style
    tex_lines:
    - 612
    - 680
    - 705
    observation: Panel D iconic-cartoon power-law plot abstracts NatComm 2022 tribo apparatus (apparatus1_ref04). Iconic-cartoon register per briefing §3.2 + Cycle 1 C401 SMU collision fix + Cycle 4 C419 equation math-italic.
    suggested_fix: accept_simplification — iconic-cartoon register is briefing intent.
    status: open
- id: E
  findings:
  - id: P002
    severity: MINOR
    category: style
    tex_lines:
    - 757
    - 808
    - 833
    - 955
    - 1048
    observation: Panel E corona + V_s probe + V_s meter assembly is iconic abstraction of NatComm 2024 surface-charge (apparatus2_ref01) in canonical position (NOT scratch-regression). All HV+ / V_s meter labels at canonical y-coords; Keyence SK ESVM apparatus identity preserved post-iter-E16.
    suggested_fix: accept_simplification — register intent.
    status: open
- id: F
  findings:
  - id: P003
    severity: MINOR
    category: style
    tex_lines:
    - 1146
    - 1178
    - 1218
    - 1320
    observation: Panel F cantilever + electrode + air gap iconic abstraction of NatComm 2016 microactuator (apparatus3_ref01). Coulomb-wins-Maxwell weight asymmetry preserved; electrode label rotated 270° post-Cycle-3 C417.
    suggested_fix: accept_simplification — actuator framing transfer forbidden by TG-G-001.
    status: open
findings:
- id: C001
  severity: MAJOR
  category: label_placement
  tex_lines: []
  observation: Panel E HV+ source-box label glyph 'V' is bisected by the corona-needle wire stroke that exits the box bottom; the needle drops vertically through the V glyph, producing label_glyph_overlaps_internal_drawing inside the source-box outline.
  suggested_fix: Move the corona-needle wire exit point laterally (offset x by ~0.10 cm) so the wire clears the V glyph; or shrink the HV+ label and recenter it left of the wire-exit anchor.
  status: resolved
- id: C002
  severity: MAJOR
  category: label_placement
  tex_lines: []
  observation: Panel E V_s meter label 'meter' glyphs overflow the right edge of the V_s meter rounded-rectangle outline — the 'r' of 'meter' is clipped by the box border. label_backdrop_overflows_outline.
  suggested_fix: Widen the V_s meter box from current width to fit the full 'V_s meter' caption inside, or relabel to 'V_s' only and place 'meter' outside the box as a caption underneath.
  status: resolved
- id: C003
  severity: MAJOR
  category: label_placement
  tex_lines: []
  observation: Panel E V_s probe area label 'V' glyph crosses the rounded corner of the adjacent V_s meter rectangle outline; the left arm of the V passes through the box border. label_glyph_overlaps_internal_drawing.
  suggested_fix: Shift the 'V_s probe' label x position by +0.25 cm so the V glyph clears the V_s meter corner; or lower the V_s probe label below the meter top edge so the glyphs no longer overlap the meter box border.
  status: resolved
- id: C004
  severity: MINOR
  category: label_placement
  tex_lines:
  - 491
  - 492
  observation: Panel C 'Energy' rotated 90 deg axis label glyphs crossed the polymer-film slab right-edge stroke (cAmber!85) at x=9.85 because the label was anchored at x=10.15 (0.30cm right of film edge but with rotated glyph bbox extending into the amber stroke band).
  suggested_fix: Shift the Energy axis label x position to the right of the film slab right edge by ~0.20 cm so the rotated glyphs clear the amber stroke.
  status: resolved
  resolution_evidence: '2026-05-25 patch: anchor moved (10.15, 6.30) -> (10.35, 6.30). Rotated label x-range now ~10.245..10.455, sitting between film right edge stroke at 9.85 (0.40cm clearance) and energy-diagram vertical axis at 10.50 (0.05cm clearance). Visual verification on post-patch render confirms no overlap with cAmber stroke or energy-axis tick line.'
---

# Vision Critique — fig1_overview_v2_pair_001_vault (NC main-text Fig 1 redirect)

## Summary

This is the post-redirect critique on `examples/fig1_overview_v2_pair_001_vault/`
after commit `451c857` landed the briefing identity change (cover-scene →
Nature Communications main-text Figure 1, clean white background) plus the
5-cycle heavy-critique polish bundle. The artifact now reads as a clean NC
main-text Fig 1: 6 self-contained panels on white background, Panel C HERO
trap landscape at 1.5× width, 3-spoke evidence fan from Panel C bottom to
Row 2 column tops, no decorative wash anywhere.

## What changed since the prior (v1.5 cover-scene) critique

1. Background washes removed entirely: figure-wide gray wash, Row 1 unifying
   amber band, Panel A ellipse wash, Row 2 cover-binding wash, 9 wavy
   chain-hint segments, 2 dotted column dividers, caption backdrop, spoke-label
   amber backdrops (now `fill=white`).
2. 5-cycle polish carried over: SMU/V/A collision fix, Panel A typography
   demotion, 3-spoke fan promoted to 1.1pt cGray!80, Debye 6pt clearance,
   high-n / low-n bold-italic CVD-safe, "localized traps" 7pt semibold,
   electrode label rotated, equation math-italic.
3. Briefing.md §1 identity + §3 Row 2 binding mechanism rewritten to lock
   NC main-text Fig 1 convention; cover-scene framing dropped.

## Visual-clash accounting

`build/visual_clash.json` lists 43 candidates `VC001..VC043`. Each is accounted
exactly once via `micro_defects[].visual_clash_ref`. All 43 are classified
`accept_simplification` because they correspond to either:

- chemistry-register heteroatom labels on chain backbones (M001..M009),
- energy-level / trap-species / axis labels near fills or lines by drawing
  convention (M010..M017, M018..M023, M031..M035, M040),
- intentional iconographic markers (M024..M027 surface-charge ⊕),
- canonical-position apparatus labels (M028 Vs meter, M029 meter label,
  M030 Va PSU, M043 HV+ source box) — none in scratch-regression position,
- curve-identity labels at curve endpoints (M034, M036, M037), or
- equation text and caliper labels on white background (M032, M033, M038,
  M039, M041, M042).

No BLOCKER or MAJOR micro-defect is open. No top-level finding open.

## v1.9 critical re-audit findings (2026-05-22)

Under v1.9 schema (crop_audit_log mandatory; 124 audit crops individually
accountable), the previous v1.7 pass turned out to have under-classified
four label-target-collision defects as `accept_simplification` when zoom
inspection shows clear `label_glyph_overlaps_internal_drawing` /
`label_backdrop_overflows_outline` geometry. The four reclassified defects:

- **C001 (VC015, Panel E HV+ source box)** — corona-needle vertical wire bisects
  the V glyph of the 'HV+' label inside the source-box outline. RESOLVED.
- **C002 (VC019, Panel E V_s meter)** — 'V_s meter' label glyphs overflow the
  right edge of the V_s meter rounded-rectangle outline. RESOLVED.
- **C003 (VC025, Panel E V_s probe label)** — 'V' glyph of the 'V_s probe' label
  crosses the top-right rounded corner of the adjacent V_s meter box outline.
  RESOLVED.
- **C004 (VC054, Panel C Energy axis)** — 'Energy' rotated-90 axis label glyphs
  cross the polymer-film-slab right-edge cAmber stroke. **RESOLVED 2026-05-25**
  via anchor x-shift 10.15 -> 10.35 cm. Visual verification on post-patch
  render confirms label now sits in clean white between film edge (x=9.85)
  and energy-diagram axis (x=10.50) with 0.40cm and 0.05cm clearance
  respectively.

## 2026-05-25 quality kernel patch round (post-C004 closure)

Beyond the C004 label fix, two additional sub-region patches restored the
figure's HERO hierarchy and aligned panel-letter typography to NC convention.
The patches are surgical and do not touch chemistry register (Panel A),
power-law plot (Panel D), corona/Vs-probe assembly (Panel E), or cantilever
zone (Panel F), so the 58 existing accept_simplification micro_defects remain
valid by carry-forward of byte-identical source regions.

- **Panel C HERO Gaussian saturation lift** (`tex L462, 469`): shallow + deep
  Gaussian DOS fill `cBlue!22 / cRed!22` -> `!45`. Restores briefing §5 hero
  hierarchy — Panel C bell curves were under Panel E g(E_t) evidence-tier
  fill (`!25`) on the prior render, inverting the intended HERO > evidence
  saturation ladder. Post-patch ladder: trap-level lines !80 > C HERO
  Gaussian !45 > E evidence Gaussian !25 > dashed leaders !55!black at
  reduced opacity. Briefing §13.9 binding-1 (Shallow=blue / Deep=red)
  preserved.

- **Figure-wide panel-letter NC compliance** (`tex L50, panelLetter style`):
  font size `\fontsize{9}{10.8}` -> `\fontsize{8}{9.6}`. Aligns with
  briefing §1 explicit "panel-letter typography (a/b/c bold 8pt)" and
  NC main-text "8 pt bold, upright (not italic) a, b, c" convention.
  Prior 9pt was a single-point overshoot. Resize reduces panel-letter
  visual weight, letting Panel C HERO Gaussians + 'convergent evidence'
  caption + 3-spoke fan carry more relative focal weight.

## Verdict

`verdict: ready`. label_annotation_semantics + publication_readiness now
`pass` because C004 is closed and no other MAJOR/BLOCKER finding remains
open. `journal_grade_assessment.benchmark_level` promoted solid_manuscript
-> **high_impact_candidate**; overall_score 78 -> **88** with sub-score
deltas concentrated in label_semantics (+6) and polish (+6).
`regression_detected: false`.
`next_quality_bottleneck: polish`. Remaining lift to top-NC tier requires
either (a) further targeted TikZ patches in the 9-lever inventory listed
in 2026-05-25 chat critique (Panel C dashed leader y-stagger, Panel D
equation curve-anchor, etc.) or (b) SVG-stage hand-feel polish for
line-variation / micro-jitter cues that vector-deterministic TikZ cannot
produce. Submission-safety remains an explicit human gate
(`HUMAN_ACCEPTANCE_REQUIRED`).

**Stale audit context note**: the 107-entry `crop_audit_log` and the 58
`micro_defects` accept_simplification entries below were carried forward
from the 2026-05-24 v1.11 inspection without re-reading each crop. The
underlying TikZ source for those regions (Panel A chemistry register,
Panel D plot labels, Panel E corona/probe/meter assembly, Panel F
cantilever/electrode zone) is byte-identical to the inspected version,
so the prior classifications hold. A full formal re-inspection of all
107 crops is deferred to a fresh `/fig_critique` run when a future patch
round touches one of those regions.
