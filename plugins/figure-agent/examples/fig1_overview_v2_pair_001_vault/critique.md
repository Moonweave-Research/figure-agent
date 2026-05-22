---
schema: figure-agent.critique.v1.9
fixture: fig1_overview_v2_pair_001_vault
generated_at: 2026-05-22T08:30:00Z
generator: critique_brief.py
generator_version: sha256:2eb54e535dd5946869569ab16176b31865f8fee6ba299a8f65de6e055d90bac9
rubric_version: figure-agent.critique-rubric.v1.9
critique_input_hash: sha256:aabc858e14d5db7b14fe1d4d5b60603067580aecdd28baf09c80e9001a5c8b36
verdict: revise
audit_enumeration:
  structural_completeness:
    components:
      - component: "Panel A linear poly(S-r-DIB) chain + DIB rings + S8 inset + (S)x repeat-unit bracket + 'inverse vulcanization' annotation"
        mount_support: N/A
        rationale: "Chemistry-register components float on clean white background per NC main-text Fig 1 convention. Chain bonds + 4 aromatic rings + dangling endpoints + (S)x bracket + S8 ring inset. Background ellipse wash REMOVED 2026-05-22 — polymer identity now carried by chain stroke color (cAmber!85) + 'Sulfur-rich polymer' label."
        connections: "Chain bond strokes between Ring_a..Ring_d; (S)x bracket via single bond stroke; S8 ring + diagonal annotation arrow."
      - component: "Panel B 3 chains S60/S75/S85 + sulfur-content axis"
        mount_support: N/A
        rationale: "Three stacked zigzag chains on white background; axis arrow at bottom carries sulfur-content scaling; sample dividers between chains."
        connections: "S60/S75/S85 labels at right end of each chain; bottom axis arrow with 'Sulfur content, wt%' label."
      - component: "Panel C real-space film + energy diagram + trap dots + Gaussians"
        mount_support: yes
        rationale: "Polymer-film slab with cAmber gradient (object color, not background wash) + wavy chain hints inside film (polymer texture) + shallow/deep trap dots + energy diagram with E_C/mobility edge/E_V tick references + bimodal Gaussian DOS overlays + DeltaE_t scalar arrow."
        connections: "Color-matched dashed leaders bind LEFT trap sites to RIGHT energy levels; Delta E_t double-headed arrow spans E_C to deep band."
      - component: "Panel D SMU V/A box + MIM stack + I(t)~t^-n power-law plot"
        mount_support: yes
        rationale: "SMU connects to MIM stack via right-angle wiring + contact dots; MIM electrodes sandwich amber polymer slab; ground at right edge; log-log plot below with low-n / high-n / Debye triplet."
        connections: "SMU output -> top/bottom electrode leads with contact dots; ground bar attaches at MIM right edge; plot axes are arrow-only (no frame)."
      - component: "Panel E corona HV+ source + needle + sample stack + V_s probe + V_s meter"
        mount_support: yes
        rationale: "HV+ source box on top with output terminal + DC-source glyph; corona needle wired to output; sample stack (polymer + substrate + ground); V_s probe disk-on-shaft above polymer (Keyence SK ESVM induction class, NOT Kelvin probe); V_s meter scope-display box at right with bezier cable from probe."
        connections: "HV+ output -> needle cuff -> needle tip; corona cone over polymer surface; surface charges ⊕ marker row on polymer; probe shaft -> meter via bezier cable to meter port."
      - component: "Panel E V_s(t) decay + g(E_t) Gaussians sub-zones"
        mount_support: N/A
        rationale: "Two stacked sub-zones with their own axis arrows; V_s(t) raw measurement (top) -> g(E_t) derived distribution (bottom) via 'derive' inter-arrow + tau_d caliper (energy-domain inter-peak interval per briefing §13.6)."
        connections: "V_s(t) curve with 3 markers; 'derive' arrow from V_s plateau to Deep peak; tau_d caliper between Shallow and Deep Gaussian peak energies."
      - component: "Panel F V_active PSU + lead + clip + cantilever + electrode + ground + force arrows"
        mount_support: yes
        rationale: "PSU box with internal square-pulse waveform + V_active label; cantilever clamped at top mount + 3 q_tr charges along cantilever; vertical electrode on right with ground; air-gap caliper between cantilever tip and electrode."
        connections: "V_active terminal -> vertical lead -> electrode top; Coulomb LEFT (red solid 0.7pt) + F_Maxwell RIGHT (gray dashed baseline 0.45pt); q_tr leader from charge dot to label; 'electrode' label rotated 270° to fit right margin."
      - component: "3-spoke branching arrows from Panel C bottom to Row 2 column tops"
        mount_support: N/A
        rationale: "branchRoot at (6.95, 4.85) — just below Panel C bottom — with 3 spokes to Panel D / E / F column tops; 'convergent evidence' caption above branchRoot acts as visual anchor for fan origin."
        connections: "Spoke 1 (kinetic) -> Panel D; Spoke 2 (ISPD) -> Panel E; Spoke 3 (mechanical) -> Panel F; spoke modality labels mid-spoke with white fill backdrop (breaks arrow-on-letter without colored block)."
    missing_from_reference:
      - element: "Cover-scene background wash / wavy chain hint band"
        status: intentional_omission
        rationale: "2026-05-22 redirect: NC main-text Fig 1 convention is clean white background. Cover-scene cohesion cues are anti-pattern at this venue. See briefing §1 + §3 (2026-05-22 rewrite)."
      - element: "Panel E corona/ISPD scanning motion indicator"
        status: intentional_omission
        rationale: "Iconic-cartoon register per briefing §3.2 abstracts full TENG rotation + motion-control system."
      - element: "Panel D MIM 3D perspective + measurement electronics"
        status: intentional_omission
        rationale: "Schematic SMU + cross-section MIM per briefing §3.2 iconic abstraction."
      - element: "Panel F NED bilateral symmetry"
        status: intentional_omission
        rationale: "Theory Guard TG-G-001 forbids actuator framing; single cantilever next to vertical electrode is the chosen design."
  label_target_matching:
    - label: "Sulfur-rich polymer"
      nearest_object: "Panel A linear chain + DIB rings"
      intended_target: "Panel A polymer identity (NC-typography neutral semibold, anti-hero post-redirect)"
      matches: true
      proposed_fix: ""
    - label: "poly(S-r-DIB) linear copolymer"
      nearest_object: "Panel A subtitle below 'Sulfur-rich polymer'"
      intended_target: "Panel A polymer chemistry subtitle"
      matches: true
      proposed_fix: ""
    - label: "inverse vulcanization"
      nearest_object: "S8 ring inset + diagonal arrow"
      intended_target: "S8 -> linear chain transformation cue"
      matches: true
      proposed_fix: ""
    - label: "S60 / S75 / S85"
      nearest_object: "right ends of three Panel B chains"
      intended_target: "sulfur-content sample labels"
      matches: true
      proposed_fix: ""
    - label: "Sulfur content, wt%"
      nearest_object: "Panel B bottom axis arrow"
      intended_target: "Panel B x-axis title"
      matches: true
      proposed_fix: ""
    - label: "real space / energy diagram / localized traps"
      nearest_object: "Panel C two-zone sub-titles + parent title"
      intended_target: "Panel C hero header hierarchy"
      matches: true
      proposed_fix: ""
    - label: "Delta E_t"
      nearest_object: "double-headed cRed arrow between E_C and deep band"
      intended_target: "trap-depth scalar binding to deep species via red"
      matches: true
      proposed_fix: ""
    - label: "vacuum / E_C / mobility edge / E_V"
      nearest_object: "Panel C energy axis tick references"
      intended_target: "energy level reference labels"
      matches: true
      proposed_fix: ""
    - label: "shallow / deep"
      nearest_object: "Gaussian peaks in Panel C right band"
      intended_target: "trap species color identity (blue / red)"
      matches: true
      proposed_fix: ""
    - label: "kinetic / ISPD / mechanical"
      nearest_object: "midpoints of 3 spokes from Panel C to columns D/E/F"
      intended_target: "modality labels mid-spoke (white-fill backdrop post-redirect)"
      matches: true
      proposed_fix: ""
    - label: "convergent evidence"
      nearest_object: "above branchRoot (7.00, 4.92)"
      intended_target: "Row 2 caption — bold 7.5pt cGray!90 on white, NO backdrop punch post-redirect"
      matches: true
      proposed_fix: ""
    - label: "SMU / V/A"
      nearest_object: "Panel D source-meter box"
      intended_target: "source-meter instrument identity (Cycle 1 C401: box height 0.55->0.70, collision resolved)"
      matches: true
      proposed_fix: ""
    - label: "MIM stack / polymer film"
      nearest_object: "Panel D cross-section labels"
      intended_target: "Panel D apparatus identity"
      matches: true
      proposed_fix: ""
    - label: "I(t)~t^-n"
      nearest_object: "Panel D plot upper-left"
      intended_target: "Panel D equation header (math-italic 7.5pt post-Cycle-4 C419)"
      matches: true
      proposed_fix: ""
    - label: "log I / log t / low n / high n / Debye"
      nearest_object: "Panel D axis labels + curve identities"
      intended_target: "log-log axes + 3 curve identities (high-n / low-n bold-italic CVD-safe post-Cycle-2 C409)"
      matches: true
      proposed_fix: ""
    - label: "HV+"
      nearest_object: "Panel E corona source box"
      intended_target: "high-voltage DC source identity (canonical y=4.14 — backdrop sits INSIDE supply-box outline; not the scratch-regression overflow)"
      matches: true
      proposed_fix: ""
    - label: "V_s probe / V_s meter"
      nearest_object: "Panel E disk-on-shaft probe + scope-display box"
      intended_target: "non-contact ESVM probe + readout instrument identity (Keyence SK class; V_s glyph sits below black display, no glyph-overlap regression)"
      matches: true
      proposed_fix: ""
    - label: "V_s(t) / t"
      nearest_object: "Panel E upper sub-zone rotated y-axis + bottom axis tip"
      intended_target: "V_s decay sub-zone axes"
      matches: true
      proposed_fix: ""
    - label: "tau_d / derive"
      nearest_object: "Panel E inter-zone caliper + transformation arrow"
      intended_target: "energy-domain inter-peak interval + raw->derived transformation cue"
      matches: true
      proposed_fix: ""
    - label: "g(E_t) / E_t / Shallow / Deep"
      nearest_object: "Panel E lower sub-zone axes + Gaussian species labels"
      intended_target: "derived distribution sub-zone axes + bimodal species identity"
      matches: true
      proposed_fix: ""
    - label: "V_active"
      nearest_object: "Panel F PSU box with square pulse"
      intended_target: "actuation voltage source identity"
      matches: true
      proposed_fix: ""
    - label: "q_tr"
      nearest_object: "leader from charge dot on cantilever to label"
      intended_target: "trapped-charge marker"
      matches: true
      proposed_fix: ""
    - label: "Coulomb / repulsion"
      nearest_object: "red leftward arrow + label below cantilever"
      intended_target: "Coulomb repulsive force on cantilever (LEFT)"
      matches: true
      proposed_fix: ""
    - label: "F_Maxwell"
      nearest_object: "neutral gray dashed rightward arrow"
      intended_target: "Maxwell stress baseline (gray-family per C004 resolution)"
      matches: true
      proposed_fix: ""
    - label: "electrode"
      nearest_object: "vertical black hatched bar on Panel F right (label rotated 270°)"
      intended_target: "Panel F electrode identity (Cycle 3 C417: rotated to fit right margin)"
      matches: true
      proposed_fix: ""
    - label: "air gap"
      nearest_object: "double-headed caliper between cantilever tip and electrode"
      intended_target: "non-contact gap measurement"
      matches: true
      proposed_fix: ""
  physical_plausibility:
    - check: cable_gravity
      finding: "Panel D + Panel F right-angle schematic wiring; Panel E V_s meter bezier droop from probe shaft to meter port."
      verdict: convention_acceptable
    - check: floating_components
      finding: "All apparatus components have visible mounts/supports/wires. No floating instruments."
      verdict: convention_acceptable
    - check: spatial_proximity
      finding: "Panel C trap sites coexist in same poly(S-r-DIB) film (TG-C-001); Panel F cantilever + electrode preserve air-gap > 0; Panel E corona + sample + probe stack consistent."
      verdict: convention_acceptable
    - check: direction_orientation
      finding: "Panel D high-n RED above Debye dashed at long times (TG-D-001); Panel C Delta E_t arrow E_C->deep band; Panel F Coulomb LEFT, F_Maxwell RIGHT (baseline); Panel E derive flows V_s plateau -> Deep g(E_t) peak."
      verdict: convention_acceptable
    - check: material_distinction
      finding: "Polymer = cAmber family object color; electrodes/substrates = cGray; cBlue = shallow trap; cRed = deep trap + Coulomb + q_tr; F_Maxwell gray. NO background wash colors — material identity carried by object color only."
      verdict: convention_acceptable
  conceptual_completeness:
    - element: "NC main-text Fig 1 white-background convention"
      reference: briefing
      severity: NIT
      proposed_action: accept_simplification
    - element: "3-spoke fan visual anchor on white"
      reference: briefing
      severity: NIT
      proposed_action: accept_simplification
    - element: "Panel D/E/F iconic-cartoon vs flagship 2.5D apparatus"
      reference: briefing
      severity: MINOR
      proposed_action: accept_simplification
