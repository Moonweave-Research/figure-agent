---
schema: figure-agent.authoring-rules.v1
fixture: fig1_overview_v2_pair_001_vault
promotion_state: n1_hypotheses
rules:
  - id: pair001.panel-c-balanced-dual-view
    category: physics_semantics
    rule: Preserve the real-space plus energy-diagram split for localized traps, but allocate only the extra area required for common-scale legibility; do not assign Panel C privileged hero status.
    source:
      kind: critique_adjudication
      locator: examples/fig1_updated_agent_redraw_v1/briefing.md
      quote: "Panel C integrates the real-space and energy-domain trap views, but it is not a privileged visual hero."
    transfer_policy: use_as_constraint
  - id: pair001.panel-c-reference-gap
    category: physics_semantics
    rule: When Panel C-like trap physics is reused, ask whether fresh figure research is needed before deep layout iteration.
    source:
      kind: iteration_comment
      locator: examples/fig1_overview_v2_pair_001_vault/spec.yaml:23
      quote: "figure-research recommended (highest-priority gap)"
    transfer_policy: use_as_question
  - id: pair001.row2-apparatus-result-grammar
    category: panel_layout
    rule: For convergent evidence columns, keep each column split into apparatus context above and result semantics below.
    source:
      kind: iteration_comment
      locator: examples/fig1_overview_v2_pair_001_vault/spec.yaml:127-128
      quote: "each split apparatus zone top + result zone bottom"
    transfer_policy: use_as_constraint
  - id: pair001.raw-to-derived-arrow-bound
    category: label_binding
    rule: For a measurement-to-derived-result sequence, the transformation arrow tail must touch the source plot boundary and its arrowhead must enter the derived-result region. Put the arrow and its verb in a dedicated transformation lane instead of floating them ambiguously between plots.
    source:
      kind: hand_patch_commit
      locator: "Fig1 Panel E deep review, measurement-to-derivation repair (2026-07-20)"
      quote: "Bind the derive arrow to both the measured V_s(t) plot and the derived g(E_t) region."
    transfer_policy: use_as_constraint
  - id: pair001.tau-d-energy-domain-exception
    category: physics_semantics
    rule: "For this paper-local overview, preserve tau_d as the qualitative energy-domain interval between the shallow and deep g(E_t) peak positions. Keep its endpoints bound to those two peak positions, but do not add numeric ticks, point markers, a value, or a unit that would turn the schematic interval into unsupported quantitative data. Do not move it onto the V_s(t) time axis merely because tau conventionally denotes time. Treat this as a source-bound exception, not a transferable default for unrelated ISPD figures."
    source:
      kind: critique_adjudication
      locator: "fig1_overview_v5f_art_direction_001_vault/briefing.md sections 8 and 13.6 E-9"
      quote: "tau_d annotation - energy-domain interval between Gaussian peaks"
    transfer_policy: use_as_constraint
  - id: pair001.host-texture-needs-physical-identity
    category: physics_semantics
    rule: "In a real-space material field, do not scatter same-size dots merely to fill empty space: repeated particles can imply fillers, pores, or a second population. Use continuous non-periodic disorder cues only when they bind to a declared spatial-energy or morphology claim; otherwise omit decorative texture and let the localized states carry the meaning."
    source:
      kind: hand_patch_commit
      locator: "Fig1 Panel C real-space deep review (2026-07-20)"
      quote: "Neutral equal-size dots read as an undeclared particle population rather than amorphous energetic disorder."
    transfer_policy: use_as_constraint
  - id: pair001.ground-symbol-grammar-consistent
    category: instrument_standard
    rule: Use the same three-bar tapered ground grammar for equivalent electrical references across one figure. A visibly different ground glyph requires a declared different electrical reference; do not vary bar count, taper, or orientation as incidental drawing shorthand.
    source:
      kind: hand_patch_commit
      locator: "Fig1 Panel D apparatus deep review against Panel E (2026-07-20)"
      quote: "Panel D used a two-bar ground while Panel E used the shared three-bar tapered symbol."
    transfer_policy: use_as_constraint
  - id: pair001.power-law-slope-matches-exponent
    category: physics_semantics
    rule: "For a log-log response declared as I(t) proportional to t^-n, the trace with larger n must have the more negative slope. Verify the rendered endpoints or source geometry and keep each rotated label aligned with its owning trace; label text alone is not evidence that the exponent ordering is correct."
    source:
      kind: hand_patch_commit
      locator: "Fig1 Panel D power-law geometry audit (2026-07-20)"
      quote: "The high-n trace must visibly fall faster than the low-n trace on log I versus log t axes."
    transfer_policy: use_as_constraint
  - id: pair001.panel-d-do-not-transfer-triboelectric
    category: physics_semantics
    rule: Reusing Panel D apparatus grammar must not transfer triboelectric mechanism or breakdown narrative into charge-trap figures.
    source:
      kind: iteration_comment
      locator: examples/fig1_overview_v2_pair_001_vault/spec.yaml:30-34
      quote: "Do-not-transfer: triboelectric mechanism, breakdown narrative"
    transfer_policy: use_as_constraint
  - id: pair001.panel-e-side-view-apparatus
    category: instrument_standard
    rule: Prefer side-view apparatus geometry for ISPD-style probe and grounded-substrate explanations unless a new source justifies isometric transfer.
    source:
      kind: iteration_comment
      locator: examples/fig1_overview_v2_pair_001_vault/spec.yaml:38-44
      quote: "side-view structurally better for this apparatus"
    transfer_policy: use_as_question
    lifecycle: superseded
    superseded_by: polymer_paper_project.ispd-two-terminal-corona-topology
    superseded_reason: The rule bundled a useful projection preference with an unverified grounded-substrate topology; later human scientific review confirmed a gridless two-terminal high-voltage charging circuit.
  - id: pair001.panel-e-probe-above-sample
    category: instrument_standard
    rule: Bind probe, motion stage, sample, grounded substrate, and Vs meter labels to their physical components in ISPD-style apparatus panels.
    source:
      kind: iteration_comment
      locator: examples/fig1_overview_v2_pair_001_vault/spec.yaml:44-47
      quote: "probe-above-sample geometry, motion-stage labeling, sample-on-grounded-substrate cross-section"
    transfer_policy: use_as_constraint
    lifecycle: superseded
    superseded_by: polymer_paper_project.ispd-keyence-manual-transfer
    superseded_reason: Later human review confirmed manual specimen transfer rather than an automated motion stage.
  - id: pair001.panel-f-cross-section-conventions
    category: style_lock
    rule: Preserve cross-section conventions for electrode hatching, insulator stipple, parameter labels, and deflection arrows when transferring Panel F visual grammar.
    source:
      kind: iteration_comment
      locator: examples/fig1_overview_v2_pair_001_vault/spec.yaml:60-63
      quote: "electrode hatching 45°+135° + insulator stipple"
    transfer_policy: use_as_constraint
  - id: pair001.mobility-edge-label-clearance
    category: label_binding
    rule: Keep mobility-edge labels clear of the reference line; a readable label must not sit on top of the semantic line it names.
    source:
      kind: hand_patch_commit
      locator: commit 0a6e308; examples/fig1_overview_v2_pair_001_vault/spec.yaml:108-114
      quote: "panel_c_mobility_edge_reference"
    transfer_policy: use_as_constraint
  - id: pair001.deep-escape-curve-clearance
    category: label_binding
    rule: Treat trap-escape curves as semantic paths with explicit clearance from neighboring labels unless a panel-specific source overrides it.
    source:
      kind: hand_patch_commit
      locator: commit 0a6e308; examples/fig1_overview_v2_pair_001_vault/spec.yaml:115-123
      quote: "panel_c_deep_escape_curve"
    transfer_policy: use_as_constraint
  - id: pair001.nc-clean-white-background
    category: style_lock
    rule: For an NC main-text Fig 1, keep a clean white background; remove wash ellipses, background fills, wavy chain hints, and dotted column dividers.
    source:
      kind: iteration_comment
      locator: examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex:57-59
      quote: "NC main-text Fig 1 convention = clean white"
    transfer_policy: use_as_constraint
  - id: pair001.molecule-atoms-and-bonds
    category: physics_semantics
    rule: Draw molecules such as S8 as atoms-and-bonds that carry molecular identity, not as a graphic icon, and drop redundant center identity labels.
    source:
      kind: iteration_comment
      locator: examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex:271
      quote: "S₈ molecule drawn as atoms-and-bonds, not graphic icon"
    transfer_policy: use_as_constraint
  - id: pair001.atom-label-adjacent-bond-terminus
    category: label_binding
    rule: Place atom labels adjacent to the bond terminus rather than on the bond line, and originate reaction arrows from the molecule exterior.
    source:
      kind: iteration_comment
      locator: examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex:304-305
      quote: "atom label adjacent to bond terminus rather than on bond line"
    transfer_policy: use_as_constraint
  - id: pair001.energy-reference-levels-horizontal
    category: physics_semantics
    rule: Draw energy-diagram reference levels such as vacuum and band edges as band-spanning horizontal lines that read as reference levels, not as quantitative measurements.
    source:
      kind: iteration_comment
      locator: examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex:621-625
      quote: "Vacuum is a *reference level*, not a quantitative measurement"
    transfer_policy: use_as_constraint
  - id: pair001.instrument-faceplate-bezel
    category: instrument_standard
    rule: Give instrument boxes a dark-glass display plus an inner faceplate bezel for machined-panel weight; avoid flat or gizmo-style boxes.
    source:
      kind: iteration_comment
      locator: examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex:1029
      quote: "inner faceplate bezel for machined-panel weight"
    transfer_policy: use_as_constraint
    lifecycle: superseded
    superseded_by: polymer_paper_project.ispd-keyence-manual-transfer
    superseded_reason: Confirmed family-level authority must not force unverified model-specific controls or a reusable faceplate primitive.
  - id: pair001.print-scale-registration
    category: style_lock
    rule: Size and weight elements against the declared final physical size, not a fixed screen zoom or legacy 178 mm proxy. For Nature-family main figures, record whether the working target is constrained by column width or by the 170 mm maximum-height guidance; verify fonts, thin features, small shapes, panel letters, and inter-panel gutters at that target before judging proportions.
    source:
      kind: hand_patch_commit
      locator: "Fig1 updated-agent redraw final-size audit (2026-07-21)"
      quote: "Current 150.7 x 153.6 mm render reaches 170 mm height at about 166.8 mm width; 180/183 mm width would exceed the 170 mm height guidance."
    transfer_policy: use_as_question
  - id: pair001.balanced-saturation-hierarchy
    category: style_lock
    rule: Use saturation to bind scientific categories consistently across panels; do not reserve the loudest color for Panel C solely because it was formerly designated as a hero.
    source:
      kind: critique_adjudication
      locator: examples/fig1_updated_agent_redraw_v1/briefing.md
      quote: "it is not a privileged visual hero"
    transfer_policy: use_as_constraint
  - id: pair001.label-tone-and-rotation-legibility
    category: label_binding
    rule: Keep labels legible; avoid a same-tone label on a same-tone fill, and avoid near-vertical rotated labels because a sloped label on a near-vertical element is unreadable.
    source:
      kind: iteration_comment
      locator: examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex:1188
      quote: "sloped label would itself be near-vertical — unreadable"
    transfer_policy: use_as_constraint
  - id: pair001.iconic-register-is-intentional
    category: style_lock
    rule: Iconic-cartoon abstraction of apparatus references in the evidence panels is briefing intent; do not treat iconic simplification as a defect to fix toward photorealism.
    source:
      kind: critique_adjudication
      locator: examples/fig1_overview_v2_pair_001_vault/critique_adjudication.yaml P001-P003
      quote: "accept_simplification — iconic-cartoon register is briefing intent"
    transfer_policy: use_as_constraint
  - id: pair001.depth-cues-need-semantics
    category: style_lock
    rule: "Do not use glossy or ball-shaded rendering as the neutral default for repeated sites, states, particles, or data markers. Keep those marks flat and restrained unless depth encodes a declared 3D geometry or material relation; this does not require apparatus photorealism."
    source:
      kind: iteration_comment
      locator: "Fig1 C-F aesthetic review (2026-07-19)"
      quote: "미감이 아직 조금 유치 한 느낌"
    transfer_policy: use_as_constraint
  - id: pair001.no-actuator-framing-transfer
    category: physics_semantics
    rule: Do not transfer actuator or MEMS framing into the charge-trap mechanical panel; the apparatus reference is borrowed for grammar only.
    source:
      kind: critique_adjudication
      locator: examples/fig1_overview_v2_pair_001_vault/critique_adjudication.yaml P003
      quote: "actuator framing transfer forbidden by TG-G-001"
    transfer_policy: use_as_constraint
---

# Pair 001 Authoring Rules

This catalog records source-anchored hypotheses extracted from the first
accepted Fig 1 pair-001 vault fixture. Rules are distilled from two source
kinds: the figure's own iteration comments and hand-patch commits in
`fig1_overview_v2_pair_001_vault.tex`, and the dismissals/decisions in
`critique_adjudication.yaml`. Each rule cites the exact comment, commit, or
adjudication entry it came from; nothing here is invented best practice.

These rules are intentionally not a general polymer-physics style guide. They
are authoring-time checks and constraints that remain in `n1_hypotheses` until
another figure validates transfer.
