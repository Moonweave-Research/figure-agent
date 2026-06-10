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
---

# Pair 001 Authoring Rules

This catalog records source-anchored hypotheses extracted from the first
accepted Fig 1 pair-001 vault fixture. These rules are intentionally not a
general polymer-physics style guide. They are authoring-time checks and
constraints that remain in `n1_hypotheses` until another figure validates
transfer.