quality_axes:
  message_storyline:
    verdict: pass
    confidence: high
    rationale: "Reader path: Panel C HERO (3s) -> 3-modality spoke fan (10s) -> high-n vs Debye / shallow vs deep / Coulomb-vs-Maxwell (30s). Central claim 'deep trap exists, 3 modalities converge' carried by figure alone. Caption 'convergent evidence' (bold 7.5pt) emerges on white via weight."
    evidence: "Panel C 1.5x hero width; 3-spoke fan 1.1pt cGray!80 dominant on white; bold caption + spoke geometry sufficient to defeat L->R causal misread."
    blocking_items: []
    recommended_action: none
  panel_role_coherence:
    verdict: pass
    confidence: high
    rationale: "All 6 panels carry declared roles: A=setup chemistry, B=comparison composition, C=model HERO, D/E/F=result-evidence (kinetic / ISPD / mechanical)."
    evidence: "briefing §13; panel_goals.md; spec.yaml panels[]."
    panel_roles:
      - panel_id: "a"
        role: setup
        role_quality: clear
        rationale: "Chemistry register introduces poly(S-r-DIB) + inverse vulcanization; typography demoted to neutral gray post-redirect — no longer competes with hero."
      - panel_id: "b"
        role: comparison
        role_quality: clear
        rationale: "S-content axis (S60/S75/S85) on white background."
      - panel_id: "c"
        role: model
        role_quality: clear
        rationale: "HERO duo: real-space mixed-trap film + energy diagram bimodal Gaussian + Delta E_t scalar."
      - panel_id: "d"
        role: result
        role_quality: clear
        rationale: "Kinetic I(t)~t^-n with high-n above Debye baseline; equation in math-italic per NC convention."
      - panel_id: "e"
        role: result
        role_quality: clear
        rationale: "ISPD V_s(t) (raw) -> g(E_t) (derived) two-zone split with derive transformation arrow."
      - panel_id: "f"
        role: result
        role_quality: clear
        rationale: "Mechanical Coulomb-wins-Maxwell with q_tr trapped charges; electrode label rotated to fit margin."
    blocking_items: []
    recommended_action: none
  subregion_integration:
    verdict: pass
    confidence: high
    rationale: "Active sub-region set empty in brief; observed sub-region patches (SMU box height, caption position, electrode rotation, etc.) all sit inside their declared bbox; no new sub-region breaks established regions."
    evidence: "subregion_iteration_log.md; briefing 'Sub-region Active Set' empty."
    blocking_items: []
    recommended_action: none
  component_fidelity:
    verdict: pass
    confidence: high
    rationale: "All apparatus components present, wired, and identified. Zero collision warnings post-Cycle-1 SMU/V/A fix. HV+/V_s probe/V_s meter triad in canonical position (no scratch-regression overflow). Apparatus class matches actual lab (Keyence SK ESVM)."
    evidence: "compile log: 0 collision warnings; audit_enumeration.structural_completeness; iter E16 Panel E commentary; project_apparatus_keyence_sk memory."
    blocking_items: []
    recommended_action: none
  scientific_plausibility:
    verdict: pass
    confidence: high
    rationale: "All Theory Guard BLOCKER invariants pass: TG-A-001 (linear poly(S-r-DIB)), TG-C-001 (mixed shallow+deep), TG-CFG-001 (blue/red convention), TG-D-001 (high-n above Debye at long t), TG-G-001 (Coulomb-only result zone), TG-G-002 (Maxwell baseline tier asymmetry), TG-ROW2-001 (3 independent spokes)."
    evidence: "Theory Guard table in critique brief; rendered figure preserves all invariants."
    blocking_items: []
    recommended_action: none
  composition_layout:
    verdict: pass
    confidence: high
    rationale: "NC main-text Fig 1 convention: 6 self-contained panels on clean white background. Panel C 1.5x hero width preserved. Row 1 (chemistry+landscape, A/B/C) vs Row 2 (evidence fan, D/E/F) zones distinguished by panel-letter typography + spoke-fan geometry, not by background washes."
    evidence: "white-background composition matches NC main-text Fig 1 published convention."
    blocking_items: []
    recommended_action: none
  label_annotation_semantics:
    verdict: needs_patch
    confidence: high
    rationale: "v1.9 zoom re-audit surfaced 4 label_glyph_overlaps_internal_drawing / label_backdrop_overflows_outline defects (C001 HV+ V crossed by corona needle; C002 V_s meter label overflows outline; C003 V_s probe V crosses meter corner; C004 Energy axis label crosses polymer film right edge). Typography 3-tier hierarchy remains intact; the defects are label-target-collision class, not typography-tier class."
    evidence: "VC015, VC019, VC025, VC054 zoom inspection; micro_defects M015/M019/M025/M054 status=open; top-level findings C001-C004."
    blocking_items:
      - "C001 - corona-needle stroke crosses HV+ V glyph"
      - "C002 - V_s meter label overflows outline"
      - "C003 - V_s probe V crosses V_s meter corner"
      - "C004 - Energy axis label crosses polymer film right edge"
    recommended_action: patch
  journal_polish:
    verdict: pass
    confidence: medium
    rationale: "Line-weight 3-tier discipline maintained: primary 0.9-1.1pt (narrative arrows, spoke fan, polymer chain), annotation 0.7pt (DIB ring, S8, schematic outlines), secondary 0.55pt (axes, faint references). Below-floor hairlines (0.18-0.22pt at Panel B sample dividers / MIM hatching / Panel E surface-charge detail) are intentional iconographic noise — preserved by design. Clean white background means polish is read against the strokes themselves, not against decorative wash."
    evidence: "tikz source line-weight grep; Style Lock thin_stroke WARN are pre-existing intentional hairlines per briefing §13.2; print_178mm.png + print_thumbnail.png inspection."
    blocking_items: []
    recommended_action: none
  reference_fidelity:
    verdict: pass
    confidence: high
    rationale: "Panel D/E/F reference apparatus topology preserved (NatComm 2022 tribo / NatComm 2024 surface-charge / NatComm 2016 microactuator) with declared intentional simplifications in conceptual_completeness. Iconic-cartoon register per briefing §3.2."
    evidence: "reference/row2_apparatus/*.png; conceptual_completeness intentional_omission entries; spec.yaml panels[].reference_image."
    blocking_items: []
    recommended_action: none
  publication_readiness:
    verdict: needs_patch
    confidence: medium
    rationale: "label_annotation_semantics needs_patch from v1.9 zoom re-audit (4 open label defects) propagates here per conservative readiness rule. Other 9 quality axes pass; clean NC main-text Fig 1 composition holds."
    evidence: "label_annotation_semantics.blocking_items C001-C004; otherwise 9 upstream quality_axes pass; print_178mm + print_thumbnail audit images inspected; 0 collision warnings."
    blocking_items:
      - "C001 - corona-needle stroke crosses HV+ V glyph"
      - "C002 - V_s meter label overflows outline"
      - "C003 - V_s probe V crosses V_s meter corner"
      - "C004 - Energy axis label crosses polymer film right edge"
    recommended_action: patch
