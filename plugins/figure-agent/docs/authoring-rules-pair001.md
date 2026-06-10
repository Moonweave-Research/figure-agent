---
schema: figure-agent.authoring-rules.v1
fixture: fig1_overview_v2_pair_001_vault
promotion_state: n1_hypotheses
rules:
  - id: pair001.panel-c-hero-split
    category: physics_semantics
    rule: Treat localized traps as the primary semantic hero and preserve the real-space plus energy-diagram split when transferring Fig 1 knowledge.
    source:
      kind: iteration_comment
      locator: examples/fig1_overview_v2_pair_001_vault/spec.yaml:21-23
      quote: "Localized traps (HERO #1) — real-space + energy diagram split"
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
  - id: pair001.panel-e-probe-above-sample
    category: instrument_standard
    rule: Bind probe, motion stage, sample, grounded substrate, and Vs meter labels to their physical components in ISPD-style apparatus panels.
    source:
      kind: iteration_comment
      locator: examples/fig1_overview_v2_pair_001_vault/spec.yaml:44-47
      quote: "probe-above-sample geometry, motion-stage labeling, sample-on-grounded-substrate cross-section"
    transfer_policy: use_as_constraint
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
  - id: pair001.print-scale-registration
    category: style_lock
    rule: Size and weight elements so they register at the real print scale (178 mm width), not only on screen; verify thin features and small shapes stay visible at print scale.
    source:
      kind: iteration_comment
      locator: examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex:670
      quote: "registers at 178mm print scale as a visible"
    transfer_policy: use_as_question
  - id: pair001.hero-saturation-hierarchy
    category: style_lock
    rule: Preserve panel visual hierarchy; the HERO panel must out-saturate secondary panels and the loudest color is reserved for the hero claim. Audit when a non-hero color reads as too prominent.
    source:
      kind: iteration_comment
      locator: examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex:675
      quote: "Panel C HERO must out-saturate Panel E"
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
