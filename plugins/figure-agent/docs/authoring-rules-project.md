---
schema: figure-agent.authoring-rules.v1
fixture: polymer_paper_project
promotion_state: n1_hypotheses
rules:
  - id: polymer_paper_project.cantilever-vertical-clip-top
    category: instrument_standard
    rule: "Draw the polymer cantilever vertical: clip/clamp on top, polymer hangs down, deflection sideways toward a side electrode. Horizontal cantilever orientation is wrong for this lab and its experiments."
    source:
      kind: hand_patch_commit
      locator: "examples/fig3_floating_clip_protocol vertical re-draw (2026-06-20)"
      quote: "clip on TOP, polymer hangs down"
    transfer_policy: use_as_constraint
  - id: polymer_paper_project.trap-colour-shallow-blue-deep-red
    category: label_binding
    rule: "Shallow traps and shallow states are blue or teal; deep traps and deep states are red. Keep this colour mapping consistent across every figure."
    source:
      kind: hand_patch_commit
      locator: "examples/fig1_overview_v2_pair_001_vault/authoring_contract.md"
      quote: "Shallow traps are blue and deep traps are red across Panels C, F, and G"
    transfer_policy: use_as_constraint
  - id: polymer_paper_project.panel-header-and-label-clearance
    category: panel_layout
    rule: "Reserve a clear header band inside every panel for the panel letter and title. Keep body geometry and subtitles out of that band. Every label must clear other text, apparatus geometry, semantic paths, and the panel frame; use whitespace or a leader when direct placement does not fit. Do not solve clearance by forcing an equal-cell grid: composition remains author-selected."
    source:
      kind: iteration_comment
      locator: "Fig1 R5 prospective v2 adversarial review (2026-07-18)"
      quote: "아직 내가 굳이 안집어줘도 많을 정도로 완성도는 부족"
    transfer_policy: use_as_constraint
---

# Project authoring rule catalog (polymer_paper_project)

Cross-figure conventions for the sulfur-polymer paper, inherited by EVERY figure's
authoring context pack. Distinct from the per-fixture `authoring-rules-pair001.md`
catalog: rules here are project-scope (not tied to one figure) and were distilled
from conventions that recur across figures — for example the vertical-cantilever
orientation, which an AI default-orientation bias kept re-violating on each new
figure because the convention was previously locked to the fig1 pilot catalog.

Add a rule here only when a convention is genuinely cross-figure and source-anchored
(an iteration comment, a critique adjudication, or a hand-patch commit).

New fixtures must annotate each panel region with a canonical `% Panel X` comment line
(matching `^\s*%\s*Panel\s+<id>`); the candidate loop maps a detector source_line to its
enclosing panel via these markers, and without them defect candidates are refused as
`unknown_panel`.