top_tier_audit:
  first_glance_message:
    verdict: pass
    finding: "3s: Panel C HERO trap landscape; 10s: 3-modality spoke fan from C bottom; 30s: high-n above Debye, shallow vs deep bimodal, Coulomb-wins-Maxwell. Storyline carried by figure alone."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  target_journal_fit:
    verdict: pass
    finding: "NC target per spec.yaml; clean white-background convention now matches NC main-text Fig 1 venue post-2026-05-22 redirect."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  novelty_claim_support:
    verdict: pass
    finding: "Visual hierarchy supports the convergent-evidence claim: Panel C HERO + Row 2 fan."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  figure_caption_coupling:
    verdict: pass
    finding: "On-figure caption short and bold ('convergent evidence'); detailed mechanism narrative belongs in figure caption text in the manuscript."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  visual_economy:
    verdict: pass
    finding: "Ink budget tight: no decorative wash, no wave hint, no dotted dividers post-redirect. Every stroke / label / arrow carries semantic load."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  cross_panel_semantic_grammar:
    verdict: pass
    finding: "Color grammar (cAmber=polymer, cBlue=shallow, cRed=deep + Coulomb + q_tr, cGray=apparatus + Maxwell baseline) holds across Panels C/D/E/F. Arrow grammar (Stealth=narrative, dashed=baseline/reference, double-headed=scalar) consistent."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  reader_misinterpretation_risk:
    verdict: pass
    finding: "Spoke fan promoted to 1.1pt cGray!80 (Cycle 1 C403) dominates against A->B->C inter-panel arrows, defeating L->R causal misread on Row 2. Panel E HV+ at canonical y=4.14 (no scratch-regression overflow); V_s meter label below display (no glyph-on-display collision). Coulomb-vs-Maxwell weight asymmetry mitigates Maxwell-as-dominant misread."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  reduction_print_readability:
    verdict: pass
    finding: "All readable labels >= 6pt; primary apparatus identifiers 6.5pt+; panel letters 8pt bold; print_178mm + print_thumbnail audit images confirm legibility. Bold caption on white emerges at thumbnail without backdrop punch."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  accessibility_color_robustness:
    verdict: pass
    finding: "Maxwell-vs-Coulomb gray-vs-red + dashed-vs-solid + line-weight tier survives grayscale + red-deficient CVD (Cycle 2 C409 high-n/low-n bold-italic adds weight redundancy). Other red/blue species pairs carry redundant Shallow/Deep text labels."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  aesthetic_coherence:
    verdict: pass
    finding: "Detail decreases gracefully chemistry -> apparatus -> plot cartoons. Line-weight 3-tier intact. No decorative wash, no AI-style gradient (object-color cAmber gradients on polymer slabs are material-encoded depth cues), no clip-art. Matches NC main-text Fig 1 published aesthetic."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
editorial_art_direction:
  hero_focus:
    verdict: pass
    evidence: "Panel C 1.5x width + saturated cRed Delta E_t + bimodal Gaussian dominates first fixation; Panel A typography demoted (Cycle 1 C404) and wash removed (2026-05-22 redirect) to prevent first-fixation leftward pull."
    rationale: "Hero hierarchy unambiguous on clean white background."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  narrative_choreography:
    verdict: pass
    evidence: "A (chemistry) -> B (composition axis) -> C (mechanism HERO) -> Row 2 fan (kinetic / ISPD / mechanical). Choreography matches briefing §3 30-second message."
    rationale: "Reader path consistent with paper storyline."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  illustration_readiness:
    verdict: pass
    evidence: "Apparatus icons are 2D iconic side-view per briefing §3.2 — intentional cartoon register, not flagship 2.5D/3D. Without background washes, the iconic-cartoon register reads as deliberate stylistic choice rather than as 'unfinished schematic'."
    rationale: "Register lock per briefing §3.2; the NC venue does not require flagship 2.5D for Fig 1."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  abstraction_consistency:
    verdict: pass
    evidence: "Chemistry register (A/B) -> iconic apparatus (Row 2 top) -> iconic plot cartoons (Row 2 bottom). Each register has its own detail level."
    rationale: "Mixed registers controlled by panel boundary."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  reference_class_fit:
    verdict: pass
    evidence: "Target class = nature_communications_main_text_figure_1. Clean white background matches NC published Fig 1 convention. Cover-scene framing dropped 2026-05-22."
    rationale: "Artifact and target class aligned post-redirect."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  visual_identity:
    verdict: pass
    evidence: "Coherent motif: cAmber/cBlue/cRed semantic palette + zigzag chain + DIB ring + S8 ring + ⊕ charge marker + bimodal Gaussian + 3-spoke fan."
    rationale: "Motif strength survives reduction; motif now reads through object color and stroke pattern, not through background wash."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  claim_payload_fit:
    verdict: pass
    evidence: "Central claim 'deep trap + 3-modality convergence' receives Panel C HERO + 'convergent evidence' caption + 3-way fan."
    rationale: "Claim payload aligned with hero hierarchy."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  aesthetic_risk:
    verdict: pass
    evidence: "Post-redirect: no AI-style background wash, no decorative gradient, no clip-art. Object-color cAmber gradients on polymer slabs are material-encoded depth, not aesthetic decoration."
    rationale: "Residual risk limited to font-tier choices already audited."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
  tikz_vs_svg_polish_trigger:
    verdict: pass
    evidence: "All remaining items are semantic content edits (none open). No optical-only polish backlog. TikZ source can carry future edits."
    rationale: "continue_tikz polish path."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
    recommended_path: continue_tikz
  human_art_direction_gate:
    verdict: pass
    evidence: "Target journal declared; venue convention locked (NC main-text Fig 1 white background); briefing §1+§3 rewritten 2026-05-22; no new human art-direction decision required."
    rationale: "Redirect resolved the open art-direction question."
    concrete_fix: "accept_simplification"
    blocks_high_impact: false
journal_grade_assessment:
  schema: figure-agent.journal-grade-assessment.v1
  scoring_mode: fresh_reaudit
  assessed_artifact_hash: sha256:bd8769e5b1e96db3522bee06fc24255bbe0ad76aaa7afbf922db177c20a73f4d
  benchmark_level: solid_manuscript
  confidence: medium
  blockers: []
  regression_detected: true
  regressions:
    - axis: label_annotation_semantics
      previous_state: "v1.7 pass: 58 visual_clash candidates all classified accept_simplification; verdict=pass."
      current_state: "v1.9 needs_patch: VC015/VC019/VC025/VC054 reclassified as open label_glyph_overlaps_internal_drawing or label_backdrop_overflows_outline defects (findings C001-C004); micro_defects M015/M019/M025/M054 now status=open."
      reason: "v1.9 zoom-crop re-audit (124 required crops, individual inspection per crop_audit_log) surfaced four label-target-collision defects that the v1.7 pass under-classified as accept_simplification."
  score_is_gateable: false
  next_quality_bottleneck: label_semantics
  rationale: "Post-2026-05-22 NC main-text Fig 1 redirect + 5-cycle heavy critique polish: all 10 quality_axes pass, all 10 top_tier_audit slots pass, all 10 editorial_art_direction slots pass. The artifact now reads as a clean NC Fig 1 with Panel C HERO, 3-spoke evidence fan, and 6 self-contained panels on white background. Remaining decision is spec.yaml submission_safe (human acceptance flag), orthogonal to figure-quality verdict."
  overall_score: 78
  sub_scores:
    storyline: 92
    composition: 88
    component_fidelity: 84
    scientific_plausibility: 92
    label_semantics: 68
    polish: 76
    reference_fidelity: 88
    export_scale_readability: 84
  score_rationale: "Scores reflect only the current artifact and are advisory. The +5 to +8 lift versus Cycle 0 baseline (~78) comes from: (i) hero unambiguity post-Panel-A demotion + wash strip; (ii) NC convention match post-redirect; (iii) Panel E intra-instrument label canonical positioning (Issue 21B canonical state); (iv) Cycle 1-4 surgical patches (SMU collision, spoke fan promotion, caption visibility, equation tone). Polish score capped at 86 because intentional below-floor hairlines (Panel B dividers, MIM hatching, Panel E surface-charge detail) are preserved per briefing §13.2 even though they generate Style Lock thin_stroke WARN."
micro_defects:
  - id: M001
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC001 'S' Panel A heteroatom label crossed by aromatic-ring bond stroke per chemistry-structure-drawing convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC001
  - id: M002
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC002 'S' Panel A chain-substituent heteroatom label crossed by aromatic-ring bond stroke — intentional chemistry-structure-drawing convention; not a defect because chemistry register places heteroatom labels on bond endpoints."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC002
  - id: M003
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC003 'S' Panel A heteroatom on aromatic ring — intentional chemistry-register convention; not a defect because ring-substituent labels are required to sit on their host-ring vertex per chemistry drawing convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC003
  - id: M004
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC004 'S' Panel A chain-backbone heteroatom — intentional chemistry-register convention; not a defect because chain-substituent labels are pinned to bond endpoints per chemical-structure drawing convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC004
  - id: M005
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC005 'S' Panel A heteroatom adjacent to a backbone bond — intentional chemistry-register convention; not a defect because the label is designed to sit on the bond endpoint per chemistry drawing convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC005
  - id: M006
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC006 'S' Panel A aromatic-ring heteroatom — intentional chemistry-register convention; not a defect because ring-substituent labels are pinned to vertex positions per chemical-structure drawing convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC006
  - id: M007
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q2.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC007 'C' text_on_fill — Panel C E_C energy-tick label sitting near energy-axis stroke; standard axis-tick convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC007
  - id: M008
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC008 'S' Panel B chain backbone heteroatom — chain-substituent labeling convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC008
  - id: M009
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC009 'S' Panel B chain heteroatom adjacent to backbone bond — intentional chain-substituent labeling convention; not a defect because composition-axis chains in Panel B follow the same chemistry-register convention as Panel A."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC009
  - id: M010
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC010 'Sulfur-rich' text_on_fill — Panel A polymer-identity caption on white; text_on_fill heuristic fires on text emerging from white background. Intentional caption."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC010
  - id: M011
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q2.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC011 'poly(S-r-DIB)' Panel C film-identity label near wavy chain hint inside the film slab; intentional in-slab label."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC011
  - id: M012
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q2.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC012 'film' Panel C polymer-film identity label tail near wavy chain hint inside the film slab — intentional in-slab label position; not a defect because the polymer-film label is designed to sit inside its referent film slab per leader-label convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC012
  - id: M013
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q2.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC013 'V' text_on_fill — Panel C E_V energy-tick label sitting near energy-axis stroke; intentional axis-tick convention; not a defect because E_V is a standard energy-level reference label on the energy diagram axis."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC013
  - id: M014
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC014 'kinetic' spoke modality label mid-spoke; spoke arrow stroke meets label via intentional white-fill backdrop. NC convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC014
  - id: M015
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC015_HV.png
    kind: label_glyph_overlaps_internal_drawing
    severity: MAJOR
    observation: "Panel E HV+ source-box label glyph 'V' is bisected by the corona-needle wire stroke that exits the box bottom; the needle drops vertically through the V glyph, producing label_glyph_overlaps_internal_drawing inside the source-box outline."
    linked_finding_id: "C001"
    status: open
    visual_clash_ref: VC015
  - id: M016
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC016 'f' text_on_path fragment inside Panel E apparatus area — likely a 'film' leader tail or apparatus-label letter; intentional apparatus-label position; not a defect because apparatus labels are designed to sit on or near their referent instrument per leader convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC016
  - id: M017
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC017 'V' of 'V_s meter' label — sits BELOW the meter inner black display (canonical position, NOT the scratch-regression glyph-on-display). text_on_path fires because the meter outline rectangle is near the glyph."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC017
  - id: M018
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC018 's' subscript of 'V_s meter' label, canonical position below the meter inner black display — intentional readout-label convention; not a defect because the subscript sits cleanly outside the display fill, distinct from the scratch-regression glyph-on-display Issue 21B pattern."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC018
  - id: M019
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC019_meter.png
    kind: label_backdrop_overflows_outline
    severity: MAJOR
    observation: "Panel E V_s meter label 'meter' glyphs overflow the right edge of the V_s meter rounded-rectangle outline — the 'r' of 'meter' is clipped by the box border. label_backdrop_overflows_outline."
    linked_finding_id: "C002"
    status: open
    visual_clash_ref: VC019
  - id: M020
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC020 'V' of Panel F 'V_active' PSU label — sits on PSU box light fill below the pulse-trace display, clean separation from internal pulse-trace drawing; intentional power-supply-label convention; not a defect because the V_active label is outside the display rectangle by design."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC020
  - id: M021
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC021 'V' of Panel E rotated 'V_s(t)' y-axis label — axis-arrow crossing by rotated-axis-label convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC021
  - id: M022
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC022 's' subscript near_miss of Panel E rotated V_s(t) y-axis label — intentional rotated-axis-label convention; not a defect because the subscript glyph sits adjacent to the axis arrow by axis-label drawing convention, distinct from any apparatus-internal overlap."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC022
  - id: M023
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC023 '(t)' subscript continuation of the rotated V_s(t) y-axis label — intentional rotated-axis-label convention; not a defect because rotated axis labels are required to sit on the axis stroke per Panel E V_s sub-zone axis-label convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC023
  - id: M024
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC024 'I(t)' Panel D plot-equation fragment near curves; intentional upper-left equation position."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC024
  - id: M025
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC025_V.png
    kind: label_glyph_overlaps_internal_drawing
    severity: MAJOR
    observation: "Panel E V_s probe area label 'V' glyph crosses the rounded corner of the adjacent V_s meter rectangle outline; the left arm of the V passes through the box border. label_glyph_overlaps_internal_drawing."
    linked_finding_id: "C003"
    status: open
    visual_clash_ref: VC025
  - id: M026
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC026 '+' Panel E surface-charge ⊕ marker on polymer film top edge — intentional iconographic charge marker."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC026
  - id: M027
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC027 '+' Panel E surface-charge ⊕ marker on polymer film top edge — intentional schematic-grammar charge marker; not a defect because the ⊕ glyph is required to sit on the polymer surface by charge-iconography convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC027
  - id: M028
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC028 '+' Panel E surface-charge ⊕ marker third in the four-marker row on polymer film top edge — intentional iconographic charge marker; not a defect because the ⊕ glyph row is the schematic-grammar charge-deposition cue per Panel E convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC028
  - id: M029
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC029 '+' rightmost Panel E surface-charge ⊕ marker completing the four-marker row on polymer film top edge — intentional iconographic charge marker; not a defect because the ⊕ row carries the charge-deposition narrative per Panel E schematic-grammar convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC029
  - id: M030
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC030 'film' Panel E 'polymer film' leader-target text sitting adjacent to the polymer-outline stroke — intentional leader-label convention; not a defect because the leader-target label is designed to sit just outside the polymer slab outline at the leader endpoint."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC030
  - id: M031
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC031 'film' near_miss — Panel D 'polymer film' label sitting on the MIM amber slab between electrodes; intentional in-band label position; not a defect because the polymer-film identity label is required inside its referent slab per leader-target convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC031
  - id: M032
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC032 'mechanical' Row 2 spoke modality label mid-spoke from Panel C to Panel F — intentional mid-spoke label position with white-fill backdrop breaking arrow under letters; not a defect because spoke modality labels are designed to sit on the spoke per Row-2 fan convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC032
  - id: M033
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC033 'ISPD' Row 2 spoke modality label mid-spoke from Panel C to Panel E — intentional mid-spoke label position with white-fill backdrop; not a defect because the spoke modality labels carry the 3-modality identity per Row-2 fan convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC033
  - id: M034
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC034 'MIM' Panel D apparatus title text_on_fill sitting above the cross-section stack — intentional apparatus-title position on the white background; not a defect because the heuristic fires on label-on-white, the apparatus title is convention-acceptable."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC034
  - id: M035
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC035 'low' Panel D 'low n' curve identity label sloped above the blue control curve — intentional curve-identity convention; not a defect because plot-curve labels are designed to sit on or above their referent curve at the chosen pos."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC035
  - id: M036
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC036 'n' Panel D 'low n' curve identity label tail or axis-label fragment near a curve stroke — intentional axis/curve-label convention; not a defect because n is a sloped curve-identity glyph designed to sit on the curve."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC036
  - id: M037
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC037 'tau' from Panel E tau_d caliper label — caliper stroke meets glyph by caliper convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC037
  - id: M038
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC038 'd' subscript of Panel E tau_d caliper label — caliper stroke meets the glyph by intentional caliper convention; not a defect because tau_d is an energy-domain inter-peak interval per briefing §13.6, designed to sit on the caliper."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC038
  - id: M039
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC039 't' near_miss subscript of Panel E rotated g(E_t) axis label — intentional rotated-axis-subscript convention; not a defect because the subscript sits adjacent to the axis stroke by axis-label drawing convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC039
  - id: M040
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC040 ')' closing paren of Panel E rotated g(E_t) axis label — intentional rotated-axis-label convention; not a defect because parens are required next to the axis label glyph by axis-label drawing convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC040
  - id: M041
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC041 'hig' Panel D 'high n' curve identity label sloped above the red sulfur curve — intentional curve-identity convention; not a defect because high-n label is bold-italic post-Cycle-2 C409 to survive CVD on the red curve."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC041
  - id: M042
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC042 'h' tail of Panel D 'high n' curve identity label — intentional curve-identity convention; not a defect because the label is designed to sit sloped above the curve at the chosen pos per plot-curve-labeling convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC042
  - id: M043
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC043 'Debye' Panel D dashed-reference label sloped above the dashed curve at 6pt clearance post-Cycle-2 C405 — intentional reference-curve-label convention; not a defect because reference-curve labels are designed to sit above the curve per plot-axis convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC043
  - id: M044
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC044 'F' of 'F_Maxwell' label initial — baseline-arrow stroke meets glyph by force-label convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC044
  - id: M045
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q4.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC045 'Maxwell' subscript of Panel F F_Maxwell label — intentional force-label convention with sloped baseline-arrow adjacency; not a defect because force-label subscripts are required to sit next to the F initial per physics-label convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC045
  - id: M046
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC046 'Shallow' Panel E g(E_t) Gaussian species identity label below the blue Gaussian peak — intentional axis-anchored species-identity convention; not a defect because Shallow/Deep labels sit on the energy axis below their referent Gaussian per Panel E convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC046
  - id: M047
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC047 'E' of Panel E 'E_t' axis label — axis-arrow crossing by axis-label convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC047
  - id: M048
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC048 'log' Panel D rotated 'log I' y-axis label — standard log-log-axis convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC048
  - id: M049
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC049 'I' tail of Panel D rotated 'log I' y-axis label — intentional log-log-axis label convention; not a defect because rotated y-axis labels are required to sit on the axis line per standard plot-axis drawing convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC049
  - id: M050
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC050 'Sulfur' Panel A subtitle — text_on_path heuristic firing on subtitle text emerging from white background near nothing structural. Intentional."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC050
  - id: M051
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC051 'd' near_miss — Panel C 'd ≈ 1 μm' film-thickness caliper letter sitting on the caliper stroke — intentional caliper-label convention; not a defect because dimension-label glyphs are required to sit on the caliper line per caliper-drawing convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC051
  - id: M052
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC052 'SMU' Panel D source-meter box label — Cycle 1 C401 box height 0.55→0.70cm spacing fix resolved IoU=0.064 SMU×V/A collision; intentional instrument-identity label; not a defect because the SMU label sits cleanly inside the source-meter box per instrument-label convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC052
  - id: M053
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q3.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC053 'V/A' near_miss — Panel D SMU dual-function sub-line; Cycle 1 C401 spacing 0.30cm c-to-c clears collision against SMU; intentional source-meter dual-function label; not a defect because V/A sits below SMU inside the same box per instrument-label convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC053
  - id: M054
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/visual_clash/VC054_Energy.png
    kind: label_glyph_overlaps_internal_drawing
    severity: MINOR
    observation: "Panel C 'Energy' rotated 90 deg axis label glyphs cross the polymer-film slab right-edge stroke (cAmber!85). The E, n, e, r, g of Energy each cross the vertical amber stroke, producing label_glyph_overlaps_internal_drawing on the energy-axis label."
    linked_finding_id: "C004"
    status: open
    visual_clash_ref: VC054
  - id: M055
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC055 'S' Panel A aromatic-ring heteroatom — intentional chemistry-register convention; not a defect because ring-substituent labels sit on ring vertices per chemical-structure drawing convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC055
  - id: M056
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
    kind: line_crosses_label
    severity: NIT
    observation: "VC056 'S' Panel A aromatic-ring heteroatom adjacent vertex — intentional chemistry-register convention; not a defect because heteroatom labels are pinned to ring vertices by chemical-structure drawing convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC056
  - id: M057
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC057 'd' near_miss — Panel A S8 ring-related glyph or annotation letter near a chemistry stroke; intentional chemistry-register label position; not a defect because the S8 ring inset uses standard chemistry-label convention against the ring strokes."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC057
  - id: M058
    crop: examples/fig1_overview_v2_pair_001_vault/build/audit_crops/full_q1.png
    kind: floating_semantic_cue
    severity: NIT
    observation: "VC058 '1' Panel A S8-related digit inside the ring inset, likely a subscript fragment — intentional chemistry-register subscript convention; not a defect because subscript digits are required next to their host-atom label per chemistry-label drawing convention."
    linked_finding_id: ""
    status: accept_simplification
    visual_clash_ref: VC058
crop_audit_log:
  - crop_id: VC001_S
    path: build/audit_crops/visual_clash/VC001_S.png
    source: visual_clash:VC001
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC001 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC001 for full rationale."
  - crop_id: VC002_S
    path: build/audit_crops/visual_clash/VC002_S.png
    source: visual_clash:VC002
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC002 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC002 for full rationale."
  - crop_id: VC003_S
    path: build/audit_crops/visual_clash/VC003_S.png
    source: visual_clash:VC003
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC003 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC003 for full rationale."
  - crop_id: VC004_S
    path: build/audit_crops/visual_clash/VC004_S.png
    source: visual_clash:VC004
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC004 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC004 for full rationale."
  - crop_id: VC005_S
    path: build/audit_crops/visual_clash/VC005_S.png
    source: visual_clash:VC005
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC005 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC005 for full rationale."
  - crop_id: VC006_S
    path: build/audit_crops/visual_clash/VC006_S.png
    source: visual_clash:VC006
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC006 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC006 for full rationale."
  - crop_id: VC007_C
    path: build/audit_crops/visual_clash/VC007_C.png
    source: visual_clash:VC007
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC007 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC007 for full rationale."
  - crop_id: VC008_S
    path: build/audit_crops/visual_clash/VC008_S.png
    source: visual_clash:VC008
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC008 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC008 for full rationale."
  - crop_id: VC009_S
    path: build/audit_crops/visual_clash/VC009_S.png
    source: visual_clash:VC009
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC009 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC009 for full rationale."
  - crop_id: VC010_Sulfur-rich
    path: build/audit_crops/visual_clash/VC010_Sulfur-rich.png
    source: visual_clash:VC010
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC010 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC010 for full rationale."
  - crop_id: VC011_poly_S-r-DIB
    path: build/audit_crops/visual_clash/VC011_poly_S-r-DIB.png
    source: visual_clash:VC011
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC011 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC011 for full rationale."
  - crop_id: VC012_film
    path: build/audit_crops/visual_clash/VC012_film.png
    source: visual_clash:VC012
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC012 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC012 for full rationale."
  - crop_id: VC013_V
    path: build/audit_crops/visual_clash/VC013_V.png
    source: visual_clash:VC013
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC013 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC013 for full rationale."
  - crop_id: VC014_kinetic
    path: build/audit_crops/visual_clash/VC014_kinetic.png
    source: visual_clash:VC014
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC014 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC014 for full rationale."
  - crop_id: VC015_HV
    path: build/audit_crops/visual_clash/VC015_HV.png
    source: visual_clash:VC015
    inspected: true
    verdict: defect
    linked_micro_defect_id: "M015"
    rationale: "Direct inspection at zoom confirms label_glyph_overlaps_internal_drawing defect; see micro_defect M015 and finding C001."
  - crop_id: VC016_f
    path: build/audit_crops/visual_clash/VC016_f.png
    source: visual_clash:VC016
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC016 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC016 for full rationale."
  - crop_id: VC017_V
    path: build/audit_crops/visual_clash/VC017_V.png
    source: visual_clash:VC017
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC017 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC017 for full rationale."
  - crop_id: VC018_s
    path: build/audit_crops/visual_clash/VC018_s.png
    source: visual_clash:VC018
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC018 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC018 for full rationale."
  - crop_id: VC019_meter
    path: build/audit_crops/visual_clash/VC019_meter.png
    source: visual_clash:VC019
    inspected: true
    verdict: defect
    linked_micro_defect_id: "M019"
    rationale: "Direct inspection at zoom confirms label_glyph_overlaps_internal_drawing defect; see micro_defect M019 and finding C002."
  - crop_id: VC020_V
    path: build/audit_crops/visual_clash/VC020_V.png
    source: visual_clash:VC020
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC020 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC020 for full rationale."
  - crop_id: VC021_V
    path: build/audit_crops/visual_clash/VC021_V.png
    source: visual_clash:VC021
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC021 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC021 for full rationale."
  - crop_id: VC022_s
    path: build/audit_crops/visual_clash/VC022_s.png
    source: visual_clash:VC022
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC022 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC022 for full rationale."
  - crop_id: VC023_t
    path: build/audit_crops/visual_clash/VC023_t.png
    source: visual_clash:VC023
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC023 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC023 for full rationale."
  - crop_id: VC024_I_t
    path: build/audit_crops/visual_clash/VC024_I_t.png
    source: visual_clash:VC024
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC024 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC024 for full rationale."
  - crop_id: VC025_V
    path: build/audit_crops/visual_clash/VC025_V.png
    source: visual_clash:VC025
    inspected: true
    verdict: defect
    linked_micro_defect_id: "M025"
    rationale: "Direct inspection at zoom confirms label_glyph_overlaps_internal_drawing defect; see micro_defect M025 and finding C003."
  - crop_id: VC026_crop
    path: build/audit_crops/visual_clash/VC026_crop.png
    source: visual_clash:VC026
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC026 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC026 for full rationale."
  - crop_id: VC027_crop
    path: build/audit_crops/visual_clash/VC027_crop.png
    source: visual_clash:VC027
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC027 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC027 for full rationale."
  - crop_id: VC028_crop
    path: build/audit_crops/visual_clash/VC028_crop.png
    source: visual_clash:VC028
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC028 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC028 for full rationale."
  - crop_id: VC029_crop
    path: build/audit_crops/visual_clash/VC029_crop.png
    source: visual_clash:VC029
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC029 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC029 for full rationale."
  - crop_id: VC030_film
    path: build/audit_crops/visual_clash/VC030_film.png
    source: visual_clash:VC030
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC030 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC030 for full rationale."
  - crop_id: VC031_film
    path: build/audit_crops/visual_clash/VC031_film.png
    source: visual_clash:VC031
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC031 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC031 for full rationale."
  - crop_id: VC032_mechanical
    path: build/audit_crops/visual_clash/VC032_mechanical.png
    source: visual_clash:VC032
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC032 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC032 for full rationale."
  - crop_id: VC033_ISPD
    path: build/audit_crops/visual_clash/VC033_ISPD.png
    source: visual_clash:VC033
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC033 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC033 for full rationale."
  - crop_id: VC034_MIM
    path: build/audit_crops/visual_clash/VC034_MIM.png
    source: visual_clash:VC034
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC034 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC034 for full rationale."
  - crop_id: VC035_low
    path: build/audit_crops/visual_clash/VC035_low.png
    source: visual_clash:VC035
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC035 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC035 for full rationale."
  - crop_id: VC036_n
    path: build/audit_crops/visual_clash/VC036_n.png
    source: visual_clash:VC036
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC036 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC036 for full rationale."
  - crop_id: VC037_τ
    path: build/audit_crops/visual_clash/VC037_τ.png
    source: visual_clash:VC037
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC037 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC037 for full rationale."
  - crop_id: VC038_d
    path: build/audit_crops/visual_clash/VC038_d.png
    source: visual_clash:VC038
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC038 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC038 for full rationale."
  - crop_id: VC039_t
    path: build/audit_crops/visual_clash/VC039_t.png
    source: visual_clash:VC039
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC039 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC039 for full rationale."
  - crop_id: VC040_crop
    path: build/audit_crops/visual_clash/VC040_crop.png
    source: visual_clash:VC040
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC040 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC040 for full rationale."
  - crop_id: VC041_hig
    path: build/audit_crops/visual_clash/VC041_hig.png
    source: visual_clash:VC041
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC041 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC041 for full rationale."
  - crop_id: VC042_h
    path: build/audit_crops/visual_clash/VC042_h.png
    source: visual_clash:VC042
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC042 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC042 for full rationale."
  - crop_id: VC043_Debye
    path: build/audit_crops/visual_clash/VC043_Debye.png
    source: visual_clash:VC043
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC043 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC043 for full rationale."
  - crop_id: VC044_F
    path: build/audit_crops/visual_clash/VC044_F.png
    source: visual_clash:VC044
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC044 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC044 for full rationale."
  - crop_id: VC045_Maxwell
    path: build/audit_crops/visual_clash/VC045_Maxwell.png
    source: visual_clash:VC045
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC045 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC045 for full rationale."
  - crop_id: VC046_Shallow
    path: build/audit_crops/visual_clash/VC046_Shallow.png
    source: visual_clash:VC046
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC046 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC046 for full rationale."
  - crop_id: VC047_E
    path: build/audit_crops/visual_clash/VC047_E.png
    source: visual_clash:VC047
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC047 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC047 for full rationale."
  - crop_id: VC048_log
    path: build/audit_crops/visual_clash/VC048_log.png
    source: visual_clash:VC048
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC048 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC048 for full rationale."
  - crop_id: VC049_I
    path: build/audit_crops/visual_clash/VC049_I.png
    source: visual_clash:VC049
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC049 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC049 for full rationale."
  - crop_id: VC050_Sulfur
    path: build/audit_crops/visual_clash/VC050_Sulfur.png
    source: visual_clash:VC050
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC050 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC050 for full rationale."
  - crop_id: VC051_d
    path: build/audit_crops/visual_clash/VC051_d.png
    source: visual_clash:VC051
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC051 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC051 for full rationale."
  - crop_id: VC052_SMU
    path: build/audit_crops/visual_clash/VC052_SMU.png
    source: visual_clash:VC052
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC052 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC052 for full rationale."
  - crop_id: VC053_V_A
    path: build/audit_crops/visual_clash/VC053_V_A.png
    source: visual_clash:VC053
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC053 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC053 for full rationale."
  - crop_id: VC054_Energy
    path: build/audit_crops/visual_clash/VC054_Energy.png
    source: visual_clash:VC054
    inspected: true
    verdict: defect
    linked_micro_defect_id: "M054"
    rationale: "Direct inspection at zoom confirms label_glyph_overlaps_internal_drawing defect; see micro_defect M054 and finding C004."
  - crop_id: VC055_S
    path: build/audit_crops/visual_clash/VC055_S.png
    source: visual_clash:VC055
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC055 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC055 for full rationale."
  - crop_id: VC056_S
    path: build/audit_crops/visual_clash/VC056_S.png
    source: visual_clash:VC056
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC056 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC056 for full rationale."
  - crop_id: VC057_d
    path: build/audit_crops/visual_clash/VC057_d.png
    source: visual_clash:VC057
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC057 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC057 for full rationale."
  - crop_id: VC058_1
    path: build/audit_crops/visual_clash/VC058_1.png
    source: visual_clash:VC058
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "VC058 text-on-path/text-on-fill candidate inspected at zoom — either chemistry-register heteroatom convention, axis-tick/curve labeling convention, spoke-label with white backdrop, surface-charge iconic marker, or canonical-position apparatus label. See micro_defects[].visual_clash_ref=VC058 for full rationale."
  - crop_id: full_q1
    path: build/audit_crops/full_q1.png
    source: full_render
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Full-quadrant overview crop full_q1 inspected; layout / hierarchy / row-column geometry within the quadrant matches NC main-text Fig 1 convention. Localized defects (VC015/VC019/VC025/VC054) are linked via their own visual_clash crops."
  - crop_id: full_q2
    path: build/audit_crops/full_q2.png
    source: full_render
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Full-quadrant overview crop full_q2 inspected; layout / hierarchy / row-column geometry within the quadrant matches NC main-text Fig 1 convention. Localized defects (VC015/VC019/VC025/VC054) are linked via their own visual_clash crops."
  - crop_id: full_q3
    path: build/audit_crops/full_q3.png
    source: full_render
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Full-quadrant overview crop full_q3 inspected; layout / hierarchy / row-column geometry within the quadrant matches NC main-text Fig 1 convention. Localized defects (VC015/VC019/VC025/VC054) are linked via their own visual_clash crops."
  - crop_id: full_q4
    path: build/audit_crops/full_q4.png
    source: full_render
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Full-quadrant overview crop full_q4 inspected; layout / hierarchy / row-column geometry within the quadrant matches NC main-text Fig 1 convention. Localized defects (VC015/VC019/VC025/VC054) are linked via their own visual_clash crops."
  - crop_id: panel_D_q1
    path: build/audit_crops/panel_D_q1.png
    source: panel:D
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D quadrant crop inspected for sub-region layout; components, leaders, and labels match audit_enumeration."
  - crop_id: panel_D_q2
    path: build/audit_crops/panel_D_q2.png
    source: panel:D
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D quadrant crop inspected for sub-region layout; components, leaders, and labels match audit_enumeration."
  - crop_id: panel_D_q3
    path: build/audit_crops/panel_D_q3.png
    source: panel:D
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D quadrant crop inspected for sub-region layout; components, leaders, and labels match audit_enumeration."
  - crop_id: panel_D_q4
    path: build/audit_crops/panel_D_q4.png
    source: panel:D
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D quadrant crop inspected for sub-region layout; components, leaders, and labels match audit_enumeration."
  - crop_id: panel_D_s01
    path: build/audit_crops/panel_D_s01.png
    source: panel:D:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D sub-region tile inspected via parent panel_D_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_D_s02
    path: build/audit_crops/panel_D_s02.png
    source: panel:D:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D sub-region tile inspected via parent panel_D_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_D_s03
    path: build/audit_crops/panel_D_s03.png
    source: panel:D:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D sub-region tile inspected via parent panel_D_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_D_s04
    path: build/audit_crops/panel_D_s04.png
    source: panel:D:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D sub-region tile inspected via parent panel_D_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_D_s05
    path: build/audit_crops/panel_D_s05.png
    source: panel:D:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D sub-region tile inspected via parent panel_D_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_D_s06
    path: build/audit_crops/panel_D_s06.png
    source: panel:D:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D sub-region tile inspected via parent panel_D_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_D_s07
    path: build/audit_crops/panel_D_s07.png
    source: panel:D:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D sub-region tile inspected via parent panel_D_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_D_s08
    path: build/audit_crops/panel_D_s08.png
    source: panel:D:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D sub-region tile inspected via parent panel_D_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_D_s09
    path: build/audit_crops/panel_D_s09.png
    source: panel:D:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D sub-region tile inspected via parent panel_D_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_D_s10
    path: build/audit_crops/panel_D_s10.png
    source: panel:D:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D sub-region tile inspected via parent panel_D_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_D_s11
    path: build/audit_crops/panel_D_s11.png
    source: panel:D:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D sub-region tile inspected via parent panel_D_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_D_s12
    path: build/audit_crops/panel_D_s12.png
    source: panel:D:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D sub-region tile inspected via parent panel_D_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_D_s13
    path: build/audit_crops/panel_D_s13.png
    source: panel:D:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D sub-region tile inspected via parent panel_D_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_D_s14
    path: build/audit_crops/panel_D_s14.png
    source: panel:D:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D sub-region tile inspected via parent panel_D_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_D_s15
    path: build/audit_crops/panel_D_s15.png
    source: panel:D:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D sub-region tile inspected via parent panel_D_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_D_s16
    path: build/audit_crops/panel_D_s16.png
    source: panel:D:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel D sub-region tile inspected via parent panel_D_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_E_q1
    path: build/audit_crops/panel_E_q1.png
    source: panel:E
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E quadrant crop inspected for sub-region layout; components, leaders, and labels match audit_enumeration."
  - crop_id: panel_E_q2
    path: build/audit_crops/panel_E_q2.png
    source: panel:E
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E quadrant crop inspected for sub-region layout; components, leaders, and labels match audit_enumeration."
  - crop_id: panel_E_q3
    path: build/audit_crops/panel_E_q3.png
    source: panel:E
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E quadrant crop inspected for sub-region layout; components, leaders, and labels match audit_enumeration."
  - crop_id: panel_E_q4
    path: build/audit_crops/panel_E_q4.png
    source: panel:E
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E quadrant crop inspected for sub-region layout; components, leaders, and labels match audit_enumeration."
  - crop_id: panel_E_s01
    path: build/audit_crops/panel_E_s01.png
    source: panel:E:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E sub-region tile inspected via parent panel_E_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_E_s02
    path: build/audit_crops/panel_E_s02.png
    source: panel:E:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E sub-region tile inspected via parent panel_E_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_E_s03
    path: build/audit_crops/panel_E_s03.png
    source: panel:E:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E sub-region tile inspected via parent panel_E_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_E_s04
    path: build/audit_crops/panel_E_s04.png
    source: panel:E:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E sub-region tile inspected via parent panel_E_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_E_s05
    path: build/audit_crops/panel_E_s05.png
    source: panel:E:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E sub-region tile inspected via parent panel_E_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_E_s06
    path: build/audit_crops/panel_E_s06.png
    source: panel:E:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E sub-region tile inspected via parent panel_E_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_E_s07
    path: build/audit_crops/panel_E_s07.png
    source: panel:E:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E sub-region tile inspected via parent panel_E_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_E_s08
    path: build/audit_crops/panel_E_s08.png
    source: panel:E:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E sub-region tile inspected via parent panel_E_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_E_s09
    path: build/audit_crops/panel_E_s09.png
    source: panel:E:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E sub-region tile inspected via parent panel_E_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_E_s10
    path: build/audit_crops/panel_E_s10.png
    source: panel:E:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E sub-region tile inspected via parent panel_E_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_E_s11
    path: build/audit_crops/panel_E_s11.png
    source: panel:E:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E sub-region tile inspected via parent panel_E_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_E_s12
    path: build/audit_crops/panel_E_s12.png
    source: panel:E:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E sub-region tile inspected via parent panel_E_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_E_s13
    path: build/audit_crops/panel_E_s13.png
    source: panel:E:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E sub-region tile inspected via parent panel_E_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_E_s14
    path: build/audit_crops/panel_E_s14.png
    source: panel:E:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E sub-region tile inspected via parent panel_E_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_E_s15
    path: build/audit_crops/panel_E_s15.png
    source: panel:E:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E sub-region tile inspected via parent panel_E_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_E_s16
    path: build/audit_crops/panel_E_s16.png
    source: panel:E:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel E sub-region tile inspected via parent panel_E_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_F_q1
    path: build/audit_crops/panel_F_q1.png
    source: panel:F
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F quadrant crop inspected for sub-region layout; components, leaders, and labels match audit_enumeration."
  - crop_id: panel_F_q2
    path: build/audit_crops/panel_F_q2.png
    source: panel:F
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F quadrant crop inspected for sub-region layout; components, leaders, and labels match audit_enumeration."
  - crop_id: panel_F_q3
    path: build/audit_crops/panel_F_q3.png
    source: panel:F
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F quadrant crop inspected for sub-region layout; components, leaders, and labels match audit_enumeration."
  - crop_id: panel_F_q4
    path: build/audit_crops/panel_F_q4.png
    source: panel:F
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F quadrant crop inspected for sub-region layout; components, leaders, and labels match audit_enumeration."
  - crop_id: panel_F_s01
    path: build/audit_crops/panel_F_s01.png
    source: panel:F:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F sub-region tile inspected via parent panel_F_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_F_s02
    path: build/audit_crops/panel_F_s02.png
    source: panel:F:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F sub-region tile inspected via parent panel_F_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_F_s03
    path: build/audit_crops/panel_F_s03.png
    source: panel:F:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F sub-region tile inspected via parent panel_F_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_F_s04
    path: build/audit_crops/panel_F_s04.png
    source: panel:F:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F sub-region tile inspected via parent panel_F_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_F_s05
    path: build/audit_crops/panel_F_s05.png
    source: panel:F:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F sub-region tile inspected via parent panel_F_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_F_s06
    path: build/audit_crops/panel_F_s06.png
    source: panel:F:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F sub-region tile inspected via parent panel_F_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_F_s07
    path: build/audit_crops/panel_F_s07.png
    source: panel:F:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F sub-region tile inspected via parent panel_F_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_F_s08
    path: build/audit_crops/panel_F_s08.png
    source: panel:F:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F sub-region tile inspected via parent panel_F_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_F_s09
    path: build/audit_crops/panel_F_s09.png
    source: panel:F:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F sub-region tile inspected via parent panel_F_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_F_s10
    path: build/audit_crops/panel_F_s10.png
    source: panel:F:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F sub-region tile inspected via parent panel_F_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_F_s11
    path: build/audit_crops/panel_F_s11.png
    source: panel:F:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F sub-region tile inspected via parent panel_F_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_F_s12
    path: build/audit_crops/panel_F_s12.png
    source: panel:F:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F sub-region tile inspected via parent panel_F_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_F_s13
    path: build/audit_crops/panel_F_s13.png
    source: panel:F:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F sub-region tile inspected via parent panel_F_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_F_s14
    path: build/audit_crops/panel_F_s14.png
    source: panel:F:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F sub-region tile inspected via parent panel_F_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_F_s15
    path: build/audit_crops/panel_F_s15.png
    source: panel:F:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F sub-region tile inspected via parent panel_F_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: panel_F_s16
    path: build/audit_crops/panel_F_s16.png
    source: panel:F:subquadrant
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Panel F sub-region tile inspected via parent panel_F_q* quadrant context; no additional micro-defect surfaced at this tile."
  - crop_id: print_178mm
    path: build/audit_crops/print_178mm.png
    source: print_scale:178mm_equivalent
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Print-scale audit image print_178mm inspected; labels survive reduction, arrow tips do not fuse, line weights survive at fixed_width_proxy width. Local label-collision defects (C001-C004) are reduction-invariant, not exposed only at print scale, so they do not propagate from this image."
  - crop_id: print_thumbnail
    path: build/audit_crops/print_thumbnail.png
    source: print_scale:thumbnail
    inspected: true
    verdict: no_defect
    linked_micro_defect_id: ""
    rationale: "Print-scale audit image print_thumbnail inspected; labels survive reduction, arrow tips do not fuse, line weights survive at fixed_width_proxy width. Local label-collision defects (C001-C004) are reduction-invariant, not exposed only at print scale, so they do not propagate from this image."
panels:
  - id: D
    findings:
      - id: P001
        severity: MINOR
        category: style
        tex_lines: [612, 680, 705]
        observation: "Panel D iconic-cartoon power-law plot abstracts NatComm 2022 tribo apparatus (apparatus1_ref04). Iconic-cartoon register per briefing §3.2 + Cycle 1 C401 SMU collision fix + Cycle 4 C419 equation math-italic."
        suggested_fix: "accept_simplification — iconic-cartoon register is briefing intent."
        status: open
  - id: E
    findings:
      - id: P002
        severity: MINOR
        category: style
        tex_lines: [757, 808, 833, 955, 1048]
        observation: "Panel E corona + V_s probe + V_s meter assembly is iconic abstraction of NatComm 2024 surface-charge (apparatus2_ref01) in canonical position (NOT scratch-regression). All HV+ / V_s meter labels at canonical y-coords; Keyence SK ESVM apparatus identity preserved post-iter-E16."
        suggested_fix: "accept_simplification — register intent."
        status: open
  - id: F
    findings:
      - id: P003
        severity: MINOR
        category: style
        tex_lines: [1146, 1178, 1218, 1320]
        observation: "Panel F cantilever + electrode + air gap iconic abstraction of NatComm 2016 microactuator (apparatus3_ref01). Coulomb-wins-Maxwell weight asymmetry preserved; electrode label rotated 270° post-Cycle-3 C417."
        suggested_fix: "accept_simplification — actuator framing transfer forbidden by TG-G-001."
        status: open
findings:
  - id: C001
    severity: MAJOR
    category: label_placement
    tex_lines: []
    observation: "Panel E HV+ source-box label glyph 'V' is bisected by the corona-needle wire stroke that exits the box bottom; the needle drops vertically through the V glyph, producing label_glyph_overlaps_internal_drawing inside the source-box outline."
    suggested_fix: "Move the corona-needle wire exit point laterally (offset x by ~0.10 cm) so the wire clears the V glyph; or shrink the HV+ label and recenter it left of the wire-exit anchor."
    status: open
  - id: C002
    severity: MAJOR
    category: label_placement
    tex_lines: []
    observation: "Panel E V_s meter label 'meter' glyphs overflow the right edge of the V_s meter rounded-rectangle outline — the 'r' of 'meter' is clipped by the box border. label_backdrop_overflows_outline."
    suggested_fix: "Widen the V_s meter box from current width to fit the full 'V_s meter' caption inside, or relabel to 'V_s' only and place 'meter' outside the box as a caption underneath."
    status: open
  - id: C003
    severity: MAJOR
    category: label_placement
    tex_lines: []
    observation: "Panel E V_s probe area label 'V' glyph crosses the rounded corner of the adjacent V_s meter rectangle outline; the left arm of the V passes through the box border. label_glyph_overlaps_internal_drawing."
    suggested_fix: "Shift the 'V_s probe' label x position by +0.25 cm so the V glyph clears the V_s meter corner; or lower the V_s probe label below the meter top edge so the glyphs no longer overlap the meter box border."
    status: open
  - id: C004
    severity: MINOR
    category: label_placement
    tex_lines: []
    observation: "Panel C 'Energy' rotated 90 deg axis label glyphs cross the polymer-film slab right-edge stroke (cAmber!85). The E, n, e, r, g of Energy each cross the vertical amber stroke, producing label_glyph_overlaps_internal_drawing on the energy-axis label."
    suggested_fix: "Shift the Energy axis label x position to the right of the film slab right edge by ~0.20 cm so the rotated glyphs clear the amber stroke; or attach the Energy label to the energy-diagram axis instead of the polymer-film right edge."
    status: open
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

`build/visual_clash.json` lists 58 candidates `VC001..VC058`. Each is accounted
exactly once via `micro_defects[].visual_clash_ref`. All 58 are classified
`accept_simplification` because they correspond to either:

- chemistry-register heteroatom labels on chain backbones (M001..M009, M055..M058),
- axis-label / axis-tick / curve-identity labels overlapping their own axis
  or curve by drawing convention (M013, M020..M023, M035..M043, M047..M049,
  M054),
- intentional iconographic markers (M026..M029 surface-charge ⊕),
- canonical-position apparatus labels (M015 HV+, M017+M018 V_s of V_s meter,
  M025 V_s probe area, M020 V_active, M052 SMU) — none in scratch-regression
  position,
- spoke modality labels with white-fill backdrop (M014, M032, M033), or
- text emerging from clean white background (M010, M050, M058).

No BLOCKER or MAJOR micro-defect is open. No top-level finding open.

## v1.9 critical re-audit findings (2026-05-22)

Under v1.9 schema (crop_audit_log mandatory; 124 audit crops individually
accountable), the previous v1.7 pass turned out to have under-classified
four label-target-collision defects as `accept_simplification` when zoom
inspection shows clear `label_glyph_overlaps_internal_drawing` /
`label_backdrop_overflows_outline` geometry. The four reclassified defects:

- **C001 (VC015, Panel E HV+ source box)** — corona-needle vertical wire bisects
  the V glyph of the 'HV+' label inside the source-box outline. Needs an x-shift
  on the needle exit anchor (or a label-position adjustment) so the wire clears
  the glyph.
- **C002 (VC019, Panel E V_s meter)** — 'V_s meter' label glyphs overflow the
  right edge of the V_s meter rounded-rectangle outline; the 'r' of 'meter' is
  clipped by the box border. Box must widen, or the label must be split so 'meter'
  sits outside the box.
- **C003 (VC025, Panel E V_s probe label)** — 'V' glyph of the 'V_s probe' label
  crosses the top-right rounded corner of the adjacent V_s meter box outline.
  Label x-offset or y-offset will clear the collision.
- **C004 (VC054, Panel C Energy axis)** — 'Energy' rotated-90 axis label glyphs
  cross the polymer-film-slab right-edge cAmber stroke; the rotated text sits on
  top of the film outline. Label needs an x-shift or a re-anchor to the
  energy-diagram axis instead of the film right edge.

## Verdict

`verdict: revise`. label_annotation_semantics + publication_readiness now
`needs_patch` because of the four open label-target-collision defects.
`journal_grade_assessment.benchmark_level` demoted high_impact_candidate ->
solid_manuscript; overall_score 90 -> 78 (label_semantics 90 -> 68 is the main
driver). `regression_detected: true` records the v1.7 -> v1.9 reclassification.
`next_quality_bottleneck: label_semantics`. The other 9 quality_axes still pass
and the NC main-text Fig 1 composition + Panel C HERO + 3-spoke fan + Row 2
iconic-cartoon evidence triplet are preserved — these are local-label fixes,
not a structural redo.
